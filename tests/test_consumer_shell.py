from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from intent_pipeline.consumer_shell import (
    ReleaseBaselineError,
    build_capability_catalog,
    build_release_delta,
    build_status_payload,
    render_catalog_markdown,
    render_release_delta_markdown,
    render_status_markdown,
    resolve_release_baseline,
)


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _write_manifest(repo: Path, summary: str) -> dict[str, object]:
    manifest = {
        "ssot_sources": [
            {
                "slug": "batman",
                "layers": {"minimal": {"summary": summary}},
            }
        ]
    }
    path = repo / ".meta/manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


def _commit_manifest(repo: Path, summary: str, message: str) -> str:
    _write_manifest(repo, summary)
    _git(repo, "add", ".meta/manifest.json")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _commit_evidence(repo: Path, message: str) -> str:
    path = repo / "release-evidence.txt"
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(f"{previous}{message}\n", encoding="utf-8")
    _git(repo, "add", "release-evidence.txt")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _entry(
    slug: str,
    *,
    display_name: str,
    summary: str,
    capability_type: str = "skill",
    supported_clis: dict[str, list[str]] | None = None,
    supported_agents: list[str] | None = None,
    invocation_hints: list[str] | None = None,
    domain_tags: list[str] | None = None,
    compatibility: str | None = None,
) -> dict[str, object]:
    return {
        "slug": slug,
        "display_name": display_name,
        "invocation_hints": invocation_hints or [],
        "quality_profile": "default",
        "quality_status": "ship",
        "layers": {
            "minimal": {
                "summary": summary,
                "capability_type": capability_type,
                "install_target": {"recommended": "repo_local"},
                "emitted_surfaces": supported_clis or {"codex": ["skill"], "claude": ["skill"]},
                "supported_agents": supported_agents or [],
                "required_inputs": ["repo context"],
                "expected_outputs": ["deterministic summary"],
                "domain_tags": domain_tags or ["analysis"],
                "compatibility": compatibility,
            },
            "expanded": {
                "overlap_candidates": [],
            },
        },
        "consumption_hints": {
            "preferred_use_cases": ["analysis"],
            "artifact_conventions": ["reports/example.md"],
            "invocation_style": "interactive",
            "requires_human_confirmation": False,
        },
        "expected_surface_names": ["codex_skill", "claude_skill"],
    }


def test_build_capability_catalog_groups_entries_for_consumers() -> None:
    manifest = {
        "ssot_sources": [
            _entry(
                "architecture",
                display_name="Architecture Studio",
                summary="Design systems and APIs.",
                capability_type="both",
                supported_clis={"codex": ["skill", "agent"], "claude": ["skill"]},
                supported_agents=["codex"],
                invocation_hints=["Use for API design."],
                domain_tags=["architecture", "analysis"],
                compatibility="codex>=0.1",
            ),
            _entry(
                "testing",
                display_name="Testing Studio",
                summary="Design test plans.",
                invocation_hints=["Use for test planning."],
                domain_tags=["testing"],
            ),
        ]
    }

    catalog = build_capability_catalog(manifest)

    assert catalog["entry_count"] == 2
    assert "architecture" in catalog["views"]["start_here"]
    assert catalog["views"]["by_cli"]["codex"] == ["architecture", "testing"]
    assert catalog["views"]["by_use_case"]["architecture"] == ["architecture"]
    assert catalog["capabilities"][0]["display_name"] == "Architecture Studio"
    rendered = render_catalog_markdown(catalog)
    assert "# Capability Catalog" in rendered
    assert "Architecture Studio" in rendered
    assert "Compatibility: codex>=0.1" in rendered


