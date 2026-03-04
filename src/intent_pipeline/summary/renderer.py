"""Deterministic fixed-template intent summary renderer."""

from __future__ import annotations

import re

_BULLET_PREFIX = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")
_INLINE_WHITESPACE = re.compile(r"\s+")

_ROLEPLAY_FRAGMENTS = (
    re.compile(r"\bas an ai language model\b", re.IGNORECASE),
    re.compile(r"\bpretend to be\b", re.IGNORECASE),
    re.compile(r"\broleplay\b", re.IGNORECASE),
    re.compile(r"\bstay in character\b", re.IGNORECASE),
    re.compile(r"\bassistant persona\b", re.IGNORECASE),
)

_REJECTED_PATTERNS = (
    re.compile(r"\bout[- ]of[- ]scope\b", re.IGNORECASE),
    re.compile(r"\bexcluded?\b", re.IGNORECASE),
    re.compile(r"\bnot in scope\b", re.IGNORECASE),
    re.compile(r"\bno downstream\b", re.IGNORECASE),
    re.compile(r"\bno url\b", re.IGNORECASE),
    re.compile(r"\bno uri\b", re.IGNORECASE),
    re.compile(r"\bdo not route\b", re.IGNORECASE),
    re.compile(r"\bdo not execute\b", re.IGNORECASE),
    re.compile(r"\bwithout (?:routing|execution)\b", re.IGNORECASE),
)

_CONSTRAINT_PATTERNS = (
    re.compile(r"\bmust\b", re.IGNORECASE),
    re.compile(r"\bshould\b", re.IGNORECASE),
    re.compile(r"\bonly\b", re.IGNORECASE),
    re.compile(r"\brequire(?:d|s)?\b", re.IGNORECASE),
    re.compile(r"\bdeterministic\b", re.IGNORECASE),
    re.compile(r"\broleplay[- ]free\b", re.IGNORECASE),
    re.compile(r"\bstrict\b", re.IGNORECASE),
    re.compile(r"\bdo not\b", re.IGNORECASE),
    re.compile(r"\bno\b", re.IGNORECASE),
)

_REQUESTED_OUTCOME_PATTERNS = (
    re.compile(r"\bimplement\b", re.IGNORECASE),
    re.compile(r"\bbuild\b", re.IGNORECASE),
    re.compile(r"\bcreate\b", re.IGNORECASE),
    re.compile(r"\bdeliver\b", re.IGNORECASE),
    re.compile(r"\bproduce\b", re.IGNORECASE),
    re.compile(r"\bgenerate\b", re.IGNORECASE),
    re.compile(r"\boutput\b", re.IGNORECASE),
    re.compile(r"\breturn\b", re.IGNORECASE),
    re.compile(r"\bwire\b", re.IGNORECASE),
    re.compile(r"\bcompose\b", re.IGNORECASE),
    re.compile(r"\bsummar(?:y|ize)\b", re.IGNORECASE),
)

_INTENT_PATTERNS = (
    re.compile(r"^\s*(intent|primary goal|goal|objective)\b", re.IGNORECASE),
)

_SECTION_ORDER = (
    "Intent",
    "Constraints",
    "Requested Outcome",
    "Rejected/Out-of-Scope Signals",
)


def _normalize_line(raw_line: str) -> str:
    line = _BULLET_PREFIX.sub("", raw_line.strip())
    for pattern in _ROLEPLAY_FRAGMENTS:
        line = pattern.sub("", line)
    line = _INLINE_WHITESPACE.sub(" ", line).strip(" -:\t")
    return line


def _unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _classify_line(line: str) -> str:
    if any(pattern.search(line) for pattern in _INTENT_PATTERNS):
        return "intent"
    if any(pattern.search(line) for pattern in _REJECTED_PATTERNS):
        return "rejected"
    if any(pattern.search(line) for pattern in _CONSTRAINT_PATTERNS):
        return "constraints"
    if any(pattern.search(line) for pattern in _REQUESTED_OUTCOME_PATTERNS):
        return "requested"
    return "intent"


def _render_section(title: str, items: list[str]) -> str:
    if not items:
        body = "- None"
    else:
        body = "\n".join(f"- {item}" for item in items)
    return f"{title}\n{body}"


def render_intent_summary(sanitized_text: str) -> str:
    """Render deterministic phase-1 summary from sanitized text only."""
    if not isinstance(sanitized_text, str):
        raise TypeError("render_intent_summary expects str input")

    buckets: dict[str, list[str]] = {
        "intent": [],
        "constraints": [],
        "requested": [],
        "rejected": [],
    }

    for raw_line in sanitized_text.splitlines():
        normalized = _normalize_line(raw_line)
        if not normalized:
            continue
        if not re.search(r"[A-Za-z0-9]", normalized):
            continue
        buckets[_classify_line(normalized)].append(normalized)

    intent_items = _unique_ordered(buckets["intent"])
    if not intent_items:
        for fallback_key in ("requested", "constraints", "rejected"):
            fallback_items = _unique_ordered(buckets[fallback_key])
            if fallback_items:
                intent_items = [fallback_items[0]]
                break

    sections = {
        "Intent": intent_items,
        "Constraints": _unique_ordered(buckets["constraints"]),
        "Requested Outcome": _unique_ordered(buckets["requested"]),
        "Rejected/Out-of-Scope Signals": _unique_ordered(buckets["rejected"]),
    }

    rendered = [_render_section(title, sections[title]) for title in _SECTION_ORDER]
    return "\n\n".join(rendered).rstrip() + "\n"


__all__ = ["render_intent_summary"]
