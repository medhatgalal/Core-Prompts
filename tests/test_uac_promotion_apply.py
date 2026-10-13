from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from core_prompts_eval.contracts import ContractError, artifact_hash


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("uac_import_promotion", ROOT / "scripts/uac-import.py")
assert SPEC and SPEC.loader
UAC_IMPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UAC_IMPORT)


def _revision(rev: str) -> str:
    return UAC_IMPORT.subprocess.run(
        ["git", "rev-parse", rev], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.mark.parametrize("change", ["revoked", "removed", "format_changed"])
def test_apply_rechecks_review_after_user_confirmation(tmp_path, monkeypatch, change):
    review = tmp_path / "review.json"
    approved = {"schema_version": "UACRequirementReview.v1", "verdict": "approved"}
    review.write_text(json.dumps(approved))
    payload = {
        "status": "accepted", "requirement_reviews": [approved],
        "requirement_review_files": [{"path": str(review.resolve()), "sha256": UAC_IMPORT.sha256(review.read_bytes()).hexdigest()}],
    }

    def confirm(_):
        if change == "removed":
            review.unlink()
        elif change == "revoked":
            review.write_text(json.dumps({**approved, "verdict": "rejected"}))
        else:
            review.write_text(json.dumps(approved, indent=2))
        return "yes"

    monkeypatch.setattr("builtins.input", confirm)
    monkeypatch.setattr(UAC_IMPORT, "_snapshot_apply_artifacts", lambda: pytest.fail("apply advanced after review changed"))
    result = UAC_IMPORT._apply_payload(payload, SimpleNamespace(yes=False, quality_loop="on", requirement_review=[review]), [])
    assert result["status"] == "stale_evidence"
    assert "requirement review" in result["detail"]


def test_finalize_existing_candidate_requires_exact_revision_hashes_and_ancestry(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    ssot = repo / "ssot"
    ssot.mkdir()
    path = ssot / "engos-orchestration-batman.md"
    path.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/engos-orchestration-batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=repo, check=True, capture_output=True)
    baseline_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    baseline_sha256 = artifact_hash(path)
    path.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/engos-orchestration-batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "candidate"], cwd=repo, check=True, capture_output=True)
    candidate_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    candidate_sha256 = artifact_hash(path)
    verdict = {
        "slug": "engos-orchestration-batman",
        "baseline_revision": baseline_revision,
        "candidate_revision": candidate_revision,
        "baseline_sha256": baseline_sha256,
        "candidate_sha256": candidate_sha256,
    }

    mode = UAC_IMPORT._validate_promotion_revision_bindings(
        repo,
        verdict,
        slug="engos-orchestration-batman",
        candidate_text="candidate\n",
        finalize_existing_candidate=True,
    )

    assert mode == "finalize_existing_candidate"


def test_finalize_existing_candidate_refuses_nonexistent_candidate() -> None:
    verdict = {
        "slug": "engos-orchestration-batman",
        "baseline_revision": _revision("HEAD"),
        "candidate_revision": "0" * 40,
        "baseline_sha256": artifact_hash(ROOT / "ssot/engos-orchestration-batman.md"),
        "candidate_sha256": artifact_hash(ROOT / "ssot/engos-orchestration-batman.md"),
    }

    with pytest.raises(ContractError, match="candidate_revision is not a repository commit"):
        UAC_IMPORT._validate_promotion_revision_bindings(
            ROOT,
            verdict,
            slug="engos-orchestration-batman",
            candidate_text=(ROOT / "ssot/engos-orchestration-batman.md").read_text(encoding="utf-8"),
            finalize_existing_candidate=True,
        )


def test_normal_baseline_to_candidate_apply_mode_remains_supported(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    ssot = repo / "ssot"
    ssot.mkdir()
    path = ssot / "engos-orchestration-batman.md"
    path.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/engos-orchestration-batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=repo, check=True, capture_output=True)
    baseline_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    baseline_sha256 = artifact_hash(path)
    path.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/engos-orchestration-batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "candidate"], cwd=repo, check=True, capture_output=True)
    candidate_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    candidate_sha256 = artifact_hash(path)
    subprocess.run(["git", "checkout", "--detach", baseline_revision], cwd=repo, check=True, capture_output=True)

    mode = UAC_IMPORT._validate_promotion_revision_bindings(
        repo,
        {
            "baseline_revision": baseline_revision,
            "candidate_revision": candidate_revision,
            "baseline_sha256": baseline_sha256,
            "candidate_sha256": candidate_sha256,
        },
        slug="engos-orchestration-batman",
        candidate_text="candidate\n",
        finalize_existing_candidate=False,
    )

    assert mode == "baseline_to_candidate"


