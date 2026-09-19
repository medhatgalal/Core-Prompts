---
name: engos-example-route-check
capability_type: skill
description: Inspect a saved route without changing it.
---
# Route Check

## Purpose
Inspect a saved route for missing destinations.

## Primary Objective
Identify broken destinations with exact source evidence.

## Invocation Hints
Use when an existing route needs diagnosis before an edit.

## Required Inputs
- The saved route and intended destination.

## Required Output
- Broken destinations, source evidence, and unresolved inputs.

## Workflow
1. Read the supplied route.
2. Compare each destination with its recorded target.
3. Report the smallest correction after diagnosis.

## Out of Scope
- Changing a route or publishing it.

## Constraints
- Do not write files or send messages.

## Companion Capability Matrix
| If this need exists | Route to | Required handoff |
| --- | --- | --- |
| A changed diff needs review after a separately authorized fix | engos-quality-code-review | The resulting diff and requirement |

## Examples
> Only use this capability when the user explicitly requests it.

## Evaluation Rubric
| Check | Passing |
| --- | --- |
| Evidence | Every finding has a supplied source |
