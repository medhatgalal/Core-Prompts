#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "plan-to-goal.packet.v1"
PORTABLE_CHAR_LIMIT = 3500
PORTABLE_BYTE_LIMIT = 3500
PREFERRED_MIN = 600
PREFERRED_MAX = 1000
WARNING_CHARS = 1200
REQUIRED_LABELS = (
    "OUTCOME",
    "READ FIRST",
    "BEFORE EDITING",
    "WORK",
    "GUARDRAILS",
    "DONE",
    "STOP / REPORT",
)
REQUIRED_SPEC_HEADINGS = (
    "## Provenance",
    "## Outcome",
    "## Outcome Anchor",
    "## Frozen Population",
    "## Non-Goals",
    "## Research Receipt",
    "### Rules Read",
    "### Code and Test Evidence",
    "### External Sources",
    "### Facts, Inferences, Contradictions, and Unknowns",
    "### Approval Decisions",
    "## Requirements and Acceptance Criteria",
    "## Milestones and Ownership",
    "## Constraints and Limits",
    "## Fake / Block Table",
    "## Two-Sided Verifier Validation",
    "### Falsifiability",
    "### Hostile Pass",
    "## Exit-Gate Truth Table",
    "## Manual Design Answers",
    "### PROXY",
    "### FORGERY",
    "### ARITHMETIC",
    "### ACHIEVABLE",
    "### TRAP",
    "## Verification Map",
    "## Drift and Stop Conditions",
)
VALID_STATES = {
    "DRAFTED_UNSEALED",
    "MATERIALIZATION_REQUIRED",
    "SEALED_READY",
    "STALE_PACKET",
    "NO_GOAL_NEEDED",
    "BLOCKED",
    "UNSUPPORTED_NATIVE_GOAL",
}
VALID_TRUST = {"external_oracle", "operator_gate", "sealed_visible", "self_check"}


class PacketError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PacketError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PacketError(f"{path} must contain a JSON object")
    return value


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(rendered)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def resource_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_hosts(path: Path | None = None) -> dict[str, Any]:
    payload = load_json(path or resource_root() / "adapters" / "hosts.json")
    hosts = payload.get("hosts")
    if not isinstance(hosts, dict):
        raise PacketError("host adapter file requires a hosts object")
    return payload


def run_git(repo: Path, *args: str, allow_failure: bool = False) -> bytes:
    if shutil.which("git") is None:
        raise PacketError("required command is unavailable: git")
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise PacketError(f"cannot run git: {exc}") from exc
    if proc.returncode != 0 and not allow_failure:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise PacketError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def packet_relative_to_repo(packet_dir: Path, repo: Path) -> str | None:
    try:
        return packet_dir.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return None


def repository_status(repo: Path, packet_dir: Path) -> bytes:
    relative = packet_relative_to_repo(packet_dir, repo)
    args = ["status", "--porcelain=v1", "-z", "--", "."]
    if relative:
        args.extend([f":(exclude){relative}", f":(exclude){relative}/**"])
    return run_git(repo, *args)


