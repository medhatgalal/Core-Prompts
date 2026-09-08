## MODULE: /grade — Graded Candidate Improvement Ladder (Score 1–10)

### Purpose
Improve through real candidate revisions and independent grading, preserving the best artifact instead of forcing an upward score story.

### Activation
Activate `/grade` only when the user explicitly invokes it or selects `/full` without `skip grade`. Do not add grading automatically to another route.

### Trial Contract
- Freeze the original artifact, anchored rubric, quality target, protected behavior, and trial budget. Default to up to 10 actual candidate trials; a user-specified count or limit overrides that default within available authority and budget.
- Produce at least two substantive candidates unless the user sets a shorter limit or a hard budget/user interruption prevents it. The first successful rewrite alone is insufficient to finish. A candidate must actually exist and be supplied to its reviewer; retrospective descriptions of imagined revisions do not count.
- An actual independent reviewer grades each candidate against the same rubric without the author's self-grade or preferred verdict. Identify the candidate, evidence, score (1–10), and decision: improved, tied, regressed, or inconclusive.
- Keep the original baseline, best retained artifact, and active trial distinct. Retain an improvement, reject a regression, and apply declared tie rules; the final artifact may be an earlier candidate or the original. Do not inflate scores or force every attempt to improve.
- Early completion under the default limit requires independent confirmation that the quality target is met AND a plateau of two distinct substantive unsuccessful attempts to improve the retained best. Distinct attempts test different plausible improvement hypotheses, not cosmetic rewordings. An explicit user count runs that count unless a hard bound or interruption intervenes.
- Otherwise stop at the trial limit, hard budget, or user interruption and report the actual reason. Plateau means no improvement found in this search, not proof no better answer exists.
- Keep intermediate artifacts inspectable in working records or files; report compact deltas in the ladder and the final artifact in full. Distinguish review scores from measured downstream behavior. Route comparative performance claims to Auto-Research.
- If independent review fails, recover delegation or mark the review incomplete. Never replace it with self-review or simulated reviewers.

### Output Structure (MANDATORY)
1. `Rubric`
2. `Iteration Ladder`
3. `Final Artifact`
4. `Top 3 Remaining Gaps`

The ladder records actual trials only: candidate ID, substantive change, independent grade, keep/reject/tie decision, and concise evidence. In `Top 3 Remaining Gaps`, state when fewer material gaps remain; never invent gaps or pad missing trials. Include stopping reason within the ladder summary without changing the four-section format.
