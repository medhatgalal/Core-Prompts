"""Deterministic context layer builder for uplift phase."""

from __future__ import annotations

from hashlib import sha256
import re
from typing import Any

_INLINE_WHITESPACE = re.compile(r"\s+")
_FACT_LINE = re.compile(r"^\s*(?P<key>[A-Za-z][A-Za-z0-9 _-]{1,64})\s*:\s*(?P<value>.+?)\s*$")
_CONSTRAINT_PATTERN = re.compile(r"\b(must|should|only|require(?:d|s)?|do not|no)\b", re.IGNORECASE)
_ACCEPTANCE_PATTERN = re.compile(
    r"\b(acceptance|criteria|criterion|verify|verification|assert|test)\b",
    re.IGNORECASE,
)

DEFAULT_SCHEMA_VERSION = "2.0.0"
SUPPORTED_SCHEMA_MAJOR = "2"


def _normalize_text(raw_value: str) -> str:
    return _INLINE_WHITESPACE.sub(" ", raw_value.strip())


def _canonical_key(raw_key: str) -> str:
    normalized = _normalize_text(raw_key).lower().replace("-", " ")
    return "_".join(part for part in normalized.split(" ") if part)


def _append_unique_ordered(bucket: list[dict[str, Any]], item: dict[str, Any], dedupe_key: str) -> None:
    marker = item.get(dedupe_key)
    if marker is None:
        bucket.append(item)
        return
    if any(existing.get(dedupe_key) == marker for existing in bucket):
        return
    bucket.append(item)


def _validate_schema_version(schema_version: str) -> str:
    if not isinstance(schema_version, str):
        raise TypeError("schema_version must be str")
    normalized = _normalize_text(schema_version)
    if not normalized:
        raise ValueError("schema_version is required")
    major = normalized.split(".", 1)[0]
    if major != SUPPORTED_SCHEMA_MAJOR:
        raise ValueError(
            f"Unsupported schema major version '{major}'. Expected {SUPPORTED_SCHEMA_MAJOR}.x"
        )
    return normalized


def build_context_layer(sanitized_text: str, schema_version: str = DEFAULT_SCHEMA_VERSION) -> dict[str, Any]:
    """Build a deterministic layered context object from sanitized text."""
    if not isinstance(sanitized_text, str):
        raise TypeError("build_context_layer expects str input")
    normalized_schema = _validate_schema_version(schema_version)

    normalized_facts: list[dict[str, Any]] = []
    inferred_facts: list[dict[str, Any]] = []
    candidate_constraints: list[dict[str, Any]] = []
    acceptance_inputs: list[dict[str, Any]] = []

    explicit_keys: set[str] = set()
    ordered_lines: list[str] = []

    for line_index, raw_line in enumerate(sanitized_text.splitlines()):
        normalized_line = _normalize_text(raw_line)
        if not normalized_line:
            continue
        ordered_lines.append(normalized_line)

        fact_match = _FACT_LINE.match(normalized_line)
        if fact_match:
            key = _canonical_key(fact_match.group("key"))
            value = _normalize_text(fact_match.group("value"))
            explicit_keys.add(key)
            _append_unique_ordered(
                normalized_facts,
                {
                    "key": key,
                    "value": value,
                    "source": "explicit",
                    "line_index": line_index,
                },
                "key",
            )

        if _CONSTRAINT_PATTERN.search(normalized_line):
            _append_unique_ordered(
                candidate_constraints,
                {
                    "text": normalized_line,
                    "line_index": line_index,
                    "source": "explicit",
                },
                "text",
            )

        if _ACCEPTANCE_PATTERN.search(normalized_line):
            _append_unique_ordered(
                acceptance_inputs,
                {
                    "text": normalized_line,
                    "line_index": line_index,
                    "source": "explicit",
                },
                "text",
            )

    inferred_candidates: list[tuple[str, str, int]] = []
    for line_index, line in enumerate(ordered_lines):
        lower_line = line.lower()
        if "goal" in lower_line or "objective" in lower_line:
            inferred_candidates.append(("primary_objective", line, line_index))
        if "in scope" in lower_line:
            inferred_candidates.append(("in_scope", line, line_index))
        if "out of scope" in lower_line or "excluded" in lower_line:
            inferred_candidates.append(("out_of_scope", line, line_index))

    for key, value, line_index in inferred_candidates:
        if key in explicit_keys:
            continue
        _append_unique_ordered(
            inferred_facts,
            {
                "key": key,
                "value": value,
                "source": "inferred",
                "inferred": True,
                "confidence": "low",
                "line_index": line_index,
            },
            "key",
        )

    content_hash = sha256(sanitized_text.encode("utf-8")).hexdigest()

    return {
        "schema_version": normalized_schema,
        "source": {
            "content_sha256": content_hash,
            "line_count": len(ordered_lines),
            "content_type": "sanitized_text",
        },
        "normalized_facts": normalized_facts,
        "inferred_facts": inferred_facts,
        "candidate_constraints": candidate_constraints,
        "acceptance_inputs": acceptance_inputs,
    }


__all__ = ["build_context_layer", "DEFAULT_SCHEMA_VERSION", "SUPPORTED_SCHEMA_MAJOR"]
