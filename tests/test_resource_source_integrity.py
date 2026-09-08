"""Resource availability, overlay staleness, and original source-location checks."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core_prompts_eval.contracts import ContractError, artifact_hash
from core_prompts_eval.topology import compile_topology
from intent_pipeline.capability_resources import ResourceContractError


def package(tmp_path: Path, entry_text: str = "# Fixture\nRequired entry behavior.\n") -> tuple[Path, Path]:
    entry = tmp_path / "ssot/example.md"
    entry.parent.mkdir()
    entry.write_bytes(entry_text.encode("utf-8"))
    root = tmp_path / "sources/capability-resources/example"
    root.mkdir(parents=True)
    (root / "module.md").write_text("## MODULE: /review\n\nNever invent evidence.\n", encoding="utf-8")
    (root / "resource-map.json").write_text(json.dumps({
        "schema_version": "CapabilityResourceMap.v1", "shared": [],
        "routes": {"/review": ["module.md"]}, "dependencies": {},
    }), encoding="utf-8")
    return entry, root


@pytest.mark.parametrize("state", ["missing", "directory", "broken_symlink"])
def test_topology_rejects_declared_manifest_unavailability(tmp_path: Path, state: str) -> None:
    entry, root = package(tmp_path, "# Fixture\nMust use resources/resource-map.json.\n")
    manifest = root / "resource-map.json"
    manifest.unlink()
    if state == "directory":
        manifest.mkdir()
    elif state == "broken_symlink":
        manifest.symlink_to(root / "absent.json")
    with pytest.raises(ResourceContractError):
        compile_topology(entry)


def test_topology_validates_entry_resource_references(tmp_path: Path) -> None:
    entry, _ = package(tmp_path, "# Fixture\nMust read resources/resource-map.json and resources/absent.md.\n")
    with pytest.raises(ResourceContractError, match="undeclared"):
        compile_topology(entry)


def test_overlay_rejects_removed_bundle_even_if_entry_has_no_map_mention(tmp_path: Path) -> None:
    entry, root = package(tmp_path)
    (root / "module.md").write_text("## MODULE: /review\nResource behavior without normative markers.\n")
    topology = compile_topology(entry)
    ids = [item["id"] for item in topology["protected_invariants"]]
    review = tmp_path / "evals/reviews/example.json"
    review.parent.mkdir(parents=True)
    review.write_text(json.dumps({
        "schema_version": "CapabilityTopologyReview.v1", "slug": "example",
        "ssot_sha256": topology["ssot_sha256"], "resource_bundle_sha256": topology["resource_bundle_sha256"],
        "clause_mappings": {clause_id: ["fixture-case"] for clause_id in ids}, "waivers": [], "review_status": "human_reviewed",
        "risk_tiers": {"critical": [], "high": [], "standard": ids},
    }))
    assert compile_topology(entry)["review_status"] == "human_reviewed"
    (root / "resource-map.json").unlink()
    with pytest.raises(ContractError, match="resource bundle hash is stale"):
        compile_topology(entry)


def test_mode_locations_use_original_entry_and_resource_files(tmp_path: Path) -> None:
    from intent_pipeline.uac_modes import extract_capability_modes
    text = "---\nname: example\n---\n# Fixture\n\n## Modes\n### Inspect\nRequired inspection.\n"
    _, root = package(tmp_path, text)
    (root / "module.md").write_text("# Review resource\n\n## MODULE: /review\n\n### Nested MODULE: /review /deep\nRequired deliberation.\n")
    modes = extract_capability_modes(tmp_path, "example", text)
    assert [item["invocations"] for item in modes] == [[], ["/review"], ["/review /deep"]]
    assert [(item["source_refs"], item["source_line"]) for item in modes] == [
        (["ssot/example.md"], 7),
        (["sources/capability-resources/example/module.md"], 3),
        (["sources/capability-resources/example/module.md"], 5),
    ]
    topology = compile_topology(tmp_path / "ssot/example.md")
    assert topology["nodes"]["modes_modules"] == modes


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_clause_locations_are_raw_file_lines_with_stable_entry_ids(tmp_path: Path, newline: str) -> None:
    text = newline.join(["---", "name: example", "description: required metadata", "---", "# Fixture", "", "Required entry behavior.", ""])
    entry, root = package(tmp_path, text)
    topology = compile_topology(entry)
    for clause in topology["protected_invariants"]:
        original_lines = (tmp_path / clause["source"]).read_text(encoding="utf-8").splitlines()
        assert original_lines[clause["source_line"] - 1].strip() == clause["text"]
        assert "required metadata" not in clause["text"]
    first = topology["protected_invariants"][0]
    assert first["id"].startswith("example:L3:")  # Preserve established body-relative IDs.
    assert first["source_line"] == 7
    assert topology["ssot_sha256"] == artifact_hash(entry)
    assert topology["source_references"][0]["sha256"] == artifact_hash(entry)


def test_source_heading_does_not_leak_between_documents(tmp_path: Path) -> None:
    entry, root = package(tmp_path, "# Fixture\n## Required Output\n- Required result.\n")
    (root / "module.md").write_text("- Required review context.\n\n## MODULE: /review\n")
    topology = compile_topology(entry)
    resource_clause = next(item for item in topology["protected_invariants"] if "review context" in item["text"])
    assert resource_clause["heading"] == "root"
    assert "- Required review context." not in topology["outputs"]


def test_topology_modes_and_clauses_use_the_same_resource_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from intent_pipeline import capability_resources
    entry, root = package(tmp_path)
    original_loader = capability_resources.load_resource_bundle

    def mutate_after_snapshot(*args, **kwargs):
        bundle = original_loader(*args, **kwargs)
        (root / "module.md").write_text("## MODULE: /changed\nNever use the stale mode.\n")
        return bundle

    monkeypatch.setattr(capability_resources, "load_resource_bundle", mutate_after_snapshot)
    topology = compile_topology(entry)
    assert "/review" in topology["explicit_invocations"]
    assert "/changed" not in topology["explicit_invocations"]
