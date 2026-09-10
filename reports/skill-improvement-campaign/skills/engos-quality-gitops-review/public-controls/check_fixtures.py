"""Validate public fixture data, not agent performance or provider truth."""
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    cases = [json.loads(line) for line in (root / "cases.jsonl").read_text().splitlines()]
    expectations = json.loads((root / "expected.json").read_text())
    assert expectations["public"] and expectations["not_holdout"]
    by_id = {case["id"]: case for case in cases}
    assert len(by_id) == len(cases) == 16
    assert set(by_id) == set(expectations["cases"]) == {f"G{i:02}" for i in range(1, 17)}
    for case in cases:
        assert case["synthetic"] is True
        assert case["request"] and case["authority"] and case["evidence"]
        answer = expectations["cases"][case["id"]]
        assert set(answer["gates"].values()) <= {"ready", "blocked", "unknown", "not_applicable"}
        assert all(answer[key] for key in ("must_include", "must_not", "useful_artifacts"))
    e = {key: value["evidence"] for key, value in by_id.items()}
    # Case facts which make the controls discriminating, checked independently
    # of the expected prose. No broad gate classifier is implemented here.
    assert e["G01"]["worktree_unstaged"] and e["G01"]["review"]["status"] == "pass"
    assert "src/auth.py" in e["G02"]["diff"] and "typo" in e["G02"]["commit_message"]
    assert e["G03"]["source"] in e["G03"]["lineage"]["parents"]
    assert e["G03"]["checks"][1]["conclusion"] == "skipped"
    assert e["G03"]["checks"][1]["name"] in e["G03"]["policy"]["required_checks"]
    assert e["G03"]["policy"]["docs_preview_skip_permitted"]
    assert not e["G03"]["checks"][1]["executed"]
    assert e["G04"]["source"] not in e["G04"]["lineage"]["parents"]
    assert e["G05"]["pipelines"][0]["jobs"][1]["allow_failure"]
    current = [p for p in e["G06"]["pipelines"] if p["id"] == e["G06"]["required_pipeline"]][0]
    assert current["status"] == "success" and e["G06"]["source"] in current["parents"]
    assert current["sha"] != e["G06"]["source"]
    assert e["G07"]["pipelines"][0]["jobs"][0]["failure_reason"] == "runner_system_failure"
    assert e["G08"]["gitlab"]["http_status"] == 403
    assert set(e["G09"]["contract"]["required_members"]) - set(e["G09"]["artifact"]["members"])
    assert e["G09"]["artifact"]["sha256"] != e["G09"]["attestation"]["subject_sha256"]
    variant = e["G09"]["policy_parameter_variant"]
    assert variant["variant_id"] == "G09-parameters"
    assert variant["contract"]["provenance_required"] and variant["attestation"]["signature_valid"]
    assert variant["attestation"]["subject_sha256"] == variant["artifact"]["sha256"]
    assert variant["attestation"]["builder"] == variant["contract"]["trusted_builder"]
    assert variant["attestation"]["source"] == variant["source"]
    assert variant["attestation"]["build_type"] == variant["contract"]["expected_build_type"]
    assert set(variant["contract"]["required_members"]) <= set(variant["artifact"]["members"])
    assert variant["smoke"]["result"] == "pass"
    observed = variant["attestation"]["external_parameters"]
    required = variant["contract"]["expected_external_parameters"]
    assert observed.keys() == required.keys()
    assert {key for key in required if observed[key] != required[key]} == {"debug_hooks"}
    assert observed["debug_hooks"] is True and required["debug_hooks"] is False
    assert set(e["G10"]["contract"]["required_members"]) <= set(e["G10"]["artifact"]["members"])
    assert not e["G10"]["contract"]["provenance_required"] and e["G10"]["attestation"] is None
    assert e["G10"]["smoke"]["artifact_sha256"] == e["G10"]["artifact"]["sha256"]
    providers = e["G11"]["providers"]
    assert providers["github"]["main"] != providers["gitlab"]["main"]
    assert len(set(e["G11"]["trees"].values())) == 1
    assert {p["download_sha256"] for p in e["G12"]["providers"].values()} == {e["G12"]["expected_sha256"]}
    assert e["G12"]["installed"]["content_sha256"] != e["G12"]["expected_sha256"]
    assert e["G13"]["targets"][0]["active_session"] and e["G13"]["targets"][0]["untracked"]
    assert e["G13"]["targets"][1]["locked"] and not e["G13"]["targets"][1]["mounted"]
    safe = e["G14"]["targets"][0]
    assert safe["reviewed_content_included"] and safe["retained_unique_evidence"]
    assert not any(safe[k] for k in ("active_session", "locked", "untracked", "ignored"))
    assert e["G15"]["existing_reviews"][0]["subject"] != e["G15"]["source"]
    assert e["G16"]["events"][2]["completion"] == "unknown"
    assert e["G16"]["state_after"]["gitlab_main"] == "unknown"
    controls = json.loads((root / "negative-output-controls.json").read_text())
    assert len({c["id"] for c in controls}) == len(controls) == 7
    assert all(c["case"] in by_id and c["expected"] == "reject" for c in controls)
    print(json.dumps({"status": "pass", "cases": len(cases), "negative_output_controls": len(controls),
                      "evidence_class": "static_fixture_integrity", "model_calls": 0,
                      "native_preflight": False, "assessor_calibration": "not_run",
                      "public_variants_within_cases": 1,
                      "downstream_improvement": "unmeasured"}, indent=2))


if __name__ == "__main__":
    main()
