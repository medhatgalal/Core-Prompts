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
