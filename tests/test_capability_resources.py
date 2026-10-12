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


# D2.S2: source authority and detached-package consistency are distinct checks.
def shared_fixture(repo: Path):
    import hashlib
    for slug in ('owner', 'consumer'):
        (repo / 'ssot').mkdir(exist_ok=True, parents=True)
        (repo / 'ssot' / f'{slug}.md').write_text(f'---\nname: {slug}\n---\n# {slug}\n')
        root = repo / 'sources/capability-resources' / slug
        root.mkdir(parents=True)
        save_manifest(root, {'schema_version': 'CapabilityResourceMap.v1', 'shared': [],
                             'routes': {'contract': ['schema.json']}, 'dependencies': {},
                             **({'shared_imports': ['contract-v1']} if slug == 'consumer' else {})})
    (repo / 'sources/capability-resources/owner/schema.json').write_text('{"type":"object"}\n')
    row = {'id': 'contract-v1', 'owner': 'owner', 'source': 'schema.json',
           'sha256': hashlib.sha256(b'{"type":"object"}\n').hexdigest(),
           'consumers': [{'slug': 'consumer', 'destination': 'schema.json'}]}
    registry = {'schema_version': 'SharedResourceImports.v1', 'imports': [row]}
    (repo / '.meta').mkdir()
    (repo / '.meta/shared-resource-imports.json').write_text(json.dumps(registry))
    return registry


def shared_load(repo):
    from intent_pipeline.capability_resources import load_capability_bundle
    return load_capability_bundle(repo, 'consumer', '', 'contract')


def detached_shared(repo, target):
    bundle = shared_load(repo)
    target.mkdir(parents=True)
    shutil.copyfile(repo / 'sources/capability-resources/consumer/resource-map.json', target / 'resource-map.json')
    for item in bundle['resources']:
        path = target / item['path']; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(item['content'].encode())
    (target / 'shared-resource-imports.json').write_text(json.dumps(bundle['shared_imports']))
    return bundle


def test_shared_package_is_detached_and_provenance_names_authored_owner(tmp_path):
    shared_fixture(tmp_path)
    detached = tmp_path / 'detached'
    bundle = detached_shared(tmp_path, detached)
    assert bundle['resources'][0]['source_path'] == 'sources/capability-resources/owner/schema.json'
    assert not (tmp_path / 'sources/capability-resources/consumer/schema.json').exists()
    (tmp_path / 'sources/capability-resources/owner/schema.json').write_text('owner changed')
    assert load_resource_bundle(detached, 'contract') == bundle
    with pytest.raises(ResourceContractError, match='digest'):
        shared_load(tmp_path)


@pytest.mark.parametrize('failure', ['owner_name', 'owner_absent', 'undeclared', 'digest', 'source_missing',
    'source_symlink', 'root_symlink', 'registry_symlink', 'manifest_symlink', 'traversal', 'absolute', 'duplicate_id',
    'duplicate_destination', 'collision', 'shadow', 'reserved', 'package_shadow', 'self_cycle', 'unknown', 'unused',
    'extra_field', 'duplicate_key', 'missing_dependency', 'unresolved_reference', 'local_cycle', 'source_reexport'])
