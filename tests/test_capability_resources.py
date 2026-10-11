from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from intent_pipeline.capability_resources import (
    ResourceContractError,
    effective_capability_text,
    load_resource_bundle,
)


def write_bundle(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    documents = {
        "shared.md": "# Shared\nRequired context.\n",
        "principles.md": "# Principles\nFirst principles.\n",
        "basis.md": "# Basis\nRead resources/principles.md.\n",
        "grade.md": "# Grade\nIndependent grading.\n",
        "archive.md": "# Retired\nNever load implicitly.\n",
    }
    for name, content in documents.items():
        (root / name).write_text(content, encoding="utf-8")
    manifest = {
        "schema_version": "CapabilityResourceMap.v1",
        "shared": ["shared.md"],
        "routes": {"basis": ["basis.md"], "grade": ["grade.md"]},
        "dependencies": {"basis.md": ["principles.md"]},
    }
    save_manifest(root, manifest)
    return manifest


def save_manifest(root: Path, manifest: dict) -> None:
    (root / "resource-map.json").write_text(json.dumps(manifest), encoding="utf-8")


def paths(bundle: dict) -> list[str]:
    return [item["path"] for item in bundle["resources"]]


def test_nested_closure_and_route_specificity(tmp_path: Path) -> None:
    manifest = write_bundle(tmp_path)
    manifest["dependencies"]["principles.md"] = ["shared.md"]
    save_manifest(tmp_path, manifest)
    assert paths(load_resource_bundle(tmp_path, "basis")) == ["shared.md", "principles.md", "basis.md"]
    assert paths(load_resource_bundle(tmp_path, "grade")) == ["shared.md", "grade.md"]
    assert paths(load_resource_bundle(tmp_path)) == ["shared.md", "principles.md", "basis.md", "grade.md"]


def test_payload_is_complete_stable_and_bound_to_raw_bytes(tmp_path: Path) -> None:
    write_bundle(tmp_path)
    initial = load_resource_bundle(tmp_path, "basis")
    assert initial == load_resource_bundle(tmp_path, "basis")
    assert initial["schema_version"] == "CapabilityResourceBundle.v1"
    assert initial["delivery_claim"] == "assembled_not_proof_of_consumption"
    assert "archive.md" not in paths(initial)
    for item in initial["resources"]:
        assert item["content"].encode("utf-8") == (tmp_path / item["path"]).read_bytes()
        assert len(item["sha256"]) == 64
    (tmp_path / "basis.md").write_bytes(b"# Basis\r\nChanged wording.\r\n")
    changed = load_resource_bundle(tmp_path, "basis")
    assert initial["sha256"] != changed["sha256"]
    assert changed["resources"][-1]["content"] == "# Basis\r\nChanged wording.\r\n"


def test_declared_archive_is_included_only_when_explicit(tmp_path: Path) -> None:
    manifest = write_bundle(tmp_path)
    manifest["routes"]["history"] = ["archive.md"]
    save_manifest(tmp_path, manifest)
    assert "archive.md" not in paths(load_resource_bundle(tmp_path, "basis"))
    assert "archive.md" in paths(load_resource_bundle(tmp_path, "history"))


def test_hash_binds_manifest_semantics_even_with_identical_all_content(tmp_path: Path) -> None:
    manifest = write_bundle(tmp_path)
    before = load_resource_bundle(tmp_path)
    manifest["routes"]["basis"].append("grade.md")
    save_manifest(tmp_path, manifest)
    after = load_resource_bundle(tmp_path)
    assert before["resources"] == after["resources"]
    assert before["sha256"] != after["sha256"]
    assert before["manifest_sha256"] != after["manifest_sha256"]


def test_hash_binds_selected_route_even_for_equal_closures(tmp_path: Path) -> None:
    manifest = write_bundle(tmp_path)
    manifest["routes"]["alias"] = list(manifest["routes"]["grade"])
    save_manifest(tmp_path, manifest)
    assert load_resource_bundle(tmp_path, "grade")["resources"] == load_resource_bundle(tmp_path, "alias")["resources"]
    assert load_resource_bundle(tmp_path, "grade")["sha256"] != load_resource_bundle(tmp_path, "alias")["sha256"]


def test_infrastructure_references_do_not_load_script_source(tmp_path: Path) -> None:
    root = tmp_path / "sources/capability-resources/example"
    write_bundle(root)
    effective = effective_capability_text(tmp_path, "example", "Use resources/resource-map.json and resources/scripts/load_module.py.")
    assert "# Basis" in effective


def test_nested_route_cli_with_single_space_tokens(tmp_path: Path) -> None:
    manifest = write_bundle(tmp_path)
    manifest["routes"]["/adversarial /debate /deep"] = ["grade.md"]
    save_manifest(tmp_path, manifest)
    source = Path(__file__).parents[1] / "src/intent_pipeline/capability_resources.py"
    result = subprocess.run([sys.executable, str(source), "--resource-root", str(tmp_path), "--route", "/adversarial /debate /deep", "--format", "json"], capture_output=True, text=True, check=True)
    assert paths(json.loads(result.stdout)) == ["shared.md", "grade.md"]


@pytest.mark.parametrize("route", [" basis", "basis ", "basis  grade", "basis\tgrade", "basis\ngrade", "", "all"])
def test_noncanonical_route_names_are_rejected(tmp_path: Path, route: str) -> None:
    manifest = write_bundle(tmp_path)
    manifest["routes"][route] = ["grade.md"]
    save_manifest(tmp_path, manifest)
    with pytest.raises(ResourceContractError, match="route"):
        load_resource_bundle(tmp_path)


@pytest.mark.parametrize("invalid", ["../outside.md", "/tmp/outside.md", "a/../shared.md", "resources/shared.md", "./shared.md", "a\\shared.md", "", "https://example.com/a", "a//b.md"])
def test_invalid_paths_are_rejected(tmp_path: Path, invalid: str) -> None:
    manifest = write_bundle(tmp_path)
    manifest["routes"]["basis"] = [invalid]
    save_manifest(tmp_path, manifest)
    with pytest.raises(ResourceContractError, match="path"):
        load_resource_bundle(tmp_path)


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    resources = tmp_path / "resources"
    write_bundle(resources)
    outside = tmp_path / "outside.md"
    outside.write_text("not a resource", encoding="utf-8")
    (resources / "basis.md").unlink()
    (resources / "basis.md").symlink_to(outside)
    with pytest.raises(ResourceContractError, match="escapes"):
        load_resource_bundle(resources)


def test_symlink_manifest_escape_is_rejected(tmp_path: Path) -> None:
    resources = tmp_path / "resources"
    write_bundle(resources)
    external = tmp_path / "external.json"
    (resources / "resource-map.json").rename(external)
    (resources / "resource-map.json").symlink_to(external)
    with pytest.raises(ResourceContractError, match="escapes"):
        load_resource_bundle(resources)


@pytest.mark.parametrize("failure", ["missing", "cycle", "unknown", "malformed", "duplicate_json", "unregistered_ref", "missing_dependency"])
def test_invalid_contracts_fail_closed(tmp_path: Path, failure: str) -> None:
    manifest = write_bundle(tmp_path)
    route = "basis"
    if failure == "missing":
        (tmp_path / "grade.md").unlink()  # Invalid inactive route is still an invalid manifest.
    elif failure == "cycle":
        manifest["dependencies"]["principles.md"] = ["basis.md"]
    elif failure == "unknown":
        route = "unknown"
    elif failure == "malformed":
        manifest["routes"]["basis"] = "basis.md"
    elif failure == "unregistered_ref":
        (tmp_path / "basis.md").write_text("Read resources/archive.md", encoding="utf-8")
    elif failure == "missing_dependency":
        (tmp_path / "basis.md").write_text("Read resources/grade.md", encoding="utf-8")
    save_manifest(tmp_path, manifest)
    if failure == "duplicate_json":
        (tmp_path / "resource-map.json").write_text('{"schema_version":"bad","schema_version":"CapabilityResourceMap.v1"}', encoding="utf-8")
    with pytest.raises(ResourceContractError):
        load_resource_bundle(tmp_path, route)


def test_effective_text_reads_only_declared_resources(tmp_path: Path) -> None:
    entry = "# Entry\nChoose resources/basis.md or resources/grade.md.\n"
    resource_root = tmp_path / "sources/capability-resources/example"
    write_bundle(resource_root)
    effective = effective_capability_text(tmp_path, "example", entry, "basis")
    assert effective.startswith(entry.rstrip() + "\n\n")
    assert "<!-- resource: principles.md sha256=" in effective
    assert "# Basis" in effective
    assert "# Grade" not in effective
    assert "# Retired" not in effective
    assert effective == effective_capability_text(tmp_path, "example", entry, "basis")


def test_effective_text_without_manifest_is_unchanged(tmp_path: Path) -> None:
    entry = "# Original\r\n  Keep exact whitespace.  \n"
    assert effective_capability_text(tmp_path, "example", entry) == entry


@pytest.mark.parametrize("state", ["missing", "directory", "broken_symlink"])
def test_declared_manifest_never_falls_back_to_entry_only(tmp_path: Path, state: str) -> None:
    root = tmp_path / "sources/capability-resources/example"
    root.mkdir(parents=True)
    manifest = root / "resource-map.json"
    if state == "directory":
        manifest.mkdir()
    elif state == "broken_symlink":
        manifest.symlink_to(root / "missing-map.json")
    with pytest.raises(ResourceContractError):
        effective_capability_text(tmp_path, "example", "Must load resources/resource-map.json.")


def test_effective_text_rejects_entry_manifest_mismatch(tmp_path: Path) -> None:
    write_bundle(tmp_path / "sources/capability-resources/example")
    with pytest.raises(ResourceContractError, match="undeclared"):
        effective_capability_text(tmp_path, "example", "Read resources/archive.md")


def test_generated_descriptor_footer_is_infrastructure_not_module_content(tmp_path: Path) -> None:
    root = tmp_path / "sources/capability-resources/example"
    write_bundle(root)
    entry = "# Example\nCapability resource: `resources/capability.json`\n"
    effective = effective_capability_text(tmp_path, "example", entry)
    assert entry in effective
    assert "capability.json" not in [item["path"] for item in load_resource_bundle(root)["resources"]]


def test_cli_bundled_default_emits_complete_content(tmp_path: Path) -> None:
    write_bundle(tmp_path)
    script = tmp_path / "scripts/load_module.py"
    script.parent.mkdir()
    shutil.copyfile(Path(__file__).parents[1] / "src/intent_pipeline/capability_resources.py", script)
    result = subprocess.run([sys.executable, str(script), "--route", "basis", "--format", "json"], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == load_resource_bundle(tmp_path, "basis")
    text_result = subprocess.run([sys.executable, str(script), "--resource-root", str(tmp_path), "--route", "basis"], capture_output=True, text=True, check=True)
    for item in load_resource_bundle(tmp_path, "basis")["resources"]:
        assert item["content"] in text_result.stdout
    assert "assembled_not_proof_of_consumption" in text_result.stdout
    invalid = subprocess.run([sys.executable, str(script), "--route", "unknown"], capture_output=True, text=True)
    assert invalid.returncode != 0
    assert invalid.stdout == ""
    assert "unknown" in invalid.stderr


# Findings.v1 checks exercise the shipped schema rather than an implementation mirror.
# jsonschema is a declared CI dependency; no local executable or network is required.
@pytest.fixture
def review_findings_contract():
    from jsonschema import Draft202012Validator

    resource_root = Path(__file__).parents[1] / "sources/capability-resources/engos-quality-code-review"
    bundle = load_resource_bundle(resource_root, "review")
    assert set(paths(bundle)) == {"references/review-targets.md", "schemas/findings.schema.json"}
    schema = json.loads((resource_root / "schemas/findings.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    record = {
        "schema_version": "Findings.v1",
        "target": {"kind": "commit", "base": "b" * 40, "head": "a" * 40,
                   "snapshot_digest": None, "comparison": "parent", "included_change_classes": ["committed"]},
        "review_status": "complete",
        "evidence": [{"id": "E-diff", "path": "candidate.diff", "kind": "diff", "side": "head",
                      "identity": "c" * 64, "line_start": None, "line_end": None, "read_status": "read"}],
        "findings": [], "unreviewed": [], "verdict": "ready",
    }
    return Draft202012Validator(schema), record


@pytest.mark.parametrize("kind,comparison,classes", [
    ("commit", "parent", ["committed"]), ("commit", "root", ["committed"]),
    ("commit", "merge_parent", ["committed"]), ("branch", "range", ["committed"]),
    ("branch", "merge_base", ["committed"]), ("staged", "staged", ["staged"]),
    ("working_tree", "unstaged", ["unstaged"]),
    ("working_tree", "combined", ["staged", "unstaged", "untracked"]),
    ("diff", "supplied_diff", ["supplied"]),
])
def test_review_findings_accept_distinct_targets(review_findings_contract, kind, comparison, classes):
    validator, record = review_findings_contract
    record["target"].update(kind=kind, comparison=comparison, included_change_classes=classes)
    if kind in {"staged", "working_tree", "diff"}:
        record["target"].update(base=None, head=None, snapshot_digest="d" * 64)
    if comparison == "root":
        record["target"]["base"] = None
    validator.validate(record)


@pytest.mark.parametrize("failure", [
    "missing_field", "incomplete_ready", "unreviewed_complete", "unread", "unavailable",
    "no_diff", "no_evidence", "unbound_evidence", "short_head", "staged_no_digest", "wrong_classes",
    "branch_no_base", "wrong_staged_comparison", "unstaged_with_staged",
])
def test_review_findings_reject_invalid_complete_receipts(review_findings_contract, failure):
    validator, record = review_findings_contract
    if failure == "missing_field":
        del record["review_status"]
    elif failure == "incomplete_ready":
        record.update(review_status="incomplete", unreviewed=["Missing consumer"])
    elif failure == "unreviewed_complete":
        record["unreviewed"] = ["Missing consumer"]
    elif failure in {"unread", "unavailable"}:
        record["evidence"][0]["read_status"] = failure
    elif failure == "no_diff":
        record["evidence"][0]["kind"] = "source"
    elif failure == "no_evidence":
        record["evidence"] = []
    elif failure == "unbound_evidence":
        record["evidence"][0]["identity"] = None
    elif failure == "short_head":
        record["target"]["head"] = "a" * 7
    elif failure == "staged_no_digest":
        record["target"].update(kind="staged", comparison="staged", included_change_classes=["staged"])
    elif failure == "wrong_classes":
        record["target"]["included_change_classes"] = ["staged"]
    elif failure == "branch_no_base":
        record["target"].update(kind="branch", comparison="range", base=None)
    elif failure == "wrong_staged_comparison":
        record["target"].update(kind="staged", snapshot_digest="d" * 64, included_change_classes=["staged"])
    elif failure == "unstaged_with_staged":
        record["target"].update(kind="working_tree", comparison="unstaged", snapshot_digest="d" * 64,
                                included_change_classes=["staged", "unstaged"])
    assert not validator.is_valid(record)


def test_review_findings_consumer_disposition_and_incomplete_rules(review_findings_contract):
    validator, record = review_findings_contract
    finding = {
        "id": "F-001", "severity": "high", "category": "introduced_breakage",
        "location": {"path": "api.py", "line": 42, "side": "base"},
        "changed_cause": {"summary": "Deleted API keyword", "evidence_refs": ["E-diff"]},
        "evidence_refs": ["E-diff", "E-caller"],
        "affected_consumer": {"path": "job.py", "line": 18, "evidence_refs": ["E-caller"]},
        "impact": "Job fails", "repair": "Preserve compatibility or update caller",
        "disposition": "open", "disposition_reason": "Caller uses removed keyword",
        "disposition_evidence_refs": [],
    }
    record["findings"] = [finding]
    record["evidence"].append({"id": "E-caller", "path": "job.py", "kind": "consumer", "side": "head",
                                "identity": "e" * 40, "line_start": 18, "line_end": 18, "read_status": "read"})
    assert not validator.is_valid(record)  # Open high finding cannot be ready.
    record["verdict"] = "blocked"
    validator.validate(record)
    consumer = finding["affected_consumer"]
    finding["affected_consumer"] = None
    assert not validator.is_valid(record)
    finding["affected_consumer"] = consumer
    finding["disposition"] = "accepted_risk"
    assert not validator.is_valid(record)  # A disposition needs evidence, not just a label.
    finding["disposition"] = "open"
    record.update(review_status="incomplete", verdict="unverifiable", unreviewed=["Binary not inspected"])
    validator.validate(record)  # Confirmed findings survive incomplete coverage.


def test_review_findings_schema_does_not_claim_reference_truth(review_findings_contract):
    validator, record = review_findings_contract
    # This is structurally valid even if a reviewer falsely asserts a read. Semantic
    # verification belongs to the reviewer/operator; schema success cannot prove it.
    validator.validate(record)
    assert "cannot prove actual reads" in validator.schema["description"]
