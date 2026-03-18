# Capability Review Pilots Program

## Goal
Use Capability Fabric and UAC to evaluate external capability families, strengthen weak SSOT descriptions, and codify durable documentation and GitOps hygiene through benchmark-grade reusable capabilities and template-backed quality gates.

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
5. UAC template and benchmark-gate hardening for future imports

## Current Outcome
- Repo architecture brief: complete
- Benchmark matrix: complete
- Docs family research and candidate landing: complete as `both`
- GitOps family research and capability landing: complete as `both`
- SSOT description uplift wave 1: complete for `supercharge`, `analyze-context`, and `converge`
- Beads / Spec-Kit evaluation: complete
- UAC template and score-gate hardening: complete

## Family Decisions
| Family | Outcome | Why |
| --- | --- | --- |
| `docs-review-expert` | land as new SSOT capability with `both` surfaces | The repo needs one reusable documentation specialist whose body is rich enough to support both skill and advisory agent surfaces. |
| `gitops-design-hygiene` | superseded by `gitops-review` capability plus maintainer guidance | The repo needs a reusable GitOps review capability, not only policy text. Durable repo rules still live in maintainer docs. |

## Execution Standard
Every new family must:
1. gather external and local benchmark sources
2. pass through `bin/uac import` or `plan` to expose fit and gaps
3. record evidence in `VALIDATION.md`
4. exceed the current description and metadata bar before landing
5. end in one explicit state: land, uplift existing, or archive as research
