---
name: "codebase-health-audit"
description: "Read-only brownfield codebase structural audit for LOC hotspots, god objects, import fan-out, dead code, prior-claim verification, drift detection, and slice-ready remediation."
---
# Codebase Health Audit — Brownfield Structural Risk Report

## Purpose

Use this capability to perform a read-only structural health audit of an existing codebase. It measures codebase risk through concrete metrics, verifies prior audit claims against live files, detects drift between audit snapshots, and produces slice-ready remediation recommendations.

This capability is for brownfield structural analysis, not feature completeness review, commit review, or broad architecture design. It can overlap with those concerns when structural findings require escalation, but its core job is metric-backed codebase health reporting.

## Primary Objective

Given a target repository path, optional prior audit state, and optional threshold overrides, produce a reproducible markdown report with YAML frontmatter that identifies LOC hotspots, god objects, high coupling, likely dead code, claim-verification status, drift trajectory, and prioritized remediation slices.

## Invocation Contract

This is a direct skill surface, not an autonomous agent. It may read files, list directories, inspect symbols, and search references. It must not modify, create, delete, stage, commit, install dependencies, run tests, or deploy anything in the target codebase.

## In Scope

- LOC hotspot detection
- class/module god-object detection
- import fan-out and circular import detection
- conservative dead-code detection
- prior finding verification
- drift computation
- machine-readable audit frontmatter
- slice-ready remediation recommendations

## Out Of Scope

- editing the audited codebase
- running tests or application code
- installing dependencies
- broad architecture redesign
- feature scope completeness review
- pre-commit diff review
- declaring dynamic code dead when references are uncertain

## Invocation Hints

Use this capability when the user asks any of the following, even without naming the skill:

- audit this codebase for structural health
- find LOC hotspots, god objects, coupling, or likely dead code
- verify whether prior codebase-health findings still hold
- compare this repo against a previous audit snapshot
- produce a read-only brownfield health report
- identify slice-ready refactors from concrete structural metrics
- detect structural drift since the last audit

## READ-ONLY MODE (Non-Negotiable)

You MUST NOT modify, create, or delete any files in the target codebase. You are a read-only analyst. Any file-write attempt is a skill violation.

## Required Inputs

- target path for the repository or subtree to audit
- optional prior state block from a previous audit when claim verification or drift detection is requested
- optional threshold overrides for LOC, method count, import fan-out, dead-code confidence floor, excludes, and language filters
- any explicit scope boundaries, such as a monorepo subdirectory or language subset

## Inputs

You receive up to three inputs:

1. **Target path** (required) — Root directory of the codebase to analyze.
2. **Prior state block** (optional) — YAML block from a previous audit, enabling drift detection and claim verification.
3. **Config overrides** (optional) — YAML block overriding default thresholds.

### Input Schema

```yaml
# Target (required)
target: /path/to/repo

# Config overrides (optional — defaults shown)
config:
  loc_warning: 500
  loc_critical: 1000
  method_warning: 15
  method_critical: 30
  fanout_warning: 10
  fanout_critical: 20
  dead_code_confidence_floor: medium  # high | medium | low
  exclude_patterns:
    - "node_modules/"
    - "dist/"
    - ".git/"
    - "__pycache__/"
    - "*.min.js"
    - ".venv/"
    - "vendor/"
  languages:
    - python
    - typescript

# Prior state block (optional — enables drift detection + claim verification)
prior_state:
  timestamp: "2026-06-17T14:30:00Z"
  thresholds:
    loc_warning: 500
    loc_critical: 1000
  findings:
    - id: "LOC-001"
      category: loc_hotspot
      severity: critical
      file_path: "src/engine.py"
      metrics: {line_count: 1247}
      evidence: "File exceeds 1000-line critical threshold"
    - id: "GOD-001"
      category: god_object
      severity: high
      file_path: "src/manager.py"
      metrics: {method_count: 28, public_methods: 22}
      evidence: "Class Manager has 28 methods, 22 public"
```

## Analysis Phases

