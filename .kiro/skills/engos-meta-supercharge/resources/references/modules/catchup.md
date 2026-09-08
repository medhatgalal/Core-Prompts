## MODULE: /catchup — Deep Forensic Catchup (Multi-Intent)

### Purpose
Reconstruct the conversation as a forensic report, not a new deliverable.
If multiple intent-result threads exist, decomplect them and output one table per intent group.

### HARD CONSTRAINTS (Non-Negotiable)
- Reconstruction only. Do not propose new solutions.
- No prose before each table.
- Do not invent missing info; label unknowns as `[Unclear]`.
- Use markers: `✅ Confirmed` · `🟡 Proposed` · `🔴 Not decided`.
- Temporal discipline: Initially, Then, Afterward, Currently, Not yet decided.
- If timestamps are present, include them; otherwise use turn numbers or sequence indices.

### Evidence and Cognitive Load
Restore the user's understanding of the session in plain English: work categories, original goals, resolved work, decisions, current activity, and recorded next steps. Keep recognizable task names and preserve the exact table and validation output below.
Verify the reconstruction against accessible conversation history, artifacts, and subagent results. An independent subagent checks substantial reconstruction before finalization. Mark inaccessible history `[Unclear]`; distinguish agent-reported completion from independently verified completion where it changes the current state.
Keep evidence collection details in working records. Do not turn the table into a source-log dump. `Next Steps` contains recorded commitments, not a new plan; if fewer than 3–5 are recorded, say so in that cell instead of inventing actions. Preserve all rows and visible validation checks.

### Output Structure (MANDATORY)
For each intent group, output exactly one table:

| Section | Content |
| --- | --- |
| Thread Purpose | Why this intent exists |
| Original Ask | Initial request for this intent |
| Current Goal | What it evolved into |
| Timeline / Phases | Ordered phases with temporal markers + time or turn hints |
| Key Decisions | ✅ Confirmed |
| Proposed (Not Final) | 🟡 Proposed |
| Artifacts Produced | Prompts, docs, outputs already created |
| Open Questions | 🔴 Not decided, blockers, missing inputs |
| Drift / Risks | Gaps, staleness, contradictions |
| Current State | Snapshot of where things stand |
| Next Steps | 3–5 concrete actions to resume |

### Catchup Validation (Run After Each Intent Table)
After each table, run this check and print the result:

```text
/VALIDATE-CATCHUP
Checks:
1) Reconstruction only (no new solution)
2) Exactly one table, no leading prose
3) Markers present (✅/🟡/🔴)
4) Temporal phases explicit
5) One-page, scannable output

If any check fails: revise once, re-run validation
Print:
Validation Status: PASS | FAIL
Failed Checks: (if any)
```
