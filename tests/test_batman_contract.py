from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMER_ALIAS = "super" + "man"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _dynamic_planning_violations(scenario: dict, observed: dict) -> list[str]:
    violations: list[str] = []
    gold = scenario["gold_result"]
    expected_keys = set(gold)
    observed_keys = set(observed)
    for key in sorted(expected_keys - observed_keys):
        violations.append(f"missing field: {key}")
    for key in sorted(observed_keys - expected_keys):
        violations.append(f"prohibited extra field: {key}")
    for key in sorted(expected_keys & observed_keys):
        if observed[key] != gold[key]:
            violations.append(f"{key}: expected {gold[key]!r}, got {observed[key]!r}")

    scenario_id = scenario["id"]
    if scenario_id == "complete-host-fit-plan":
        if observed.get("waived_gates") != []:
            violations.append("dynamic planning waived a gate")
        if observed.get("authority_delta") != []:
            violations.append("dynamic planning expanded authority")
        if observed.get("verified_facilities_only") is not True:
            violations.append("dynamic planning used an unverified facility")
    elif scenario_id == "incomplete-inventory-degrades":
        if observed.get("live_writes") != "prohibited":
            violations.append("incomplete inventory allowed live writes")
        if observed.get("implementation_mode") != "sequential":
            violations.append("incomplete inventory did not degrade to sequential implementation")
    elif scenario_id == "required-gate-facility-stops":
        if observed.get("action") != "stop":
            violations.append("missing required gate facility did not stop")
    elif scenario_id == "one-word-integrity":
        if observed.get("tdd_before_review") is not False or observed.get("fabricated_authority") is not False:
            violations.append("one-word input bypassed integrity review")
    elif scenario_id == "test-provenance":
        if observed.get("evidence_bearing_author") != "fresh_implementer":
            violations.append("evidence-bearing test was not authored independently")
        if observed.get("unchanged_adoption_counts_as_red") is not False:
            violations.append("unchanged controller-authored test counted as observed red")
    elif scenario_id == "offline-live-proof":
        if observed.get("live_verified") is not False or observed.get("action") != "refuse_live_claim":
            violations.append("offline evidence was reported as live proof")
    elif scenario_id == "cleanup-preserves-receipt":
        if observed.get("scratch_deleted") is not False:
            violations.append("only live receipt was deleted")
    elif scenario_id == "one-surface":
        if len(observed.get("canonical_identities", [])) != 1:
            violations.append("public operation has more than one canonical identity")
    elif scenario_id == "capability-nesting":
        if not observed.get("existing_job"):
            violations.append("capability was not nested under an existing job")
    elif scenario_id == "walk-up-interface":
        if observed.get("opaque_id_required") is not False:
            violations.append("walk-up interface requires an opaque ID")
    elif scenario_id == "typed-cli-errors":
        expected_codes = {"absence", "permission", "rate_limit", "outage"}
        if set(observed.get("codes", {})) != expected_codes or observed.get("prose_only") is not False:
            violations.append("agent-consumed CLI errors are not typed")
    else:
        violations.append(f"unknown scenario: {scenario_id}")
    return violations


def _assert_dynamic_mutation_detected(scenario: dict, observed: dict) -> None:
    violations = _dynamic_planning_violations(scenario, observed)
    if not violations:
        raise AssertionError("mutation produced no contract violation")