def test_finalize_refuses_candidate_that_is_not_an_ancestor_of_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    ssot = repo / "ssot"
    ssot.mkdir()
    path = ssot / "engos-orchestration-batman.md"
    path.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/engos-orchestration-batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=repo, check=True, capture_output=True)
    baseline_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    baseline_sha256 = artifact_hash(path)
    subprocess.run(["git", "checkout", "-b", "candidate"], cwd=repo, check=True, capture_output=True)
    path.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/engos-orchestration-batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "candidate"], cwd=repo, check=True, capture_output=True)
    candidate_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    candidate_sha256 = artifact_hash(path)
    subprocess.run(["git", "checkout", "main"], cwd=repo, check=True, capture_output=True)
    (repo / "other.txt").write_text("divergent\n", encoding="utf-8")
    subprocess.run(["git", "add", "other.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "divergent"], cwd=repo, check=True, capture_output=True)
    path.write_text("candidate\n", encoding="utf-8")

    with pytest.raises(ContractError, match="candidate_revision is not an ancestor of HEAD"):
        UAC_IMPORT._validate_promotion_revision_bindings(
            repo,
            {
                "baseline_revision": baseline_revision,
                "candidate_revision": candidate_revision,
                "baseline_sha256": baseline_sha256,
                "candidate_sha256": candidate_sha256,
            },
            slug="engos-orchestration-batman",
            candidate_text="candidate\n",
            finalize_existing_candidate=True,
        )


def test_finalize_refuses_candidate_present_only_as_a_dirty_worktree_edit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    ssot = repo / "ssot"
    ssot.mkdir()
    path = ssot / "engos-orchestration-batman.md"
    path.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/engos-orchestration-batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=repo, check=True, capture_output=True)
    baseline_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    baseline_sha256 = artifact_hash(path)
    path.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/engos-orchestration-batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "candidate"], cwd=repo, check=True, capture_output=True)
    candidate_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    candidate_sha256 = artifact_hash(path)
    path.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/engos-orchestration-batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "revert candidate"], cwd=repo, check=True, capture_output=True)
    path.write_text("candidate\n", encoding="utf-8")

    with pytest.raises(ContractError, match="HEAD canonical SSOT does not equal the candidate hash"):
        UAC_IMPORT._validate_promotion_revision_bindings(
            repo,
            {
                "baseline_revision": baseline_revision,
                "candidate_revision": candidate_revision,
                "baseline_sha256": baseline_sha256,
                "candidate_sha256": candidate_sha256,
            },
            slug="engos-orchestration-batman",
            candidate_text="candidate\n",
            finalize_existing_candidate=True,
        )


