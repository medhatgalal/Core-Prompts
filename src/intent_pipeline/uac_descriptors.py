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


def build_descriptor(
    *,
    manifest: Mapping[str, object],
    family_slug: str | None = None,
    shared_summary: str | None = None,
    shared_constraints: Sequence[str] = (),
    modes: Sequence[Mapping[str, object]] = (),
    benchmark_sources: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    payload = json.loads(json.dumps(manifest))
    payload["descriptor_version"] = DESCRIPTOR_VERSION
    payload["family_slug"] = family_slug or payload.get("slug")
    payload["shared_summary"] = shared_summary or payload.get("layers", {}).get("minimal", {}).get("summary", "")
    payload["shared_constraints"] = list(shared_constraints)
    payload["modes"] = list(modes)
    payload["benchmark_sources"] = list(benchmark_sources)
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
