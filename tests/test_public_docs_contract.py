from __future__ import annotations

import json
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
        "LOCAL_REPO.env",
        "--check-release",
        "--accept-release",
        "--rollback",
        "never auto-installs",
        "explicit install/apply step",
    ]
    for path, text in public_docs.items():
        for needle in required:
            assert needle in text, f"{path} missing {needle}"

    assert "Scheduled runs auto-accept valid releases by default" in public_docs["docs/GETTING-STARTED.md"]
    assert "`--notify-only` to keep scheduling check-only" in public_docs["docs/CLI-REFERENCE.md"]
    assert "`--rollback previous` restores the latest pre-release snapshot" in public_docs["docs/RELEASE-PACKAGING.md"]


def test_public_help_contract_mentions_release_watch() -> None:
    fabric = subprocess.run([str(ROOT / "bin" / "capability-fabric"), "--help"], cwd=ROOT, capture_output=True, text=True, check=True)
    update = subprocess.run(["python3", str(ROOT / "scripts" / "update-core-prompts.py"), "--help"], cwd=ROOT, capture_output=True, text=True, check=True)
    install = subprocess.run([str(ROOT / "scripts" / "install-local.sh"), "--help"], cwd=ROOT, capture_output=True, text=True, check=True)

    assert "update [args...]" in fabric.stdout
    assert "--check-release checks only and never auto-installs" in fabric.stdout
    assert "--check-release" in update.stdout
    assert "--accept-release" in update.stdout
    assert "--rollback" in update.stdout
    assert "--notify-only" in update.stdout
    assert "checks only and never auto-installs" in update.stdout
    assert "standalone updater bundle" in install.stdout
    assert "RELEASE_SOURCE.env" in install.stdout


def test_readme_skill_count_matches_generated_manifest() -> None:
    manifest = json.loads(read(".meta/manifest.json"))
    shipped_skills = manifest["surfaces"]["codex_skill"]
    readme = read("README.md")
    match = re.search(r"current generated surfaces ship `(\d+)` skills", readme)
    assert match, "README.md must publish the current generated skill count"
    assert int(match.group(1)) == len(shipped_skills)


def test_plan_to_goal_is_discoverable_from_public_onboarding() -> None:
    public_docs = (
        "README.md",
        "docs/GETTING-STARTED.md",
        "docs/EXAMPLES.md",
        "docs/CLI-REFERENCE.md",
    )
    for path in public_docs:
        assert "plan-to-goal-design" in read(path), f"{path} must include plan-to-goal-design"

    examples = read("docs/EXAMPLES.md")
    for required in (
        "criterion-flips.json",
        "judge-amendments.json",
        "CRITERION_ID=ANCHOR_ROUTE",
        "goal_packet.py seal",
        "behavioral promotion",
    ):
        assert required in examples, f"docs/EXAMPLES.md missing {required}"
