# Memory and Planning Tool Evaluation

## Decision
Do not adopt Beads or Spec-Kit for this slice. Keep `.planning/` as the working ledger.

## Why `.planning/` Wins Right Now
- it already matches the repo's existing initiative structure
- it is cheap to inspect in git history
- it keeps planning state in-repo without new runtime dependencies
- it is sufficient for this initiative's mix of research, matrix scoring, and selective uplifts

## Beads Evaluation
### Strengths
- strong long-horizon task tracking and dependency graph
- explicit persistent memory for agent workflows
- good fit when tasks need a living operational backlog

### Weaknesses For This Slice
- introduces a new operational system and storage model for a planning-only initiative
- protected-branch guidance in Beads is useful, but even its own docs mark parts of the old sync-branch workflow as historical
- higher operator overhead than plain markdown for a research-and-uplift slice

## Spec-Kit Evaluation
### Strengths
- rigorous constitution/spec/plan/tasks workflow
- good fit for greenfield feature delivery or larger implementation programs

### Weaknesses For This Slice
- too heavyweight for cross-family capability research and naming/metadata uplift
- would fragment the repo between `.planning/` and `.specify/`
- best used when the repo needs a full feature-spec workflow, not when the main need is capability evaluation and doc/process cleanup

## Trigger To Revisit
Re-evaluate if a future initiative has any of these properties:
- parallel execution across many dependent implementation tracks
- repeated loss of context in `.planning/`
- need for issue graphs or spec enforcement that markdown cannot manage cleanly
