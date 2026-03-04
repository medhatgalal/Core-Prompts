from __future__ import annotations

import pytest

from intent_pipeline.uplift.contracts import (
    AcceptanceCriterion,
    AcceptanceDecision,
    AcceptanceEvidence,
    AcceptanceReport,
    UPLIFT_CONTRACT_SCHEMA_VERSION,
    UpliftContract,
)


def _build_sample_acceptance_report() -> AcceptanceReport:
    criteria = (
        AcceptanceCriterion(
            criterion_id="hard-schema",
            label="Schema version supported",
            is_hard=True,
            passed=True,
            score=30,
            max_score=30,
            rationale="Schema major version is 2 and contract is valid.",
            evidence=(
                AcceptanceEvidence(
                    evidence_id="ev-schema-1",
                    task_id="context-analysis",
                    source="context.schema_version",
                    detail="schema_version=2.0.0",
                ),
            ),
        ),
        AcceptanceCriterion(
            criterion_id="soft-traceability",
            label="Traceability links preserved",
            is_hard=False,
            passed=True,
            score=20,
            max_score=20,
            rationale="All criteria include task-linked evidence.",
            evidence=(
                AcceptanceEvidence(
                    evidence_id="ev-trace-1",
                    task_id="acceptance-review",
                    source="acceptance.criteria",
                    detail="criterion evidence references task ids",
                ),
            ),
        ),
    )
    return AcceptanceReport(
        decision=AcceptanceDecision.PASS,
        score=50,
        max_score=50,
        threshold=35,
        criteria=criteria,
        summary="Acceptance passed with deterministic criterion evidence.",
    )


def test_uplift_acceptance_schema_01_contract_payload_has_required_structure() -> None:
    report = _build_sample_acceptance_report()
    contract = UpliftContract(
        schema_version=UPLIFT_CONTRACT_SCHEMA_VERSION,
        context={"schema_version": "2.0.0", "normalized_facts": []},
        intent={"schema_version": "2.0.0", "unknowns": []},
        task_graph={"nodes": [{"node_id": "context-analysis"}, {"node_id": "acceptance-review"}], "edges": []},
        constraints={"applied_hard": [], "applied_soft": [], "dropped_soft": [], "conflicts": []},
        acceptance=report,
    )

    payload = contract.as_payload()
    assert "UPLIFT-ACCEPTANCE"
    assert list(payload.keys()) == [
        "schema_version",
        "context",
        "intent",
        "task_graph",
        "constraints",
        "acceptance",
    ]
    assert payload["acceptance"]["decision"] == "PASS"
    assert payload["acceptance"]["criteria"][0]["task_ids"] == ["context-analysis"]


def test_uplift_acceptance_contract_02_serialization_is_byte_stable() -> None:
    report = _build_sample_acceptance_report()
    contract = UpliftContract(
        schema_version=UPLIFT_CONTRACT_SCHEMA_VERSION,
        context={"schema_version": "2.0.0", "normalized_facts": []},
        intent={"schema_version": "2.0.0", "unknowns": []},
        task_graph={"nodes": [{"node_id": "context-analysis"}], "edges": []},
        constraints={"applied_hard": [], "applied_soft": [], "dropped_soft": [], "conflicts": []},
        acceptance=report,
    )

    outputs = [contract.to_json() for _ in range(16)]
    assert outputs == [outputs[0]] * len(outputs)


def test_uplift_acceptance_schema_03_evidence_requires_task_link_fields() -> None:
    with pytest.raises(ValueError, match="task_id is required"):
        AcceptanceEvidence(
            evidence_id="ev-missing-task",
            task_id="",
            source="acceptance.criteria",
            detail="missing task id should fail",
        )


def test_uplift_acceptance_contract_04_schema_major_is_enforced() -> None:
    report = _build_sample_acceptance_report()
    with pytest.raises(ValueError, match="Unsupported schema major version"):
        UpliftContract(
            schema_version="3.0.0",
            context={"schema_version": "2.0.0"},
            intent={"schema_version": "2.0.0"},
            task_graph={"nodes": [], "edges": []},
            constraints={"applied_hard": [], "applied_soft": [], "dropped_soft": [], "conflicts": []},
            acceptance=report,
        )
