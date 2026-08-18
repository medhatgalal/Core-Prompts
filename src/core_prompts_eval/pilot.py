from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve(repo_root: Path, relative: str) -> Path:
    path = repo_root / relative
    if not path.is_file():
        raise ValueError(f"missing pilot fixture: {relative}")
    return path


def _has_path(payload: dict[str, Any], dotted: str) -> bool:
    current: Any = payload
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True


def validate_pilot_foundations(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    case_count = 0
    try:
        plan = _load_json(repo_root / "evals" / "pilot-plan.json")
    except Exception as exc:
        return {"status": "hold", "errors": [f"pilot plan invalid: {exc}"], "experiment_count": 0, "case_count": 0}

    experiments = plan.get("experiments")
    if plan.get("schema_version") != "PilotPlan.v1" or not isinstance(experiments, list) or len(experiments) != 4:
        errors.append("pilot plan must declare exactly four PilotPlan.v1 experiments")
        experiments = []
    ids = [str(item.get("id")) for item in experiments if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("pilot experiment ids must be unique")
    try:
        policy = _load_json(repo_root / ".meta" / "evaluation-policy.json")
        policy_experiments = policy.get("pilot_experiments") or []
        policy_index = {str(item.get("id")): set(item.get("skills") or []) for item in policy_experiments}
        plan_index = {str(item.get("id")): set(item.get("skills") or []) for item in experiments}
        if policy_index != plan_index:
            errors.append("evaluation policy and pilot plan disagree on experiment ids or skills")
    except Exception as exc:
        errors.append(f"evaluation policy invalid: {exc}")

    for experiment in experiments:
        try:
            fixture_path = _resolve(repo_root, str(experiment["static_fixture"]))
            experiment_id = str(experiment["id"])
            if experiment_id == "supercharge-module-preservation":
                fixture = _load_json(fixture_path)
                target = _resolve(repo_root, fixture["target"]).read_text(encoding="utf-8")
                for marker in fixture.get("required_markers", []):
                    if marker not in target:
                        errors.append(f"{experiment_id}: missing marker {marker!r}")
                for marker in fixture.get("forbidden_markers", []):
                    if marker in target:
                        errors.append(f"{experiment_id}: forbidden marker survives {marker!r}")
                case_count += len(fixture.get("required_markers", [])) + len(fixture.get("forbidden_markers", []))
            elif experiment_id == "code-review-seeded-defect":
                fixture = _load_json(fixture_path)
                artifact = _resolve(repo_root, fixture["artifact"]).read_text(encoding="utf-8")
                defects = fixture.get("seeded_defects") or []
                if not defects:
                    errors.append(f"{experiment_id}: no seeded defects")
                for defect in defects:
                    if defect.get("line_marker") not in artifact:
                        errors.append(f"{experiment_id}: seed marker missing for {defect.get('id')}")
                case_count += len(defects)
            elif experiment_id == "product-repo-code-routing":
                cases = [json.loads(line) for line in fixture_path.read_text(encoding="utf-8").splitlines() if line.strip()]
                expected_skills = set(experiment.get("skills") or [])
                represented = {case.get("expected_skill") for case in cases}
                if represented != expected_skills:
                    errors.append(f"{experiment_id}: expected-skill coverage is {sorted(represented)}")
                if len({case.get("id") for case in cases}) != len(cases):
                    errors.append(f"{experiment_id}: case ids must be unique")
                for case in cases:
                    if case.get("expected_skill") in set(case.get("forbidden_skills") or []):
                        errors.append(f"{experiment_id}: {case.get('id')} forbids its expected skill")
                case_count += len(cases)
            elif experiment_id == "uac-import-metadata-safety":
                fixture = _load_json(fixture_path)
                source = fixture.get("input") or {}
                for protected in fixture.get("protected_paths", []):
                    if not _has_path(source, protected):
                        errors.append(f"{experiment_id}: missing protected path {protected}")
                html = _resolve(repo_root, fixture["html_fixture"]).read_text(encoding="utf-8").lower()
                if "<html" not in html or fixture.get("expected_html_policy") != "reject":
                    errors.append(f"{experiment_id}: HTML rejection control is invalid")
                uac_script = (repo_root / "scripts" / "uac-import.py").read_text(encoding="utf-8")
                if "'allowed_content_types': ['text/plain', 'text/markdown']" not in uac_script:
                    errors.append(f"{experiment_id}: reviewed UAC HTML boundary is not present")
                case_count += len(fixture.get("protected_paths", [])) + 1
            else:
                errors.append(f"unknown pilot experiment: {experiment_id}")
        except Exception as exc:
            errors.append(f"{experiment.get('id', '<unknown>')}: {exc}")

    return {
        "status": "structural_ready" if not errors else "hold",
        "errors": errors,
        "experiment_count": len(experiments),
        "case_count": case_count,
        "model_calls": 0,
        "behavioral_claim": "none",
    }
