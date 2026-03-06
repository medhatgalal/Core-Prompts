"""Pass 1 sanitization: deterministic structural cleanup."""

from __future__ import annotations

import re
import unicodedata

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_INLINE_WHITESPACE = re.compile(r"[ \t\f\v]+")
_EXCESS_NEWLINES = re.compile(r"\n{3,}")


def sanitize_pass1(raw_text: str) -> str:
    """Normalize encoding, newlines, control chars, and whitespace."""
    if not isinstance(raw_text, str):
        raise TypeError("sanitize_pass1 expects str input")

    normalized = unicodedata.normalize("NFKC", raw_text)
    normalized = normalized.replace("\ufeff", "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _CONTROL_CHARS.sub("", normalized)

    cleaned_lines = []
    for line in normalized.split("\n"):
        cleaned_lines.append(_INLINE_WHITESPACE.sub(" ", line).strip())

    cleaned = "\n".join(cleaned_lines)
    cleaned = _EXCESS_NEWLINES.sub("\n\n", cleaned)
    return cleaned.strip()
