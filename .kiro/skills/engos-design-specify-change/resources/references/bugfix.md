# Bugfix route

Record current, expected and unchanged behavior before describing a correction.
Preserve evidence labels: reported failure, reproduced failure, inferred cause
and verified cause are different claims.

1. Capture the trigger, environment, relevant input and reported/observed result.
   Link the report or reproduction evidence. If reproduction has not happened,
   state that; drafting requirements does not imply permission to run a live test.
2. Establish expected behavior from the actual product contract or authorized
   decision. A bug label alone does not establish what the correct behavior is.
3. State unchanged behavior: adjacent valid cases, compatibility, access controls
   and recovery/retry behavior relevant to this change. Avoid unrelated cleanup.
4. Express requirements and acceptance for the failing case and preservation
   cases. Leave cause unknown when unsupported. Architecture owns a material
   technical remedy; this route specifies results without selecting an algorithm.
5. Reconcile ambiguous expectations or preservation conflicts before dependent
   task approval. Return a pending draft with exact questions if needed.

Example: two clicks reportedly create duplicate invoices. Require the agreed
single-operation result and preserve legitimate later submissions. The definition
of the same operation and any time window need evidence or an explicit decision;
writing “idempotent” alone is not an acceptance test.

The optional machine contract requires bug_context with current_behavior,
expected_behavior and unchanged_behavior for this route. Also populate individual
requirements so the triad remains connected to observable acceptance. Schema
validation cannot establish reproduction, causal diagnosis or regression safety.
