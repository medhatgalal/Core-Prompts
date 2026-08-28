from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "evals/history/batman/e602e19"

FROZEN_ARTIFACTS = {
    "ssot/batman.md": "3f649676d77fad3ef73e068bd0b8544c7511b696dd2511b73b2835f136da8ca1",
    "evals/contracts/batman.json": "1316f9882c27b9f8247514c78b5a16f8a400f91b9f40de2d393969ffd5c33e8f",
    "evals/topologies/batman.json": "98691d7f04d8dec8b72b13ca23ab0bb51317aa99723b483d3c519bb1cf3191ec",
    "evals/reviews/batman.json": "be9612621e9d30421fd293d5f9cbd05ab171690c34850a3a320c064de11e9261",
    "evals/mutations/batman.json": "66b61af1839d57f3d4eb0b2fbaf5a23f4e9cf6cb0f9b52c19fb57a35f2b4a808",
    "evals/scorers/batman.json": "627d7f0ccacdfa0a65cf32ec4b767ee95d37257bb84a4e298a3d62f717c85597",
    "evals/mappings/batman-baseline-to-candidate.json": "8ec04b9743e0b69f500ef7324b510fa20cc6f7607c12a9ac897fc6039b11a88c",
    "evals/preregistrations/batman-promotion.json": "798182ec3b362447cdcaa0454d5a558fc858bfeaf9cd776de301615ca447ab6c",
    "evals/cases/public/batman/core.jsonl": "77d2c21dae2011354462096e7a3adb2cee6067fad0dffe6f0d6c4c94c2845b7b",
    "evals/fixtures/batman/alias-microflow.json": "be3d67e6fe9a83f92ed4a4938376a19a99da3098777d113a0e31be3e8c34d710",
    "evals/fixtures/batman/implementation-microflow.json": "3a1132a9549311ab03f3155704f1869793205a5969e26d60f219350bf5bc4989",
    "evals/fixtures/batman/landing-microflow.json": "13ad353352f65adf4be7567ae47e56eb8fce770f26652c073a875f3d98cd9924",
    "evals/fixtures/batman/review-microflow.json": "0b583ff8d052ac7dcab35ba4542dba882c380ecbedbebab4d7894df42727f948",
    "evals/fixtures/batman/status-microflow.json": "59c8658fc6b0b5b697235bbad663e28f850f3aecae748bf7be707cca73b5ce10",
    "src/core_prompts_eval/scorers/batman.py": "c56f4ca78267da2f16690985b19ed5013033979bc9975801b24bd24adc5b2279",
}

ABSTRACT_ROLE_BRIEFS = {
    "context researcher",
    "challenger",
    "designer",
    "implementer",
    "reviewer",
    "attacker",
    "adversarial reviewer",
    "fixer",
}

