# Requirements checklist — adapt to the existing specification format

Retain existing artifact names, IDs and authority. This is a content checklist,
not a requirement to duplicate an existing spec or use every heading verbatim.
Remove template placeholders from completed output; unknowns remain explicit.

## Change and evidence

- Change ID and objective:
- Affected people/callers and outcome:
- Entry order: requirements_first / design_first / bugfix
- Authoritative artifact and source references, including revisions where available:
- Actual authority reference, accepted revision and status, or pending/unknown:
- Evidence limitations (reported versus reproduced behavior, inaccessible sources):

## Scope and requirements

- In scope:
- Non-goals:
- Existing constraints and their sources:
- Optional independently testable capability groups and dependencies:

| Requirement ID | Condition/trigger | Observable behavior | Acceptance conditions | Unchanged behavior | Priority |
| --- | --- | --- | --- | --- | --- |

Acceptance states the scenario, expected result and relevant boundary or failure
case. Priorities are must/should/could/undecided in the optional machine contract;
map the project's vocabulary explicitly. Do not invent thresholds to fill cells.
A genuinely inapplicable unchanged-behavior field may be empty in the sidecar;
explain why in the human specification rather than assuming no regression matters.

## Assumptions and decisions

| Assumption ID | Assumption | Status | Source/decision reference | Affected requirements and hold |
| --- | --- | --- | --- | --- |

Use open, confirmed, rejected or deferred. Confirmed is an attributed decision,
not the author's confidence. Rejected assumptions require affected requirements
to be reconciled. Deferred material assumptions still hold dependent work unless
an authorized scope decision removes that dependency.

## Supplied design, if any

| Design ID | Source path/reference | Current SHA-256 when available | Assumptions/conflicts and reconciliation |
| --- | --- | --- | --- |

A digest identifies bytes, not whether the design is sound. If the bytes cannot
be obtained, disclose the limitation; do not invent a digest or a verified ref.

## Bugfix, when selected

- Trigger and reported/observed current behavior, with evidence:
- Expected behavior and its source:
- Unchanged behavior and compatibility boundaries:
- Unresolved reproduction, environment or cause questions:

## Review and handoff

- Source coverage and conflicts:
- Structural checks performed, including explicit ID uniqueness comparison:
- Semantic review and authority/acceptance evidence:
- Unresolved material assumptions and dependent holds:
- Exact revision to hand off and authorized next owner:

Only create the SpecContract.v1 sidecar for a real interchange need. Its schema
checks shape, not truth, unique ID properties, reference existence, authority,
approval or behavior. Resolve those separately and report their actual status.
