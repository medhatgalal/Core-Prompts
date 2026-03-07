"""Terminal phase-1 pipeline: local ingestion -> two-pass sanitization -> summary."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from intent_pipeline.extensions.contracts import ExtensionPolicyContract
from intent_pipeline.extensions.gates import (
    ExtensionGateDecision,
    ExtensionGateOutcome,
    ExtensionGateReasonCode,
    evaluate_extension_gate,
)
from intent_pipeline.ingestion.reader import read_local_file_text, read_snapshot_text
from intent_pipeline.ingestion.source_resolver import ResolvedSourceKind, resolve_source
from intent_pipeline.ingestion.url_policy import (
    UrlPolicyContract,
    UrlSourceRejectedError,
    reject_unsuitable_content,
)
from intent_pipeline.ingestion.url_snapshot_store import UrlSnapshotStore
from intent_pipeline.intent_structure import extract_intent_structure
from intent_pipeline.sanitization.pipeline import sanitize_two_pass
from intent_pipeline.summary.renderer import render_intent_summary


class ExtensionGateBlockedError(RuntimeError):
    """Raised when shared extension boundary gates reject a request."""

    def __init__(self, decision: ExtensionGateDecision) -> None:
        super().__init__(f"{decision.reason_code.value}: extension request blocked at boundary")
        self.decision = decision


class ExtensionBoundaryNotEnabledError(RuntimeError):
    """Raised when extension paths are policy-admitted but still out of phase scope."""


@dataclass(frozen=True, slots=True)
class Phase1IngestionResult:
    raw_text: str
    source_metadata: dict[str, str]


def run_phase1_pipeline(
    source: str | Path,
    *,
    extension_mode: str = "DISABLED",
    route_profile: str = "IMPLEMENTATION",
    requested_capabilities: Sequence[str] = (),
    extension_policy: ExtensionPolicyContract | Mapping[str, Any] | None = None,
    url_policy: UrlPolicyContract | Mapping[str, Any] | None = None,
    snapshot_root: Path | None = None,
    url_transport: object | None = None,
) -> str:
    """Return deterministic intent summary and terminate the phase-1 pipeline."""
    ingestion = ingest_phase1_source(
        source,
        extension_mode=extension_mode,
        route_profile=route_profile,
        requested_capabilities=requested_capabilities,
        extension_policy=extension_policy,
        url_policy=url_policy,
        snapshot_root=snapshot_root,
        url_transport=url_transport,
    )
    sanitized_text = sanitize_two_pass(ingestion.raw_text)
    return render_intent_summary(sanitized_text)


def ingest_phase1_source(
    source: str | Path,
    *,
    extension_mode: str = "DISABLED",
    route_profile: str = "IMPLEMENTATION",
    requested_capabilities: Sequence[str] = (),
    extension_policy: ExtensionPolicyContract | Mapping[str, Any] | None = None,
    url_policy: UrlPolicyContract | Mapping[str, Any] | None = None,
    snapshot_root: Path | None = None,
    url_transport: object | None = None,
) -> Phase1IngestionResult:
    """Resolve local or URL sources into deterministic text plus provenance metadata."""
    resolved = resolve_source(source)
    if resolved.kind is ResolvedSourceKind.LOCAL_FILE:
        decision = _prevalidate_extension_request(
            extension_mode=extension_mode,
            route_profile=route_profile,
            requested_capabilities=requested_capabilities,
        )
        if decision is not None:
            raise ExtensionGateBlockedError(decision)
        raw_text = read_local_file_text(source)
        return Phase1IngestionResult(
            raw_text=raw_text,
            source_metadata=_build_source_metadata(
                source_type=ResolvedSourceKind.LOCAL_FILE.value,
                normalized_source=resolved.normalized_source,
                policy_rule_id="v1.local.baseline.allow",
                content_sha256=sha256(raw_text.encode("utf-8")).hexdigest(),
                content_type="text/plain",
            ),
        )

    if not _is_extension_mode_requested(extension_mode):
        raise ExtensionGateBlockedError(
            ExtensionGateDecision(
                schema_version="1.0.0",
                outcome=ExtensionGateOutcome.BLOCK,
                reason_code=ExtensionGateReasonCode.EXTENSIONS_DISABLED,
                extension_mode="DISABLED",
                route_profile=str(route_profile).strip().upper() or "UNKNOWN",
                policy_schema_version="disabled",
                matched_rule_ids=(),
                requested_capabilities=_requested_capabilities_for_url(requested_capabilities),
                evidence_paths=("pipeline.extension_mode",),
            )
        )

    gate_result = evaluate_extension_gate(
        extension_mode=extension_mode,
        route_profile=route_profile,
        requested_capabilities=_requested_capabilities_for_url(requested_capabilities),
        policy_contract=extension_policy,
    )
    if gate_result.outcome is not ExtensionGateOutcome.ALLOW:
        raise ExtensionGateBlockedError(gate_result)

    snapshot = UrlSnapshotStore(snapshot_root, transport=url_transport).materialize(
        resolved,
        url_policy,
    )
    raw_text = read_snapshot_text(snapshot)
    _enforce_url_source_suitability(
        raw_text,
        normalized_source=resolved.normalized_source,
        policy_rule_id=snapshot.policy_rule_id,
    )
    return Phase1IngestionResult(raw_text=raw_text, source_metadata=snapshot.as_source_metadata())


def _enforce_url_source_suitability(
    raw_text: str,
    *,
    normalized_source: str,
    policy_rule_id: str,
) -> None:
    sanitized_text = sanitize_two_pass(raw_text)
    structure = extract_intent_structure(sanitized_text)
    semantic_categories = structure.semantic_category_count
    if structure.objective and semantic_categories >= 2:
        return

    resolved = resolve_source(normalized_source)
    raise UrlSourceRejectedError(
        reject_unsuitable_content(
            resolved,
            (
                "Source is not intent-bearing: require at least one objective signal "
                "and at least two semantic categories overall "
                f"(objective={len(structure.objective)}, in_scope={len(structure.in_scope)}, "
                f"out_of_scope={len(structure.out_of_scope)}, constraints={len(structure.constraints)}, "
                f"acceptance={len(structure.acceptance)})."
            ),
            matched_rule_id=policy_rule_id,
            evidence_paths=(
                "source_suitability.objective",
                "source_suitability.in_scope",
                "source_suitability.out_of_scope",
                "source_suitability.constraints",
                "source_suitability.acceptance",
            ),
        )
    )


def _is_extension_mode_requested(extension_mode: str) -> bool:
    normalized_mode = " ".join(str(extension_mode).split()).strip().upper()
    return normalized_mode != "DISABLED"


def _requested_capabilities_for_url(requested_capabilities: Sequence[str]) -> tuple[str, ...]:
    normalized = {str(capability).strip() for capability in requested_capabilities if str(capability).strip()}
    normalized.add("cap.fetch")
    return tuple(sorted(normalized))


def _prevalidate_extension_request(
    *,
    extension_mode: str,
    route_profile: str,
    requested_capabilities: Sequence[str],
) -> ExtensionGateDecision | None:
    normalized_mode = " ".join(str(extension_mode).split()).strip().upper()
    if normalized_mode == "DISABLED":
        return None

    normalized_profile = " ".join(str(route_profile).split()).strip().upper() or "UNKNOWN"
    normalized_capabilities = tuple(
        sorted({str(capability).strip() for capability in requested_capabilities if str(capability).strip()})
    )
    known_modes = {"DISABLED", "CONTROLLED"}
    known_profiles = {"IMPLEMENTATION", "RESEARCH", "VALIDATION", "NEEDS_REVIEW"}
    known_capabilities = {"cap.read", "cap.fetch", "cap.write", "cap.execute"}

    if normalized_mode not in known_modes:
        return ExtensionGateDecision(
            schema_version="1.0.0",
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.UNKNOWN_MODE,
            extension_mode=normalized_mode or "UNKNOWN",
            route_profile=normalized_profile,
            policy_schema_version="unknown",
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=("pipeline.extension_mode",),
        )
    if normalized_profile not in known_profiles:
        return ExtensionGateDecision(
            schema_version="1.0.0",
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.UNKNOWN_ROUTE_PROFILE,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version="unknown",
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=("pipeline.route_profile",),
        )
    unknown_capabilities = tuple(
        capability for capability in normalized_capabilities if capability not in known_capabilities
    )
    if unknown_capabilities:
        return ExtensionGateDecision(
            schema_version="1.0.0",
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.UNKNOWN_CAPABILITY,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version="unknown",
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=(
                "pipeline.requested_capabilities",
                f"pipeline.requested_capabilities::{unknown_capabilities[0]}",
            ),
        )
    return None


def _build_source_metadata(
    *,
    source_type: str,
    normalized_source: str,
    policy_rule_id: str,
    content_sha256: str,
    content_type: str,
) -> dict[str, str]:
    return {
        "source_type": source_type,
        "normalized_source": normalized_source,
        "policy_rule_id": policy_rule_id,
        "content_sha256": content_sha256,
        "content_type": content_type,
    }


__all__ = [
    "ExtensionBoundaryNotEnabledError",
    "ExtensionGateBlockedError",
    "Phase1IngestionResult",
    "UrlSourceRejectedError",
    "ingest_phase1_source",
    "run_phase1_pipeline",
]
