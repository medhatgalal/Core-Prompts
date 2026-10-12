"""Every resource-backed skill must ship its complete bundle on every skill surface."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from intent_pipeline.capability_resources import load_resource_bundle, load_capability_bundle


ROOT = Path(__file__).resolve().parents[1]
SURFACES = ("codex", "gemini", "claude", "kiro", "grok")


def distributable_files(root: Path) -> list[Path]:
    # Match build-surfaces.copy_capability_resources: interpreter caches are
    # incidental local state, not distributable capability resources.
    return sorted(path for path in root.rglob('*') if path.is_file()
                  and '__pycache__' not in path.relative_to(root).parts
                  and path.suffix != '.pyc')


def test_resource_inventory_ignores_bytecode_not_real_resources(tmp_path: Path):
    (tmp_path / 'scripts/__pycache__').mkdir(parents=True)
    for name in ['scripts/helper.py', 'guide.md', 'scripts/loose.pyc', 'scripts/__pycache__/helper.pyc']:
        (tmp_path / name).write_text('fixture')
    assert [p.relative_to(tmp_path).as_posix() for p in distributable_files(tmp_path)] == ['guide.md', 'scripts/helper.py']


def test_resource_backed_skill_bundles_are_complete_and_installed_in_manifest():
    install_files = json.loads((ROOT / ".meta" / "install-bundle.json").read_text(encoding="utf-8"))["files"]
    canonical_roots = sorted(
        path.parent for path in (ROOT / "sources" / "capability-resources").glob("*/resource-map.json")
    )

    assert canonical_roots
    for canonical_root in canonical_roots:
        slug = canonical_root.name
        canonical_files = distributable_files(canonical_root)
        bundle = load_capability_bundle(ROOT, slug, (ROOT / "ssot" / f"{slug}.md").read_text())
        assert (ROOT / "ssot" / f"{slug}.md").is_file()

        for surface in SURFACES:
            generated_root = ROOT / f".{surface}" / "skills" / slug / "resources"
            if bundle and "shared_imports" in bundle:
                assert load_resource_bundle(generated_root) == bundle
                for relative in [i["path"] for i in bundle["resources"]] + ["shared-resource-imports.json"]:
                    data = (generated_root / relative).read_bytes()
                    assert install_files[f".{surface}/skills/{slug}/resources/{relative}"]["sha256"] == hashlib.sha256(data).hexdigest()
            for canonical in canonical_files:
                relative = canonical.relative_to(canonical_root)
                generated = generated_root / relative
                assert generated.is_file(), generated
                assert generated.read_bytes() == canonical.read_bytes(), generated

                manifest_entry = install_files.get(
                    f".{surface}/skills/{slug}/resources/{relative.as_posix()}"
                )
                assert manifest_entry, f"missing install entry for {generated}"
                assert manifest_entry["sha256"] == hashlib.sha256(canonical.read_bytes()).hexdigest()


def test_generated_resource_loaders_deliver_every_declared_route(tmp_path: Path):
    canonical_roots = sorted(
        path.parent for path in (ROOT / "sources" / "capability-resources").glob("*/resource-map.json")
    )

    for canonical_root in canonical_roots:
        slug = canonical_root.name
        routes = json.loads((canonical_root / "resource-map.json").read_text(encoding="utf-8"))["routes"]
        for surface in SURFACES:
            generated_root = ROOT / f".{surface}" / "skills" / slug / "resources"
            loader = generated_root / "scripts" / "load_module.py"
            assert loader.is_file(), loader
            for route in routes:
                result = subprocess.run(
                    [sys.executable, str(loader), "--route", route, "--format", "json"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert result.returncode == 0, result.stderr
                assert json.loads(result.stdout) == load_capability_bundle(ROOT, slug, (ROOT / "ssot" / f"{slug}.md").read_text(), route)


def test_generated_loader_blocks_missing_route_resources(tmp_path: Path):
    source = ROOT / ".codex" / "skills" / "engos-meta-supercharge" / "resources"
    copied = tmp_path / "resources"
    shutil.copytree(source, copied)
    (copied / "references/modules/catchup.md").unlink()

    result = subprocess.run(
        [sys.executable, str(copied / "scripts/load_module.py"), "--route", "/catchup", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "Resource assembly failed" in result.stderr


def test_shared_build_and_independent_validation_on_all_providers(tmp_path, monkeypatch):
    import importlib.util
    from test_capability_resources import shared_fixture, shared_load
    shared_fixture(tmp_path)
    loader_source = ROOT / 'src/intent_pipeline/capability_resources.py'
    loader_target = tmp_path / 'src/intent_pipeline/capability_resources.py'
    loader_target.parent.mkdir(parents=True); shutil.copyfile(loader_source, loader_target)
    def script(name):
        spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / f'{name}.py')
        module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
        monkeypatch.setattr(module, 'ROOT', tmp_path)
        return module
    builder = script('build-surfaces')
    monkeypatch.setattr(builder, 'CAPABILITY_RESOURCE_SOURCE_DIR', tmp_path / 'sources/capability-resources')
    monkeypatch.setattr(builder, 'RESOURCE_DIRS', {provider + '_skill': (lambda slug, provider=provider: tmp_path / f'.{provider}/skills/{slug}/resources') for provider in SURFACES})
    validator = script('validate-surfaces')
    expected = shared_load(tmp_path)
    for provider in SURFACES:
        copied = builder.copy_capability_resources(provider + '_skill', 'consumer')
        root = tmp_path / f'.{provider}/skills/consumer/resources'
        assert str((root / 'schema.json').relative_to(tmp_path)) in copied
        assert load_resource_bundle(root, 'contract') == expected
    assert validator.validate_shared_resource_delivery() == []
    detached = tmp_path / 'independent/resources'
    shutil.copytree(tmp_path / '.codex/skills/consumer/resources', detached)
    result = subprocess.run([sys.executable, str(detached / 'scripts/load_module.py'), '--route', 'contract', '--format', 'json'], capture_output=True, text=True, check=True, cwd=detached.parent)
    assert json.loads(result.stdout) == expected
    # A self-consistent forged receipt still fails canonical validation.
    receipt = tmp_path / '.codex/skills/consumer/resources/shared-resource-imports.json'
    data = json.loads(receipt.read_text()); data['imports'][0]['owner'] = 'forged-owner'; receipt.write_text(json.dumps(data))
    assert load_resource_bundle(receipt.parent, 'contract')['sha256'] != expected['sha256']
    assert any('canonical shared resource delivery drift' in e for e in validator.validate_shared_resource_delivery())


def test_missing_registry_is_blocked_before_builder_writes(tmp_path, monkeypatch):
    import importlib.util
    import pytest
    from intent_pipeline.capability_resources import ResourceContractError
    from test_capability_resources import shared_fixture, shared_load
    shared_fixture(tmp_path)
    bundle = shared_load(tmp_path)
    consumer = tmp_path / 'sources/capability-resources/consumer'
    (consumer / 'schema.json').write_bytes(bundle['resources'][0]['content'].encode())
    (consumer / 'shared-resource-imports.json').write_text(json.dumps(bundle['shared_imports']))
    (tmp_path / '.meta/shared-resource-imports.json').unlink()
    spec = importlib.util.spec_from_file_location('build_shared_preflight', ROOT / 'scripts/build-surfaces.py')
    builder = importlib.util.module_from_spec(spec); sys.modules[spec.name] = builder; spec.loader.exec_module(builder)
    monkeypatch.setattr(builder, 'ROOT', tmp_path)
    # Shared-resource validation must precede every remaining build phase.
    reached = []
    def unexpected_next_phase(root):
        reached.append(root)
        raise AssertionError('Shared-resource preflight did not stop the build')
    monkeypatch.setattr(builder, 'preflight_agent_emission', unexpected_next_phase)
    with pytest.raises(ResourceContractError):
        builder.main()
    assert reached == []
    assert all(not (tmp_path / f'.{provider}').exists() for provider in SURFACES)


def test_resource_conversion_preserves_curated_product_modes_and_refreshes_modules(tmp_path, monkeypatch):
    import copy
    import importlib.util
    from types import SimpleNamespace
    spec = importlib.util.spec_from_file_location('build_curated_modes', ROOT / 'scripts/build-surfaces.py')
    builder = importlib.util.module_from_spec(spec); sys.modules[spec.name] = builder; spec.loader.exec_module(builder)
    slug = 'engos-design-architecture'
    entry_path = tmp_path / 'ssot' / f'{slug}.md'; entry_path.parent.mkdir()
    text = '# Architecture\n## Modes\n### Design API\nDesign the API.\n'
    entry_path.write_text(text)
    resource_root = tmp_path / 'sources/capability-resources' / slug; resource_root.mkdir(parents=True)
    (resource_root / 'resource-map.json').write_text(json.dumps({'schema_version': 'CapabilityResourceMap.v1', 'shared': [], 'routes': {'context': ['guide.md']}, 'dependencies': {}}))
    # Same slug, different entry_kind must coexist with the curated product mode.
    (resource_root / 'guide.md').write_text('## Module: /design-api\nFresh API context.\n## Module: /current\nFresh current context.\n')
    curated = [{'entry_kind': 'mode', 'mode_slug': mode, 'display_name': mode,
                'source_refs': ['https://example.org/original/' + mode],
                'invocations': [], 'mode_summary': 'Curated behavior for ' + mode,
                'required_inputs': ['existing requirements'], 'expected_outputs': ['reviewed design'],
                'examples': ['preserved example'], 'uplift_notes': ['preserved decision']}
               for mode in ['design-api', 'design-database', 'design-patterns', 'system-design']]
    stored = {'modes': copy.deepcopy(curated) + [{'entry_kind': 'module', 'mode_slug': 'stale-context', 'mode_summary': 'Removed resource'}]}
    monkeypatch.setattr(builder, 'ROOT', tmp_path)
    monkeypatch.setattr(builder, 'CAPABILITY_RESOURCE_SOURCE_DIR', tmp_path / 'sources/capability-resources')
    monkeypatch.setattr(builder, 'load_descriptor', lambda root, name: copy.deepcopy(stored))
    monkeypatch.setattr(builder, 'resolve_historical_baseline', lambda root, name: SimpleNamespace(as_payload=lambda: {}, scenario_matrix=[]))
    def save(root, name, value):
        stored.clear(); stored.update(copy.deepcopy(value))
    monkeypatch.setattr(builder, 'save_descriptor', save)
    entry = SimpleNamespace(slug=slug, display_name='Architecture', path=entry_path, body=text)
    manifest = {'slug': slug, 'layers': {'minimal': {'summary': 'Architecture design'}}, 'expected_surface_names': ['codex_skill']}
    result = builder.resolve_descriptor(entry, manifest, {})
    assert [mode for mode in result['modes'] if mode['entry_kind'] == 'mode'] == curated
    modules = [mode for mode in result['modes'] if mode['entry_kind'] == 'module']
    assert [mode['mode_slug'] for mode in modules] == ['design-api', 'current']
    assert all(mode['source_refs'] == [f'sources/capability-resources/{slug}/guide.md'] for mode in modules)
    assert len({(mode['entry_kind'], mode['mode_slug']) for mode in result['modes']}) == 6
    assert builder.resolve_descriptor(entry, manifest, {}) == result
