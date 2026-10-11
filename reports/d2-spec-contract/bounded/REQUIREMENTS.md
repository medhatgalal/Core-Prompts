# Team invitations — requirements draft

## Intent

Change ID: `INV-TOKEN-LIFETIME`. Revision: `draft-1`. Entry order: `design_first`.
Specify safe invitation redemption: strict expiry and at most one successful redemption over the entire lifetime of each token, while preserving legitimate unused-token redemption.

This file, `product/invitations/REQUIREMENTS.md`, is the authoritative requirements artifact. Its established headings and location are retained. `SpecContract.v1.json` is the adjacent interchange projection and must be reconciled whenever this file changes. Paths in the sidecar resolve from the supplied workspace root.

Sources inspected in full:

| Source ID | Reference | Revision evidence |
| --- | --- | --- |
| SRC-POLICY | `inputs/policy.md` | SHA-256 `56bc3a142f9770f1ddd37251c5c3d35287f07580c064d19f9c0df8ca2baa9da8` |
| SRC-DESIGN | `inputs/design.md` | SHA-256 `b7116a20ff1b66c84ed0355ef8bfb0ef30cccc749572a96c581922e6f4ad4fe6` |
| SRC-SPEC | `product/invitations/REQUIREMENTS.md` | `draft-1`; original document contained placeholders and no requirement IDs |

No source version labels or external evidence were supplied. Both inputs are accessible; no implementation was inspected or behavior reproduced. The design analysis below concerns the described algorithm only.

The current user request authorizes local specification drafting and a sidecar. Final acceptance authority is unidentified (`authority_ref: null`); no accepted revision or technical-choice approval is recorded. Status: **draft, acceptance pending**. Policy defines requested outcomes, not approval of this exact draft.

In scope: redemption expiry, token-lifetime reuse prevention, concurrent attempts, invalid-token rejection and the legitimate positive path. No capability decomposition or build order is needed.

Non-goals:
- Selecting a persistence mechanism, transaction boundary, locking or other concurrency architecture.
- Implementation, executable task planning, test execution, external publication, installation or acceptance of unresolved choices.
- Changing token issuance, membership removal, eligibility or unrelated membership behavior beyond the stated redemption guarantees.

## Actors

The team owner invites a person using a token. The recipient is the redeeming person; the supplied design represents that person as `principal_id`. The service caller submits `token` and `principal_id` to proposed `POST /redeem`. Authentication and eligibility rules are not supplied and are not invented here.

## Behavior and acceptance

All requirements below have priority **must**, derived from the mandatory outcomes in SRC-POLICY. Acceptance conditions are proposed checks, not executed tests or runtime results. Success means a successful redemption, not merely an HTTP transport outcome; exact response mapping remains open.

**REQ-INV-001 — priority: must**

Condition: A token is presented for redemption at current_time >= expires_at.

Required behavior: Reject redemption without changing membership; expiry equality is invalid.

Acceptance:
- For an otherwise legitimate unused token at current_time == expires_at, redemption is rejected and membership before and after is identical.
- Repeat with current_time > expires_at; redemption is rejected and membership is unchanged.
- The expiry predicate is current_time < expires_at; an otherwise legitimate unused token strictly before expiry remains eligible under REQ-INV-005.

Unchanged behavior: Legitimate unused, unexpired tokens remain usable.

**REQ-INV-002 — priority: must**

Condition: A token has already produced one successful redemption.

Required behavior: It never produces another successful redemption, regardless of current membership or the principal presenting it.

Acceptance:
- After one successful redemption, a later attempt with the same token and principal cannot succeed again.
- After that successful redemption and removal of its membership, a later attempt with the same still-unexpired token cannot succeed or recreate membership.
- After one successful redemption, presenting that still-unexpired token for a different principal cannot succeed or grant that principal membership.

Unchanged behavior: Use of a different legitimate unused, unexpired token is not prohibited by consumption of this token.

**REQ-INV-003 — priority: must**

Condition: Two simultaneous attempts present the same legitimate unused, unexpired token.

Required behavior: No more than one attempt succeeds; concurrency must preserve the token lifetime limit in REQ-INV-002.

Acceptance:
- For two simultaneous attempts with the same token and same principal, the combined count of successful redemptions is at most one.
- For two simultaneous attempts with the same token and two distinct eligible principals, the combined count of successful redemptions is at most one; both must not gain membership through that token.
- Any subsequent attempt remains subject to REQ-INV-002 if either simultaneous attempt succeeded.

Unchanged behavior: The normal legitimate unused-token case in REQ-INV-005 remains supported; rejecting every request is not a compliant resolution.

**REQ-INV-004 — priority: must**

Condition: An invalid token is submitted.

Required behavior: Reject it without changing membership.

Acceptance:
- For a token known to be invalid, compare membership before and after the attempted redemption: no membership changes and no success.
- Expiry-invalid cases include equality and later times under REQ-INV-001; other invalid-token classifications require the clarification recorded in ASM-INV-004.

Unchanged behavior: Valid unused tokens retain the successful path in REQ-INV-005.

**REQ-INV-005 — priority: must**

Condition: An eligible recipient without team membership submits a legitimate unused token while current_time < expires_at, with no competing attempt.

Required behavior: The token works: redemption succeeds and grants the recipient membership in the invited team.

