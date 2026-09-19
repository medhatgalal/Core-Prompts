# Unified chat — Research stop

G1 passed before this artifact. Source identity: `engos-example-unified-chat/input.md`; all 30 numbered lines opened. Evidence class: deliberately incomplete teaching fixture (`input.md:3-4`). No external product research, API invention, prototype or runtime spike executed. U1 and pending U2–U4 in decisions.md remain unchanged.

| Question | Disposition | Actual answer / missing evidence | Opened evidence |
| --- | --- | --- | --- |
| U-Q1 | needs_spike | Persistence API existence is supplied; compatibility with reload/navigation and combined HostHarness session model is expressly unproven. Core outcome still depends on this seam. | `input.md:8-9`, `input.md:17-20` |
| U-Q2 | needs_spike | PreviewAPI supplies renderable content and caller uses session authentication. Neither proves inline preview works in every supported authentication mode. No specifications or results are supplied. | `input.md:17-22` |
| U-Q3 | answered: claim has no evidence | “ready” and “prototype confirmed” are unsupported labels. Reject them as proof; this answer does not resolve U-Q1 or U-Q2. | `input.md:23-24` |
| U-Q4 | unresolved / decision_pending | Sub-agent feature is unfinished; its necessity/completion is unproven. Neither streaming nor completion-only has been chosen. Cannot assume the dependency away. | `input.md:25-26` |

## Bounded evidence requests — proposed, not executed or approved

The fixture explicitly requests a bounded spike with role, criteria and impact (`input.md:28-30`). The effort bounds below are author proposals, not supplied budgets or permission to run code. Engineering is the sourced research owner; ProductOwner owns any changed outcome (`input.md:16`).

| ID / owner | Question and proposed effort cap | Success evidence | Failure / impact |
| --- | --- | --- | --- |
| U-S1 / Engineering | U-Q1: within two engineer-days, assess persistence with reload/navigation and combined HostHarness session model | Actual API/spec references plus recorded cases where the same conversation, planning/building continuity and navigation context survive reload; session ownership is preserved | Missing spec, lost context, incompatible model or cap expiry leaves U-Q1 unresolved; ProductOwner must reshape the core or walk away under U1 |
| U-S2 / Engineering | U-Q2: within two engineer-days, enumerate supported authentication modes from actual specifications and assess inline PreviewAPI behavior under each | Attributable specification and executed results for every supported mode, covering allowed access and denied access without exposing preview content | Unknown mode inventory, untested mode or permission bypass fails clearance; ProductOwner must explicitly narrow preview scope or retain the stop |
| U-S3 / Engineering with ProductOwner decision | U-Q4: within one engineer-day, establish whether core continuity/result delivery depends on the unfinished feature; present evidence for the result-experience choice | Dependency evidence and completion proof if required, plus ProductOwner decision on streaming/completion-only | Unfinished required dependency or absent outcome decision prevents shaping; any exclusion must show the core no longer depends on it |

## Risk and clearance record

| Risk / grounded source | Mitigation and owner | Clearance status |
| --- | --- | --- |
| Persistent API existence mistaken for reload/session compatibility (`input.md:19-20`) | Engineering supplies U-S1 evidence | Missing; load-bearing core blocker |
| Session authentication mistaken for all-mode preview compatibility (`input.md:18-22`) | Engineering supplies U-S2; ProductOwner alone may narrow outcome | Missing; no approved exclusion |
| A readiness label launders unsupported proof (`input.md:23-24`) | Author rejects label; Engineering supplies actual records | Label rejected here; feasibility remains unproven |
| Unfinished dependency or undecided streaming adds work beyond the month (`input.md:8-11`, `input.md:25-26`) | Engineering supplies dependency assessment; ProductOwner resolves U3 | Missing; neither design direction selected |

## Exact next handoff

Engineering must provide the missing specifications, recorded seam evidence and dependency assessment. ProductOwner must resolve the required result experience and any proposed exclusions; all-mode preview remains desired until then. An exclusion cannot remove persistence/reload from the bet while pretending to preserve U1 unchanged. If scope changes, revise the frame/decision record and rerun G1; otherwise recheck G2 against the new evidence. The proposed total five engineer-day investigation is not a commitment and must fit the hypothetical month if accepted.

Stop at Research. Do not create pitch, diagrams, contracts, security-owner table, renders or betting preparation. Missing interfaces and owner details must not be invented to make a shaped document look complete.
