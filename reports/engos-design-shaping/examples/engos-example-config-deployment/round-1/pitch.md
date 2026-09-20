# Carry cost definitions through deployment without losing target edits

Stage 3 source draft — **review_pending / render_pending**. G0–G2 passed by author inspection against a constructed fixture, not a live system. G3/G4 have not passed. Source identity: `engos-example-config-deployment/input.md` (`input.md:3-4`). Original statement preserved verbatim in intake.md:

> Deploy cost settings with the process package without overwriting
> settings someone changed in the target environment. Older packages must still work.

Source: `input.md:6-7`. No live deployment, mutation or integration test is authorized (`input.md:35-36`).

## Problem, use case and business win

The scenario customer manually re-enters cost settings after every deployment (`input.md:13`). Guiding use case: deploy a process with its currency and activity-cost definitions, preserve a target admin's local edits by default, and continue accepting old packages. Removing repeated entry is the intended business win; no measured savings or production acceptance is claimed (`input.md:6-12`).

## Appetite

Hypothetical C1: one week, two engineers. Stop if target override protection cannot be preserved (`input.md:9-12`). Fit comes from extending existing export/import, revision protection and atomic validation, with no new transport, credentials, permission roles or recomputation (`input.md:16-33`). This is a bounded design rationale, not a verified delivery estimate. Roles/components below are fixture names; no team assignment is invented.

## Proposed solution and alternatives

Add an optional cost-definition section to the existing process package. PackageExporter reads currency/activity definitions from CostConfigStore and carries the stable process UUID and existing activity associations without inventing new identifiers. The section extension is proposed; exporter/importer, store and UUID association are fixture premises (`input.md:16-25`).

PackageImporter retains admin authorization, revision comparison and explicit force-overwrite choice. An absent section leaves target costs untouched. A present section contributes validated definitions to the existing atomic deployment transaction. Proposed semantics: supplied definitions update their matching associations; omission never requests removal, and malformed/empty cost sections are rejected rather than interpreted as deletion. This defines the new contract without claiming an existing signature or wire format. All included configuration is validated before a guarded commit; a stale revision produces a visible conflict with no write unless the authorized target admin explicitly chooses force. Force does not bypass permission or validation (`input.md:11-12`, `input.md:16-27`).

RunningAnalysis consumes committed cost settings at its next ordinary scheduled run. Deployment does not trigger analysis, data reload or historical recomputation (`input.md:28-29`). Existing encrypted deployment transport and authorization remain responsible for crossing environments (`input.md:32-33`). The diagrams and complete contract/security tables below preserve these boundaries.

Alternatives considered by the author:

| Alternative | Why not selected |
| --- | --- |
| Keep manual re-entry | Retains the supplied repeated-work problem (`input.md:13`) |
| Always overwrite costs on import | Violates default target-local preservation and explicit admin choice (`input.md:11-12`, `input.md:19-21`) |
| Import costs in a separate non-atomic step | Introduces partial application instead of using the supplied atomic transaction (`input.md:26-27`) |
| Reload/recompute after deploying settings | Explicitly outside the scenario (`input.md:28-29`) |

## In / Out / Later

| Bucket | Content and rationale |
| --- | --- |
| In | Currency/activity definitions, UUID association, old-package compatibility, conflict/no-write default, explicit existing force path, validation/atomicity and ordinary next-run consumption (`input.md:6-12`, `input.md:16-29`) |
| Out | Cost results, customer transaction data, unrelated configuration, new permission roles/credentials/transport, full reload and historical recomputation (`input.md:10-12`, `input.md:23`, `input.md:28-33`) |
| Later | No additional product work is committed. Independent review and local rendering are next validation steps; eventual local HTML reference placement is the fixture target (`input.md:35-36`). Any expanded feature scope requires a new decision. |

## Ordered cut list and kill criteria

Author-proposed cuts, in order: (1) defer extra explanatory walkthrough examples beyond the proof cases below; (2) defer visual embellishment beyond readable labels/diagrams and the existing visible conflict; (3) if the complete protected core still exceeds C1, stop and reshape. These cuts remove optional presentation effort, not either requested definition type, old-package support, atomicity, security or evidence. They are not new approved product exclusions (`input.md:6-12`, `input.md:19-27`).

Objective kill criteria for later authorized acceptance: any default stale-base write; unauthorized force; absence deleting target costs; validation failure changing any prior state; or a design needing new permission roles, credentials, full reload or historical recomputation. At appetite exhaustion without the complete usable core, return for a decision rather than extending the week. These are proposed checks of C1 and fixture invariants, not results (`input.md:9-12`, `input.md:19-29`, `input.md:32-33`).

