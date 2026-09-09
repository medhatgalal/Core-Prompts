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
    match = re.search(r"^##[ \t]+([^ \t\r\n]+)[ \t]+-[ \t]+", changelog, re.MULTILINE)
    assert match
    assert match.group(1) == version

    # Lifecycle guarantees have one canonical home; onboarding must route there.
    release = read("docs/RELEASE-PACKAGING.md")
    cli = read("docs/CLI-REFERENCE.md")
    for needle in (
        "VERSION", "RELEASE_SOURCE.env", "LOCAL_REPO.env",
        "--check-release", "--accept-release", "--rollback",
        "never auto-installs", "explicit install/apply step",
        "--notify-only", "Saved-profile", "verified release mirror",
    ):
        assert needle in release, f"release contract missing {needle}"
        assert needle in cli, f"CLI reference missing {needle}"
    assert "`--notify-only` to keep scheduling check-only" in cli
    assert "`--rollback previous` restores the latest pre-release snapshot" in release
    assert "two-snapshot pruning policy" in release
    assert "not applied on that path" in release
    assert "later edits" in cli

    routes = {
        "README.md": ("docs/CLI-REFERENCE.md", "docs/RELEASE-PACKAGING.md"),
        "docs/GETTING-STARTED.md": ("CLI-REFERENCE.md#check-or-accept-installed-releases", "RELEASE-PACKAGING.md#installed-release-watch-contract"),
        "docs/README.md": ("CLI-REFERENCE.md#check-or-accept-installed-releases", "RELEASE-PACKAGING.md#installed-release-watch-contract"),
        "docs/MAINTAINER-HYGIENE.md": ("RELEASE-PACKAGING.md#installed-release-watch-contract",),
    }
    for path, targets in routes.items():
        text = read(path)
        for target in targets:
            assert f"]({target})" in text, f"{path} must link to {target}"
            target_path = ROOT / Path(path).parent / target.split("#", 1)[0]
            assert target_path.is_file(), f"{path} has missing target {target}"
    assert "Scheduled runs auto-accept valid releases by default" in read("docs/GETTING-STARTED.md")


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
        assert "engos-design-plan-to-goal" in read(path), f"{path} must include engos-design-plan-to-goal"

    examples = read("docs/EXAMPLES.md")
    for required in (
        "criterion-flips.json",
        "judge-amendments.json",
        "CRITERION_ID=ANCHOR_ROUTE",
        "goal_packet.py seal",
        "behavioral promotion",
    ):
        assert required in examples, f"docs/EXAMPLES.md missing {required}"


def test_opex_incident_audit_is_discoverable_with_snapshot_examples() -> None:
    public_docs = (
        "README.md",
        "docs/GETTING-STARTED.md",
        "docs/EXAMPLES.md",
        "docs/CLI-REFERENCE.md",
    )
    for path in public_docs:
        assert "engos-audit-opex-incident-review" in read(path), f"{path} missing the OpEx audit skill"

    examples = read("docs/EXAMPLES.md")
    for required in (
        "Needs a Decision",
        "Who Owes What",
        "R2 data-quality corrections",
        "opex_digest.py validate",
        "opex_digest.py render",
    ):
        assert required in examples, f"docs/EXAMPLES.md missing {required}"
