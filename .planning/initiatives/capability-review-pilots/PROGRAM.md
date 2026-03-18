# Capability Review Pilots Program

## Goal
Use Capability Fabric and UAC to evaluate external capability families, strengthen weak SSOT descriptions, and codify durable documentation and GitOps hygiene for future changes.

## Non-Goals
- No orchestration runtime or delegation engine.
- No adoption of new planning infrastructure unless it clearly beats the current `.planning/` model.
- No bulk landing of low-quality external prompts just because they are available.

## Decisions
- Canonical planning home: `.planning/initiatives/capability-review-pilots/`
- Canonical intake engine: `bin/uac`
- Benchmark families: `architecture`, `code-review`, `testing`, and `uac-import`
- First pilot families:
  - `docs-review-expert`
  - `gitops-design-hygiene`
- Memory/process tooling:
  - keep `.planning/` as the working ledger
  - evaluate Beads and Spec-Kit, but do not adopt either in this slice

## Workstreams
1. Repo understanding and benchmark baseline
2. External family research and UAC intake
3. SSOT and metadata uplift for weak descriptions
4. Durable maintainer hygiene rules for docs, GitOps, and lessons

## Current Outcome
- Repo architecture brief: complete
- Benchmark matrix: complete
- Docs family research and candidate landing: complete
- GitOps family research and maintainer guidance: complete
- SSOT description uplift wave 1: complete for `supercharge`, `analyze-context`, and `converge`
- Beads / Spec-Kit evaluation: complete

## Family Decisions
| Family | Outcome | Why |
| --- | --- | --- |
| `docs-review-expert` | land as new SSOT skill | The repo lacks one explicit documentation hygiene and IA specialist, and the research set plus local benchmarks support a durable capability shape. |
| `gitops-design-hygiene` | maintain as durable maintainer guidance plus selective SSOT uplift | The strongest material is process and policy oriented; it fits better as repo rules and review timing than as a generic reusable prompt in this slice. |

## Execution Standard
Every new family must:
1. gather external and local benchmark sources
2. pass through `bin/uac import` or `plan` to expose fit and gaps
3. record evidence in `VALIDATION.md`
4. exceed the current description and metadata bar before landing
5. end in one explicit state: land, uplift existing, or archive as research