def test_build_release_delta_tracks_material_changes() -> None:
    previous = {
        "ssot_sources": [
            _entry("architecture", display_name="Architecture Studio", summary="Old summary."),
            _entry("testing-old", display_name="Old Testing", summary="Old test helper."),
        ]
    }
    current = {
        "ssot_sources": [
            _entry(
                "architecture",
                display_name="Architecture Studio",
                summary="New summary.",
                invocation_hints=["Use for migration plans."],
            ),
            _entry("testing", display_name="Testing Studio", summary="Design test plans."),
        ]
    }

    delta = build_release_delta(current, previous)

    assert delta["summary"]["new_count"] == 1
    assert delta["summary"]["material_change_count"] == 1
    assert delta["new_capabilities"] == [{"slug": "testing", "display_name": "Testing Studio"}]
    assert delta["removed_capabilities"] == [{"slug": "testing-old", "display_name": "Old Testing"}]
    assert delta["material_changes"][0]["slug"] == "architecture"
    assert "summary" in delta["material_changes"][0]["material_fields"]
    rendered = render_release_delta_markdown(delta)
    assert "# Release Delta" in rendered
    assert "`testing`" in rendered
    assert "## Removed Capabilities" in rendered
    assert "`testing-old`" in rendered


def test_build_release_delta_tracks_contract_metadata_changes() -> None:
    previous_entry = _entry(
        "presentations",
        display_name="Presentations",
        summary="Build decks.",
    )
    current_entry = _entry(
        "presentations",
        display_name="Presentations",
        summary="Build decks.",
    )
    current_entry["layers"]["minimal"]["required_inputs"].append("approved image assets")
    current_entry["shared_constraints"] = ["Use relative image paths."]
    current_entry["modes"] = [{"mode_slug": "portable-package"}]
    current_entry["consumption_hints"]["artifact_conventions"].append("<deck>/images/<asset>")

    delta = build_release_delta(
        {"ssot_sources": [current_entry]},
        {"ssot_sources": [previous_entry]},
    )

    material_fields = delta["material_changes"][0]["material_fields"]
    assert "required_inputs" in material_fields
    assert "shared_constraints" in material_fields
    assert "modes" in material_fields
    assert "artifact_conventions" in material_fields
    rendered = render_release_delta_markdown(delta)
    assert "shared_constraints" in rendered
    assert "artifact_conventions" in rendered


def test_build_status_payload_reports_health_from_validation_and_smoke() -> None:
    manifest = {"ssot_sources": [_entry("architecture", display_name="Architecture Studio", summary="Design systems.")]}
    status = build_status_payload(
        manifest,
        build_report={"generated_at": "2026-04-02T00:00:00Z"},
        validation_report={"validated_at": "2026-04-02T00:05:00Z", "validation_errors": 1, "validation_warnings": 0},
        smoke_report={"smoked_at": "2026-04-02T00:06:00Z", "failures": ["missing surface"], "warnings": []},
    )

    assert status["health"] == "error"
    assert status["entry_count"] == 1
    rendered = render_status_markdown(status)
    assert "# Consumer Status" in rendered
    assert "Overall health: `error`" in rendered


def test_build_status_payload_warns_on_smoke_warnings_without_failures() -> None:
    manifest = {"ssot_sources": [_entry("testing", display_name="Testing Studio", summary="Design tests.")]}
    status = build_status_payload(
        manifest,
        build_report={"generated_at": "2026-04-02T00:00:00Z"},
        validation_report={"validated_at": "2026-04-02T00:05:00Z", "validation_errors": 0, "validation_warnings": 0},
        smoke_report={"smoked_at": "2026-04-02T00:06:00Z", "failures": [], "warnings": ["missing optional binary"]},
    )

    assert status["health"] == "warn"