Execute these phases sequentially. Each phase uses the agent's built-in tools (file reading, grep, code intelligence, AST search).

### Phase 1: Configuration Resolution

1. Merge provided config overrides with defaults (overrides win).
2. Validate prior state block schema if provided:
   - Must have `timestamp` (ISO 8601)
   - Must have `findings` (list, may be empty)
   - Each finding must have: `id`, `category`, `severity`, `file_path`, `evidence`
3. Resolve target path to absolute.
4. Verify target path exists and contains source files.
5. If validation fails, report the error and STOP.

### Phase 2: Structural Analysis

Run these sub-phases. For each, scan only files matching `languages` config and not matching `exclude_patterns`.

#### Phase 2a: LOC Hotspot Scan

1. List all source files in target (respecting excludes).
2. Count lines per file.
3. Flag files exceeding `loc_warning` as severity `medium`.
4. Flag files exceeding `loc_critical` as severity `critical`.
5. Record finding with `category: loc_hotspot`, actual line count in `metrics.line_count`.

#### Phase 2b: God Object Detection

1. For each file exceeding `loc_warning` (from 2a), inspect class/module structure.
2. Count methods/functions per class or module-level.
3. Flag classes/modules exceeding `method_warning` as severity `medium`.
4. Flag classes/modules exceeding `method_critical` as severity `critical`.
5. Note public vs private method ratio — >80% public at >15 methods is severity `high`.
6. Record finding with `category: god_object`, metrics: `{method_count, public_methods, private_methods}`.

#### Phase 2c: Coupling Analysis (Import Fan-out)

1. For each source file, count distinct module imports (fan-out).
2. Flag files exceeding `fanout_warning` as severity `medium`.
3. Flag files exceeding `fanout_critical` as severity `critical`.
4. Identify circular import clusters (A→B→A or A→B→C→A) — severity `high`.
5. Record finding with `category: coupling`, metrics: `{import_count, circular: true|false}`.

#### Phase 2d: Dead Code Detection

1. For each public function/class/constant, search for references across the codebase.
2. If zero references found outside the defining file:
   - `high` confidence: no references anywhere, not in `__init__.py` exports, not in test files
   - `medium` confidence: only referenced in tests (possibly test-only utility)
   - `low` confidence: referenced only in strings/comments (dynamic dispatch possible)
3. Filter by `dead_code_confidence_floor` config — only report findings at or above this level.
4. Record finding with `category: dead_code`, metrics: `{references_found, confidence}`.

### Phase 3: Claim Verification (if prior state provided)

For each finding in `prior_state.findings`:

1. Read the file at `file_path`. If the file no longer exists → status: `resolved`.
2. Re-measure the metric that triggered the finding.
3. Compare against the threshold that was active when the finding was made.
4. Determine verification status:
   - **verified**: finding still holds (metrics still exceed threshold)
   - **resolved**: file deleted, or metrics now below threshold
   - **worsened**: metrics have increased since prior measurement
   - **improved**: metrics decreased but still exceed threshold
   - **unverifiable**: file exists but metric cannot be measured (e.g., structural change)

Record each verification with: `finding_id`, `status`, `prior_value`, `current_value`, `evidence`.

### Phase 4: Drift Computation (if prior state provided)

1. Collect all current findings (from Phase 2).
2. Match current findings to prior findings by `file_path` + `category`.
3. For each pair, compute drift status:
   - `new`: current finding has no matching prior finding
   - `resolved`: prior finding has no matching current finding
   - `worsened`: severity increased (medium→high, high→critical)
   - `improved`: severity decreased (critical→high, high→medium)
   - `unchanged`: same severity
4. Compute trajectory:
   - Count: new, resolved, worsened, improved, unchanged
   - Verdict:
     - `improving`: resolved > new AND worsened == 0
     - `degrading`: new > resolved OR worsened > 0
     - `stable`: otherwise
5. State rationale for verdict.

### Phase 5: Output Assembly

Produce the structured report in the format specified below.

## Output Format

The output is a markdown document with YAML frontmatter for machine consumption.

