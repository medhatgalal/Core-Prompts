"""The portable catalog must prove historical bytes, not local claims."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def api():
    from core_install import catalog
    return catalog


def test_real_v1122_population_and_complete_agent_resources():
    catalog = api()
    specs = catalog.packages(catalog.load_catalog(ROOT))
    for provider in ("codex", "claude", "gemini", "kiro"):
        old = [p for p in specs if p["provider"] == provider and "v1.12.2" in p["releases"]]
        assert len([p for p in old if p["kind"] == "skill"]) == 24
        assert len([p for p in old if p["kind"] == "agent"]) == 11
        agent = next(p for p in old if p["kind"] == "agent" and p["slug"] == "auto-research")
        assert len(agent["roots"]) == 2
        assert any(name.endswith("bootstrap.py") for name in agent["files"])
        for name, identity in agent["files"].items():
            import hashlib
            blob = subprocess.check_output(["git", "show", f"v1.12.2:{name}"], cwd=ROOT)
            assert identity["sha256"] == hashlib.sha256(blob).hexdigest()
            assert identity["mode"] in (0o644, 0o755)


def test_retired_renamed_and_upstream_boundaries():
    catalog = api()
    specs = catalog.packages(catalog.load_catalog(ROOT))
    assert any(p["slug"] == "mentor" and p["successor"] is None for p in specs)
    assert any(p["slug"] == "autosearch" and p["successor"] == "engos-optimization-auto-research" for p in specs)
    assert any(p["slug"].startswith("engos-") and "v1.14.0" in p["releases"] for p in specs)
    assert any(p["slug"] == "engos-audit-opex-incident-review" and "v1.14.0" in p["releases"] for p in specs)
    assert not any(p["slug"] == "loopy" for p in specs)


def test_runtime_includes_pre_inventory_bundle_and_launcher():
    catalog = api()
    data = catalog.load_catalog(ROOT)
    import hashlib
    for rel in (".meta/manifest.json", "VERSION", "RELEASE_SOURCE.env", "scripts/deploy-surfaces.sh"):
        blob = subprocess.check_output(["git", "show", f"v1.12.2:{rel}"], cwd=ROOT)
        assert hashlib.sha256(blob).hexdigest() in {v["sha256"] for v in catalog.runtime_identities(data, rel)}
    assert catalog.runtime_identities(data, "update_core_prompts.sh")
    assert catalog.runtime_identities(data, "invented") == []


def test_portable_runtime_needs_no_git(monkeypatch):
    catalog = api()
    monkeypatch.setenv("PATH", "")
    data = catalog.load_catalog(ROOT)
    assert catalog.packages(data)
    assert catalog.runtime_identities(data, "VERSION")


@pytest.mark.parametrize("damage", [None, "bytes", "mode", "extra"])
def test_pinned_shaping_packages_upgrade_without_claiming_custom_files(tmp_path, damage):
    """A complete released package can upgrade; local changes stay protected."""
    from core_install import planner

    slugs = ("engos-design-shaping", "engos-quality-shaping-gate",
             "engos-delivery-diagram-contract-artifacts")
    target = tmp_path / "target"
    target.mkdir()
    for slug in slugs:
        prefix = f".grok/skills/{slug}"
        rows = subprocess.check_output(
            ["git", "ls-tree", "-r", "v1.16.4", "--", prefix], cwd=ROOT, text=True,
        ).splitlines()
        assert rows, f"missing pinned release fixture: {prefix}"
        for row in rows:
            meta, rel = row.split("\t", 1)
            path = target / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(subprocess.check_output(["git", "show", f"v1.16.4:{rel}"], cwd=ROOT))
            path.chmod(int(meta.split()[0], 8) & 0o777)

    changed_root = ".grok/skills/engos-design-shaping"
    entry = target / changed_root / "SKILL.md"
    if damage == "bytes":
        entry.write_bytes(entry.read_bytes() + b"\nUser customization.\n")
    elif damage == "mode":
        entry.chmod(0o600)
    elif damage == "extra":
        (target / changed_root / "user-notes.md").write_text("Keep my notes.\n")

    result = planner.plan(ROOT, target, dict(
        mode="install", providers=["grok"], kinds=["skill"], slugs=list(slugs), runtime=False,
    ))
    assert not result["blockers"]
    held = {item["slug"] for item in result["preserved"]}
    if damage is None:
        assert not held
        assert any(action["path"] == changed_root + "/SKILL.md" for action in result["actions"])
    else:
        assert held == {"engos-design-shaping"}
        assert not any(action["path"].startswith(changed_root + "/") for action in result["actions"])
    assert result["selection"] == [f"grok:skill:{slug}" for slug in sorted(slugs)]
    assert not any("/agents/" in action["path"] for action in result["actions"])


@pytest.mark.parametrize("corrupt", ["path", "hash", "mode", "schema", "root", "release"])
def test_invalid_catalog_fails_closed(tmp_path, corrupt):
    catalog = api()
    data = copy.deepcopy(catalog.load_catalog(ROOT))
    if corrupt == "path":
        data["runtime"]["../escape"] = next(iter(data["runtime"].values()))
    elif corrupt == "hash":
        next(iter(data["identities"].values()))["sha256"] = "spoof"
    elif corrupt == "mode":
        next(iter(data["identities"].values()))["mode"] = 0o777
    elif corrupt == "schema":
        data["schema"] = 200
    elif corrupt == "root":
        data["packages"][0]["roots"] = [".codex"]
    else:
        data["packages"][0]["releases"] = ["invented"]
    (tmp_path / ".meta/install-profiles").mkdir(parents=True)
    (tmp_path / catalog.CATALOG_PATH).write_text(json.dumps(data))
    with pytest.raises(ValueError):
        catalog.load_catalog(tmp_path)


def test_generator_rejects_unverified_tag_object(tmp_path):
    spec = importlib.util.spec_from_file_location("build_legacy_catalog", ROOT / "scripts/build-legacy-catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="tag object"):
        module.verified_releases(ROOT, {"refs/tags/v1.12.2": "0" * 40})
    actual = subprocess.check_output(["git", "rev-parse", "refs/tags/v1.12.2"], cwd=ROOT).decode().strip()
    with pytest.raises(ValueError, match="peeled commit"):
        module.verified_releases(ROOT, {"refs/tags/v1.12.2": actual, "refs/tags/v1.12.2^{}": "0" * 40})


def test_v1_16_3_receipt_only_membership_does_not_grant_receiptless_adoption(tmp_path):
    catalog = api()
    value = catalog.load_catalog(ROOT)
    assert value['releases']['v1.16.3'] == {'commit':'8e24429574d7348fca070170e2197a36d627cd2d','tag_object':'faa10b133ec38dea7ebc3376d3f59d17b4b02d59'}
    assert {p['slug'] for p in value['receipt_membership_packages']} == catalog.RECEIPT_PROOF_SLUGS
    assert not any(p['slug'] in catalog.RECEIPT_PROOF_SLUGS for p in catalog.packages(value))
    from core_install import planner, transaction
    target = tmp_path/'target';target.mkdir()
    for spec in catalog.membership_packages(value):
        if spec['provider'] != 'kiro' or spec['slug'] not in catalog.RECEIPT_PROOF_SLUGS:
            continue
        for rel, ident in spec['files'].items():
            content = subprocess.check_output(['git','show','8e24429574d7348fca070170e2197a36d627cd2d:'+rel],cwd=ROOT)
            path = target/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content);path.chmod(ident['mode'])
            assert transaction.identity(path) == ident
    plan = planner.plan(ROOT,target,{'mode':'repair','providers':['kiro'],'runtime':False})
    assert set(catalog.RECEIPT_PROOF_SLUGS) <= {p['slug'] for p in plan['preserved']}
    assert not any(a['path'].startswith('.kiro/') for a in plan['actions'])


@pytest.mark.parametrize('mutation',['proof-promoted','proof-duplicate','normal-duplicate','normal-authority'])
def test_adopt_src003_container_authority_cannot_be_promoted_or_duplicated(mutation):
    catalog=api()
    data=copy.deepcopy(catalog.load_catalog(ROOT))
    if mutation=='proof-promoted':
        data['packages'].append(copy.deepcopy(data['receipt_membership_packages'][0]))
    elif mutation=='proof-duplicate':
        data['receipt_membership_packages'].append(copy.deepcopy(data['receipt_membership_packages'][0]))
    elif mutation=='normal-duplicate':
        data['packages'].append(copy.deepcopy(data['packages'][0]))
    else:
        data['packages'][0]['authority']='receipt_membership_only'
    with pytest.raises(ValueError,match='authority|duplicate'):
        catalog.validate_catalog(data)
