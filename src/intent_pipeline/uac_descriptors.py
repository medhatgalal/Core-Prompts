from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

DESCRIPTOR_VERSION = "capability-fabric.descriptor.v0"


def capability_dir(repo_root: Path) -> Path:
    return repo_root / ".meta" / "capabilities"


def descriptor_path(repo_root: Path, slug: str) -> Path:
    return capability_dir(repo_root) / f"{slug}.json"


def source_note_path(repo_root: Path, slug: str) -> Path:
    return capability_dir(repo_root) / f"{slug}.sources.md"


def load_descriptor(repo_root: Path, slug: str) -> dict[str, object] | None:
    path = descriptor_path(repo_root, slug)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_descriptor(repo_root: Path, slug: str, descriptor: Mapping[str, object]) -> Path:
    path = descriptor_path(repo_root, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")
    return path


def normalize_descriptor_summary(value: object, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    summary = value.strip()
    if not summary:
        return fallback
    if summary.startswith("---") or "\n#" in summary or len(summary) > 320:
        return fallback
    return summary


def build_descriptor(
    *,
    manifest: Mapping[str, object],
    display_name: str | None = None,
    family_slug: str | None = None,
    shared_summary: str | None = None,
    shared_constraints: Sequence[str] = (),
    modes: Sequence[Mapping[str, object]] = (),
    benchmark_sources: Sequence[Mapping[str, object]] = (),
    quality_profile: str | None = None,
    quality_status: str | None = None,
    judge_reports: Sequence[Mapping[str, object]] = (),
    consumption_hints: Mapping[str, object] | None = None,
    quality_pass_count: int | None = None,
    quality_stop_reason: str | None = None,
) -> dict[str, object]:
    payload = json.loads(json.dumps(manifest))
    minimal = dict(payload.get("layers", {}).get("minimal", {}))
    fallback_summary = str(minimal.get("summary") or "")
    minimal["summary"] = normalize_descriptor_summary(minimal.get("summary"), fallback_summary)
    if display_name is not None:
        minimal["display_name"] = display_name
    elif minimal.get("display_name") is None:
        minimal["display_name"] = str(payload.get("slug") or "")
    payload.setdefault("layers", {})
    payload["layers"]["minimal"] = minimal
    payload["descriptor_version"] = DESCRIPTOR_VERSION
    payload["display_name"] = display_name or str(minimal.get("display_name") or payload.get("slug") or "")
    payload["family_slug"] = family_slug or payload.get("slug")
    payload["shared_summary"] = normalize_descriptor_summary(
        shared_summary,
        str(payload.get("layers", {}).get("minimal", {}).get("summary", "")),
    )
    payload["shared_constraints"] = list(shared_constraints)
    payload["modes"] = list(modes)
    payload["benchmark_sources"] = list(benchmark_sources)
    if quality_profile is not None:
        payload["quality_profile"] = quality_profile
    if quality_status is not None:
        payload["quality_status"] = quality_status
    if judge_reports:
        payload["judge_reports"] = list(judge_reports)
    if consumption_hints is not None:
        payload["consumption_hints"] = dict(consumption_hints)
    if quality_pass_count is not None:
        payload["quality_pass_count"] = quality_pass_count
    if quality_stop_reason is not None:
        payload["quality_stop_reason"] = quality_stop_reason
    return payload


def write_source_note(
    repo_root: Path,
    slug: str,
    *,
    title: str,
    source_refs: Sequence[str],
    benchmark_sources: Sequence[Mapping[str, object]] = (),
    rationale: str,
) -> Path:
    path = source_note_path(repo_root, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", "", "## Imported Sources"]
    lines.extend(f"- `{item}`" for item in source_refs)
    if benchmark_sources:
        lines.extend(["", "## Benchmarks"])
        for item in benchmark_sources:
            label = str(item.get("label") or item.get("url") or "benchmark")
            url = str(item.get("url") or "")
            note = str(item.get("note") or "")
            if url:
                lines.append(f"- {label}: {url}" + (f" — {note}" if note else ""))
            else:
                lines.append(f"- {label}" + (f" — {note}" if note else ""))
    lines.extend(["", "## Rationale", rationale.strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
