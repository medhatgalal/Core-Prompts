"""Canonical UAC capability model, deployment matrix, and audit helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

CapabilityType = str
AuditStatus = str

_CAPABILITY_MATRIX: dict[str, dict[str, tuple[str, ...]]] = {
    "skill": {
        "codex": ("codex_skill",),
        "gemini": ("gemini_command", "gemini_skill"),
        "claude": ("claude_command",),
        "kiro": ("kiro_prompt", "kiro_skill"),
    },
    "agent": {
        "codex": ("codex_agent",),
        "gemini": ("gemini_agent",),
        "claude": ("claude_agent",),
        "kiro": ("kiro_agent",),
    },
    "both": {
        "codex": ("codex_skill", "codex_agent"),
        "gemini": ("gemini_command", "gemini_skill", "gemini_agent"),
        "claude": ("claude_command", "claude_agent"),
        "kiro": ("kiro_prompt", "kiro_skill", "kiro_agent"),
    },
    "manual_review": {
        "codex": (),
        "gemini": (),
        "claude": (),
        "kiro": (),
    },
}

_PRIMARY_SURFACE: dict[str, str] = {
    "skill": "skill",
    "agent": "agent",
    "both": "both",
    "manual_review": "manual_review",
}

_DECLARED_TO_CAPABILITY: dict[str, str] = {
    "skill": "skill",
    "workflow": "skill",
    "prompt": "skill",
    "agent": "agent",
    "subagent": "agent",
    "sub-agent": "agent",
    "both": "both",
}


@dataclass(frozen=True, slots=True)
class UacAuditResult:
    status: AuditStatus
    issues: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        return {"status": self.status, "issues": list(self.issues)}


def normalize_declared_capability(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return _DECLARED_TO_CAPABILITY.get(normalized)


def deployment_matrix_payload() -> dict[str, object]:
    return {
        "capability_types": {
            "skill": {
                "meaning": "Reusable prompt/workflow/procedure with explicit task guidance, structure, outputs, and bounded use.",
                "surfaces": {cli: list(surfaces) for cli, surfaces in _CAPABILITY_MATRIX["skill"].items()},
            },
            "agent": {
                "meaning": "Delegated specialist with tool/process autonomy, separate operating identity, or explicit agent/subagent semantics.",
                "surfaces": {cli: list(surfaces) for cli, surfaces in _CAPABILITY_MATRIX["agent"].items()},
            },
            "both": {
                "meaning": "One SSOT entry that should emit both workflow/skill surfaces and agent surfaces.",
                "surfaces": {cli: list(surfaces) for cli, surfaces in _CAPABILITY_MATRIX["both"].items()},
            },
            "manual_review": {
                "meaning": "Conflicting, low-structure, or mixed wrapper content that should not deploy automatically.",
                "surfaces": {cli: list(surfaces) for cli, surfaces in _CAPABILITY_MATRIX["manual_review"].items()},
            },
        },
        "notes": [
            "command is an invocation surface, not a peer capability type",
            "both means one SSOT source can emit multiple surfaces without duplicating SSOT entries",
            "manual_review emits no deployable surfaces until reviewed",
        ],
    }


def emitted_surfaces_by_cli(capability_type: CapabilityType) -> dict[str, tuple[str, ...]]:
    if capability_type not in _CAPABILITY_MATRIX:
        raise ValueError(f"Unsupported capability_type: {capability_type}")
    return _CAPABILITY_MATRIX[capability_type]


def emitted_surface_names(capability_type: CapabilityType) -> tuple[str, ...]:
    matrix = emitted_surfaces_by_cli(capability_type)
    flattened: list[str] = []
    for surfaces in matrix.values():
        flattened.extend(surfaces)
    return tuple(flattened)


def primary_surface(capability_type: CapabilityType) -> str:
    return _PRIMARY_SURFACE[capability_type]


def deployment_intent(capability_type: CapabilityType, confidence: float) -> str:
    if capability_type == "manual_review":
        return "hold_for_review"
    if confidence >= 0.8:
        return "generate"
    return "generate_with_review"


def capability_conflicts(declared_capability: str | None, inferred_capability: str) -> bool:
    if declared_capability is None:
        return False
    if declared_capability == inferred_capability:
        return False
    # both is intentionally explicit; if declared is narrower than inferred both, surface as mismatch.
    return True


def audit_surface_alignment(
    *,
    declared_capability: str | None,
    inferred_capability: str,
    expected_surfaces: set[str],
    actual_surfaces: set[str],
) -> UacAuditResult:
    issues: list[str] = []
    if inferred_capability == "manual_review":
        return UacAuditResult(status="manual_review", issues=("UAC classified this entry as manual_review",))

    if capability_conflicts(declared_capability, inferred_capability):
        issues.append(
            f"declared capability {declared_capability or 'unset'} does not match inferred capability {inferred_capability}"
        )
        return UacAuditResult(status="frontmatter_mismatch", issues=tuple(issues))

    missing = expected_surfaces - actual_surfaces
    extra = actual_surfaces - expected_surfaces
    if extra:
        issues.append("unexpected generated surfaces: " + ", ".join(sorted(extra)))
        return UacAuditResult(status="over-generated", issues=tuple(issues))

    missing_agent = {name for name in missing if name.endswith("_agent")}
    missing_skill = missing - missing_agent
    if missing_agent and not missing_skill:
        issues.append("missing agent surfaces: " + ", ".join(sorted(missing_agent)))
        return UacAuditResult(status="missing_agent_surface", issues=tuple(issues))
    if missing_skill and not missing_agent:
        issues.append("missing skill/workflow surfaces: " + ", ".join(sorted(missing_skill)))
        return UacAuditResult(status="missing_skill_surface", issues=tuple(issues))
    if missing:
        issues.append("missing mixed surfaces: " + ", ".join(sorted(missing)))
        return UacAuditResult(status="manual_review", issues=tuple(issues))
    return UacAuditResult(status="aligned", issues=())


def recommended_target_systems(target_system: str, capability_type: str) -> list[str]:
    if target_system == "all":
        return ["codex", "gemini", "claude", "kiro"]
    if target_system == "auto":
        return [cli for cli, names in emitted_surfaces_by_cli(capability_type).items() if names]
    return [target_system]


def summarized_emitted_surfaces(capability_type: str) -> dict[str, list[str]]:
    return {cli: list(surfaces) for cli, surfaces in emitted_surfaces_by_cli(capability_type).items() if surfaces}


__all__ = [
    "UacAuditResult",
    "audit_surface_alignment",
    "deployment_intent",
    "deployment_matrix_payload",
    "emitted_surface_names",
    "emitted_surfaces_by_cli",
    "normalize_declared_capability",
    "primary_surface",
    "recommended_target_systems",
    "summarized_emitted_surfaces",
]
