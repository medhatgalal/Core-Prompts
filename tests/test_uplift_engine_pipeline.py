from __future__ import annotations

from intent_pipeline.uplift.engine import run_uplift_engine


def _sample_uplift_input() -> str:
    return "\n".join(
        [
            "Primary Objective: Compose deterministic uplift contract",
            "Secondary Objectives: Keep criterion evidence linked to task ids",
            "In Scope: Context Layer, Intent Layer, Task Decomposition, Constraint Architecture, Acceptance Criteria",
            "Out of Scope: Rosetta translation, target tool validation, output generation",
            "Must keep schema major version deterministic.",
            "Acceptance Criteria: criterion-level evidence links back to deterministic task ids.",
        ]
    )


def test_uplift_pipeline_01_engine_returns_canonical_contract_shape() -> None:
    contract = run_uplift_engine(_sample_uplift_input())
    payload = contract.as_payload()

    assert "uplift"
    assert list(payload.keys()) == [
        "schema_version",
        "context",
        "intent",
        "task_graph",
        "constraints",
        "acceptance",
    ]
    assert payload["schema_version"].split(".", 1)[0] == "2"
    assert payload["context"]["schema_version"].split(".", 1)[0] == "2"
    assert payload["acceptance"]["decision"] == "PASS"


def test_uplift_pipeline_02_acceptance_evidence_links_to_task_graph_nodes() -> None:
    contract = run_uplift_engine(_sample_uplift_input())
    payload = contract.as_payload()

    node_ids = {node["node_id"] for node in payload["task_graph"]["nodes"]}
    assert node_ids
    for criterion in payload["acceptance"]["criteria"]:
        assert criterion["task_ids"]
        assert set(criterion["task_ids"]).issubset(node_ids)
        for evidence in criterion["evidence"]:
            assert evidence["task_id"] in node_ids


def test_uplift_pipeline_03_repeated_runs_are_byte_stable() -> None:
    payloads = [run_uplift_engine(_sample_uplift_input()).to_json() for _ in range(20)]
    assert payloads == [payloads[0]] * len(payloads)


def test_uplift_pipeline_04_acceptance_criteria_retain_stable_task_linkage() -> None:
    contract = run_uplift_engine(_sample_uplift_input())
    payload = contract.as_payload()
    criteria = payload["acceptance"]["criteria"]

    assert [criterion["criterion_id"] for criterion in criteria] == [
        "hard-constraint-conflicts",
        "hard-context-schema",
        "hard-task-graph",
        "soft-acceptance-signals",
        "soft-intent-completeness",
    ]
    for criterion in criteria:
        task_ids = criterion["task_ids"]
        evidence_task_ids = sorted({entry["task_id"] for entry in criterion["evidence"]})
        assert task_ids == evidence_task_ids
