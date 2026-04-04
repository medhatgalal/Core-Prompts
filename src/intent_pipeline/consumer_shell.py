from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence


def _manifest_entries(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in manifest.get("ssot_sources") or [] if isinstance(item, Mapping)]


def _minimal(entry: Mapping[str, Any]) -> dict[str, Any]:
    return dict((entry.get("layers") or {}).get("minimal") or {})


def _consumption_hints(entry: Mapping[str, Any]) -> dict[str, Any]:
    return dict(entry.get("consumption_hints") or {})


def _slug(entry: Mapping[str, Any]) -> str:
    return str(entry.get("slug") or "")


def _display_name(entry: Mapping[str, Any]) -> str:
    minimal = _minimal(entry)
    return str(entry.get("display_name") or minimal.get("display_name") or _slug(entry))


def _surface_map(entry: Mapping[str, Any]) -> dict[str, list[str]]:
    return {
        cli: list(values)
        for cli, values in dict(_minimal(entry).get("emitted_surfaces") or {}).items()
        if values
    }


def _supported_clis(entry: Mapping[str, Any]) -> list[str]:
    surfaces = _surface_map(entry)
    return sorted(cli for cli, values in surfaces.items() if values)


def _starter_score(entry: Mapping[str, Any]) -> tuple[int, int, str]:
    minimal = _minimal(entry)
    tags = set(minimal.get("domain_tags") or [])
    broad_tags = {"analysis", "review", "planning", "debugging", "context", "architecture", "testing"}
    preferred_use_cases = list(_consumption_hints(entry).get("preferred_use_cases") or [])
    capability_type = str(minimal.get("capability_type") or "skill")
    score = len(tags & broad_tags) + min(len(preferred_use_cases), 3)
    if capability_type == "both":
        score += 2
    elif capability_type == "skill":
        score += 1
    return (score, len(_supported_clis(entry)), _slug(entry))


def _entry_catalog_record(entry: Mapping[str, Any]) -> dict[str, Any]:
    minimal = _minimal(entry)
    hints = _consumption_hints(entry)
    return {
        "slug": _slug(entry),
        "display_name": _display_name(entry),
        "summary": str(minimal.get("summary") or ""),
        "description": str(minimal.get("summary") or ""),
        "capability_type": str(minimal.get("capability_type") or ""),
        "install_target": dict(minimal.get("install_target") or {}),
        "emitted_surfaces": _surface_map(entry),
        "supported_clis": _supported_clis(entry),
        "supported_agents": list(minimal.get("supported_agents") or []),
        "version": minimal.get("version"),
        "author": minimal.get("author"),
        "compatibility": minimal.get("compatibility"),
        "required_inputs": list(minimal.get("required_inputs") or []),
        "expected_outputs": list(minimal.get("expected_outputs") or []),
        "domain_tags": list(minimal.get("domain_tags") or []),
        "invocation_hints": list(entry.get("invocation_hints") or []),
        "preferred_use_cases": list(hints.get("preferred_use_cases") or []),
        "artifact_conventions": list(hints.get("artifact_conventions") or []),
        "invocation_style": hints.get("invocation_style"),
        "requires_human_confirmation": hints.get("requires_human_confirmation"),
        "quality_profile": entry.get("quality_profile"),
        "quality_status": entry.get("quality_status"),
        "overlap_candidates": list(((entry.get("layers") or {}).get("expanded") or {}).get("overlap_candidates") or []),
        "resources": list(minimal.get("resources") or []),
    }


