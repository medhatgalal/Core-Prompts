"""Deterministic intent derivation from layered context."""

from __future__ import annotations

import re
from typing import Any

_INLINE_WHITESPACE = re.compile(r"\s+")
_LIST_SPLIT = re.compile(r"[;,]")


def _normalize_text(value: str) -> str:
    return _INLINE_WHITESPACE.sub(" ", value.strip())


def _unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _normalize_list_values(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        for part in _LIST_SPLIT.split(value):
            candidate = _normalize_text(part)
            if candidate:
                normalized.append(candidate)
    return _unique_ordered(normalized)


def _is_supported_schema(context: dict[str, Any]) -> bool:
    schema_version = context.get("schema_version")
    if not isinstance(schema_version, str):
        return False
    return schema_version.split(".", 1)[0] == "2"


def _extract_keyed_values(context: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    facts = context.get("normalized_facts", [])
    if not isinstance(facts, list):
        return []
    values: list[str] = []
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        key = fact.get("key")
        value = fact.get("value")
        if key in keys and isinstance(value, str):
            normalized = _normalize_text(value)
            if normalized:
                values.append(normalized)
    return _unique_ordered(values)


def _extract_constraints(context: dict[str, Any]) -> list[str]:
    constraints = context.get("candidate_constraints", [])
    if not isinstance(constraints, list):
        return []
    values: list[str] = []
    for entry in constraints:
        if not isinstance(entry, dict):
            continue
        text = entry.get("text")
        if isinstance(text, str):
            normalized = _normalize_text(text)
            if normalized:
                values.append(normalized)
    return _unique_ordered(values)


def derive_intent_layer(context: dict[str, Any]) -> dict[str, Any]:
    """Derive deterministic intent fields from context with explicit unknown capture."""
    if not isinstance(context, dict):
        raise TypeError("derive_intent_layer expects dict context input")
    if not _is_supported_schema(context):
        raise ValueError("derive_intent_layer requires context schema version 2.x")

    primary_candidates = _extract_keyed_values(
        context,
        ("primary_objective", "objective", "goal", "intent"),
    )
    secondary_candidates = _extract_keyed_values(
        context,
        ("secondary_objective", "secondary_objectives"),
    )
    in_scope_candidates = _extract_keyed_values(context, ("in_scope", "scope"))
    out_of_scope_candidates = _extract_keyed_values(context, ("out_of_scope", "excluded"))
    quality_candidates = _extract_keyed_values(
        context,
        ("quality_constraints", "quality_constraint", "constraint"),
    )
    quality_candidates.extend(_extract_constraints(context))
    quality_constraints = _unique_ordered(_normalize_list_values(quality_candidates))

    unknowns: list[str] = []
    primary_objective: str | None = None

    if primary_candidates:
        primary_objective = primary_candidates[0]
    else:
        unknowns.append("primary_objective: missing explicit evidence")

    secondary_objectives = _normalize_list_values(secondary_candidates)
    if not secondary_objectives:
        unknowns.append("secondary_objectives: no explicit secondary objectives found")

    in_scope = _normalize_list_values(in_scope_candidates)
    if not in_scope:
        unknowns.append("in_scope: missing explicit in-scope definition")

    out_of_scope = _normalize_list_values(out_of_scope_candidates)
    if not out_of_scope:
        unknowns.append("out_of_scope: missing explicit out-of-scope definition")

    if not quality_constraints:
        unknowns.append("quality_constraints: no explicit quality constraints found")

    return {
        "schema_version": context["schema_version"],
        "primary_objective": primary_objective,
        "secondary_objectives": secondary_objectives,
        "in_scope": in_scope,
        "out_of_scope": out_of_scope,
        "quality_constraints": quality_constraints,
        "unknowns": _unique_ordered(unknowns),
    }


__all__ = ["derive_intent_layer"]
