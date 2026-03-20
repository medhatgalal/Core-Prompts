"""Deterministic UAC source assessment and packaging recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping

from intent_pipeline.intent_structure import extract_intent_structure
from intent_pipeline.uac_capabilities import (
    deployment_intent,
    deployment_matrix_payload,
    primary_surface,
    summarized_emitted_surfaces,
)

_DEFAULT_TARGET_SYSTEMS = ("codex", "gemini", "claude", "kiro")
_AGENT_SIGNAL_PATTERNS = (
    re.compile(r"^kind\s*:\s*[\"']?agent[\"']?\b", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^role\s*:\s*[\"']?agent[\"']?\b", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^max_turns\s*:\s*\d+\b", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\bsub-?agent\b", re.IGNORECASE),
    re.compile(r"\bagentspawn\b", re.IGNORECASE),
    re.compile(r"\bdeveloper_instructions\b", re.IGNORECASE),
    re.compile(r"\bsystem prompt\b", re.IGNORECASE),
    re.compile(r"\byou are\b", re.IGNORECASE),
    re.compile(r"\bresponsibilities\b", re.IGNORECASE),
    re.compile(r"\bmission\b", re.IGNORECASE),
    re.compile(r"\bmode of operation\b", re.IGNORECASE),
    re.compile(r"\btool boundaries\b", re.IGNORECASE),
)
_SKILL_SIGNAL_PATTERNS = (
    re.compile(r"^#\s+.+", re.MULTILINE),
    re.compile(r"\bworkflow\b", re.IGNORECASE),
    re.compile(r"\busage examples?\b", re.IGNORECASE),
    re.compile(r"\bhard constraints?\b", re.IGNORECASE),
    re.compile(r"\boutput format\b", re.IGNORECASE),
    re.compile(r"\bpurpose\b", re.IGNORECASE),
    re.compile(r"\binputs\b", re.IGNORECASE),
    re.compile(r"\bexamples?\b", re.IGNORECASE),
    re.compile(r"\bsteps?\b", re.IGNORECASE),
    re.compile(r"\bprocess\b", re.IGNORECASE),
)
_CONFIG_SIGNAL_PATTERNS = (
    re.compile(r"^\s*\[.+\]\s*$", re.MULTILINE),
    re.compile(r"^\s*\w+\s*=\s*.+$", re.MULTILINE),
    re.compile(r"^\s*\{\s*\"", re.MULTILINE),
)
_PROMPT_MARKER_PATTERNS = (
    re.compile(r"\bobjective\b", re.IGNORECASE),
    re.compile(r"\bin scope\b", re.IGNORECASE),
    re.compile(r"\bout of scope\b", re.IGNORECASE),
    re.compile(r"\bconstraints?\b", re.IGNORECASE),
    re.compile(r"\bacceptance criteria\b", re.IGNORECASE),
)


@dataclass(frozen=True, slots=True)
class UacAssessment:
    source_type: str
    normalized_source: str
    content_kind: str
    capability_type: str
    recommended_surface: str
    confidence: float
    signals: tuple[str, ...]
    rationale: str
    scorecard: Mapping[str, int]
    emitted_surfaces: Mapping[str, tuple[str, ...]]
    deployment_intent: str
    target_systems: tuple[str, ...] = _DEFAULT_TARGET_SYSTEMS
    modernization_focus: tuple[str, ...] = ()

    def as_payload(self) -> dict[str, object]:
        return {
            "source_type": self.source_type,
            "normalized_source": self.normalized_source,
            "content_kind": self.content_kind,
            "capability_type": self.capability_type,
            "recommended_surface": self.recommended_surface,
            "confidence": round(self.confidence, 2),
            "signals": list(self.signals),
            "rationale": self.rationale,
            "scorecard": dict(self.scorecard),
            "rubric": classification_rubric_payload(),
            "deployment_matrix": deployment_matrix_payload(),
            "emitted_surfaces": {cli: list(names) for cli, names in self.emitted_surfaces.items() if names},
            "deployment_intent": self.deployment_intent,
            "target_systems": list(self.target_systems),
            "modernization_focus": list(self.modernization_focus),
        }


def assess_uac_source(
    raw_text: str,
    *,
    analysis_text: str | None = None,
    source_metadata: Mapping[str, object] | None = None,
    source_hint: str | Path | None = None,
) -> UacAssessment:
    if not isinstance(raw_text, str):
        raise TypeError("assess_uac_source expects raw_text as str")
    source_type = _normalize_metadata_value(source_metadata, "source_type", default="LOCAL_FILE")
    normalized_source = _normalize_source(source_metadata, source_hint)
    source_path = Path(normalized_source) if source_type == "LOCAL_FILE" else None
    lower_text = raw_text.casefold()
    analysis_basis = analysis_text if isinstance(analysis_text, str) and analysis_text.strip() else raw_text
    structure = extract_intent_structure(analysis_basis)

    signals: list[str] = []
    agent_score = 0
    skill_score = 0
    config_score = 0

    if source_path is not None:
        if source_path.name == "SKILL.md":
            skill_score += 4
            signals.append("source file is SKILL.md")
        if source_path.suffix.casefold() == ".toml":
            config_score += 2
            signals.append("source file is TOML")
        if source_path.suffix.casefold() == ".json":
            config_score += 2
            signals.append("source file is JSON")

    for pattern in _AGENT_SIGNAL_PATTERNS:
        if pattern.search(raw_text):
            agent_score += 2
    if agent_score:
        signals.append("agent control markers detected")

    for pattern in _SKILL_SIGNAL_PATTERNS:
        if pattern.search(raw_text):
            skill_score += 1
    if skill_score:
        signals.append("skill/workflow markers detected")

    for pattern in _CONFIG_SIGNAL_PATTERNS:
        if pattern.search(raw_text):
            config_score += 1
    if config_score:
        signals.append("config-like structure detected")

    semantic_count = structure.semantic_category_count
    if structure.objective:
        skill_score += 2
        signals.append("explicit objective structure detected")
    if structure.in_scope:
        skill_score += 2
        signals.append("explicit in-scope structure detected")
    if structure.out_of_scope:
        skill_score += 1
        signals.append("explicit out-of-scope structure detected")
    if structure.constraints:
        skill_score += 1
        signals.append("explicit constraint structure detected")
    if structure.acceptance:
        skill_score += 1
        signals.append("explicit acceptance structure detected")
    if semantic_count >= 3:
        signals.append("multi-section prompt/spec structure detected")

    prompt_marker_hits = sum(1 for pattern in _PROMPT_MARKER_PATTERNS if pattern.search(raw_text))
    if prompt_marker_hits >= 2:
        skill_score += 1

    if "developer_instructions" in lower_text or "system prompt" in lower_text:
        agent_score += 2
        signals.append("agent/system prompt framing detected")

    if "usage examples" in lower_text or "output format" in lower_text:
        skill_score += 1

    scorecard = {
        "agent_score": agent_score,
        "skill_score": skill_score,
        "config_score": config_score,
        "semantic_category_count": semantic_count,
        "prompt_marker_hits": prompt_marker_hits,
    }

    capability_type: str
    content_kind: str
    confidence: float
    rationale: str
    modernization_focus: tuple[str, ...]

    if config_score >= 2 and not semantic_count and skill_score <= 1 and agent_score <= 2:
        capability_type = "manual_review"
        content_kind = "config_like"
        confidence = 0.71
        rationale = (
            "Source is mostly configuration or registration data. It should be paired with a prompt body "
            "before attempting automatic uplift into a user-facing skill or agent."
        )
        modernization_focus = (
            "locate canonical prompt body",
            "pair config with executable prompt instructions",
            "review target platform-specific fields manually",
        )
    elif agent_score >= 4 and skill_score >= 4:
        capability_type = "both"
        content_kind = "hybrid_agent_workflow"
        confidence = min(0.98, 0.58 + (agent_score + skill_score) * 0.02)
        rationale = (
            "Source carries both strong workflow/prompt structure and explicit agent-only control semantics. "
            "Keep one SSOT entry and emit both workflow and agent surfaces."
        )
        modernization_focus = (
            "separate reusable workflow guidance from agent-only control metadata",
            "emit both skill/command and agent surfaces from one canonical SSOT entry",
            "preserve safety, escalation, and tool-boundary declarations",
        )
    elif agent_score >= max(skill_score + 2, 4):
        capability_type = "agent"
        content_kind = "agent_like"
        confidence = min(0.98, 0.55 + (agent_score - skill_score) * 0.08)
        rationale = (
            "Source reads like an orchestrated agent definition with explicit behavior, "
            "control-plane markers, or agent-only metadata."
        )
        modernization_focus = (
            "normalize role and tool declarations",
            "preserve explicit safety and escalation rules",
            "emit target agent registrations where supported",
        )
    elif skill_score >= 3:
        capability_type = "skill"
        content_kind = "prompt_like" if semantic_count >= 2 else "skill_like"
        confidence = min(0.97, 0.56 + skill_score * 0.05)
        rationale = (
            "Source contains reusable workflow/prompt structure with explicit objectives, "
            "constraints, or usage framing and is best shipped as a skill surface."
        )
        modernization_focus = (
            "normalize prompt sections into deterministic headings",
            "preserve examples and hard constraints",
            "emit skill surfaces across supported CLIs",
        )
    else:
        capability_type = "manual_review"
        content_kind = "unknown"
        confidence = 0.52
        rationale = (
            "Source does not expose enough deterministic structure to classify safely as a skill or agent. "
            "Manual packaging review is required."
        )
        modernization_focus = (
            "add objective and scope markers",
            "separate prompt body from configuration",
            "annotate intended runtime surface",
        )

    return UacAssessment(
        source_type=source_type,
        normalized_source=normalized_source,
        content_kind=content_kind,
        capability_type=capability_type,
        recommended_surface=primary_surface(capability_type),
        confidence=confidence,
        signals=tuple(dict.fromkeys(signals)),
        rationale=rationale,
        scorecard=scorecard,
        emitted_surfaces={cli: tuple(names) for cli, names in summarized_emitted_surfaces(capability_type).items()},
        deployment_intent=deployment_intent(capability_type, confidence),
        modernization_focus=modernization_focus,
    )


def classification_rubric_payload() -> dict[str, object]:
    return {
        "skill": {
            "decision_rule": "Choose skill when reusable prompt/workflow structure is strong, skill_score >= 3, and agent control markers are not dominant.",
            "signals": [
                "explicit objective / in-scope / out-of-scope / constraints / acceptance sections",
                "workflow or usage framing",
                "examples or output format sections",
                "SKILL.md or prompt-like source shape",
            ],
        },
        "agent": {
            "decision_rule": "Choose agent when agent_score is dominant and agent_score >= 4.",
            "signals": [
                "kind: agent or role: agent",
                "max_turns or explicit tool/control-plane metadata",
                "sub-agent, delegation, or system-prompt framing",
                "responsibilities / mission / operating-mode sections",
            ],
        },
        "both": {
            "decision_rule": "Choose both when strong workflow structure and strong agent control semantics are both present (agent_score >= 4 and skill_score >= 4).",
            "signals": [
                "reusable workflow/prompt sections plus explicit agent registration markers",
                "one source needs both skill invocation and agent execution surfaces",
            ],
        },
        "manual_review": {
            "decision_rule": "Choose manual_review for config-only, low-structure, or mixed-shape sources that cannot be deployed safely.",
            "signals": [
                "config markers without prompt structure",
                "missing semantic sections",
                "ambiguous or mixed prompt/config content",
            ],
        },
        "scoring": {
            "agent_score": "weighted sum of agent/control-plane markers",
            "skill_score": "weighted sum of prompt/workflow and semantic-structure markers",
            "config_score": "weighted sum of config-only markers",
            "semantic_category_count": "count of populated semantic buckets from deterministic intent extraction",
            "prompt_marker_hits": "count of coarse prompt marker matches",
        },
    }


def _normalize_metadata_value(
    source_metadata: Mapping[str, object] | None,
    key: str,
    *,
    default: str,
) -> str:
    if source_metadata is None:
        return default
    value = source_metadata.get(key, default)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _normalize_source(
    source_metadata: Mapping[str, object] | None,
    source_hint: str | Path | None,
) -> str:
    if source_metadata is not None:
        normalized = source_metadata.get("normalized_source")
        if isinstance(normalized, str) and normalized.strip():
            return normalized.strip()
    if isinstance(source_hint, Path):
        return str(source_hint.expanduser().resolve())
    if isinstance(source_hint, str) and source_hint.strip():
        return source_hint.strip()
    return "unknown"


__all__ = ["UacAssessment", "assess_uac_source", "classification_rubric_payload"]
