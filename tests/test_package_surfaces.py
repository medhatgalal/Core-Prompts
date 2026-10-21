from __future__ import annotations

import os
import hashlib
import json
import posixpath
import re
from urllib.parse import unquote, urlsplit
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest


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


def test_package_boundary_includes_release_watch_contract(
    tmp_path: Path, finalized_release_tree: Path
) -> None:
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

    repo = finalized_release_tree
    version = (repo / "VERSION").read_text(encoding="utf-8").strip()
    result = subprocess.run(
        [str(repo / "scripts/package-surfaces.sh"), "--version", version, "--output-dir", str(tmp_path)],
        cwd=repo,
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
        tar_files = {member.name for member in archive.getmembers() if member.isfile()}
    with zipfile.ZipFile(zip_path) as archive:
        zip_names = set(archive.namelist())
        zip_files = {member.filename for member in archive.infolist() if not member.is_dir()}

    expected = {
        "VERSION",
        "RELEASE_SOURCE.env",
        ".meta/evaluation-policy.json",
        ".meta/instruction-clarity.json",
        ".meta/skill-job-map.json",
        "docs/CAPABILITY-EVALUATION.md",
        "docs/SKILL-JOB-MAP.md",
        ".meta/intent-routing.json",
        ".kiro/steering/skill-routing.md",
        ".kiro/steering/intent-routing.json",
        "docs/INTENT-ROUTING.md",
        "docs/GUIDE-HOSTING.md",
        "docs/guide/index.html",
        "docs/guide/intent-flow.svg",
        "docs/engos-design-shaping.md",
        "docs/FRONTIER-MODERNIZATION.md",
        "scripts/eng-report.py",
        "scripts/update-core-prompts.py",
        "scripts/deploy-surfaces.sh",
        "scripts/deploy-profile.py",
        "scripts/core_install/planner.py",
        ".meta/install-profiles/legacy-installations.json",
        ".meta/install-profiles/codex-kiro-grok.json",
        "scripts/install-local.sh",
    }
    for provider in ("codex", "gemini", "claude", "kiro", "grok"):
        prefix = f".{provider}/skills/engos-debug-diagnose-failure"
        expected.add(f"{prefix}/SKILL.md")
        for resource in ("resource-map.json", "templates/hypothesis-evidence.md",
                         "templates/reproduction-receipt.json", "schemas/diagnosis-receipt.schema.json"):
            expected.add(f"{prefix}/resources/{resource}")
    assert expected <= tar_names
    assert expected <= zip_names
    for names in (tar_files, zip_files):
        assert not any(name.startswith(tuple(f".{p}/agents/" for p in ("codex", "claude", "gemini", "kiro")))
                       and not name.endswith("/") for name in names)
        assert sum(name.endswith("/SKILL.md") for name in names) == 5 * len(list((repo / "ssot").glob("*.md")))

    # Every provider ships the same owned receipt bytes in both archive formats.
    slug = "engos-delivery-implement-slice"
    resource_names = ("resource-map.json", "templates/slice-receipt.json",
                      "schemas/slice-receipt.schema.json")
    for archive_path, opener in ((tar_path, tarfile.open), (zip_path, zipfile.ZipFile)):
        with opener(archive_path) as archive:
            for provider in ("codex", "gemini", "claude", "kiro", "grok"):
                for resource in resource_names:
                    name = f".{provider}/skills/{slug}/resources/{resource}"
                    actual = (archive.extractfile(name).read() if isinstance(archive, tarfile.TarFile)
                              else archive.read(name))
                    assert actual == (repo / "sources/capability-resources" / slug / resource).read_bytes()

    # The shipped guide must resolve its local skill/resource links in both formats.
    import re
    for archive_path, names, opener in [(tar_path, tar_names, tarfile.open), (zip_path, zip_names, zipfile.ZipFile)]:
        with opener(archive_path) as archive:
            guide = (archive.extractfile("docs/FRONTIER-MODERNIZATION.md").read() if isinstance(archive, tarfile.TarFile)
                     else archive.read("docs/FRONTIER-MODERNIZATION.md")).decode()
        for link in re.findall(r"\]\(([^)]+)\)", guide):
            if "://" in link or link.startswith("#"):
                continue
            target = (ROOT / "docs" / link.split("#", 1)[0]).resolve().relative_to(ROOT).as_posix()
            assert target in names, (archive_path, link)

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
    for names in (tar_files, zip_files):
        assert not any(
            name == retired.rstrip("/") or name.startswith(retired)
            for name in names
            for retired in retired_package_paths
        )



SOURCE_MARKERS = (".meta/surface-rules.json", "scripts/build-surfaces.py", "scripts/validate-surfaces.py")
LAYOUT_RULES = ("AGENTS.md", ".kiro/steering/agent-behavior.md", ".kiro/steering/repo-workflow.md")


def assert_layout_instruction_contract(files: dict[str, bytes]) -> None:
    """Static clause/placement checks only: no claim about model routing behavior."""
    agents, behavior, workflow = (files[name].decode() for name in LAYOUT_RULES)
    flat = lambda text: " ".join(text.split())
    assert "## Execution context" in agents
    assert ".kiro/steering/agent-behavior.md#execution-context" in agents
    assert "source-checkout maintenance" in agents
    for steering in (behavior, workflow):
        assert steering.startswith("---\ninclusion: always\n---\n")
    assert "## Execution context" in behavior
    assert all(marker in behavior for marker in ("ssot/", *SOURCE_MARKERS))
    assert "Do not infer a distribution from missing `.git` alone." in behavior
    for clause in (
        "All canonical source markers must be absent",
        "runtime inventory verification must pass",
        "Incomplete or ambiguous layout",
        "separately verified complete source checkout",
        "project's own rules",
        "do not require Core-Prompts SSOT, UAC, build/validate, worktree or PR/MR prerequisites",
        "Safety, approvals, preservation and evidence boundaries apply in every context",
    ):
        assert clause in flat(behavior), clause
    assert "## Source-checkout-only guard" in workflow
    assert "agent-behavior.md#execution-context" in workflow
    assert "Do not apply the delivery sequence to ordinary skill use" in flat(workflow)
    # Preserve the source-maintainer contract instead of solving archive use by deleting it.
    for clause in ("isolated linked worktree from verified main", "bin/uac plan", "bin/uac judge"):
        assert clause in flat(agents + workflow), clause
    for clause in ("both remotes", "GitHub PR and GitLab MR", "post-merge checks",
                   "explicit review-only", "validation failures as blocking"):
        assert clause in flat(workflow), clause


@pytest.mark.parametrize("archive_format", ["tar", "zip"])
def test_packaged_primary_onboarding_links_resolve(
    tmp_path: Path, finalized_release_tree: Path, archive_format: str
) -> None:
    """Check actual shipped bytes, not the checkout that can mask missing members."""
    repo = finalized_release_tree
    version = (repo / "VERSION").read_text().strip()
    subprocess.run(
        [str(repo / "scripts/package-surfaces.sh"), "--version", version,
         "--output-dir", str(tmp_path / "artifacts")],
        cwd=repo, check=True, capture_output=True, text=True,
    )
    base = tmp_path / "artifacts" / f"core-prompts-{version}-surfaces"
    if archive_format == "tar":
        with tarfile.open(str(base) + ".tar.gz") as archive:
            files = {m.name: archive.extractfile(m).read()
                     for m in archive.getmembers() if m.isfile()}
    else:
        with zipfile.ZipFile(str(base) + ".zip") as archive:
            files = {m.filename: archive.read(m) for m in archive.infolist()
                     if not m.is_dir()}
    primary = ("README.md", "docs/GETTING-STARTED.md", "docs/EXAMPLES.md",
               "docs/SKILL-FLOWS.md", "docs/INSTALL-PROFILES.md", "AGENTS.md")
    errors = [f"missing primary guide: {name}" for name in primary if name not in files]
    for name in primary:
        if name not in files:
            continue
        assert files[name] == (repo / name).read_bytes(), name
        for link in re.findall(r"\]\(([^)]+)\)", files[name].decode()):
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue  # Source-only links are explicitly external, not archive claims.
            target = (posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path)))
                      if url.path else name)
            if url.path.endswith("/") and any(member.startswith(target + "/") for member in files):
                continue
            if target not in files:
                errors.append(f"{name}: {link} -> missing {target}")
                continue
            if url.fragment and target.endswith(".md"):
                headings = re.findall(r"^#{1,6} +(.+)$", files[target].decode(), re.M)
                anchors = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
                anchors.update(re.findall(r'<a\s+(?:id|name)=[\"]([^\"]+)', files[target].decode()))
                if unquote(url.fragment) not in anchors:
                    errors.append(f"{name}: {link} -> missing anchor")
    assert not errors, "\n".join(errors)

    # The copied full source has no .git, yet remains a source layout.
    assert not (repo / ".git").exists()
    assert (repo / "ssot").is_dir()
    assert all((repo / marker).is_file() for marker in SOURCE_MARKERS)
    source_rules = {name: (repo / name).read_bytes() for name in LAYOUT_RULES}

    # Actual distribution bytes omit canonical authoring inputs but carry a complete
    # independently checked runtime inventory. Keep the exact canonical instructions.
    assert not any(name.startswith("ssot/") for name in files)
    assert not any(marker in files for marker in SOURCE_MARKERS)
    inventory = json.loads(files[".meta/install-bundle.json"])
    assert {"VERSION", "scripts/install-local.sh", "scripts/deploy-profile.py",
            "scripts/install_bundle.py"} <= inventory["files"].keys()
    for name, identity in inventory["files"].items():
        assert hashlib.sha256(files[name]).hexdigest() == identity["sha256"], name
    assert {name: files[name] for name in LAYOUT_RULES} == source_rules
    assert_layout_instruction_contract(files)
    assert_layout_instruction_contract(source_rules)


