# Installation migration delivery plan
Status: historical execution plan; implementation and local verification completed. Current delivery status is tracked in GitHub PR #64, GitLab MR !66, and VERIFICATION.md. No live home installation was applied.
Candidate starts at 6646862, rebased by merge onto verified main 9d481a2.
Source: this task's approved product-wide migration plan and effort/delegation instructions.

## Outcome and boundaries
One installation engine supports fresh install, receipt-less historical repair, saved skills-only profiles, current named agents, scheduled and manual updates, and recovery. Kiro is the primary agent acceptance case; Codex, Claude, Gemini and Grok skills are provider-specific. The 24 historical variants are recognition inputs, not a current catalog cap.
No unrecognized/customized package is overwritten or retired. No provider/surface expansion is inferred from a different provider or surface. Existing schedules and user data are preserved. KiroCrew registry changes and other project roots are outside this slice.

## Architecture and decisions
- Modular Python source under scripts/core_install: catalog, providers, planner, transaction, CLI.
- One deterministic generated runtime capsule in existing scripts/deploy-profile.py preserves the older installed bundle path allowlist and legacy v1 APIs.
- Historical catalog under .meta/install-profiles is derived from matching verified release refs captured in legacy-release-refs.json. Old releases need not contain install-bundle.json. Target-local manifests alone prove nothing.
- A versioned installation.json records provider/surface/slug selections and ownership; explicit schema1 profiles preserve their skill selections and discover only independently recognizable installed agents on selected providers.
- An old installed engine can receive the new runtime when its existing skill scope passes its guards. Unsupported old scopes use the current installer once; no claim of universal remote self-upgrade.
- Planner is read-only. Transaction engine locks the target, replans, journals preimages and expected postimages, stages writes, verifies replacements before retirement, and provides conflict-aware rollback.
- Unknown dependencies or custom successor packages block the affected migration. Report partial preservation explicitly; never claim complete parity.

## Stages and owners
1. Design: Astra XHigh independent design review; root researches current callers/runtime and owns integration.
2. Historical catalog: Astra High worker owns catalog source, generator, data, and contract tests.
3. Transaction engine: Astra High worker owns transaction module and failure/recovery tests.
4. Planner/providers: root owns selection/reconciliation and provider adapters; independent final reviewers use Max.
5. Integration and bootstrap: root owns shell entry points, profile compatibility capsule, updater, package inventory and CI.
6. Docs: independent High worker owns README, CLI/reference/getting-started/examples, install guide, changelog after CLI contracts settle.
7. Verification: focused TDD, Kiro-first E2E, repeated updates, missing updater, actual old-engine bridge, packaging, full local suite, both CI providers.
8. Landing: update existing PR64/MR66, resolve all significant review findings, merge parity, release/install gates separately, preserve receipts and clean task-owned state.

## Required acceptance evidence
C1: recognized historical packages incl mentor/autosearch; 24 v1.12.2 and later additions.
C2: receipt-less repair; forged manifests/custom/mixed package inventory rejected.
C3: same-provider, same-surface selection incl independently installed Kiro agents.
C4: customization, symlink boundaries, config fields and dependent resources preserved.
C5: saved schema1 profile transition and exact supported old-engine bootstrap.
C6: migration then two routine runs maintain scope; runtime resource additions/removals within owned packages reconcile.
C7: interrupted apply, lock contention, stale plan, rollback and later-edit conflicts.
C8: packaged runtime works without source checkout; catalog/capsule deterministic and verified.
C9: scheduled, unscheduled and no-updater install flows; schedules do not duplicate or change implicitly.
C10: tests wired to GitHub and GitLab; fresh independent review PASS; exact source and delivery receipts.

## Evidence and stop conditions
Review findings are confirmed against 6646862. Earlier green CI omitted deployment tests and does not establish safety. No earlier implementation claim is reused as acceptance.
Stop dependent writes on malformed state, unresolved ownership/dependencies, failed verification, incompatible runtime, or changed approved target inventory. Preserve partial transaction recovery.
Completion requires requirement coverage and disclosure of any unverified live/provider/install gates. No persistent goal or separate sidebar task created.
