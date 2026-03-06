"""Two-pass sanitization pipeline enforcing pass sequencing."""

from __future__ import annotations

from intent_pipeline.sanitization.pass1 import sanitize_pass1
from intent_pipeline.sanitization.pass2 import sanitize_pass2


def sanitize_two_pass(raw_text: str) -> str:
    """Run pass2 strictly over pass1 output."""
    if not isinstance(raw_text, str):
        raise TypeError("sanitize_two_pass expects str input")
    return sanitize_pass2(sanitize_pass1(raw_text))
