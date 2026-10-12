from __future__ import annotations

from pathlib import Path

import pytest

from intent_pipeline.uac_ssot import (
    audit_ssot_entries,
    build_ssot_handoff_contract,
    build_ssot_manifest_entry,
    load_ssot_entries,
    render_audit_table,
)


ROOT = Path(__file__).resolve().parents[1]


def test_audit_ssot_entries_reports_known_entries() -> None:
    audits = audit_ssot_entries(ROOT)
    slugs = {entry.slug for entry in audits}

    assert 'engos-meta-supercharge' in slugs
    assert 'engos-meta-uac-import' in slugs


def test_shipped_capabilities_are_skills_only() -> None:
    audits = audit_ssot_entries(ROOT)
    assert len(audits) == 33
    for audit in audits:
        assert audit.manifest['layers']['minimal']['capability_type'] == 'skill'
        assert all(name.endswith('_skill') for name in audit.expected_surface_names)


def test_architecture_entry_publishes_display_name_and_skill_surfaces() -> None:
    audits = {entry.slug: entry for entry in audit_ssot_entries(ROOT)}
    architecture = audits['engos-design-architecture']

    assert architecture.manifest['display_name'] == 'Architecture Studio'
    assert 'codex_agent' not in architecture.expected_surface_names
    assert 'kiro_agent' not in architecture.expected_surface_names
    assert 'gemini_skill' in architecture.expected_surface_names
    assert 'claude_skill' in architecture.expected_surface_names
    assert 'kiro_prompt' not in architecture.expected_surface_names


def test_render_audit_table_includes_headers() -> None:
    table = render_audit_table(audit_ssot_entries(ROOT))

    assert 'slug' in table.splitlines()[0]
    assert 'status' in table.splitlines()[0]


def test_audit_ssot_entries_include_manifest_and_fit_analysis() -> None:
    audits = audit_ssot_entries(ROOT)

    assert audits[0].manifest["manifest_version"] == "capability-fabric.v0"
    assert "fit_assessment" in audits[0].cross_analysis


def test_build_ssot_handoff_contract_is_advisory() -> None:
    payload = build_ssot_handoff_contract(ROOT)

    assert payload["advisory_only"] is True
    assert payload["capabilities"]


def test_audit_ssot_entries_persist_repo_relative_source_refs() -> None:
    audits = {entry.slug: entry for entry in audit_ssot_entries(ROOT)}
    architecture = audits["engos-design-architecture"].manifest["layers"]["minimal"]

    assert architecture["resources"] == ["ssot/engos-design-architecture.md"]
    assert architecture["source_provenance"]["normalized_source"] == "ssot/engos-design-architecture.md"


def test_build_ssot_manifest_entry_honors_install_target_frontmatter() -> None:
    entries = {entry.slug: entry for entry in load_ssot_entries(ROOT / "ssot")}
    manifest = build_ssot_manifest_entry(entries["engos-content-dynamic-html-presentations"], ROOT)
    install_target = manifest["layers"]["minimal"]["install_target"]

    assert install_target["recommended"] == "global"
    assert install_target["confidence"] == 1.0


def test_every_generated_routing_draft_revalidates_against_canonical_source():
    import json
    from intent_pipeline.skill_jobs import validate_routing_fitness, load_skill_job_map
    slugs=sorted(path.stem for path in (ROOT/'ssot').glob('*.md'))
    jobs=load_skill_job_map(ROOT/'.meta/skill-job-map.json',slugs)['skills']
    for slug in slugs:
        descriptor=json.loads((ROOT/'.meta/capabilities'/f'{slug}.json').read_text())
        assert descriptor['job_contract']==jobs[slug]
        validate_routing_fitness(descriptor['job_contract'],ROOT,slug)


def test_specify_change_generated_descriptor_exposes_the_specification_job() -> None:
    import json

    descriptor = json.loads((ROOT / ".meta/capabilities/engos-design-specify-change.json").read_text())
    minimal = descriptor["layers"]["minimal"]
    inputs = minimal["required_inputs"]
    outputs = minimal["expected_outputs"]
    # Test the emitted descriptor, not only the source extractor: discovery and
    # handoff consumers need specification content rather than intake defaults.
    assert any("supplied design revision" in item for item in inputs)
    assert any("observed or reported failure" in item for item in inputs)
    assert any("scope/acceptance authority" in item for item in inputs)
    assert any("acceptance, unchanged behavior and priority" in item for item in outputs)
    assert any("dependent requirements held by unresolved material questions" in item for item in outputs)
    assert any("accepted revision if evidenced" in item for item in outputs)
    assert not {"source text", "user intent/context"}.intersection(inputs)
    assert not {"deterministic summary", "uplift payload", "capability recommendation", "deployment guidance"}.intersection(outputs)


