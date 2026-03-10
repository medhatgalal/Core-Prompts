from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from intent_pipeline.ingestion.url_policy import UrlSourceRejectedError
from intent_pipeline.ingestion.url_snapshot_store import UrlTransportResponse
from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.phase6.contracts import ApprovalMode, ExecutionApprovalContract, ExecutionDecisionCode, ExecutionRequest
from intent_pipeline.phase6.engine import run_phase6
from intent_pipeline.pipeline import ingest_phase1_source, run_phase1_pipeline
from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uplift.engine import run_uplift_engine

NEGATIVE_URL = "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore"
KEP_URL = (
    "https://raw.githubusercontent.com/kubernetes/enhancements/master/keps/"
    "sig-api-machinery/2885-server-side-unknown-field-validation/README.md"
)
PRD_URL = "https://gist.githubusercontent.com/jwiegley/f8a06408f5c605798352074e312113c4/raw/prd.txt"

KEP_SOURCE = "\n".join(
    [
        "## Summary",
        "As a client sending a create, update, or patch request to the server, I want to be able to instruct the server to fail when the kubernetes object I send has fields that are not valid fields of the kubernetes resource.",
        "### Goals",
        "- Server should validate that no extra fields are present or invalid (e.g. misspelled), nor are any fields duplicated (for json and yaml data).",
        "- We must maintain compatibility with all existing clients, thus server side unknown field validation should be opt-in.",
        "- kubectl should default to server-side validation against servers that support it.",
        "- kubectl should provide the ability for a user to request no validation, or warning only validation, instead of strict server-side validation on a per-request basis.",
        "### Non-Goals",
        "- Complete business-logic server-side validation of every aspect of an object.",
        "- Protobuf support.",
        "### Notes/Constraints/Caveats",
        "- Must remain opt-in for existing clients.",
        "- Should preserve compatibility with existing kubectl behavior.",
        "### Acceptance Criteria",
        "- Verify requests with unknown fields fail deterministically.",
        "- Test create, update, and patch validation paths.",
    ]
)

PRD_SOURCE = "\n".join(
    [
        "# Project Requirements Document",
        "## GNU Emacs Codebase Performance Analysis",
        "### Primary Objectives",
        "- Identify all performance bottlenecks in the GNU Emacs C codebase.",
        "- Provide actionable recommendations for performance improvements.",
        "### Secondary Objectives",
        "- Create a performance baseline for future optimization efforts.",
        "- Establish performance metrics and monitoring points.",
        "### In Scope",
        "- Core C codebase analysis.",
        "- Platform-specific code review.",
        "### Out of Scope",
        "- Third-party packages.",
        "- Build system performance.",
        "### Constraints",
        "- Must keep findings deterministic and reproducible.",
        "### Acceptance Criteria",
        "- Verify each issue includes severity, impact, and file references.",
    ]
)

NEGATIVE_SOURCE = "\n".join(
    [
        "# Byte-compiled / optimized / DLL files",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
    ]
)


@dataclass
class FakeTransport:
    responses: dict[str, UrlTransportResponse]

    def open(self, url: str, *, timeout_seconds: int, max_bytes: int) -> UrlTransportResponse:
        return self.responses[url]


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
            {
                "rule_id": "v1.url.gist-prd",
                "allowed_schemes": ["https"],
                "allowed_hosts": ["gist.githubusercontent.com"],
                "allowed_domains": [],
                "allowed_path_prefixes": ["/jwiegley/f8a06408f5c605798352074e312113c4/raw/"],
                "allowed_content_types": ["text/plain"],
                "max_bytes": 524288,
                "redirect_limit": 2,
                "timeout_seconds": 15,
                "priority": 30,
                "evidence_paths": ["url_policy.rules[2]"],
            },
        ],
    }


