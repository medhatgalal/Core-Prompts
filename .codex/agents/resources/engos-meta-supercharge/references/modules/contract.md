## MODULE: /contract — 2026 Contract + QA (Unified Spec + Evaluation)

### Purpose
Resolve meaningful ambiguity about what is promised and what establishes completion. This is useful across delegation boundaries, conflicting requirements, or unsupported completion claims. Preserve an adequate existing contract rather than restating it or adding ceremony. Define the contract, then have an actual independent checker evaluate against that fixed version.

### HARD CONSTRAINTS (Non-Negotiable)
- Do not invent context or silently turn proposed criteria into user requirements.
- Prioritize the user's primary value and outcome over secondary benefits. If they conflict, make the trade-off explicit rather than optimizing secondary polish at the primary goal's expense.
- Map each material obligation to its source, acceptance condition, available evidence, and result or gap. Put this mapping in `Contract Spec`; keep the QA JSON schema unchanged.
- Version the contract before review. If a criterion is defective, record the revision and re-evaluate; do not move the criteria merely to fit the artifact.
- The checker receives the contract and artifact without the author's desired score. A contract already sufficient for the task is a valid result; identify only real gaps.
- If required info is missing, ask at most three questions or offer assumption packs.
- Evaluation must be verifiable and output strictly as JSON when requested.
- If safety or compliance is violated, escalate explicitly.

### Output Structure (MANDATORY)
1. `Contract Spec`
2. `QA Evaluation JSON`

### Contract Spec Template
- `[CONTEXT]` Target for evaluation + relevant references provided by the user
- `[INTENT]` Goals and trade-offs
- `[SPEC]` Problem statement + decomposition into verifiable subtasks
- `[CONSTRAINTS]` MUST / MUST NOT / PREFER / ESCALATE rules
- `[ACCEPTANCE]` What an independent observer can verify

### QA Evaluation JSON (Strict)
Return valid JSON with this schema:

```json
{
  "overall_score": 0,
  "critical_escalations": [],
  "step_by_step_critique": [
    {
      "step": "",
      "critique": "",
      "actionable_recommendation": ""
    }
  ],
  "intent_alignment_summary": ""
}
```
