#!/usr/bin/env python3
"""Execute every verifier criterion in synthetic present and absent states."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


EXIT_PASS = 0
EXIT_FINDINGS = 1
EXIT_INPUT = 2
SCHEMA_VERSION = "plan-to-goal.criterion-flips.v1"
ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]*$")


class FlipError(RuntimeError):
    pass


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FlipError(f"cannot read valid JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise FlipError(f"{path} must contain a JSON object")
    return value


def resolve_fixture(packet_dir: Path, value: object, criterion_id: str, state: str) -> Path:
    if not isinstance(value, str) or not value:
        raise FlipError(f"criterion {criterion_id} requires {state}_tree")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise FlipError(f"criterion {criterion_id} {state}_tree must stay inside the packet")
    resolved = (packet_dir / relative).resolve()
    try:
        resolved.relative_to(packet_dir)
    except ValueError as error:
        raise FlipError(f"criterion {criterion_id} {state}_tree escapes the packet") from error
    if not resolved.is_dir():
        raise FlipError(f"criterion {criterion_id} {state}_tree does not exist: {resolved}")
    return resolved


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_symlink():
            raise FlipError(f"criterion fixture trees must not contain symlinks: {path}")
        if path.is_dir():
            digest.update(b"D\0" + relative + b"\0")
        elif path.is_file():
            digest.update(b"F\0" + relative + b"\0" + hashlib.sha256(path.read_bytes()).digest())
        else:
            raise FlipError(f"unsupported criterion fixture entry: {path}")
    return digest.hexdigest()


def verifier_criteria(verify_path: Path, timeout: int) -> list[str]:
    result = subprocess.run(
        ["bash", str(verify_path), "--list-criteria"],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise FlipError(f"verify.sh --list-criteria returned {result.returncode}: {result.stderr.strip()}")
    criteria = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not criteria or any(not ID_PATTERN.fullmatch(item) for item in criteria):
        raise FlipError("verify.sh --list-criteria must print one valid criterion ID per line")
    if len(criteria) != len(set(criteria)):
        raise FlipError("verify.sh --list-criteria returned duplicate criterion IDs")
    return criteria


def run_criterion(verify_path: Path, criterion_id: str, root: Path, timeout: int) -> dict[str, Any]:
    result = subprocess.run(
        ["bash", str(verify_path)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env={
            **os.environ,
            "ANCHOR_ROOT": str(root),
            "REPO_ROOT": str(root),
            "CRITERION_ID": criterion_id,
        },
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def evaluate(packet_dir: Path) -> dict[str, Any]:
    packet_dir = packet_dir.resolve()
    if not packet_dir.is_dir():
        raise FlipError(f"packet directory does not exist: {packet_dir}")
    manifest = load_object(packet_dir / "criterion-flips.json")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise FlipError(f"criterion-flips.json requires schema_version {SCHEMA_VERSION}")
    timeout = manifest.get("timeout_seconds", 30)
    if not isinstance(timeout, int) or not 1 <= timeout <= 300:
        raise FlipError("criterion-flips.json timeout_seconds must be an integer from 1 to 300")
    entries = manifest.get("criteria")
    if not isinstance(entries, list) or not entries:
        raise FlipError("criterion-flips.json requires a nonempty criteria list")
    verify_path = packet_dir / "verify.sh"
    if not verify_path.is_file():
        raise FlipError("verify.sh is missing")

    declared_ids: list[str] = []
    anchor_ids: list[str] = []
    normalized: list[tuple[str, Path, Path]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise FlipError("every criterion flip entry must be an object")
        criterion_id = entry.get("id")
        if not isinstance(criterion_id, str) or not ID_PATTERN.fullmatch(criterion_id):
            raise FlipError(f"invalid criterion id: {criterion_id!r}")
        role = entry.get("role")
        if role not in {"anchor", "mechanism"}:
            raise FlipError(f"criterion {criterion_id} role must be anchor or mechanism")
        if role == "anchor":
            anchor_ids.append(criterion_id)
        declared_ids.append(criterion_id)
        present_tree = resolve_fixture(packet_dir, entry.get("present_tree"), criterion_id, "present")
        absent_tree = resolve_fixture(packet_dir, entry.get("absent_tree"), criterion_id, "absent")
        if present_tree == absent_tree:
            raise FlipError(f"criterion {criterion_id} present and absent trees must be different")
        for state, root in (("present", present_tree), ("absent", absent_tree)):
            expected_hash = entry.get(f"{state}_sha256")
            if expected_hash is not None:
                if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                    raise FlipError(f"criterion {criterion_id} {state}_sha256 is invalid")
                actual_hash = tree_sha256(root)
                if actual_hash != expected_hash:
                    raise FlipError(
                        f"criterion {criterion_id} {state} tree hash mismatch: expected {expected_hash}, found {actual_hash}"
                    )
        normalized.append((criterion_id, present_tree, absent_tree))
    if len(declared_ids) != len(set(declared_ids)):
        raise FlipError("criterion-flips.json contains duplicate criterion IDs")
    if len(anchor_ids) != 1:
        raise FlipError(f"criterion-flips.json requires exactly one anchor criterion; found {len(anchor_ids)}")

    baseline = load_object(packet_dir / "baseline.json")
    if baseline.get("anchor_id") != anchor_ids[0]:
        raise FlipError("baseline.json anchor_id must match the criterion entry whose role is anchor")
    listed_ids = verifier_criteria(verify_path, timeout)
    if set(listed_ids) != set(declared_ids):
        missing = sorted(set(listed_ids) - set(declared_ids))
        extra = sorted(set(declared_ids) - set(listed_ids))
        raise FlipError(f"criterion inventory mismatch: missing fixtures={missing}, undeclared by verifier={extra}")

    results: list[dict[str, Any]] = []
    for criterion_id, present_tree, absent_tree in normalized:
        present = run_criterion(verify_path, criterion_id, present_tree, timeout)
        absent = run_criterion(verify_path, criterion_id, absent_tree, timeout)
        present_output = "\n".join(part for part in (present["stdout"], present["stderr"]) if part)
        absent_output = "\n".join(part for part in (absent["stdout"], absent["stderr"]) if part)
        present_marker = f"CRITERION {criterion_id} PASS"
        absent_marker = f"CRITERION {criterion_id} FAIL"
        passed = (
            present["exit_code"] == 0
            and absent["exit_code"] == 1
            and present_marker in present_output.splitlines()
            and absent_marker in absent_output.splitlines()
        )
        if passed:
            message = f"{criterion_id} flips correctly: present=0 absent=1"
        elif present["exit_code"] == absent["exit_code"]:
            message = (
                f"{criterion_id} cannot flip: present={present['exit_code']} absent={absent['exit_code']}"
            )
        elif present["exit_code"] not in {0, 1} or absent["exit_code"] not in {0, 1}:
            message = (
                f"{criterion_id} returned an error instead of a verdict: "
                f"present={present['exit_code']} absent={absent['exit_code']}"
            )
        else:
            message = f"{criterion_id} did not emit the required PASS/FAIL criterion markers"
        results.append(
            {
                "id": criterion_id,
                "status": "pass" if passed else "fail",
                "message": message,
                "present": present,
                "absent": absent,
            }
        )
    failures = sum(result["status"] == "fail" for result in results)
    return {
        "schema_version": "criterion-flip-report.v1",
        "status": "pass" if failures == 0 else "findings",
        "criterion_count": len(results),
        "finding_count": failures,
        "criteria": results,
    }


def render_human(report: dict[str, Any]) -> None:
    for result in report["criteria"]:
        print(f"{result['status'].upper():7} {result['id']:16} {result['message']}")
    print(
        f"\ncriterion flip result: {report['status']} "
        f"({report['criterion_count']} checked, {report['finding_count']} findings)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute each verifier criterion against synthetic present and absent trees."
    )
    parser.add_argument("packet_dir", type=Path, help="Goal packet containing criterion-flips.json and verify.sh.")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object to stdout.")
    args = parser.parse_args()
    try:
        report = evaluate(args.packet_dir)
    except (FlipError, OSError, subprocess.SubprocessError) as error:
        print(f"criterion-flip: {error}", file=sys.stderr)
        if args.json:
            print(json.dumps({"status": "input_error", "error": str(error)}, sort_keys=True))
        return EXIT_INPUT
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        render_human(report)
    return EXIT_PASS if report["status"] == "pass" else EXIT_FINDINGS


if __name__ == "__main__":
    raise SystemExit(main())