def test_packaged_profile_updates_verified_release_and_rolls_back(
    tmp_path: Path, finalized_release_tree: Path
) -> None:
    """No checkout fallback: run only the extracted distribution in a disposable home."""
    import importlib.util
    import json
    import shutil
    import sys
    repo = finalized_release_tree
    version = (repo / "VERSION").read_text().strip()
    artifacts = tmp_path / 'artifacts'
    subprocess.run([str(repo / "scripts/package-surfaces.sh"), '--version', version, '--output-dir', str(artifacts)],
                   cwd=repo, check=True, capture_output=True)
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
    # A real regenerated release keeps both shared skill surfaces equivalent.
    (release_root / f'.gemini/skills/{slug}/SKILL.md').write_bytes(changed.read_bytes())
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
    assert negative.returncode == 2
    assert 'customized' in negative.stdout
    assert skill.read_text() == 'independent customization'
    assert (support / 'VERSION').read_text().strip() == 'v99.0.0'
    assert json.loads(state_file.read_text())['status'] == 'attention-required'
    skill.write_bytes(prior)
    # Resolve the custom package and reconcile using the already accepted runtime.
    release = subprocess.run(base, cwd=tmp_path, text=True, capture_output=True)
    assert release.returncode == 0, release.stderr
    assert skill.read_bytes() == changed.read_bytes()
    assert optional_view.read_text() == 'retained optional view'
    assert (support / 'VERSION').read_text().strip() == 'v99.0.0'
    assert not (home / f'.codex/skills/{slug}/SKILL.md').exists()
    assert json.loads((home / '.core-prompts-state/installation.json').read_text())['preserved'] == []
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
    # The old v1 profile is recovery history after promotion, not a second
    # active authority capable of expanding the v2 installation.
    assert widened.returncode == 0, widened.stderr
    assert not (home / '.kiro/skills' / slug).exists()
    saved.write_bytes(saved_bytes)
    polled = json.loads(state_file.read_text())
    polled.update(last_checked_at='later scheduled check', note='latest release observation')
    state_file.write_text(json.dumps(polled))
    restored = subprocess.run([*base, '--rollback', 'previous'], cwd=tmp_path, text=True, capture_output=True)
    assert restored.returncode == 0, restored.stderr
    # Undo clean package reconciliation before undoing partial release acceptance.
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


