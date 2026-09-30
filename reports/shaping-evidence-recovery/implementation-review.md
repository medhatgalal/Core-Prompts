# Independent initial implementation review

Reviewer Bernoulli, Luna high, 01a0f3b2-9ac7-7ef2-8fc1-0eff6e967214.
Actual unstaged diff at base c39effe; no reviewer edits or tests. Disposition:
blocked pending repair. Preserve these findings rather than replacing this review
with the later repaired result.

- P1: lookup of a malformed JSON-list work_order_id before the guarded block
  can escape as TypeError instead of Recovery/exit3. Add exact CLI evidence.
- P2: the initial bad-coverage control corrupts a content-addressed snapshot
  under its unchanged key. Existing _load rejects it before the classifier.
  Add invalid/missing historical coverage while latest G2 remains valid.
- P2: requiring original mutable receipt bytes for historical classification
  adds a retention dependency beyond the captured journal. Classify the captured
  receipt under common journal bindings, without retroactive raw-file retention.

Reviewer found no P1/P2 instruction preservation issues: twelve scores and3/4,
generic scope, no diagram/native-agent expansion and honest pre-seal protocol
versus host enforcement distinction are preserved. Repair is returned to the
assigned implementation author, not represented as reviewer-authored code.
