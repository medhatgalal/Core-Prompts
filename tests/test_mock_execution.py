from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

from intent_pipeline.phase4.contracts import (
    MockDecision,
    MockErrorCode,
    MockStage,
    MockStepStatus,
)
from intent_pipeline.phase4.mock_executor import run_mock_execution
from intent_pipeline.phase4.validator import validate_target


def test_mock_01_dry_run_only_no_side_effect_imports_or_calls(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    validation_report = validate_target(
        deepcopy(phase4_route_spec_payload),
        deepcopy(phase4_capability_matrix_payload),
        deepcopy(phase4_policy_contract_payload),
    )
    trace = run_mock_execution(validation_report)

    assert "MOCK-01"
    assert trace.decision is MockDecision.PASS
    assert [step.stage for step in trace.steps] == [
        MockStage.PRECHECK,
        MockStage.PLAN,
        MockStage.SIMULATE,
        MockStage.VERIFY,
    ]
    assert [step.status for step in trace.steps] == [
        MockStepStatus.PASS,
        MockStepStatus.PASS,
        MockStepStatus.PASS,
        MockStepStatus.PASS,
    ]
    assert all("dry-run" in step.action for step in trace.steps)

    module_path = Path(__file__).resolve().parents[1] / "src" / "intent_pipeline" / "phase4" / "mock_executor.py"
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))

    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")

    forbidden_import_fragments = (
        "phase6",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "shutil",
        "pathlib",
        "os",
    )
    normalized_imports = tuple(module.casefold() for module in imported_modules)
    for forbidden in forbidden_import_fragments:
        assert all(forbidden not in module for module in normalized_imports)

    called_names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            called_names.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            called_names.append(node.func.attr)

    forbidden_call_names = {
        "open",
        "system",
        "popen",
        "run",
        "check_call",
        "check_output",
        "unlink",
        "remove",
        "rmtree",
        "rename",
        "replace",
        "write_text",
        "write_bytes",
        "request",
        "get",
        "post",
        "put",
        "delete",
    }
    assert forbidden_call_names.isdisjoint(set(called_names))


def test_mock_02_trace_is_deterministic_and_failure_evidence_linked(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    blocking_policy = deepcopy(phase4_policy_contract_payload)
    blocking_policy["required_capabilities"][0]["capabilities"] = ["cap.read", "cap.write", "cap.execute"]
    validation_block = validate_target(
        deepcopy(phase4_route_spec_payload),
        deepcopy(phase4_capability_matrix_payload),
        blocking_policy,
    )

    outputs = [run_mock_execution(validation_block).to_json() for _ in range(20)]
    trace = run_mock_execution(validation_block)

    assert "MOCK-02"
    assert trace.decision is MockDecision.FAIL
    assert outputs == [outputs[0]] * len(outputs)
    assert [step.stage for step in trace.steps] == [
        MockStage.PRECHECK,
        MockStage.PLAN,
        MockStage.SIMULATE,
        MockStage.VERIFY,
    ]
    assert [step.status for step in trace.steps] == [
        MockStepStatus.FAIL,
        MockStepStatus.SKIP,
        MockStepStatus.SKIP,
        MockStepStatus.SKIP,
    ]

    failed_step = trace.steps[0]
    assert failed_step.error_code is MockErrorCode.VALIDATION_NOT_PASS
    assert any(path.startswith("route_spec.") for path in failed_step.evidence_paths)
    assert any(path.startswith("capability_matrix.") for path in failed_step.evidence_paths)
    assert any(path.startswith("validation_report.") for path in failed_step.evidence_paths)
    assert any(path.startswith("mock_trace.steps.") for path in failed_step.evidence_paths)

    for skipped_step in trace.steps[1:]:
        assert skipped_step.error_code is None
