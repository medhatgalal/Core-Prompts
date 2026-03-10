from __future__ import annotations

import ast
import inspect
from pathlib import Path

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.contracts import (
    Phase5BoundaryErrorCode,
    Phase5BoundaryViolation,
)
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uplift.engine import run_uplift_engine


def _phase5_input_text() -> str:
    return "\n".join(
        [
            "Primary Objective: enforce deterministic runtime/output/help boundaries.",
            "Secondary Objectives: keep preflight checks side-effect free.",
            "In Scope: runtime dependency reports, output rendering, help resolution.",
            "Out of Scope: execution, package installation, network operations.",
            "Must keep deterministic contracts and sorted evidence.",
            "Acceptance Criteria: strict no-execution boundary diagnostics.",
        ]
    )


def _build_phase4_result():
    uplift = run_uplift_engine(_phase5_input_text())
    route_spec = run_semantic_routing(uplift).route_spec.as_payload()
    route_profile = str(route_spec["route_profile"])
    tool_id = f"tool-{route_profile.lower()}"
    capability_matrix = {
        "schema_version": "4.0.0",
        "tools": [
            {
                "tool_id": tool_id,
                "supported_route_profiles": [route_profile],
                "capabilities": ["cap.read", "cap.write"],
            }
        ],
    }
    policy_contract = {
        "schema_version": "4.0.0",
        "route_to_tool": [{"route_profile": route_profile, "tool_id": tool_id}],
        "required_capabilities": [{"route_profile": route_profile, "capabilities": ["cap.read", "cap.write"]}],
        "blocked_dominant_rule_ids": [],
        "allowed_route_decisions": ["PASS_ROUTE"],
    }
    return run_phase4(route_spec, capability_matrix, policy_contract)


def test_bound_05_phase5_entrypoint_signature_is_contract_only() -> None:
    signature = inspect.signature(run_phase5)

    assert "BOUND-05"
    assert tuple(signature.parameters) == ("phase4_result", "dependency_specs", "topic", "code")
    assert signature.parameters["dependency_specs"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["topic"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["code"].kind is inspect.Parameter.KEYWORD_ONLY


def test_bound_05_phase5_output_excludes_execution_install_and_network_fields() -> None:
    payload = run_phase5(_build_phase4_result()).as_payload()

    assert "BOUND-05"
    forbidden_fields = {
        "execution",
        "execution_result",
        "runtime_execute",
        "auto_remediation",
        "install",
        "dependency_install",
        "network_fetch",
        "http_request",
        "tool_invocation",
    }

    assert forbidden_fields.isdisjoint(set(payload))
    assert forbidden_fields.isdisjoint(set(payload["runtime"]))
    assert forbidden_fields.isdisjoint(set(payload["output"]))
    assert forbidden_fields.isdisjoint(set(payload["help"]))


def test_bound_05_phase5_modules_do_not_import_or_call_forbidden_execution_layers() -> None:
    project_root = Path(__file__).resolve().parents[1]
    module_paths = (
        project_root / "src" / "intent_pipeline" / "phase5" / "engine.py",
        project_root / "src" / "intent_pipeline" / "phase5" / "runtime_checks.py",
        project_root / "src" / "intent_pipeline" / "phase5" / "help.py",
    )
    forbidden_import_fragments = (
        "phase6",
        "subprocess",
        "requests",
        "httpx",
        "socket",
        "urllib.request",
        "pip",
        "ensurepip",
        "venv",
    )
    forbidden_calls = {
        "os.system",
        "subprocess.run",
        "subprocess.Popen",
        "requests.get",
        "httpx.get",
        "urllib.request.urlopen",
        "socket.create_connection",
    }

    for module_path in module_paths:
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
        imported_modules: list[str] = []
        call_targets: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    call_targets.append(f"{node.func.value.id}.{node.func.attr}")
                elif isinstance(node.func, ast.Name):
                    call_targets.append(node.func.id)

        normalized_imports = tuple(module.casefold() for module in imported_modules)

        assert "BOUND-05"
        for forbidden in forbidden_import_fragments:
            if "." in forbidden:
                assert all(forbidden != module for module in normalized_imports)
                continue
            assert all(forbidden not in module.split(".") for module in normalized_imports)
        for forbidden in forbidden_calls:
            assert forbidden not in call_targets


def test_bound_05_typed_boundary_codes_and_evidence_paths_are_deterministic() -> None:
    violation = Phase5BoundaryViolation(
        code=Phase5BoundaryErrorCode.FORBIDDEN_NETWORK_IMPORT,
        evidence_paths=("phase5.boundary.module:engine", "phase5.boundary.import:socket", "phase5.boundary.module:engine"),
        detail="forbidden network dependency/help operation import detected",
    )
    payload = violation.as_payload()

    assert "BOUND-05"
    assert payload["code"].startswith("BOUND-05-")
    assert payload["evidence_paths"] == sorted(payload["evidence_paths"])
    assert payload["evidence_paths"] == [
        "phase5.boundary.import:socket",
        "phase5.boundary.module:engine",
    ]
