from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from .contracts import artifact_hash, canonical_json


class ArtifactError(RuntimeError):
    """Raised when immutable evaluation artifacts are incomplete or corrupt."""


def evaluator_package_hash(repo_root: Path) -> str:
    package_root = repo_root / "src" / "core_prompts_eval"
    entries: list[dict[str, str]] = []
    for path in sorted(package_root.glob("*.py")):
        entries.append({"path": str(path.relative_to(repo_root)), "sha256": artifact_hash(path)})
    return artifact_hash({"files": entries})


def write_run_artifacts(
    reports_root: Path,
    *,
    run_id: str,
    preregistered_plan: Mapping[str, Any],
    manifest: Mapping[str, Any],
    trial_records: Iterable[Mapping[str, Any]],
    receipt_payloads: Iterable[Mapping[str, Any]],
    traces: Iterable[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> Path:
    reports_root.mkdir(parents=True, exist_ok=True)
    destination = reports_root / run_id
    if destination.exists():
        raise ArtifactError(f"immutable run directory already exists: {destination}")
    temporary = Path(tempfile.mkdtemp(prefix=f".{run_id}.", dir=reports_root))
    try:
        (temporary / "trials").mkdir()
        (temporary / "traces").mkdir()
        _write_json(temporary / "preregistered-plan.json", preregistered_plan)
        trace_hashes: list[str] = []
        for index, trace in enumerate(traces):
            trace_path = temporary / "traces" / f"{index:06d}.json"
            _write_json(trace_path, trace)
            trace_hashes.append(artifact_hash(trace_path))
        manifest_payload = dict(manifest)
        manifest_payload["raw_trace_hashes"] = trace_hashes
        _write_json(temporary / "manifest.json", manifest_payload)
        _write_jsonl(temporary / "trials" / "records.jsonl", trial_records)
        _write_jsonl(temporary / "trials" / "receipt-payloads.jsonl", receipt_payloads)
        _write_jsonl(temporary / "scores.jsonl", ())
        _write_json(temporary / "summary.json", summary)
        _write_hash_chain(temporary)
        _fsync_tree(temporary)
        os.replace(temporary, destination)
        _fsync_directory(reports_root)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return destination


def verify_artifact_chain(run_dir: Path) -> dict[str, Any]:
    chain_path = run_dir / "hash-chain.json"
    try:
        payload = json.loads(chain_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"cannot load artifact hash chain: {exc}") from exc
    entries = payload.get("entries")
    if payload.get("schema_version") != "EvalArtifactChain.v1" or not isinstance(entries, list):
        raise ArtifactError("invalid artifact hash chain")
    previous = "0" * 64
    for raw in entries:
        if not isinstance(raw, Mapping):
            raise ArtifactError("invalid artifact chain entry")
        relative = str(raw.get("path") or "")
        if relative.startswith("/") or ".." in Path(relative).parts:
            raise ArtifactError("artifact chain contains an unsafe path")
        path = run_dir / relative
        digest = artifact_hash(path)
        if digest != raw.get("sha256"):
            raise ArtifactError(f"artifact digest mismatch: {relative}")
        chained = artifact_hash(f"{previous}\0{relative}\0{digest}")
        if chained != raw.get("chain_sha256"):
            raise ArtifactError(f"artifact chain mismatch: {relative}")
        previous = chained
    if previous != payload.get("root_sha256"):
        raise ArtifactError("artifact chain root mismatch")
    return {"schema_version": "EvalArtifactVerification.v1", "status": "valid", "root_sha256": previous, "files": len(entries)}


def _write_hash_chain(root: Path) -> None:
    previous = "0" * 64
    entries: list[dict[str, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "hash-chain.json"):
        relative = path.relative_to(root).as_posix()
        digest = artifact_hash(path)
        previous = artifact_hash(f"{previous}\0{relative}\0{digest}")
        entries.append({"path": relative, "sha256": digest, "chain_sha256": previous})
    _write_json(
        root / "hash-chain.json",
        {"schema_version": "EvalArtifactChain.v1", "entries": entries, "root_sha256": previous},
    )


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, payloads: Iterable[Mapping[str, Any]]) -> None:
    content = "".join(canonical_json(dict(payload)) + "\n" for payload in payloads)
    path.write_text(content, encoding="utf-8")


def _fsync_tree(root: Path) -> None:
    for path in (item for item in root.rglob("*") if item.is_file()):
        with path.open("rb") as handle:
            os.fsync(handle.fileno())
    for path in sorted((item for item in root.rglob("*") if item.is_dir()), reverse=True):
        _fsync_directory(path)
    _fsync_directory(root)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


__all__ = ["ArtifactError", "evaluator_package_hash", "verify_artifact_chain", "write_run_artifacts"]
