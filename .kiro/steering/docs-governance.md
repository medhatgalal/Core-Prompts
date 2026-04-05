---
inclusion: fileMatch
fileMatchPattern: ["README.md", "AGENTS.md", "docs/**/*.md", ".kiro/steering/**/*.md"]
---

# Docs Governance Steering

## Purpose

Keep the documentation set oriented around real user value while preserving maintainer depth and preventing drift.

## Scope

- This file is the canonical rule surface for documentation hierarchy and docs drift behavior.
- Do not treat human docs in `README.md` or `docs/` as the canonical policy source for these rules.

## Entry Order

Documentation should lead in this order:

1. installed capabilities first
2. UAC, the capability intake and uplift workflow, second
3. broader repo tooling and maintainer operations third

## Canonical Doc Homes

- `README.md`: orientation, value, and the fastest path to real usage
- `docs/GETTING-STARTED.md`: first successful use and shortest setup or verification loop
- `docs/EXAMPLES.md`: concrete asks and expected outputs
- `docs/UAC-USAGE.md`: intake, uplift, plan, judge, and apply guidance
- `docs/CLI-REFERENCE.md`: exact commands, paths, and generated-surface locations
- `docs/MAINTAINER-HYGIENE.md` and technical docs: maintainer and release depth

## Drift Rules

- Review docs whenever commands, paths, examples, setup flow, release flow, metadata contracts, or generated-surface behavior change materially.
- Verify onboarding pages against current installed capabilities and current generated surfaces.
- Keep one canonical home per concept and link instead of duplicating full explanations unless deeper duplication is intentionally user-serving.
- If README embeds a higher-value example or explanation, the linked doc must stay aligned with it.

## Generated Docs Positioning

- `docs/CAPABILITY-CATALOG.md` is a generated inventory and lookup aid, not the primary onboarding document.
- `docs/RELEASE-DELTA.md` is a generated release-review aid, not a primary product overview.
- `docs/STATUS.md` is a generated health snapshot for packaged output inspection.
- Generated docs may be linked for inspection, but they should not displace real usage examples in onboarding pages.

## Example Rules

- Prefer real asks over abstract descriptions.
- Show current capabilities only; do not document surfaces that are not emitted now.
- Pair example asks with the response shape or artifact the user should expect.

## Review Timing

- commit: if user-facing commands, examples, paths, or setup flow changed
- pull request: if docs structure, release-facing docs, or generated-doc positioning changed
- merge: if adjacent docs or generated views may now disagree
- release: always re-check README, getting-started, examples, UAC usage, CLI reference, and release packaging against shipped behavior
