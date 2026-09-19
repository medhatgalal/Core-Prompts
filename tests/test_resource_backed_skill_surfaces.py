"""Every resource-backed skill must ship its complete bundle on every skill surface."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from intent_pipeline.capability_resources import load_resource_bundle


ROOT = Path(__file__).resolve().parents[1]
SURFACES = ("codex", "gemini", "claude", "kiro", "grok")


def test_resource_backed_skill_bundles_are_complete_and_installed_in_manifest():
    install_files = json.loads((ROOT / ".meta" / "install-bundle.json").read_text(encoding="utf-8"))["files"]
    canonical_roots = sorted(
        path.parent for path in (ROOT / "sources" / "capability-resources").glob("*/resource-map.json")
    )

    assert canonical_roots
    for canonical_root in canonical_roots:
        slug = canonical_root.name
        canonical_files = sorted(path for path in canonical_root.rglob("*") if path.is_file())
        assert (ROOT / "ssot" / f"{slug}.md").is_file()

        for surface in SURFACES:
            generated_root = ROOT / f".{surface}" / "skills" / slug / "resources"
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
                assert json.loads(result.stdout) == load_resource_bundle(canonical_root, route)


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