Acceptance:
- Given a legitimate unused token, an eligible recipient without that team membership, and current_time strictly before expires_at, a normal uncontended redemption succeeds and creates the intended membership.
- After this success, the token is subject to REQ-INV-002.
- Existing-member handling is unresolved under ASM-INV-003; this positive case does not decide that behavior.

Unchanged behavior: The team-owner invitation and recipient redemption purpose remains intact.

**Supplied design reconciliation**

`DES-INV-001` is `inputs/design.md`, at the SRC-DESIGN SHA-256 above. Preserve that supplied revision for reassessment; it has no approval record. It reads expiry, checks the current principal's membership, then inserts membership. Its only described uniqueness constraint is `(team_id, principal_id)`; no separate persistent token redemption history or transaction boundary is described.

- Expiry: “reject if expired” does not spell out equality. REQ-INV-001 supplies the policy's strict predicate. No implementation check has verified it.
- Membership removal: under the described checks, after a successful redemption and membership removal, the still-unexpired token encounters no membership and can follow the success path again. That conflicts with REQ-INV-002.
- Different principal: membership for the first principal does not prevent creation for a second principal with the same token. That conflicts with REQ-INV-002 even sequentially.
- Simultaneous distinct principals: both can pass their membership checks and insert distinct `(team_id, principal_id)` values. Pair uniqueness alone does not enforce REQ-INV-003. For identical principals it can constrain duplicate membership rows, but the excerpt does not specify failure handling or prove token-wide redemption semantics.
- Existing membership: `already_redeemed` conflates current membership with the history of this particular token. ASM-INV-003 preserves the missing product decision.

These are source-based counterexamples and gaps, not observed failures. The requested policy invariants remain the acceptance target. Technical revision belongs to architecture; this draft chooses no storage model, lock, transaction or retry strategy and does not accept the design as sufficient.

## Unchanged behavior

Legitimate unused, unexpired tokens must still work for eligible recipients. Invalid or expired tokens must leave membership unchanged. Removing membership remains a separate operation and must not restore an already-used token. Changing the presenting principal must not reset a token's history. No change to invitation issuance, authentication, membership removal or unrelated membership behavior is specified. Details of those mechanisms were not supplied and are not claimed as verified current behavior.

## Open questions

- **ASM-INV-001 — open**: DES-INV-001 assumes current membership for the presenting principal can stand in for the token lifetime redemption history. Policy contradicts that sufficiency after membership removal or a principal change. The technical replacement remains open; hold dependent design/task approval for REQ-INV-002. Source: DES-INV-001 compared with SRC-POLICY. No decision reference supplied.
- **ASM-INV-002 — open**: DES-INV-001 leaves concurrency coordination unspecified and supplies only uniqueness of (team_id, principal_id). That constraint does not establish one winner per token across distinct principals. A token-wide concurrency guarantee and its failure boundary need architecture review; hold dependent design/task approval for REQ-INV-002 and REQ-INV-003. Source: DES-INV-001 compared with SRC-POLICY. No decision reference supplied.
- **ASM-INV-003 — open**: DES-INV-001 returns already_redeemed when the principal already belongs to the team, even if the token has never been used. Whether such a request consumes the token, succeeds, or returns a distinct non-success outcome is unspecified by policy. Product decision required; hold this existing-member extension of REQ-INV-005 and its REQ-INV-002 implications. Source: DES-INV-001 compared with SRC-POLICY. No decision reference supplied.
- **ASM-INV-004 — open**: Policy fixes the strict expiry boundary but does not identify the authoritative clock/evaluation instant, legitimate-principal rules, the full set of invalid-token conditions, or API error mapping. Clarification is needed for those details in REQ-INV-001, REQ-INV-004 and REQ-INV-005. No numerical latency, clock tolerance or response-code target is proposed. Source: DES-INV-001 compared with SRC-POLICY. No decision reference supplied.

All four assumptions remain open; none is confirmed, accepted, or silently deferred. The contradictions in ASM-INV-001 and ASM-INV-002 do not reopen the policy's required invariant; they require revision of how the design would meet it. The remaining unknown details need their actual product or architecture decision owner. No exclusion decision has been supplied.

**Review and bounded handoff:** Source coverage includes expiry equality/after-expiry, lifetime reuse after removal and principal change, simultaneous attempts, invalid-token non-mutation and legitimate redemption. Independent semantic review and exact-revision acceptance remain pending. The local authoring review identifies the design conflicts above; it is not approval or proof of implementation.

Handoff is `INV-TOKEN-LIFETIME`, `draft-1`, for user review and identification of the decision authority. Dependent design/task approval is held as described per assumption, and no planning or execution is authorized by this request. No task/test links were supplied, so no trace ledger or coverage claims were created.

**Interchange limits:** The schema has no dedicated fields for draft revision, actor, objective, acceptance status, dependent holds, reconciliation narrative or validation receipt. Those local fields remain authoritative here; assumption text carries the relevant holds in the sidecar. Source references identify the authoritative file and inputs, with byte hashes. `authority_ref: null` deliberately records missing acceptance authority.

**Validation receipt:** The supplied design-first and contract resource routes were loaded completely. Local checks verify JSON parsing, required/allowed keys, schema-declared basic types/enums/hash formats, unique ID values in each namespace, accessible file references and source hashes, retained headings, and matching requirement/assumption content across artifacts. A full JSON Schema validator is unavailable in the current standard runtime (`jsonschema` is not installed), so no full Draft 2020-12 validation is claimed. Structural checks do not establish source truth, design sufficiency, approval or behavior. No product tests or runtime checks were run.