def test_shared_registry_rejects_invalid_authority(tmp_path, failure):
    registry = shared_fixture(tmp_path); row = registry['imports'][0]
    owner = tmp_path / 'sources/capability-resources/owner'
    consumer = tmp_path / 'sources/capability-resources/consumer'
    if failure == 'owner_name': (tmp_path / 'ssot/owner.md').write_text('---\nname: wrong\n---\n')
    elif failure == 'owner_absent': (tmp_path / 'ssot/owner.md').unlink()
    elif failure == 'undeclared': save_manifest(owner, {'schema_version': 'CapabilityResourceMap.v1', 'shared': [], 'routes': {}, 'dependencies': {}})
    elif failure == 'digest': row['sha256'] = 'a' * 64
    elif failure == 'source_missing': (owner / 'schema.json').unlink()
    elif failure in ('source_symlink', 'manifest_symlink'):
        source = owner / ('schema.json' if failure == 'source_symlink' else 'resource-map.json')
        elsewhere = tmp_path / 'elsewhere'; source.rename(elsewhere); source.symlink_to(elsewhere)
    elif failure == 'root_symlink':
        elsewhere = tmp_path / 'elsewhere'; owner.rename(elsewhere); owner.symlink_to(elsewhere, target_is_directory=True)
    elif failure == 'traversal': row['source'] = '../schema.json'
    elif failure == 'absolute': row['source'] = '/schema.json'
    elif failure == 'duplicate_id': registry['imports'].append(dict(row))
    elif failure == 'duplicate_destination': row['consumers'].append(dict(row['consumers'][0]))
    elif failure == 'collision': row['consumers'].append({'slug': 'consumer', 'destination': 'schema.json/child'})
    elif failure == 'shadow': (consumer / 'schema.json').write_bytes((owner / 'schema.json').read_bytes())
    elif failure == 'reserved': row['consumers'][0]['destination'] = 'capability.json'
    elif failure == 'package_shadow':
        path = tmp_path / 'sources/skill-package-resources/consumer/resources/schema.json'; path.parent.mkdir(parents=True); path.write_text('shadow')
    elif failure == 'self_cycle': row['consumers'][0]['slug'] = 'owner'
    elif failure in ('unknown', 'unused', 'local_cycle', 'source_reexport'):
        manifest = json.loads((consumer / 'resource-map.json').read_text())
        if failure == 'unknown': manifest['shared_imports'] = ['unknown']
        elif failure == 'unused': manifest['shared_imports'] = []
        elif failure == 'local_cycle': manifest['dependencies'] = {'schema.json': ['schema.json']}
        else:
            other = dict(row, id='return-v1', owner='consumer', consumers=[{'slug': 'owner', 'destination': 'schema.json'}])
            registry['imports'].append(other)
            (consumer / 'schema.json').write_bytes((owner / 'schema.json').read_bytes())
        save_manifest(consumer, manifest)
    elif failure == 'extra_field': row['fallback'] = True
    elif failure == 'missing_dependency':
        manifest = json.loads((owner / 'resource-map.json').read_text()); manifest['dependencies'] = {'schema.json': ['dep.md']}
        (owner / 'dep.md').write_text('dependency'); save_manifest(owner, manifest)
    elif failure == 'unresolved_reference':
        import hashlib
        raw = b'read resources/absent.md'; (owner / 'schema.json').write_bytes(raw); row['sha256'] = hashlib.sha256(raw).hexdigest()
    path = tmp_path / '.meta/shared-resource-imports.json'; path.write_text(json.dumps(registry))
    if failure == 'duplicate_key': path.write_text('{"schema_version":1,"schema_version":2}')
    if failure == 'registry_symlink':
        elsewhere = tmp_path / 'elsewhere'; path.rename(elsewhere); path.symlink_to(elsewhere)
    with pytest.raises(ResourceContractError): shared_load(tmp_path)


@pytest.mark.parametrize('failure', ['missing_receipt', 'bytes', 'owner', 'id', 'destination', 'unknown_field', 'duplicate', 'undeclared', 'source_path', 'digest'])
def test_detached_imports_fail_closed(tmp_path, failure):
    shared_fixture(tmp_path); target = tmp_path / 'detached'; detached_shared(tmp_path, target)
    path = target / 'shared-resource-imports.json'; receipt = json.loads(path.read_text())
    if failure == 'missing_receipt': path.unlink()
    elif failure == 'bytes': (target / 'schema.json').write_text('tampered')
    else:
        binding = receipt['imports'][0]
        if failure == 'owner': binding['owner'] = 'consumer'
        elif failure == 'id': binding['id'] = 'other'
        elif failure == 'destination': binding['destination'] = 'capability.json'
        elif failure == 'unknown_field': receipt['trusted'] = True
        elif failure == 'duplicate': receipt['imports'].append(dict(binding))
        elif failure == 'undeclared': binding['destination'] = 'other.json'
        elif failure == 'source_path': binding['source'] = '../escape'
        elif failure == 'digest': binding['sha256'] = '0' * 64
        path.write_text(json.dumps(receipt))
    with pytest.raises(ResourceContractError): load_resource_bundle(target)


def test_shared_identity_binds_owner_but_excludes_unrelated_rows(tmp_path):
    registry = shared_fixture(tmp_path); before = shared_load(tmp_path)
    shutil.copytree(tmp_path / 'sources/capability-resources/owner', tmp_path / 'sources/capability-resources/other')
    (tmp_path / 'ssot/other.md').write_text('---\nname: other\n---\n')
    registry['imports'][0]['owner'] = 'other'
    (tmp_path / '.meta/shared-resource-imports.json').write_text(json.dumps(registry))
    after = shared_load(tmp_path)
    assert before['resources'][0]['sha256'] == after['resources'][0]['sha256']
    assert before['sha256'] != after['sha256']
    shutil.copytree(tmp_path / 'sources/capability-resources/consumer', tmp_path / 'sources/capability-resources/extra')
    (tmp_path / 'ssot/extra.md').write_text('---\nname: extra\n---\n')
    manifest_path = tmp_path / 'sources/capability-resources/extra/resource-map.json'
    manifest = json.loads(manifest_path.read_text()); manifest['shared_imports'] = ['extra-v1']; manifest_path.write_text(json.dumps(manifest))
    registry['imports'].append(dict(registry['imports'][0], id='extra-v1', owner='owner', consumers=[{'slug': 'extra', 'destination': 'schema.json'}]))
    (tmp_path / '.meta/shared-resource-imports.json').write_text(json.dumps(registry))
    assert shared_load(tmp_path) == after