def build_capability_catalog(manifest: Mapping[str, Any]) -> dict[str, Any]:
    entries = sorted(_manifest_entries(manifest), key=lambda item: _display_name(item).casefold())
    records = [_entry_catalog_record(entry) for entry in entries]
    by_cli: dict[str, list[str]] = defaultdict(list)
    by_tag: dict[str, list[str]] = defaultdict(list)
    by_install_target: dict[str, list[str]] = defaultdict(list)
    for record in records:
        for cli in record["supported_clis"]:
            by_cli[cli].append(record["slug"])
        for tag in record["domain_tags"]:
            by_tag[tag].append(record["slug"])
        target = str((record.get("install_target") or {}).get("recommended") or "unknown")
        by_install_target[target].append(record["slug"])

    start_here = [
        _slug(entry)
        for entry in sorted(entries, key=_starter_score, reverse=True)[:5]
    ]

    return {
        "schema_version": "capability-fabric.consumer-shell.v1",
        "entry_count": len(records),
        "capabilities": records,
        "views": {
            "start_here": start_here,
            "by_cli": {cli: sorted(slugs) for cli, slugs in sorted(by_cli.items())},
            "by_use_case": {tag: sorted(slugs) for tag, slugs in sorted(by_tag.items())},
            "by_install_target": {target: sorted(slugs) for target, slugs in sorted(by_install_target.items())},
        },
    }


def load_previous_manifest_from_git(repo_root: Path, ref: str = "HEAD") -> dict[str, Any] | None:
    try:
        proc = subprocess.run(
            ["git", "show", f"{ref}:.meta/manifest.json"],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=True,
        )
    except Exception:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def _compare_list(before: Sequence[Any], after: Sequence[Any]) -> tuple[list[Any], list[Any]]:
    left = list(before)
    right = list(after)
    added = [item for item in right if item not in left]
    removed = [item for item in left if item not in right]
    return added, removed


