# Installation lifecycle follow-up

Status: deferred proposal, not implemented. This closeout preserves evidence; it does not authorize the lifecycle upgrade, assign an implementing task, or claim release readiness for it.

Source: Codex task `01a086ee-c457-7682-a011-a72b221b9ea9` (Update core-prompt installation), follow-up discussion and closeout authorization through 2026-09-10. The original migration execution plan remains historical in [PLAN.md](PLAN.md); its implementation evidence remains in [VERIFICATION.md](VERIFICATION.md).

## Completed scope and exclusions

The v1.14.1 migration was delivered through [PR #64](https://github.com/medhatgalal/Core-Prompts/pull/64) and [MR !66](https://gitlab.appian-stratus.com/medhat.galal/core-prompts/-/merge_requests/66). It supports the explicitly catalogued historical names, independent provider/surface ownership, resource reconciliation, and guarded transactions. The historical 24-skill population is not a cap on current installations.

Home adoption was not applied by this task. The separate task Assess frontend design prompt reported v1.14.2 publication and release cleanup complete; this handoff does not repeat or take ownership of that release. It also excludes Experience Design, skill-improvement experiments, other tasks' worktrees, live schedules, KiroCrew application state, and new permissions.

## Characterized boundary

Initial diagnostic revision: `42962f7ac4346f4c4b739a20acaa8227d676e719`. Closeout base: `ce6ccd3a9f812ef9161d305c90385633ab3db864`. Recheck code and release identity before implementation.

| Scenario | Current result | Probe cases |
| --- | --- | --- |
| Same-name content/hash changes | Old receipt proves ownership; new bytes and receipt install; next sync is a no-op. Stale source inventory is rejected. | 5 |
| New capability | Routine sync preserves explicit selection; explicit installation adds the new skill. | 5 |
| Customized active package | Preserved while an unrelated selected package can update. | 5 |
| Future rename, merge, or retirement | Missing saved names reject before lifecycle processing, even with an in-memory successor-map change. | 15 |
| Resource addition/removal within an owned package | Exact inventory additions/removals reconcile; next sync is a no-op. | 5 |
| Customized inactive payload inside shared runtime | A runtime conflict blocks a proposed unrelated active update. | 1 |

The initial disposable run passed all 36 cases. Fifteen cases assert the existing refusal, and one asserts broad runtime blocking: these are evidence of limitations, not desired future acceptance criteria. The portable reproduction is [lifecycle-boundary-probe.py](lifecycle-boundary-probe.py).

Run from the selected repository root with Python 3.11+ and the repository's pytest dependency (preferred runtime: 3.14):

```bash
PYTHONDONTWRITEBYTECODE=1 python3.14 -m pytest -q -p no:cacheprovider reports/installation-migration/lifecycle-boundary-probe.py
```

The file is intentionally outside the default `tests/` collection and is invoked explicitly. It imports the repository's existing `tests/test_installation.py` fixtures and creates only disposable targets. It is a characterization artifact, not new product CI coverage; future implementation must promote appropriate assertions to permanent regression tests and replace the expected-gap assertions with migration acceptance cases.

Original scratch probe SHA-256: `4778671582bd4607a3b9e00f1ccd91963cc40f77fb78494c7ed6e84e95b2ccf5`. The preserved script changes only its explanatory module docstring and repository-root lookup; test bodies are unchanged. The original run observed skill surfaces across Codex, Kiro, Claude, Gemini, and Grok. It does not prove native agent behavior, runtime hook transformations, engine bootstrap, semantic skill compatibility, or hosted release correctness.

Closeout reproduction and review results are recorded with the delivering PR/MR. No new implementation success is inferred from them.

## Follow-up design to review

Objective: support routine future capability evolution while preserving existing installation ownership, selections, customizations, and recovery. Keep the established checksums and transaction machinery; do not broaden authority to make migration succeed.

1. **Identity and lifecycle metadata.** Separate durable capability identity, current invocation/path name, and content hashes. Define versioned, data-only rename, many-to-one merge, and retirement declarations. Define receipt-format conversion and migration history. Reject cycles, ambiguous mappings, invalid targets, and undeclared removals. Historical complete-package fingerprints remain a distinct source of ownership proof; append reviewed release inventories for receiptless recognition without trusting target-authored metadata.
2. **Pure lifecycle resolver.** Proposed contract: previous selection + current catalog + lifecycle declarations -> proposed selection, transitions, and conflicts. Resolve transitions before missing-name validation. Preserve provider and surface independently. For merges, specify behavior for either predecessor, both predecessors, custom predecessors, and an existing successor. No transition may silently select another provider, install an absent agent, or broaden permissions. Explicit approval is required where the replacement expands authorized scope.
3. **Provider adapters and dependencies.** Keep provider discovery, supported roots, native layouts, registrations, and declared dependencies outside identity resolution. Kiro is the primary agent acceptance case; Codex registrations require independent checks. Do not claim a Grok agent surface. Resolve known dependencies before retirement, preserve unknown/custom references conservatively, and treat runtime transformations as explicit versioned behavior rather than ignoring differing fields.
4. **Engine/payload isolation.** Separate the shared engine inventory from capability payload inventories. Package conflicts should hold that package and required dependents, not unrelated inactive payloads. Shared-engine corruption may still block everything. Preserve release/source integrity, stale-plan detection, and exact-file ownership checks. Per-component results must not be summarized as complete installation parity when packages were preserved.
5. **Selection policy.** New skills remain opt-in. A future follow-new-skills profile requires a separate explicit product choice and consent. Discovery is not authorization. Do not infer splits or automatically rewrite arbitrary user configuration.

The existing catalog supplies ownership evidence; the resolver supplies transitions; provider adapters supply layouts/dependencies/registration patches; the planner produces the exact write set; the transaction module remains the only installation writer. Reject ad hoc hard-coded aliases, arbitrary migration scripts, filename-based ownership, blanket hash exemptions, and a replacement installer without a demonstrated need.

## Mandatory bootstrap gate

The [current updater](../../scripts/update-core-prompts.py) loads the installed engine to plan the incoming release. The [planner](../../scripts/core_install/planner.py) validates saved scope before historical resolution. Merely shipping new engine code alongside removed names can therefore fail before that code executes.

Before any new name-removal release, prove a supported transition using frozen actual old runtimes and their saved state, not only a freshly installed new planner:

- old schema-1 skills-only profiles, schema-2 independent skills/agents, and receiptless historical copies;
- an already installed v1.14.0/v1.14.1/v1.14.2 engine where available in verified release history;
- skipped releases, including a client that never received the proposed bridge;
- interruption and rollback during engine activation and receipt conversion;
- a current-installer entry point that works without an old updater, receipt, or schedule.

A bridge release is not universal coverage: users can skip it. Where an immutable old reader cannot transition automatically, document the exact current-installer recovery route and support boundary rather than weakening safeguards. A machine with no updater/schedule still needs a user invocation; no repository release can execute itself there. The existing [bootstrap tests](../../tests/test_install_bootstrap.py) are a starting point, not proof of this future route.

Rollback must cover files, registrations, selection/receipt state, migration records, and engine activation in an order compatible with the restored reader. Refuse to overwrite later user edits. Preserve recovery data for partial operations and verify repeated recovery is idempotent.

## Execution gates and acceptance

| Gate | Required outcome before advancing |
| --- | --- |
| G0: ownership and scope | Refresh task/worktree/main identity and open work; select a sole implementation owner and approve the exact slice. |
| G1: bootstrap proof | Actual old-engine and skipped-bridge tests establish the automatic path or explicit fallback. Freeze the lifecycle/receipt contract and compatibility floor. |
| G2: implementation | Add resolver/metadata, receipt migration, adapter integration, and dependency/isolation changes without bypassing ownership. |
| G3: verification | Test rename chains, merge combinations, retirements/dependencies, explicit additions, customized/mixed packages, stale plans, concurrent locks, interruption, rollback, and two subsequent updates. Cover five skill providers and four supported agent providers; perform native Kiro and Codex checks separately. |
| G4: documentation and review | Update README, getting-started, installation/CLI examples, maintainer migration guidance, and changelog with the feature. Independently review architecture, code, tests, and docs against one candidate. |
| G5: delivery | Follow isolated linked-worktree and paired GitHub/GitLab delivery; exact-head checks, matching main refs, and separately authorized release/downloaded-asset and live-install gates. |

Future CI should reject an unexplained removed name/surface and validate lifecycle declarations. Generate hashes from canonical sources; ordinary content updates must not require editing historical fingerprints. Skill behavior changes still follow SSOT/UAC; do not manufacture a capability intake for a records-only or installer-only change.

## Coordination and resume instructions

At the 2026-09-10 overlap check, Experience Design remained in draft PR #65 / MR !67 and touched manifests, onboarding/install docs, changelog, and versioning. Older design worktrees contained uncommitted data. Campaign branches had report-only changes; the campaign has its own coordinator. These are dated observations, not permission to reuse or clean those worktrees.

Start a future implementation from freshly verified main in its own worktree. Recheck ownership, coordinate shared-file and release ordering, and regenerate shared outputs from the integrated canonical sources after either change lands. Preserve frozen research evidence and renew only affected integration/behavior evidence. Do not copy, reset, rebuild, or clean another task's unfinished state.

Next owner: unassigned Core-Prompts installer maintainer. Next action: obtain implementation authorization, refresh this dated handoff, and perform G0/G1. The closeout authorization covers preservation and cleanup only. No follow-up task, standing automation, release, or home deployment is created by this document.
