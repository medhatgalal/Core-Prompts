from __future__ import annotations

import re
from typing import Any, Mapping, Sequence


SHA256_RE = re.compile(r"[0-9a-f]{64}")
MIN_BINARY_AGREEMENT = 0.80
MIN_KRIPPENDORFF_ALPHA = 0.70
MAX_BIAS_DELTA = 0.05
METRIC_FIELDS = {
    "binary_agreement",
    "krippendorff_alpha",
    "critical_exact",
    "mirrored_bias_delta",
    "label_bias_delta",
    "verbosity_bias_delta",
    "expected_samples",
    "observed_samples",
}
JUDGE_BINDING_FIELDS = (
    "judge_model_sha256",
    "judge_prompt_sha256",
    "judge_rubric_sha256",
    "judge_tool_policy_sha256",
    "judge_preregistration_sha256",
    "gold_set_commitment_sha256",
)


class QualificationError(ValueError):
    """Raised when a semantic judge has not satisfied the qualification gate."""


def binary_agreement(gold: Sequence[object], observed: Sequence[object]) -> float:
    if not gold or len(gold) != len(observed):
        raise QualificationError("gold and observed labels must be complete and equally sized")
    return sum(left == right for left, right in zip(gold, observed, strict=True)) / len(gold)


def krippendorff_alpha_nominal(gold: Sequence[object], observed: Sequence[object]) -> float:
    """Calculate nominal alpha for two complete raters without external dependencies."""

    if not gold or len(gold) != len(observed):
        raise QualificationError("gold and observed labels must be complete and equally sized")
    observed_disagreement = sum(left != right for left, right in zip(gold, observed, strict=True)) / len(gold)
    labels = [*gold, *observed]
    counts = {label: labels.count(label) for label in set(labels)}
    total = len(labels)
    expected_agreement = sum((count / total) ** 2 for count in counts.values())
    expected_disagreement = 1.0 - expected_agreement
    if expected_disagreement == 0:
        return 1.0 if observed_disagreement == 0 else 0.0
    return 1.0 - (observed_disagreement / expected_disagreement)


def qualification_metrics(
    gold: Sequence[object],
    observed: Sequence[object],
    *,
    critical_indexes: Sequence[int],
    mirrored_bias_delta: float,
    label_bias_delta: float,
    verbosity_bias_delta: float,
) -> dict[str, Any]:
    if any(index < 0 or index >= len(gold) for index in critical_indexes):
        raise QualificationError("critical sample indexes must address the supplied samples")
    return {
        "binary_agreement": binary_agreement(gold, observed),
        "krippendorff_alpha": krippendorff_alpha_nominal(gold, observed),
        "critical_exact": all(gold[index] == observed[index] for index in critical_indexes),
        "mirrored_bias_delta": mirrored_bias_delta,
        "label_bias_delta": label_bias_delta,
        "verbosity_bias_delta": verbosity_bias_delta,
        "expected_samples": len(gold),
        "observed_samples": len(observed),
    }


def qualify_judge(
    metrics: Mapping[str, Any],
    *,
    judge_model_sha256: str,
    judge_prompt_sha256: str,
    judge_rubric_sha256: str,
    judge_tool_policy_sha256: str,
    judge_preregistration_sha256: str,
    gold_set_commitment_sha256: str,
) -> dict[str, Any]:
    """Apply the complete fail-closed semantic-judge qualification gate."""

    if set(metrics) != METRIC_FIELDS:
        raise QualificationError("judge qualification metrics are incomplete or contain unknown fields")
    bindings = {
        "judge_model_sha256": judge_model_sha256,
        "judge_prompt_sha256": judge_prompt_sha256,
        "judge_rubric_sha256": judge_rubric_sha256,
        "judge_tool_policy_sha256": judge_tool_policy_sha256,
        "judge_preregistration_sha256": judge_preregistration_sha256,
        "gold_set_commitment_sha256": gold_set_commitment_sha256,
    }
    invalid = [field for field, value in bindings.items() if not SHA256_RE.fullmatch(value)]
    if invalid:
        raise QualificationError(f"judge qualification has invalid binding hashes: {', '.join(invalid)}")
    try:
        agreement = float(metrics["binary_agreement"])
        alpha = float(metrics["krippendorff_alpha"])
        bias_values = [
            float(metrics["mirrored_bias_delta"]),
            float(metrics["label_bias_delta"]),
            float(metrics["verbosity_bias_delta"]),
        ]
        expected = int(metrics["expected_samples"])
        observed = int(metrics["observed_samples"])
    except (TypeError, ValueError) as exc:
        raise QualificationError("judge qualification metrics must be numeric") from exc
    checks = {
        "binary_agreement": agreement >= MIN_BINARY_AGREEMENT,
        "krippendorff_alpha": alpha >= MIN_KRIPPENDORFF_ALPHA,
        "critical_exact": metrics["critical_exact"] is True,
        "mirrored_bias": abs(bias_values[0]) <= MAX_BIAS_DELTA,
        "label_bias": abs(bias_values[1]) <= MAX_BIAS_DELTA,
        "verbosity_bias": abs(bias_values[2]) <= MAX_BIAS_DELTA,
        "sample_completeness": expected > 0 and observed == expected,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise QualificationError(f"judge qualification failed: {', '.join(failed)}")
    return {
        "qualified": True,
        **bindings,
        "metrics": dict(metrics),
        "checks": checks,
    }


def validate_qualification_binding(
    qualification: Mapping[str, Any],
    *,
    judge_model_sha256: str,
    judge_prompt_sha256: str,
    judge_rubric_sha256: str,
    judge_tool_policy_sha256: str,
    judge_preregistration_sha256: str,
    gold_set_commitment_sha256: str,
) -> None:
    bindings = {
        "judge_model_sha256": judge_model_sha256,
        "judge_prompt_sha256": judge_prompt_sha256,
        "judge_rubric_sha256": judge_rubric_sha256,
        "judge_tool_policy_sha256": judge_tool_policy_sha256,
        "judge_preregistration_sha256": judge_preregistration_sha256,
        "gold_set_commitment_sha256": gold_set_commitment_sha256,
    }
    stale = [field for field, value in bindings.items() if qualification.get(field) != value]
    if stale:
        raise QualificationError(f"judge qualification binding is stale: {', '.join(stale)}")
    result = qualify_judge(
        qualification.get("metrics", {}),
        **bindings,
    )
    if qualification.get("qualified") is not True or result["qualified"] is not True:
        raise QualificationError("judge qualification does not assert a passing result")