def _entry_delta(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    prev_min = _minimal(previous)
    cur_min = _minimal(current)
    changed_fields: list[str] = []
    material_fields: list[str] = []
    details: dict[str, Any] = {}
    field_names = (
        "summary",
        "capability_type",
        "version",
        "author",
        "compatibility",
        "supported_agents",
    )
    material_field_set = {"summary", "capability_type", "compatibility", "supported_agents"}
    for name in field_names:
        before = prev_min.get(name)
        after = cur_min.get(name)
        if before != after:
            changed_fields.append(name)
            details[name] = {"before": before, "after": after}
            if name in material_field_set:
                material_fields.append(name)

    if _display_name(previous) != _display_name(current):
        changed_fields.append("display_name")
        details["display_name"] = {"before": _display_name(previous), "after": _display_name(current)}
        material_fields.append("display_name")

    prev_target = str((prev_min.get("install_target") or {}).get("recommended") or "")
    cur_target = str((cur_min.get("install_target") or {}).get("recommended") or "")
    if prev_target != cur_target:
        changed_fields.append("install_target")
        details["install_target"] = {"before": prev_target, "after": cur_target}
        material_fields.append("install_target")

    added_hints, removed_hints = _compare_list(previous.get("invocation_hints") or [], current.get("invocation_hints") or [])
    if added_hints or removed_hints:
        changed_fields.append("invocation_hints")
        details["invocation_hints"] = {"added": added_hints, "removed": removed_hints}
        material_fields.append("invocation_hints")

    prev_outputs = list(prev_min.get("expected_outputs") or [])
    cur_outputs = list(cur_min.get("expected_outputs") or [])
    added_outputs, removed_outputs = _compare_list(prev_outputs, cur_outputs)
    if added_outputs or removed_outputs:
        changed_fields.append("expected_outputs")
        details["expected_outputs"] = {"added": added_outputs, "removed": removed_outputs}
        material_fields.append("expected_outputs")

    prev_use_cases = list(_consumption_hints(previous).get("preferred_use_cases") or [])
    cur_use_cases = list(_consumption_hints(current).get("preferred_use_cases") or [])
    added_use_cases, removed_use_cases = _compare_list(prev_use_cases, cur_use_cases)
    if added_use_cases or removed_use_cases:
        changed_fields.append("preferred_use_cases")
        details["preferred_use_cases"] = {"added": added_use_cases, "removed": removed_use_cases}
        material_fields.append("preferred_use_cases")

    prev_surfaces = sorted(previous.get("expected_surface_names") or [])
    cur_surfaces = sorted(current.get("expected_surface_names") or [])
    if prev_surfaces != cur_surfaces:
        changed_fields.append("expected_surface_names")
        details["expected_surface_names"] = {"before": prev_surfaces, "after": cur_surfaces}
        material_fields.append("expected_surface_names")

    return {
        "slug": _slug(current),
        "display_name": _display_name(current),
        "changed_fields": changed_fields,
        "material_fields": material_fields,
        "details": details,
        "material": bool(material_fields),
    }


def build_release_delta(current_manifest: Mapping[str, Any], previous_manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    current_entries = {_slug(entry): entry for entry in _manifest_entries(current_manifest)}
    previous_entries = {_slug(entry): entry for entry in _manifest_entries(previous_manifest or {})}
    new_slugs = sorted(slug for slug in current_entries if slug not in previous_entries)
    removed_slugs = sorted(slug for slug in previous_entries if slug not in current_entries)
    changed = []
    for slug in sorted(current_entries):
        if slug not in previous_entries:
            continue
        delta = _entry_delta(previous_entries[slug], current_entries[slug])
        if delta["changed_fields"]:
            changed.append(delta)
    material_changes = [item for item in changed if item["material"]]
    return {
        "schema_version": "capability-fabric.release-delta.v1",
        "comparison_basis": "git:HEAD .meta/manifest.json" if previous_manifest else "unavailable",
        "new_capabilities": [
            {"slug": slug, "display_name": _display_name(current_entries[slug])}
            for slug in new_slugs
        ],
        "removed_capabilities": [
            {"slug": slug, "display_name": _display_name(previous_entries[slug])}
            for slug in removed_slugs
        ],
        "changed_capabilities": changed,
        "material_changes": material_changes,
        "summary": {
            "new_count": len(new_slugs),
            "removed_count": len(removed_slugs),
            "changed_count": len(changed),
            "material_change_count": len(material_changes),
        },
    }


def build_status_payload(
    manifest: Mapping[str, Any],
    *,
    build_report: Mapping[str, Any] | None,
    validation_report: Mapping[str, Any] | None,
    smoke_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    validation_errors = int((validation_report or {}).get("validation_errors") or 0)
    validation_warnings = int((validation_report or {}).get("validation_warnings") or 0)
    smoke_failures = len(list((smoke_report or {}).get("failures") or []))
    smoke_warnings = len(list((smoke_report or {}).get("warnings") or []))
    if validation_errors or smoke_failures:
        health = "error"
    elif validation_warnings or smoke_warnings:
        health = "warn"
    else:
        health = "ok"
    return {
        "schema_version": "capability-fabric.status.v1",
        "health": health,
        "entry_count": len(_manifest_entries(manifest)),
        "generated_at": (build_report or {}).get("generated_at"),
        "validated_at": (validation_report or {}).get("validated_at"),
        "smoked_at": (smoke_report or {}).get("smoked_at"),
        "build": dict(build_report or {}),
        "validation": dict(validation_report or {}),
        "smoke": dict(smoke_report or {}),
    }


def _safe_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_status_inputs(repo_root: Path) -> dict[str, dict[str, Any] | None]:
    return {
        "build_report": _safe_json(repo_root / "reports" / "build-surfaces" / "latest.json"),
        "validation_report": _safe_json(repo_root / "reports" / "validation" / "latest.json"),
        "smoke_report": _safe_json(repo_root / "reports" / "smoke-clis" / "latest.json"),
    }


def render_catalog_markdown(catalog: Mapping[str, Any]) -> str:
    entries = list(catalog.get("capabilities") or [])
    start_here = list((catalog.get("views") or {}).get("start_here") or [])
    by_cli = dict((catalog.get("views") or {}).get("by_cli") or {})
    by_use_case = dict((catalog.get("views") or {}).get("by_use_case") or {})
    entry_by_slug = {item["slug"]: item for item in entries if isinstance(item, Mapping) and item.get("slug")}
    lines = [
        "# Capability Catalog",
        "",
        "Generated from canonical manifest and descriptor metadata. Use this page to see what Core-Prompts ships, what each capability is for, and where it lands.",
        "",
        f"- Capability count: `{catalog.get('entry_count', 0)}`",
        "",
        "## Start Here",
    ]
    for slug in start_here:
        entry = entry_by_slug.get(slug)
        if not entry:
            continue
        lines.append(f"- `{slug}` — {entry.get('display_name')}: {entry.get('summary')}")
    lines.extend(["", "## By CLI"])
    for cli, slugs in sorted(by_cli.items()):
        rendered = ", ".join(f"`{slug}`" for slug in slugs)
        lines.append(f"- `{cli}`: {rendered}")
    lines.extend(["", "## By Use Case"])
    for tag, slugs in sorted(by_use_case.items()):
        rendered = ", ".join(f"`{slug}`" for slug in slugs)
        lines.append(f"- `{tag}`: {rendered}")
    lines.extend(["", "## All Capabilities"])
    for entry in entries:
        compatible = entry.get("compatibility")
        version = entry.get("version")
        author = entry.get("author")
        lines.append(f"### {entry.get('display_name')}")
        lines.append(f"- Slug: `{entry.get('slug')}`")
        lines.append(f"- Type: `{entry.get('capability_type')}`")
        lines.append(f"- Install target: `{(entry.get('install_target') or {}).get('recommended', 'unknown')}`")
        lines.append(f"- Supported CLIs: `{', '.join(entry.get('supported_clis') or [])}`")
        if version:
            lines.append(f"- Version: `{version}`")
        if author:
            lines.append(f"- Author: `{author}`")
        if compatible:
            lines.append(f"- Compatibility: {compatible}")
        if entry.get("invocation_hints"):
            lines.append("- Invocation hints:")
            for hint in entry["invocation_hints"]:
                lines.append(f"  - {hint}")
        lines.append(f"- Summary: {entry.get('summary')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_release_delta_markdown(delta: Mapping[str, Any]) -> str:
    lines = [
        "# Release Delta",
        "",
        f"- Comparison basis: `{delta.get('comparison_basis')}`",
        f"- New capabilities: `{delta.get('summary', {}).get('new_count', 0)}`",
        f"- Removed capabilities: `{delta.get('summary', {}).get('removed_count', 0)}`",
        f"- Changed capabilities: `{delta.get('summary', {}).get('changed_count', 0)}`",
        f"- Material changes: `{delta.get('summary', {}).get('material_change_count', 0)}`",
        "",
        "## New Capabilities",
    ]
    for item in delta.get("new_capabilities") or []:
        lines.append(f"- `{item.get('slug')}` — {item.get('display_name')}")
    if not (delta.get("new_capabilities") or []):
        lines.append("- none")
    lines.extend(["", "## Material Changes"])
    for item in delta.get("material_changes") or []:
        lines.append(f"- `{item.get('slug')}` — changed `{', '.join(item.get('material_fields') or [])}`")
    if not (delta.get("material_changes") or []):
        lines.append("- none")
    lines.extend(["", "## All Changed Capabilities"])
    for item in delta.get("changed_capabilities") or []:
        lines.append(f"- `{item.get('slug')}` — changed `{', '.join(item.get('changed_fields') or [])}`")
    if not (delta.get("changed_capabilities") or []):
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def render_status_markdown(status: Mapping[str, Any]) -> str:
    validation = dict(status.get("validation") or {})
    smoke = dict(status.get("smoke") or {})
    lines = [
        "# Consumer Status",
        "",
        "Generated from the latest build, validation, and smoke reports. This is the user-facing health snapshot for packaged Core-Prompts artifacts.",
        "",
        f"- Overall health: `{status.get('health')}`",
        f"- Capability count: `{status.get('entry_count')}`",
        f"- Latest build: `{status.get('generated_at') or 'unknown'}`",
        f"- Latest validation: `{status.get('validated_at') or 'unknown'}`",
        f"- Latest smoke: `{status.get('smoked_at') or 'unknown'}`",
        "",
        "## Validation",
        f"- Errors: `{validation.get('validation_errors', 'unknown')}`",
        f"- Warnings: `{validation.get('validation_warnings', 'unknown')}`",
        "",
        "## Smoke",
    ]
    if smoke:
        failures = list(smoke.get("failures") or [])
        warnings = list(smoke.get("warnings") or [])
        lines.append(f"- Failures: `{len(failures)}`")
        lines.append(f"- Warnings: `{len(warnings)}`")
    else:
        lines.append("- No smoke report recorded yet.")
    return "\n".join(lines).rstrip() + "\n"
