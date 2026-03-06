"""Terminal phase-1 pipeline: local ingestion -> two-pass sanitization -> summary."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from intent_pipeline.extensions.contracts import ExtensionPolicyContract
from intent_pipeline.extensions.gates import (
    ExtensionGateDecision,
    ExtensionGateOutcome,
    evaluate_extension_gate,
)
from intent_pipeline.ingestion.reader import read_local_file_text
from intent_pipeline.sanitization.pipeline import sanitize_two_pass
from intent_pipeline.summary.renderer import render_intent_summary


class ExtensionGateBlockedError(RuntimeError):
    """Raised when shared extension boundary gates reject a request."""

    def __init__(self, decision: ExtensionGateDecision) -> None:
        super().__init__(f"{decision.reason_code.value}: extension request blocked at boundary")
        self.decision = decision


class ExtensionBoundaryNotEnabledError(RuntimeError):
    """Raised when extension paths are policy-admitted but still out of phase scope."""


def run_phase1_pipeline(
    source: str | Path,
    *,
    extension_mode: str = "DISABLED",
    route_profile: str = "IMPLEMENTATION",
    requested_capabilities: Sequence[str] = (),
    extension_policy: ExtensionPolicyContract | Mapping[str, Any] | None = None,
) -> str:
    """Return deterministic intent summary and terminate the phase-1 pipeline."""
    if _is_extension_mode_requested(extension_mode):
        gate_result = evaluate_extension_gate(
            extension_mode=extension_mode,
            route_profile=route_profile,
            requested_capabilities=requested_capabilities,
            policy_contract=extension_policy,
        )
        if gate_result.outcome is not ExtensionGateOutcome.ALLOW:
            raise ExtensionGateBlockedError(gate_result)
        raise ExtensionBoundaryNotEnabledError(
            "EXT-GATE-011-EXTENSION-PATH-NOT-ENABLED: extension behavior remains out of scope in Phase 8"
        )

    raw_text = read_local_file_text(source)
    sanitized_text = sanitize_two_pass(raw_text)
    return render_intent_summary(sanitized_text)


def _is_extension_mode_requested(extension_mode: str) -> bool:
    normalized_mode = " ".join(str(extension_mode).split()).strip().upper()
    return normalized_mode != "DISABLED"


__all__ = [
    "ExtensionBoundaryNotEnabledError",
    "ExtensionGateBlockedError",
    "run_phase1_pipeline",
]
