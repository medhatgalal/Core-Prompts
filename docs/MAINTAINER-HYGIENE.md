# Maintainer Hygiene Guide

Use this page as the human-facing maintainer guide for documentation review, release checks, and repository hygiene. The canonical rule surfaces live in `.kiro/steering/`.

## Canonical Policy Sources

When you need the actual governing rules, read these first:

- [Repository workflow](../.kiro/steering/repo-workflow.md)
- [Documentation governance](../.kiro/steering/docs-governance.md)
- [Agent behavior](../.kiro/steering/agent-behavior.md)
- [Repository rules router](../AGENTS.md)

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
- do platform examples distinguish the requested artifact, implementation scope, checked behavior, and simulation limits
- do the Skill Job Map and generated catalog route new capabilities against their actual neighboring jobs

### When commands, paths, or generation changed

Check:

- wrapper help for `bin/uac` and `bin/capability-fabric`
- actual generated directories under `.codex/`, `.gemini/`, `.claude/`, `.kiro/`, and `.grok/`
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
- [release-watch behavior](RELEASE-PACKAGING.md#installed-release-watch-contract), including saved-profile versus legacy acceptance, scheduling, installed version, and recovery evidence

### When evaluation evidence is archived

Follow [Historical evaluation archives](CAPABILITY-EVALUATION.md#historical-evaluation-archives). Verify the archive manifest and byte hashes, keep the archive outside automatic discovery and promotion, rebuild the active contract, topology, and review overlay after SSOT changes, and treat maintenance fixtures as structural evidence only.

## Generated Views: How To Use Them

- `docs/CAPABILITY-CATALOG.md`: use for inventory lookup and current surface placement
- `docs/RELEASE-DELTA.md`: use for release review and change inspection
- `docs/STATUS.md`: use for packaged-output health inspection

They are useful generated inspection aids. They should not replace the real onboarding and example docs.

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
