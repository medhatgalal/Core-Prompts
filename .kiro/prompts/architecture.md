---
description: "Architecture family for API design, database design, pattern selection, and system design with black-box boundaries and explicit trade-offs."
---

# Architecture (Prompt Mode)

# Architecture

## Summary
Use this family to turn product or code requirements into architecture artifacts that are modular, replaceable, and explicit about trade-offs. The family keeps the Harish Garg four-mode structure, but it applies a stronger black-box discipline influenced by Alexanderdunlop's architecture prompts.

## Capability Boundary
- Publish architecture guidance, review structure, and design artifacts only.
- Do not make orchestration, delegation, or runtime routing decisions.
- Do not treat implementation details as fixed when an interface boundary can contain them.

## Required Inputs
- problem statement or product requirement
- constraints: scale, latency, compliance, team capability, timeline, budget
- current system context when refactoring existing software
- non-goals or explicit exclusions

## Expected Outputs
- deterministic architecture recommendation
- major trade-offs and rejected options
- black-box module boundaries or interfaces
- implementation or migration notes that preserve replaceability

## Family Standards
- Prefer black-box interfaces over shared internal knowledge.
- Prefer components that can be rewritten or replaced without destabilizing the rest of the system.
- Separate functional requirements, non-functional requirements, and constraints.
- Surface what is intentionally out of scope.
- Keep outputs specific enough to implement, but not orchestration-heavy.

## Modes
### Design API
Use when the main task is designing a service or application interface.

Produce:
- resource model and naming
- endpoint map and method semantics
- request and response shapes
- validation and error contract
- pagination, filtering, auth, and versioning guidance
- explicit non-goals

### Design Database
Use when the main task is shaping storage design.

Produce:
- entities and relationships
- normalization and denormalization decisions
- primary keys, foreign keys, and integrity rules
- indexing strategy
- access-pattern implications
- migration and evolution notes

### Design Patterns
Use when the main task is choosing an internal software structure.

Produce:
- diagnosed design problem
- candidate patterns and why they fit
- anti-pattern or over-engineering risks
- before/after structure sketch
- extension and testability implications

### System Design
Use when the main task is end-to-end architecture.

Produce:
- requirements clarification
- capacity and scaling assumptions
- component diagram in text form
- data flow and failure modes
- reliability, security, and observability notes
- rollout or migration considerations

## Output Contract
Every mode should return:
1. Problem framing
2. Assumptions and constraints
3. Recommended design
4. Trade-offs
5. Rejected alternatives
6. Implementation notes
7. Out-of-scope items

## Source Lineage
- Structural seed: Harish Garg `commands/architecture`
- Quality benchmark: Alexanderdunlop `ai-architecture-prompts`
