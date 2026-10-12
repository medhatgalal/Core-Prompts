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


def planner_resource_root() -> Path:
    return Path(__file__).parents[1] / 'sources/capability-resources/engos-design-plan-implementation'


def planner_validator():
    # Resolve the packaged sibling schema offline; no network or D2 checkout.
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    root = planner_resource_root()
    task = json.loads((root / 'schemas/task-contract.schema.json').read_text())
    plan = json.loads((root / 'schemas/task-plan.schema.json').read_text())
    Draft202012Validator.check_schema(task)
    Draft202012Validator.check_schema(plan)
    registry = Registry().with_resource('task-contract.schema.json', Resource.from_contents(task))
    return Draft202012Validator(plan, registry=registry)


def planner_fixture() -> dict:
    return {
        'schema_version': 'TaskPlan.v1', 'id': 'export-plan',
        'spec_ref': 'accepted-request.md', 'spec_sha256': None,
        'tracker_ref': 'existing-tracker/EXPORT-7', 'completed_task_ids': [],
        'unresolved': ['Source bytes unavailable; authority for execution pending.'],
        'tasks': [{
            'schema_version': 'TaskContract.v1', 'id': 'EXPORT-7',
            'outcome': 'Filtered export contains exactly the accepted rows and columns.',
            'requirement_ids': ['REQ-1'], 'design_ids': [], 'depends_on': [],
            'consumes': [{'path': 'accepted-request.md', 'sha256': None}],
            'produces': ['export(filter) -> CSV with accepted columns'],
            'likely_files': ['src/export.py'], 'allowed_writes': [],
            'constraints': ['Preserve filter semantics'],
            'verification': [{'id': 'CHECK-1', 'oracle': 'CSV rows equal filtered fixture rows',
                              'command_or_inspection': 'Inspect fixture comparison result'}],
            'stop_condition': 'Hold execution until source and authority are verified',
            'authority_ref': None,
        }],
    }


def test_planner_resource_routes_include_local_schema_closure():
    root = planner_resource_root()
    assert paths(load_resource_bundle(root, 'task_plan')) == [
        'schemas/task-contract.schema.json', 'schemas/task-plan.schema.json',
    ]
    assert paths(load_resource_bundle(root, 'task_contract')) == ['schemas/task-contract.schema.json']
    assert paths(load_resource_bundle(root, 'dependency_map')) == ['templates/dependency-map.json']
    assert set(paths(load_resource_bundle(root))) == {
        'schemas/task-contract.schema.json', 'schemas/task-plan.schema.json', 'templates/dependency-map.json',
    }


def test_planner_schemas_allow_pending_plain_requirements_without_d2_or_new_tracker():
    plan = planner_fixture()
    planner_validator().validate(plan)
    plan['tracker_ref'] = None  # Chat-only planning requires no new tracker.
    plan['completed_task_ids'] = ['EXPORT-7']  # Historical evidence stays in the actual tracker.
    planner_validator().validate(plan)


@pytest.mark.parametrize('mutation', ['missing_oracle', 'missing_authority', 'bad_digest',
                                     'empty_requirements', 'blank_outcome', 'extra_execution'])
def test_planner_schemas_reject_incomplete_or_misleading_shapes(mutation: str):
    from jsonschema import ValidationError
    plan = planner_fixture()
    task = plan['tasks'][0]
    if mutation == 'missing_oracle':
        del task['verification'][0]['oracle']
    elif mutation == 'missing_authority':
        del task['authority_ref']
    elif mutation == 'bad_digest':
        task['consumes'][0]['sha256'] = 'not-observed'
    elif mutation == 'empty_requirements':
        task['requirement_ids'] = []
    elif mutation == 'blank_outcome':
        task['outcome'] = '  '
    else:
        task['dispatch_now'] = True
    with pytest.raises(ValidationError):
        planner_validator().validate(plan)


def test_planner_schema_does_not_claim_graph_or_acceptance_validation():
    # Deliberately shape-valid but semantically unready: those checks belong to
    # human/source review now and the separately scoped future graph checker.
    plan = planner_fixture()
    plan['tasks'][0]['depends_on'] = ['missing-task']
    plan['completed_task_ids'] = ['unknown-task']
    plan['tasks'].append(dict(plan['tasks'][0]))
    planner_validator().validate(plan)
