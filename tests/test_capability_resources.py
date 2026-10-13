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


D7_RESOURCE_ROOT = Path(__file__).parents[1] / "sources/capability-resources/engos-quality-testing-review"


def test_test_design_routes_deliver_schema_and_bind_oracle_edits(tmp_path: Path) -> None:
    shutil.copytree(D7_RESOURCE_ROOT, tmp_path / "design")
    root = tmp_path / "design"
    for route in ("unit", "e2e", "edge-cases", "coverage"):
        bundle = load_resource_bundle(root, route)
        assert set(paths(bundle)) == {"references/test-oracles.md", "templates/test-design.md", "schemas/test-design.schema.json"}
    before = load_resource_bundle(root, "unit")["sha256"]
    oracle = root / "references/test-oracles.md"
    oracle.write_text(oracle.read_text() + "\nAdditional fixture constraint.\n")
    assert load_resource_bundle(root, "unit")["sha256"] != before
    oracle.unlink()
    with pytest.raises(ResourceContractError):
        load_resource_bundle(root, "coverage")


def test_test_design_schema_allows_design_and_coverage_only_but_rejects_execution() -> None:
    from copy import deepcopy
    from jsonschema import Draft202012Validator

    schema = json.loads((D7_RESOURCE_ROOT / "schemas/test-design.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    coverage = {"schema_version": "TestDesign.v1", "id": "coverage-1", "requirement_ids": [], "tests": [], "execution_status": "not_run", "gaps": ["No coverage artifact supplied; source inspection only."]}
    validator.validate(coverage)
    design = deepcopy(coverage)
    design["requirement_ids"] = ["spec.md#expiry"]
    design["tests"] = [{"id": "expiry-equality", "requirements": ["spec.md#expiry"], "expected": "Reject at expiry equality", "oracle": "A > comparison accepts equality; rejection assertion catches it", "fixture": "Fixed clock at expiration", "negative_case": "Malformed token rejected", "boundary_case": "One tick before accepted; equality rejected", "command_source": "unknown: repository runner not supplied"}]
    validator.validate(design)
    for field in design["tests"][0]:
        invalid = deepcopy(design)
        del invalid["tests"][0][field]
        assert list(validator.iter_errors(invalid)), field
    for status in ("passed", "failed", "run", None):
        invalid = deepcopy(design)
        invalid["execution_status"] = status
        assert list(validator.iter_errors(invalid))
    invalid = deepcopy(design)
    invalid["coverage_percent"] = 100
    assert list(validator.iter_errors(invalid))
    # Shape validity deliberately cannot certify a meaningful oracle.
    weak = deepcopy(design)
    weak["tests"][0]["oracle"] = "A mock was called"
    validator.validate(weak)


SLICE_RESOURCES = (Path(__file__).resolve().parents[1]
                   / "sources/capability-resources/engos-delivery-implement-slice")


def slice_receipt_validator():
    from jsonschema import Draft202012Validator
    schema = json.loads((SLICE_RESOURCES / "schemas/slice-receipt.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def slice_receipt_template():
    return json.loads((SLICE_RESOURCES / "templates/slice-receipt.json").read_text())


def test_slice_receipt_optional_route_and_template():
    from intent_pipeline.capability_resources import load_capability_bundle
    bundle = load_capability_bundle(Path(__file__).resolve().parents[1],
                                    "engos-delivery-implement-slice", "", "receipt")
    assert paths(bundle) == ["schemas/slice-receipt.schema.json", "templates/slice-receipt.json"]
    receipt = slice_receipt_template()
    slice_receipt_validator().validate(receipt)
    assert receipt["checks"] == []
    assert receipt["task_generation"] is None
    assert receipt["task_contract_sha256"] is None
    assert receipt["unresolved_context"]
    assert not list(SLICE_RESOURCES.rglob("*.py"))


@pytest.mark.parametrize("status,exit_status,evidence,reason,valid", [
    ("passed", 0, "evidence/focused-test.log", None, True),
    ("passed", None, "evidence/focused-test.log", None, False),
    ("passed", 1, "evidence/focused-test.log", None, False),
    ("passed", 0, None, None, False),
    ("passed", 0, " ", None, False),
    ("failed", 1, "evidence/failure.log", "assertion failed", True),
    ("failed", 0, "evidence/failure.log", "assertion failed", False),
    ("failed", None, "evidence/failure.log", "unknown", False),
    ("failed", 1, None, "assertion failed", False),
    ("not_run", None, None, "not selected for this prose change", True),
    ("not_run", 0, None, "not selected", False),
    ("unavailable", None, None, "required runner is absent", True),
    ("unavailable", 127, None, "runner absent", False),
    ("unavailable", None, None, None, False),
])
def test_slice_receipt_cannot_relabel_missing_or_failed_execution(
    status, exit_status, evidence, reason, valid
):
    receipt = slice_receipt_template()
    receipt["checks"] = [{"command": "python -m pytest tests/test_expiry.py",
                          "exit_status": exit_status, "evidence_ref": evidence,
                          "status": status, "reason": reason}]
    assert slice_receipt_validator().is_valid(receipt) is valid


def test_slice_receipt_unknown_context_and_candidate_identity():
    validator = slice_receipt_validator()
    receipt = slice_receipt_template()
    receipt["unresolved_context"] = []
    assert not validator.is_valid(receipt)
    receipt["unresolved_context"] = ["Plain ask has no structured contract or generation."]
    receipt.update(target_kind="commit", base="a" * 40, head_or_snapshot_digest="b" * 40)
    validator.validate(receipt)
    receipt["target_kind"] = "dirty_snapshot"
    assert not validator.is_valid(receipt)  # HEAD alone cannot identify dirty bytes.
    receipt.update(head_or_snapshot_digest="c" * 64,
                   snapshot_method="sha256 of retained path/digest/deletion/mode manifest",
                   snapshot_evidence_ref="evidence/candidate-manifest.json",
                   changed_files=["src/expiry.py"], initial_dirty_files=["ui/draft.ts"])
    validator.validate(receipt)
    receipt["target_kind"] = None
    assert not validator.is_valid(receipt)


def test_slice_receipt_shape_is_not_execution_or_preservation_proof():
    receipt = slice_receipt_template()
    receipt["checks"] = [{"command": "example only", "exit_status": 0,
                          "evidence_ref": "nonexistent.log", "status": "passed", "reason": None}]
    # This passes deliberately: resolving evidence and checking semantic truth is
    # the consumer's responsibility, never a claim made by JSON Schema.
    slice_receipt_validator().validate(receipt)
    schema = json.loads((SLICE_RESOURCES / "schemas/slice-receipt.schema.json").read_text())
    assert "do not establish" in schema["description"]


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


DIAGNOSIS_ROOT = Path(__file__).resolve().parents[1] / "sources/capability-resources/engos-debug-diagnose-failure"


def test_diagnosis_routes_keep_optional_receipt_separate_and_close_dependencies() -> None:
    assert paths(load_resource_bundle(DIAGNOSIS_ROOT, "hypotheses")) == ["templates/hypothesis-evidence.md"]
    assert paths(load_resource_bundle(DIAGNOSIS_ROOT, "receipt")) == [
        "schemas/diagnosis-receipt.schema.json", "templates/reproduction-receipt.json"
    ]


def diagnosis_contract() -> tuple[dict, dict]:
    schema = json.loads((DIAGNOSIS_ROOT / "schemas/diagnosis-receipt.schema.json").read_text())
    receipt = json.loads((DIAGNOSIS_ROOT / "templates/reproduction-receipt.json").read_text())
    return schema, receipt


def test_diagnosis_receipt_accepts_explicit_unknown_without_fabricated_observations() -> None:
    import jsonschema
    schema, receipt = diagnosis_contract()
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(receipt, schema)
    assert receipt["cause_status"] == "unknown"
    assert receipt["observations"] == receipt["hypotheses"] == []


def test_diagnosis_receipt_requires_structural_support_for_identified() -> None:
    import jsonschema
    schema, receipt = diagnosis_contract()
    receipt["cause_status"] = "identified"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)
    receipt["observations"] = [{"command_redacted": "fixture: compare retained traces", "exit_status": None,
                                "environment": "isolated structural fixture", "evidence_ref": "fixture://trace"}]
    receipt["hypotheses"] = [{"id": "h1", "prediction": "one boundary differs", "discriminator": "compare boundaries",
                              "result": "fixture://trace: contrast observed", "status": "unresolved", "evidence_refs": []}]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)
    receipt["hypotheses"][0]["status"] = "supported"
    receipt["hypotheses"][0]["evidence_refs"] = ["fixture://trace"]
    jsonschema.validate(receipt, schema)  # Shape only; this fixture does not prove causal truth.


@pytest.mark.parametrize("field", ["subject_revision", "current_behavior", "expected_behavior", "unchanged_behavior",
                                  "observations", "hypotheses", "repair_scope", "next_owner",
                                  "conclusion", "investigated_scope", "remaining_uncertainty"])
def test_diagnosis_receipt_rejects_incomplete_handoff(field: str) -> None:
    import jsonschema
    schema, receipt = diagnosis_contract()
    del receipt[field]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)


@pytest.mark.parametrize("change", ["unredacted_field", "invented_status", "text_exit"])
def test_diagnosis_receipt_rejects_unsupported_contract_shapes(change: str) -> None:
    import jsonschema
    schema, receipt = diagnosis_contract()
    if change == "unredacted_field":
        receipt["raw_environment"] = "unapproved extra field"
    elif change == "invented_status":
        receipt["cause_status"] = "fixed"
    else:
        receipt["observations"] = [{"command_redacted": "fixture", "exit_status": "passed",
                                    "environment": "fixture", "evidence_ref": "fixture://trace"}]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)


@pytest.mark.parametrize("status", ["supported", "rejected", "unresolved"])
def test_diagnosis_hypothesis_reference_requirement_depends_on_status(status: str) -> None:
    import jsonschema
    schema, receipt = diagnosis_contract()
    hypothesis = {"id": "h1", "prediction": "fixture prediction", "discriminator": "fixture contrast",
                  "result": "structural fixture only", "status": status, "evidence_refs": []}
    receipt["hypotheses"] = [hypothesis]
    if status == "unresolved":
        jsonschema.validate(receipt, schema)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(receipt, schema)
    hypothesis["evidence_refs"] = ["fixture://observation"]
    jsonschema.validate(receipt, schema)  # Structural reference presence is not evidence authenticity.
    hypothesis["evidence_refs"] = [""]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)
    del hypothesis["evidence_refs"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)


@pytest.mark.parametrize("field", ["conclusion", "investigated_scope", "remaining_uncertainty"])
def test_diagnosis_receipt_requires_nonempty_summary_fields(field: str) -> None:
    import jsonschema
    schema, receipt = diagnosis_contract()
    receipt[field] = ""
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)
