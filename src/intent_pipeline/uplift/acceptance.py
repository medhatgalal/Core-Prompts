"""Deterministic acceptance evaluator for uplift contracts."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from intent_pipeline.uplift.contracts import (
    AcceptanceCriterion,
    AcceptanceDecision,
    AcceptanceEvidence,
    AcceptanceReport,
)


ACCEPTANCE_MAX_SCORE = 100
ACCEPTANCE_THRESHOLD = 70

_CRITERION_WEIGHTS: dict[str, int] = {
    "hard-context-schema": 30,
    "hard-task-graph": 30,
    "hard-constraint-conflicts": 20,
    "soft-acceptance-signals": 10,
    "soft-intent-completeness": 10,
}


def _major_version(value: str) -> str:
    return value.split(".", 1)[0]


def _node_ids(task_graph: Mapping[str, Any]) -> tuple[str, ...]:
    nodes = task_graph.get("nodes")
    if not isinstance(nodes, Sequence):
        return ()
    extracted: list[str] = []
    for node in nodes:
        if not isinstance(node, Mapping):
            continue
        node_id = node.get("node_id")
        if isinstance(node_id, str) and node_id.strip():
            extracted.append(node_id.strip())
    seen: set[str] = set()
    ordered: list[str] = []
    for node_id in extracted:
        if node_id in seen:
            continue
        seen.add(node_id)
        ordered.append(node_id)
    return tuple(ordered)


def _constraint_linked_task_ids(task_graph: Mapping[str, Any], ordered_node_ids: tuple[str, ...]) -> tuple[str, ...]:
    nodes = task_graph.get("nodes")
    if not isinstance(nodes, Sequence):
        return ordered_node_ids[:1]
    linked: list[str] = []
    for node in nodes:
        if not isinstance(node, Mapping):
            continue
        node_id = node.get("node_id")
        constraint_keys = node.get("constraint_keys")
        if (
            isinstance(node_id, str)
            and node_id.strip()
            and isinstance(constraint_keys, Sequence)
            and len(constraint_keys) > 0
        ):
            linked.append(node_id.strip())
    if linked:
        return tuple(sorted(set(linked)))
    return ordered_node_ids[:1]


def _criterion(
    *,
    criterion_id: str,
    label: str,
    is_hard: bool,
    passed: bool,
    rationale: str,
    source: str,
    detail: str,
    task_ids: tuple[str, ...],
) -> AcceptanceCriterion:
    evidence_items = tuple(
        AcceptanceEvidence(
            evidence_id=f"{criterion_id}-ev-{index + 1:02d}",
            task_id=task_id,
            source=source,
            detail=detail,
        )
        for index, task_id in enumerate(task_ids)
    )
    score = _CRITERION_WEIGHTS[criterion_id] if passed else 0
    return AcceptanceCriterion(
        criterion_id=criterion_id,
        label=label,
        is_hard=is_hard,
        passed=passed,
        score=score,
        max_score=_CRITERION_WEIGHTS[criterion_id],
        rationale=rationale,
        evidence=evidence_items,
    )


def evaluate_acceptance(
    *,
    context: Mapping[str, Any],
    intent: Mapping[str, Any],
    task_graph: Mapping[str, Any],
    constraints: Mapping[str, Any],
) -> AcceptanceReport:
    """Evaluate deterministic gate-plus-score acceptance outcome."""
    if not isinstance(context, Mapping):
        raise TypeError("context must be a mapping")
    if not isinstance(intent, Mapping):
        raise TypeError("intent must be a mapping")
    if not isinstance(task_graph, Mapping):
        raise TypeError("task_graph must be a mapping")
    if not isinstance(constraints, Mapping):
        raise TypeError("constraints must be a mapping")

    ordered_node_ids = _node_ids(task_graph)
    default_task_id = ordered_node_ids[0] if ordered_node_ids else "system.acceptance"
    missing_evidence: list[str] = []

    schema_version = context.get("schema_version")
    schema_present = isinstance(schema_version, str) and bool(schema_version.strip())
    if not schema_present:
        missing_evidence.append("context.schema_version")
    schema_supported = schema_present and _major_version(schema_version.strip()) == "2"
    context_schema = _criterion(
        criterion_id="hard-context-schema",
        label="Context schema major is supported",
        is_hard=True,
        passed=schema_supported,
        rationale=(
            "Context schema major is 2.x and accepted."
            if schema_supported
            else "Context schema is missing or not 2.x."
        ),
        source="context.schema_version",
        detail=f"schema_version={schema_version!r}",
        task_ids=(default_task_id,),
    )

    nodes_present = len(ordered_node_ids) > 0
    if not nodes_present:
        missing_evidence.append("task_graph.nodes")
    task_graph_criterion = _criterion(
        criterion_id="hard-task-graph",
        label="Task graph contains linked execution tasks",
        is_hard=True,
        passed=nodes_present,
        rationale=(
            f"Task graph exposes {len(ordered_node_ids)} deterministic task nodes."
            if nodes_present
            else "Task graph has no task nodes to link acceptance evidence."
        ),
        source="task_graph.nodes",
        detail=f"node_count={len(ordered_node_ids)}",
        task_ids=(default_task_id,),
    )

    conflicts_raw = constraints.get("conflicts")
    if not isinstance(conflicts_raw, Sequence):
        conflicts_raw = []
        missing_evidence.append("constraints.conflicts")
    hard_conflict_present = False
    for conflict in conflicts_raw:
        if not isinstance(conflict, Mapping):
            continue
        code = conflict.get("code")
        if isinstance(code, str) and code.strip().upper() == "HARD_CONFLICT":
            hard_conflict_present = True
            break
    constraints_criterion = _criterion(
        criterion_id="hard-constraint-conflicts",
        label="No unresolved hard constraint conflicts",
        is_hard=True,
        passed=not hard_conflict_present,
        rationale=(
            "Constraint payload has no hard conflicts."
            if not hard_conflict_present
            else "Hard constraint conflicts are present in constraint payload."
        ),
        source="constraints.conflicts",
        detail=f"hard_conflict_present={hard_conflict_present}",
        task_ids=_constraint_linked_task_ids(task_graph, ordered_node_ids) or (default_task_id,),
    )

    acceptance_inputs = context.get("acceptance_inputs")
    acceptance_signals_present = isinstance(acceptance_inputs, Sequence) and len(acceptance_inputs) > 0
    if not isinstance(acceptance_inputs, Sequence):
        missing_evidence.append("context.acceptance_inputs")
    acceptance_signals = _criterion(
        criterion_id="soft-acceptance-signals",
        label="Acceptance signals are available",
        is_hard=False,
        passed=acceptance_signals_present,
        rationale=(
            "Acceptance inputs are present for criterion-level evaluation."
            if acceptance_signals_present
            else "Acceptance inputs are absent or empty."
        ),
        source="context.acceptance_inputs",
        detail=f"acceptance_input_count={len(acceptance_inputs) if isinstance(acceptance_inputs, Sequence) else 0}",
        task_ids=(default_task_id,),
    )

    unknowns = intent.get("unknowns")
    unknown_list: list[str] = []
    if isinstance(unknowns, Sequence):
        for item in unknowns:
            if isinstance(item, str) and item.strip():
                unknown_list.append(item.strip())
    else:
        missing_evidence.append("intent.unknowns")
    intent_complete = len(unknown_list) == 0
    intent_completeness = _criterion(
        criterion_id="soft-intent-completeness",
        label="Intent evidence is complete",
        is_hard=False,
        passed=intent_complete,
        rationale=(
            "Intent layer unknowns are empty."
            if intent_complete
            else "Intent layer reports missing or ambiguous evidence."
        ),
        source="intent.unknowns",
        detail=f"unknown_count={len(unknown_list)}",
        task_ids=(default_task_id,),
    )

    criteria = (
        context_schema,
        task_graph_criterion,
        constraints_criterion,
        acceptance_signals,
        intent_completeness,
    )
    score = sum(criterion.score for criterion in criteria)
    failed_hard_criteria = tuple(
        criterion.criterion_id for criterion in criteria if criterion.is_hard and not criterion.passed
    )
    normalized_missing = tuple(sorted(set(missing_evidence)))

    if normalized_missing:
        decision = AcceptanceDecision.NEEDS_REVIEW
    elif failed_hard_criteria:
        decision = AcceptanceDecision.FAIL
    elif score >= ACCEPTANCE_THRESHOLD:
        decision = AcceptanceDecision.PASS
    else:
        decision = AcceptanceDecision.FAIL

    summary = (
        f"Decision={decision.value}; score={score}/{ACCEPTANCE_MAX_SCORE}; "
        f"threshold={ACCEPTANCE_THRESHOLD}; "
        f"failed_hard={len(failed_hard_criteria)}; missing={len(normalized_missing)}"
    )
    return AcceptanceReport(
        decision=decision,
        score=score,
        max_score=ACCEPTANCE_MAX_SCORE,
        threshold=ACCEPTANCE_THRESHOLD,
        criteria=criteria,
        missing_evidence=normalized_missing,
        failed_hard_criteria=failed_hard_criteria,
        summary=summary,
    )


__all__ = ["ACCEPTANCE_MAX_SCORE", "ACCEPTANCE_THRESHOLD", "evaluate_acceptance"]
