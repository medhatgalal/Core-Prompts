from __future__ import annotations

from typing import Any

import pytest

from intent_pipeline.pipeline import run_phase1_pipeline


def test_bound_01_pipeline_executes_only_ingest_sanitize_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_read_local_file_text(source: str) -> str:
        calls.append("ingest")
        assert source == "local.txt"
        return "raw-intent"

    def fake_sanitize_two_pass(raw_text: str) -> str:
        calls.append("sanitize")
        assert raw_text == "raw-intent"
        return "sanitized-intent"

    def fake_render_intent_summary(sanitized_text: str) -> str:
        calls.append("summary")
        assert sanitized_text == "sanitized-intent"
        return "terminal-summary-output"

    monkeypatch.setattr(
        "intent_pipeline.pipeline.read_local_file_text",
        fake_read_local_file_text,
    )
    monkeypatch.setattr("intent_pipeline.pipeline.sanitize_two_pass", fake_sanitize_two_pass)
    monkeypatch.setattr(
        "intent_pipeline.pipeline.render_intent_summary",
        fake_render_intent_summary,
    )

    result = run_phase1_pipeline("local.txt")

    assert result == "terminal-summary-output"
    assert calls == ["ingest", "sanitize", "summary"]


def test_bound_02_pipeline_returns_summary_directly_without_post_hooks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel: Any = object()

    monkeypatch.setattr(
        "intent_pipeline.pipeline.read_local_file_text",
        lambda _source: "raw",
    )
    monkeypatch.setattr(
        "intent_pipeline.pipeline.sanitize_two_pass",
        lambda raw_text: f"sanitized::{raw_text}",
    )
    monkeypatch.setattr(
        "intent_pipeline.pipeline.render_intent_summary",
        lambda _sanitized: sentinel,
    )

    result = run_phase1_pipeline("local.txt")

    assert result is sentinel


def test_bound_01_pipeline_exposes_no_downstream_hook_argument() -> None:
    with pytest.raises(TypeError):
        run_phase1_pipeline(  # type: ignore[call-arg]
            source="local.txt",
            downstream_hook=lambda _summary: None,
        )
