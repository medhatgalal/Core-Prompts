"""Deterministic semantic router with fixed precedence and ambiguity handling."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable, Mapping, Sequence

from intent_pipeline.routing.contracts import RouteDecision, RouteProfile
from intent_pipeline.routing.signal_bundle import ConstraintSignal, SignalBundle


PRECEDENCE_ORDER: tuple[str, ...] = ("hard", "intent", "task_graph", "acceptance")
PROFILE_TIE_BREAK_ORDER: tuple[RouteProfile, ...] = (
    RouteProfile.IMPLEMENTATION,
    RouteProfile.RESEARCH,
    RouteProfile.VALIDATION,
)

_RULE_MISSING_EVIDENCE = "ROUTE-UNK-001"
_RULE_AMBIGUITY = "ROUTE-UNK-002"
_RULE_NO_DECISIVE_ROUTE = "ROUTE-UNK-003"
_RULE_HARD_EXPLICIT = "ROUTE-HARD-001"
_RULE_HARD_KEYWORD = "ROUTE-HARD-002"
_RULE_HARD_TIE_BREAK = "ROUTE-HARD-003"
_RULE_INTENT_KEYWORD = "ROUTE-INTENT-001"
_RULE_INTENT_TIE_BREAK = "ROUTE-INTENT-002"
_RULE_TASK_KEYWORD = "ROUTE-TASK-001"
_RULE_TASK_TIE_BREAK = "ROUTE-TASK-002"
_RULE_ACCEPTANCE_KEYWORD = "ROUTE-ACCEPT-001"
_RULE_ACCEPTANCE_TIE_BREAK = "ROUTE-ACCEPT-002"
_RULE_ACCEPTANCE_BLOCK = "ROUTE-ACCEPT-900"

_PROFILE_KEYWORDS: dict[RouteProfile, tuple[str, ...]] = {
    RouteProfile.IMPLEMENTATION: ("implement", "build", "code", "fix", "patch", "refactor"),
    RouteProfile.RESEARCH: ("research", "investigate", "explore", "analyze", "discovery"),
    RouteProfile.VALIDATION: ("validate", "validation", "verify", "test", "qa", "audit"),
}


@dataclass(frozen=True, slots=True)
class RouteSelection:
    """Canonical deterministic route result payload."""

    decision: RouteDecision
    route_profile: RouteProfile
    dominant_layer: str
    dominant_rule_id: str
    applied_rule_ids: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    ambiguity_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.decision, RouteDecision):
            object.__setattr__(self, "decision", RouteDecision(str(self.decision)))
        if not isinstance(self.route_profile, RouteProfile):
            object.__setattr__(self, "route_profile", RouteProfile(str(self.route_profile)))

        object.__setattr__(self, "dominant_layer", _normalize_text(self.dominant_layer))
        object.__setattr__(self, "dominant_rule_id", _normalize_text(self.dominant_rule_id))
        object.__setattr__(self, "applied_rule_ids", _unique_in_order(self.applied_rule_ids))
        object.__setattr__(self, "missing_evidence", _normalize_sorted_text(self.missing_evidence))
        object.__setattr__(self, "ambiguity_reasons", _normalize_sorted_text(self.ambiguity_reasons))

        if self.decision is RouteDecision.NEEDS_REVIEW:
            object.__setattr__(self, "route_profile", RouteProfile.NEEDS_REVIEW)
        elif self.route_profile is RouteProfile.NEEDS_REVIEW:
            raise ValueError("PASS_ROUTE decisions cannot use route_profile NEEDS_REVIEW")

    def as_payload(self) -> dict[str, object]:
        return {
            "decision": self.decision.value,
            "route_profile": self.route_profile.value,
            "dominant_layer": self.dominant_layer,
            "dominant_rule_id": self.dominant_rule_id,
            "applied_rule_ids": list(self.applied_rule_ids),
            "missing_evidence": list(self.missing_evidence),
            "ambiguity_reasons": list(self.ambiguity_reasons),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class _LayerDecision:
    profile: RouteProfile | None
    rule_id: str | None
    ambiguity_reason: str | None = None


def select_route(signals: SignalBundle) -> RouteSelection:
    """Select deterministic route profile with fixed precedence and explicit review states."""
    if not isinstance(signals, SignalBundle):
        raise TypeError("select_route expects SignalBundle input")

    applied_rule_ids: list[str] = []
    missing_evidence = _normalize_sorted_text(signals.missing_evidence)
    if missing_evidence:
        return _build_review_selection(
            dominant_rule_id=_RULE_MISSING_EVIDENCE,
            applied_rule_ids=(*_with_rule(applied_rule_ids, _RULE_MISSING_EVIDENCE),),
            missing_evidence=missing_evidence,
            ambiguity_reasons=(),
        )

    hard_decision = _evaluate_hard_layer(signals)
    if hard_decision.rule_id:
        applied_rule_ids.append(hard_decision.rule_id)
    if hard_decision.ambiguity_reason:
        return _build_review_selection(
            dominant_rule_id=_RULE_AMBIGUITY,
            applied_rule_ids=(*_with_rule(applied_rule_ids, _RULE_AMBIGUITY),),
            missing_evidence=(),
            ambiguity_reasons=(hard_decision.ambiguity_reason,),
        )

    intent_decision = _evaluate_intent_layer(signals)
    if intent_decision.rule_id:
        applied_rule_ids.append(intent_decision.rule_id)

    task_decision = _evaluate_task_layer(signals)
    if task_decision.rule_id:
        applied_rule_ids.append(task_decision.rule_id)

    dominant_profile, dominant_layer, dominant_rule_id = _resolve_precedence_winner(
        hard_decision=hard_decision,
        intent_decision=intent_decision,
        task_decision=task_decision,
    )

    acceptance_review_reason = _acceptance_block_reason(signals)
    if acceptance_review_reason is not None:
        return _build_review_selection(
            dominant_rule_id=_RULE_ACCEPTANCE_BLOCK,
            applied_rule_ids=(*_with_rule(applied_rule_ids, _RULE_ACCEPTANCE_BLOCK),),
            missing_evidence=(),
            ambiguity_reasons=(acceptance_review_reason,),
        )

    acceptance_decision = _evaluate_acceptance_layer(signals)
    if acceptance_decision.rule_id:
        applied_rule_ids.append(acceptance_decision.rule_id)

    if dominant_profile is None:
        dominant_profile = acceptance_decision.profile
        if dominant_profile is not None:
            dominant_layer = "acceptance"
            dominant_rule_id = acceptance_decision.rule_id

    if dominant_profile is None or dominant_rule_id is None or dominant_layer is None:
        return _build_review_selection(
            dominant_rule_id=_RULE_NO_DECISIVE_ROUTE,
            applied_rule_ids=(*_with_rule(applied_rule_ids, _RULE_NO_DECISIVE_ROUTE),),
            missing_evidence=(),
            ambiguity_reasons=("no_decisive_route_after_precedence",),
        )

    return RouteSelection(
        decision=RouteDecision.PASS_ROUTE,
        route_profile=dominant_profile,
        dominant_layer=dominant_layer,
        dominant_rule_id=dominant_rule_id,
        applied_rule_ids=tuple(applied_rule_ids),
        missing_evidence=(),
        ambiguity_reasons=(),
    )


def _resolve_precedence_winner(
    *,
    hard_decision: _LayerDecision,
    intent_decision: _LayerDecision,
    task_decision: _LayerDecision,
) -> tuple[RouteProfile | None, str | None, str | None]:
    if hard_decision.profile is not None:
        return hard_decision.profile, "hard", hard_decision.rule_id
    if intent_decision.profile is not None:
        return intent_decision.profile, "intent", intent_decision.rule_id
    if task_decision.profile is not None:
        return task_decision.profile, "task_graph", task_decision.rule_id
    return None, None, None


def _acceptance_block_reason(signals: SignalBundle) -> str | None:
    acceptance_gate = _normalize_text(signals.acceptance_decision).upper()
    if signals.acceptance_failed_hard_criteria:
        criteria = ",".join(sorted(signals.acceptance_failed_hard_criteria))
        return f"acceptance_failed_hard_criteria:{criteria}"
    if acceptance_gate in {"FAIL", "NEEDS_REVIEW"}:
        return f"acceptance_gate_blocked:{acceptance_gate}"
    return None


def _evaluate_hard_layer(signals: SignalBundle) -> _LayerDecision:
    hard_conflicts = sorted(
        code for code in signals.conflict_codes if _normalize_text(code).upper().startswith("HARD_CONFLICT")
    )
    explicit_profiles = _explicit_profiles_from_constraints(signals.hard_constraints)
    if hard_conflicts:
        reason = f"hard_constraint_conflict_code:{','.join(hard_conflicts)}"
        if len(explicit_profiles) > 1:
            profiles = ",".join(profile.value for profile in explicit_profiles)
            reason = f"{reason};hard_constraints_conflicting_profiles:{profiles}"
        return _LayerDecision(profile=None, rule_id=None, ambiguity_reason=reason)
    if len(explicit_profiles) > 1:
        profiles = ",".join(profile.value for profile in explicit_profiles)
        return _LayerDecision(
            profile=None,
            rule_id=None,
            ambiguity_reason=f"hard_constraints_conflicting_profiles:{profiles}",
        )
    if len(explicit_profiles) == 1:
        return _LayerDecision(profile=explicit_profiles[0], rule_id=_RULE_HARD_EXPLICIT)

    scores = _score_profiles(
        _iter_constraint_text(signals.hard_constraints),
    )
    profile, rule_id = _resolve_scored_profile(scores, default_rule_id=_RULE_HARD_KEYWORD, tie_break_rule_id=_RULE_HARD_TIE_BREAK)
    return _LayerDecision(profile=profile, rule_id=rule_id)


def _evaluate_intent_layer(signals: SignalBundle) -> _LayerDecision:
    scores = _score_profiles(
        (
            signals.primary_objective or "",
            *signals.in_scope,
            *signals.quality_constraints,
        )
    )
    profile, rule_id = _resolve_scored_profile(
        scores,
        default_rule_id=_RULE_INTENT_KEYWORD,
        tie_break_rule_id=_RULE_INTENT_TIE_BREAK,
    )
    return _LayerDecision(profile=profile, rule_id=rule_id)


def _evaluate_task_layer(signals: SignalBundle) -> _LayerDecision:
    scores = _score_profiles((*signals.task_node_ids, *signals.constrained_task_ids))
    profile, rule_id = _resolve_scored_profile(
        scores,
        default_rule_id=_RULE_TASK_KEYWORD,
        tie_break_rule_id=_RULE_TASK_TIE_BREAK,
    )
    return _LayerDecision(profile=profile, rule_id=rule_id)


def _evaluate_acceptance_layer(signals: SignalBundle) -> _LayerDecision:
    acceptance_gate = _normalize_text(signals.acceptance_decision).upper()
    if acceptance_gate != "PASS":
        return _LayerDecision(profile=None, rule_id=None)
    scores = _score_profiles(signals.acceptance_criterion_ids)
    profile, rule_id = _resolve_scored_profile(
        scores,
        default_rule_id=_RULE_ACCEPTANCE_KEYWORD,
        tie_break_rule_id=_RULE_ACCEPTANCE_TIE_BREAK,
    )
    return _LayerDecision(profile=profile, rule_id=rule_id)


def _score_profiles(texts: Iterable[str]) -> dict[RouteProfile, int]:
    scores: dict[RouteProfile, int] = {}
    for raw_text in texts:
        text = _normalize_text(raw_text).casefold()
        if not text:
            continue
        for profile, keywords in _PROFILE_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                scores[profile] = scores.get(profile, 0) + 1
    return scores


def _resolve_scored_profile(
    scores: Mapping[RouteProfile, int],
    *,
    default_rule_id: str,
    tie_break_rule_id: str,
) -> tuple[RouteProfile | None, str | None]:
    if not scores:
        return None, None
    max_score = max(scores.values())
    leaders = tuple(profile for profile, score in scores.items() if score == max_score)
    if len(leaders) == 1:
        return leaders[0], default_rule_id
    for profile in PROFILE_TIE_BREAK_ORDER:
        if profile in leaders:
            return profile, tie_break_rule_id
    return None, None


def _explicit_profiles_from_constraints(constraints: Sequence[ConstraintSignal]) -> tuple[RouteProfile, ...]:
    found: list[RouteProfile] = []
    for constraint in constraints:
        if _normalize_text(constraint.key).casefold() != "route_profile":
            continue
        profile = _profile_from_text(constraint.value)
        if profile is not None:
            found.append(profile)
    unique = sorted(set(found), key=lambda profile: profile.value)
    return tuple(unique)


def _profile_from_text(text: str) -> RouteProfile | None:
    normalized = _normalize_text(text).upper()
    for profile in PROFILE_TIE_BREAK_ORDER:
        if normalized == profile.value:
            return profile
    if normalized == RouteProfile.NEEDS_REVIEW.value:
        return RouteProfile.NEEDS_REVIEW
    return None


def _iter_constraint_text(constraints: Sequence[ConstraintSignal]) -> tuple[str, ...]:
    values: list[str] = []
    for constraint in constraints:
        values.append(constraint.key)
        values.append(constraint.value)
        values.append(constraint.source)
    return tuple(values)


def _build_review_selection(
    *,
    dominant_rule_id: str,
    applied_rule_ids: Sequence[str],
    missing_evidence: Sequence[str],
    ambiguity_reasons: Sequence[str],
) -> RouteSelection:
    return RouteSelection(
        decision=RouteDecision.NEEDS_REVIEW,
        route_profile=RouteProfile.NEEDS_REVIEW,
        dominant_layer="review",
        dominant_rule_id=dominant_rule_id,
        applied_rule_ids=tuple(applied_rule_ids),
        missing_evidence=tuple(missing_evidence),
        ambiguity_reasons=tuple(ambiguity_reasons),
    )


def _normalize_text(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _normalize_sorted_text(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({text for text in (_normalize_text(value) for value in values) if text}))


def _unique_in_order(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = _normalize_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _with_rule(existing: Sequence[str], rule_id: str) -> tuple[str, ...]:
    if rule_id in existing:
        return tuple(existing)
    return (*existing, rule_id)


__all__ = [
    "PRECEDENCE_ORDER",
    "PROFILE_TIE_BREAK_ORDER",
    "RouteSelection",
    "select_route",
]