````markdown
---
audit:
  timestamp: "2026-06-20T14:30:00Z"
  target: /path/to/repo
  config:
    loc_warning: 500
    loc_critical: 1000
    method_warning: 15
    method_critical: 30
    fanout_warning: 10
    fanout_critical: 20
  summary:
    total_findings: 12
    critical: 2
    high: 4
    medium: 5
    low: 1
    categories:
      loc_hotspot: 3
      god_object: 2
      coupling: 4
      dead_code: 3
  trajectory:  # only present if prior_state provided
    verdict: degrading
    rationale: "3 new findings, 1 resolved, 1 worsened"
    counts: {new: 3, resolved: 1, worsened: 1, improved: 0, unchanged: 7}
---

# Codebase Health Audit Report

## Summary

| Metric | Value |
|--------|-------|
| Files scanned | 142 |
| Total findings | 12 |
| Critical | 2 |
| High | 4 |
| Medium | 5 |
| Low | 1 |

## Findings

### Critical

#### LOC-001: src/engine.py — LOC Hotspot
- **Lines:** 1247
- **Threshold:** 1000 (critical)
- **Evidence:** File contains monolithic request handling with no class decomposition
- **Remediation:** [S] Extract request parsing into `request_parser.py` (~200 LOC), response formatting into `response_formatter.py` (~150 LOC)
  - Priority: P1
  - Complexity: S (mechanical extraction, no logic changes)

### High

#### GOD-001: src/manager.py — God Object
- **Methods:** 28 (22 public, 6 private)
- **Threshold:** 15 (warning)
- **Evidence:** Class Manager handles user CRUD, notifications, permissions, and caching in one class
- **Remediation:** [M] Split into UserRepository, NotificationService, PermissionChecker
  - Priority: P2
  - Complexity: M (requires interface extraction + dependency rewiring)

### Medium

#### CYC-001: src/utils.py — High Coupling
- **Imports:** 14 distinct modules
- **Threshold:** 10 (warning)
- **Evidence:** Utility grab-bag importing from every layer
- **Remediation:** [S] Split into domain-specific utility modules
  - Priority: P3
  - Complexity: S (move functions to caller packages)

## Claim Verification

*Only present when prior_state is provided.*

| Finding ID | Prior Severity | Current Status | Prior Value | Current Value | Evidence |
|-----------|---------------|----------------|-------------|---------------|----------|
| LOC-001 | critical | worsened | 1247 lines | 1312 lines | 65 lines added since prior audit |
| GOD-001 | high | verified | 28 methods | 28 methods | No change in method count |

## Drift Analysis

*Only present when prior_state is provided.*

| Status | Count | Findings |
|--------|-------|----------|
| New | 3 | CYC-002, CYC-003, DEAD-001 |
| Resolved | 1 | DEAD-003 (file deleted) |
| Worsened | 1 | LOC-001 (1247→1312) |
| Improved | 0 | — |
| Unchanged | 7 | LOC-002, GOD-001, GOD-002, CYC-001, CYC-004, DEAD-001, DEAD-002 |

**Trajectory:** degrading — 3 new findings and 1 worsened vs only 1 resolved.

## Slice-Ready Recommendations

Remediation recommendations ordered by priority, sized for slice creation:

| # | Priority | Finding | Action | Complexity | Slice Title |
|---|----------|---------|--------|------------|-------------|
| 1 | P1 | LOC-001 | Extract request_parser + response_formatter | S | "Split engine.py into focused modules" |
| 2 | P2 | GOD-001 | Decompose Manager into 3 services | M | "Decompose Manager god object" |
| 3 | P3 | CYC-001 | Move utils into domain packages | S | "Eliminate utils grab-bag" |

## Prior State Block (for next audit)

Copy this block as `prior_state` input for the next audit run:

```yaml
prior_state:
  timestamp: "2026-06-20T14:30:00Z"
  thresholds:
    loc_warning: 500
    loc_critical: 1000
    method_warning: 15
    method_critical: 30
    fanout_warning: 10
    fanout_critical: 20
  findings:
    - id: "LOC-001"
      category: loc_hotspot
      severity: critical
      file_path: "src/engine.py"
      metrics: {line_count: 1312}
      evidence: "File exceeds 1000-line critical threshold"
    # ... all current findings listed here
```
````

