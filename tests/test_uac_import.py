from __future__ import annotations

import json
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "uac-import.py"
SPEC = importlib.util.spec_from_file_location("uac_import_script", SCRIPT_PATH)
assert SPEC and SPEC.loader
UAC_IMPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UAC_IMPORT)
BOOTSTRAP_SOURCE_PATH = ROOT / "sources" / "capability-resources" / "autosearch" / "bootstrap.py"


def test_uac_import_local_file_flow(tmp_path: Path) -> None:
    sample = tmp_path / "prompt.md"
    sample.write_text(
        """# API Design\n\nPrimary Objective: Produce a reusable API design prompt.\n\nIn Scope:\n- Normalize endpoint requirements\n- Preserve acceptance criteria\n\nOut of Scope:\n- Live API calls\n\nConstraints:\n- Deterministic output only\n""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--source", str(sample), "--benchmark-search", "off"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "accepted"
    assert payload["uac"]["capability_type"] == "skill"
    assert payload["uac"]["recommended_surface"] == "skill"
    assert payload["source"]["normalized_source"] == str(sample.resolve())
    assert payload["routing"]["decision"] in {"PASS_ROUTE", "NEEDS_REVIEW"}
    assert "manifest" in payload
    assert "cross_analysis" in payload
    assert payload["handoff_contract"]["advisory_only"] is True


def test_uac_import_respects_target_system_override(tmp_path: Path) -> None:
    sample = tmp_path / "prompt.md"
    sample.write_text(
        """Primary Objective: Normalize this prompt.\n\nIn Scope:\n- Package for Codex\n\nConstraints:\n- Deterministic output only\n""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "uac-import.py"),
            "--source",
            str(sample),
            "--target-system",
            "codex",
            "--benchmark-search",
            "off",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["recommendation"]["primary_target_systems"] == ["codex"]
    assert payload["recommendation"]["install_target"]["recommended"] in {"repo_local", "global", "both"}


