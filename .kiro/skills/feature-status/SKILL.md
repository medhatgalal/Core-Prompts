---
name: "feature-status"
description: "[BenK] Deep feature completeness analysis — scope vs. proof with prioritized recommendations"
---
# Feature Status — Deep Completeness Analysis

## Purpose
Perform a thorough, evidence-based comparison of a feature's defined scope against concrete proof in the codebase. Produce a rich, categorized status report with test gap analysis, spec drift detection, and priority-ordered recommendations for what to address next.

This is not a shallow checklist. It is a deep forensic audit of where a feature actually stands.

## Primary Objective
Given scope documents (pitch, HLD, OAS, tickets) and proof sources (code, tests, config, git history), produce a single categorized status report that:
- maps every verifiable work item to concrete evidence
- enforces a scope-confirmation gate before analysis
- surfaces spec drift and test gaps the developer did not ask about
- ends with prioritized recommendations ordered by shipping risk

## Workflow

### Phase 1 — Extract Scope
Read all scope documents (pitch -> HLD -> OAS -> tickets) and extract a flat, categorized checklist of verifiable work items across these categories:

- **API Surface** — endpoints, methods, request/response schemas, status codes, error handling, pagination
- **Business Logic** — services, providers, domain rules, validation, edge cases
- **Data Model** — DTOs, database schemas, migrations, serialization
- **Infrastructure** — IAM roles, feature toggles, config, deployment, helm values
- **Integration** — cross-service calls, SDK changes, client updates
- **Tests** — integration tests, unit tests, contract/pact tests, eval tests
- **Documentation** — READMEs, migration guides, changelog, OpenAPI spec updates

Present the checklist and ask the developer to confirm or adjust before proceeding. Do not proceed to Phase 2 until confirmed.

### Phase 2 — Gather and Read Proof
For each category, read the actual code, tests, and config. Do not rely on filenames, commit messages, or assumptions.

- Compare route/endpoint implementations against the OAS field-by-field
- Read test files and identify which scenarios and edge cases are covered
- Check feature toggle state and whether it gates the new functionality
- Inspect DTOs and compare against the OAS schemas
- Review git history for related commits and their scope

### Phase 3 — Deep Status Assessment
For each work item, assign a status with evidence:

| Status | Meaning | Evidence Standard |
|--------|---------|-------------------|
| ✅ Complete | Implementation exists, appears correct, and has test coverage | Code verified, tests verified |
| 🟢 Implemented | Code exists and looks correct but test coverage is missing or thin | Code verified, no matching tests found |
| 🟡 Partial | Some evidence exists but the implementation is incomplete | Partial code or partial tests |
| 🔴 Not Started | No evidence found in any proof source | Nothing in code, tests, or config |
| ⚠️ Drift | Implementation diverges from the spec (OAS, HLD, or pitch) | Spec says X, code does Y |
| ❓ Unclear | Cannot determine from available proof — needs manual verification | Do not guess |

### Phase 4 — Gap Analysis
Go beyond the checklist. Identify what the developer may not have thought of:

- **Test gaps** — scenarios defined in the pitch/HLD that have no test coverage; missing negative/error path tests; missing edge cases
- **Spec drift** — where the implementation differs from the OAS or HLD (field names, types, status codes, error shapes, missing fields)
- **Missing error handling** — endpoints without proper error responses, missing validation
- **Security gaps** — auth/authz not enforced, missing input validation, exposed internals
- **Observability gaps** — missing metrics, logging, or tracing for new code paths
- **Documentation gaps** — README not updated, no migration guide, changelog missing

### Phase 5 — Prioritized Recommendations
Produce an ordered list of what to address next, ranked by:
1. **P0 Blocking** — things that prevent the feature from shipping (broken contracts, missing core logic)
2. **P1 High Risk** — gaps that could cause production issues (missing error handling, security, no tests for critical paths)
3. **P2 Completeness** — remaining work items that are not started or partial
4. **P3 Polish** — documentation, observability, minor spec alignment

## Tool Boundaries
- allowed: read source code, tests, config, specs, git history, and any documents the developer provides; produce status reports, gap analyses, and recommendations
- forbidden: modifying code, running tests, deploying, or making changes without explicit developer approval; guessing scope from code alone when no spec is provided
- escalation: if the audit reveals architecture concerns, route to `architecture`; if it reveals test generation needs, route to `testing`; if it reveals docs drift, route to `docs-review-expert`

## Rules
1. **Demand context** — always ask for scope documents (pitch, HLD, OAS, tickets) and proof sources (code, tests, config). Do not guess scope from code alone.
2. **Confirm scope first** — present the extracted checklist for developer approval before gathering proof. Do not skip this gate.
3. **Read the code** — inspect actual files, diffs, and test bodies. Never rely on filenames or commit messages as proof.
4. **Spec is truth** — compare implementation against the OAS and HLD. Flag every divergence as drift.
5. **No false greens** — if you cannot verify an item from proof, mark it ❓ or 🟡, never ✅.
6. **Go deeper than the checklist** — the gap analysis must surface things the developer did not explicitly ask about.
7. **Prioritize recommendations** — always rank by blocking -> high risk -> completeness -> polish.
8. **Evidence with references** — every status must cite a file, line, commit, or test. No hand-waving.
9. **Handle missing specs explicitly** — if the developer provides code but no spec, note the gap and analyze what is available, but flag every finding as unverifiable against spec.

