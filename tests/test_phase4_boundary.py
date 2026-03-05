from __future__ import annotations

import ast
import inspect
from pathlib import Path

from intent_pipeline.phase4.contracts import (
    Phase4BoundaryErrorCode,
    Phase4BoundaryViolation,
)
from intent_pipeline.phase4.engine import run_phase4


def test_bound_04_phase4_entrypoint_signature_is_contract_only() -> None:
    signature = inspect.signature(run_phase4)

    assert "BOUND-04"
    assert tuple(signature.parameters) == ("route_spec", "capability_matrix", "policy_contract")


def test_bound_04_phase4_output_excludes_execution_output_help_runtime_fields(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    payload = run_phase4(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    ).as_payload()

    assert "BOUND-04"
    forbidden_fields = {
        "execution",
        "execution_result",
        "runtime_check",
        "runtime_dependency",
        "output",
        "output_text",
        "help",
        "help_text",
        "assistant_message",
        "chat_response",
        "tool_adapter",
    }

    assert forbidden_fields.isdisjoint(set(payload))
    assert forbidden_fields.isdisjoint(set(payload["validation"]))
    assert forbidden_fields.isdisjoint(set(payload["mock"]))
    assert forbidden_fields.isdisjoint(set(payload["fallback"]))


def test_bound_04_phase4_modules_do_not_import_disallowed_layers() -> None:
    project_root = Path(__file__).resolve().parents[1]
    module_paths = (
        project_root / "src" / "intent_pipeline" / "phase4" / "engine.py",
        project_root / "src" / "intent_pipeline" / "phase4" / "fallback.py",
    )
    forbidden_import_fragments = (
        "execution",
        "output",
        "help",
        "summary.renderer",
        "dependency",
        "subprocess",
        "requests",
        "httpx",
        "socket",
    )

    for module_path in module_paths:
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
        imported_modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")

        normalized = tuple(module.casefold() for module in imported_modules)

        assert "BOUND-04"
        for forbidden in forbidden_import_fragments:
            assert all(forbidden not in module for module in normalized)


def test_bound_04_phase4_engine_composes_validate_mock_fallback_only(
    monkeypatch,
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    calls: list[str] = []

    from intent_pipeline.phase4 import engine as phase4_engine

    original_validate_target = phase4_engine.validate_target
    original_run_mock_execution = phase4_engine.run_mock_execution
    original_resolve_fallback = phase4_engine.resolve_fallback

    def tracked_validate_target(route_spec, capability_matrix, policy_contract):
        calls.append("validate_target")
        return original_validate_target(route_spec, capability_matrix, policy_contract)

    def tracked_run_mock_execution(validation_report):
        calls.append("run_mock_execution")
        return original_run_mock_execution(validation_report)

    def tracked_resolve_fallback(validation_report, mock_trace):
        calls.append("resolve_fallback")
        return original_resolve_fallback(validation_report, mock_trace)

    monkeypatch.setattr(phase4_engine, "validate_target", tracked_validate_target)
    monkeypatch.setattr(phase4_engine, "run_mock_execution", tracked_run_mock_execution)
    monkeypatch.setattr(phase4_engine, "resolve_fallback", tracked_resolve_fallback)

    run_phase4(phase4_route_spec_payload, phase4_capability_matrix_payload, phase4_policy_contract_payload)

    assert "BOUND-04"
    assert calls == ["validate_target", "run_mock_execution", "resolve_fallback"]


def test_bound_04_typed_boundary_codes_and_evidence_paths_are_deterministic() -> None:
    violation = Phase4BoundaryViolation(
        code=Phase4BoundaryErrorCode.FORBIDDEN_RUNTIME_IMPORT,
        evidence_paths=("phase4.boundary.module:engine", "phase4.boundary.import:dependency_checker"),
        detail="forbidden runtime dependency-check import detected",
    )
    payload = violation.as_payload()

    assert "BOUND-04"
    assert payload["code"].startswith("BOUND-04-")
    assert payload["evidence_paths"] == sorted(payload["evidence_paths"])
    assert payload["evidence_paths"] == [
        "phase4.boundary.import:dependency_checker",
        "phase4.boundary.module:engine",
    ]
