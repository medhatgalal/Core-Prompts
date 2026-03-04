"""Terminal phase-1 pipeline: local ingestion -> two-pass sanitization -> summary."""

from __future__ import annotations

from pathlib import Path

from intent_pipeline.ingestion.reader import read_local_file_text
from intent_pipeline.sanitization.pipeline import sanitize_two_pass
from intent_pipeline.summary.renderer import render_intent_summary


def run_phase1_pipeline(source: str | Path) -> str:
    """Return deterministic intent summary and terminate the phase-1 pipeline."""
    raw_text = read_local_file_text(source)
    sanitized_text = sanitize_two_pass(raw_text)
    return render_intent_summary(sanitized_text)


__all__ = ["run_phase1_pipeline"]