def test_uac_import_local_directory_flow(tmp_path: Path) -> None:
    (tmp_path / "design-api.toml").write_text(
        'prompt = """Primary Objective: Design an API prompt.\n\nIn Scope:\n- Request contracts\n\nConstraints:\n- Deterministic\n"""\n',
        encoding="utf-8",
    )
    (tmp_path / "system-design.toml").write_text(
        'prompt = """Primary Objective: Design a system prompt.\n\nIn Scope:\n- Architecture review\n\nConstraints:\n- Explicit trade-offs\n"""\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--source", str(tmp_path), "--benchmark-search", "off", "--use-repomix", "off"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "accepted"
    assert payload["source"]["type"] == "LOCAL_DIRECTORY"
    assert payload["collection"]["collection_type"] == "skill_family"
    assert payload["items"][0]["extraction"]["wrapper_kind"] == "toml_prompt"
    assert len(payload["items"]) == 2
    assert payload["manifest"]["layers"]["minimal"]["install_target"]["recommended"] in {"repo_local", "global", "both"}


def test_uac_import_clusters_mixed_repo_candidates(tmp_path: Path) -> None:
    architecture_dir = tmp_path / "commands" / "architecture"
    testing_dir = tmp_path / "commands" / "testing"
    architecture_dir.mkdir(parents=True)
    testing_dir.mkdir(parents=True)
    (architecture_dir / "design-api.toml").write_text(
        'prompt = """Primary Objective: Design APIs.\n\nIn Scope:\n- Interfaces\n\nConstraints:\n- Deterministic\n"""\n',
        encoding="utf-8",
    )
    (testing_dir / "generate-unit-tests.toml").write_text(
        'prompt = """Primary Objective: Generate unit tests.\n\nIn Scope:\n- Test cases\n\nConstraints:\n- Deterministic\n"""\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "uac-import.py"),
            "--mode",
            "plan",
            "--source",
            str(tmp_path),
            "--benchmark-search",
            "off",
            "--use-repomix",
            "off",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["source"]["cluster_count"] == 2
    cluster_slugs = {cluster["slug"] for cluster in payload["clusters"]}
    assert {"architecture", "testing"} <= cluster_slugs
    assert payload["plan"]["action"] == "narrow to one family before apply"
    assert payload["quality_plan"]["quality_profile"] == "default"


def test_uac_judge_returns_quality_plan_and_result(tmp_path: Path) -> None:
    sample = tmp_path / "architecture.md"
    sample.write_text(
        """# Architecture\n\nPrimary Objective: Design a reusable architecture prompt.\n\nIn Scope:\n- API design\n- database design\n\nConstraints:\n- deterministic output only\n- rollback required\n""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "uac-import.py"),
            "--mode",
            "judge",
            "--source",
            str(sample),
            "--quality-profile",
            "architecture",
            "--benchmark-search",
            "off",
            "--use-repomix",
            "off",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["mode"] == "judge"
    assert payload["quality_plan"]["quality_profile"] == "architecture"
    assert "historical_baseline" in payload["quality_plan"]
    assert "validation_matrix" in payload["quality_plan"]
    assert payload["quality_result"]["status"] in {"ship", "revise", "manual_review"}
    assert "historical_baseline" in payload["quality_result"]
    assert len(payload["quality_result"]["judge_reports"]) >= 1


def test_uac_import_can_emit_rubric(tmp_path: Path) -> None:
    sample = tmp_path / "prompt.md"
    sample.write_text(
        """Primary Objective: Normalize this prompt.\n\nIn Scope:\n- Package for Codex\n\nConstraints:\n- Deterministic output only\n""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--source", str(sample), "--show-rubric", "--benchmark-search", "off"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert "classification_rubric" in payload
    assert "skill" in payload["classification_rubric"]
    assert "agent" in payload["classification_rubric"]


def test_uac_import_audit_mode_returns_table_and_items() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--mode", "audit"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["mode"] == "audit"
    assert "audit_table" in payload
    assert payload["summary"]["entry_count"] >= 1
    assert payload["handoff_contract"]["advisory_only"] is True


def test_uac_import_explain_mode_returns_deployment_matrix() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--mode", "explain"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["mode"] == "explain"
    assert "deployment_matrix" in payload
    assert "both" in payload["deployment_matrix"]["capability_types"]


def test_uac_apply_writes_ssot_and_descriptor_in_workspace_copy(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns('.git', '.pytest_cache', '__pycache__', '.DS_Store', '.venv', 'node_modules'),
    )
    sample = tmp_path / "capability-fabric-sample.md"
    sample.write_text(
        """# Capability Fabric Sample

Purpose: Provide a canonical sample capability that demonstrates deterministic UAC landing.

Primary Objective: Create a canonical capability-fabric sample skill that imports cleanly, produces deterministic metadata, and generates reusable review-ready surfaces.

Operating Contract:
- accept a single markdown source as the canonical input
- normalize the capability into repo-quality SSOT structure before landing
- emit stable metadata and generated surfaces without runtime side effects

In Scope:
- deterministic import flow
- descriptor sidecars
- generated skill surfaces
- validation-ready metadata

Out of Scope:
- live execution
- orchestration
- runtime execution control

Required Inputs:
- one markdown source file
- benchmark references from architecture and code-review

Required Output:
- a canonical SSOT entry
- descriptor metadata
- generated surfaces
- a validation-ready build result

Examples:
- Given a thin external prompt, rewrite it into a repo-grade capability with explicit boundaries.
- Produce metadata that explains expected outputs and install target.

Evaluation Rubric:
- title clarity
- description richness
- intent coverage
- boundary clarity
- output specificity
- metadata completeness
- surface usability

Constraints:
- Deterministic output only
- Advisory-only behavior unless the caller explicitly requests execution
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(workspace / "scripts" / "uac-import.py"),
            "--mode",
            "apply",
            "--source",
            str(sample),
            "--yes",
            "--benchmark-search",
            "off",
            "--use-repomix",
            "off",
        ],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "applied"
    slug = payload["plan"]["proposed_ssot_slug"]
    assert (workspace / "ssot" / f"{slug}.md").is_file()
    descriptor_path = workspace / ".meta" / "capabilities" / f"{slug}.json"
    assert descriptor_path.is_file()
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    assert "historical_baseline" in descriptor
    assert "quality_validation_matrix" in descriptor
    baseline_path = workspace / descriptor["historical_baseline"]["baseline_path"]
    assert baseline_path.is_file()
    assert payload["apply_result"]["build"]["returncode"] == 0
    assert payload["apply_result"]["validate"]["returncode"] == 0


def test_uac_apply_refuses_landing_when_quality_gate_fails(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns('.git', '.pytest_cache', '__pycache__', '.DS_Store', '.venv', 'node_modules'),
    )
    sample = tmp_path / "thin-sample.md"
    sample.write_text("Short prompt.\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(workspace / "scripts" / "uac-import.py"),
            "--mode",
            "apply",
            "--source",
            str(sample),
            "--yes",
            "--benchmark-search",
            "off",
            "--use-repomix",
            "off",
        ],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "manual_review"
    assert payload["apply_result"]["quality"]["status"] in {"revise", "manual_review"}
    assert not (workspace / "ssot" / "thin-sample.md").exists()
    assert (workspace / "reports" / "quality-reviews" / payload["manifest"]["slug"] / "LATEST.md").is_file()


def test_preferred_ssot_text_preserves_complete_authored_source(tmp_path: Path) -> None:
    sample = tmp_path / "autosearch.md"
    sample.write_text(
        """---
name: "autosearch"
display_name: "Autosearch"
description: "Rich authored source."
capability_type: "both"
install_target: "repo_local"
---
# Autosearch

## Purpose
Preserve the authored body.

## Primary Objective
Keep the complete source text when it already satisfies the template.

## Agent Operating Contract
Agent contract.

## Tool Boundaries
Tool boundaries.

## Output Directory
reports/autosearch/

## Workflow
1. Freeze baseline.

## Rules
- Deterministic.

## Required Inputs
- target

## Required Output
- promotion packet

## Constraints
- No silent merge.

## Examples
### Example Request
> Improve this system.

### Example Output Shape
- Goal contract

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Source fidelity | The authored source is preserved |

## Help System
Copy-Ready Starter Invocation
""",
        encoding="utf-8",
    )

    payload = {
        "source": {"normalized_source": str(sample)},
        "manifest": {"layers": {"minimal": {"capability_type": "both"}}},
    }
    quality_result = {"final_candidate_text": "# Generic fallback\n"}

    chosen = UAC_IMPORT._preferred_ssot_text("autosearch", payload, quality_result=quality_result)

    assert "Copy-Ready Starter Invocation" in chosen
    assert "Generic fallback" not in chosen


def test_normalize_payload_for_same_slug_update_allows_judge_and_apply() -> None:
    payload = {
        "status": "accepted",
        "manifest": {
            "slug": "autosearch",
            "layers": {
                "minimal": {"capability_type": "both"},
                "expanded": {"overlap_candidates": ["autosearch"]},
            },
        },
        "uac": {"capability_type": "both"},
        "routing": {"route_profile": "IMPLEMENTATION"},
        "recommendation": {"next_actions": ["old"]},
        "cross_analysis": {
            "duplicate_risk": "high",
            "fit_assessment": "manual_review",
            "conflict_report": ["slug autosearch already exists"],
            "overlap_report": [{"slug": "autosearch", "score": 1.0, "reason": "same slug"}],
            "required_existing_adjustments": [],
            "required_new_entry_adjustments": [],
            "work_graph_change_summary": "autosearch risks duplicate or conflicting graph roles and should not auto-apply.",
        },
    }

    normalized = UAC_IMPORT._normalize_payload_for_same_slug_update(payload)

    assert normalized["cross_analysis"]["fit_assessment"] == "fits_cleanly"
    assert normalized["cross_analysis"]["conflict_report"] == []
    assert normalized["manifest"]["layers"]["expanded"]["overlap_candidates"] == []


def test_source_constraints_prefer_authored_constraints(tmp_path: Path) -> None:
    sample = tmp_path / "autosearch.md"
    sample.write_text(
        """## Constraints
- Do not auto-merge.
- Do not claim unmeasured wins.
""",
        encoding="utf-8",
    )

    payload = {"source": {"normalized_source": str(sample)}}

    assert UAC_IMPORT._source_constraints(payload) == (
        "Do not auto-merge.",
        "Do not claim unmeasured wins.",
    )


def test_autosearch_bootstrap_creates_artifacts(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports" / "autosearch"
    result = subprocess.run(
        [
            sys.executable,
            str(BOOTSTRAP_SOURCE_PATH),
            "--target",
            "review prompt",
            "--goal",
            "increase regression catch rate",
            "--editable-scope",
            "prompt body",
            "--must-not-change",
            "review authority",
            "--baseline-evidence",
            "existing eval cases",
            "--promotion-threshold",
            "higher catch rate with no added noise",
            "--report-dir",
            str(report_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    created = payload["created"]
    assert Path(created["goal_contract"]).is_file()
    assert Path(created["experiment_ledger"]).is_file()
    assert Path(created["promotion_packet"]).is_file()
    scorecard_path = Path(created["scorecard"])
    assert scorecard_path.is_file()
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
    assert scorecard["goal"] == "increase regression catch rate"


def test_build_surfaces_emits_autosearch_bootstrap_resource(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns('.git', '.pytest_cache', '__pycache__', '.DS_Store', '.venv', 'node_modules'),
    )

    subprocess.run(
        ["/opt/homebrew/bin/python3.14", str(workspace / "scripts" / "build-surfaces.py")],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )

    assert (workspace / ".codex" / "skills" / "autosearch" / "resources" / "bootstrap.py").is_file()
    assert (workspace / ".codex" / "agents" / "resources" / "autosearch" / "bootstrap.py").is_file()
    assert (workspace / ".codex" / "skills" / "autosearch" / "resources" / "templates" / "goal-contract.md.tmpl").is_file()
    assert (workspace / ".codex" / "skills" / "autosearch" / "resources" / "templates" / "scorecard.json.tmpl").is_file()