## Examples

### First Audit

```text
Use `codebase-health-audit` to audit this repo:

target: /path/to/repo
config:
  languages: [python, typescript]
  loc_warning: 500
  loc_critical: 1000
```

Expected result:
- read-only scan of matching files only
- LOC, god-object, coupling, and likely dead-code findings
- machine-readable audit summary
- slice-ready recommendations ordered by severity and priority
- prior-state block to copy into the next audit

### Drift Check

```text
Use `codebase-health-audit` to verify these prior findings and tell me whether the codebase is improving, stable, or degrading:

target: /path/to/repo
prior_state:
  timestamp: "2026-06-17T14:30:00Z"
  thresholds:
    loc_warning: 500
    loc_critical: 1000
  findings:
    - id: "LOC-001"
      category: loc_hotspot
      severity: critical
      file_path: "src/engine.py"
      metrics: {line_count: 1247}
      evidence: "File exceeds 1000-line critical threshold"
```

Expected result:
- each prior claim marked verified, resolved, worsened, improved, or unverifiable
- drift counts for new, resolved, worsened, improved, and unchanged findings
- trajectory verdict with rationale

## Evaluation Rubric

| Check | What Passing Looks Like |
| --- | --- |
| Read-only safety | The audit never modifies files, runs tests, installs dependencies, stages changes, commits, or deploys |
| Metric fidelity | Every finding cites concrete files, thresholds, and measured values |
| Conservative evidence | Uncertain dead-code or dynamic-reference claims are omitted or marked low confidence instead of overstated |
| Prior-claim verification | Prior findings are re-measured against live files and classified with evidence |
| Drift clarity | Snapshot comparison produces explicit counts, trajectory, and rationale |
| Output contract | The report includes machine-readable YAML frontmatter, grouped findings, recommendations, and a next-run prior-state block |
| Slice readiness | High-severity findings include remediation ideas with priority and complexity |
| Scope control | The audit respects target subtree, excludes, language filters, and monorepo boundaries |

## Edge Cases

1. **Empty repository:** Report 0 findings, skip Phases 3-4, emit valid output with empty sections.
2. **Prior state with no matching files:** All prior findings → status `resolved`. Trajectory: `improving`.
3. **Binary/generated files:** Skip files matching exclude patterns. If a file appears binary (null bytes in first 512 bytes), skip it.
4. **Monorepo:** Analyze only the subtree at `target`. Do not traverse parent directories.
5. **No prior state:** Skip Phases 3-4 entirely. Omit "Claim Verification" and "Drift Analysis" sections. Omit `trajectory` from frontmatter.
6. **All findings resolved:** Trajectory `improving`, congratulate the team in summary.
7. **Extremely large codebases (>5000 files):** Sample the top 50 largest files for detailed analysis. Note sampling in the summary.
8. **Mixed languages:** Apply language-specific method counting (Python: `def`/`async def`, TypeScript: class methods + exported functions).

## Constraints

- **Read-only.** Never modify, create, or delete files in the target.
- **Evidence-based.** Every finding cites specific file + metric. No subjective claims.
- **Reproducible.** Same input + same codebase state = same output.
- **Scoped.** Only analyze files matching `languages` config. Skip everything else.
- **Conservative.** Prefer false negatives over false positives. If uncertain, don't flag it.
- **Actionable.** Every finding ≥ high severity includes a remediation with complexity estimate.

## Tool Boundaries

- **Allowed:** Read files, grep/search, count lines, inspect AST/symbols, list directories.
- **Forbidden:** Write files, run code, install dependencies, execute tests, modify git state.
- **Escalation:** If structural problems suggest architectural redesign, recommend invoking the `architecture` skill. If dead code is extensive, recommend `testing` skill for coverage analysis.


Capability resource: `.claude/skills/codebase-health-audit/resources/capability.json`
