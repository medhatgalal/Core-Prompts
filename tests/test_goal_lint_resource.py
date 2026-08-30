from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOAL_LINT = ROOT / "sources" / "capability-resources" / "plan-to-goal-design" / "goal-lint"


def write_fixture(tmp_path: Path, *, hostile_passes: bool = False) -> tuple[Path, Path, Path]:
    untouched = tmp_path / "untouched"
    hostile = tmp_path / "hostile"
    goal_dir = tmp_path / "goal"
    untouched.mkdir()
    hostile.mkdir()
    goal_dir.mkdir()
    (hostile / "mechanism.done").write_text("proxy only\n", encoding="utf-8")

    (goal_dir / "goal.txt").write_text(
        "Complete the frozen outcome population. Read spec.md first. "
        "Done only when bash verify.sh exits 0; the anchor decides, not you. "
        "Never replace the frozen ids, forge evidence, or weaken the verifier. "
        "If the outcome is unachievable, stop and report why.\n",
        encoding="utf-8",
    )
    (goal_dir / "spec.md").write_text(
        """# Fixture goal

## Outcome Anchor
ANCHOR C1 requires every frozen id to have outcome.done.

## Frozen Population
The one frozen id is fixture.

## Fake / Block Table
| Fake | Block |
| --- | --- |
| mechanism.done only | C1 reads outcome.done |

## Two-Sided Verifier Validation
The untouched and cheapest-fake trees must both fail C1.

## Exit-Gate Truth Table
| State | Exit |
| --- | --- |
| untouched | 1 |
| cheapest fake | 1 |
| achieved | 0 |

## Manual Design Answers

### PROXY
mechanism.done can exist while outcome.done is absent, so C1 reads the outcome directly.

### FORGERY
Only the operator-owned outcome file is evidence; probe records are ignored.

### ARITHMETIC
One frozen id contributes exactly one incomplete result until outcome.done exists.

### ACHIEVABLE
The fixture population contains one reachable id and no alternate disposition.

### TRAP
If mechanism.done exists and outcome.done does not, verify.sh still exits one.
""",
        encoding="utf-8",
    )
    (goal_dir / "baseline.json").write_text(
        json.dumps(
            {
                "schema_version": "plan-to-goal.baseline.v1",
                "anchor_id": "C1",
                "frozen_ids": ["fixture"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    hostile_clause = (
        '[ -f "$root/mechanism.done" ] && { echo "ANCHOR C1 fake passed"; exit 0; }\n'
        if hostile_passes
        else ""
    )
    (goal_dir / "verify.sh").write_text(
        "#!/bin/sh\n"
        "root=${ANCHOR_ROOT:-}\n"
        "[ -n \"$root\" ] || { echo 'ANCHOR C1 UNVERIFIABLE'; exit 2; }\n"
        "anchor_ok=0\n"
        "[ -f \"$root/outcome.done\" ] && anchor_ok=1\n"
        + hostile_clause
        + "[ \"$anchor_ok\" -ne 1 ] && { echo 'ANCHOR C1 unmet'; exit 1; }\n"
        "echo 'ANCHOR C1 complete'\n"
        "exit 0\n",
        encoding="utf-8",
    )
    (goal_dir / "verify.sh").chmod(0o644)
    return goal_dir, untouched, hostile


def run_lint(goal_dir: Path, untouched: Path, hostile: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            str(GOAL_LINT),
            "--json",
            "--tree",
            str(untouched),
            "--hostile-tree",
            str(hostile),
            str(goal_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_help_documents_interface_and_exit_codes() -> None:
    result = subprocess.run(["bash", str(GOAL_LINT), "--help"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "--hostile-tree" in result.stdout
    assert "Exit codes:" in result.stdout
    assert result.stderr == ""


def test_invalid_option_is_usage_error_on_stderr() -> None:
    result = subprocess.run(["bash", str(GOAL_LINT), "--unknown"], capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "unknown option" in result.stderr


def test_json_clean_run_is_parseable_and_keeps_five_questions(tmp_path: Path) -> None:
    goal_dir, untouched, hostile = write_fixture(tmp_path)
    result = run_lint(goal_dir, untouched, hostile)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "clean"
    assert payload["counts"]["finding"] == 0
    assert [item["id"] for item in payload["manual_questions"]] == [
        "PROXY",
        "FORGERY",
        "ARITHMETIC",
        "ACHIEVABLE",
        "TRAP",
    ]
    assert result.stderr == ""
    assert "\x1b" not in result.stdout


def test_relative_goal_and_tree_paths_resolve_before_verifier_changes_cwd(tmp_path: Path) -> None:
    goal_dir, untouched, hostile = write_fixture(tmp_path)
    result = subprocess.run(
        [
            "bash",
            str(GOAL_LINT),
            "--json",
            "--tree",
            untouched.name,
            "--hostile-tree",
            hostile.name,
            goal_dir.name,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "clean"


def test_resource_and_verifier_do_not_need_execute_bits(tmp_path: Path) -> None:
    goal_dir, untouched, hostile = write_fixture(tmp_path)
    assert GOAL_LINT.stat().st_mode & 0o777 == 0o644
    assert (goal_dir / "verify.sh").stat().st_mode & 0o777 == 0o644
    assert run_lint(goal_dir, untouched, hostile).returncode == 0


def test_missing_hostile_tree_is_a_blocking_finding(tmp_path: Path) -> None:
    goal_dir, untouched, _ = write_fixture(tmp_path)
    result = subprocess.run(
        ["bash", str(GOAL_LINT), "--json", "--tree", str(untouched), str(goal_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    finding = next(item for item in payload["checks"] if item["id"] == "verifier.hostile-pass")
    assert finding["status"] == "fail"


def test_hostile_pass_catches_fake_that_exits_zero(tmp_path: Path) -> None:
    goal_dir, untouched, hostile = write_fixture(tmp_path, hostile_passes=True)
    result = run_lint(goal_dir, untouched, hostile)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    finding = next(item for item in payload["checks"] if item["id"] == "verifier.hostile-pass")
    assert finding["status"] == "fail"
    assert "exit 0" in finding["message"]


def test_exact_4000_character_goal_is_allowed_but_4001_is_blocked(tmp_path: Path) -> None:
    goal_dir, untouched, hostile = write_fixture(tmp_path)
    goal_path = goal_dir / "goal.txt"
    original = goal_path.read_text(encoding="utf-8").rstrip("\n")
    goal_path.write_text(original + "x" * (4000 - len(original)), encoding="utf-8")
    at_limit = run_lint(goal_dir, untouched, hostile)
    assert at_limit.returncode == 0, at_limit.stdout + at_limit.stderr

    goal_path.write_text(original + "x" * (4001 - len(original)), encoding="utf-8")
    over_limit = run_lint(goal_dir, untouched, hostile)
    assert over_limit.returncode == 1
    payload = json.loads(over_limit.stdout)
    size_check = next(item for item in payload["checks"] if item["id"] == "size.goal.txt")
    assert size_check["status"] == "fail"


def test_blank_manual_answer_blocks_dispatch(tmp_path: Path) -> None:
    goal_dir, untouched, hostile = write_fixture(tmp_path)
    spec_path = goal_dir / "spec.md"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8").replace(
            "### FORGERY\nOnly the operator-owned outcome file is evidence; probe records are ignored.",
            "### FORGERY\n",
        ),
        encoding="utf-8",
    )
    result = run_lint(goal_dir, untouched, hostile)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    check = next(item for item in payload["checks"] if item["id"] == "manual.FORGERY")
    assert check["status"] == "fail"


def test_invalid_or_duplicate_frozen_ids_block_dispatch(tmp_path: Path) -> None:
    goal_dir, untouched, hostile = write_fixture(tmp_path)
    (goal_dir / "baseline.json").write_text('{"frozen_ids":["fixture","fixture"]}\n', encoding="utf-8")
    result = run_lint(goal_dir, untouched, hostile)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    check = next(item for item in payload["checks"] if item["id"] == "baseline.frozen_ids")
    assert check["status"] == "fail"


def test_duplicate_outcome_anchor_section_blocks_dispatch(tmp_path: Path) -> None:
    goal_dir, untouched, hostile = write_fixture(tmp_path)
    spec_path = goal_dir / "spec.md"
    spec_path.write_text(spec_path.read_text(encoding="utf-8") + "\n## Outcome Anchor\nduplicate\n", encoding="utf-8")
    result = run_lint(goal_dir, untouched, hostile)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    check = next(item for item in payload["checks"] if item["id"] == "spec.Outcome-Anchor")
    assert check["status"] == "fail"