def test_shared_explicit_dependency_closure(tmp_path):
    import hashlib
    registry = shared_fixture(tmp_path)
    for slug in ('owner', 'consumer'):
        root = tmp_path / 'sources/capability-resources' / slug
        manifest = json.loads((root / 'resource-map.json').read_text()); manifest['dependencies'] = {'schema.json': ['dep.md']}
        if slug == 'consumer': manifest['shared_imports'].append('dep-v1')
        else: (root / 'dep.md').write_text('shared dependency\n')
        save_manifest(root, manifest)
    registry['imports'].append({'id': 'dep-v1', 'owner': 'owner', 'source': 'dep.md', 'sha256': hashlib.sha256(b'shared dependency\n').hexdigest(), 'consumers': [{'slug': 'consumer', 'destination': 'dep.md'}]})
    (tmp_path / '.meta/shared-resource-imports.json').write_text(json.dumps(registry))
    assert paths(shared_load(tmp_path)) == ['dep.md', 'schema.json']


def test_uac_resource_admission_uses_canonical_imports(tmp_path):
    from intent_pipeline.uac_quality import _load_declared_capability_resource_texts
    shared_fixture(tmp_path)
    assert _load_declared_capability_resource_texts('consumer', '', repo_root=tmp_path) == ('{"type":"object"}\n',)


def test_no_import_hash_contract_remains_byte_equivalent(tmp_path):
    import hashlib
    write_bundle(tmp_path)
    bundle = load_resource_bundle(tmp_path, 'basis')
    identity = {'schema_version': 'CapabilityResourceBundle.v1',
                'manifest_sha256': hashlib.sha256((tmp_path / 'resource-map.json').read_bytes()).hexdigest(),
                'route': 'basis', 'resources': [{'path': p, 'sha256': hashlib.sha256((tmp_path / p).read_bytes()).hexdigest()} for p in ['shared.md', 'principles.md', 'basis.md']]}
    assert bundle['sha256'] == hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert 'shared_imports' not in bundle
    assert all(set(item) == {'path', 'sha256', 'content'} for item in bundle['resources'])


@pytest.mark.parametrize('registry_state', ['missing', 'empty', 'undeclared_consumer'])
@pytest.mark.parametrize('generated_sidecar', [False, True])
@pytest.mark.parametrize('entrypoint', ['canonical', 'preflight'])
def test_canonical_shared_import_never_falls_back_to_detached_receipt(tmp_path, registry_state, generated_sidecar, entrypoint):
    from intent_pipeline.capability_resources import validate_shared_resource_imports
    registry = shared_fixture(tmp_path)
    bundle = shared_load(tmp_path)
    consumer = tmp_path / 'sources/capability-resources/consumer'
    if generated_sidecar:
        (consumer / 'schema.json').write_bytes(bundle['resources'][0]['content'].encode())
        (consumer / 'shared-resource-imports.json').write_text(json.dumps(bundle['shared_imports']))
        assert load_resource_bundle(consumer, 'contract') == bundle
    path = tmp_path / '.meta/shared-resource-imports.json'
    if registry_state == 'missing':
        path.unlink()
    elif registry_state == 'empty':
        path.write_text(json.dumps({'schema_version': 'SharedResourceImports.v1', 'imports': []}))
    else:
        shutil.copytree(tmp_path / 'sources/capability-resources/owner', tmp_path / 'sources/capability-resources/other')
        (tmp_path / 'sources/capability-resources/other/schema.json').unlink()
        (tmp_path / 'ssot/other.md').write_text('---\nname: other\n---\n')
        manifest = json.loads((consumer / 'resource-map.json').read_text())
        save_manifest(tmp_path / 'sources/capability-resources/other', manifest)
        registry['imports'][0]['consumers'][0]['slug'] = 'other'
        path.write_text(json.dumps(registry))
    with pytest.raises(ResourceContractError):
        (shared_load if entrypoint == "canonical" else validate_shared_resource_imports)(tmp_path)


@pytest.mark.parametrize('content', [
    r'{"\u0024ref": "outside.json"}',
    r'{"properties":{"nested":{"\u0024ref":"outside.json"}}}',
    r'{"allOf":[{"\u0024dynamicRef":"outside.json"}]}',
    r'{"$dynamicRef":"outside.json"}',
    r'{"$ref":"outside.json"}',
])
def test_shared_json_references_are_decoded_before_rejection(tmp_path, content):
    import hashlib
    registry = shared_fixture(tmp_path)
    source = tmp_path / 'sources/capability-resources/owner/schema.json'
    source.write_text(content)
    registry['imports'][0]['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    (tmp_path / '.meta/shared-resource-imports.json').write_text(json.dumps(registry))
    with pytest.raises(ResourceContractError, match='closure'):
        shared_load(tmp_path)
