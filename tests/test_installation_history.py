"""Historical-package acceptance tests; fixtures come from immutable Git trees.

These exercise the real planner and journal writer on disposable targets. The
source fixture keeps actual generated package bytes and the production catalog,
but limits the runtime inventory to the packages relevant to each scenario.
CI must fetch the release tags: missing history is a failure, never a skip.
"""
from functools import lru_cache
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install_bundle
from core_install import catalog, planner, transaction

ARCH = "engos-design-architecture"
REVIEW = "engos-quality-code-review"
# An explicit acceptance inventory, independent of the implementation's mapper.
V1122 = {
    "address-code-review": "engos-delivery-address-code-review",
    "analyze-context": "engos-memory-context-continuity",
    "architecture": ARCH,
    "auto-research": "engos-optimization-auto-research",
    "batman": "engos-orchestration-batman",
    "code-review": REVIEW,
    "codebase-health-audit": "engos-audit-code-health",
    "converge": "engos-reconciliation-converge",
    "demo-recorder": "engos-browser-demo-recorder",
    "docs-review-expert": "engos-quality-docs-review",
    "dynamic-html-presentations": "engos-content-dynamic-html-presentations",
    "eng-report": "engos-audit-engineering-progress",
    "feature-status": "engos-audit-feature-status",
    "gitops-review": "engos-quality-gitops-review",
    "ic-assistant": "engos-operations-ic-assistant",
    "instruction-editor": "engos-meta-instruction-editor",
    "pitch": "engos-audit-pitch-review",
    "pulse": "engos-triage-my-inbox-chat-pulse",
    "resolve-conflict": "engos-delivery-resolve-conflict",
    "supercharge": "engos-meta-supercharge",
    "testing": "engos-quality-testing-review",
    "threader": "engos-memory-threader",
    "uac-import": "engos-meta-uac-import",
    "weekly-intel": "engos-audit-weekly-intel",
}
V1122_AGENTS = {
    "architecture", "auto-research", "batman", "converge",
    "docs-review-expert", "gitops-review", "ic-assistant", "pitch",
    "pulse", "supercharge", "weekly-intel",
}


def put(root, relative, content, mode=0o644):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode() if isinstance(content, str) else content)
    path.chmod(mode)
    return path


