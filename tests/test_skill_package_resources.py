from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).parents[1]


def test_loopy_preservation_snapshot():
    provenance = json.loads((ROOT / 'sources/intake/loopy/provenance.json').read_text())
    package = ROOT / 'sources/intake/loopy/package'
    actual = {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in package.rglob('*') if p.is_file()}
    assert actual == {name: item['sha256'] for name, item in provenance['files'].items()}
    assert len(actual) == 7
    assert 'agents/openai.yaml' in actual
    assert len([name for name in actual if name.startswith('references/')]) == 5


def test_package_resources_keep_relative_paths_and_modes(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('build_surfaces_package', ROOT / 'scripts/build-surfaces.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    source = tmp_path / 'sources/demo'
    source.mkdir(parents=True)
    for rel in ['references/a.md', 'agents/openai.yaml', 'scripts/run.py']:
        path = source / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('native package bytes')
        path.chmod(0o755 if rel.endswith('.py') else 0o644)
    monkeypatch.setattr(build, 'ROOT', tmp_path)
    monkeypatch.setattr(build, 'SKILL_PACKAGE_SOURCE_DIR', tmp_path / 'sources')
    monkeypatch.setattr(build, 'SURFACE_PATHS', {'grok_skill': lambda slug: tmp_path / '.grok/skills' / slug / 'SKILL.md'})
    copied = build.copy_skill_package_resources('grok_skill', 'demo')
    assert len(copied) == 3
    assert (tmp_path / '.grok/skills/demo/agents/openai.yaml').read_bytes() == (source / 'agents/openai.yaml').read_bytes()
    assert (tmp_path / '.grok/skills/demo/scripts/run.py').stat().st_mode & 0o777 == 0o755


def test_grok_generated_packages_use_relative_descriptor_links():
    manifest = json.loads((ROOT / '.meta/manifest.json').read_text())
    assert manifest['surfaces']['grok_skill']
    for relative in manifest['surfaces']['grok_skill']:
        text = (ROOT / relative).read_text()
        assert 'Capability resource: `resources/capability.json`' in text
        assert (ROOT / relative).parent.joinpath('resources/capability.json').is_file()
