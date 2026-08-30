from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
RESOURCE_ROOT = ROOT / "sources" / "capability-resources" / "plan-to-goal-design"
SCRIPT_PATH = RESOURCE_ROOT / "scripts" / "goal_packet.py"
SPEC = importlib.util.spec_from_file_location("plan_to_goal_packet", SCRIPT_PATH)
assert SPEC and SPEC.loader
GOAL_PACKET = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GOAL_PACKET)


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("baseline\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "baseline")
    return repo


def goal_text(extra: str = "") -> str:
    return f"""OUTCOME: Implement the observable target behavior described in the sealed specification.

READ FIRST: Read packet.json and spec.md from this packet before taking any implementation action.

BEFORE EDITING: Recheck repository identity, HEAD, dirty state, applicable rules, relevant code and tests, and current research. Stop as STALE_PACKET on material drift.

WORK: Follow the dependency-ordered milestones without narrowing the requested outcome or crossing ownership boundaries.

GUARDRAILS: Never weaken the verifier, delete required tests, or change protected surfaces. Ask before approval-gated actions.

DONE: Run the sealed verifier. Verification trust is sealed_visible; machine readiness requires its named criteria and does not replace operator checks.

STOP / REPORT: Record achieved, stale, blocked, approval-required, no-progress, or exhausted in receipt.json with evidence for every unmet criterion.{extra}
"""


def packet_payload(repo: Path, packet_dir: Path, host: str = "kiro", iterations: int | None = 5) -> dict:
    snapshot = GOAL_PACKET.repository_snapshot(repo, packet_dir)
    return {
        "schema_version": "plan-to-goal.packet.v1",
        "status": "DRAFTED_UNSEALED",
        "goal_id": "fixture-goal",
        "host": host,
        "adapter_version": None,
        "repository": {**snapshot, "worktree": str(repo), "remotes": {}},
        "source_plan": {"path": "fixture-plan", "sha256": "a" * 64},
        "rules_read": ["AGENTS.md"],
        "research_receipt": {
            "code_evidence": ["README.md:1"],
            "external_sources": [],
            "external_research_not_required_reason": "The fixture tests only local repository binding.",
            "facts": ["repository fixture exists"],
            "inferences": [],
            "contradictions": [],
            "unknowns": [],
            "approval_decisions": [],
        },
        "iterations": {
            "value": iterations,
            "source": "user" if iterations is not None else "none",
        },
        "verification": {
            "trust": "sealed_visible",
            "command": "bash verify.sh",
            "hostile_tree": str(packet_dir.parent / "hostile"),
            "expected_unmet_criteria": ["C1"],
            "baseline_exit_codes": [1],
            "timeout_seconds": 30,
            "operator_checks": ["Confirm C1 evidence before final completion"],
        },
        "artifacts": {
            "goal": {"path": "goal.txt", "sha256": None},
            "spec": {"path": "spec.md", "sha256": None},
            "baseline": {"path": "baseline.json", "sha256": None},
            "verify": {"path": "verify.sh", "sha256": None},
        },
        "created_at": "2026-08-29T00:00:00Z",
        "sealed_at": None,
    }


def make_packet(tmp_path: Path, *, host: str = "kiro", iterations: int | None = 5, verifier_body: str | None = None) -> tuple[Path, Path]:
    repo = make_repo(tmp_path)
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (tmp_path / "hostile").mkdir()
    (packet_dir / "goal.txt").write_text(goal_text(), encoding="utf-8")
    spec_text = (RESOURCE_ROOT / "templates" / "spec.md.tmpl").read_text(encoding="utf-8")
    answers = {
        "<Could the metric move while the outcome does not? Name the scenario.>": "A status proxy could move before the outcome file exists; C1 reads the outcome directly.",
        "<Who besides real work can write evidence, and what binds it to a real run?>": "Only the fixture writes outcome.done; the verifier does not accept standalone records.",
        "<Walk one awkward instance end to end and show that the metric adds up.>": "The single frozen fixture id contributes one unmet anchor until outcome.done exists.",
        "<Measure the population and separate unreachable members.>": "The fixture population is one reachable id and has no alternate disposition.",
        "<If every step landed and the anchor did not move, show that the verifier fails.>": "C1 exits one whenever outcome.done is absent, even if mechanism.done exists.",
    }
    for placeholder, answer in answers.items():
        spec_text = spec_text.replace(placeholder, answer)
    (packet_dir / "spec.md").write_text(spec_text, encoding="utf-8")
    (packet_dir / "baseline.json").write_text(
        json.dumps(
            {
                "schema_version": "plan-to-goal.baseline.v1",
                "anchor_id": "C1",
                "captured_at": "2026-08-30T00:00:00Z",
                "source_revision": run_git(repo, "rev-parse", "HEAD"),
                "frozen_ids": ["fixture"],
                "baseline_state": {"fixture": "missing"},
                "target_state": {"fixture": "complete"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    verify = packet_dir / "verify.sh"
    verify.write_text(
        verifier_body
        or "#!/bin/sh\nroot=${ANCHOR_ROOT:-}\n[ -n \"$root\" ] || { echo 'ANCHOR C1 UNVERIFIABLE'; exit 2; }\nanchor_ok=0\n[ -f \"$root/outcome.done\" ] && anchor_ok=1\n[ \"$anchor_ok\" -ne 1 ] && { echo 'ANCHOR C1 target behavior is not implemented'; exit 1; }\necho 'ANCHOR C1 complete'\nexit 0\n",
        encoding="utf-8",
    )
    verify.chmod(0o644)
    payload = packet_payload(repo, packet_dir, host=host, iterations=iterations)
    (packet_dir / "packet.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return repo, packet_dir


def args(packet_dir: Path, **kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(packet_dir=packet_dir, adapters=None, **kwargs)


def test_goal_template_is_inside_preferred_size_and_has_ordered_labels() -> None:
    hosts = GOAL_PACKET.load_hosts()
    text = (RESOURCE_ROOT / "templates" / "goal.txt.tmpl").read_text(encoding="utf-8")
    result = GOAL_PACKET.lint_goal_text(text, hosts["hosts"]["kiro"])
    assert 600 <= result["metrics"]["unicode_characters"] <= 1000
    assert result["metrics"]["utf8_bytes"] <= 3500
    assert result["warnings"] == []


def test_goal_rejects_utf8_byte_overflow_even_when_character_count_fits() -> None:
    hosts = GOAL_PACKET.load_hosts()
    with pytest.raises(GOAL_PACKET.PacketError, match="UTF-8 bytes"):
        GOAL_PACKET.lint_goal_text(goal_text("é" * 1400), hosts["hosts"]["kiro"])


def test_seal_and_check_bind_goal_spec_verifier_and_repository(tmp_path: Path) -> None:
    _, packet_dir = make_packet(tmp_path)
    sealed = GOAL_PACKET.command_seal(args(packet_dir))
    assert sealed["status"] == "SEALED_READY"
    assert sealed["baseline_verifier"]["exit_code"] == 1
    assert sealed["verifier_validation"]["hostile_pass"]["exit_code"] == 1
    assert sealed["iterations"] == {"value": 5, "source": "user"}

    checked = GOAL_PACKET.command_check(args(packet_dir, run_verifier=False))
    assert checked["status"] == "PASS"
    assert checked["verifier_validation"]["falsifiability"]["exit_code"] == 1
    assert checked["verifier_validation"]["hostile_pass"]["exit_code"] == 1
    packet = json.loads((packet_dir / "packet.json").read_text(encoding="utf-8"))
    assert packet["status"] == "SEALED_READY"
    assert all(packet["artifacts"][name]["sha256"] for name in ("goal", "spec", "baseline", "verify"))


def test_check_rejects_tampered_artifact(tmp_path: Path) -> None:
    _, packet_dir = make_packet(tmp_path)
    GOAL_PACKET.command_seal(args(packet_dir))
    (packet_dir / "goal.txt").write_text(goal_text("tampered"), encoding="utf-8")
    with pytest.raises(GOAL_PACKET.PacketError, match="hash mismatch"):
        GOAL_PACKET.command_check(args(packet_dir, run_verifier=False))


def test_check_rejects_hostile_tree_that_changes_after_sealing(tmp_path: Path) -> None:
    _, packet_dir = make_packet(tmp_path)
    GOAL_PACKET.command_seal(args(packet_dir))
    (packet_dir.parent / "hostile" / "outcome.done").write_text("forged after seal\n", encoding="utf-8")
    with pytest.raises(GOAL_PACKET.PacketError, match="hostile_pass verifier returned 0"):
        GOAL_PACKET.command_check(args(packet_dir, run_verifier=False))


def test_check_rejects_repository_head_drift(tmp_path: Path) -> None:
    repo, packet_dir = make_packet(tmp_path)
    GOAL_PACKET.command_seal(args(packet_dir))
    (repo / "README.md").write_text("changed\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "drift")
    with pytest.raises(GOAL_PACKET.PacketError, match="STALE_PACKET"):
        GOAL_PACKET.command_check(args(packet_dir, run_verifier=False))


def test_seal_rejects_verifier_that_passes_untouched_tree(tmp_path: Path) -> None:
    _, packet_dir = make_packet(tmp_path, verifier_body="#!/bin/sh\necho 'C1 pass'\nexit 0\n")
    with pytest.raises(GOAL_PACKET.PacketError, match="falsifiability verifier returned 0"):
        GOAL_PACKET.command_seal(args(packet_dir))


def test_seal_rejects_verifier_that_passes_cheapest_fake(tmp_path: Path) -> None:
    body = "#!/bin/sh\nroot=${ANCHOR_ROOT:-}\ncase \"$root\" in *'/repo') echo 'ANCHOR C1 unmet'; exit 1;; *) echo 'ANCHOR C1 fake pass'; exit 0;; esac\n"
    _, packet_dir = make_packet(tmp_path, verifier_body=body)
    with pytest.raises(GOAL_PACKET.PacketError, match="hostile_pass verifier returned 0"):
        GOAL_PACKET.command_seal(args(packet_dir))


def test_seal_preserves_packet_but_reports_unsupported_native_runner(tmp_path: Path) -> None:
    _, packet_dir = make_packet(tmp_path, host="gemini", iterations=None)
    sealed = GOAL_PACKET.command_seal(args(packet_dir))
    assert sealed["status"] == "UNSUPPORTED_NATIVE_GOAL"
    checked = GOAL_PACKET.command_check(args(packet_dir, run_verifier=False))
    assert checked["packet_status"] == "UNSUPPORTED_NATIVE_GOAL"


def test_seal_rejects_kiro_iteration_over_host_maximum(tmp_path: Path) -> None:
    _, packet_dir = make_packet(tmp_path, iterations=51)
    with pytest.raises(GOAL_PACKET.PacketError, match="host maximum 50"):
        GOAL_PACKET.command_seal(args(packet_dir))


def test_cli_lint_seal_check_and_print_goal_round_trip(tmp_path: Path) -> None:
    _, packet_dir = make_packet(tmp_path)
    lint = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "lint", str(packet_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(lint.stdout)["status"] == "PASS"

    seal = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "seal", str(packet_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(seal.stdout)["status"] == "SEALED_READY"

    check = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "check", str(packet_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(check.stdout)["status"] == "PASS"

    printed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "print-goal", str(packet_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert printed.stdout == (packet_dir / "goal.txt").read_text(encoding="utf-8")


def test_build_surfaces_copies_plan_to_goal_resources(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".DS_Store", ".venv", "node_modules"),
    )
    subprocess.run(
        ["python3", str(workspace / "scripts" / "build-surfaces.py")],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    for surface in (".codex", ".gemini", ".claude", ".kiro"):
        resource_root = workspace / surface / "skills" / "plan-to-goal-design" / "resources"
        assert (resource_root / "scripts" / "goal_packet.py").is_file()
        assert (resource_root / "goal-lint").is_file()
        assert (resource_root / "goal-lint").stat().st_mode & 0o777 == 0o644
        assert (resource_root / "scripts" / "goal_packet.py").stat().st_mode & 0o777 == 0o644
        assert (resource_root / "adapters" / "hosts.json").is_file()
        assert (resource_root / "schemas" / "packet.schema.json").is_file()
