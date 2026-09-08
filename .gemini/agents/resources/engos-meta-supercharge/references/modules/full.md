## MODULE: /full — Illumination Gauntlet (No Execution)

### Purpose
Show how multiple lenses treat the same input to illuminate trade-offs and avoid blind spots.

### HARD CONSTRAINTS
- Do not execute the final generated prompt.
- Run sequential passes and show outputs per pass. Use the actual independent subagents required by each pass. Carry the current artifact and unresolved findings forward; identify each finding as resolved, rejected with evidence, or still open so later passes cannot silently erase earlier work.
- When stacked with `/ult`, announce that this invocation reviews and grades the improved prompt without executing its task. This no-execution rule overrides `/ult` execution for the invocation, not its persistence.
- If missing info blocks correctness, ask at most three questions or provide assumption packs.
- Includes `/grade` at the end unless the user says "skip grade".
- Does not include `/basis` by default; add `/basis` explicitly when first-principles reasoning is part of the ask.

### Output Structure (MANDATORY)
- `PASS 1 — SIMPLE`
- `PASS 2 — INVERT`
- `PASS 3 — ADVERSARIAL`
- `PASS 4 — CONTRACT`
- `PASS 5 — GRADE (up to 10 trials)`

If `/basis` is explicitly stacked with `/full`, run it first and label it `PASS 0 — BASIS`.
