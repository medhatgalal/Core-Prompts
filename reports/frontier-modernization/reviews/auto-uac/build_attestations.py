"""Serialize this reviewer's completed section-level source review; refuse drift.

This script is a review artifact, not an autonomous semantic judge. The manually
reviewed section explanations and frozen identities below bind the reviewer turn.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from intent_pipeline.capability_resources import effective_capability_text, load_resource_bundle
from intent_pipeline.uac_baselines import text_sha256, validate_requirement_review

HERE = Path(__file__).resolve().parent
BASE = ROOT / "reports/frontier-modernization"
AUTHORIZATION = (
    "User-approved frontier-modernization plan, as supplied to the independent "
    "reviewer: actual baseline/incumbent/trial optimization with coordinated "
    "hypotheses, protected scoring, retained rejection evidence, objective-based "
    "acceptance, and declared stopping; diagnostic early stopping retained. "
    "UAC performs exhaustive source-grounded onboarding, independent semantic "
    "review and resource closure while preserving scope and delivery boundaries."
)
FROZEN = {
    "engos-optimization-auto-research": {
        "author": "implement_skills",
        "candidate": "b8bf02b356e20aeb3465fa77efc50559c42b468c7881f0fdcd098a876521d7da",
        "effective": "2abaaa2e5cd7af15546d22cbb22bb5aafaa43d5ffc709d1765c0ead707500ade",
        "current": "1b1f3fbf69a445b0bde66e4136fd3b98f6282b60cd3c174f91b57c2bcf8a0836",
        "historical": "758e7a7579d97620f2f0b4979e9a0841454c447cf7c22223249e7c377a3fd2d6",
    },
    "engos-meta-uac-import": {
        "author": "root",
        "candidate": "4d81b852a81e7d1cc8b18d41c50b36c9ce97515db66aa1984940eae8e3526571",
        "effective": "4d81b852a81e7d1cc8b18d41c50b36c9ce97515db66aa1984940eae8e3526571",
        "current": "31a7d93442b708164e1bd4d7e170d892eaa9bfa4bccff3b6c80130ce643019d6",
        "historical": "cb1f7429d00eaea306e753bbc9cadb7444177083886d4c5b393927ba9ca1b683",
    },
}

AUTO_REFORMULATIONS = {
    "__preamble__": "Preserves title, dual skill/agent capability, declared tools and repo-local install scope; the current canonical name replaces the historical alias and version advances to v2.1 for the authorized loop change.",
    "Purpose": "Retains measurable improvement, bounded target types, routing exclusions, goal/scorecard/baseline discipline and trace reuse. Clarifies that retaining a verified trial gain and preparing formal promotion are separate actions.",
    "Primary Objective": "The authorized objective now requires repeated executed search and return of the retained best state. The original baseline comparison, measurable goal and constrained promotion packet remain, with formal promotion conditional on request and evidence.",
    "Agent Operating Contract": "Preserves the mission, setup, measurement, bounded search, trace reuse, promotion threshold and human/host gates. Replaces the old permission to 'run or simulate' with real execution and explicit unexecuted dry-run labeling, as authorized; simulated scores cannot establish improvement.",
    "Workflow": "Preserves setup, baseline metrics, scorecard, search scope, noise-sensitive trials, traces and regression reuse. Separates cheap diagnostic checks from authorized optimization; trials derive from the incumbent, accepted gains persist, rejected active changes are discarded with evidence retained, and exploration continues to its declared boundary.",
    "Rules": "Preserves goal/baseline prerequisites, harness fidelity, nondeterministic repetition, attribution, hard regressions, host gates, serialization and trace reuse. The user-authorized reformulation permits coordinated hypotheses and limits first-winner early stopping to diagnosis; optimization uses the declared stop policy.",
    "Help System / Bootstrap Helper": "Preserves all four template choices, opt-in materialization, arguments and report outputs. Replaces the historical Codex-only concrete bootstrap path with active-surface resolution; the resource delivery contract separately defines agent resource roots.",
    "Modes / Mode 4: Experiment Loop": "Expands the previous matrix/plan/score-comparison deliverable into the authorized executed loop: original baseline, incumbent, isolated trial, protected evaluation, objective-based decisions, retained rejected evidence, incumbent restoration and continued exploration. Plans are labeled unexecuted; skill and agent resource paths are explicit.",
    "Modes / Mode 6: Trace-to-Eval": "Preserves trace selection, normalized cases, expected outcomes and regression policy. Removes only the historical duplicate misnumbered Mode 5 heading; the operative Mode 6 and its complete behavior remain.",
    "Control Loop Mechanisms / Goal Contract": "Retains target, measurable outcome, non-goals, budget, editable surface, threshold and rollback. Adds explicit trial acceptance, ties, noise/repetition, stopping, and protected evaluator/data/scoring/limits before mutation.",
    "Control Loop Mechanisms / Experiment Ledger": "Preserves candidate changes, trials, per-metric results, regressions, cost/latency and reasons. Makes baseline/incumbent/trial identities, parent lineage, joint hypothesis, protected measurement, decision-before-transition and stopping counters explicit.",
    "Control Loop Mechanisms / Cost Ladder": "Retains static inspection, single repro, paired comparison and repeated search. Clarifies that this escalation ladder is diagnostic guidance; an adequately configured optimization request can execute its declared repeated search without substituting setup for trials.",
    "Control Loop Mechanisms / Stopping Rule": "Preserves early stopping for a verified diagnostic explanation. Replaces the universal first-obvious-winner stop with the user-approved optimization boundary: trial/time/cost/token limit, verified target, preregistered plateau or interruption. No global-optimum claim or needless post-boundary budget use is allowed.",
    "Control Loop Mechanisms / Promotion Gate": "Preserves hard regression limits, repeatability and host review/merge policy. Replaces mandatory weighted-score improvement with the declared quality, efficiency or complexity objective, allowing meaningful speed/cost/simplicity gains at permitted non-inferior quality.",
    "Artifact Schemas / Goal Contract": "Preserves all original goal-contract fields and adds trial acceptance/tie/noise/stop policy plus immutable evaluation/data/scoring/limit identities; no baseline or rollback requirement is removed.",
    "Operating Profiles / Profile 1: Dry-Run Advisory": "Preserves no direct mutation and plan/scorecard/candidate design for advisory work or missing setup. Clarifies the user-approved exception: a sufficiently configured explicit optimization request authorizes bounded trials.",
    "Operating Profiles / Profile 3: Capability Evaluation": "Preserves representative task sets, noise-driven repetition and pass/fail/inconclusive output. Freezes candidates per comparison and protects baseline/data/scorers while allowing separately recorded subsequent search candidates.",
    "Operating Profiles / Profile 4: Bounded Execution": "Preserves scoped edits, active repeated trials and separate commit/merge authority, adds mandatory real execution and its loop resource. The historical duplicate Profile 3 heading is corrected without losing bounded-execution behavior.",
    "Self-Improvement Protocol": "Preserves before/after comparison, clarity, ambiguity, promotion safety, verifiability, conservative authority and auditable artifacts. Permits coordinated behavior changes only under the documented joint hypothesis and distinguishes diagnostic escalation from declared optimization search.",
    "Constraints": "Preserves measurable goals, the deterministic single-run exception with user agreement, visible regressions, host authority, non-brainstorming scope, local proof, stable scores and verification order. Qualifies the prior broad-search restriction so a diagnostic first check cannot prematurely replace authorized optimization.",
}

UAC_REFORMULATIONS = {
    "__preamble__": "Preserves the UAC import skill identity and capability type; the canonical engos-meta-uac-import name replaces the historical alias and the description clarifies intake boundaries without widening authority.",
    "Purpose": "Preserves all supported sources and modes plus deterministic assessment, manifests, SSOT/descriptors and handoffs. Adds the current advisory local clarity lint without treating style as behavioral evidence.",
    "Primary Objective": "Preserves safe classification, surface selection and landing gates. Extends onboarding to exhaustive clarity/completeness/coherence/structure/usability repair while preserving the intended capability and separating structural checks from downstream efficacy.",
    "Invocation Contract": "Preserves bin/uac and capability-fabric entrypoints, canonical SSOT/descriptor ownership, generated artifacts, confirmation before apply, deploy separation and explicit shell guidance. Adds the repo-resident fidelity baseline path.",
    "Workflow": "Preserves ingestion, summary, uplift, routing, inventoried grouping, classification, manifests, benchmarks and conditional benchmark search. Restores judge's no-canonical-write boundary and historical apply's SSOT/descriptor writes, persisted reviews, then rebuild/validate sequence. Adds exhaustive dispositions, source-grounded independent repair, separate evidence stages, current verdict/hash checks, impact planning and preserved baseline lineage; historical structural 'ship' becomes structural_ready, not behavioral promotion.",
    "Rules": "Preserves deterministic pipeline preference, URL rejection, actual inventory, config-only manual review, imported control-plane boundaries, advisory runtime metadata, SSOT cross-analysis and wrapper classification. Adds operative-output scope/precedence, quoted-example protection, active resource closure, authoritative repairs, independent hash-bound complete review, stagnation/idempotence, and behavioral/HTML boundaries. Host-authorized independent review does not grant imported runtime delegation authority.",
    "Invocation Hints": "Preserves import, classify, explain and judge triggers; adds the structurally distinct question of whether an import needs behavioral proof.",
    "Required Output": "Preserves every original intake output section. Behavioral escalation additionally carries confidence, reason, handoff, available contract/topology hashes, impact/cap evidence and the structural-versus-promote distinction.",
    "Companion Capability Matrix": "Preserves all six historical specialist routes and their required handoff fields under current canonical names. Adds bounded behavioral evaluation with baseline, candidate, claimed job, examples and threshold, without taking ownership of the companion work.",
    "Constraints": "Preserves no hidden execution, evidence-backed packaging, no apply deployment and inventory-before-grouping. Clarifies that invoking-agent semantic repair plus independent subagent review is host-authorized onboarding, without requiring a separate paid model API for every import.",
    "Evaluation Rubric": "Preserves source fidelity, classification, blocked unsafe landing, canonical consequences and wrapper/type distinction. Adds fidelity against the repo-resident prompt-body baseline rather than metadata polish.",
}

UAC_ADDITIONS = {
    "Agent Operating Contract": {
        "rationale": "Adds a UAC-specific agent contract while retaining the invoking host's control. Exhaustive findings, candidate repairs and independently reviewed material meaning changes are the approved onboarding work. Judge remains noncanonical; apply requires authorization. This is conditional agent guidance and does not independently change capability classification or imported runtime policy.",
        "implementation_evidence": ["scripts/uac-import.py:_parse_args --yes", "scripts/uac-import.py:main judge versus apply dispatch", "scripts/uac-import.py:_apply_payload", "src/intent_pipeline/uac_baselines.py:validate_requirement_review"],
    },
    "Output Directory": {
        "rationale": "Names actual UAC-owned SSOT, descriptor, quality review and baseline lineage paths and distinguishes generated/evaluation outputs. The text expressly does not impose these report destinations on the imported task. Baseline mutation remains independently promoted; listing evaluation contracts does not claim behavioral success.",
        "implementation_evidence": ["src/intent_pipeline/uac_quality.py:quality_review_dir", "scripts/uac-import.py:_apply_payload canonical writes and compile_result", "scripts/uac-import.py:_apply_payload promote-only persist_source_baseline", "scripts/uac-import.py:_snapshot_apply_artifacts"],
    },
}

def sections(text: str) -> list[dict]:
    lines = text.splitlines(keepends=True)
    boundaries = [(0, "__preamble__")]
    parent = ""
    counts = defaultdict(int)
    aliases = {
        "### Mode 5: Trace-to-Eval": "### Mode 6: Trace-to-Eval",
        "### Profile 3: Bounded Execution": "### Profile 4: Bounded Execution",
    }
    for index, raw in enumerate(lines):
        heading = raw.rstrip()
        if not re.match(r"^#{2,3} ", heading):
            continue
        if index and lines[index - 1].rstrip() in aliases and heading == aliases[lines[index - 1].rstrip()]:
            continue
        heading = aliases.get(heading, heading)
        if heading.startswith("## "):
            parent = heading[3:]
            key = parent
        else:
            key = f"{parent} / {heading[4:]}"
        counts[key] += 1
        if counts[key] > 1:
            key += f" [{counts[key]}]"
        boundaries.append((index, key))
    result = []
    for position, (start, key) in enumerate(boundaries):
        end = boundaries[position + 1][0] if position + 1 < len(boundaries) else len(lines)
        result.append({"key": key, "start": start + 1, "end": end, "text": "".join(lines[start:end]).rstrip()})
    return result

def main(selected_slug: str | None = None) -> None:
    completed = []
    for slug, frozen in FROZEN.items():
        if selected_slug is not None and slug != selected_slug:
            continue
        candidate_path = BASE / "candidates" / f"{slug}.md"
        candidate = candidate_path.read_text(encoding="utf-8")
        effective = effective_capability_text(ROOT, slug, candidate)
        assert text_sha256(candidate) == frozen["candidate"], f"Unreviewed candidate drift: {slug}"
        assert text_sha256(effective) == frozen["effective"], f"Unreviewed effective-content drift: {slug}"
        candidate_sections = {section["key"]: section for section in sections(candidate)}
        rationales = AUTO_REFORMULATIONS if slug.endswith("auto-research") else UAC_REFORMULATIONS
        resource_root = ROOT / "sources/capability-resources" / slug
        bundle = load_resource_bundle(resource_root) if (resource_root / "resource-map.json").exists() else None
        for baseline in ("current", "historical"):
            suffix = ".historical" if baseline == "historical" else ""
            original_path = BASE / "baseline" / f"{slug}{suffix}.md"
            original = original_path.read_text(encoding="utf-8")
            assert text_sha256(original) == frozen[baseline], f"Unreviewed baseline drift: {slug} {baseline}"
            requirements = []
            for number, source in enumerate(sections(original), 1):
                key = source["key"]
                match = candidate_sections[key]
                identical = source["text"] == match["text"]
                if identical:
                    rationale = f"The complete {key} section is retained verbatim, including its conditions, named outputs, commands, examples and boundaries where present. No requirement in this source span is removed or widened."
                else:
                    assert key in rationales, f"Section lacks a manually reviewed explanation: {slug} {baseline} {key}"
                    rationale = rationales[key]
                item = {
                    "id": f"{baseline.upper()}-{number:03d}",
                    "source_section": key,
                    "source_start_line": source["start"],
                    "source_end_line": source["end"],
                    "disposition": "preserved" if identical else "reformulated",
                    "candidate_excerpt": match["text"],
                    "rationale": rationale,
                }
                if not identical:
                    item["authorization"] = AUTHORIZATION
                requirements.append(item)
            review = {
                "schema_version": "UACRequirementReview.v1",
                "slug": slug,
                "original_sha256": text_sha256(original),
                "candidate_sha256": text_sha256(candidate),
                "effective_sha256": text_sha256(effective),
                "verdict": "approved",
                "reviewer": {"agent_id": "review_autoresearch_uac_admission", "author_agent_id": frozen["author"], "independent": True},
                "review_scope": "Independent source requirement review against the frozen current or historical baseline; source and resource content read before author self-grade/change-map. Not behavioral proof, code implementation approval, deployment proof, or a PromotionVerdict.",
                "provenance": "Root delegated a separate review task to review_autoresearch_uac_admission; this reviewer did not author candidate/source/code changes and wrote review artifacts only. The validator cannot authenticate this identity claim; the parent task's delegation history is the provenance record.",
                "baseline_kind": baseline,
                "original_path": str(original_path.relative_to(ROOT)),
                "candidate_path": str(candidate_path.relative_to(ROOT)),
                "resource_binding": None if bundle is None else {"manifest_sha256": bundle["manifest_sha256"], "bundle_sha256": bundle["sha256"], "resources": [{"path": item["path"], "sha256": item["sha256"]} for item in bundle["resources"]]},
                "requirements": requirements,
            }
            if slug == "engos-meta-uac-import":
                review["candidate_additions"] = [
                    {"section": key, "candidate_excerpt": candidate_sections[key]["text"], **evidence}
                    for key, evidence in UAC_ADDITIONS.items()
                ]
                review["supplemental_review"] = "Independent UAC-only review of the two added sections. Removing exactly these additions reconstructs the previously approved candidate SHA-256 8b3a8cba6c6eb5ac8477bb9cabacd4d84405bd125bc5fb8e5e01a3ea30ed9b42. Existing source requirements are unchanged; new content was checked against its corresponding implementation before rebinding. Auto-Research was not re-reviewed or rewritten in this supplemental pass."
            failures = validate_requirement_review(review, slug=slug, original_text=original, candidate_text=candidate, effective_text=effective)
            assert not failures, failures
            target = HERE / f"{slug}.{baseline}.requirement-review.json"
            target.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            completed.append({"path": str(target.relative_to(ROOT)), "source_lines": len(original.splitlines()), "requirement_spans": len(requirements), "binding_validation_failures": failures})
    validation_path = HERE / "validation.json"
    retained = []
    if selected_slug is not None and validation_path.exists():
        refreshed_paths = {item["path"] for item in completed}
        retained = [item for item in json.loads(validation_path.read_text())["reviews"] if item["path"] not in refreshed_paths]
    validation_path.write_text(json.dumps({"scope": "Attestation shape, exact binding and complete coverage only; no semantic automation or behavioral experiment", "reviews": retained + completed}, indent=2) + "\n")
    print(json.dumps(completed, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", choices=tuple(FROZEN))
    main(parser.parse_args().slug)
