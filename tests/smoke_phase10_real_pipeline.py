from __future__ import annotations

import json
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from intent_pipeline.ingestion.url_policy import UrlSourceRejectedError
from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.phase6.contracts import ApprovalMode, ExecutionApprovalContract, ExecutionRequest
from intent_pipeline.phase6.engine import run_phase6
from intent_pipeline.pipeline import ingest_phase1_source, run_phase1_pipeline
from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uplift.engine import run_uplift_engine

NEGATIVE_URL = "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore"
POSITIVE_URL = (
    "https://raw.githubusercontent.com/kubernetes/enhancements/master/keps/"
    "sig-api-machinery/2885-server-side-unknown-field-validation/README.md"
)


def _extension_policy_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "extension_mode": "CONTROLLED",
        "rules": [
            {
                "rule_id": "v1.url.allow",
                "source_kind": "URL",
                "decision": "ALLOW",
                "priority": 10,
                "evidence_paths": ["policy_contract.rules[0]"],
            }
        ],
    }


def _url_policy_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "rules": [
            {
                "rule_id": "v1.url.raw-github-python-gitignore",
                "allowed_schemes": ["https"],
                "allowed_hosts": ["raw.githubusercontent.com"],
                "allowed_domains": [],
                "allowed_path_prefixes": ["/github/gitignore/main/"],
                "allowed_content_types": ["text/plain"],
                "max_bytes": 262144,
                "redirect_limit": 2,
                "timeout_seconds": 15,
                "priority": 10,
                "evidence_paths": ["url_policy.rules[0]"],
            },
            {
                "rule_id": "v1.url.raw-kubernetes-kep-2885",
                "allowed_schemes": ["https"],
                "allowed_hosts": ["raw.githubusercontent.com"],
                "allowed_domains": [],
                "allowed_path_prefixes": [
                    "/kubernetes/enhancements/master/keps/sig-api-machinery/2885-server-side-unknown-field-validation/"
                ],
                "allowed_content_types": ["text/plain"],
                "max_bytes": 524288,
                "redirect_limit": 2,
                "timeout_seconds": 15,
                "priority": 20,
                "evidence_paths": ["url_policy.rules[1]"],
            },
        ],
    }


def _build_capability_matrix(route_spec_payload: dict[str, object]) -> dict[str, object]:
    route_profile = str(route_spec_payload["route_profile"])
    normalized_profile = route_profile.lower().replace("_", "-")
    tool_id = f"tool-{normalized_profile}"
    return {
        "schema_version": "4.0.0",
        "tools": [
            {
                "tool_id": tool_id,
                "supported_route_profiles": [route_profile],
                "capabilities": ["cap.read", "cap.write"],
            }
        ],
    }


def _build_policy_contract(route_spec_payload: dict[str, object], capability_matrix_payload: dict[str, object]) -> dict[str, object]:
    route_profile = str(route_spec_payload["route_profile"])
    tool_id = str(capability_matrix_payload["tools"][0]["tool_id"])
    capabilities = list(capability_matrix_payload["tools"][0]["capabilities"])
    return {
        "schema_version": "4.0.0",
        "route_to_tool": [
            {
                "route_profile": route_profile,
                "tool_id": tool_id,
            }
        ],
        "required_capabilities": [
            {
                "route_profile": route_profile,
                "capabilities": capabilities,
            }
        ],
        "blocked_dominant_rule_ids": [],
        "allowed_route_decisions": ["PASS_ROUTE"],
    }


def _build_registry(request: ExecutionRequest) -> dict[str, object]:
    return {
        "schema_version": "6.0.0",
        "entries": [
            {
                "adapter_id": "hermetic-adapter",
                "route_profile": request.route_profile,
                "target_tool_id": request.target_tool_id,
                "capabilities": list(request.required_capabilities),
                "supports_simulation": True,
                "supports_execution": True,
                "rule_id": "REGISTRY-RULE-001",
            }
        ],
    }


def _build_approval(request: ExecutionRequest, *, mode: ApprovalMode, key: str) -> ExecutionApprovalContract:
    return ExecutionApprovalContract(
        schema_version="6.0.0",
        approval_mode=mode,
        approval_id=f"approval-{mode.value.lower()}",
        approved_by="qa@example.com",
        approved_at="2026-03-10T10:00:00Z",
        expires_at="2026-03-11T10:00:00Z",
        idempotency_key=key,
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        required_capabilities=request.required_capabilities,
        policy_schema_version=request.policy_schema_version,
        policy_rule_ids=request.policy_rule_ids,
    )


def _assert_concise_summary(summary: str) -> None:
    bullet_lines = [line for line in summary.splitlines() if line.startswith("- ")]
    assert bullet_lines, "summary must contain bullet output"
    assert len(bullet_lines) <= 10, f"summary too long: {len(bullet_lines)} bullets"
    assert "Primary Objective" in summary or "Intent" in summary, "summary lacks intent framing"