def test_invalid_promotion_verdict_refusal_is_an_exact_noop(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".DS_Store"),
    )
    verdict_path = tmp_path / "invalid-verdict.json"
    verdict_path.write_text('{"schema_version":"PromotionVerdict.v1"}\n', encoding="utf-8")
    before = {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    original_root = UAC_IMPORT.ROOT
    try:
        UAC_IMPORT.ROOT = workspace
        result = UAC_IMPORT._apply_payload(
            {
                "status": "accepted",
                "source": {"normalized_source": str(workspace / "ssot/engos-orchestration-batman.md")},
                "cross_analysis": {"fit_assessment": "fits_cleanly"},
                "manifest": {"slug": "engos-orchestration-batman"},
            },
            SimpleNamespace(
                promotion_verdict=verdict_path,
                promotion_trust_root=workspace / "evals/trust-root.json",
                finalize_existing_candidate=True,
                yes=True,
                quality_loop="off",
            ),
            [str(workspace / "ssot/engos-orchestration-batman.md")],
        )
    finally:
        UAC_IMPORT.ROOT = original_root
    after = {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    assert result["status"] == "stale_evidence"
    assert "requires PromotionVerdict.v2" in result["detail"]
    assert after == before


def test_blocked_promoted_baseline_materialization_is_an_exact_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".DS_Store"),
    )
    baseline_path = workspace / "sources/ssot-baselines/engos-orchestration-batman/baseline.md"
    baseline_path.parent.mkdir(parents=True)
    baseline_path.write_text("\n".join(f"## Section {index}\n- Required behavior {index}" for index in range(100)) + "\n", encoding="utf-8")
    registry_path = workspace / "sources/ssot-baselines/index.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["skills"]["engos-orchestration-batman"] = {
        "strategy": "source_library",
        "group": "applied_baseline",
        "baseline_path": "sources/ssot-baselines/engos-orchestration-batman/baseline.md",
    }
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    verdict_path = tmp_path / "promotion-verdict.json"
    verdict_path.write_text(
        json.dumps(
            {
                "schema_version": "PromotionVerdict.v2",
                "slug": "engos-orchestration-batman",
                "status": "promote",
                "candidate_sha256": artifact_hash("thin candidate\n"),
                "candidate_revision": "b" * 40,
                "goal_contract_sha256": "c" * 64,
                "topology_sha256": "d" * 64,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    before = {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    original_root = UAC_IMPORT.ROOT
    try:
        UAC_IMPORT.ROOT = workspace
        monkeypatch.setattr(UAC_IMPORT, "validate_promotion_verdict", lambda *args, **kwargs: None)
        monkeypatch.setattr(
            UAC_IMPORT,
            "_validate_promotion_revision_bindings",
            lambda *args, **kwargs: "finalize_existing_candidate",
        )
        monkeypatch.setattr(
            UAC_IMPORT,
            "_safe_apply_ssot_text",
            lambda *args, **kwargs: ("thin candidate\n", {}),
        )
        result = UAC_IMPORT._apply_payload(
            {
                "status": "accepted",
                "source": {"normalized_source": str(workspace / "ssot/engos-orchestration-batman.md")},
                "cross_analysis": {"fit_assessment": "fits_cleanly"},
                "manifest": {
                    "slug": "engos-orchestration-batman",
                    "layers": {
                        "minimal": {
                            "capability_type": "both",
                            "summary": "Batman",
                            "required_inputs": [],
                            "expected_outputs": [],
                        },
                        "expanded": {"adjustment_recommendations": []},
                    },
                },
                "quality_result": {"status": "structural_ready"},
                "benchmark_sources": [],
            },
            SimpleNamespace(
                promotion_verdict=verdict_path,
                promotion_trust_root=workspace / "trust-root.json",
                finalize_existing_candidate=True,
                approved_trust_policy_sha256="e" * 64,
                approved_trust_policy_revision="f" * 40,
                yes=True,
                quality_loop="off",
            ),
            [str(workspace / "ssot/engos-orchestration-batman.md")],
        )
    finally:
        UAC_IMPORT.ROOT = original_root
    after = {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    assert result["status"] == "stale_evidence"
    assert "baseline materialization" in result["detail"]
    assert after == before


def test_baseline_materialization_refuses_if_preflight_state_changes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    baseline = root / "sources/ssot-baselines/engos-orchestration-batman/baseline.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("original\n", encoding="utf-8")
    index = root / "sources/ssot-baselines/index.json"
    index.write_text(
        json.dumps(
            {
                "version": "uac-baseline-sources.v1",
                "skills": {
                    "engos-orchestration-batman": {
                        "baseline_path": "sources/ssot-baselines/engos-orchestration-batman/baseline.md",
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    preflight = UAC_IMPORT.preview_source_baseline(
        root,
        slug="engos-orchestration-batman",
        baseline_text="promoted candidate\n",
    )
    baseline.write_text("concurrent change\n", encoding="utf-8")
    before = {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}

    with pytest.raises(ValueError, match="changed after preflight"):
        UAC_IMPORT.persist_source_baseline(
            root,
            slug="engos-orchestration-batman",
            baseline_text="promoted candidate\n",
            preflight=preflight,
        )

    after = {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    assert after == before


def test_uac_promotion_toctou_refusal_leaves_entire_workspace_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".DS_Store"),
    )
    candidate_text = "\n".join(
        f"## Section {index}\n- Required behavior {index}" for index in range(100)
    ) + "\n"
    baseline_path = workspace / "sources/ssot-baselines/engos-orchestration-batman/baseline.md"
    baseline_path.parent.mkdir(parents=True)
    baseline_path.write_text(candidate_text, encoding="utf-8")
    registry_path = workspace / "sources/ssot-baselines/index.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["skills"]["engos-orchestration-batman"] = {
        "strategy": "source_library",
        "group": "applied_baseline",
        "baseline_path": "sources/ssot-baselines/engos-orchestration-batman/baseline.md",
    }
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    verdict_path = tmp_path / "promotion-verdict.json"
    verdict_path.write_text(
        json.dumps(
            {
                "schema_version": "PromotionVerdict.v2",
                "slug": "engos-orchestration-batman",
                "status": "promote",
                "candidate_sha256": artifact_hash(candidate_text),
                "candidate_revision": "b" * 40,
                "goal_contract_sha256": "c" * 64,
                "topology_sha256": "d" * 64,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    before = {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }
    real_persist = UAC_IMPORT.persist_source_baseline

    def inject_observed_drift(*args, **kwargs):
        stale_preflight = dict(kwargs["preflight"])
        stale_preflight["existing_sha256"] = "0" * 64
        return real_persist(*args, **{**kwargs, "preflight": stale_preflight})

    original_root = UAC_IMPORT.ROOT
    try:
        UAC_IMPORT.ROOT = workspace
        monkeypatch.setattr(UAC_IMPORT, "validate_promotion_verdict", lambda *args, **kwargs: None)
        monkeypatch.setattr(
            UAC_IMPORT,
            "_validate_promotion_revision_bindings",
            lambda *args, **kwargs: "finalize_existing_candidate",
        )
        monkeypatch.setattr(
            UAC_IMPORT,
            "_safe_apply_ssot_text",
            lambda *args, **kwargs: (candidate_text, {}),
        )
        monkeypatch.setattr(UAC_IMPORT, "persist_source_baseline", inject_observed_drift)
        result = UAC_IMPORT._apply_payload(
            {
                "status": "accepted",
                "source": {"normalized_source": str(workspace / "ssot/engos-orchestration-batman.md")},
                "cross_analysis": {"fit_assessment": "fits_cleanly"},
                "manifest": {
                    "slug": "engos-orchestration-batman",
                    "layers": {
                        "minimal": {
                            "capability_type": "both",
                            "summary": "Batman",
                            "required_inputs": [],
                            "expected_outputs": [],
                        },
                        "expanded": {"adjustment_recommendations": []},
                    },
                },
                "quality_result": {"status": "structural_ready"},
                "benchmark_sources": [],
            },
            SimpleNamespace(
                promotion_verdict=verdict_path,
                promotion_trust_root=workspace / "trust-root.json",
                finalize_existing_candidate=True,
                approved_trust_policy_sha256="e" * 64,
                approved_trust_policy_revision="f" * 40,
                yes=True,
                quality_loop="off",
            ),
            [str(workspace / "ssot/engos-orchestration-batman.md")],
        )
    finally:
        UAC_IMPORT.ROOT = original_root
    after = {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    assert result["status"] == "stale_evidence"
    assert "changed after preflight" in result["detail"]
    assert after == before


def test_promotion_descriptor_fields_persist_status_and_evidence() -> None:
    verdict = {
        "status": "promote",
        "run_id": "run-primary",
        "baseline_revision": "a" * 40,
        "candidate_revision": "b" * 40,
        "run_manifest_sha256": "1" * 64,
        "evaluation_policy_sha256": "2" * 64,
        "impact_plan_sha256": "3" * 64,
        "evaluator_sha256": "4" * 64,
        "trust_root_sha256": "5" * 64,
        "issued_at": "2026-08-27T12:00:00Z",
        "expires_at": "2026-08-28T12:00:00Z",
    }

    fields = UAC_IMPORT._promotion_descriptor_fields(verdict)

    assert fields["behavioral_status"] == "promote"
    assert fields["promotion_evidence"]["candidate_revision"] == "b" * 40
    assert fields["promotion_evidence"]["run_manifest_sha256"] == "1" * 64
    assert "signature" not in fields["promotion_evidence"]


def test_promote_compile_check_never_writes_human_reviewed_contracts(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def fake_compile(repo_root, slug, *, write=False):
        calls.append(write)
        return {
            "status": "structural_ready",
            "topology": {"ssot_sha256": "a" * 64},
            "goal_contract": {"review_status": "human_reviewed"},
        }

    monkeypatch.setattr(UAC_IMPORT, "compile_skill", fake_compile)

    result = UAC_IMPORT._compile_applied_skill(ROOT, "engos-orchestration-batman", promotion=True)

    assert result["status"] == "structural_ready"
    assert calls == [False]


@pytest.mark.parametrize("removed_mode", [None, "system-design"])
def test_resource_backed_same_slug_uac_preserves_modes_in_apply_and_preview(tmp_path, monkeypatch, removed_mode):
    import copy
    slug = 'engos-design-architecture'
    # Copy actual declaration syntax and rich canonical curation independently.
    # Declaring only API cannot justify retaining three undeclared product modes.
    architecture = (ROOT / 'ssot' / f'{slug}.md').read_text()
    selection = architecture.split('## Mode Selection\n', 1)[1].split('## Standard Workflow', 1)[0]
    if removed_mode:
        selection = selection.split('### `system-design`', 1)[0]
    text = f'---\nname: {slug}\n---\n# Architecture\n## Mode Selection\n' + selection
    ssot = tmp_path / 'ssot' / f'{slug}.md'
    ssot.parent.mkdir()
    ssot.write_text(text)
    resources = tmp_path / 'sources/capability-resources' / slug
    resources.mkdir(parents=True)
    (resources / 'resource-map.json').write_text(json.dumps({'schema_version': 'CapabilityResourceMap.v1', 'shared': [], 'routes': {'context': ['guide.md']}, 'dependencies': {}}))
    (resources / 'guide.md').write_text('## Module: /current\nCurrent resource context.\n')
    curated = json.loads((ROOT / '.meta/capabilities' / f'{slug}.json').read_text())['modes']
    assert [m['mode_slug'] for m in curated] == ['design-api', 'design-database', 'design-patterns', 'system-design']
    stale = copy.deepcopy(curated)
    for mode in stale:
        mode.update(source_refs=['stale-source'], source_line=999, invocations=['/stale'])
    undeclared = copy.deepcopy(stale[0])
    undeclared.update(mode_slug='undeclared-mode', display_name='Undeclared Mode')
    existing = {'slug': slug, 'modes': stale + [undeclared, {'entry_kind': 'module', 'mode_slug': 'stale'}],
                'job_contract': {'keep': 'curated job'}}
    monkeypatch.setattr(UAC_IMPORT, 'ROOT', tmp_path)
    monkeypatch.setattr(UAC_IMPORT, 'load_descriptor', lambda root, name: copy.deepcopy(existing))
    quality = {'final_candidate_text': text, 'status': 'structural_ready'}
    merged, bound = UAC_IMPORT._merge_existing_descriptor_for_apply(slug, {'modes': []}, ssot_text=text, quality_result=quality)
    assert bound
    current = [m for m in merged['modes'] if m['entry_kind'] == 'mode']
    expected = [m for m in curated if m['mode_slug'] != removed_mode]
    assert [(m['mode_slug'], m['display_name']) for m in current] == [(m['mode_slug'], m['display_name']) for m in expected]
    for actual, prior in zip(current, expected, strict=True):
        for field in ('mode_summary', 'required_inputs', 'expected_outputs', 'examples', 'uplift_notes'):
            assert actual[field] == prior[field]
        assert actual['source_refs'] == [f'ssot/{slug}.md']
        assert actual['source_line'] == text.splitlines().index('### `' + actual['mode_slug'] + '`') + 1
        assert actual['invocations'] == []
    assert not {'undeclared-mode', 'stale'} & {m['mode_slug'] for m in merged['modes']}
    if removed_mode:
        assert removed_mode not in {m['mode_slug'] for m in merged['modes']}
    modules = [m for m in merged['modes'] if m['entry_kind'] == 'module']
    assert [m['mode_slug'] for m in modules] == ['current']
    assert modules[0]['source_refs'] == [f'sources/capability-resources/{slug}/guide.md']
    assert modules[0]['invocations'] == ['/current']
    assert merged['job_contract'] == existing['job_contract']
    # Exercise real preview and applied merge, then exact descriptor replay.
    monkeypatch.setattr(UAC_IMPORT, '_preferred_ssot_text', lambda *args, **kwargs: text)
    monkeypatch.setattr(UAC_IMPORT, '_routing_job_for_text', lambda *args: existing['job_contract'])
    payload = {'manifest': {'slug': slug, 'layers': {'minimal': {'summary': 'Architecture'}}}, 'items': []}
    preview, _ = UAC_IMPORT._build_descriptor_preview(payload, quality_result=quality)
    assert preview['modes'] == merged['modes']
    existing = copy.deepcopy(merged)
    replay, replay_bound = UAC_IMPORT._merge_existing_descriptor_for_apply(slug, {'modes': []}, ssot_text=text, quality_result=quality)
    assert replay_bound and replay == merged
