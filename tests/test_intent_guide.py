from pathlib import Path
import importlib.util
import json
import re
import shutil
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "intent_guide", ROOT / "scripts/build-intent-guide.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_generated_portable_guide_and_runtime_route_snapshot_are_current():
    assert (ROOT / "docs/guide/index.html").read_text() == m.render()
    assert (ROOT / "docs/guide/intent-flow.svg").read_text() == m.svg()
    assert (ROOT / ".kiro/steering/intent-routing.json").read_bytes() == (
        ROOT / ".meta/intent-routing.json"
    ).read_bytes()


def test_real_catalog_and_distinct_high_value_intents():
    p = m.payload()
    assert len(p["skills"]) == 36
    routes = {r["id"]: r for r in p["routes"]}
    expected = {
        "rough-problem": "engos-design-frame-from-vague",
        "unclear-feature": "engos-design-specify-change",
        "competing-proposals": "engos-reconciliation-converge",
        "shape-up": "engos-design-shaping",
        "small-change": "engos-delivery-implement-slice",
        "unexplained-failure": "engos-debug-diagnose-failure",
        "review-diff": "engos-quality-code-review",
        "review-pitch": "engos-audit-pitch-review",
    }
    assert {k: routes[k]["entry_skill"] for k in expected} == expected
    assert "engos-design-architecture" not in [
        s["skill"] for s in routes["small-change"]["steps"]
    ]
    assert routes["controller-delivery"]["entry_skill"] == "engos-orchestration-batman"


def fixture(tmp_path):
    for rel in [".meta/intent-routing.json", ".meta/skill-job-map.json"]:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, p)
    (tmp_path / "ssot").mkdir()
    for slug in json.loads((ROOT / ".meta/skill-job-map.json").read_text())["skills"]:
        (tmp_path / "ssot" / f"{slug}.md").write_text("fixture canonical entry")
    return tmp_path


@pytest.mark.parametrize(
    "fault", ["unknown-skill", "duplicate-id", "missing-prompt", "unsafe-id"]
)
def test_invalid_catalog_fails_instead_of_emitting_plausible_guidance(tmp_path, fault):
    root = fixture(tmp_path)
    p = root / ".meta/intent-routing.json"
    d = json.loads(p.read_text())
    if fault == "unknown-skill":
        d["routes"][0]["entry_skill"] = "engos-invented"
    if fault == "duplicate-id":
        d["routes"][1]["id"] = d["routes"][0]["id"]
    if fault == "missing-prompt":
        d["routes"][0]["prompt"] = ""
    if fault == "unsafe-id":
        d["routes"][0]["id"] = "../escape"
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError):
        m.payload(root)


def test_json_payload_cannot_close_the_script_element(tmp_path):
    root = fixture(tmp_path)
    p = root / ".meta/intent-routing.json"
    d = json.loads(p.read_text())
    attack = "</script><script>alert(1)</script>&"
    d["routes"][0]["intent"] = attack
    p.write_text(json.dumps(d))
    dest = root / "scripts/templates"
    dest.mkdir(parents=True)
    shutil.copyfile(
        ROOT / "scripts/templates/intent-guide.html", dest / "intent-guide.html"
    )
    page = m.render(root)
    embedded = page.split('id="routing-data">', 1)[1].split("</script>", 1)[0]
    assert "<" not in embedded and "&" not in embedded
    assert json.loads(embedded)["routes"][0]["intent"] == attack


def test_runtime_and_release_archive_boundaries_include_the_routing_inputs():
    inv = importlib.util.spec_from_file_location(
        "guide_bundle", ROOT / "scripts/install_bundle.py"
    )
    module = importlib.util.module_from_spec(inv)
    inv.loader.exec_module(module)
    for path in [
        ".kiro/steering/skill-routing.md",
        ".kiro/steering/intent-routing.json",
    ]:
        assert module.permitted(path)
    package = (ROOT / "scripts/package-surfaces.sh").read_text()
    for path in [
        ".meta/intent-routing.json",
        "docs/INTENT-ROUTING.md",
        "docs/GUIDE-HOSTING.md",
        "docs/guide",
    ]:
        assert '"' + path + '"' in package


def test_offline_template_does_not_load_remote_assets_or_classify_free_text():
    page = m.render()
    assert "<script src=" not in page and '<link rel="stylesheet"' not in page
    assert "connect-src" in page and "connect-src 'none'" in page
    script = page.rsplit("<script>", 1)[1].split("</script>", 1)[0]
    assert not re.search(r"\b(?:fetch|XMLHttpRequest|WebSocket|eval)\s*\(", script)
    assert "localStorage" not in script and "sessionStorage" not in script


def test_each_stage_has_its_own_result_and_handoff():
    routes = {r["id"]: r for r in m.payload()["routes"]}
    review = routes["small-change"]["steps"][1]
    assert review["skill"] == "engos-quality-code-review"
    assert "findings" in review["output"].lower()
    assert review["output"] != routes["small-change"]["output"]
    framing, specification = routes["rough-problem"]["steps"]
    assert framing["output"] != specification["output"]
    assert framing["next"] != specification["next"]
