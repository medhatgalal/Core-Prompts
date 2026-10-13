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
    text = '# Architecture\n## Mode Selection\n' + ''.join(f'### `{mode}`\nDesign this concern.\n' for mode in ['design-api', 'design-database', 'design-patterns', 'system-design'])
    entry_path.write_text(text)
    resource_root = tmp_path / 'sources/capability-resources' / slug; resource_root.mkdir(parents=True)
    (resource_root / 'resource-map.json').write_text(json.dumps({'schema_version': 'CapabilityResourceMap.v1', 'shared': [], 'routes': {'context': ['guide.md']}, 'dependencies': {}}))
    # Same slug, different entry_kind must coexist with the curated product mode.
    (resource_root / 'guide.md').write_text('## Module: /design-api\nFresh API context.\n## Module: /current\nFresh current context.\n')
    curated = [{'entry_kind': 'mode', 'mode_slug': mode, 'display_name': mode.replace('-', ' ').title().replace('Api', 'API'),
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
    actual_modes = [mode for mode in result['modes'] if mode['entry_kind'] == 'mode']
    assert [mode['mode_slug'] for mode in actual_modes] == [mode['mode_slug'] for mode in curated]
    for actual, prior in zip(actual_modes, curated, strict=True):
        assert actual['source_refs'] == [f'ssot/{slug}.md']
        assert actual['invocations'] == []
        assert actual['source_line'] == text.splitlines().index('### `' + actual['mode_slug'] + '`') + 1
        for field in ('mode_summary', 'required_inputs', 'expected_outputs', 'examples', 'uplift_notes'):
            assert actual[field] == prior[field]
    modules = [mode for mode in result['modes'] if mode['entry_kind'] == 'module']
    assert [mode['mode_slug'] for mode in modules] == ['design-api', 'current']
    assert all(mode['source_refs'] == [f'sources/capability-resources/{slug}/guide.md'] for mode in modules)
    assert len({(mode['entry_kind'], mode['mode_slug']) for mode in result['modes']}) == 6
    assert builder.resolve_descriptor(entry, manifest, {}) == result


def test_mode_selection_declarations_match_current_architecture_source():
    from intent_pipeline.uac_modes import extract_declared_modes
    slug = 'engos-design-architecture'
    source = (ROOT / 'ssot' / f'{slug}.md').read_text()
    modes = extract_declared_modes(slug, source)
    assert [m['mode_slug'] for m in modes if m['entry_kind'] == 'mode'] == [
        'design-api', 'design-database', 'design-patterns', 'system-design']


def test_mode_reconciliation_through_generator_and_uac_paths(tmp_path, monkeypatch):
    """Source changes and imported ownership reach all three descriptor boundaries."""
    import copy
    import importlib.util
    from types import SimpleNamespace
    from test_capability_resources import shared_fixture
    from intent_pipeline.uac_modes import extract_capability_modes

    registry = shared_fixture(tmp_path)
    slug = 'consumer'
    entry_path = tmp_path / 'ssot/consumer.md'
    owner_path = tmp_path / 'sources/capability-resources/owner/schema.json'
    owner_text = '## Module: /current\nFresh imported context.\n'
    owner_path.write_text(owner_text)
    registry['imports'][0]['sha256'] = hashlib.sha256(owner_text.encode()).hexdigest()
    (tmp_path / '.meta/shared-resource-imports.json').write_text(json.dumps(registry))
    names = ['design-api', 'design-database', 'design-patterns', 'system-design']
    original = '---\nname: consumer\n---\n# Architecture\n## Mode Selection\n' + ''.join(f'### `{name}`\nChoose this concern.\n' for name in names)
    curated = [{'entry_kind': 'mode', 'mode_slug': name, 'display_name': name.replace('-', ' ').title().replace('Api', 'API'),
                'source_refs': ['stale-source'], 'source_line': 999, 'invocations': ['/stale'],
                'mode_summary': 'Reviewed ' + name, 'required_inputs': ['reviewed input'],
                'expected_outputs': ['reviewed output'], 'examples': ['reviewed example'],
                'uplift_notes': ['reviewed note']} for name in names]
    curated += [{'entry_kind': 'mode', 'mode_slug': 'removed', 'display_name': 'removed'},
                {'entry_kind': 'module', 'mode_slug': 'stale-context', 'display_name': 'stale-context'}]
    stored = {'modes': curated}
    loaded = []
    for name, filename in [('foundation_mode_builder', 'build-surfaces.py'), ('foundation_mode_uac', 'uac-import.py')]:
        spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        monkeypatch.setattr(module, 'ROOT', tmp_path)
        monkeypatch.setattr(module, 'load_descriptor', lambda *args: copy.deepcopy(stored))
        loaded.append(module)
    builder, uac = loaded
    monkeypatch.setattr(builder, 'CAPABILITY_RESOURCE_SOURCE_DIR', tmp_path / 'sources/capability-resources')
    monkeypatch.setattr(builder, 'resolve_historical_baseline', lambda *args: SimpleNamespace(as_payload=lambda: {}, scenario_matrix=[]))
    saved = []
    monkeypatch.setattr(builder, 'save_descriptor', lambda *args: saved.append(copy.deepcopy(args[-1])))
    manifest = {'slug': slug, 'layers': {'minimal': {'summary': 'Architecture design'}}, 'expected_surface_names': ['codex_skill']}

    def boundaries(text):
        entry_path.write_text(text)
        entry = SimpleNamespace(slug=slug, display_name='Architecture', path=entry_path, body=text)
        built = builder.resolve_descriptor(entry, manifest, {})
        preview, _ = uac._build_descriptor_preview({'manifest': manifest, 'items': []}, quality_result={'final_candidate_text': text})
        applied, bound = uac._merge_existing_descriptor_for_apply(slug, {}, ssot_text=text, quality_result={'final_candidate_text': text})
        assert bound
        assert built['modes'] == preview['modes'] == applied['modes']
        assert saved[-1]['modes'] == built['modes']
        return built['modes']

    current = boundaries(original)
    assert [m['mode_slug'] for m in current if m['entry_kind'] == 'mode'] == names
    for mode in current[:4]:
        assert mode['source_refs'] == ['ssot/consumer.md']
        assert mode['source_line'] == original.splitlines().index('### `' + mode['mode_slug'] + '`') + 1
        assert mode['invocations'] == []  # Explicit current absence clears old invocations.
        assert mode['expected_outputs'] == ['reviewed output']
    assert current[-1]['source_refs'] == ['sources/capability-resources/owner/schema.json']
    assert current[-1]['source_line'] == 1
    assert current[-1]['invocations'] == ['/current']
    assert not {'removed', 'stale-context'} & {m['mode_slug'] for m in current}

    # Removed declarations drop; same slug with changed display identity must not inherit curation.
    changed = original.replace('### `system-design`\nChoose this concern.\n', '').replace('### `design-database`', '### design Database')
    # A moved source declaration refreshes source locations even when curation matches.
    changed = changed.replace('# Architecture\n', '# New preface\n# Architecture\n')
    updated = boundaries(changed)
    assert [m['mode_slug'] for m in updated if m['entry_kind'] == 'mode'] == names[:3]
    database = next(m for m in updated if m['mode_slug'] == 'design-database')
    assert database['display_name'] == 'design Database'
    assert database['expected_outputs'] == []
    api = next(m for m in updated if m['mode_slug'] == 'design-api' and m['entry_kind'] == 'mode')
    assert api['source_line'] == current[0]['source_line'] + 1
    assert api['expected_outputs'] == ['reviewed output']

    # Resource membership and invocations also obey current source, not stored modes.
    owner_text = '## Module: /replacement\nReplacement imported context.\n'
    owner_path.write_text(owner_text)
    registry['imports'][0]['sha256'] = hashlib.sha256(owner_text.encode()).hexdigest()
    (tmp_path / '.meta/shared-resource-imports.json').write_text(json.dumps(registry))
    final = boundaries(changed)
    assert [m['mode_slug'] for m in final if m['entry_kind'] == 'module'] == ['replacement']
    assert final[-1]['invocations'] == ['/replacement']
    assert final[-1]['source_refs'] == ['sources/capability-resources/owner/schema.json']
    assert extract_capability_modes(tmp_path, slug, changed)[-1]['source_refs'] == final[-1]['source_refs']

def test_actual_architecture_declarations_preserve_exact_curated_identity():
    from intent_pipeline.uac_modes import extract_capability_modes, resolve_mode_entries
    slug = 'engos-design-architecture'
    source = (ROOT / 'ssot' / f'{slug}.md').read_text()
    curated = json.loads((ROOT / '.meta/capabilities' / f'{slug}.json').read_text())['modes']
    actual = resolve_mode_entries(extract_capability_modes(ROOT, slug, source), curated, slug)
    modes = [m for m in actual if m['entry_kind'] == 'mode']
    assert [(m['mode_slug'], m['display_name']) for m in modes] == [(m['mode_slug'], m['display_name']) for m in curated]
    for mode, prior in zip(modes, curated, strict=True):
        assert mode['source_refs'] == [f'ssot/{slug}.md']
        assert mode['invocations'] == []
        for field in ('mode_summary', 'required_inputs', 'expected_outputs', 'examples', 'uplift_notes'):
            assert mode[field] == prior[field]


def test_instruction_seams_exact_source_metadata_conversion(tmp_path, monkeypatch):
    """Exercise the approved one-time normalization using actual source and fabric paths."""
    import copy
    import importlib.util
    from types import SimpleNamespace
    modules = []
    for name, script in [('seams_builder', 'build-surfaces.py'), ('seams_uac', 'uac-import.py')]:
        spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / script)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        monkeypatch.setattr(module, 'ROOT', tmp_path)
        modules.append(module)
    builder, uac = modules
    monkeypatch.setattr(builder, 'CAPABILITY_RESOURCE_SOURCE_DIR', tmp_path / 'sources/capability-resources')
    # Real baseline resolver and descriptor persistence operate in the isolated fixture.
    shutil.copytree(ROOT / 'sources/ssot-baselines', tmp_path / 'sources/ssot-baselines')
    (tmp_path / 'ssot').mkdir()
    (tmp_path / '.meta/capabilities').mkdir(parents=True)
    manifest_rows = json.loads((ROOT / '.meta/manifest.json').read_text())
    if isinstance(manifest_rows, dict):
        manifest_rows = manifest_rows['ssot_sources']
    for slug, route, expected_count in [('engos-reconciliation-converge', 'source-conflict', 0),
                                         ('engos-audit-pitch-review', 'standalone-pitch', 9)]:
        candidate = ROOT / 'reports/program-instruction-seams' / f'{slug}-candidate.md'
        text = candidate.read_text() if candidate.exists() else (ROOT / 'ssot' / f'{slug}.md').read_text()
        path = tmp_path / 'ssot' / f'{slug}.md'
        path.write_text(text)
        resource_root = tmp_path / 'sources/capability-resources' / slug
        shutil.copytree(ROOT / 'sources/capability-resources' / slug, resource_root)
        stored_path = tmp_path / '.meta/capabilities' / f'{slug}.json'
        prior = json.loads((ROOT / '.meta/capabilities' / f'{slug}.json').read_text())
        frozen = json.loads((ROOT / 'tests/fixtures/instruction-seams-metadata.json').read_text())[slug]
        prior['modes'] = frozen['original_modes']
        stored_path.write_text(json.dumps(prior))
        manifest = next(row for row in manifest_rows if row['slug'] == slug)
        entry = SimpleNamespace(slug=slug, display_name=manifest.get('display_name', slug), path=path, body=text)
        quality = {'final_candidate_text': text}
        preview, _ = uac._build_descriptor_preview({'manifest': manifest, 'items': []}, quality_result=quality)
        applied, bound = uac._merge_existing_descriptor_for_apply(slug, preview, ssot_text=text, quality_result=quality)
        assert bound
        for field in ('historical_baseline', 'quality_validation_matrix', 'job_contract'):
            assert applied[field] == prior[field]
        stored_path.write_text(json.dumps(applied))
        built = builder.resolve_descriptor(entry, manifest, prior['job_contract'])
        assert built['modes'] == applied['modes'] == preview['modes']
        assert len(built['modes']) == expected_count
        assert [[m['entry_kind'], m['mode_slug'], m['display_name']] for m in built['modes']] == frozen['expected_identities']
        assert all(m['entry_kind'] == 'command' and m['mode_slug'].startswith(slug + '-')
                   and m['invocations'] == [] for m in built['modes'])
        readback = json.loads(stored_path.read_text())
        assert readback == built
        for field in ('historical_baseline', 'quality_validation_matrix'):
            assert readback[field] == prior[field]
        assert builder.resolve_descriptor(entry, manifest, prior['job_contract']) == built
        repeated, bound = uac._merge_existing_descriptor_for_apply(slug, built, ssot_text=text, quality_result=quality)
        assert bound and repeated['modes'] == built['modes']
        # Detached resource closure: no sibling/repository access is needed for this route.
        detached = tmp_path / ('detached-' + slug)
        shutil.copytree(resource_root, detached)
        selected = load_resource_bundle(detached, route)
        assert [row['path'] for row in selected['resources']] == [f'examples/{route}.md']
        assert selected['resources'][0]['content'] == (detached / f'examples/{route}.md').read_text()
        if expected_count:
            assert '### `engos-audit-pitch-review components <source>`' in text
            # Source-matched curation survives; stale identity cannot inherit it.
            current = copy.deepcopy(built)
            current['modes'][0]['mode_summary'] = 'Reviewed source-grounded creation guidance'
            current['modes'].append(dict(current['modes'][0], mode_slug='pitch-stale', mode_summary='Unmatched curation'))
            stored_path.write_text(json.dumps(current))
            refreshed, _ = uac._build_descriptor_preview({'manifest': manifest, 'items': []}, quality_result=quality)
            assert refreshed['modes'][0]['mode_summary'] == current['modes'][0]['mode_summary']
            assert not any(m['mode_slug'] == 'pitch-stale' for m in refreshed['modes'])
            merged, bound = uac._merge_existing_descriptor_for_apply(slug, refreshed, ssot_text=text, quality_result=quality)
            assert bound and merged['modes'] == refreshed['modes']
            stored_path.write_text(json.dumps(merged))
            assert builder.resolve_descriptor(entry, manifest, prior['job_contract'])['modes'] == refreshed['modes']
        else:
            for control in ['/swot', '/mcda', '/scenarios', '/montecarlo', '/conflicts', '/lean', '/explore', '/help']:
                assert control in text
