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


# D2.S1: verify the portable specification contract, not requirement truth or behavior.
SPEC_RESOURCE_ROOT = Path(__file__).resolve().parents[1] / "sources/capability-resources/engos-design-specify-change"


def spec_contract_fixture(entry_order: str = "requirements_first") -> dict:
    return {
        "schema_version": "SpecContract.v1",
        "id": "export-results",
        "source_refs": [{"id": "issue", "ref": "issues/42"}],
        "authority_ref": None,
        "entry_order": entry_order,
        "requirements": [{
            "id": "REQ-1", "condition": "An authorized user exports filtered results",
            "behavior": "Export the matching records", "acceptance": ["Fixture rows match the filter"],
            "unchanged_behavior": ["Viewing results retains the active filter"], "priority": "undecided",
        }],
        "non_goals": ["Changing the filter UI"],
        "assumptions": [{"id": "A-1", "text": "Export size is acceptable", "status": "open"}],
        "design_refs": [],
    }


def spec_schema_validator():
    # jsonschema is a declared dependency on both CI providers; do not skip if absent.
    from jsonschema import Draft202012Validator
    schema = json.loads((SPEC_RESOURCE_ROOT / "schemas/spec-contract.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize("route", ["requirements_first", "design_first"])
def test_spec_schema_admits_pending_drafts_without_fabricated_authority(route: str) -> None:
    draft = spec_contract_fixture(route)
    assert not list(spec_schema_validator().iter_errors(draft))
    assert draft["authority_ref"] is None and draft["assumptions"][0]["status"] == "open"


def test_spec_bugfix_requires_current_expected_and_unchanged_behavior() -> None:
    draft = spec_contract_fixture("bugfix")
    validator = spec_schema_validator()
    assert list(validator.iter_errors(draft))
    draft["bug_context"] = {
        "current_behavior": "Two clicks reportedly create two invoices; reproduction pending",
        "expected_behavior": "The agreed same operation creates one invoice",
        "unchanged_behavior": ["Legitimate later submissions still work"],
    }
    assert not list(validator.iter_errors(draft))
    for field in draft["bug_context"]:
        broken = json.loads(json.dumps(draft))
        del broken["bug_context"][field]
        assert list(validator.iter_errors(broken)), field
    draft["bug_context"]["unchanged_behavior"] = []
    assert list(validator.iter_errors(draft))


@pytest.mark.parametrize("field", ["schema_version", "id", "source_refs", "authority_ref", "entry_order", "requirements", "non_goals", "assumptions", "design_refs"])
def test_spec_contract_requires_its_public_fields(field: str) -> None:
    draft = spec_contract_fixture()
    del draft[field]
    assert list(spec_schema_validator().iter_errors(draft))


@pytest.mark.parametrize("field,value", [
    ("id", "  "), ("condition", ""), ("behavior", "\t"), ("acceptance", []),
    ("unchanged_behavior", "preserve filters"), ("priority", "guessed-urgent"),
])
def test_spec_requirement_rejects_empty_or_mistyped_acceptance_contract(field: str, value) -> None:
    draft = spec_contract_fixture()
    draft["requirements"][0][field] = value
    assert list(spec_schema_validator().iter_errors(draft))


def test_spec_design_reference_requires_a_real_digest_shape() -> None:
    draft = spec_contract_fixture("design_first")
    draft["design_refs"] = [{"id": "D-1", "path": "design.md", "sha256": "a" * 64}]
    validator = spec_schema_validator()
    assert not list(validator.iter_errors(draft))
    for digest in ["unknown", "", "a" * 63, "g" * 64]:
        draft["design_refs"][0]["sha256"] = digest
        assert list(validator.iter_errors(draft))


def test_spec_schema_does_not_claim_id_uniqueness_or_semantic_approval() -> None:
    draft = spec_contract_fixture()
    duplicate = dict(draft["requirements"][0], behavior="A conflicting behavior")
    draft["requirements"].append(duplicate)
    # JSON Schema cannot enforce uniqueness of one property across array items.
    # This intentional admission requires the skill's separate semantic/ID review.
    validator = spec_schema_validator()
    assert not list(validator.iter_errors(draft))
    draft["approved"] = True
    assert list(validator.iter_errors(draft))


@pytest.mark.parametrize("route,selected", [
    ("requirements_first", "references/requirements-first.md"),
    ("design_first", "references/design-first.md"),
    ("bugfix", "references/bugfix.md"),
    ("contract", "schemas/spec-contract.schema.json"),
    ("trace_ledger", "templates/trace-matrix.json"),
])
def test_spec_routes_have_bounded_self_contained_resource_closure(route: str, selected: str) -> None:
    bundle = load_resource_bundle(SPEC_RESOURCE_ROOT, route)
    assert set(paths(bundle)) == {"templates/requirements.md", selected}
    assert bundle["delivery_claim"] == "assembled_not_proof_of_consumption"


def test_spec_resources_load_from_a_relocated_package(tmp_path: Path) -> None:
    package = tmp_path / "independent-install" / "resources"
    shutil.copytree(SPEC_RESOURCE_ROOT, package)
    helper = package / "scripts" / "load_module.py"
    helper.parent.mkdir()
    shutil.copy2(Path(__file__).resolve().parents[1] / "src/intent_pipeline/capability_resources.py", helper)
    result = subprocess.run(
        [sys.executable, str(helper), "--route", "design_first", "--format", "json"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    bundle = json.loads(result.stdout)
    assert set(paths(bundle)) == {"templates/requirements.md", "references/design-first.md"}
    assert bundle["sha256"] == load_resource_bundle(SPEC_RESOURCE_ROOT, "design_first")["sha256"]


def test_spec_trace_template_is_blank_and_makes_no_coverage_claim() -> None:
    ledger = json.loads((SPEC_RESOURCE_ROOT / "templates/trace-matrix.json").read_text())
    assert ledger["links"] == []
    assert ledger["assessment"] == {
        "link_validation": "not_assessed", "test_coverage": "not_assessed",
        "semantic_correctness": "not_assessed", "behavioral_verification": "not_assessed",
    }
    assert not (SPEC_RESOURCE_ROOT / "scripts/trace_check.py").exists()
    assert not (SPEC_RESOURCE_ROOT / "schemas/trace-result.schema.json").exists()