STALE_ACTIVE_PROMOTION_ARTIFACTS = (
    "evals/mutations/batman.json",
    "evals/scorers/batman.json",
    "evals/mappings/batman-baseline-to-candidate.json",
    "evals/preregistrations/batman-promotion.json",
    "evals/cases/public/batman/core.jsonl",
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_closed_world_archive(root: Path, allowed: set[str]) -> None:
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    unexpected = sorted(actual - allowed)
    missing = sorted(allowed - actual)
    assert not unexpected and not missing, f"unexpected={unexpected}; missing={missing}"


def _expected_dispatch(scenario: dict) -> dict:
    capability = scenario["request"]["capability"]
    role_brief = scenario["request"]["role_brief"]
    usable_agents = set(scenario["inventory"]["usable_registered_agents"])
    installed_skills = set(scenario["inventory"]["installed_skills"])

    if capability in usable_agents:
        return {
            "action": "registered_agent",
            "agent": capability,
            "apply_skill": None,
            "role_brief": role_brief,
            "dependent_outcome": "proceed",
        }
    if capability in installed_skills:
        return {
            "action": "default_independent_subagent",
            "agent": "default",
            "apply_skill": capability,
            "role_brief": role_brief,
            "dependent_outcome": "proceed",
        }
    return {
        "action": "stop",
        "agent": None,
        "apply_skill": None,
        "role_brief": role_brief,
        "dependent_outcome": "stop",
    }


def _dispatch_violations(scenario: dict, observed: dict) -> list[str]:
    violations: list[str] = []
    expected = _expected_dispatch(scenario)
    for key, value in expected.items():
        if observed.get(key) != value:
            violations.append(f"{key}: expected {value!r}, got {observed.get(key)!r}")

    if observed.get("authority_delta") != []:
        violations.append("resolution changed authority")

    context_id = observed.get("context_id")
    if observed.get("action") != "stop":
        if observed.get("fresh_context") is not True:
            violations.append("dispatch context is not fresh")
        if context_id in scenario["inventory"]["prior_context_ids"]:
            violations.append("dispatch reused a prior context")
    elif context_id is not None:
        violations.append("stop outcome created a context")

    if observed.get("role_is_registry_slug") is not False:
        violations.append("role brief was treated as a registry slug")
    return violations


def test_companion_names_resolve_as_capabilities_not_assumed_agent_slugs() -> None:
    text = _read("ssot/batman.md")

    assert "Companion names are capability identities, not guaranteed agent registrations." in text
    registered = text.index("usable registered agent for that capability")
    fallback = text.index("fresh default independent subagent")
    missing = text.index("stop the dependent stage or gate")
    assert registered < fallback < missing
    assert "apply the installed skill with the same capability name" in text

    for ambiguous_dispatch in (
        r"fresh `code-review` subagent",
        r"Dispatch `code-review`",
        r"fresh `docs-review-expert`",
    ):
        assert re.search(ambiguous_dispatch, text) is None


def test_companion_resolution_is_authority_neutral_and_fail_closed() -> None:
    text = _read("ssot/batman.md")

    assert (
        "Companion resolution grants no write, review, merge, deploy, cleanup, or other authority."
        in text
    )
    assert "Existing approval and role-separation boundaries remain unchanged." in text
    assert "If neither surface is available, stop the dependent stage or gate" in text


def test_abstract_seats_are_role_briefs_not_registry_slugs() -> None:
    text = _read("ssot/batman.md")

    assert (
        "Context researcher, challenger, designer, implementer, reviewer, attacker, adversarial "
        "reviewer, and fixer are role briefs, not agent registry slugs."
    ) in text
    assert (
        "fresh adversarial reviewer role brief applies `supercharge /adversarial` through the "
        "companion resolution rule"
    ) in text


def test_companion_call_sites_reference_one_resolution_rule_and_examples_remain_end_to_end() -> None:
    text = _read("ssot/batman.md")
    examples = _read("docs/EXAMPLES.md")

    assert "through companion resolution" not in text
    assert text.count("through the companion resolution rule") >= 10
    assert "### Skills-only companion fallback\n> Batman: implement" in text
    portable_example = examples.split("Portable companion ask:", 1)[1].split("\nExpected output:", 1)[0]
    assert "> Batman: implement" in portable_example
    assert "review-only" not in portable_example


def test_maintenance_fixture_covers_resolution_freshness_authority_and_mutations() -> None:
    fixture = _json("evals/maintenance/batman/companion-dispatch.json")
    inventory = _json("evals/maintenance/batman/companion-dispatch-mutations.json")

    assert fixture["schema_version"] == "BatmanCompanionDispatchMaintenance.v1"
    assert fixture["promotion_eligible"] is False
    assert fixture["model_calls"] == 0
    scenarios = {scenario["id"]: scenario for scenario in fixture["scenarios"]}
    assert {
        "registered-agent-preferred",
        "installed-skill-fallback",
        "registered-agent-unusable-skill-fallback",
        "missing-capability-stops",
        "fresh-reviewer-fallback",
    } <= scenarios.keys()
    assert {scenario["request"]["role_brief"] for scenario in scenarios.values()} <= ABSTRACT_ROLE_BRIEFS
    assert all(not _dispatch_violations(scenario, scenario["gold_result"]) for scenario in scenarios.values())

    assert inventory["schema_version"] == "BatmanCompanionDispatchMutations.v1"
    assert inventory["promotion_eligible"] is False
    assert inventory["source_fixture"] == "evals/maintenance/batman/companion-dispatch.json"
    assert {
        "capability_assumed_agent",
        "skill_fallback_skipped",
        "default_without_named_skill",
        "controller_applies_skill_directly",
        "missing_both_continues",
        "authority_expansion",
        "abstract_role_as_slug",
        "stale_context_reuse",
    } == {mutation["class"] for mutation in inventory["mutations"]}
    assert all(
        _dispatch_violations(scenarios[mutation["scenario_id"]], mutation["observed_result"])
        for mutation in inventory["mutations"]
    )


def test_released_e602e19_evidence_is_archived_byte_identically_and_non_promoting() -> None:
    manifest = json.loads((HISTORY / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "BatmanHistoricalEvidence.v1"
    assert manifest["candidate_commit"] == "e602e19c757b7e0c9ac81fc9f89730ecdf3ba237"
    assert manifest["archive_only"] is True
    assert manifest["auto_discovery"] is False
    assert manifest["promotion_eligible"] is False
    assert {artifact["source"]: artifact["sha256"] for artifact in manifest["artifacts"]} == FROZEN_ARTIFACTS
    _assert_closed_world_archive(HISTORY, {"manifest.json", *FROZEN_ARTIFACTS})

    for source, expected_hash in FROZEN_ARTIFACTS.items():
        archived = HISTORY / source
        assert archived.is_file(), source
        assert _sha256(archived) == expected_hash


def test_historical_archive_closed_world_rejects_an_unexpected_file(tmp_path: Path) -> None:
    archive = tmp_path / "history"
    expected = archive / "ssot/batman.md"
    expected.parent.mkdir(parents=True)
    expected.write_text("frozen\n", encoding="utf-8")
    (archive / "manifest.json").write_text("{}\n", encoding="utf-8")
    (archive / "unexpected.txt").write_text("residue\n", encoding="utf-8")

    with pytest.raises(AssertionError, match=r"unexpected\.txt"):
        _assert_closed_world_archive(archive, {"manifest.json", "ssot/batman.md"})


def _is_absent_or_machine_disabled(path: Path) -> bool:
    if not path.exists():
        return True
    if path.suffix != ".json":
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("active") is False and payload.get("promotion_eligible") is False


def test_stale_active_promotion_artifacts_are_absent_or_machine_disabled() -> None:
    stale = [path for path in STALE_ACTIVE_PROMOTION_ARTIFACTS if not _is_absent_or_machine_disabled(ROOT / path)]
    assert stale == []
