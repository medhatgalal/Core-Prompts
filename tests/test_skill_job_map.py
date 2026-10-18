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

    assert "product feature" in skills["engos-audit-feature-status"]["primary_job"].lower()
    assert "repository activity" in skills["engos-audit-engineering-progress"]["primary_job"].lower()
    assert "structural risks" in skills["engos-audit-code-health"]["primary_job"].lower()
    assert len({skills[slug]["primary_job"] for slug in ("engos-design-architecture", "engos-reconciliation-converge", "engos-meta-supercharge")}) == 3
    assert "mentor" not in skills
    assert all("mentor" not in job["nearest_neighbors"] for job in skills.values())


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
    assert all(rendered.count(f"\n| `{slug}`<br>") == 1 for slug in slugs)


def test_availability_never_infers_live_state_from_source(tmp_path: Path) -> None:
    from intent_pipeline.skill_jobs import build_advisory_job_map, compile_skill_job
    slug = "sample-skill"
    source = "# Sample\n\n## Purpose\nInspect a supplied example.\n"
    (tmp_path / "ssot").mkdir()
    (tmp_path / "ssot" / f"{slug}.md").write_text(source)
    job = compile_skill_job(tmp_path, slug, source, display_name="Sample", description="Inspect")
    payload = build_advisory_job_map({slug: job})
    state = payload["availability"][slug]
    assert state["source_at_revision"]["status"] == "present"
    assert state["generated_package_at_revision"]["status"] == "not_inspected"
    assert len(state["generated_package_at_revision"]["distribution_paths"]) == 5
    assert state["installed_bytes_observation"]["status"] == "not_inspected"
    assert state["native_discovery_observation"]["status"] == "not_established"
    assert state["scoped_runtime_evidence"]["status"] == "no_applicable_case_evidence"
    # A copied live observation cannot be laundered through otherwise valid source metadata.
    state["native_discovery_observation"]["status"] = "discovery_observed"
    path = tmp_path / "map.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="per-run evidence gaps"):
        load_skill_job_map(path, [slug])


def test_source_availability_changes_with_source_not_worktree_identity(tmp_path: Path) -> None:
    from intent_pipeline.skill_jobs import build_advisory_job_map, compile_skill_job
    slug = "sample-skill"
    (tmp_path / "ssot").mkdir()
    path = tmp_path / "ssot" / f"{slug}.md"
    def compile_text(text: str) -> dict:
        path.write_text(text)
        job = compile_skill_job(tmp_path, slug, text, display_name="Sample", description="Inspect")
        return build_advisory_job_map({slug: job})["availability"]
    before = compile_text("# Sample\n\n## Purpose\nInspect one example.\n")
    assert before == compile_text(path.read_text())
    after = compile_text("# Sample\n\n## Purpose\nInspect a changed example.\n")
    assert before[slug]["source_at_revision"]["sha256"] != after[slug]["source_at_revision"]["sha256"]
    assert before[slug]["native_discovery_observation"] == after[slug]["native_discovery_observation"]
    assert str(tmp_path) not in json.dumps(after)


def test_legacy_v2_map_without_availability_stays_readable() -> None:
    payload = json.loads(JOB_MAP.read_text())
    payload.pop("availability", None)
    from intent_pipeline.skill_jobs import _validate_skill_job_map
    assert _validate_skill_job_map(payload, payload["skills"]) == payload


def test_neighbor_handoff_rejects_stale_or_nonportable_source(tmp_path: Path) -> None:
    import hashlib
    from intent_pipeline.skill_jobs import validate_neighbor_handoff
    target = tmp_path / "source.md"
    target.write_text("One retained handoff.\n")
    ref = {"path": "source.md", "start_line": 1, "end_line": 1,
           "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
    job = {"neighbor_handoff": {"condition_and_handoff": "A conditional handoff.", "source_refs": [ref]}}
    validate_neighbor_handoff(job, tmp_path)
    target.write_text("Changed source requires renewed review.\n")
    with pytest.raises(ValueError, match="stale"):
        validate_neighbor_handoff(job, tmp_path)
    ref["path"] = "../outside.md"
    with pytest.raises(ValueError, match="invalid neighbor source"):
        validate_neighbor_handoff(job)


def test_rendered_source_links_remain_usable_without_bundled_ssot() -> None:
    slugs = sorted(path.stem for path in (ROOT / "ssot").glob("*.md"))
    payload = load_skill_job_map(JOB_MAP, slugs)
    rendered = render_skill_job_map(payload, {slug: slug for slug in slugs})
    assert "(../ssot/" not in rendered
    assert "https://github.com/medhatgalal/Core-Prompts/blob/main/ssot/" in rendered
    assert "selected bundled `SKILL.md`" in rendered
    assert "verify the recorded content hashes" in rendered
