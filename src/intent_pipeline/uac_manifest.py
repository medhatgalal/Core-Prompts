"""Capability Fabric manifest, install-target inference, and orchestrator handoff helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping, Sequence
from urllib.parse import urlsplit

GENERIC_TAGS = {"analysis", "planning", "context", "prompting", "review", "packaging", "import", "routing", "debugging"}
GENERIC_ROLES = {"workflow", "advisor", "analyst", "specialist", "specialist_workflow"}


ROLE_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    (
        "advisor",
        (
            re.compile(r"\bmentor\b", re.IGNORECASE),
            re.compile(r"\bcoach\b", re.IGNORECASE),
            re.compile(r"\bguidance\b", re.IGNORECASE),
        ),
    ),
    (
        "analyst",
        (
            re.compile(r"\banaly[sz]e\b", re.IGNORECASE),
            re.compile(r"\baudit\b", re.IGNORECASE),
            re.compile(r"\breview\b", re.IGNORECASE),
            re.compile(r"\bdiagnos", re.IGNORECASE),
        ),
    ),
    (
        "importer",
        (
            re.compile(r"\bimport\b", re.IGNORECASE),
            re.compile(r"\bpackage\b", re.IGNORECASE),
            re.compile(r"\bclassif", re.IGNORECASE),
            re.compile(r"\buac\b", re.IGNORECASE),
        ),
    ),
    (
        "architect",
        (
            re.compile(r"\barchitect", re.IGNORECASE),
            re.compile(r"\bsystem design\b", re.IGNORECASE),
            re.compile(r"\bblack box\b", re.IGNORECASE),
        ),
    ),
    (
        "resolver",
        (
            re.compile(r"\bresolve\b", re.IGNORECASE),
            re.compile(r"\bconflict\b", re.IGNORECASE),
            re.compile(r"\bmerge\b", re.IGNORECASE),
        ),
    ),
)

TAG_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    ("architecture", (re.compile(r"\barchitect", re.IGNORECASE), re.compile(r"\bsystem design\b", re.IGNORECASE))),
    ("review", (re.compile(r"\breview\b", re.IGNORECASE), re.compile(r"\baudit\b", re.IGNORECASE))),
    ("analysis", (re.compile(r"\banaly[sz]e\b", re.IGNORECASE), re.compile(r"\bdiagnos", re.IGNORECASE))),
    ("routing", (re.compile(r"\broute\b", re.IGNORECASE), re.compile(r"\bdispatch\b", re.IGNORECASE))),
    ("packaging", (re.compile(r"\bpackage\b", re.IGNORECASE), re.compile(r"\bsurface\b", re.IGNORECASE))),
    ("import", (re.compile(r"\bimport\b", re.IGNORECASE), re.compile(r"\bingest\b", re.IGNORECASE))),
    ("planning", (re.compile(r"\bplan\b", re.IGNORECASE), re.compile(r"\broadmap\b", re.IGNORECASE))),
    ("debugging", (re.compile(r"\bdebug\b", re.IGNORECASE), re.compile(r"\bfailure\b", re.IGNORECASE))),
    ("context", (re.compile(r"\bcontext\b", re.IGNORECASE), re.compile(r"\bmemory\b", re.IGNORECASE))),
    ("prompting", (re.compile(r"\bprompt\b", re.IGNORECASE), re.compile(r"\bworkflow\b", re.IGNORECASE))),
)


@dataclass(frozen=True, slots=True)
class UacCrossAnalysis:
    duplicate_risk: str
    overlap_report: tuple[dict[str, object], ...]
    conflict_report: tuple[str, ...]
    fit_assessment: str
    required_existing_adjustments: tuple[str, ...]
    required_new_entry_adjustments: tuple[str, ...]
    work_graph_change_summary: str

    def as_payload(self) -> dict[str, object]:
        return {
            "duplicate_risk": self.duplicate_risk,
            "overlap_report": list(self.overlap_report),
            "conflict_report": list(self.conflict_report),
            "fit_assessment": self.fit_assessment,
            "required_existing_adjustments": list(self.required_existing_adjustments),
            "required_new_entry_adjustments": list(self.required_new_entry_adjustments),
            "work_graph_change_summary": self.work_graph_change_summary,
        }


def infer_install_target(
    normalized_source: str,
    *,
    source_type: str,
    repo_root: Path,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    recommended = "global"
    rationale = "Remote or external sources default to global library installation until a repo-local need is confirmed."
    confidence = 0.66
    if source_type == "LOCAL_FILE":
        path = Path(normalized_source).expanduser()
        if not path.is_absolute():
            path = repo_root / path
        path = path.resolve()
        try:
            path.relative_to(repo_root)
            recommended = "repo_local"
            rationale = "Source lives inside the current repository, so repo-local installation is the safer default."
            confidence = 0.88
        except ValueError:
            recommended = "global"
            rationale = "Local source lives outside the current repository, so global library installation is the safer default."
            confidence = 0.78
    elif source_type == "GITHUB_TREE":
        recommended = "global"
        rationale = "GitHub folder imports are treated as external capability candidates and default to the global library."
        confidence = 0.74
    elif source_type == "URL":
        parsed = urlsplit(normalized_source)
        if parsed.netloc == "github.com":
            recommended = "global"
            rationale = "GitHub-hosted prompt sources default to the global library unless explicitly landing inside a repo."
            confidence = 0.74
    return {
        "recommended": recommended,
        "confidence": round(confidence, 2),
        "confirmation_required_for_apply": True,
        "rationale": rationale,
        "supported": ["global", "repo_local", "both"],
    }


def normalize_persisted_source_reference(
    normalized_source: str,
    *,
    source_type: str,
    repo_root: Path,
) -> str:
    repo_root = repo_root.resolve()
    if source_type != "LOCAL_FILE":
        return normalized_source

    path = Path(normalized_source).expanduser()
    if not path.is_absolute():
        return str(path.as_posix())

    try:
        relative = path.resolve().relative_to(repo_root)
    except ValueError:
        return str(path.resolve())
    return relative.as_posix()


def derive_role(raw_text: str, capability_type: str, slug: str) -> str:
    for role, patterns in ROLE_PATTERNS:
        if any(pattern.search(raw_text) for pattern in patterns):
            return role
    if capability_type == "agent":
        return "specialist"
    if capability_type == "both":
        return "specialist_workflow"
    if slug == "uac-import":
        return "importer"
    return "workflow"


def derive_domain_tags(raw_text: str, slug: str) -> tuple[str, ...]:
    tags: list[str] = []
    lowered_slug = slug.replace("_", "-")
    for tag, patterns in TAG_PATTERNS:
        if any(pattern.search(raw_text) for pattern in patterns):
            tags.append(tag)
    for part in lowered_slug.split("-"):
        if len(part) >= 4 and part not in {"skill", "agent", "manual", "review", "both"}:
            tags.append(part)
    ordered = tuple(dict.fromkeys(tags))
    return ordered[:8]


def _manifest_signal_text(
    *,
    slug: str,
    summary: str,
    primary_objective: object,
    in_scope: Sequence[object],
) -> str:
    parts: list[str] = []
    if summary.strip():
        parts.append(summary.strip())
    if primary_objective:
        objective = str(primary_objective).strip()
        if objective:
            parts.append(objective)
    for item in in_scope[:4]:
        text = str(item).strip()
        if text:
            parts.append(text)
    slug_text = " ".join(part for part in slug.replace("_", "-").split("-") if part)
    if slug_text:
        parts.append(slug_text)
    return "\n".join(parts)


def packaging_profile(capability_type: str, emitted_surfaces: Mapping[str, Sequence[str]]) -> dict[str, object]:
    wrappers = {
        "codex": ["plugin_wrapper"] if any(name.endswith("_agent") for name in emitted_surfaces.get("codex", ())) else [],
        "gemini": ["skill_wrapper"],
        "claude": ["skill_wrapper", "plugin_wrapper"],
        "kiro": ["skill_wrapper", "power_wrapper"],
    }
    return {
        "capability_type": capability_type,
        "primary_surfaces": {cli: list(values) for cli, values in emitted_surfaces.items() if values},
        "wrapper_surfaces": wrappers,
        "notes": [
            "wrapper surfaces are additive deployment forms, not capability types",
            "orchestrators must not infer execution authority from wrapper presence alone",
        ],
    }


def build_capability_manifest(
    *,
    slug: str,
    source_metadata: Mapping[str, object],
    raw_text: str,
    summary: str,
    assessment_payload: Mapping[str, object],
    uplift_payload: Mapping[str, object],
    routing_payload: Mapping[str, object],
    repo_root: Path,
) -> dict[str, object]:
    capability_type = str(assessment_payload["capability_type"])
    emitted_surfaces = {
        cli: tuple(values)
        for cli, values in (assessment_payload.get("emitted_surfaces") or {}).items()
        if isinstance(values, Sequence)
    }
    source_type = str(source_metadata.get("source_type") or "unknown")
    normalized_source = str(source_metadata.get("normalized_source") or "unknown")
    persisted_source = normalize_persisted_source_reference(
        normalized_source,
        source_type=source_type,
        repo_root=repo_root,
    )
    install_target = infer_install_target(persisted_source, source_type=source_type, repo_root=repo_root)
    primary_objective = uplift_payload.get("primary_objective")
    in_scope = tuple(uplift_payload.get("in_scope") or [])
    quality_constraints = tuple(uplift_payload.get("quality_constraints") or [])
    route_profile = routing_payload.get("route_profile")
    signal_text = _manifest_signal_text(
        slug=slug,
        summary=summary,
        primary_objective=primary_objective,
        in_scope=in_scope,
    )
    role = derive_role(signal_text, capability_type, slug)
    tags = derive_domain_tags(signal_text, slug)

    minimal = {
        "capability_type": capability_type,
        "summary": summary.strip(),
        "role": role,
        "domain_tags": list(tags),
        "required_inputs": ["source text", "user intent/context"],
        "expected_outputs": [
            "deterministic summary",
            "uplift payload",
            "capability recommendation",
            "deployment guidance",
        ],
        "tool_policy": {
            "allowed": ["deterministic classification", "metadata publication", "surface generation"],
            "forbidden": ["orchestration", "delegation decisions", "runtime execution control"],
        },
        "resources": [persisted_source],
        "packaging_profile": packaging_profile(capability_type, emitted_surfaces),
        "install_target": install_target,
        "emitted_surfaces": {cli: list(values) for cli, values in emitted_surfaces.items()},
        "source_provenance": {
            "source_type": source_type,
            "normalized_source": persisted_source,
            "policy_rule_id": source_metadata.get("policy_rule_id"),
            "content_sha256": source_metadata.get("content_sha256"),
        },
        "confidence": assessment_payload.get("confidence"),
        "rationale": assessment_payload.get("rationale"),
        "review_status": "manual_review" if capability_type == "manual_review" else "ready_for_orchestrator_review",
    }
    expanded = {
        "relationship_suggestions": _relationship_suggestions(role, capability_type, tags),
        "capability_dependencies": _capability_dependencies(tags),
        "overlap_candidates": [],
        "migration_notes": [
            "If the capability lands, compare it against existing entries before apply.",
            "Relationship suggestions are advisory only and do not imply runtime routing.",
        ],
        "adjustment_recommendations": _adjustment_recommendations(primary_objective, in_scope, quality_constraints),
    }
    org_graph = {
        "org_role": _org_role(role, capability_type),
        "reports_to_suggestions": [],
        "delegates_to_suggestions": [],
        "collaborates_with_suggestions": list(tags[:2]),
        "authority_tier": "advisory",
        "work_graph_impact": f"Adds or updates a {capability_type} capability with route profile {route_profile}.",
    }
    return {
        "slug": slug,
        "manifest_version": "capability-fabric.v0",
        "layers": {
            "minimal": minimal,
            "expanded": expanded,
            "org_graph": org_graph,
        },
    }


def analyze_manifest_fit(candidate_manifest: Mapping[str, object], existing_manifests: Sequence[Mapping[str, object]]) -> UacCrossAnalysis:
    candidate_min = candidate_manifest.get("layers", {}).get("minimal", {})
    candidate_slug = str(candidate_manifest.get("slug") or "unknown")
    candidate_type = str(candidate_min.get("capability_type") or "manual_review")
    candidate_role = str(candidate_min.get("role") or "workflow")
    candidate_tags = set(candidate_min.get("domain_tags") or [])

    overlaps: list[dict[str, object]] = []
    conflicts: list[str] = []
    existing_adjustments: list[str] = []
    new_adjustments: list[str] = []
    duplicate_risk = "low"

    for manifest in existing_manifests:
        slug = str(manifest.get("slug") or "unknown")
        if slug == candidate_slug:
            overlaps.append({"slug": slug, "score": 1.0, "reason": "same slug"})
            duplicate_risk = "high"
            conflicts.append(f"slug {candidate_slug} already exists")
            continue
        minimal = manifest.get("layers", {}).get("minimal", {})
        existing_type = str(minimal.get("capability_type") or "manual_review")
        existing_role = str(minimal.get("role") or "workflow")
        existing_tags = set(minimal.get("domain_tags") or [])
        candidate_specific = {tag for tag in candidate_tags if tag not in GENERIC_TAGS}
        existing_specific = {tag for tag in existing_tags if tag not in GENERIC_TAGS}
        tag_basis_left = candidate_specific or candidate_tags
        tag_basis_right = existing_specific or existing_tags
        union = tag_basis_left | tag_basis_right
        overlap_score = 0.0 if not union else len(tag_basis_left & tag_basis_right) / len(union)
        role_only_signal = candidate_role == existing_role and candidate_role not in GENERIC_ROLES
        if overlap_score >= 0.34 or role_only_signal:
            reason_bits = []
            if overlap_score:
                reason_bits.append(f"tag overlap {overlap_score:.2f}")
            if candidate_role == existing_role and (overlap_score or role_only_signal):
                reason_bits.append(f"shared role {candidate_role}")
            overlaps.append({"slug": slug, "score": round(overlap_score, 2), "reason": ", ".join(reason_bits) or "role overlap"})
        if overlap_score >= 0.7 and candidate_type == existing_type:
            duplicate_risk = "high"
            conflicts.append(f"{candidate_slug} substantially overlaps {slug}")
        elif overlap_score >= 0.45:
            duplicate_risk = "medium" if duplicate_risk == "low" else duplicate_risk
            existing_adjustments.append(f"review {slug} for tag/role normalization against {candidate_slug}")
            new_adjustments.append(f"tighten scope for {candidate_slug} relative to {slug}")
        if candidate_role == existing_role and candidate_type != existing_type and candidate_role not in GENERIC_ROLES and overlap_score >= 0.45:
            existing_adjustments.append(f"review role boundary between {candidate_slug} and {slug}")
            new_adjustments.append(f"clarify whether {candidate_slug} should stay {candidate_type} or align more tightly with {slug}")

    fit = "fits_cleanly"
    if duplicate_risk == "high" or conflicts:
        fit = "manual_review"
    elif overlaps:
        fit = "requires_adjustment"

    if fit == "fits_cleanly":
        summary = f"{candidate_slug} fits the current capability graph without required adjustments."
    elif fit == "requires_adjustment":
        summary = f"{candidate_slug} fits, but existing and new manifests need coordinated metadata adjustments."
    else:
        summary = f"{candidate_slug} risks duplicate or conflicting graph roles and should not auto-apply."

    return UacCrossAnalysis(
        duplicate_risk=duplicate_risk,
        overlap_report=tuple(sorted(overlaps, key=lambda item: (-float(item["score"]), str(item["slug"])))),
        conflict_report=tuple(dict.fromkeys(conflicts)),
        fit_assessment=fit,
        required_existing_adjustments=tuple(dict.fromkeys(existing_adjustments)),
        required_new_entry_adjustments=tuple(dict.fromkeys(new_adjustments)),
        work_graph_change_summary=summary,
    )


def orchestrator_handoff_payload(manifests: Sequence[Mapping[str, object]]) -> dict[str, object]:
    capabilities: list[dict[str, object]] = []
    for manifest in manifests:
        minimal = manifest.get("layers", {}).get("minimal", {})
        expanded = manifest.get("layers", {}).get("expanded", {})
        org_graph = manifest.get("layers", {}).get("org_graph", {})
        capabilities.append(
            {
                "slug": manifest.get("slug"),
                "display_name": manifest.get("display_name") or minimal.get("display_name"),
                "capability_type": minimal.get("capability_type"),
                "summary": minimal.get("summary"),
                "role": minimal.get("role"),
                "domain_tags": list(minimal.get("domain_tags") or []),
                "required_inputs": list(minimal.get("required_inputs") or []),
                "expected_outputs": list(minimal.get("expected_outputs") or []),
                "tool_policy": minimal.get("tool_policy"),
                "install_target": minimal.get("install_target"),
                "emitted_surfaces": minimal.get("emitted_surfaces"),
                "confidence": minimal.get("confidence"),
                "review_status": minimal.get("review_status"),
                "overlap_candidates": list(expanded.get("overlap_candidates") or []),
                "relationship_suggestions": list(expanded.get("relationship_suggestions") or []),
                "quality_status": manifest.get("quality_status"),
                "benchmark_profile": manifest.get("quality_profile"),
                "preferred_use_cases": list((manifest.get("consumption_hints") or {}).get("preferred_use_cases") or []),
                "artifact_conventions": list((manifest.get("consumption_hints") or {}).get("artifact_conventions") or []),
                "invocation_style": (manifest.get("consumption_hints") or {}).get("invocation_style"),
                "requires_human_confirmation": (manifest.get("consumption_hints") or {}).get("requires_human_confirmation"),
                "org_graph": org_graph,
                "advisory_only": True,
            }
        )
    return {
        "schema_version": "capability-fabric.handoff.v0",
        "advisory_only": True,
        "notes": [
            "Capability Fabric publishes metadata and suggestions only.",
            "Orchestrators remain responsible for delegation and runtime routing.",
        ],
        "capabilities": capabilities,
    }


def _relationship_suggestions(role: str, capability_type: str, tags: tuple[str, ...]) -> list[str]:
    suggestions: list[str] = []
    if capability_type in {"agent", "both"}:
        suggestions.append("prefer explicit review or analyst companions before high-authority use")
    if "architecture" in tags:
        suggestions.append("pair with review and analysis capabilities when converging design proposals")
    if role == "importer":
        suggestions.append("pair with convergence capability for multi-source synthesis")
    return suggestions


def _capability_dependencies(tags: tuple[str, ...]) -> list[str]:
    dependencies: list[str] = []
    if "architecture" in tags:
        dependencies.append("analysis")
    if "review" in tags:
        dependencies.append("context")
    if "import" in tags:
        dependencies.append("packaging")
    return dependencies


def _adjustment_recommendations(primary_objective: object, in_scope: Sequence[object], quality_constraints: Sequence[object]) -> list[str]:
    adjustments: list[str] = []
    if not primary_objective:
        adjustments.append("add an explicit primary objective before packaging")
    if not in_scope:
        adjustments.append("add deterministic in-scope sections to improve routing fitness")
    if not quality_constraints:
        adjustments.append("capture quality constraints or non-negotiables")
    return adjustments


def _org_role(role: str, capability_type: str) -> str:
    if capability_type == "agent":
        return "specialist"
    if capability_type == "both":
        return "specialist_with_workflow_surface"
    if role in {"advisor", "analyst", "architect", "importer", "resolver"}:
        return role
    return "workflow_provider"


__all__ = [
    "UacCrossAnalysis",
    "analyze_manifest_fit",
    "build_capability_manifest",
    "derive_domain_tags",
    "derive_role",
    "infer_install_target",
    "normalize_persisted_source_reference",
    "orchestrator_handoff_payload",
    "packaging_profile",
]