def main() -> int:
    extension_policy = _extension_policy_payload()
    url_policy = _url_policy_payload()
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_root = Path(temp_dir) / "snapshots"
        journal_root = Path(temp_dir) / "journals"
        now = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)

        try:
            ingest_phase1_source(
                NEGATIVE_URL,
                extension_mode="CONTROLLED",
                route_profile="IMPLEMENTATION",
                requested_capabilities=("cap.read",),
                extension_policy=extension_policy,
                url_policy=url_policy,
                snapshot_root=snapshot_root,
            )
        except UrlSourceRejectedError as exc:
            negative_payload = {
                "normalized_source": exc.rejection.normalized_source,
                "policy_rule_id": exc.rejection.matched_rule_id,
                "rejection_code": exc.rejection.code.value,
                "terminal_status": exc.rejection.terminal_status,
                "detail": exc.rejection.detail,
                "evidence_paths": list(exc.rejection.evidence_paths),
            }
        else:
            raise AssertionError("negative real source must be rejected before Phase 6")

        ingestion = ingest_phase1_source(
            POSITIVE_URL,
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=extension_policy,
            url_policy=url_policy,
            snapshot_root=snapshot_root,
        )
        summary = run_phase1_pipeline(
            POSITIVE_URL,
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=extension_policy,
            url_policy=url_policy,
            snapshot_root=snapshot_root,
        )
        uplift = run_uplift_engine(ingestion.raw_text, source_metadata=ingestion.source_metadata)
        routing = run_semantic_routing(uplift)

        capability_matrix_payload = _build_capability_matrix(routing.route_spec.as_payload())
        policy_contract_payload = _build_policy_contract(routing.route_spec.as_payload(), capability_matrix_payload)
        phase4_result = run_phase4(routing.route_spec.as_payload(), capability_matrix_payload, policy_contract_payload)
        phase5_result = run_phase5(phase4_result)
        request = ExecutionRequest.from_phase_results(
            phase4_result,
            phase5_result,
            policy_schema_version="4.0.0",
            policy_rule_ids=("POLICY-RULE-001",),
        )
        registry = _build_registry(request)
        simulate_approval = _build_approval(request, mode=ApprovalMode.SIMULATE_ONLY, key="real-source-simulate")
        execute_approval = _build_approval(request, mode=ApprovalMode.EXECUTE_APPROVED, key="real-source-execute")
        simulate_result = run_phase6(
            request,
            simulate_approval,
            registry,
            journal_root=journal_root / "simulate",
            now=now,
        )
        execute_result = run_phase6(
            request,
            execute_approval,
            registry,
            journal_root=journal_root / "execute",
            now=now,
        )

    uplift_payload = uplift.as_payload()
    routing_payload = routing.as_payload()
    phase4_payload = phase4_result.as_payload()
    phase5_payload = phase5_result.as_payload()
    simulate_payload = simulate_result.as_payload()
    execute_payload = execute_result.as_payload()

    _assert_concise_summary(summary)
    assert negative_payload["rejection_code"] == "URL-INGEST-013-UNSUITABLE-CONTENT"
    assert negative_payload["terminal_status"] == "REJECTED"
    assert ingestion.source_metadata["normalized_source"] == POSITIVE_URL
    assert ingestion.source_metadata["policy_rule_id"] == "v1.url.raw-kubernetes-kep-2885"
    assert ingestion.source_metadata["content_sha256"]
    assert uplift_payload["intent"]["primary_objective"]
    assert uplift_payload["intent"]["in_scope"] or uplift_payload["intent"]["out_of_scope"]
    assert routing_payload["route_selection"]["decision"] == "PASS_ROUTE"
    assert phase4_payload["validation"]["decision"] == "PASS"
    assert phase4_payload["validation"]["can_proceed"] is True
    assert phase4_payload["fallback"]["decision"] == "USE_PRIMARY"
    assert phase5_payload["output"]["machine_payload"]["terminal_status"] == "USE_PRIMARY"
    assert simulate_payload["decision"] == "SIMULATED"
    assert simulate_payload["decision_code"] == "EXEC-017-SIMULATION-COMPLETED"
    assert execute_payload["decision"] == "EXECUTED"
    assert execute_payload["decision_code"] == "EXEC-018-EXECUTION-COMPLETED"
    assert all(item.startswith("phase6:simulate:") for item in simulate_payload["produced_artifacts"])
    assert all(item.startswith("phase6:execute:") for item in execute_payload["produced_artifacts"])

    report = {
        "negative_case": negative_payload,
        "positive_case": {
            "url": POSITIVE_URL,
            "normalized_source": ingestion.source_metadata["normalized_source"],
            "policy_rule_id": ingestion.source_metadata["policy_rule_id"],
            "content_sha256": ingestion.source_metadata["content_sha256"],
            "first_10_lines": ingestion.raw_text.splitlines()[:10],
            "summary": summary,
            "uplift_intent": {
                "primary_objective": uplift_payload["intent"].get("primary_objective"),
                "in_scope": uplift_payload["intent"].get("in_scope"),
                "out_of_scope": uplift_payload["intent"].get("out_of_scope"),
            },
            "routing": routing_payload["route_selection"],
            "phase4": {
                "validation_decision": phase4_payload["validation"]["decision"],
                "validation_can_proceed": phase4_payload["validation"]["can_proceed"],
                "fallback_decision": phase4_payload["fallback"]["decision"],
            },
            "phase5": {
                "terminal_status": phase5_payload["output"]["machine_payload"]["terminal_status"],
                "output_code": phase5_payload["output"]["machine_payload"]["output_code"],
            },
            "phase6_simulate": {
                "decision": simulate_payload["decision"],
                "decision_code": simulate_payload["decision_code"],
                "journal_path": simulate_payload["journal_path"],
                "produced_artifacts": simulate_payload["produced_artifacts"],
            },
            "phase6_execute": {
                "decision": execute_payload["decision"],
                "decision_code": execute_payload["decision_code"],
                "journal_path": execute_payload["journal_path"],
                "produced_artifacts": execute_payload["produced_artifacts"],
            },
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