def _patch_host_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "intent_pipeline.ingestion.url_snapshot_store._resolve_host_addresses",
        lambda _host, _port: ("185.199.111.133",),
    )


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
    return {
        "schema_version": "4.0.0",
        "route_to_tool": [{"route_profile": route_profile, "tool_id": tool_id}],
        "required_capabilities": [{"route_profile": route_profile, "capabilities": ["cap.read", "cap.write"]}],
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


def test_kep_style_positive_source_reaches_phase4_phase5_and_phase6(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_host_resolution(monkeypatch)
    transport = FakeTransport(
        responses={
            KEP_URL: UrlTransportResponse(
                status_code=200,
                headers={"content-type": "text/plain"},
                body=KEP_SOURCE.encode("utf-8"),
            )
        }
    )

    ingestion = ingest_phase1_source(
        KEP_URL,
        extension_mode="CONTROLLED",
        route_profile="IMPLEMENTATION",
        requested_capabilities=("cap.read",),
        extension_policy=_extension_policy_payload(),
        url_policy=_url_policy_payload(),
        snapshot_root=tmp_path / "snapshots",
        url_transport=transport,
    )
    summary = run_phase1_pipeline(
        KEP_URL,
        extension_mode="CONTROLLED",
        route_profile="IMPLEMENTATION",
        requested_capabilities=("cap.read",),
        extension_policy=_extension_policy_payload(),
        url_policy=_url_policy_payload(),
        snapshot_root=tmp_path / "snapshots",
        url_transport=transport,
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
    simulate_result = run_phase6(
        request,
        _build_approval(request, mode=ApprovalMode.SIMULATE_ONLY, key="kep-simulate"),
        registry,
        journal_root=tmp_path / "journal-simulate",
        now=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
    )
    execute_result = run_phase6(
        request,
        _build_approval(request, mode=ApprovalMode.EXECUTE_APPROVED, key="kep-execute"),
        registry,
        journal_root=tmp_path / "journal-execute",
        now=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
    )

    assert summary.startswith("Intent\n- As a client sending a create, update, or patch request")
    assert uplift.intent["primary_objective"] is not None
    assert uplift.intent["secondary_objectives"] == []
    assert routing.route_selection.decision.value == "PASS_ROUTE"
    assert phase4_result.validation.decision.value == "PASS"
    assert phase4_result.validation.can_proceed is True
    assert phase4_result.fallback.decision.value == "USE_PRIMARY"
    assert phase5_result.output.machine_payload.terminal_status.value == "USE_PRIMARY"
    assert simulate_result.decision_code is ExecutionDecisionCode.SIMULATION_COMPLETED
    assert execute_result.decision_code is ExecutionDecisionCode.EXECUTION_COMPLETED


def test_public_prd_primary_objectives_plural_is_accepted_by_suitability_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_host_resolution(monkeypatch)
    transport = FakeTransport(
        responses={
            PRD_URL: UrlTransportResponse(
                status_code=200,
                headers={"content-type": "text/plain"},
                body=PRD_SOURCE.encode("utf-8"),
            )
        }
    )

    ingestion = ingest_phase1_source(
        PRD_URL,
        extension_mode="CONTROLLED",
        route_profile="IMPLEMENTATION",
        requested_capabilities=("cap.read",),
        extension_policy=_extension_policy_payload(),
        url_policy=_url_policy_payload(),
        snapshot_root=tmp_path / "snapshots",
        url_transport=transport,
    )
    summary = run_phase1_pipeline(
        PRD_URL,
        extension_mode="CONTROLLED",
        route_profile="IMPLEMENTATION",
        requested_capabilities=("cap.read",),
        extension_policy=_extension_policy_payload(),
        url_policy=_url_policy_payload(),
        snapshot_root=tmp_path / "snapshots",
        url_transport=transport,
    )

    assert ingestion.source_metadata["normalized_source"] == PRD_URL
    assert ingestion.source_metadata["policy_rule_id"] == "v1.url.gist-prd"
    assert "Identify all performance bottlenecks in the GNU Emacs C codebase." in summary
    assert "Core C codebase analysis." in summary
    assert "Third-party packages. Build system performance." in summary


def test_negative_real_source_shape_still_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_host_resolution(monkeypatch)
    transport = FakeTransport(
        responses={
            NEGATIVE_URL: UrlTransportResponse(
                status_code=200,
                headers={"content-type": "text/plain"},
                body=NEGATIVE_SOURCE.encode("utf-8"),
            )
        }
    )

    with pytest.raises(UrlSourceRejectedError) as exc_info:
        ingest_phase1_source(
            NEGATIVE_URL,
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=_extension_policy_payload(),
            url_policy=_url_policy_payload(),
            snapshot_root=tmp_path / "snapshots",
            url_transport=transport,
        )

    assert exc_info.value.rejection.code.value == "URL-INGEST-013-UNSUITABLE-CONTENT"
    assert exc_info.value.rejection.terminal_status == "REJECTED"
