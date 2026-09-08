"""Resource-bound evaluation input and canonical identities, not model efficacy."""
import json
from pathlib import Path

import pytest

from core_prompts_eval.contracts import artifact_hash
from core_prompts_eval.evaluator import draft_goal_contract
from core_prompts_eval.topology import compile_topology, detect_ambiguities


def package(tmp_path):
    slug = "engos-meta-supercharge"
    entry = tmp_path / "ssot" / f"{slug}.md"
    entry.parent.mkdir()
    entry.write_text("# Supercharge\n\n### Terminal-Control Precedence\n"
                     "If the user supplies more than one reflective control, ask.\n")
    resources = tmp_path / "sources/capability-resources" / slug
    (resources / "modules").mkdir(parents=True)
    (resources / "resource-map.json").write_text(json.dumps({
        "schema_version": "CapabilityResourceMap.v1", "shared": [],
        "routes": {"/grade": ["modules/grade.md"]}, "dependencies": {},
    }))
    module = resources / "modules/grade.md"
    module.write_text("## MODULE: /grade\nNever invent a trial.\n")
    return entry, module


def test_canonical_supercharge_receives_specific_outcome(tmp_path):
    package(tmp_path)
    result = draft_goal_contract(tmp_path, "engos-meta-supercharge")
    assert "downstream" in result["intended_outcome"]


def test_canonical_supercharge_checks_match_legacy_alias():
    text = "# Supercharge\nNo controls defined."
    assert detect_ambiguities("engos-meta-supercharge", text) == detect_ambiguities("supercharge", text)
    assert detect_ambiguities("engos-meta-supercharge", text)


def test_topology_covers_resource_clauses_and_binds_changes(tmp_path):
    entry, module = package(tmp_path)
    before = compile_topology(entry)
    assert any("Never invent a trial" in item["text"] for item in before["protected_invariants"])
    assert "/grade" in before["explicit_invocations"]
    assert any(item["path"].endswith("modules/grade.md") for item in before["source_references"])
    module.write_text("## MODULE: /grade\nNever invent a trial or score.\n")
    after = compile_topology(entry)
    assert before["ssot_sha256"] == after["ssot_sha256"] == artifact_hash(entry.read_text())
    assert before["resource_bundle_sha256"] != after["resource_bundle_sha256"]


def test_review_overlay_rejects_changed_resource_bundle(tmp_path):
    entry, module = package(tmp_path)
    topology = compile_topology(entry)
    review = tmp_path / "evals/reviews/engos-meta-supercharge.json"
    review.parent.mkdir(parents=True)
    review.write_text(json.dumps({
        "schema_version": "CapabilityTopologyReview.v1", "slug": "engos-meta-supercharge",
        "ssot_sha256": topology["ssot_sha256"],
        "resource_bundle_sha256": topology.get("resource_bundle_sha256", "old"),
        "clause_mappings": {}, "waivers": [], "review_status": "draft",
        "risk_tiers": {"critical": [], "high": [], "standard": [x["id"] for x in topology["protected_invariants"]]},
    }))
    module.write_text("## MODULE: /grade\nNever invent a new result.\n")
    with pytest.raises(ValueError, match="resource.*stale"):
        compile_topology(entry)
