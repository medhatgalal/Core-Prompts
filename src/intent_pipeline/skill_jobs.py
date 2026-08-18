from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


REQUIRED_FIELDS = {
    "primary_job",
    "use_when",
    "works_on",
    "main_output",
    "not_for",
    "authority",
    "routing_question",
    "nearest_neighbors",
    "shape",
    "portfolio_action",
}


def load_skill_job_map(path: Path, expected_slugs: Iterable[str]) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "SkillJobMap.v1":
        raise ValueError("skill job map must use SkillJobMap.v1")
    skills = payload.get("skills")
    if not isinstance(skills, dict):
        raise ValueError("skill job map requires a skills object")
    expected = set(expected_slugs)
    actual = set(skills)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"skill job map slug mismatch; missing={missing}, extra={extra}")
    for slug, job in skills.items():
        if not isinstance(job, dict):
            raise ValueError(f"{slug}: job contract must be an object")
        missing_fields = sorted(REQUIRED_FIELDS - set(job))
        if missing_fields:
            raise ValueError(f"{slug}: job contract missing {missing_fields}")
        for field in REQUIRED_FIELDS - {"nearest_neighbors"}:
            if not isinstance(job[field], str) or not job[field].strip():
                raise ValueError(f"{slug}: {field} must be a non-empty string")
        neighbors = job["nearest_neighbors"]
        if not isinstance(neighbors, list) or any(item not in expected or item == slug for item in neighbors):
            raise ValueError(f"{slug}: nearest_neighbors must reference other known skills")
    return payload


def render_skill_job_map(payload: Mapping[str, Any], display_names: Mapping[str, str]) -> str:
    lines = [
        "# Skill Job Map",
        "",
        "This is a plain-English routing map, not behavioral proof and not a merger plan. The canonical behavior remains in `ssot/`.",
        "",
        "Portfolio actions mean:",
        "",
        "- `keep`: the boundary is already focused.",
        "- `keep_and_clarify_boundary`: preserve the skill and sharpen how it differs from neighbors.",
        "- `keep_but_review_scope`: preserve it, then test whether its Swiss-army or advisory scope is too broad.",
        "- `experimental_keep_pending_evidence`: keep the experiment separate until routing and preservation evidence exists.",
        "- `keep_and_improve_process`: preserve the capability and improve its evidence or workflow controls.",
        "",
        "No skill is marked for merger or deletion because current evidence does not justify either action.",
        "",
        "| Skill | Primary job | Use when | Main output | Not for | Closest neighbors | Portfolio action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for slug, job in payload["skills"].items():
        name = display_names.get(slug, slug)
        neighbors = ", ".join(f"`{item}`" for item in job["nearest_neighbors"]) or "none"
        cells = [
            f"`{slug}`<br>{name}",
            job["primary_job"],
            job["use_when"],
            job["main_output"],
            job["not_for"],
            neighbors,
            f"`{job['portfolio_action']}`",
        ]
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells) + " |")
    lines.extend(
        [
            "",
            "## Routing Questions",
            "",
        ]
    )
    for slug, job in payload["skills"].items():
        lines.append(f"- `{slug}`: {job['routing_question']}")
    lines.append("")
    return "\n".join(lines)
