#!/usr/bin/env python3
"""PUBLIC fixture integrity checks, not a model evaluator or promotion scorer.

Only the three checked-in synthetic Python programs are executed. Documentation
commands are never eval'd. Tests write only to their own temporary directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
CATEGORIES = ("stale_flag", "broken_path", "broken_anchor", "generated_drift",
              "wrong_audience", "release_guidance")


def inventory(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-B", *args], cwd=root,
                          text=True, capture_output=True, timeout=10, check=False)


def link_ok(root: Path, source: str, target: str) -> bool:
    filename, _, anchor = target.partition("#")
    path = (root / source).parent / filename if filename else root / source
    if not path.is_file():
        return False
    headings = re.findall(r"^#{1,6} (.+)$", path.read_text(), re.MULTILINE)
    # These fixtures deliberately use simple ASCII, unique Markdown headings.
    anchors = {re.sub(r"[^a-z0-9 -]", "", h.lower()).replace(" ", "-") for h in headings}
    return not anchor or anchor in anchors


def observe(root: Path) -> dict:
    before = inventory(root)
    readme = (root / "README.md").read_text()
    guide = re.search(r"\[operator guide\]\(([^)]+)\)", readme)
    start = re.search(r"\[fast start\]\(([^)]+)\)", readme)
    assert guide and start, "fixture navigation markers missing"
    help_result = run(root, "cli.py", "--help")
    old = run(root, "cli.py", "--json")
    current = run(root, "cli.py", "--format", "json")
    custom = run(root, "cli.py", "--format", "json", "--theme", "dark")
    generated = run(root, "scripts/render_catalog.py")
    release_help = run(root, "scripts/release.py", "--help")
    assert help_result.returncode == generated.returncode == release_help.returncode == 0
    assert "--format" in help_result.stdout and "--json" not in help_result.stdout
    assert old.returncode == 2 and "unrecognized arguments: --json" in old.stderr
    assert current.returncode == custom.returncode == 0
    assert "publishing is a separate reviewed job" in release_help.stdout
    assert link_ok(root, "README.md", "docs/GUIDE.md#output-modes")
    assert link_ok(root, "docs/REFERENCE.md", "GUIDE.md#output-modes")
    assert link_ok(root, "docs/GUIDE.md", "#quick-start")
    assert "Historical snapshot, not current setup instructions" in (root / "docs/history/v1.md").read_text()
    assert "User-owned customization" in (root / "docs/LOCAL.md").read_text()
    result = {
        "stale_flag": "Run `python3 cli.py --json`." in readme,
        "broken_path": not link_ok(root, "README.md", guide.group(1)),
        "broken_anchor": not link_ok(root, "README.md", start.group(1)),
        "generated_drift": generated.stdout != (root / "docs/CATALOG.md").read_text(),
        "wrong_audience": "## Signing-key rotation" in readme,
        "release_guidance": "publish to the package registry automatically" in (root / "docs/RELEASE.md").read_text(),
    }
    assert before == inventory(root), "read-only tree invariant failed"
    return {"seed_observations": result, "safe_controls_pass": True,
            "tree_unchanged": True, "old_flag_exit": old.returncode,
            "current_command_exit": current.returncode, "custom_command_exit": custom.returncode}


def validate(fixtures: Path) -> dict:
    observations = {case: observe(fixtures / case) for case in ("drift", "clean")}
    for case, expected in (("drift", True), ("clean", False)):
        assert observations[case]["seed_observations"] == dict.fromkeys(CATEGORIES, expected), case
    return observations


def self_test(fixtures: Path) -> list[str]:
    passed = []
    mutations = {
        "stale_flag": ("README.md", "Run `python3 cli.py --format json`.", "Run `python3 cli.py --json`."),
        "broken_path": ("README.md", "[operator guide](docs/GUIDE.md)", "[operator guide](docs/MISSING.md)"),
        "broken_anchor": ("README.md", "#quick-start", "#missing-anchor"),
        "generated_drift": ("docs/CATALOG.md", "--format json", "--json"),
        "wrong_audience": ("README.md", "Maintainers: see", "## Signing-key rotation\n\nMaintainers: see"),
        "release_guidance": ("docs/RELEASE.md", "describe local packaging", "publish to the package registry automatically"),
    }
    for category, (filename, old, new) in mutations.items():
        with tempfile.TemporaryDirectory(prefix="docs-fixture-control-") as temp:
            root = Path(temp) / "clean"
            shutil.copytree(fixtures / "clean", root)
            path = root / filename
            text = path.read_text()
            assert old in text
            path.write_text(text.replace(old, new))
            result = observe(root)["seed_observations"]
            assert result == {key: key == category for key in CATEGORIES}, result
            passed.append(category + ": injected fault observed")
    with tempfile.TemporaryDirectory(prefix="docs-tree-control-") as temp:
        root = Path(temp)
        path = root / "sentinel"
        path.write_text("preserve")
        before = inventory(root)
        path.write_text("changed")
        assert before != inventory(root)
        passed.append("tree mutation: detected")
        path.write_text("preserve")
        assert before == inventory(root)
        (root / "added").write_text("new")
        assert before != inventory(root)
        passed.append("tree addition: detected")
    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    fixtures = HERE / "fixtures"
    before = inventory(fixtures)
    try:
        result = {"kind": "public_static_fixture_integrity", "observations": validate(fixtures),
                  "model_calls": 0, "behavioral_claim": "none", "promotion_eligible": False}
        if args.self_test:
            result["failure_controls"] = self_test(fixtures)
        assert before == inventory(fixtures), "fixture trees changed"
        result["status"] = "pass"
        print(json.dumps(result, indent=2))
        return 0
    except (AssertionError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "fail", "reason": str(exc), "model_calls": 0}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
