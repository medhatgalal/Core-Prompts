"""Deterministic extraction of intent-bearing structural signals from text."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

_INLINE_WHITESPACE = re.compile(r"\s+")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*(.+?)\s*$")
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*(.+?)\s*$")
_KEY_VALUE = re.compile(r"^\s*(?P<key>[A-Za-z][A-Za-z0-9 _/-]{1,80})\s*:\s*(?P<value>.+?)\s*$")

_REJECTED_PATTERNS = (
    re.compile(r"\bout[- ]of[- ]scope\b", re.IGNORECASE),
    re.compile(r"\bexcluded?\b", re.IGNORECASE),
    re.compile(r"\bnon[- ]goals?\b", re.IGNORECASE),
    re.compile(r"\bnot in scope\b", re.IGNORECASE),
    re.compile(r"\bno downstream\b", re.IGNORECASE),
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
    re.compile(r"\bstrict\b", re.IGNORECASE),
    re.compile(r"\bdo not\b", re.IGNORECASE),
    re.compile(r"\bno\b", re.IGNORECASE),
)
_REQUESTED_PATTERNS = (
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
_OBJECTIVE_PATTERNS = (
    re.compile(r"^\s*(intent|primary goal|goal|objective|summary)\b", re.IGNORECASE),
)
_ACCEPTANCE_PATTERNS = (
    re.compile(r"\b(acceptance|criteria|criterion|verify|verification|assert|test plan|success criteria)\b", re.IGNORECASE),
)
_TEMPLATE_PATTERNS = (
    re.compile(r"\bthis section is\b", re.IGNORECASE),
    re.compile(r"\blist the specific goals\b", re.IGNORECASE),
    re.compile(r"\bwhat is out of scope\b", re.IGNORECASE),
    re.compile(r"\ba good summary\b", re.IGNORECASE),
    re.compile(r"\baction required\b", re.IGNORECASE),
    re.compile(r"\bwhen your kep is complete\b", re.IGNORECASE),
    re.compile(r"\bto get started with this template\b", re.IGNORECASE),
    re.compile(r"\bdocumentation such as release notes\b", re.IGNORECASE),
    re.compile(r"\bpossible to collect this information before implementation begins\b", re.IGNORECASE),
    re.compile(r"\bavoid requiring implementors to split their attention\b", re.IGNORECASE),
    re.compile(r"\btone and content of the `summary` section\b", re.IGNORECASE),
    re.compile(r"\bwide audience\b", re.IGNORECASE),
    re.compile(r"\bhow will we know that this has succeeded\b", re.IGNORECASE),
    re.compile(r"\blisting non-goals helps\b", re.IGNORECASE),
    re.compile(r"\bmake progress\b", re.IGNORECASE),
)

_SECTION_ALIASES = {
    "summary": "objective",
    "objective": "objective",
    "objectives": "objective",
    "purpose": "objective",
    "goals": "in_scope",
    "goal": "in_scope",
    "in scope": "in_scope",
    "scope": "in_scope",
    "non-goals": "out_of_scope",
    "non goals": "out_of_scope",
    "out of scope": "out_of_scope",
    "excluded": "out_of_scope",
    "notes/constraints/caveats": "constraints",
    "notes constraints caveats": "constraints",
    "constraints": "constraints",
    "requirements": "constraints",
    "guardrails": "constraints",
    "acceptance criteria": "acceptance",
    "test plan": "acceptance",
    "success criteria": "acceptance",
    "verification": "acceptance",
}
_KEY_ALIASES = {
    "primary objective": "objective",
    "objective": "objective",
    "objectives": "objective",
    "goal": "objective",
    "summary": "objective",
    "in scope": "in_scope",
    "scope": "in_scope",
    "goals": "in_scope",
    "out of scope": "out_of_scope",
    "non-goals": "out_of_scope",
    "non goals": "out_of_scope",
    "excluded": "out_of_scope",
    "constraints": "constraints",
    "constraint": "constraints",
    "requirements": "constraints",
    "requirement": "constraints",
    "acceptance criteria": "acceptance",
    "test plan": "acceptance",
    "verification": "acceptance",
}


@dataclass(frozen=True, slots=True)
class IntentSignal:
    text: str
    line_index: int
    evidence_path: str


@dataclass(frozen=True, slots=True)
class IntentStructure:
    objective: tuple[IntentSignal, ...]
    in_scope: tuple[IntentSignal, ...]
    out_of_scope: tuple[IntentSignal, ...]
    constraints: tuple[IntentSignal, ...]
    acceptance: tuple[IntentSignal, ...]
    requested: tuple[IntentSignal, ...]

    @property
    def semantic_category_count(self) -> int:
        return sum(
            1
            for bucket in (
                self.objective,
                self.in_scope,
                self.out_of_scope,
                self.constraints,
                self.acceptance,
            )
            if bucket
        )


def _normalize_text(raw_value: str) -> str:
    return _INLINE_WHITESPACE.sub(" ", raw_value.strip())


def _normalize_heading(raw_heading: str) -> str:
    candidate = _normalize_text(raw_heading).strip("# ").casefold()
    candidate = re.sub(r"\s*\([^)]*\)\s*", " ", candidate)
    candidate = candidate.replace("_", " ").replace("/", " ")
    candidate = re.sub(r"[^a-z0-9 -]+", " ", candidate)
    return _normalize_text(candidate)


def _normalize_key(raw_key: str) -> str:
    candidate = _normalize_text(raw_key).casefold().replace("_", " ")
    return _normalize_text(candidate)


def _normalize_signal_text(raw_text: str) -> str:
    text = _normalize_text(raw_text)
    text = text.strip("-: ")
    return text


def _is_noise_line(line: str) -> bool:
    if not re.search(r"[A-Za-z0-9]", line):
        return True
    if line.startswith("[") and "]:" in line:
        return True
    if line.startswith("|"):
        return True
    if all(character in "-=_*`" for character in line):
        return True
    return False


def _is_template_line(line: str) -> bool:
    return any(pattern.search(line) for pattern in _TEMPLATE_PATTERNS)


def _dedupe_signals(items: Iterable[IntentSignal]) -> tuple[IntentSignal, ...]:
    seen: set[str] = set()
    ordered: list[IntentSignal] = []
    for item in items:
        marker = item.text
        if marker in seen:
            continue
        seen.add(marker)
        ordered.append(item)
    return tuple(ordered)


class _SignalBuilder:
    def __init__(self) -> None:
        self._signals: dict[str, list[IntentSignal]] = {
            "objective": [],
            "in_scope": [],
            "out_of_scope": [],
            "constraints": [],
            "acceptance": [],
            "requested": [],
        }
        self._current_section: str | None = None
        self._buffer_kind: str | None = None
        self._buffer_lines: list[str] = []
        self._buffer_line_index: int | None = None
        self._buffer_path: str | None = None
        self._in_comment = False
        self._in_code_fence = False
        self._structured_mode = False

    def add_text(self, text: str) -> IntentStructure:
        for line_index, raw_line in enumerate(text.splitlines()):
            if self._should_skip_line(raw_line):
                continue
            self._consume_line(raw_line, line_index)
        self._flush_buffer()
        return IntentStructure(
            objective=_dedupe_signals(self._signals["objective"]),
            in_scope=_dedupe_signals(self._signals["in_scope"]),
            out_of_scope=_dedupe_signals(self._signals["out_of_scope"]),
            constraints=_dedupe_signals(self._signals["constraints"]),
            acceptance=_dedupe_signals(self._signals["acceptance"]),
            requested=_dedupe_signals(self._signals["requested"]),
        )

    def _should_skip_line(self, raw_line: str) -> bool:
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            self._in_code_fence = not self._in_code_fence
            return True
        if self._in_code_fence:
            return True
        if self._in_comment:
            if "-->" in stripped:
                self._in_comment = False
            return True
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                self._in_comment = True
            return True
        return False

    def _consume_line(self, raw_line: str, line_index: int) -> None:
        line = _normalize_text(raw_line)
        if not line or _is_noise_line(line) or _is_template_line(line):
            return

        heading_match = _HEADING.match(line)
        if heading_match:
            self._flush_buffer()
            self._current_section = _SECTION_ALIASES.get(_normalize_heading(heading_match.group(1)))
            if self._current_section is not None:
                if not self._structured_mode:
                    self._signals = {key: [] for key in self._signals}
                self._structured_mode = True
            return

        key_match = _KEY_VALUE.match(line)
        if key_match:
            self._flush_buffer()
            mapped = _KEY_ALIASES.get(_normalize_key(key_match.group("key")))
            if mapped is None:
                self._classify_generic(line, line_index)
                return
            self._append_signal(mapped, line, line_index, f"structured.key_value[{mapped}]")
            return

        bullet_match = _BULLET.match(line)
        if bullet_match:
            self._flush_buffer()
            bucket = self._current_section or _generic_bucket_for_line(bullet_match.group(1))
            if bucket in {"objective", "constraints", "acceptance", "in_scope", "out_of_scope"}:
                self._start_buffer(
                    kind=bucket,
                    initial_text=bullet_match.group(1),
                    line_index=line_index,
                    evidence_path=f"structured.section[{bucket}]",
                )
                return
            self._classify_generic(bullet_match.group(1), line_index)
            return

        if self._current_section in {"objective", "constraints", "acceptance", "in_scope", "out_of_scope"}:
            if self._buffer_kind == self._current_section:
                self._buffer_lines.append(line)
                return
            self._start_buffer(
                kind=self._current_section,
                initial_text=line,
                line_index=line_index,
                evidence_path=f"structured.section[{self._current_section}]",
            )
            return

        if not self._structured_mode:
            self._classify_generic(line, line_index)

    def _classify_generic(self, line: str, line_index: int) -> None:
        bucket = _generic_bucket_for_line(line)
        if bucket is None:
            return
        self._append_signal(bucket, line, line_index, f"structured.line[{bucket}]")

    def _start_buffer(self, *, kind: str, initial_text: str, line_index: int, evidence_path: str) -> None:
        self._buffer_kind = kind
        self._buffer_lines = [_normalize_signal_text(initial_text)]
        self._buffer_line_index = line_index
        self._buffer_path = evidence_path

    def _flush_buffer(self) -> None:
        if self._buffer_kind is None or self._buffer_line_index is None or self._buffer_path is None:
            self._buffer_kind = None
            self._buffer_lines = []
            self._buffer_line_index = None
            self._buffer_path = None
            return
        text = _normalize_signal_text(" ".join(part for part in self._buffer_lines if part))
        if text:
            values = _split_list_values(text, allow_commas=False)
            if self._buffer_kind in {"in_scope", "out_of_scope"} and values:
                for value in values:
                    self._append_signal(self._buffer_kind, value, self._buffer_line_index, self._buffer_path)
            else:
                self._append_signal(self._buffer_kind, text, self._buffer_line_index, self._buffer_path)
        self._buffer_kind = None
        self._buffer_lines = []
        self._buffer_line_index = None
        self._buffer_path = None

    def _append_signal(self, bucket: str, text: str, line_index: int, evidence_path: str) -> None:
        normalized = _normalize_signal_text(text)
        if not normalized or _is_template_line(normalized):
            return
        self._signals[bucket].append(
            IntentSignal(
                text=normalized,
                line_index=line_index,
                evidence_path=evidence_path,
            )
        )


def _split_list_values(text: str, *, allow_commas: bool = True) -> list[str]:
    if not isinstance(text, str):
        return []
    if ";" in text:
        parts = text.split(";")
    elif allow_commas and "," in text and len(text) < 240:
        parts = text.split(",")
    else:
        return []
    values = [_normalize_signal_text(part) for part in parts]
    return [value for value in values if value]


def _generic_bucket_for_line(line: str) -> str | None:
    if any(pattern.search(line) for pattern in _OBJECTIVE_PATTERNS):
        return "objective"
    if any(pattern.search(line) for pattern in _REJECTED_PATTERNS):
        return "out_of_scope"
    if any(pattern.search(line) for pattern in _CONSTRAINT_PATTERNS):
        return "constraints"
    if any(pattern.search(line) for pattern in _ACCEPTANCE_PATTERNS):
        return "acceptance"
    if any(pattern.search(line) for pattern in _REQUESTED_PATTERNS):
        return "requested"
    return None


def extract_intent_structure(text: str) -> IntentStructure:
    if not isinstance(text, str):
        raise TypeError("extract_intent_structure expects str input")
    return _SignalBuilder().add_text(text)


__all__ = ["IntentSignal", "IntentStructure", "extract_intent_structure"]
