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


def test_finalize_existing_candidate_requires_exact_revision_hashes_and_ancestry() -> None:
    baseline_revision = _revision("22654fb")
    candidate_revision = _revision("6be4830")
    verdict = {
        "slug": "batman",
        "baseline_revision": baseline_revision,
        "candidate_revision": candidate_revision,
        "baseline_sha256": "ac7e2684d99dc6a0267d785d1a6751a742e39e74ce3853a9877f98051690b3f2",
        "candidate_sha256": artifact_hash(ROOT / "ssot/batman.md"),
    }

    mode = UAC_IMPORT._validate_promotion_revision_bindings(
        ROOT,
        verdict,
        slug="batman",
        candidate_text=(ROOT / "ssot/batman.md").read_text(encoding="utf-8"),
        finalize_existing_candidate=True,
    )

    assert mode == "finalize_existing_candidate"


def test_finalize_existing_candidate_refuses_non_ancestor_candidate() -> None:
    verdict = {
        "slug": "batman",
        "baseline_revision": _revision("22654fb"),
        "candidate_revision": "0" * 40,
        "baseline_sha256": "ac7e2684d99dc6a0267d785d1a6751a742e39e74ce3853a9877f98051690b3f2",
        "candidate_sha256": artifact_hash(ROOT / "ssot/batman.md"),
    }

    with pytest.raises(ContractError, match="candidate_revision is not a repository commit"):
        UAC_IMPORT._validate_promotion_revision_bindings(
            ROOT,
            verdict,
            slug="batman",
            candidate_text=(ROOT / "ssot/batman.md").read_text(encoding="utf-8"),
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
    path = ssot / "batman.md"
    path.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=repo, check=True, capture_output=True)
    baseline_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    baseline_sha256 = artifact_hash(path)
    path.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/batman.md"], cwd=repo, check=True)
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
        slug="batman",
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
    path = ssot / "batman.md"
    path.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=repo, check=True, capture_output=True)
    baseline_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    baseline_sha256 = artifact_hash(path)
    subprocess.run(["git", "checkout", "-b", "candidate"], cwd=repo, check=True, capture_output=True)
    path.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/batman.md"], cwd=repo, check=True)
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
            slug="batman",
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
    path = ssot / "batman.md"
    path.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=repo, check=True, capture_output=True)
    baseline_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    baseline_sha256 = artifact_hash(path)
    path.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/batman.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "candidate"], cwd=repo, check=True, capture_output=True)
    candidate_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    candidate_sha256 = artifact_hash(path)
    path.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "ssot/batman.md"], cwd=repo, check=True)
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
            slug="batman",
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
                "source": {"normalized_source": str(workspace / "ssot/batman.md")},
                "cross_analysis": {"fit_assessment": "fits_cleanly"},
                "manifest": {"slug": "batman"},
            },
            SimpleNamespace(
                promotion_verdict=verdict_path,
                promotion_trust_root=workspace / "evals/trust-root.json",
                finalize_existing_candidate=True,
                yes=True,
                quality_loop="off",
            ),
            [str(workspace / "ssot/batman.md")],
        )
    finally:
        UAC_IMPORT.ROOT = original_root
    after = {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    assert result["status"] == "stale_evidence"
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

    result = UAC_IMPORT._compile_applied_skill(ROOT, "batman", promotion=True)

    assert result["status"] == "structural_ready"
    assert calls == [False]
