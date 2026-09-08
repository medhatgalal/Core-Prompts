"""Fixture-only adapter capture; no provider calls or credentials are used."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import jsonschema
import pytest

from core_prompts_eval.adapters import AdapterResponse
from core_prompts_eval.artifacts import evaluator_package_hash, verify_artifact_chain
from core_prompts_eval.contracts import artifact_hash
from core_prompts_eval.run_plan import RunPlanError, load_run_plan
from core_prompts_eval.runner import run_model_comparison
from intent_pipeline.capability_resources import load_resource_bundle
from test_eval_runner import ROOT, _plan


def setup_run(tmp_path: Path) -> tuple[Path, Path]:
    plan_path = _plan(tmp_path)
    repo = tmp_path / "repo"
    files = list((ROOT / "src/core_prompts_eval").glob("*.py")) + [
        ROOT / "src/intent_pipeline/capability_resources.py",
        ROOT / "evals/adapters/registry.json",
        ROOT / "evals/adapters/fake_adapter.py",
        ROOT / "evals/contracts/engos-orchestration-batman.json",
        ROOT / "evals/topologies/engos-orchestration-batman.json",
    ]
    for source in files:
        destination = repo / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return repo, plan_path


def bind_arm(repo: Path, plan_path: Path, arm: str, content: str) -> Path:
    root = repo / "snapshots" / arm / "resources"
    root.mkdir(parents=True)
    (root / "shared.md").write_text("Shared reviewer instructions.\n", encoding="utf-8")
    (root / "module.md").write_bytes(content.encode("utf-8"))
    manifest = {
        "schema_version": "CapabilityResourceMap.v1",
        "shared": ["shared.md"],
        "routes": {"/ult": ["module.md"], "/other": ["module.md"]},
        "dependencies": {},
    }
    (root / "resource-map.json").write_text(json.dumps(manifest), encoding="utf-8")
    entry_path = plan_path.parent / f"{arm}.md"
    entry_path.write_text(f"# {arm}\nLoad resources/resource-map.json and resources/module.md.\n", encoding="utf-8")
    bundle = load_resource_bundle(root, "/ult")
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload[f"{arm}_sha256"] = artifact_hash(entry_path)
    payload.setdefault("artifact_resource_bindings", {})[arm] = {
        "resource_root": root.relative_to(repo).as_posix(),
        "manifest_sha256": bundle["manifest_sha256"],
        "bundle_sha256": bundle["sha256"],
        "route": "/ult",
    }
    plan_path.write_text(json.dumps(payload), encoding="utf-8")
    return root


def capture_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    calls: list[dict] = []

    def execute(spec, request, **kwargs):
        calls.append(dict(request))
        return AdapterResponse(
            output="Fixture output", resolved_model_identifier=request["resolved_model_identifier"],
            model_version=request["model_version"], usage={"raw": 1, "cached": 0, "billed": 1},
            raw={"schema_version": "EvalAdapterResponse.v1", "fixture": True},
        )

    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", execute)
    return calls


def run(repo: Path, plan_path: Path) -> dict:
    return run_model_comparison(
        repo, slug="engos-orchestration-batman", profile="canary",
        baseline=plan_path.parent / "baseline.md", candidate=plan_path.parent / "candidate.md",
        run_plan_path=plan_path, max_tokens=512, reports_root=plan_path.parent / "reports",
    )


def test_delivers_distinct_exact_resources_and_hashes_actual_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, plan_path = setup_run(tmp_path)
    bind_arm(repo, plan_path, "baseline", "Historical baseline instruction.\r\n")
    bind_arm(repo, plan_path, "candidate", "New candidate instruction.\n")
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    jsonschema.validate(payload, json.loads((ROOT / "evals/schemas/eval-run-plan.schema.json").read_text()))
    calls = capture_calls(monkeypatch)
    result = run(repo, plan_path)
    assert result["status"] == "completed", result
    assert len(calls) == 4
    for request in calls:
        arm = "baseline" if request["entry_sha256"] == payload["baseline_sha256"] else "candidate"
        original = (plan_path.parent / f"{arm}.md").read_text(encoding="utf-8")
        assert request["artifact"].startswith(original)
        expected = "Historical baseline instruction.\r\n" if arm == "baseline" else "New candidate instruction.\n"
        excluded = "New candidate instruction." if arm == "baseline" else "Historical baseline instruction."
        assert expected in request["artifact"]
        assert excluded not in request["artifact"]
        assert "Shared reviewer instructions.\n" in request["artifact"]
        assert request["artifact_sha256"] == artifact_hash(request["artifact"])
        assert request["artifact_sha256"] != request["entry_sha256"]
        assert request["resource_binding"]["bundle_sha256"] == payload["artifact_resource_bindings"][arm]["bundle_sha256"]
    run_dir = Path(result["artifact_path"])
    for path, request in zip(sorted((run_dir / "traces").glob("*.json")), calls, strict=True):
        trace = json.loads(path.read_text(encoding="utf-8"))
        assert trace["request_sha256"] == artifact_hash(request)
        assert trace["artifact_delivery"]["artifact_sha256"] == request["artifact_sha256"]
        assert trace["artifact_delivery"]["resource_binding"] == request["resource_binding"]
    assert verify_artifact_chain(run_dir)["status"] == "valid"


def test_legacy_baseline_stays_self_contained_when_candidate_has_resources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, plan_path = setup_run(tmp_path)
    bind_arm(repo, plan_path, "candidate", "Candidate-only module.\n")
    calls = capture_calls(monkeypatch)
    result = run(repo, plan_path)
    assert result["status"] == "completed", result
    original_requests = [request for request in calls if request["artifact"] == "baseline"]
    assert len(original_requests) == 2
    assert all(request["artifact_sha256"] == request["entry_sha256"] for request in original_requests)
    assert all("resource_binding" not in request for request in original_requests)


@pytest.mark.parametrize("location", ["adjacent", "canonical"])
def test_existing_map_requires_binding_even_without_entry_reference(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, location: str) -> None:
    repo, plan_path = setup_run(tmp_path)
    payload = json.loads(plan_path.read_text())
    if location == "adjacent":
        map_path = plan_path.parent / "resources/resource-map.json"
        candidate = plan_path.parent / "candidate.md"
    else:
        candidate = repo / "ssot/engos-orchestration-batman.md"
        candidate.parent.mkdir()
        candidate.write_text("candidate")
        map_path = repo / "sources/capability-resources/engos-orchestration-batman/resource-map.json"
    map_path.parent.mkdir(parents=True)
    map_path.write_text("{}")
    calls = capture_calls(monkeypatch)
    result = run_model_comparison(
        repo, slug=payload["slug"], profile="canary", baseline=plan_path.parent / "baseline.md",
        candidate=candidate, run_plan_path=plan_path, max_tokens=512,
        reports_root=plan_path.parent / "reports",
    )
    assert result["status"] == "blocked_preflight", result
    assert calls == []
    assert "resource" in " ".join(result["blockers"])


@pytest.mark.parametrize("failure", ["missing_binding", "stale_manifest", "stale_content", "changed_route", "missing_file", "entry_mismatch", "root_escape"])
def test_invalid_resource_binding_blocks_before_adapter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    repo, plan_path = setup_run(tmp_path)
    root = bind_arm(repo, plan_path, "candidate", "Candidate module.\n")
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    binding = payload["artifact_resource_bindings"]["candidate"]
    if failure == "missing_binding":
        del payload["artifact_resource_bindings"]
    elif failure == "stale_manifest":
        (root / "resource-map.json").write_text((root / "resource-map.json").read_text() + "\n")
    elif failure == "stale_content":
        (root / "module.md").write_text("Changed content.\n")
    elif failure == "changed_route":
        binding["route"] = "/other"
    elif failure == "missing_file":
        (root / "module.md").unlink()
    elif failure == "entry_mismatch":
        candidate = plan_path.parent / "candidate.md"
        candidate.write_text("Read resources/resource-map.json and resources/undeclared.md")
        payload["candidate_sha256"] = artifact_hash(candidate)
    elif failure == "root_escape":
        target = plan_path.parent / "outside-resources"
        root.rename(target)
        root.symlink_to(target, target_is_directory=True)
    plan_path.write_text(json.dumps(payload))
    calls = capture_calls(monkeypatch)
    result = run(repo, plan_path)
    assert result["status"] == "blocked_preflight", result
    assert result["model_calls"] == 0
    assert calls == []
    assert "resource" in " ".join(result["blockers"]).lower()


def test_changed_resource_after_preflight_prevents_adapter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from core_prompts_eval import runner
    repo, plan_path = setup_run(tmp_path)
    root = bind_arm(repo, plan_path, "candidate", "Candidate module.\n")
    payload = json.loads(plan_path.read_text())
    payload["order"] = "candidate_first"
    plan_path.write_text(json.dumps(payload))
    original_resolve = runner.resolve_adapter_cli_sha256
    observations = 0

    def resolve(spec):
        nonlocal observations
        observations += 1
        if observations == 2:
            (root / "module.md").write_text("Changed immediately before dispatch.\n")
        return original_resolve(spec)

    monkeypatch.setattr(runner, "resolve_adapter_cli_sha256", resolve)
    calls = capture_calls(monkeypatch)
    result = run(repo, plan_path)
    assert result["status"] == "failed", result
    assert result["model_calls"] == 0
    assert "resource" in result["failure"].lower()
    assert calls == []


@pytest.mark.parametrize("update", [
    {"resource_root": "../escape"}, {"resource_root": "/absolute"},
    {"resource_root": "a/./b"}, {"resource_root": "a//b"}, {"resource_root": "a\x00b"},
    {"route": " /ult"}, {"manifest_sha256": "invalid"}, {"extra": True},
])
def test_run_plan_rejects_malformed_resource_binding(tmp_path: Path, update: dict) -> None:
    repo, plan_path = setup_run(tmp_path)
    bind_arm(repo, plan_path, "candidate", "Candidate module.\n")
    payload = json.loads(plan_path.read_text())
    payload["artifact_resource_bindings"]["candidate"].update(update)
    plan_path.write_text(json.dumps(payload))
    with pytest.raises(RunPlanError, match="resource"):
        load_run_plan(plan_path)


def test_resource_helper_is_in_evaluator_package_identity(tmp_path: Path) -> None:
    repo, _ = setup_run(tmp_path)
    before = evaluator_package_hash(repo)
    helper = repo / "src/intent_pipeline/capability_resources.py"
    helper.write_text(helper.read_text() + "\n# changed resource assembly\n")
    assert evaluator_package_hash(repo) != before
