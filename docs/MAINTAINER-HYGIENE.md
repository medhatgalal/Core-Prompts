# Maintainer Hygiene Rules

Use this document as the durable maintainer rule set for documentation hygiene, GitOps review timing, and lessons capture.

## Purpose
Keep repo changes explainable, reviewable, and aligned with the actual architecture, release flow, and multi-remote setup.

## Documentation Hygiene
- `README.md` is for orientation, install, and fast-path usage only.
- `docs/` is for durable operator, reference, and maintainer documentation.
- Technical implementation detail belongs in technical or architecture docs, not onboarding pages.
- Research, planning, and iteration notes stay out of user-facing docs unless promoted intentionally.
- Every significant workflow or release change must be checked for doc drift.

## GitOps Review Timing
### Commit
Review docs or process guidance when a commit changes:
- user-facing commands or install behavior
- naming, capability descriptions, or metadata contracts
- CI workflows, release scripts, deploy/install scripts, or surface generation

### Pull Request
Add or refresh review coverage when a pull request changes:
- docs structure or repo information architecture
- protected-branch assumptions, approval expectations, or CI gates
- release packaging, versioning, or GitHub/GitLab parity behavior

### Merge
Before merge, confirm:
- adjacent doc surfaces are not drifting against one another
- CI and release rules still match the branch integration behavior
- release-facing docs still match the merged branch state

### Release
Every release must re-check:
- `README.md`
- `docs/GETTING-STARTED.md`
- `docs/EXAMPLES.md`
- `docs/CLI-REFERENCE.md`
- `docs/RELEASE-PACKAGING.md`
- any changed maintainer/process docs

## GitHub and GitLab Parity
- Keep GitHub and GitLab CI surface area intentionally aligned where possible.
- If one platform is intentionally different, document why and where the source of truth lives.
- Treat CODEOWNERS, approval rules, protected branches, rulesets, and required checks as design constraints, not afterthoughts.

## Lessons and Self-Improvement
- Record transient lessons, experiments, and evidence in `.planning/` for the active initiative.
- Promote a lesson into `AGENTS.md` or a durable maintainer doc when any of these are true:
  - it caused repeated drift or repeated review failure
  - it changed the repo's stable operating rule
  - future agents are likely to repeat the mistake without a durable instruction
- Prefer one durable rule in one canonical place instead of duplicating the same guidance across many files.

## Promotion Test
Promote a rule only if it is:
- stable across future work
- repo-wide rather than initiative-local
- precise enough to guide behavior without project-specific context recovery