class ReleaseBaselineTests(unittest.TestCase):
    def _init_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        _git(repo, "init", "-b", "main")
        _git(repo, "config", "user.name", "Core Prompts Test")
        _git(repo, "config", "user.email", "core-prompts@example.test")
        return repo

    def _add_origin(self, root: Path, repo: Path) -> Path:
        remote = root / "origin.git"
        remote.mkdir()
        _git(remote, "init", "--bare")
        _git(repo, "remote", "add", "origin", str(remote))
        _git(repo, "push", "-u", "origin", "main")
        _git(repo, "remote", "set-head", "origin", "main")
        return remote

    def assertBasis(self, basis: str, ref: str, sha: str) -> None:
        self.assertEqual(basis, f"git:{ref}@{sha} .meta/manifest.json")

    def test_pushed_feature_tracking_itself_uses_remote_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = self._init_repo(root)
            baseline = _commit_manifest(repo, "baseline", "baseline")
            self._add_origin(root, repo)
            _git(repo, "checkout", "-b", "feature")
            _commit_manifest(repo, "batman changed", "feature change")
            _git(repo, "push", "-u", "origin", "feature")

            previous, basis = resolve_release_baseline(repo)

            self.assertEqual(previous, _write_manifest_snapshot("baseline"))
            self.assertBasis(basis, "origin/main", baseline)
            delta = build_release_delta(
                _write_manifest_snapshot("batman changed"),
                previous,
                comparison_basis=basis,
            )
            self.assertEqual(delta["comparison_basis"], basis)
            self.assertEqual(delta["summary"]["material_change_count"], 1)

    def test_merge_commit_uses_distinct_first_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            baseline = _commit_manifest(repo, "baseline", "baseline")
            _git(repo, "checkout", "-b", "feature")
            _commit_manifest(repo, "batman changed", "feature change")
            _git(repo, "checkout", "main")
            _git(repo, "merge", "--no-ff", "feature", "-m", "merge feature")

            previous, basis = resolve_release_baseline(repo)

            self.assertEqual(previous, _write_manifest_snapshot("baseline"))
            self.assertBasis(basis, "HEAD^1", baseline)

    def test_explicit_environment_ref_precedes_tags_and_branches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            baseline = _commit_manifest(repo, "baseline", "baseline")
            _git(repo, "tag", "v1.0.0")
            _commit_manifest(repo, "current", "current")

            previous, basis = resolve_release_baseline(
                repo,
                env={"CORE_PROMPTS_RELEASE_BASE_REF": baseline},
            )

            self.assertEqual(previous, _write_manifest_snapshot("baseline"))
            self.assertBasis(basis, baseline, baseline)
            previous, basis = resolve_release_baseline(
                repo,
                explicit_ref=baseline,
                env={"CORE_PROMPTS_RELEASE_BASE_REF": "does-not-exist"},
            )
            self.assertEqual(previous, _write_manifest_snapshot("baseline"))
            self.assertBasis(basis, baseline, baseline)

    def test_invalid_explicit_ref_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            _commit_manifest(repo, "current", "current")

            with self.assertRaisesRegex(ReleaseBaselineError, "explicit release baseline"):
                resolve_release_baseline(
                    repo,
                    env={"CORE_PROMPTS_RELEASE_BASE_REF": "does-not-exist"},
                )

    def test_explicit_ref_without_manifest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            (repo / "README.md").write_text("baseline\n", encoding="utf-8")
            _git(repo, "add", "README.md")
            _git(repo, "commit", "-m", "no manifest")
            no_manifest = _git(repo, "rev-parse", "HEAD")
            _commit_manifest(repo, "current", "current")

            with self.assertRaisesRegex(ReleaseBaselineError, "no valid .meta/manifest.json"):
                resolve_release_baseline(repo, explicit_ref=no_manifest)

    def test_current_tag_is_skipped_for_previous_version_tag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            baseline = _commit_manifest(repo, "baseline", "baseline")
            _git(repo, "tag", "v1.9.0")
            current = _commit_manifest(repo, "current", "current")
            _git(repo, "tag", "v1.10.0")

            previous, basis = resolve_release_baseline(repo)

            self.assertNotEqual(current, baseline)
            self.assertEqual(previous, _write_manifest_snapshot("baseline"))
            self.assertBasis(basis, "v1.9.0", baseline)

    def test_pre_tag_release_uses_newest_tag_even_when_manifest_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            baseline = _commit_manifest(repo, "unchanged", "v1 baseline")
            _git(repo, "tag", "v1.0.0")
            _commit_evidence(repo, "release prep")

            previous, basis = resolve_release_baseline(repo)
            delta = build_release_delta(
                _write_manifest_snapshot("unchanged"),
                previous,
                comparison_basis=basis,
            )

            self.assertBasis(basis, "v1.0.0", baseline)
            self.assertEqual(delta["baseline_status"], "available")
            self.assertEqual(delta["summary"]["changed_count"], 0)
            self.assertEqual(delta["summary"]["material_change_count"], 0)

    def test_post_current_tag_uses_previous_tag_when_manifest_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            baseline = _commit_manifest(repo, "unchanged", "v1 baseline")
            _git(repo, "tag", "v1.0.0")
            _commit_evidence(repo, "release prep")
            _git(repo, "tag", "v1.1.0")

            previous, basis = resolve_release_baseline(repo)
            delta = build_release_delta(
                _write_manifest_snapshot("unchanged"),
                previous,
                comparison_basis=basis,
            )

            self.assertBasis(basis, "v1.0.0", baseline)
            self.assertEqual(delta["baseline_status"], "available")
            self.assertEqual(delta["summary"]["changed_count"], 0)
            self.assertEqual(delta["summary"]["material_change_count"], 0)

    def test_remote_baseline_uses_distinct_commit_when_manifest_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = self._init_repo(root)
            baseline = _commit_manifest(repo, "unchanged", "baseline")
            self._add_origin(root, repo)
            _git(repo, "checkout", "-b", "feature")
            _commit_evidence(repo, "feature evidence")
            _git(repo, "push", "-u", "origin", "feature")

            previous, basis = resolve_release_baseline(repo)
            delta = build_release_delta(
                _write_manifest_snapshot("unchanged"),
                previous,
                comparison_basis=basis,
            )

            self.assertBasis(basis, "origin/main", baseline)
            self.assertEqual(delta["baseline_status"], "available")
            self.assertEqual(delta["summary"]["changed_count"], 0)
            self.assertEqual(delta["summary"]["material_change_count"], 0)

    def test_release_prep_after_merge_uses_previous_release_tag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            baseline = _commit_manifest(repo, "baseline", "baseline")
            _git(repo, "tag", "v1.0.0")
            _git(repo, "checkout", "-b", "feature")
            _commit_manifest(repo, "batman changed", "feature change")
            _git(repo, "checkout", "main")
            _git(repo, "merge", "--no-ff", "feature", "-m", "merge feature")
            (repo / "release.txt").write_text("prepare\n", encoding="utf-8")
            _git(repo, "add", "release.txt")
            _git(repo, "commit", "-m", "release prep")

            previous, basis = resolve_release_baseline(repo)

            self.assertEqual(previous, _write_manifest_snapshot("baseline"))
            self.assertBasis(basis, "v1.0.0", baseline)

    def test_detached_multi_commit_without_trustworthy_baseline_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            _commit_manifest(repo, "baseline", "baseline")
            _commit_manifest(repo, "current", "current")
            _git(repo, "checkout", "--detach")

            previous, basis = resolve_release_baseline(repo)

            self.assertIsNone(previous)
            self.assertEqual(basis, "unavailable")

    def test_no_upstream_multi_commit_branch_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self._init_repo(Path(temp_dir))
            _commit_manifest(repo, "baseline", "baseline")
            _git(repo, "checkout", "-b", "feature")
            _commit_manifest(repo, "current", "current")

            previous, basis = resolve_release_baseline(repo)

            self.assertIsNone(previous)
            self.assertEqual(basis, "unavailable")

    def test_missing_baseline_delta_is_empty_and_explicit(self) -> None:
        current = _write_manifest_snapshot("current")

        delta = build_release_delta(current, None, comparison_basis="unavailable")

        self.assertEqual(delta["baseline_status"], "missing")
        self.assertEqual(delta["comparison_basis"], "unavailable")
        self.assertEqual(delta["new_capabilities"], [])
        self.assertEqual(delta["changed_capabilities"], [])
        self.assertEqual(delta["summary"]["new_count"], 0)

    def test_in_memory_manifest_default_is_neutral(self) -> None:
        delta = build_release_delta(
            _write_manifest_snapshot("current"),
            _write_manifest_snapshot("baseline"),
        )

        self.assertEqual(delta["baseline_status"], "available")
        self.assertEqual(delta["comparison_basis"], "provided manifest")


def _write_manifest_snapshot(summary: str) -> dict[str, object]:
    return {
        "ssot_sources": [
            {
                "slug": "batman",
                "layers": {"minimal": {"summary": summary}},
            }
        ]
    }


if __name__ == "__main__":
    unittest.main()
