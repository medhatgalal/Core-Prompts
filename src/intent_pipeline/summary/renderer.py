"""Deterministic fixed-template intent summary renderer."""

from __future__ import annotations

from intent_pipeline.intent_structure import extract_intent_structure

_SECTION_ORDER = (
    "Intent",
    "Constraints",
    "Requested Outcome",
    "Rejected/Out-of-Scope Signals",
)


def _unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _preferred_signal_texts(
    signals,
    *,
    limit: int,
    allow_generic_fallback: bool = True,
) -> list[str]:
    preferred = [
        signal.text
        for signal in signals
        if not signal.evidence_path.startswith("structured.line[")
    ]
    if preferred:
        return _unique_ordered(preferred[:limit])
    if allow_generic_fallback:
        return _unique_ordered([signal.text for signal in signals[:limit]])
    return []


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
    structure = extract_intent_structure(sanitized_text)

    intent_items = _preferred_signal_texts(structure.objective, limit=2)
    if not intent_items:
        for fallback_items in (
            _unique_ordered([signal.text for signal in structure.in_scope[:3]]),
            _unique_ordered([signal.text for signal in structure.constraints[:3]]),
            _unique_ordered([signal.text for signal in structure.out_of_scope[:3]]),
            _unique_ordered([signal.text for signal in structure.requested[:3]]),
        ):
            if fallback_items:
                intent_items = [fallback_items[0]]
                break

    requested_items = _unique_ordered([signal.text for signal in structure.in_scope[:4]])
    if not requested_items:
        requested_items = _preferred_signal_texts(structure.requested, limit=2)

    sections = {
        "Intent": intent_items,
        "Constraints": _preferred_signal_texts(structure.constraints, limit=1),
        "Requested Outcome": requested_items,
        "Rejected/Out-of-Scope Signals": _unique_ordered(
            [signal.text for signal in structure.out_of_scope[:2]]
        ),
    }

    rendered = [_render_section(title, sections[title]) for title in _SECTION_ORDER]
    return "\n\n".join(rendered).rstrip() + "\n"


__all__ = ["render_intent_summary"]
