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

_DEFAULT_TARGET_SYSTEMS = ("codex", "gemini", "claude", "kiro", "grok")
# Native declarations are review signals, never evidence of runtime benefit.
_AGENT_SIGNAL_PATTERNS = (
    re.compile(r"^(?:kind|role)\s*:\s*[\"']?agent[\"']?\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*(?:max_turns|timeout_mins|developer_instructions|sandbox_mode)\s*[:=]", re.MULTILINE),
)


def _unquoted_source(text: str) -> str:
    """Exclude examples from source-shape inference; retain actual frontmatter."""
    lines: list[str] = []
    fence = ""
    fence_length = 0
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker:
            token = marker.group(1)
            if not fence:
                fence, fence_length = token[0], len(token)
            elif token[0] == fence and len(token) >= fence_length:
                fence = ""
            continue
        if not fence and not stripped.startswith(">"):
            lines.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(lines)


def _explicit_capability(text: str) -> str | None:
    # Only a leading canonical declaration counts, not prose or an example.
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|$)", text, re.DOTALL)
    if not frontmatter:
        return None
    match = re.search(
        r"^capability_type\s*:\s*[\"']?(skill|agent|both)[\"']?\s*$",
        frontmatter.group(1), re.MULTILINE,
    )
    return match.group(1) if match else None


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
    inference_text = _unquoted_source(raw_text)
    lower_text = inference_text.casefold()
    declared = _explicit_capability(raw_text)
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
        if pattern.search(inference_text):
            agent_score += 2
    if agent_score:
        signals.append("native agent configuration requires packaging review")

    for pattern in _SKILL_SIGNAL_PATTERNS:
        if pattern.search(inference_text):
            skill_score += 1
    if skill_score:
        signals.append("skill/workflow markers detected")

    for pattern in _CONFIG_SIGNAL_PATTERNS:
        if pattern.search(inference_text):
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

    if declared is not None:
        capability_type = declared
        content_kind = "declared_capability"
        confidence = 1.0
        rationale = (
            "Preserve the explicit capability declaration. It specifies packaging, not proven "
            "agent benefit; new or expanded agent emission requires reviewed execution evidence."
        )
        modernization_focus = ("preserve the declared surface set", "review changes to native execution requirements")
        signals.append("explicit capability_type declaration preserved")
    elif config_score >= 2 and not semantic_count and skill_score <= 1 and agent_score <= 2:
        capability_type = "manual_review"
        content_kind = "config_like"
        confidence = 0.71
        rationale = "Configuration-only sources require a prompt body and packaging review."
        modernization_focus = ("locate canonical prompt body", "review native configuration")
    elif agent_score:
        capability_type = "manual_review"
        content_kind = "agent_configuration"
        confidence = 0.71
        rationale = (
            "Native agent configuration indicates a possible adapter requirement. Review its "
            "provider-specific execution need before declaring agent or both; wording is not proof."
        )
        modernization_focus = ("identify the necessary native execution guarantee", "review skill plus generic worker alternative")
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
            "decision_rule": "Choose skill when reusable prompt/workflow structure is strong, skill_score >= 3, without using agent vocabulary as evidence of execution need.",
            "signals": [
                "explicit objective / in-scope / out-of-scope / constraints / acceptance sections",
                "workflow or usage framing",
                "examples or output format sections",
                "SKILL.md or prompt-like source shape",
            ],
        },
        "agent": {
            "decision_rule": "Preserve an explicit agent declaration; require reviewed native execution need for new or expanded emission.",
            "signals": [
                "kind: agent or role: agent",
                "max_turns or explicit tool/control-plane metadata",
                "reviewed provider-specific execution need",
            ],
        },
        "both": {
            "decision_rule": "Preserve an explicit both declaration; workflow headings and independent-review requirements never imply both.",
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
            "agent_score": "native configuration review signals; not an emission or benefit score",
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
