# Maintainer Hygiene Guide

Use this page as the human-facing maintainer guide for documentation review, release checks, and repository hygiene. The canonical rule surfaces live in `.kiro/steering/`.

## Canonical Policy Sources

When you need the actual governing rules, read these first:

- `.kiro/steering/repo-workflow.md`
- `.kiro/steering/docs-governance.md`
- `.kiro/steering/agent-behavior.md`
- `AGENTS.md`

This page explains how to use those rules in practice. It is not the canonical policy source.

## Maintainer Focus

When you are reviewing or updating this repo, keep these priorities in mind:

1. Preserve the intended product order: installed capabilities first, UAC second, repo tooling third.
2. Verify commands, paths, generated surfaces, and release behavior against the repo as it exists now.
3. Keep user-facing docs concrete and example-rich.
4. Treat docs uplift as part of the same change when shipped behavior or discoverability changes. Do not leave README, getting-started, or examples stale and assume release notes are enough.
5. Change canonical source first and regenerate outputs when the repo has an SSOT or generator model.
6. Keep build, validate, smoke, dry-run, and install steps ordered so each step observes complete output rather than racing half-finished generation.
7. Keep one canonical home per concept and link instead of duplicating unless the duplication is intentionally user-serving.
8. When multiple branches are moving at once, prefer separate worktrees over layering unrelated edits into the same checkout.

## Delivering A Change