class BatmanContractTests(unittest.TestCase):
    def test_batman_is_subagent_driven_implementation_not_parent_authorship(self) -> None:
        text = _read("ssot/batman.md")
        self.assertIn("Batman delivers implementation through independent subagents", text)
        self.assertIn("The controller must not author production code, failing tests, or implementation fixes.", text)
        self.assertIn("Skipping implementation means Batman did not run.", text)

    def test_batman_has_four_blocking_milestone_review_gates(self) -> None:
        text = _read("ssot/batman.md")
        self.assertIn("All four milestone gates are blocking.", text)
        self.assertEqual(
            re.findall(r"^\| [1-4] \|", text, flags=re.MULTILINE),
            ["| 1 |", "| 2 |", "| 3 |", "| 4 |"],
        )
        for milestone in ("Scope", "Design readiness", "Task implementation", "Landing readiness"):
            self.assertIn(milestone, text)
        self.assertIn("a fresh reviewer role brief independent of the design author", text)
        self.assertIn("Every applicable milestone gate reviews its declared evidence and blocks downstream work on failure.", text)
        self.assertNotIn("All four milestone gates review the actual saved revision or diff", text)

    def test_batman_landing_gate_follows_pr_and_hosted_ci(self) -> None:
        text = _read("ssot/batman.md")
        stage_six = text.split("### Stage 6 — Document, land, and clean", 1)[1].split("\n## Rules", 1)[0]
        ordered_steps = (
            "Update documentation and examples",
            "Open a scoped PR or MR",
            "Verify current hosted CI",
            "Run milestone gate 4",
            "When landing is authorized, merge",
        )
        positions = [stage_six.index(step) for step in ordered_steps]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("fresh documentation and GitOps reviewer role briefs", stage_six)
        self.assertIn("fresh adversarial reviewer role brief applies `supercharge /adversarial`", stage_six)

    def test_batman_progress_reporting_is_event_driven_and_time_bounded(self) -> None:
        text = _read("ssot/batman.md")
        for trigger in (
            "initial status immediately after preflight",
            "stage status at every stage transition",
            "blocker status immediately when a blocker appears",
            "heartbeat status every 15 minutes during long-running work",
        ):
            self.assertIn(trigger, text)
        self.assertIn("against the written delivery plan", text)

    def test_batman_is_portable_and_has_one_active_identity(self) -> None:
        text = _read("ssot/batman.md")
        supercharge = _read("ssot/supercharge.md")
        fixture = _read("evals/fixtures/supercharge/module-preservation.json")
        self.assertNotIn(FORMER_ALIAS, text.lower())
        self.assertFalse((ROOT / "evals/fixtures/batman/alias-microflow.json").exists())
        self.assertIn("Use only the host's subagent mechanism", text)
        self.assertIn("Core-Prompts companions available in the active installation and named in this contract", text)
        for companion in (
            "architecture", "auto-research", "supercharge", "converge", "testing",
            "code-review", "address-code-review", "docs-review-expert", "gitops-review",
        ):
            self.assertIn(f"- `{companion}`", text)
        for term in ("WorkGraph", "workgraph-jira", "globally installed", "orchestrate_subagent", "Grok", "Kiro"):
            self.assertNotIn(term, text)
        self.assertNotIn("repository-local Core-Prompts companions", text)
        self.assertIsNone(re.search(r"\b(?:PT|AT)\b", text))
        self.assertIsNone(re.search(r"/Users/|~/|https?://", text))
        self.assertIn("Internal milestone findings return to the original implementer or a bounded default fixer.", text)
        self.assertIn("Use `address-code-review` only for selected comments on an existing PR or MR.", text)
        self.assertIn("all applicable milestone gates", text)
        self.assertNotIn("## MODULE: /batman", supercharge)
        self.assertNotIn('"heading": "## MODULE: /batman"', fixture)

    def test_instruction_integrity_precedes_implementation(self) -> None:
        text = _read("ssot/batman.md")
        integrity = text.split("## Instruction Integrity", 1)[1].split("\n## ", 1)[0]
        for field in ("outcome", "success evidence", "scope", "authority", "contradictions"):
            self.assertIn(field, integrity)
        self.assertIn("one-word work-item key", integrity)
        self.assertIn("never fabricate intent", integrity)
        self.assertIn("stop", integrity)

    def test_dynamic_planning_is_between_preflight_and_size_and_cannot_waive_gates(self) -> None:
        text = _read("ssot/batman.md")
        preflight = text.index("### Preflight — Verify and dispatch")
        planning = text.index("### Dynamic Planning — Fit the verified host")
        size = text.index("### Size gate")
        self.assertLess(preflight, planning)
        self.assertLess(planning, size)
        planner = text[planning:size]
        for field in (
            "selected companions and resolution paths", "independent parallel work and dependencies",
            "bounded expert briefs", "cheapest valid path", "higher-assurance path",
            "missing-facility degradations", "cost, quality, and speed ranking",
        ):
            self.assertIn(field, planner)
        self.assertIn("not a second controller", planner)
        self.assertIn("must not waive or reorder gates", planner)
        self.assertIn("must not expand authority", planner)
        self.assertIn("Use only verified facilities", planner)
        self.assertIn("use sequential implementation", planner)
        self.assertIn("stop only when a facility required by the current gate", planner)

    def test_dynamic_planning_discovers_repository_verification_and_budgets(self) -> None:
        text = _read("ssot/batman.md")
        planner = text.split("### Dynamic Planning — Fit the verified host", 1)[1].split("### Size gate", 1)[0]
        for term in (
            "repository languages",
            "build, test, lint, type, smoke, package, CI, deploy, and release commands",
            "time, agent-call, token, and cost budgets",
            "mark missing budgets `unknown`",
        ):
            self.assertIn(term, planner)

    def test_fresh_implementer_owns_test_provenance_and_red(self) -> None:
        text = _read("ssot/batman.md")
        stage_three = text.split("### Stage 3 — TDD-led subagent implementation", 1)[1].split("### Stage 4", 1)[0]
        self.assertIn("Prior-session or controller-authored tests are dirty input", stage_three)
        self.assertIn("fresh implementer", stage_three)
        self.assertIn("recorded unfixed revision", stage_three)
        self.assertIn("freshly observe the intended failure", stage_three)
        self.assertIn("revise, rewrite, or discard it", stage_three)
        self.assertIn("cannot satisfy observed-red evidence unchanged", stage_three)
        self.assertIn("inspect and validate it only to decide whether to revise, rewrite, or discard", stage_three)
        self.assertIn("must author the evidence-bearing version independently", stage_three)

    def test_stalled_implementation_is_narrowed_or_reassigned_not_taken_over(self) -> None:
        text = _read("ssot/batman.md")
        self.assertIn("narrow or reassign the task to a fresh implementer", text)
        self.assertIn("The controller never takes over the task.", text)

    def test_offline_suite_is_not_live_ship_proof(self) -> None:
        text = _read("ssot/batman.md")
        stage_four = text.split("### Stage 4 — Validation and verification", 1)[1].split("### Stage 5", 1)[0]
        self.assertIn("An offline suite is necessary but not sufficient", stage_four)
        self.assertIn("Name the authorized live environment", stage_four)
        self.assertIn("refuse the live claim", stage_four)
        self.assertIn("do not substitute offline tests", stage_four)

    def test_conditional_interface_and_evidence_rules_are_explicit(self) -> None:
        text = _read("ssot/batman.md")
        rules = text.split("## Conditional Interface and Evidence Rules", 1)[1].split("\n## Milestone Backpressure", 1)[0]
        for clause in (
            "one canonical identity per public operation", "under an existing job",
            "three options with A/B/C variants", "bound project context or readable names",
            "durable or run-scoped", "absence, permission, rate limit, and outage",
            "stable machine-readable codes",
        ):
            self.assertIn(clause, rules)

    def test_cleanup_receipt_preserves_durable_facts_before_scratch_removal(self) -> None:
        text = _read("ssot/batman.md")
        stage_six = text.split("### Stage 6 — Document, land, and clean", 1)[1].split("\n## Rules", 1)[0]
        self.assertIn("Persist required run-scoped facts durably", stage_six)
        self.assertIn("Never delete the only live receipt", stage_six)
        self.assertIn("exact removed and retained targets", stage_six)

    def test_post_merge_delivery_actions_are_authority_gated_and_reported_separately(self) -> None:
        text = _read("ssot/batman.md")
        required_output = text.split("## Required Output", 1)[1].split("\n## Output Directory", 1)[0]
        stage_six = text.split("### Stage 6 — Document, land, and clean", 1)[1].split("\n## Rules", 1)[0]

        for action in ("tag", "package release", "deployment", "installation"):
            self.assertIn(action, required_output)
            self.assertIn(action, stage_six)
        for state in ("actual", "skipped", "refused"):
            self.assertIn(state, required_output)
            self.assertIn(state, stage_six)
        release = stage_six.index("tag, package release, deployment, and installation")
        persist = stage_six.index("Persist required run-scoped facts durably")
        cleanup = stage_six.index("Remove only authorized run-scoped scratch")
        self.assertLess(release, persist)
        self.assertLess(persist, cleanup)
        self.assertIn("separately authorized", stage_six)
        self.assertIn("record its receipt", stage_six)

    def test_dynamic_planning_maintenance_assets_cover_gold_and_mutations(self) -> None:
        scenarios = json.loads(_read("evals/maintenance/batman/dynamic-planning.json"))
        mutations = json.loads(_read("evals/maintenance/batman/dynamic-planning-mutations.json"))
        self.assertEqual(
            set(scenarios),
            {"schema_version", "slug", "promotion_eligible", "model_calls", "purpose", "scenarios"},
        )
        self.assertEqual(scenarios["schema_version"], "BatmanDynamicPlanningMaintenance.v2")
        self.assertFalse(scenarios["promotion_eligible"])
        self.assertEqual(scenarios["model_calls"], 0)
        self.assertEqual(
            set(mutations),
            {"schema_version", "slug", "promotion_eligible", "source_fixture", "mutations"},
        )
        self.assertEqual(mutations["schema_version"], "BatmanDynamicPlanningMutations.v2")
        self.assertFalse(mutations["promotion_eligible"])
        self.assertEqual(mutations["source_fixture"], "evals/maintenance/batman/dynamic-planning.json")
        scenario_ids = {scenario["id"] for scenario in scenarios["scenarios"]}
        mutation_classes = {mutation["class"] for mutation in mutations["mutations"]}
        self.assertTrue({
            "complete-host-fit-plan", "incomplete-inventory-degrades",
            "required-gate-facility-stops", "one-word-integrity", "test-provenance",
            "offline-live-proof", "cleanup-preserves-receipt", "one-surface",
            "capability-nesting", "walk-up-interface", "typed-cli-errors",
        }.issubset(scenario_ids))
        self.assertTrue({
            "planner_waives_gate", "planner_expands_authority", "unverified_facility_used",
            "controller_test_treated_as_red", "offline_claimed_live", "cleanup_receipt_deleted",
            "dual_public_surface", "capability_not_nested", "opaque_id_walk_up",
            "prose_only_cli_errors",
        }.issubset(mutation_classes))
        prohibited_extras = {
            "unverified_facility_used": "unverified_facility_used",
            "controller_test_treated_as_red": "controller_authored_test_accepted",
            "offline_claimed_live": "claimed_live",
            "cleanup_receipt_deleted": "deleted_only_live_receipt",
        }
        for mutation in mutations["mutations"]:
            self.assertEqual(set(mutation), {"id", "class", "scenario_id", "observed_result"})
            scenario_id = mutation["scenario_id"]
            self.assertIn(scenario_id, scenario_ids)
            scenario = next(item for item in scenarios["scenarios"] if item["id"] == scenario_id)
            self.assertTrue(_dynamic_planning_violations(scenario, mutation["observed_result"]))
            known_differences = sum(
                mutation["observed_result"].get(key) != expected
                for key, expected in scenario["gold_result"].items()
            )
            extra_fields = set(mutation["observed_result"]) - set(scenario["gold_result"])
            missing_fields = set(scenario["gold_result"]) - set(mutation["observed_result"])
            self.assertEqual(known_differences + len(extra_fields), 1)
            self.assertEqual(missing_fields, set())
            expected_extra = prohibited_extras.get(mutation["class"])
            self.assertEqual(extra_fields, {expected_extra} if expected_extra else set())

        for scenario in scenarios["scenarios"]:
            scenario_keys = set(scenario)
            common_keys = {"id", "allowed_result_fields", "gold_result"}
            context_keys = scenario_keys - common_keys
            self.assertEqual(len(context_keys), 1)
            self.assertTrue(context_keys.issubset({"inventory", "request", "input", "evidence"}))
            self.assertEqual(_dynamic_planning_violations(scenario, scenario["gold_result"]), [])
            self.assertEqual(set(scenario["gold_result"]), set(scenario["allowed_result_fields"]))

    def test_gold_identical_dynamic_planning_mutation_is_rejected(self) -> None:
        scenarios = json.loads(_read("evals/maintenance/batman/dynamic-planning.json"))["scenarios"]
        scenario = next(item for item in scenarios if item["id"] == "complete-host-fit-plan")

        with self.assertRaisesRegex(AssertionError, "mutation produced no contract violation"):
            _assert_dynamic_mutation_detected(scenario, scenario["gold_result"])

    def test_archive_is_immutable_and_non_promoting(self) -> None:
        manifest = json.loads(_read("evals/history/batman/e602e19/manifest.json"))
        historical = _read("evals/history/batman/e602e19/ssot/batman.md")
        self.assertTrue(manifest["archive_only"])
        self.assertFalse(manifest["auto_discovery"])
        self.assertFalse(manifest["promotion_eligible"])
        self.assertIn(FORMER_ALIAS, historical.lower())

    def test_batman_job_map_and_benchmark_are_ship_ready(self) -> None:
        job_map = json.loads(_read(".meta/skill-job-map.json"))["skills"]["batman"]
        benchmark = _read(".planning/initiatives/capability-review-pilots/BENCHMARK-MATRIX.md")
        self.assertEqual(job_map["shape"], "implementation_delivery_controller")
        self.assertEqual(job_map["portfolio_action"], "ship_single_batman_identity")
        self.assertNotIn(FORMER_ALIAS, json.dumps(job_map).lower())
        self.assertNotIn("draft", " ".join(str(value) for value in job_map.values()).lower())
        self.assertNotIn("pending", " ".join(str(value) for value in job_map.values()).lower())
        self.assertIn("| batman | 5 | 5 | 5 | 5 | 5 | 5 | 5 | structural_ready |", benchmark)
        self.assertNotIn(FORMER_ALIAS, benchmark.lower())


if __name__ == "__main__":
    unittest.main()
