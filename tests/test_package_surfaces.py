from __future__ import annotations

import subprocess
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = ROOT / "scripts" / "package-surfaces.sh"


def test_package_version_must_match_version_file(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(PACKAGE_SCRIPT), "--version", "v0.0.0", "--output-dir", str(tmp_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    assert result.returncode != 0
    assert "must match repo VERSION" in result.stdout


def test_package_boundary_includes_release_watch_contract(tmp_path: Path) -> None:
    retired_repo_paths = (
        ROOT / ".codex" / "skills" / "mentor",
        ROOT / ".codex" / "agents" / "resources" / "mentor",
        ROOT / ".gemini" / "skills" / "mentor",
        ROOT / ".gemini" / "agents" / "resources" / "mentor",
        ROOT / ".claude" / "skills" / "mentor",
        ROOT / ".claude" / "agents" / "resources" / "mentor",
        ROOT / ".kiro" / "skills" / "mentor",
        ROOT / ".kiro" / "agents" / "resources" / "mentor",
        ROOT / "sources" / "ssot-baselines" / "mentor",
    )
    assert all(not path.exists() for path in retired_repo_paths)

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    result = subprocess.run(
        [str(PACKAGE_SCRIPT), "--version", version, "--output-dir", str(tmp_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )

    tar_path = tmp_path / f"core-prompts-{version}-surfaces.tar.gz"
    zip_path = tmp_path / f"core-prompts-{version}-surfaces.zip"
    assert tar_path.is_file(), result.stdout
    assert zip_path.is_file(), result.stdout

    with tarfile.open(tar_path, "r:gz") as archive:
        tar_names = set(archive.getnames())
    with zipfile.ZipFile(zip_path) as archive:
        zip_names = set(archive.namelist())

    expected = {
        "VERSION",
        "RELEASE_SOURCE.env",
        ".meta/evaluation-policy.json",
        ".meta/instruction-clarity.json",
        ".meta/skill-job-map.json",
        "docs/CAPABILITY-EVALUATION.md",
        "docs/SKILL-JOB-MAP.md",
        "scripts/eng-report.py",
        "scripts/update-core-prompts.py",
        "scripts/deploy-surfaces.sh",
        "scripts/deploy-profile.py",
        ".meta/install-profiles/codex-kiro-grok.json",
        "scripts/install-local.sh",
    }
    assert expected <= tar_names
    assert expected <= zip_names

    retired_package_paths = (
        "skills/opex-briefing/",
        "sources/retired/opex-briefing/",
        ".codex/skills/mentor/",
        ".codex/agents/mentor.toml",
        ".codex/agents/resources/mentor/",
        ".gemini/skills/mentor/",
        ".gemini/agents/mentor.md",
        ".gemini/agents/resources/mentor/",
        ".claude/skills/mentor/",
        ".claude/agents/mentor.md",
        ".claude/agents/resources/mentor/",
        ".kiro/skills/mentor/",
        ".kiro/agents/mentor.json",
        ".kiro/agents/resources/mentor/",
        "sources/ssot-baselines/mentor/",
    )
    for names in (tar_names, zip_names):
        assert not any(
            name == retired.rstrip("/") or name.startswith(retired)
            for name in names
            for retired in retired_package_paths
        )


def test_packaged_profile_updates_verified_release_and_rolls_back(tmp_path: Path) -> None:
    """No checkout fallback: run only the extracted distribution in a disposable home."""
    import importlib.util
    import json
    import shutil
    import sys
    version = (ROOT / "VERSION").read_text().strip()
    artifacts = tmp_path / 'artifacts'
    subprocess.run([str(PACKAGE_SCRIPT), '--version', version, '--output-dir', str(artifacts)],
                   cwd=ROOT, check=True, capture_output=True)
    home = tmp_path / 'home'; support = home / '.core-prompts-updater'
    support.mkdir(parents=True)
    with tarfile.open(artifacts / f'core-prompts-{version}-surfaces.tar.gz') as archive:
        archive.extractall(support, filter='data')
    spec = importlib.util.spec_from_file_location('packaged_profile', support / 'scripts/deploy-profile.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    manifest = json.loads((support / '.meta/manifest.json').read_text())
    slug = next(e['slug'] for e in manifest['ssot_sources'] if 'codex_skill' in e['expected_surface_names'])
    profile = {'schema': 1, 'scope': 'skills', 'targets': ['codex', 'grok'], 'slugs': [slug], 'retire': [],
               'reader_evidence': '.meta/install-profiles/reader-fixture.json'}
    (support / profile['reader_evidence']).write_text('{"fixture":"separately verified reader contract"}')
    known = {}
    for target, item in module.desired_files(support, profile).items():
        if not target.startswith('.agents/'):
            continue
        legacy = item['source']; dst = home / legacy
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(support / legacy, dst)
        profile['retire'].append(legacy)
        known[legacy] = {'source': legacy, 'identity': module.snapshot(dst)}
    optional_view = support / 'dist/consumer-shell/local-view.json'
    optional_view.parent.mkdir(parents=True, exist_ok=True)
    optional_view.write_text('retained optional view')
    receipt = home / module.RECEIPT; receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({'schema': 1, 'owner': 'Core-Prompts', 'files': known}))
    plan = module.plan(support, home, profile)
    module.apply(support, home, profile, plan)
    assert (home / f'.agents/skills/{slug}/SKILL.md').is_file()
    assert not (home / f'.codex/skills/{slug}/SKILL.md').exists()
    updater = support / 'scripts/update-core-prompts.py'
    base = [sys.executable, str(updater), '--support-root', str(support), '--target-home', str(home)]
    ordinary = subprocess.run(base, cwd=tmp_path, text=True, capture_output=True)
    assert ordinary.returncode == 0, ordinary.stderr
    assert not (home / f'.codex/skills/{slug}/SKILL.md').exists()
    release_root = tmp_path / 'released-package'
    release_root.mkdir()
    with tarfile.open(artifacts / f'core-prompts-{version}-surfaces.tar.gz') as archive:
        tracked = set(subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines())
        members = [m for m in archive.getmembers() if m.name in tracked]
        archive.extractall(release_root, members=members, filter='data')
    assert not (release_root / 'dist').exists()
    (release_root / 'VERSION').write_text('v99.0.0\n')
    changed = release_root / f'.codex/skills/{slug}/SKILL.md'
    changed.write_text(changed.read_text() + '\nReleased update fixture.\n')
    module.install_bundle.build(release_root)
    state = {'installed_version': version, 'pending_version': 'v99.0.0', 'latest_version': 'v99.0.0',
             'status': 'pending-install', 'mirror_path': str(release_root),
             'verified_bundle_sha256': module.digest((release_root / '.meta/install-bundle.json').read_bytes())}
    # This pinned package receipt stands in for check_release's remote/tag verification.
    state_file = home / '.core-prompts-state/release-watch.json'
    state_file.write_text(json.dumps(state))
    skill = home / f'.agents/skills/{slug}/SKILL.md'
    prior = skill.read_bytes()
    skill.write_text('independent customization')
    negative = subprocess.run([*base, '--accept-release', '--yes'], cwd=tmp_path, text=True, capture_output=True)
    assert negative.returncode != 0
    assert 'customized' in negative.stderr
    assert skill.read_text() == 'independent customization'
    assert (support / 'VERSION').read_text().strip() == version
    skill.write_bytes(prior)
    release = subprocess.run([*base, '--accept-release', '--yes'], cwd=tmp_path, text=True, capture_output=True)
    assert release.returncode == 0, release.stderr
    assert skill.read_bytes() == changed.read_bytes()
    assert optional_view.read_text() == 'retained optional view'
    assert (support / 'VERSION').read_text().strip() == 'v99.0.0'
    assert not (home / f'.codex/skills/{slug}/SKILL.md').exists()
    assert json.loads(state_file.read_text())['status'] == 'current'
    assert json.loads(state_file.read_text())['verification_scope'] == 'managed_runtime'
    assert json.loads(state_file.read_text())['optional_views_status'] == 'retained_unverified'
    ordinary = subprocess.run(base, cwd=tmp_path, text=True, capture_output=True)
    assert ordinary.returncode == 0, ordinary.stderr
    assert not (home / f'.codex/skills/{slug}/SKILL.md').exists()
    saved = home / module.PROFILE
    saved_bytes = saved.read_bytes()
    altered = json.loads(saved_bytes); altered['targets'].append('kiro')
    saved.write_text(json.dumps(altered))
    widened = subprocess.run(base, cwd=tmp_path, text=True, capture_output=True)
    assert widened.returncode != 0 and 'scope' in widened.stderr
    assert not (home / '.kiro/skills' / slug).exists()
    saved.write_bytes(saved_bytes)
    polled = json.loads(state_file.read_text())
    polled.update(last_checked_at='later scheduled check', note='latest release observation')
    state_file.write_text(json.dumps(polled))
    restored = subprocess.run([*base, '--rollback', 'previous'], cwd=tmp_path, text=True, capture_output=True)
    assert restored.returncode == 0, restored.stderr
    assert (support / 'VERSION').read_text().strip() == version
    assert skill.read_bytes() == prior
    assert not (home / f'.codex/skills/{slug}/SKILL.md').exists()
    assert json.loads((home / module.PROFILE).read_text())['retire'] == []
    assert json.loads(state_file.read_text())['last_checked_at'] == 'later scheduled check'
    assert json.loads(state_file.read_text())['installed_version'] == version


def test_runtime_inventory_is_available_in_a_tagged_git_mirror() -> None:
    import json
    inventory = json.loads((ROOT / '.meta/install-bundle.json').read_text())['files']
    tracked = set(subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines())
    assert set(inventory) <= tracked
    assert not any(path.startswith('dist/') for path in inventory)
