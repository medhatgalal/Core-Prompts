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
- generated inspection views such as `docs/CAPABILITY-CATALOG.md`, `docs/RELEASE-DELTA.md`, and `docs/STATUS.md`
- dry-run deploy output before local install when the release overwrites installed home surfaces
- direct comparison between generated outputs and installed state when local customizations or prior tool-written state may exist

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

- use `docs-review-expert` when the change is primarily about docs hierarchy, drift, and rewrite quality
- use `gitops-review` when the change affects branch hygiene, CI, packaging, merge, or release readiness
- use `testing`, `code-review`, and `architecture` when the changed behavior crosses those boundaries