## Invocation Hints
Use this capability when the user asks any of the following, even without naming the skill:
- how complete is this feature
- what is left to ship
- compare scope vs implementation
- find gaps in this feature
- feature readiness check
- what is blocking this feature from shipping
- audit this feature against the spec
- what's the gap between spec and code
- pre-ship readiness check for this feature

## Required Inputs

### Scope Documents
| Document | What It Tells You | Example Path |
|----------|-------------------|--------------|
| Pitch / Spec | Feature goals, boundaries, success criteria, appetite | `docs/teams/.../pitches/my-feature.md` |
| High-Level Design (HLD) | Architecture, component interactions, data flow, trade-offs | `docs/architecture/HLDs/AIPL-XXX-feature.md` |
| OpenAPI Spec (OAS) | API contract — endpoints, methods, schemas, status codes, error shapes | `docs/architecture/OASs/AIPL-XXX-feature.openapi.yaml` |
| Ticket / Epic | Acceptance criteria, subtasks, definition of done | JIRA ticket or linked issue |

### Proof Sources
| Source | What It Proves | Example Path |
|--------|---------------|--------------|
| Source code | Implementation exists | `services/ai-platform/src/` |
| Integration tests | Feature works end-to-end against real dependencies | `services/ai-platform/test/integration/` |
| Unit tests | Component-level correctness | `services/ai-platform/test/unit/` |
| Git history | What was changed and when | `git log --oneline -30` |
| Config / Infra | Feature toggles, terraform, helm, deploy templates | `terraform/`, `charts/`, `deploy/` |
| OpenAPI output | Generated spec matches proposed spec | `services/ai-platform/openapi.json` |

## Required Output

Every response must include:

```
## Feature Status: [feature name / ticket ID]

### Scope Sources
| Document | Path |
|----------|------|
| Pitch    | [path] |
| HLD      | [path] |
| OAS      | [path] |

### Summary
**[X/Y] work items complete** | **[N] with test coverage** | **[N] spec drift issues**

---

### API Surface
| # | Work Item | Status | Evidence | Notes |
|---|-----------|--------|----------|-------|

### Business Logic
| # | Work Item | Status | Evidence | Notes |
|---|-----------|--------|----------|-------|

### Data Model
| # | Work Item | Status | Evidence | Notes |
|---|-----------|--------|----------|-------|

### Infrastructure
| # | Work Item | Status | Evidence | Notes |
|---|-----------|--------|----------|-------|

### Integration
| # | Work Item | Status | Evidence | Notes |
|---|-----------|--------|----------|-------|

### Tests
| # | Work Item | Status | Evidence | Notes |
|---|-----------|--------|----------|-------|

### Documentation
| # | Work Item | Status | Evidence | Notes |
|---|-----------|--------|----------|-------|

---

### 🔍 Gap Analysis

#### Test Gaps
- [Scenarios missing coverage, with specific recommendations]

#### Spec Drift
- [Where implementation diverges from OAS/HLD, with file:line references]

#### Missing Error Handling
- [Endpoints or paths without proper error responses]

#### Security Concerns
- [Auth, validation, or exposure issues]

#### Observability Gaps
- [Missing metrics, logging, or tracing]

---

### 📋 Prioritized Recommendations

| Priority | Category | Action | Why |
|----------|----------|--------|-----|
| 🔴 P0 — Blocking | | | |
| 🟠 P1 — High Risk | | | |
| 🟡 P2 — Completeness | | | |
| 🟢 P3 — Polish | | | |

---

### Risks / Blockers
- [Anything discovered that could affect delivery]
```

## Examples

### Example Request
```
Use feature-status to audit this feature:

Pitch: docs/teams/ai-platform-core-apis/pitches/internal-only-model-framework.md
HLD: docs/architecture/HLDs/AIPL-771-adding-new-models.md
OAS: docs/architecture/OASs/AIPL-771-adding-new-models.openapi.yaml
Code: services/ai-platform/src/
Tests: services/ai-platform/test/integration/
```

### Example Follow-Up
> The scope checklist is missing the webhook callback endpoint from the HLD. Add it and re-run Phase 3 for that item only.

## Evaluation Rubric
| Check | What Passing Looks Like |
|-------|------------------------|
| Context demanded | The skill asks for scope documents and proof sources before analyzing |
| Scope confirmed | The extracted checklist is presented for developer approval before Phase 2 |
| Evidence grounding | Every status cites a file, line, commit, or test — no hand-waving |
| No false greens | Unverifiable items are marked ❓ or 🟡, never ✅ |
| Spec fidelity | Implementation is compared against OAS/HLD, not just checked for existence |
| Gap depth | The gap analysis surfaces issues the developer did not explicitly ask about |
| Priority ordering | Recommendations are ranked blocking -> high risk -> completeness -> polish |
| Output contract | The report follows the required output format with all sections populated |

## Review Timing
- commit: when commands, behavior, or metadata contracts change
- pull request: when repo structure, CI, release flow, or docs drift materially
- merge: when adjacent capability or doc surfaces changed and drift is likely
- release: verify shipped behavior, install flow, and references against the final state

## Advisory Notes
- Relationship and org-graph metadata remain advisory for future orchestrators.
- Use the sidecar descriptor as the canonical machine-readable contract.
- Emit surfaces for: `claude_skill, codex_skill, gemini_skill, kiro_skill`


Capability resource: `.kiro/skills/feature-status/resources/capability.json`