The [delivery workflow](../.kiro/steering/repo-workflow.md#delivery-workflow) applies to skill improvements, docs, and steering alike. Work starts in a linked worktree from current main and finishes through the GitHub PR and GitLab MR, verified main parity, and task-owned cleanup. An explicit review-only or no-merge scope stops at that boundary.

For existing capabilities, prepare the candidate from current SSOT and use the [same-slug UAC update flow](UAC-USAGE.md#update-an-existing-capability). Helpers live under `sources/capability-resources/<slug>/`; generated and installed bundles are outputs. User docs travel with the change. Installation and versioned release checks are separate from merge evidence.

## Practical Review Checklist

### When onboarding or examples changed

Check:

- does `README.md` still lead with real installed capability usage
- does `docs/GETTING-STARTED.md` still follow the intended product order
- does `docs/EXAMPLES.md` still use current shipped capabilities only
- do any linked docs contradict the README examples
- if invocation changed, can a user discover that change from README, getting-started, or examples without reading capability source files

### When commands, paths, or generation changed

Check:

- wrapper help for `bin/uac` and `bin/capability-fabric`
- actual generated directories under `.codex/`, `.gemini/`, `.claude/`, and `.kiro/`
- any generated user views that depend on the changed behavior
- any user-facing capability guidance that should change because the feature is now invoked differently or is discoverable in a new way
- whether the edit touched canonical source rather than hand-patching generated output
- whether build-dependent validation and smoke were run after generation completed, not in a racy parallel sequence

### When release or packaging behavior changed

Check:

- `docs/CLI-REFERENCE.md`
- `docs/UAC-USAGE.md`
- `docs/RELEASE-PACKAGING.md`
- `VERSION`, `RELEASE_SOURCE.env`, and `CHANGELOG.md`
- `LOCAL_REPO.env` handling for home installs and recorded source checkout updates
- updater help for `bin/capability-fabric update --help`
- generated inspection views such as `docs/CAPABILITY-CATALOG.md`, `docs/RELEASE-DELTA.md`, and `docs/STATUS.md`
- dry-run deploy output before local install when the release overwrites installed home surfaces
- whether a narrowly approved repair should use `--surface-only --slug <slug>` so updater, launcher, local binaries, and unrelated surfaces remain untouched
- confirm that every dry-run path is actually read-only; treat attempted writes during dry-run as a release blocker
- direct comparison between generated outputs and installed state when local customizations or prior tool-written state may exist
- whether concurrent UAC engine work and docs or prompt work should be split into separate worktrees before more edits land
- release-watch behavior: scheduled runs check first, auto-accept valid releases by default, update the recorded source checkout only when it is clean and fast-forwardable, `--notify-only` preserves check-only scheduling, `--check-release` never auto-installs when run directly, `--accept-release` remains the explicit install/apply step, and `--rollback previous` restores the latest snapshot

### When evaluation evidence is archived

Follow [Historical evaluation archives](CAPABILITY-EVALUATION.md#historical-evaluation-archives). Verify the archive manifest and byte hashes, keep the archive outside automatic discovery and promotion, rebuild the active contract, topology, and review overlay after SSOT changes, and treat maintenance fixtures as structural evidence only.

## Generated Views: How To Use Them

- `docs/CAPABILITY-CATALOG.md`: use for inventory lookup and current surface placement
- `docs/RELEASE-DELTA.md`: use for release review and change inspection
- `docs/STATUS.md`: use for packaged-output health inspection

They are useful generated inspection aids. They should not replace the real onboarding and example docs.

## Harvesting Lessons From Completed Work

A useful retained lesson connects an observed failure or success to the next decision it changes. Stable operating requirements belong in the linked steering or owning capability; explanations belong beside the relevant workflow; regression cases belong in the existing tests/evals. Run-specific observations stay in evidence with their limits. This keeps lessons discoverable without making every invocation load another playbook.

The modernization and v1.14.0 delivery produced these reusable lessons:

| Lesson | What happened and what carries forward | Durable home |
| --- | --- | --- |
| Keep the whole approved scope | A derived checklist omitted comparative work and sequencing prose. Closure now reconciles the original source plus later authorized changes. | [Scope rules](../.kiro/steering/repo-workflow.md#scope-rules); [recorded gap](../reports/frontier-modernization/EVIDENCE.md) |
| Match claims to evidence | Source review and resource assembly were once described as a live council demonstration. A later run supplied that missing evidence, but could not prove an earlier sequence occurred. | [Verification expectations](../.kiro/steering/repo-workflow.md#verification-expectations); [resource evidence levels](FRONTIER-MODERNIZATION.md#complete-resources-explicit-evidence) |
| Make evaluations discriminate | Pilot rubrics saturated and reviewers disagreed about wording. Those results support narrower conclusions, not universal model rankings or fixed iteration counts. | [Evaluation discipline](../.kiro/steering/agent-behavior.md#comparative-evaluation-and-bounded-work); [pilot limits](CAPABILITY-EVALUATION.md#learning-from-bounded-pilots) |
| Budget the entire workflow | Coordination, occupied agent slots, and final verification exceeded planned elapsed windows. Naming the clock and counted phases prevents a model-time measurement from becoming an end-to-end claim. | [Bounded work](../.kiro/steering/agent-behavior.md#comparative-evaluation-and-bounded-work); [timing evidence](../reports/frontier-modernization/EVIDENCE.md#honest-remaining-limits) |
| Fix every output producer | Changing the prompt text initially left the bootstrap helper and UAC fallback generating dated copies. Stable paths and preservation behavior now cover those producers, with regression coverage. | [Artifact guidance](FRONTIER-MODERNIZATION.md#what-changed-for-users); [bootstrap tests](../tests/test_uac_import.py); [UAC tests](../tests/test_uac_source_integrity.py) |
| Verify published bytes | During v1.14.0 verification, a private download returned sign-in HTML despite exit zero. Authenticated downloads then matched the reviewed archives. Transport success alone was insufficient. | [Publication verification](RELEASE-PACKAGING.md#recommended-release-order) |
| Separate pre-existing drift from installer effects | A Codex configuration changed before apply. Its refreshed preservation baseline was recorded; the reviewed install left those bytes, the saved profile, and prior rollback data unchanged. | [Installation preservation](INSTALL-PROFILES.md#review-and-apply-a-plan) |

For the next harvest, the useful questions are: what decision would this lesson change, where does that decision already live, what evidence supports it, and what would make the lesson obsolete? An entry adds value when it improves that existing home or a regression check. Repeated advice, transient statuses, and untested prompting theories do not need new standing rules.

A compact harvest can record the evidence reference, the existing owner, and a disposition such as incorporated, proposed follow-up, or retained as case evidence. For example, a confirmed defect that survived an inconclusive pilot can inform development guidance while an adapter protection remains proposed work owned by the evaluator. That distinction makes the next action visible without describing the protection as implemented. The [development scope rules](../.kiro/steering/repo-workflow.md#scope-rules) govern this closeout; a small change may need only a short disposition in its PR/MR rather than a new report.

The [archived experience-design harvest](https://github.com/medhatgalal/Core-Prompts/blob/aa1e3201c3a43751b5de2c537c1026875beddc75/reports/design-experience-v55/LESSONS.md) illustrates this separation between observed defects, development lessons, and proposed evaluator work. It remains draft research with stated limits. [Learning from bounded pilots](CAPABILITY-EVALUATION.md#learning-from-bounded-pilots) explains how those lessons inform comparable inputs, measurement preflight, and an inconclusive closeout that retains known failures. The governing evaluation rules stay in [agent behavior steering](../.kiro/steering/agent-behavior.md#comparative-evaluation-and-bounded-work).

## Suggested Review Rhythm

- commit: check the touched commands, paths, examples, and any adjacent docs that may now drift
- pull request: read the changed onboarding and reference pages together, not one file at a time
- merge: re-check adjacent surfaces that might now disagree after integration
- release: review README, getting-started, examples, UAC usage, CLI reference, release packaging, and the generated inspection views together

## Companion Review Capabilities

- use `engos-quality-docs-review` when the change is primarily about docs hierarchy, drift, and rewrite quality
- use `engos-quality-gitops-review` when the change affects branch hygiene, CI, packaging, merge, or release readiness
- use `engos-quality-testing-review`, `engos-quality-code-review`, and `engos-design-architecture` when the changed behavior crosses those boundaries

## Archived OpEx source

The original OpEx briefing source and metadata are retained as [archive-only history](../sources/retired/opex-briefing/README.md). The active capability is `engos-audit-opex-incident-review`; its optional `briefing` module carries the preserved meeting-preparation outcomes. The archive is not an installable skill or promotion baseline.