## Pitch-wide proof slice and workstreams

First proposed end-to-end slice: a single process's currency/activity definitions travel through the existing package path. Compare a matching revision, a target-local edit causing conflict/no write, an old package with no section, and invalid included configuration. After a successful commit, the next ordinary analysis run reads the changed definitions; prior results remain untouched. Add explicit authorized force and permission-denial cases before acceptance. This is a proof plan, not executed evidence (`input.md:16-29`, `input.md:32-33`).

| Workstream / state | Boundary and dependencies | First visible slice / proposed completion proof |
| --- | --- | --- |
| W1 PackageExporter + CostConfigStore / ready for teaching design | C01–C02; only scoped definitions associated with process UUID (`input.md:22-23`) | One process package visibly contains the definitions and UUID; excludes results/transaction data; missing or invalid association cannot silently remap data |
| W2 PackageImporter + deployment transaction / ready for teaching design | C03–C06; consumes W1 section or old format; validation and revision rules (`input.md:16-27`) | Show success, unchanged old-package costs, stale conflict, denied/explicit force, and invalid-data zero-write outcomes; no partial commit |
| W3 RunningAnalysis / ready for teaching design | C07; consumes committed store values only through existing timing (`input.md:28-29`) | Next ordinary run sees the deployed definitions; deployment creates no reload or historical recomputation |
| W4 Scenario-scale boundary / ready for teaching design | W1/W2; total configuration capacity (`input.md:30-31`) | Inspect an at-limit valid package and a beyond-limit rejection, both preserving atomicity and all required definitions |
| Results/recomputation/new roles / excluded | C1-S, C1-A, C1-T (`input.md:10-12`, `input.md:28-33`) | No slice or hidden prerequisite; excluded behavior must stay absent |

“Ready” describes contract-level teaching work only. No implementation workstream or live seam is certified ready. These are provisional scopes, not production tickets. Parallel export/import work depends on the same optional-section semantics, not on independent conflicting formats; analysis requires no new deployment trigger.

## Risks, clearance and no-gos

| Risk | Grounding and mitigation owner | Required clearance; current state |
| --- | --- | --- |
| R1 Silent overwrite | Revision conflict and admin choice (`input.md:19-21`); PackageImporter + target admin | Stale-base/no-write, unauthorized denial and separate explicit-force evidence; fixture rule only, checks unrun |
| R2 Old-package data loss | Absent means unchanged (`input.md:24-25`); PackageImporter | Before/after cost equality for absent section; unrun |
| R3 Partial or wrong-process update | UUID + atomic validation (`input.md:22`, `input.md:26-27`); PackageImporter / deployment transaction | Invalid association/definition preserves all prior state; guarded commit retains revision protection; unrun |
| R4 Capacity rabbit hole | 100 × 200 activities and 25,000 records (`input.md:30-31`); PackageExporter / PackageImporter | Proposed 20,100 cost records includes 100 currencies, leaving 4,900 for other included configuration. Count total; reject excess before writes. No batching workaround or latency claim; boundary checks unrun |
| R5 Security or analysis scope expansion | Existing controls/exclusions (`input.md:10-12`, `input.md:23`, `input.md:28-33`); responsibilities in security-owners.md | Contract inspection now; later authorized negative-path evidence before product acceptance. No runtime clearance claimed |

Load-bearing no-gos carried into W1–W4 and contracts: no default overwrite; no force without explicit target-admin choice; no deletion from absence; no partial writes; no transport/credential/role expansion; no results/transaction export; no forced analysis/reload/history work. Removing any of these changes the bet or violates C1. Risk mitigation uses supplied boundaries and does not claim risks eliminated (`input.md:9-12`, `input.md:19-33`).

## Artifact handoff

Component, sequence and data-flow sources: component.mmd, sequence.mmd, data-flow.mmd. Semantic interface inventory: contracts.md (C01–C07). Security and negative responsibilities: security-owners.md (S01–S07). Evidence answers and provenance: research-notes.md, decisions.md. Sequential author receipts and actual hashes: journal.md.

Missing to advance G3: actual renders/pixel inspection and independent review of current source hashes with both scorecards. G4 is unreached; the requested local HTML reference has not been produced or verified. Live feasibility and implementation acceptance remain outside this teaching exercise (`input.md:35-36`).
