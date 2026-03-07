"""Pass 2 sanitization: deterministic roleplay/instruction residue cleanup."""

from __future__ import annotations

import re

_SPEAKER_PREFIX = re.compile(r"^\s*(system|assistant|developer|user)\s*:\s*", re.IGNORECASE)
_INLINE_WHITESPACE = re.compile(r"[ \t]+")

_DROP_LINE_PATTERNS = (
    re.compile(r"^\s*(you are|act as|pretend to be|roleplay as)\b", re.IGNORECASE),
    re.compile(r"^\s*(ignore|disregard)\b.*\binstruction", re.IGNORECASE),
    re.compile(r"^\s*(follow|obey)\b.*\b(instruction|command|policy)", re.IGNORECASE),
    re.compile(r"^\s*as an ai language model\b", re.IGNORECASE),
    re.compile(r"^\s*(do not|don't)\s+break\s+character\b", re.IGNORECASE),
)

_INLINE_RESIDUE_PATTERNS = (
    re.compile(r"\bas an ai language model\b", re.IGNORECASE),
    re.compile(r"\bstay in character\b", re.IGNORECASE),
    re.compile(r"\bout of character\b", re.IGNORECASE),
    re.compile(r"\bin this roleplay\b", re.IGNORECASE),
    re.compile(r"\bexecute this now\b", re.IGNORECASE),
    re.compile(r"\bimmediately execute\b", re.IGNORECASE),
)


def sanitize_pass2(pass1_output: str) -> str:
    """Strip roleplay and instruction residue from pass-1 output."""
    if not isinstance(pass1_output, str):
        raise TypeError("sanitize_pass2 expects str input")

    kept_lines: list[str] = []
    for raw_line in pass1_output.split("\n"):
        candidate = _SPEAKER_PREFIX.sub("", raw_line).strip()
        if not candidate:
            continue

        if candidate in {"<!--", "-->"}:
            kept_lines.append(candidate)
            continue

        if any(pattern.search(candidate) for pattern in _DROP_LINE_PATTERNS):
            continue

        for pattern in _INLINE_RESIDUE_PATTERNS:
            candidate = pattern.sub("", candidate)

        candidate = _INLINE_WHITESPACE.sub(" ", candidate).strip(" -:\t")
        if candidate and re.search(r"[A-Za-z0-9]", candidate):
            kept_lines.append(candidate)

    return "\n".join(kept_lines)