def test_package_rejects_unreleased_changes_before_archive_creation(tmp_path: Path) -> None:
    import shutil
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / ".meta").mkdir()
    shutil.copy2(PACKAGE_SCRIPT, repo / "scripts/package-surfaces.sh")
    (repo / ".meta/manifest.json").write_text("{}")
    (repo / "VERSION").write_text("v1.0.0\n")
    (repo / "CHANGELOG.md").write_text("## Unreleased\n\n- New behavior\n\n## v1.0.0 - 2026-01-01\n\n- Old release\n")
    result = subprocess.run([str(repo / "scripts/package-surfaces.sh"), "--version", "v1.0.0", "--output-dir", str(tmp_path / "out")], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Unreleased content" in result.stdout + result.stderr
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("existing_output", [False, True])
def test_stale_runtime_inventory_rejects_packaging_before_output_writes(
    tmp_path: Path, finalized_release_tree: Path, existing_output: bool
) -> None:
    repo = finalized_release_tree
    inventory = repo / ".meta/install-bundle.json"
    inventory_before = inventory.read_bytes()
    wrapper = repo / "scripts/install-local.sh"
    wrapper.write_text(wrapper.read_text() + "\n# Help-only drift must block packaging.\n")
    output = tmp_path / "artifacts"
    if existing_output:
        output.mkdir()
        (output / "sentinel.txt").write_text("preserve existing output\n")
    before = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    # The negative path must not depend on archive tools being installed.
    tools = tmp_path / "archive-tool-shims"
    tools.mkdir()
    marker = tmp_path / "archive-tool-invoked"
    for name in ("tar", "zip"):
        shim = tools / name
        shim.write_text('#!/bin/sh\nprintf invoked > "$ARCHIVE_TOOL_MARKER"\nexit 97\n')
        shim.chmod(0o755)
    env = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"],
               ARCHIVE_TOOL_MARKER=str(marker))
    version = (repo / "VERSION").read_text().strip()

    result = subprocess.run(
        [str(repo / "scripts/package-surfaces.sh"), "--version", version,
         "--output-dir", str(output)], cwd=repo, env=env,
        capture_output=True, text=True,
    )

    assert result.returncode != 0
    assert "standalone bundle identity mismatch: scripts/install-local.sh" in result.stdout + result.stderr
    assert inventory.read_bytes() == inventory_before
    assert not marker.exists()
    assert output.exists() == existing_output
    assert {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()} == before
