from __future__ import annotations

from copy import deepcopy

from intent_pipeline.phase4.contracts import (
    ValidationDecision,
    ValidationErrorCode,
    parse_capability_matrix,
    parse_policy_contract,
)
from intent_pipeline.phase4.validator import validate_target


def test_val_01_typed_matrix_rejects_freeform_capabilities(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    typed_matrix = parse_capability_matrix(deepcopy(phase4_capability_matrix_payload))
    typed_policy = parse_policy_contract(deepcopy(phase4_policy_contract_payload))
    pass_report = validate_target(deepcopy(phase4_route_spec_payload), typed_matrix, typed_policy)

    assert "VAL-01"
    assert pass_report.decision is ValidationDecision.PASS
    assert pass_report.can_proceed is True

    freeform_matrix = deepcopy(phase4_capability_matrix_payload)
    freeform_matrix["tools"][0]["metadata"] = {"owner": "freeform"}

    block_report = validate_target(deepcopy(phase4_route_spec_payload), freeform_matrix, typed_policy)

    assert block_report.decision is ValidationDecision.BLOCK
    assert block_report.can_proceed is False
    assert block_report.issues
    first_issue = block_report.issues[0]
    assert first_issue.code is ValidationErrorCode.FREEFORM_CAPABILITY_METADATA_PATH
    assert "capability_matrix.tools[0].metadata" in first_issue.evidence_paths
    assert any(path.startswith("route_spec.") for path in first_issue.evidence_paths)


def test_val_02_fail_closed_blocks_on_capability_mismatch(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    pass_report = validate_target(
        deepcopy(phase4_route_spec_payload),
        deepcopy(phase4_capability_matrix_payload),
        deepcopy(phase4_policy_contract_payload),
    )

    assert "VAL-02"
    assert pass_report.decision is ValidationDecision.PASS
    assert pass_report.can_proceed is True

    blocking_policy = deepcopy(phase4_policy_contract_payload)
    blocking_policy["required_capabilities"][0]["capabilities"] = ["cap.read", "cap.write", "cap.execute"]

    block_report = validate_target(
        deepcopy(phase4_route_spec_payload),
        deepcopy(phase4_capability_matrix_payload),
        blocking_policy,
    )

    assert block_report.decision is ValidationDecision.BLOCK
    assert block_report.can_proceed is False
    assert [issue.code for issue in block_report.issues] == [ValidationErrorCode.REQUIRED_CAPABILITY_MISSING]
    assert block_report.checked_capabilities == ("cap.execute", "cap.read", "cap.write")


def test_val_03_validation_errors_include_code_and_evidence_paths_deterministically(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    route_spec = deepcopy(phase4_route_spec_payload)
    matrix = deepcopy(phase4_capability_matrix_payload)
    policy = deepcopy(phase4_policy_contract_payload)

    dominant_rule_id = str(route_spec["dominant_rule_id"])
    policy["required_capabilities"][0]["capabilities"] = ["cap.read", "cap.write", "cap.execute"]
    policy["allowed_route_decisions"] = ["NEEDS_REVIEW"]
    policy["blocked_dominant_rule_ids"] = [dominant_rule_id]

    outputs = [validate_target(deepcopy(route_spec), deepcopy(matrix), deepcopy(policy)).to_json() for _ in range(20)]
    report = validate_target(route_spec, matrix, policy)

    assert "VAL-03"
    assert report.decision is ValidationDecision.BLOCK
    assert outputs == [outputs[0]] * len(outputs)

    expected_codes = [
        ValidationErrorCode.REQUIRED_CAPABILITY_MISSING,
        ValidationErrorCode.POLICY_RULE_BLOCKED,
        ValidationErrorCode.ROUTE_DECISION_BLOCKED,
    ]
    issue_codes = [issue.code for issue in report.issues]
    assert issue_codes == expected_codes
    assert issue_codes == sorted(issue_codes, key=lambda code: code.value)

    for issue in report.issues:
        assert issue.dominant_rule_id == dominant_rule_id
        assert any(path.startswith("route_spec.") for path in issue.evidence_paths)
        assert any(path.startswith("capability_matrix.") for path in issue.evidence_paths)