def repository_snapshot(repo: Path, packet_dir: Path) -> dict[str, Any]:
    root = Path(run_git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    head = run_git(root, "rev-parse", "HEAD").decode().strip()
    branch_bytes = run_git(root, "symbolic-ref", "--short", "-q", "HEAD", allow_failure=True)
    branch = branch_bytes.decode().strip() or "DETACHED"
    status = repository_status(root, packet_dir)
    return {
        "root": str(root),
        "branch": branch,
        "head": head,
        "dirty": bool(status),
        "status_sha256": sha256_bytes(status),
    }


def goal_metrics(text: str) -> dict[str, int]:
    return {
        "unicode_characters": len(text),
        "utf8_bytes": len(text.encode("utf-8")),
        "lines": len(text.splitlines()),
    }


def lint_goal_text(text: str, adapter: dict[str, Any]) -> dict[str, Any]:
    if not text.strip():
        raise PacketError("goal.txt is empty")
    metrics = goal_metrics(text)
    if metrics["unicode_characters"] > PORTABLE_CHAR_LIMIT:
        raise PacketError(
            f"goal has {metrics['unicode_characters']} characters; portable limit is {PORTABLE_CHAR_LIMIT}"
        )
    if metrics["utf8_bytes"] > PORTABLE_BYTE_LIMIT:
        raise PacketError(f"goal has {metrics['utf8_bytes']} UTF-8 bytes; portable limit is {PORTABLE_BYTE_LIMIT}")
    objective_limit = adapter.get("objective_limit") or {}
    if objective_limit.get("value") is not None and metrics["unicode_characters"] > int(objective_limit["value"]):
        raise PacketError(
            f"goal has {metrics['unicode_characters']} characters; host limit is {objective_limit['value']}"
        )

    positions: list[int] = []
    for label in REQUIRED_LABELS:
        needle = f"{label}:"
        count = text.count(needle)
        if count != 1:
            raise PacketError(f"goal must contain {needle!r} exactly once; found {count}")
        positions.append(text.index(needle))
    if positions != sorted(positions):
        raise PacketError("goal labels are not in the required order")

    warnings: list[str] = []
    if metrics["unicode_characters"] < PREFERRED_MIN:
        warnings.append(f"goal is below the preferred {PREFERRED_MIN}-character lower bound; confirm nothing essential is missing")
    if metrics["unicode_characters"] > PREFERRED_MAX:
        warnings.append(f"goal exceeds the preferred {PREFERRED_MAX}-character upper bound")
    if metrics["unicode_characters"] > WARNING_CHARS:
        warnings.append(f"goal exceeds the {WARNING_CHARS}-character review threshold; move detail to spec.md")
    return {"metrics": metrics, "warnings": warnings}


def resolve_artifact(packet_dir: Path, entry: dict[str, Any], label: str) -> Path:
    raw_path = entry.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise PacketError(f"artifact {label} requires a path")
    path = Path(raw_path)
    resolved = (packet_dir / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(packet_dir.resolve())
    except ValueError as exc:
        raise PacketError(f"artifact {label} must stay inside packet directory: {resolved}") from exc
    if not resolved.is_file():
        raise PacketError(f"artifact {label} is missing: {resolved}")
    return resolved


def validate_packet_shape(packet: dict[str, Any]) -> None:
    if packet.get("schema_version") != SCHEMA_VERSION:
        raise PacketError(f"schema_version must be {SCHEMA_VERSION}")
    if packet.get("status") not in VALID_STATES:
        raise PacketError(f"invalid packet status: {packet.get('status')}")
    if not isinstance(packet.get("goal_id"), str) or not packet["goal_id"].strip():
        raise PacketError("goal_id is required")
    if not isinstance(packet.get("host"), str) or not packet["host"].strip():
        raise PacketError("host is required")
    repository = packet.get("repository")
    if not isinstance(repository, dict):
        raise PacketError("repository object is required")
    for key in ("root", "branch", "head", "dirty", "status_sha256"):
        if key not in repository:
            raise PacketError(f"repository.{key} is required")
    source_plan = packet.get("source_plan")
    if not isinstance(source_plan, dict):
        raise PacketError("source_plan object is required")
    if not isinstance(source_plan.get("path"), str):
        raise PacketError("source_plan.path must be a string")
    source_sha = source_plan.get("sha256")
    if not isinstance(source_sha, str) or len(source_sha) != 64 or any(char not in "0123456789abcdef" for char in source_sha):
        raise PacketError("source_plan.sha256 must be a lowercase SHA-256 value")
    if not isinstance(packet.get("rules_read"), list) or not packet["rules_read"]:
        raise PacketError("rules_read must contain at least one instruction path")
    research = packet.get("research_receipt")
    if not isinstance(research, dict):
        raise PacketError("research_receipt object is required")
    for key in ("code_evidence", "external_sources", "facts", "inferences", "contradictions", "unknowns", "approval_decisions"):
        if not isinstance(research.get(key), list):
            raise PacketError(f"research_receipt.{key} must be a list")
    if not research["code_evidence"]:
        raise PacketError("research_receipt.code_evidence must contain current repository evidence")
    if not research["facts"]:
        raise PacketError("research_receipt.facts must contain at least one grounded fact")
    no_external_reason = research.get("external_research_not_required_reason")
    if not research["external_sources"] and (not isinstance(no_external_reason, str) or not no_external_reason.strip()):
        raise PacketError(
            "research_receipt requires external_sources or a nonempty external_research_not_required_reason"
        )
    verification = packet.get("verification")
    if not isinstance(verification, dict):
        raise PacketError("verification object is required")
    if verification.get("trust") not in VALID_TRUST:
        raise PacketError(f"invalid verification trust: {verification.get('trust')}")
    if verification.get("trust") == "self_check":
        raise PacketError("self_check cannot seal a launchable packet because it cannot decide completion")
    operator_checks = verification.get("operator_checks")
    if not isinstance(operator_checks, list):
        raise PacketError("verification.operator_checks must be a list")
    if verification.get("trust") in {"operator_gate", "sealed_visible"} and not operator_checks:
        raise PacketError(f"verification trust {verification.get('trust')} requires at least one operator check")
    hostile_tree = verification.get("hostile_tree")
    if not isinstance(hostile_tree, str) or not hostile_tree.strip():
        raise PacketError("verification.hostile_tree must name the cheapest-fake tree")
    criteria = verification.get("expected_unmet_criteria")
    if not isinstance(criteria, list) or not criteria or not all(isinstance(item, str) and item for item in criteria):
        raise PacketError("verification.expected_unmet_criteria must contain named criteria")
    codes = verification.get("baseline_exit_codes")
    if not isinstance(codes, list) or not codes or not all(isinstance(code, int) and code != 0 for code in codes):
        raise PacketError("verification.baseline_exit_codes must contain nonzero integers")
    artifacts = packet.get("artifacts")
    if not isinstance(artifacts, dict) or not all(name in artifacts for name in ("goal", "spec", "baseline", "verify")):
        raise PacketError("artifacts must define goal, spec, baseline, and verify")


def validate_repository_binding(packet: dict[str, Any], packet_dir: Path) -> dict[str, Any]:
    expected = packet["repository"]
    repo = Path(str(expected["root"])).expanduser().resolve()
    if not repo.is_dir():
        raise PacketError(f"repository root does not exist: {repo}")
    actual = repository_snapshot(repo, packet_dir)
    mismatches = []
    for key in ("root", "branch", "head", "dirty", "status_sha256"):
        if actual[key] != expected.get(key):
            mismatches.append(f"{key}: expected {expected.get(key)!r}, found {actual[key]!r}")
    if mismatches:
        raise PacketError("STALE_PACKET repository drift: " + "; ".join(mismatches))
    return actual


def validate_spec(text: str) -> None:
    missing = [heading for heading in REQUIRED_SPEC_HEADINGS if heading not in text]
    if missing:
        raise PacketError("spec.md is missing required headings: " + ", ".join(missing))
    for answer_id in ("PROXY", "FORGERY", "ARITHMETIC", "ACHIEVABLE", "TRAP"):
        match = re.search(
            rf"^### {answer_id}\s*$\n(.*?)(?=^#{{2,3}} |\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        body = match.group(1).strip() if match else ""
        if not body or (body.startswith("<") and body.endswith(">")):
            raise PacketError(f"spec.md requires a nonblank written answer for {answer_id}")


def validate_baseline(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "plan-to-goal.baseline.v1":
        raise PacketError("baseline.json requires schema_version plan-to-goal.baseline.v1")
    if not isinstance(payload.get("anchor_id"), str) or not payload["anchor_id"].strip():
        raise PacketError("baseline.json requires anchor_id")
    frozen_ids = payload.get("frozen_ids")
    if not isinstance(frozen_ids, list) or not frozen_ids or not all(isinstance(item, str) and item for item in frozen_ids):
        raise PacketError("baseline.json requires a nonempty frozen_ids list")
    if len(frozen_ids) != len(set(frozen_ids)):
        raise PacketError("baseline.json frozen_ids must be unique")


def validate_iterations(packet: dict[str, Any], adapter: dict[str, Any]) -> dict[str, Any]:
    iterations = packet.get("iterations")
    if not isinstance(iterations, dict):
        raise PacketError("iterations object is required")
    config = adapter.get("iteration") or {}
    value = iterations.get("value")
    source = iterations.get("source")
    if source not in {"user", "host_default", "none"}:
        raise PacketError(f"invalid iteration source: {source}")
    if config.get("supported"):
        if value is None:
            value = config.get("default")
            source = "host_default"
        if not isinstance(value, int) or value < 1:
            raise PacketError("host requires a positive iteration value")
        maximum = config.get("maximum")
        if maximum is not None and value > int(maximum):
            raise PacketError(f"iteration value {value} exceeds host maximum {maximum}")
    elif value is not None or source != "none":
        raise PacketError("host has no verified iteration mechanism; use value null and source none")
    return {"value": value, "source": source}


def run_verifier_case(packet: dict[str, Any], verify_path: Path, root: Path, label: str) -> dict[str, Any]:
    if not root.is_dir():
        raise PacketError(f"{label} tree does not exist: {root}")
    if shutil.which("bash") is None:
        raise PacketError("required command is unavailable: bash")
    verification = packet["verification"]
    timeout = int(verification.get("timeout_seconds") or 300)
    try:
        proc = subprocess.run(
            ["bash", str(verify_path)],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "ANCHOR_ROOT": str(root), "REPO_ROOT": str(root)},
        )
    except subprocess.TimeoutExpired as exc:
        raise PacketError(f"{label} verifier timed out after {timeout}s") from exc
    except OSError as exc:
        raise PacketError(f"cannot run {label} verifier: {exc}") from exc
    combined = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
    if proc.returncode == 0:
        raise PacketError(f"{label} verifier returned 0; the verifier can pass without proving the outcome")
    expected_codes = packet["verification"]["baseline_exit_codes"]
    if proc.returncode not in expected_codes:
        raise PacketError(f"{label} verifier returned {proc.returncode}; expected one of {expected_codes}")
    missing = [criterion for criterion in verification["expected_unmet_criteria"] if criterion not in combined]
    if missing:
        raise PacketError(f"{label} verifier output omitted expected criteria: " + ", ".join(missing))
    return {
        "case": label,
        "root": str(root),
        "exit_code": proc.returncode,
        "expected_unmet_criteria": list(verification["expected_unmet_criteria"]),
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "checked_at": utc_now(),
    }


def run_two_sided_verifier(packet: dict[str, Any], verify_path: Path) -> dict[str, Any]:
    untouched = Path(packet["repository"]["root"]).resolve()
    hostile = Path(packet["verification"]["hostile_tree"]).expanduser().resolve()
    return {
        "falsifiability": run_verifier_case(packet, verify_path, untouched, "falsifiability"),
        "hostile_pass": run_verifier_case(packet, verify_path, hostile, "hostile_pass"),
    }


def command_lint(args: argparse.Namespace) -> dict[str, Any]:
    packet_dir = args.packet_dir.resolve()
    packet = load_json(packet_dir / "packet.json")
    validate_packet_shape(packet)
    hosts = load_hosts(args.adapters)
    adapter = hosts["hosts"].get(args.host or packet["host"])
    if not isinstance(adapter, dict):
        raise PacketError(f"no host adapter for {args.host or packet['host']}")
    goal_path = resolve_artifact(packet_dir, packet["artifacts"]["goal"], "goal")
    result = lint_goal_text(goal_path.read_text(encoding="utf-8"), adapter)
    return {"status": "PASS", "host": args.host or packet["host"], **result}


def command_seal(args: argparse.Namespace) -> dict[str, Any]:
    packet_dir = args.packet_dir.resolve()
    packet_path = packet_dir / "packet.json"
    packet = load_json(packet_path)
    validate_packet_shape(packet)
    if packet["status"] not in {"DRAFTED_UNSEALED", "MATERIALIZATION_REQUIRED"}:
        raise PacketError(f"seal requires DRAFTED_UNSEALED or MATERIALIZATION_REQUIRED, found {packet['status']}")

    hosts = load_hosts(args.adapters)
    adapter = hosts["hosts"].get(packet["host"])
    if not isinstance(adapter, dict):
        raise PacketError(f"no verified host adapter for {packet['host']}")
    native_goal = bool(adapter.get("native_goal"))

    goal_path = resolve_artifact(packet_dir, packet["artifacts"]["goal"], "goal")
    spec_path = resolve_artifact(packet_dir, packet["artifacts"]["spec"], "spec")
    baseline_path = resolve_artifact(packet_dir, packet["artifacts"]["baseline"], "baseline")
    verify_path = resolve_artifact(packet_dir, packet["artifacts"]["verify"], "verify")
    goal_result = lint_goal_text(goal_path.read_text(encoding="utf-8"), adapter)
    validate_spec(spec_path.read_text(encoding="utf-8"))
    validate_baseline(load_json(baseline_path))
    goal_text = goal_path.read_text(encoding="utf-8")
    if packet["verification"]["trust"] not in goal_text:
        raise PacketError("goal.txt must name the packet verification trust level")
    if "packet.json" not in goal_text or "spec.md" not in goal_text:
        raise PacketError("goal.txt must name packet.json and spec.md")
    verify_relative = verify_path.relative_to(packet_dir).as_posix()
    accepted_commands = {
        f"bash {verify_path}",
        f"bash {verify_relative}",
        f"bash ./{verify_relative}",
    }
    if packet["verification"].get("command") not in accepted_commands:
        raise PacketError(
            "verification.command must be the exact verifier artifact path: " + ", ".join(sorted(accepted_commands))
        )
    snapshot = validate_repository_binding(packet, packet_dir)
    iterations = validate_iterations(packet, adapter)
    verifier_validation = run_two_sided_verifier(packet, verify_path)

    for name, path in (("goal", goal_path), ("spec", spec_path), ("baseline", baseline_path), ("verify", verify_path)):
        packet["artifacts"][name]["sha256"] = sha256_file(path)
        packet["artifacts"][name]["path"] = str(path.relative_to(packet_dir))
    result_status = "SEALED_READY" if native_goal else "UNSUPPORTED_NATIVE_GOAL"
    packet["status"] = result_status
    packet["adapter_version"] = str(adapter.get("tested_version") or "unknown")
    packet["repository"].update(snapshot)
    packet["iterations"] = iterations
    packet["goal_size"] = goal_result["metrics"]
    packet["baseline_verifier"] = verifier_validation["falsifiability"]
    packet["verifier_validation"] = verifier_validation
    packet["sealed_at"] = utc_now()
    write_json_atomic(packet_path, packet)
    return {
        "status": result_status,
        "host": packet["host"],
        "adapter_version": packet["adapter_version"],
        "goal_size": packet["goal_size"],
        "warnings": goal_result["warnings"],
        "iterations": packet["iterations"],
        "verification_trust": packet["verification"]["trust"],
        "artifact_hashes": {name: value["sha256"] for name, value in packet["artifacts"].items()},
        "baseline_verifier": verifier_validation["falsifiability"],
        "verifier_validation": verifier_validation,
    }


def command_check(args: argparse.Namespace) -> dict[str, Any]:
    packet_dir = args.packet_dir.resolve()
    packet = load_json(packet_dir / "packet.json")
    validate_packet_shape(packet)
    if packet["status"] not in {"SEALED_READY", "UNSUPPORTED_NATIVE_GOAL"}:
        raise PacketError(f"check requires a sealed packet, found {packet['status']}")
    hosts = load_hosts(args.adapters)
    adapter = hosts["hosts"].get(packet["host"])
    if not isinstance(adapter, dict):
        raise PacketError(f"no verified host adapter for {packet['host']}")

    artifacts: dict[str, Path] = {}
    for name in ("goal", "spec", "baseline", "verify"):
        path = resolve_artifact(packet_dir, packet["artifacts"][name], name)
        expected = packet["artifacts"][name].get("sha256")
        actual = sha256_file(path)
        if actual != expected:
            raise PacketError(f"artifact hash mismatch for {name}: expected {expected}, found {actual}")
        artifacts[name] = path
    lint = lint_goal_text(artifacts["goal"].read_text(encoding="utf-8"), adapter)
    validate_spec(artifacts["spec"].read_text(encoding="utf-8"))
    validate_baseline(load_json(artifacts["baseline"]))
    validate_repository_binding(packet, packet_dir)
    verifier_validation = run_two_sided_verifier(packet, artifacts["verify"])
    result: dict[str, Any] = {
        "status": "PASS",
        "packet_status": packet["status"],
        "goal_size": lint["metrics"],
        "warnings": lint["warnings"],
        "verification_trust": packet["verification"]["trust"],
        "verifier_validation": verifier_validation,
    }
    if args.run_verifier:
        result["verifier"] = verifier_validation["falsifiability"]
    return result


def command_print_goal(args: argparse.Namespace) -> None:
    packet_dir = args.packet_dir.resolve()
    packet = load_json(packet_dir / "packet.json")
    validate_packet_shape(packet)
    if packet["status"] not in {"SEALED_READY", "UNSUPPORTED_NATIVE_GOAL"}:
        raise PacketError(f"print-goal requires a sealed packet, found {packet['status']}")
    goal_path = resolve_artifact(packet_dir, packet["artifacts"]["goal"], "goal")
    sys.stdout.write(goal_path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lint, seal, and verify plan-to-goal packets.")
    parser.add_argument("--adapters", type=Path, help="Override hosts.json path for testing.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    lint = subparsers.add_parser("lint", help="Validate packet shape and goal size/labels without sealing.")
    lint.add_argument("packet_dir", type=Path)
    lint.add_argument("--host", help="Override packet host for lint only.")
    seal = subparsers.add_parser("seal", help="Validate and seal a launch-ready packet.")
    seal.add_argument("packet_dir", type=Path)
    check = subparsers.add_parser("check", help="Recheck hashes, repository binding, and optional verifier execution.")
    check.add_argument("packet_dir", type=Path)
    check.add_argument("--run-verifier", action="store_true")
    print_goal = subparsers.add_parser("print-goal", help="Print only the wrapper-free goal from a sealed packet.")
    print_goal.add_argument("packet_dir", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "lint":
            result = command_lint(args)
            print(json.dumps(result, indent=2, sort_keys=True))
        elif args.command == "seal":
            result = command_seal(args)
            print(json.dumps(result, indent=2, sort_keys=True))
        elif args.command == "check":
            result = command_check(args)
            print(json.dumps(result, indent=2, sort_keys=True))
        elif args.command == "print-goal":
            command_print_goal(args)
        else:
            raise PacketError(f"unsupported command: {args.command}")
    except PacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
