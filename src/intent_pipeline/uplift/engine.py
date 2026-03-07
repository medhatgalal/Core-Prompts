"""Phase-2 uplift engine composition."""

from __future__ import annotations

import re
from typing import Any

from intent_pipeline.uplift.acceptance import evaluate_acceptance
from intent_pipeline.uplift.constraints import ConstraintStrength, resolve_constraints
from intent_pipeline.uplift.context_layer import DEFAULT_SCHEMA_VERSION, build_context_layer
from intent_pipeline.uplift.contracts import UPLIFT_CONTRACT_SCHEMA_VERSION, UpliftContract
from intent_pipeline.uplift.intent_layer import derive_intent_layer
from intent_pipeline.uplift.task_decomposition import build_task_graph


_HARD_CONSTRAINT_PATTERN = re.compile(r"\b(must|only|require(?:d|s)?|do not|no)\b", re.IGNORECASE)
_ID_SANITIZER = re.compile(r"[^a-z0-9]+")


def _slugify(raw: str) -> str:
    slug = _ID_SANITIZER.sub("-", raw.casefold()).strip("-")
    return slug or "item"


def _task_specs(intent: dict[str, Any]) -> list[dict[str, object]]:
    in_scope = intent.get("in_scope")
    in_scope_items = [item for item in in_scope if isinstance(item, str) and item.strip()] if isinstance(in_scope, list) else []

    tasks: list[dict[str, object]] = [
        {
            "id": "context-analysis",
            "title": "Analyze context and derive intent",
        },
        {
            "id": "constraint-resolution",
            "title": "Resolve hard and soft constraints",
            "depends_on": ["context-analysis"],
            "constraint_keys": ["schema_version"],
        },
    ]

    scope_node_ids: list[str] = []
    for index, scope_item in enumerate(in_scope_items, start=1):
        node_id = f"scope-{index:02d}-{_slugify(scope_item)[:24]}"
        scope_node_ids.append(node_id)
        tasks.append(
            {
                "id": node_id,
                "title": f"Deliver in-scope objective: {scope_item}",
                "depends_on": ["constraint-resolution"],
                "constraint_keys": ["in_scope"],
            }
        )

    tasks.append(
        {
            "id": "acceptance-review",
            "title": "Evaluate acceptance criteria and evidence links",
            "depends_on": scope_node_ids if scope_node_ids else ["constraint-resolution"],
        }
    )
    return tasks


def _constraint_inputs(context: dict[str, Any], intent: dict[str, Any]) -> list[dict[str, object]]:
    constraints: list[dict[str, object]] = []
    schema_version = context.get("schema_version")
    schema_value = str(schema_version).split(".", 1)[0] if isinstance(schema_version, str) else "2"
    constraints.append(
        {
            "id": "hard-schema-major",
            "key": "schema_version",
            "value": schema_value,
            "strength": ConstraintStrength.HARD.value,
            "priority": 100,
            "source": "context.schema_version",
        }
    )

    quality_constraints = intent.get("quality_constraints")
    if isinstance(quality_constraints, list):
        for index, quality_constraint in enumerate(quality_constraints, start=1):
            if not isinstance(quality_constraint, str):
                continue
            normalized = quality_constraint.strip()
            if not normalized:
                continue
            strength = (
                ConstraintStrength.HARD
                if _HARD_CONSTRAINT_PATTERN.search(normalized)
                else ConstraintStrength.SOFT
            )
            constraints.append(
                {
                    "id": f"quality-{index:02d}",
                    "key": f"quality_rule_{index:02d}",
                    "value": normalized,
                    "strength": strength.value,
                    "priority": max(1, 40 - index),
                    "source": "intent.quality_constraints",
                }
            )
    return constraints


def run_uplift_engine(
    sanitized_text: str,
    *,
    schema_version: str = DEFAULT_SCHEMA_VERSION,
    source_metadata: dict[str, object] | None = None,
) -> UpliftContract:
    """Compose deterministic phase-2 uplift layers into one canonical contract."""
    context = build_context_layer(
        sanitized_text,
        schema_version=schema_version,
        source_metadata=source_metadata,
    )
    intent = derive_intent_layer(context)
    task_graph = build_task_graph(_task_specs(intent))
    constraints = resolve_constraints(_constraint_inputs(context, intent))
    acceptance = evaluate_acceptance(
        context=context,
        intent=intent,
        task_graph=task_graph.as_payload(),
        constraints=constraints.as_payload(),
    )

    return UpliftContract(
        schema_version=UPLIFT_CONTRACT_SCHEMA_VERSION,
        context=context,
        intent=intent,
        task_graph=task_graph.as_payload(),
        constraints=constraints.as_payload(),
        acceptance=acceptance,
    )


__all__ = ["run_uplift_engine"]
