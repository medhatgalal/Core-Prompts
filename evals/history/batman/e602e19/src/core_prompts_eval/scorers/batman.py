from __future__ import annotations

from typing import Any, Mapping


def _value_at(payload: Mapping[str, Any], path: str) -> Any:
    value: Any = payload
    for segment in path.split("."):
        if not isinstance(value, Mapping) or segment not in value:
            return None
        value = value[segment]
    return value


def _passes(check: Mapping[str, Any], trace: Mapping[str, Any]) -> bool:
    actual = _value_at(trace, str(check["path"]))
    operation = check["op"]
    expected = check.get("value")
    if operation == "equals":
        return actual == expected
    if operation == "truthy":
        return bool(actual)
    if operation == "contains":
        return isinstance(actual, (list, str)) and expected in actual
    if operation == "excludes":
        return isinstance(actual, (list, str)) and expected not in actual
    if operation == "ordered_contains":
        if not isinstance(actual, list) or not isinstance(expected, list):
            return False
        positions = [actual.index(item) for item in expected if item in actual]
        return len(positions) == len(expected) and positions == sorted(positions)
    if operation == "min_count":
        return isinstance(actual, (list, dict, str)) and len(actual) >= int(expected)
    if operation == "max_count":
        return isinstance(actual, (list, dict, str)) and len(actual) <= int(expected)
    raise ValueError(f"unsupported Batman scorer operation: {operation}")


def score_case(case: Mapping[str, Any], trace: Mapping[str, Any]) -> dict[str, Any]:
    """Score one structured Batman microflow without model calls or fuzzy matching."""
    checks = list(case.get("checks", []))
    results = [
        {
            "id": str(check["id"]),
            "passed": _passes(check, trace),
            "critical": bool(check.get("critical", case.get("risk") == "critical")),
        }
        for check in checks
    ]
    failed = [result["id"] for result in results if not result["passed"]]
    critical_failed = [result["id"] for result in results if result["critical"] and not result["passed"]]
    score = sum(1 for result in results if result["passed"]) / len(results) if results else 0.0
    return {
        "schema_version": "BatmanDeterministicScore.v1",
        "case_id": case.get("id"),
        "passed": not failed,
        "score": score,
        "failed_checks": failed,
        "critical_failed_checks": critical_failed,
        "model_calls": 0,
    }
