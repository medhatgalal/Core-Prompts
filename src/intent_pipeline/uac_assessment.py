"""Deterministic UAC source assessment and packaging recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping, Sequence

from intent_pipeline.intent_structure import extract_intent_structure

_DEFAULT_TARGET_SYSTEMS = ("codex", "gemini", "claude", "kiro")
_AGENT_SIGNAL_PATTERNS = (
    re.compile(r"^kind\s*:\s*agent\b", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^role\s*:\s*agent\b", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^max_turns\s*:\s*\d+\b", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\bsub-?agent\b", re.IGNORECASE),
    re.compile(r"\bagentSpawn\b", re.IGNORECASE),
    re.compile(r"\bapproved_by\b", re.IGNORECASE),
)
_SKILL_SIGNAL_PATTERNS = (
    re.compile(r"^#\s+.+", re.MULTILINE),
    re.compile(r"\bworkflow\b", re.IGNORECASE),
    re.compile(r"\busage examples?\b", re.IGNORECASE),
    re.compile(r"\bhard constraints?\b", re.IGNORECASE),
    re.compile(r"\boutput format\b", re.IGNORECASE),
    re.compile(r"\bpurpose\b", re.IGNORECASE),
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
    recommended_surface: str
    confidence: float
    signals: tuple[str, ...]
    rationale: str
    target_systems: tuple[str, ...] = _DEFAULT_TARGET_SYSTEMS
    modernization_focus: tuple[str, ...] = ()

    def as_payload(self) -> dict[str, object]:
        return {
            "source_type": self.source_type,
            "normalized_source": self.normalized_source,
            "content_kind": self.content_kind,
            "recommended_surface": self.recommended_surface,
            "confidence": round(self.confidence, 2),
            "signals": list(self.signals),
            "rationale": self.rationale,
            "target_systems": list(self.target_systems),
            "modernization_focus": list(self.modernization_focus),
        }


def assess_uac_source(
    raw_text: str,
    *,
    source_metadata: Mapping[str, object] | None = None,
    source_hint: str | Path | None = None,
) -> UacAssessment:
    if not isinstance(raw_text, str):
        raise TypeError("assess_uac_source expects raw_text as str")
    source_type = _normalize_metadata_value(source_metadata, "source_type", default="LOCAL_FILE")
    normalized_source = _normalize_source(source_metadata, source_hint)
    source_path = Path(normalized_source) if source_type == "LOCAL_FILE" else None
    lower_text = raw_text.casefold()
    structure = extract_intent_structure(raw_text)

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

    if agent_score >= skill_score + 2:
        recommended_surface = "agent"
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
        recommended_surface = "skill"
        content_kind = "prompt_like" if semantic_count >= 2 else "skill_like"
        confidence = min(0.97, 0.56 + skill_score * 0.05)
        rationale = (
            "Source contains reusable workflow/prompt structure with explicit objectives, "
            "constraints, or usage framing and is best shipped as a command/skill surface."
        )
        modernization_focus = (
            "normalize prompt sections into deterministic headings",
            "preserve examples and hard constraints",
            "emit skill/command surfaces across supported CLIs",
        )
    elif config_score >= 2 and not semantic_count:
        recommended_surface = "manual_review"
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
    else:
        recommended_surface = "manual_review"
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
        recommended_surface=recommended_surface,
        confidence=confidence,
        signals=tuple(dict.fromkeys(signals)),
        rationale=rationale,
        modernization_focus=modernization_focus,
    )


def _normalize_metadata_value(
    source_metadata: Mapping[str, object] | None,
    key: str,
    *,
    default: str,
) -> str:
    if not source_metadata:
        return default
    raw_value = source_metadata.get(key)
    if not isinstance(raw_value, str):
        return default
    normalized = raw_value.strip()
    return normalized or default


def _normalize_source(
    source_metadata: Mapping[str, object] | None,
    source_hint: str | Path | None,
) -> str:
    if source_metadata:
        raw_value = source_metadata.get("normalized_source")
        if isinstance(raw_value, str) and raw_value.strip():
            return raw_value.strip()
    if source_hint is None:
        return "unknown"
    if isinstance(source_hint, Path):
        return str(source_hint)
    return str(source_hint).strip() or "unknown"


__all__ = ["UacAssessment", "assess_uac_source"]