def test_resource_modes_preserve_only_matching_curation_and_source_authority():
    from copy import deepcopy
    from intent_pipeline.uac_modes import extract_declared_modes, resolve_mode_entries
    source = extract_declared_modes('example', '## Modes\n### Keep\n### New\n')
    prior = deepcopy(source[0])
    prior.update(mode_summary='Curated behavior', required_inputs=['contract'], expected_outputs=['plan'], examples=['example'], uplift_notes=['boundary'], source_line=99, source_refs=['old.md'], invocations=['/old'])
    removed = dict(prior, mode_slug='removed', display_name='Removed')
    result = resolve_mode_entries(source, [prior, removed], 'example')
    assert [m['mode_slug'] for m in result] == ['keep', 'new']
    assert result[0]['expected_outputs'] == ['plan']
    assert result[0]['source_line'] == 2
    assert result[0]['source_refs'] == ['ssot/example.md']
    assert result[0]['invocations'] == []
    assert result[1]['expected_outputs'] == []
    changed_identity = dict(prior, display_name='Different')
    assert resolve_mode_entries(source, [changed_identity], 'example')[0]['expected_outputs'] == []
    explicit = deepcopy(source)
    explicit[0]['expected_outputs'] = ['source output']
    assert resolve_mode_entries(explicit, [prior], 'example')[0]['expected_outputs'] == ['source output']
    assert resolve_mode_entries(source, [prior], 'example', authoritative_fields={('mode', 'keep'): {'expected_outputs'}})[0]['expected_outputs'] == []
    explicit_empty = deepcopy(source)
    explicit_empty[0].update(source_refs=[], invocations=[], source_line=0)
    empty_result = resolve_mode_entries(explicit_empty, [prior], 'example')[0]
    assert empty_result['source_refs'] == []
    assert empty_result['invocations'] == []
    assert empty_result['source_line'] == 0


def test_testing_modes_retain_curated_contract_in_canonical_and_five_packages():
    import json
    # Public per-mode contract: independently specified expected consumer outputs.
    expected = {
        'generate-unit-tests': ['test file', 'fixtures or mocks', 'coverage notes'],
        'generate-e2e-tests': ['journey tests', 'setup/teardown plan', 'diagnostic expectations'],
        'edge-cases': ['edge-case catalog', 'risk ranking', 'tests to add first'],
        'coverage-analysis': ['gap report', 'risk-based priorities', 'recommended next tests'],
    }
    slug = 'engos-quality-testing-review'
    canonical = json.loads((ROOT / '.meta/capabilities' / f'{slug}.json').read_text())
    assert {m['mode_slug']: m['expected_outputs'] for m in canonical['modes']} == expected
    for provider in ('codex', 'gemini', 'claude', 'kiro', 'grok'):
        packaged = json.loads((ROOT / f'.{provider}/skills' / slug / 'resources/capability.json').read_text())
        assert packaged['modes'] == canonical['modes']


@pytest.mark.parametrize('slug', ['engos-quality-testing-review', 'engos-design-architecture'])
def test_resource_mode_curation_survives_apply_and_builder_resolution(monkeypatch, slug):
    import importlib.util
    import json
    import sys
    from copy import deepcopy
    source = (ROOT / 'ssot' / f'{slug}.md').read_text()
    stored = json.loads((ROOT / '.meta/capabilities' / f'{slug}.json').read_text())
    canonical_path = ROOT / '.meta/capabilities' / f'{slug}.json'
    canonical_before = canonical_path.read_bytes()
    saved = []
    # Distinct contract values expose replacement by heading defaults on either path.
    curated = deepcopy(stored)
    fields = ('mode_summary', 'required_inputs', 'expected_outputs', 'examples', 'uplift_notes')
    for mode in curated['modes']:
        mode['mode_summary'] = 'Reviewed contract for ' + mode['mode_slug']
        for field in fields[1:]:
            mode[field] = [mode['mode_slug'] + ':' + field]
    loaded = []
    for name, filename in [('d7_apply_contract', 'uac-import.py'), ('d7_build_contract', 'build-surfaces.py')]:
        spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        monkeypatch.setattr(module, 'load_descriptor', lambda *args: deepcopy(curated))
        loaded.append(module)
    # resolve_descriptor persists through save_descriptor; capture that boundary.
    # Neither this integration check nor its read helpers may write repository files.
    monkeypatch.setattr(loaded[1], 'save_descriptor', lambda root, name, payload: saved.append((root, name, deepcopy(payload))))
    def reject_write(*args, **kwargs):
        raise AssertionError('resolver test attempted a filesystem write')
    monkeypatch.setattr(Path, 'write_text', reject_write)
    monkeypatch.setattr(Path, 'write_bytes', reject_write)
    applied, bound = loaded[0]._merge_existing_descriptor_for_apply(slug, stored, ssot_text=source, quality_result={'final_candidate_text': source})
    assert bound
    entry = next(e for e in load_ssot_entries(ROOT / 'ssot') if e.slug == slug)
    manifest = build_ssot_manifest_entry(entry, ROOT)
    built = loaded[1].resolve_descriptor(entry, manifest, stored['job_contract'])
    preview, _ = loaded[0]._build_descriptor_preview({'manifest': manifest, 'items': []}, quality_result={'final_candidate_text': source})
    assert len(saved) == 1 and saved[0] == (ROOT, slug, built)
    assert canonical_path.read_bytes() == canonical_before
    for output in (applied, built, preview):
        for actual, previous in zip(output['modes'], curated['modes'], strict=True):
            assert {f: actual[f] for f in fields} == {f: previous[f] for f in fields}
            assert actual['source_refs'] == [f'ssot/{slug}.md']
            heading = ('### `' + actual['mode_slug'] + '`') if slug == 'engos-design-architecture' else ('### ' + actual['display_name'])
            assert actual['source_line'] == source.splitlines().index(heading) + 1
            assert actual['invocations'] == []
