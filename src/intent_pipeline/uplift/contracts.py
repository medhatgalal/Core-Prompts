"""Canonical uplift contract and acceptance report types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Mapping


UPLIFT_CONTRACT_SCHEMA_VERSION = "2.0.0"
_SUPPORTED_SCHEMA_MAJOR = "2"


def _normalize_text(value: str) -> str:
    return value.strip()


def _canonicalize_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    return {key: _canonicalize_value(data[key]) for key in sorted(data)}


def _canonicalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _canonicalize_mapping(value)
    if isinstance(value, list):
        return [_canonicalize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_canonicalize_value(item) for item in value]
    return value


def _validate_schema_version(schema_version: str) -> str:
    if not isinstance(schema_version, str):
        raise TypeError("schema_version must be str")
    normalized = _normalize_text(schema_version)
    if not normalized:
        raise ValueError("schema_version is required")
    major = normalized.split(".", 1)[0]
    if major != _SUPPORTED_SCHEMA_MAJOR:
        raise ValueError(
            f"Unsupported schema major version '{major}'. Expected {_SUPPORTED_SCHEMA_MAJOR}.x"
        )
    return normalized


class AcceptanceDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass(frozen=True, slots=True)
class AcceptanceEvidence:
    evidence_id: str
    task_id: str
    source: str
    detail: str

    def __post_init__(self) -> None:
        for field_name in ("evidence_id", "task_id", "source", "detail"):
            value = _normalize_text(getattr(self, field_name))
            if not value:
                raise ValueError(f"{field_name} is required")
            object.__setattr__(self, field_name, value)

    def as_payload(self) -> dict[str, str]:
        return {
            "evidence_id": self.evidence_id,
            "task_id": self.task_id,
            "source": self.source,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    criterion_id: str
    label: str
    is_hard: bool
    passed: bool
    score: int
    max_score: int
    rationale: str
    evidence: tuple[AcceptanceEvidence, ...]

    def __post_init__(self) -> None:
        normalized_id = _normalize_text(self.criterion_id)
        normalized_label = _normalize_text(self.label)
        normalized_rationale = _normalize_text(self.rationale)
        if not normalized_id:
            raise ValueError("criterion_id is required")
        if not normalized_label:
            raise ValueError("label is required")
        if not normalized_rationale:
            raise ValueError("rationale is required")
        if self.max_score < 0:
            raise ValueError("max_score must be >= 0")
        if self.score < 0 or self.score > self.max_score:
            raise ValueError("score must be between 0 and max_score")
        if not self.evidence:
            raise ValueError("criterion evidence is required")
        object.__setattr__(self, "criterion_id", normalized_id)
        object.__setattr__(self, "label", normalized_label)
        object.__setattr__(self, "rationale", normalized_rationale)
        object.__setattr__(self, "evidence", tuple(sorted(self.evidence, key=lambda item: item.evidence_id)))

    def task_ids(self) -> tuple[str, ...]:
        return tuple(sorted({entry.task_id for entry in self.evidence}))

    def as_payload(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "label": self.label,
            "is_hard": self.is_hard,
            "passed": self.passed,
            "score": self.score,
            "max_score": self.max_score,
            "rationale": self.rationale,
            "task_ids": list(self.task_ids()),
            "evidence": [entry.as_payload() for entry in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class AcceptanceReport:
    decision: AcceptanceDecision
    score: int
    max_score: int
    threshold: int
    criteria: tuple[AcceptanceCriterion, ...]
    missing_evidence: tuple[str, ...] = ()
    failed_hard_criteria: tuple[str, ...] = ()
    summary: str = ""

    def __post_init__(self) -> None:
        if self.max_score < 0:
            raise ValueError("max_score must be >= 0")
        if self.threshold < 0 or self.threshold > self.max_score:
            raise ValueError("threshold must be between 0 and max_score")
        if self.score < 0 or self.score > self.max_score:
            raise ValueError("score must be between 0 and max_score")
        if not self.criteria:
            raise ValueError("criteria are required")
        if self.missing_evidence and self.decision is not AcceptanceDecision.NEEDS_REVIEW:
            raise ValueError("missing_evidence requires NEEDS_REVIEW decision")
        object.__setattr__(self, "criteria", tuple(sorted(self.criteria, key=lambda item: item.criterion_id)))
        object.__setattr__(self, "missing_evidence", tuple(sorted({item for item in self.missing_evidence if item})))
        object.__setattr__(
            self,
            "failed_hard_criteria",
            tuple(sorted({item for item in self.failed_hard_criteria if item})),
        )
        object.__setattr__(self, "summary", _normalize_text(self.summary))

    def as_payload(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "score": self.score,
            "max_score": self.max_score,
            "threshold": self.threshold,
            "criteria": [criterion.as_payload() for criterion in self.criteria],
            "missing_evidence": list(self.missing_evidence),
            "failed_hard_criteria": list(self.failed_hard_criteria),
            "summary": self.summary,
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class UpliftContract:
    schema_version: str
    context: Mapping[str, Any]
    intent: Mapping[str, Any]
    task_graph: Mapping[str, Any]
    constraints: Mapping[str, Any]
    acceptance: AcceptanceReport

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_version(self.schema_version))
        object.__setattr__(self, "context", _canonicalize_mapping(self.context))
        object.__setattr__(self, "intent", _canonicalize_mapping(self.intent))
        object.__setattr__(self, "task_graph", _canonicalize_mapping(self.task_graph))
        object.__setattr__(self, "constraints", _canonicalize_mapping(self.constraints))

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "context": dict(self.context),
            "intent": dict(self.intent),
            "task_graph": dict(self.task_graph),
            "constraints": dict(self.constraints),
            "acceptance": self.acceptance.as_payload(),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


__all__ = [
    "AcceptanceCriterion",
    "AcceptanceDecision",
    "AcceptanceEvidence",
    "AcceptanceReport",
    "UPLIFT_CONTRACT_SCHEMA_VERSION",
    "UpliftContract",
]