@lru_cache(maxsize=None)
def history(tag, provider):
    """Read real bytes/modes, without trusting target-authored hash claims."""
    commit = subprocess.check_output(
        ["git", "rev-parse", tag + "^{commit}"], cwd=ROOT, text=True).strip()
    trusted = catalog.load_catalog(ROOT)
    assert commit == trusted["releases"][tag]["commit"]
    archive = subprocess.check_output(
        ["git", "archive", commit, f".{provider}/skills", f".{provider}/agents"],
        cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        # Git tracks only the executable bit. Archive permissions additionally
        # reflect tar.umask; materialize the canonical checkout modes.
        return {m.name: (tree.extractfile(m).read(), 0o755 if m.mode & 0o111 else 0o644)
                for m in tree.getmembers() if m.isfile()}


def historical(target, slug, kind="skill", provider="kiro", tag="v1.12.2"):
    root = f".{provider}/skills/{slug}/" if kind == "skill" else f".{provider}/agents/resources/{slug}/"
    ext = {"kiro": "json", "codex": "toml", "claude": "md", "gemini": "md"}[provider]
    entry = f".{provider}/agents/{slug}.{ext}"
    files = {r: v for r, v in history(tag, provider).items()
             if r.startswith(root) or (kind == "agent" and r == entry)}
    assert files, (tag, provider, kind, slug)
    for relative, (content, mode) in files.items():
        put(target, relative, content, mode)
    return files


@pytest.fixture
def source(tmp_path):
    def make(slugs=(ARCH,), providers=("kiro",)):
        repo = tmp_path / "source"
        repo.mkdir()
        manifest = json.loads((ROOT / ".meta/manifest.json").read_text())
        entries, resources = [], {}
        for entry in manifest["ssot_sources"]:
            if entry["slug"] not in slugs:
                continue
            names = [s for s in entry["expected_surface_names"]
                     if s.rsplit("_", 1)[0] in providers]
            entries.append({**entry, "expected_surface_names": names})
            for surface in names:
                provider, kind = surface.rsplit("_", 1)
                slug = entry["slug"]
                if kind == "skill":
                    prefix = f".{provider}/skills/{slug}/"
                    entrypoint = prefix + "SKILL.md"
                else:
                    ext = {"kiro": "json", "codex": "toml", "claude": "md", "gemini": "md"}[provider]
                    entrypoint = f".{provider}/agents/{slug}.{ext}"
                    prefix = f".{provider}/agents/resources/{slug}/"
                members = [r for r in manifest.get("resources", {}).get(surface, [])
                           if r.startswith(prefix)]
                resources.setdefault(surface, []).extend(members)
                for relative in [entrypoint, *members]:
                    destination = repo / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(ROOT / relative, destination)
        assert {e["slug"] for e in entries} == set(slugs)
        put(repo, ".meta/manifest.json", json.dumps({"ssot_sources": entries, "resources": resources}))
        for relative in (catalog.CATALOG_PATH, "VERSION", "scripts/deploy-profile.py", "scripts/update-core-prompts.py"):
            destination = repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        install_bundle.build(repo)
        install_bundle.verified(repo)
        return repo
    return make


@pytest.fixture
def target(tmp_path):
    path = tmp_path / "target"
    path.mkdir()
    return path


def execute(repo, target, **request):
    proposal = planner.plan(repo, target, request)
    assert not proposal["blockers"], proposal["blockers"]
    receipt = transaction.apply(repo, target, proposal,
                                lambda: planner.plan(repo, target, request))
    return proposal, receipt


def state(target):
    return json.loads((target / planner.STATE).read_text())


def assert_files(target, files):
    for relative, (content, mode) in files.items():
        assert (target / relative).read_bytes() == content, relative
        assert (target / relative).stat().st_mode & 0o777 == mode, relative


def test_all_24_skills_and_11_agents_migrate_without_receipt_or_updater(source, target):
    # Include later additions in the available catalog, proving repair never
    # turns the historical installation into an implicit install-everything.
    current_slugs = tuple(e["slug"] for e in json.loads(
        (ROOT / ".meta/manifest.json").read_text())["ssot_sources"])
    repo = source(current_slugs)
    for slug in V1122:
        historical(target, slug)
    for slug in V1122_AGENTS:
        historical(target, slug, "agent")
    assert len(list((target / ".kiro/skills").glob("*/SKILL.md"))) == 24
    assert len(list((target / ".kiro/agents").glob("*.json"))) == 11
    assert not (target / ".core-prompts-state").exists()
    assert not (target / "update_core_prompts.sh").exists()
    proposal, _ = execute(repo, target, mode="repair", providers=["kiro"])
    assert not proposal["preserved"], proposal["preserved"]
    expected = {f"kiro:skill:{s}" for s in V1122.values()}
    expected |= {f"kiro:agent:{V1122[s]}" for s in V1122_AGENTS}
    assert set(state(target)["selection"]) == expected
    assert set(state(target)["packages"]) == expected
    for package in state(target)["packages"].values():
        for relative in package["files"]:
            assert (target / relative).read_bytes() == (ROOT / relative).read_bytes(), relative
    for old, new in V1122.items():
        assert not (target / f".kiro/skills/{old}/SKILL.md").exists()
        assert (target / f".kiro/skills/{new}/SKILL.md").read_bytes() == (ROOT / f".kiro/skills/{new}/SKILL.md").read_bytes()
    for old in V1122_AGENTS:
        new = V1122[old]
        assert not (target / f".kiro/agents/{old}.json").exists()
        assert not list((target / f".kiro/agents/resources/{old}").rglob("*.*"))
        payload = json.loads((target / f".kiro/agents/{new}.json").read_text())
        for resource in payload["resources"]:
            if resource.startswith(("file://", "skill://")) and "*" not in resource:
                assert (target / resource.split("://", 1)[1]).is_file(), resource
    assert (target / "update_core_prompts.sh").stat().st_mode & 0o777 == 0o755
    for _ in range(2):
        repeat, _ = execute(repo, target, mode="sync")
        assert not repeat["actions"]
        assert set(state(target)["selection"]) == expected


def test_provider_isolation_even_with_other_provider_history_present(source, target):
    repo = source(providers=("kiro", "codex", "gemini", "claude"))
    historical(target, "architecture")
    outside = historical(target, "architecture", provider="codex")
    outside.update(historical(target, "architecture", "agent", provider="codex"))
    execute(repo, target, mode="repair", providers=["kiro"])
    assert_files(target, outside)
    assert state(target)["selection"] == [f"kiro:skill:{ARCH}"]
    assert not (target / ".agents").exists()
    assert not (target / ".gemini").exists()
    assert not (target / ".claude").exists()
    assert not (target / f".kiro/agents/{ARCH}.json").exists()


def test_older_autosearch_maps_directly_to_current_skill_without_agent_expansion(source, target):
    slug = "engos-optimization-auto-research"
    repo = source((slug, ARCH))
    historical(target, "autosearch", tag="v1.9.1")
    execute(repo, target, mode="repair", providers=["kiro"])
    assert not (target / ".kiro/skills/autosearch/SKILL.md").exists()
    assert (target / f".kiro/skills/{slug}/SKILL.md").read_bytes() == (ROOT / f".kiro/skills/{slug}/SKILL.md").read_bytes()
    assert state(target)["selection"] == [f"kiro:skill:{slug}"]
    assert not (target / ".kiro/agents").exists()
    assert not (target / f".kiro/skills/{ARCH}/SKILL.md").exists()


def test_agent_only_history_preserved_when_new_agent_requires_missing_skill(source, target):
    repo = source()
    before = historical(target, "architecture", "agent")
    proposal, _ = execute(repo, target, mode="repair", providers=["kiro"])
    assert_files(target, before)
    assert any("dependency" in item["reason"] for item in proposal["preserved"])
    assert not state(target)["packages"]
    assert not (target / ".kiro/skills").exists()
    assert not (target / f".kiro/agents/{ARCH}.json").exists()


@pytest.mark.parametrize("customization", ["successor", "hooks", "prompt", "extra-resource"])
def test_custom_agent_packages_and_their_legacy_resources_survive(source, target, customization):
    repo = source()
    before = historical(target, "architecture", "agent")
    historical(target, "architecture")
    if customization == "successor":
        custom = put(target, f".kiro/agents/{ARCH}.json", '{"name":"mine","prompt":"local successor"}\n')
    elif customization == "extra-resource":
        custom = put(target, ".kiro/agents/resources/architecture/local.md", "local notes\n")
    else:
        custom = target / ".kiro/agents/architecture.json"
        document = json.loads(custom.read_text())
        document[customization] = ({"agentSpawn": [{"command": "echo local"}]}
                                   if customization == "hooks" else "My personal prompt")
        custom.write_text(json.dumps(document))
        before[custom.relative_to(target).as_posix()] = (custom.read_bytes(), 0o644)
    custom_bytes = custom.read_bytes()
    proposal, _ = execute(repo, target, mode="repair", providers=["kiro"])
    assert proposal["preserved"]
    assert_files(target, before)
    assert custom.read_bytes() == custom_bytes
    assert f"kiro:agent:{ARCH}" not in state(target)["packages"]


def test_saved_schema1_scope_converts_then_explicit_repair_adopts_agents(source, target):
    repo = source((ARCH, REVIEW))
    old = historical(target, "architecture")
    agent = historical(target, "architecture", "agent")
    profile = {"schema": 1, "scope": "skills", "targets": ["kiro"], "slugs": ["architecture"]}
    put(target, planner.V1_PROFILE, transaction.encoded(profile))
    receipt = {"schema": 1, "owner": "Core-Prompts",
               "approved_profile_sha256": hashlib.sha256(transaction.encoded(profile)).hexdigest(),
               "files": {r: {"identity": transaction.identity(target / r)} for r in old},
               "bundle_files": {}}
    put(target, planner.V1_RECEIPT, transaction.encoded(receipt))
    execute(repo, target, mode="sync")
    assert state(target)["selection"] == [f"kiro:skill:{ARCH}"]
    assert_files(target, agent)
    execute(repo, target, mode="repair", providers=["kiro"])
    expected = {f"kiro:{kind}:{ARCH}" for kind in ("skill", "agent")}
    assert set(state(target)["packages"]) == expected
    assert set(state(target)["selection"]) == expected
    assert not (target / f".kiro/skills/{REVIEW}/SKILL.md").exists()
    for _ in range(2):
        execute(repo, target, mode="sync")
        assert set(state(target)["selection"]) == expected
    assert json.loads((target / planner.V1_PROFILE).read_text()) == profile


def test_rollback_restores_old_packages_resources_and_retired_mentor(source, target):
    repo = source()
    before = historical(target, "architecture")
    before.update(historical(target, "architecture", "agent"))
    before.update(historical(target, "mentor", tag="v1.10.2"))
    before.update(historical(target, "mentor", "agent", tag="v1.10.2"))
    untouched = put(target, ".kiro/steering/local.md", "stable project steering\n")
    _, receipt = execute(repo, target, mode="repair", providers=["kiro"])
    assert not (target / ".kiro/skills/mentor/SKILL.md").exists()
    assert not (target / ".kiro/agents/mentor.json").exists()
    transaction.rollback(target, receipt["transaction"])
    assert_files(target, before)
    assert not (target / f".kiro/skills/{ARCH}/SKILL.md").exists()
    assert not (target / f".kiro/agents/{ARCH}.json").exists()
    assert not (target / planner.STATE).exists()
    assert not (target / "update_core_prompts.sh").exists()
    assert untouched.read_text() == "stable project steering\n"


def test_target_manifest_cannot_legitimize_custom_historical_bytes(source, target):
    repo = source()
    historical(target, "architecture")
    custom = put(target, ".kiro/skills/architecture/SKILL.md", "custom arbitrary instructions\n")
    forged = {"schema": 1, "owner": "Core-Prompts", "scope": "standalone_runtime",
              "files": {".kiro/skills/architecture/SKILL.md": transaction.identity(custom)}}
    put(target, ".meta/install-bundle.json", json.dumps(forged))
    proposal, _ = execute(repo, target, mode="repair", providers=["kiro"])
    assert proposal["preserved"]
    assert custom.read_text() == "custom arbitrary instructions\n"
    assert not (target / f".kiro/skills/{ARCH}/SKILL.md").exists()
    assert not state(target)["packages"]


@pytest.mark.parametrize("dependency", ["skill", "agent-resource"])
def test_unknown_agent_references_keep_legacy_dependencies_stable(source, target, dependency):
    repo = source()
    before = historical(target, "architecture")
    before.update(historical(target, "architecture", "agent"))
    reference = (".kiro/skills/architecture/SKILL.md" if dependency == "skill"
                 else ".kiro/agents/resources/architecture/capability.json")
    custom = put(target, ".kiro/agents/personal.json", json.dumps({
        "name": "personal", "prompt": "Use this stable reference: " + reference,
        "resources": ["file://" + reference], "hooks": {}}))
    custom_bytes = custom.read_bytes()
    proposal, _ = execute(repo, target, mode="repair", providers=["kiro"])
    assert any("depends on legacy" in item["reason"] for item in proposal["preserved"])
    assert (target / reference).read_bytes() == before[reference][0]
    assert custom.read_bytes() == custom_bytes
