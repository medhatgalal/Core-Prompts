from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_version_changelog_and_docs_contract_are_aligned() -> None:
    version = read("VERSION").strip()
    changelog = read("CHANGELOG.md")
    match = re.search(r"^##\s+([^ ]+)\s+-\s+", changelog, re.M)
    assert match
    assert match.group(1) == version

    public_docs = {
        "README.md": read("README.md"),
        "docs/GETTING-STARTED.md": read("docs/GETTING-STARTED.md"),
        "docs/CLI-REFERENCE.md": read("docs/CLI-REFERENCE.md"),
        "docs/RELEASE-PACKAGING.md": read("docs/RELEASE-PACKAGING.md"),
        "docs/MAINTAINER-HYGIENE.md": read("docs/MAINTAINER-HYGIENE.md"),
        "docs/README.md": read("docs/README.md"),
    }

    required = [
        "VERSION",
        "RELEASE_SOURCE.env",
        "--check-release",
        "--accept-release",
        "never auto-installs",
        "explicit install/apply step",
    ]
    for path, text in public_docs.items():
        for needle in required:
            assert needle in text, f"{path} missing {needle}"

    assert "Daily scheduled updater runs execute `~/update_core_prompts.sh --check-release` before normal update sync" in public_docs["docs/GETTING-STARTED.md"]
    assert "pending release state shows a warning" in public_docs["docs/CLI-REFERENCE.md"]
    assert "do not silently mutate the user system" in public_docs["docs/RELEASE-PACKAGING.md"]


def test_public_help_contract_mentions_release_watch() -> None:
    fabric = subprocess.run([str(ROOT / "bin" / "capability-fabric"), "--help"], cwd=ROOT, capture_output=True, text=True, check=True)
    update = subprocess.run(["python3", str(ROOT / "scripts" / "update-core-prompts.py"), "--help"], cwd=ROOT, capture_output=True, text=True, check=True)
    install = subprocess.run([str(ROOT / "scripts" / "install-local.sh"), "--help"], cwd=ROOT, capture_output=True, text=True, check=True)

    assert "update [args...]" in fabric.stdout
    assert "--check-release checks only and never auto-installs" in fabric.stdout
    assert "--check-release" in update.stdout
    assert "--accept-release" in update.stdout
    assert "checks only and never auto-installs" in update.stdout
    assert "standalone updater bundle" in install.stdout
    assert "RELEASE_SOURCE.env" in install.stdout
