from __future__ import annotations

import json
from pathlib import Path

import pytest

from intent_pipeline.skill_jobs import load_skill_job_map, load_skill_job_map_for_build, render_skill_job_map


ROOT = Path(__file__).resolve().parents[1]
JOB_MAP = ROOT / ".meta" / "skill-job-map.json"


def test_job_map_covers_every_skill_exactly_once() -> None:
    slugs = sorted(path.stem for path in (ROOT / "ssot").glob("*.md"))
    payload = load_skill_job_map(JOB_MAP, slugs)

    assert sorted(payload["skills"]) == slugs
    assert payload["review_status"] == "draft_for_human_review"


def test_job_map_preserves_user_identified_product_repo_and_code_boundaries() -> None:
    skills = load_skill_job_map(JOB_MAP, (path.stem for path in (ROOT / "ssot").glob("*.md")))["skills"]

    assert "product feature" in skills["feature-status"]["primary_job"].lower()
    assert "repository activity" in skills["eng-report"]["primary_job"].lower()
    assert "structural risks" in skills["codebase-health-audit"]["primary_job"].lower()
    assert len({skills[slug]["primary_job"] for slug in ("architecture", "converge", "mentor")}) == 3


def test_job_map_does_not_claim_unproven_merger_or_deletion() -> None:
    payload = json.loads(JOB_MAP.read_text(encoding="utf-8"))
    actions = {job["portfolio_action"] for job in payload["skills"].values()}

    assert not actions.intersection({"merge", "delete", "retire"})


def test_job_map_rejects_missing_or_unknown_skills(tmp_path: Path) -> None:
    path = tmp_path / "jobs.json"
    path.write_text(
        json.dumps({"schema_version": "SkillJobMap.v1", "skills": {"unknown": {}}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="slug mismatch"):
        load_skill_job_map(path, ["known"])


def test_build_path_creates_reviewable_draft_for_new_skill(tmp_path: Path) -> None:
    path = tmp_path / "jobs.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "SkillJobMap.v1",
                "review_status": "draft_for_human_review",
                "skills": {},
            }
        ),
        encoding="utf-8",
    )

    payload = load_skill_job_map_for_build(
        path,
        {"new-skill": {"display_name": "New Skill", "description": "Does one useful thing"}},
    )

    job = payload["skills"]["new-skill"]
    assert job["portfolio_action"] == "draft_new_skill_pending_review"
    assert job["nearest_neighbors"] == []
    assert payload["review_status"] == "draft_for_human_review"


def test_rendered_job_map_is_plain_english_and_routes_all_skills() -> None:
    slugs = sorted(path.stem for path in (ROOT / "ssot").glob("*.md"))
    payload = load_skill_job_map(JOB_MAP, slugs)
    rendered = render_skill_job_map(payload, {slug: slug for slug in slugs})

    assert "not behavioral proof and not a merger plan" in rendered
    assert "No skill is marked for merger or deletion" in rendered
    assert rendered.count("\n| `") == len(slugs)
