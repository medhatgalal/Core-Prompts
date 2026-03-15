from __future__ import annotations

from pathlib import Path

from intent_pipeline.uac_sources import (
    aggregate_collection_recommendation,
    enumerate_local_directory,
    parse_github_tree_url,
)


def test_parse_github_tree_url_for_folder() -> None:
    ref = parse_github_tree_url(
        "https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/architecture"
    )

    assert ref is not None
    assert ref.owner == "harish-garg"
    assert ref.repo == "gemini-cli-prompt-library"
    assert ref.ref == "main"
    assert ref.path == "commands/architecture"


def test_enumerate_local_directory_filters_prompt_like_files(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("Primary Objective: Test", encoding="utf-8")
    (tmp_path / "b.txt").write_text("Primary Objective: Test", encoding="utf-8")
    (tmp_path / "ignore.py").write_text("print('x')", encoding="utf-8")

    candidates = enumerate_local_directory(tmp_path, recurse=False)

    assert [candidate.display_name for candidate in candidates] == ["a.md", "b.txt"]


def test_aggregate_collection_recommendation_prefers_skill_family() -> None:
    recommendation = aggregate_collection_recommendation(
        "architecture",
        [
            {"status": "accepted", "uac": {"capability_type": "skill"}},
            {"status": "accepted", "uac": {"capability_type": "skill"}},
        ],
    )

    assert recommendation.collection_type == "skill_family"
    assert recommendation.capability_type == "skill"
    assert recommendation.recommended_surface == "skill"
    assert recommendation.shared_roof is True
