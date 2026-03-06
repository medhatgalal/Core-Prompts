"""UPLIFT-DECOMP deterministic decomposition coverage."""

from __future__ import annotations

import pytest

from intent_pipeline.uplift.task_decomposition import (
    TaskGraphValidationCode,
    TaskGraphValidationError,
    build_task_graph,
)


REQUIREMENT_ID = "UPLIFT-DECOMP"


def test_uplift_decomp_01_graph_is_deterministic_and_dependency_safe() -> None:
    tasks = [
        {
            "id": "build",
            "title": "Build modules",
            "depends_on": ["plan"],
            "constraint_keys": ["schema-version"],
        },
        {
            "id": "plan",
            "title": "Plan scope",
            "subtasks": [
                {"id": "collect", "title": "Collect context"},
                {
                    "id": "define",
                    "title": "Define constraints",
                    "depends_on": ["collect"],
                    "constraint_keys": ["timebox"],
                },
            ],
        },
        {"id": "verify", "title": "Verify output", "depends_on": ["build"]},
    ]

    graph_first = build_task_graph(tasks)
    graph_second = build_task_graph(tasks)

    assert graph_first.to_json() == graph_second.to_json()
    ordered_ids = [node.node_id for node in graph_first.nodes]
    assert ordered_ids == ["plan", "build", "verify", "collect", "define"]
    assert ordered_ids.index("plan") < ordered_ids.index("build")
    assert ordered_ids.index("build") < ordered_ids.index("verify")
    assert ordered_ids.index("collect") < ordered_ids.index("define")
    assert [(edge.from_id, edge.to_id) for edge in graph_first.edges] == [
        ("build", "verify"),
        ("collect", "define"),
        ("plan", "build"),
    ]


def test_uplift_decomp_02_depth_is_limited_to_two_levels() -> None:
    tasks = [
        {
            "id": "parent",
            "title": "Parent",
            "subtasks": [
                {
                    "id": "child",
                    "title": "Child",
                    "subtasks": [{"id": "grandchild", "title": "Grandchild"}],
                }
            ],
        }
    ]

    with pytest.raises(TaskGraphValidationError) as exc_info:
        build_task_graph(tasks)

    failure = exc_info.value.failure
    assert failure.code is TaskGraphValidationCode.DEPTH_LIMIT_EXCEEDED
    assert failure.as_payload()["detail"] == {"depth": 3, "max_depth": 2}


def test_uplift_decomp_03_cycle_error_includes_stable_payload() -> None:
    tasks = [
        {"id": "alpha", "title": "Alpha", "depends_on": ["beta"]},
        {"id": "beta", "title": "Beta", "depends_on": ["alpha"]},
    ]

    with pytest.raises(TaskGraphValidationError) as exc_info:
        build_task_graph(tasks)

    failure = exc_info.value.failure
    assert failure.code is TaskGraphValidationCode.CYCLE_DETECTED
    assert failure.as_payload()["detail"] == {"cycle_nodes": ["alpha", "beta"]}


def test_uplift_decomp_04_tie_break_order_is_canonical_under_input_permutations() -> None:
    tasks_variant_a = [
        {"id": "c", "title": "Gamma"},
        {"id": "a", "title": "Alpha"},
        {"id": "b", "title": "Beta"},
    ]
    tasks_variant_b = [
        {"id": "b", "title": "Beta"},
        {"id": "c", "title": "Gamma"},
        {"id": "a", "title": "Alpha"},
    ]

    graph_a = build_task_graph(tasks_variant_a)
    graph_b = build_task_graph(tasks_variant_b)

    assert graph_a.to_json() == graph_b.to_json()
    assert [node.node_id for node in graph_a.nodes] == ["a", "b", "c"]


def test_uplift_decomp_05_cycle_matrix_reports_all_cycle_nodes() -> None:
    tasks = [
        {"id": "alpha", "title": "Alpha", "depends_on": ["gamma"]},
        {"id": "beta", "title": "Beta", "depends_on": ["alpha"]},
        {"id": "gamma", "title": "Gamma", "depends_on": ["beta"]},
    ]

    with pytest.raises(TaskGraphValidationError) as exc_info:
        build_task_graph(tasks)

    failure = exc_info.value.failure
    assert failure.code is TaskGraphValidationCode.CYCLE_DETECTED
    assert failure.as_payload()["detail"] == {"cycle_nodes": ["alpha", "beta", "gamma"]}


def test_uplift_decomp_06_repeated_runs_are_byte_stable() -> None:
    tasks = [
        {"id": "build", "title": "Build", "depends_on": ["plan"]},
        {"id": "plan", "title": "Plan"},
        {"id": "verify", "title": "Verify", "depends_on": ["build"]},
    ]

    payloads = [build_task_graph(tasks).to_json() for _ in range(8)]
    assert payloads == [payloads[0]] * len(payloads)
