# Unified chat — Research, evidence still missing

Current round-2 G1 passed before this artifact. Sources: `engos-example-unified-chat/input.md`, U2 at `round-two-clarifications.md:66-75`, and the recovered assigned-case independent-review entries. This is fixture inspection, not live API research or executed prototyping.

| Question | Disposition / actual finding | Opened source |
| --- | --- | --- |
| U-Q1 | needs_spike: persistence exists but reload/navigation and combined HostHarness-session compatibility are not evidenced | `input.md:17-20`, `round-two-clarifications.md:71-72` |
| U-Q2 | needs_spike: inline preview across every supported auth mode remains core; API specifications, mode inventory and integration results are missing | `input.md:17-22`, `round-two-clarifications.md:66-67`, `round-two-clarifications.md:71-75` |
| U-Q3 | answered: unsupported “prototype confirmed” label still supplies no clearance; no new prototype evidence was added | `input.md:23-24`, `round-two-clarifications.md:71-75` |
| U-Q4 | needs_spike: streaming subagent activity can be Later, but no evidence establishes whether the retained core depends on unfinished sub-agent functionality | `input.md:25-26`, `round-two-clarifications.md:67-69` |

## Bounded proposed evidence requests, not executed spikes

Engineering is the research owner; ProductOwner owns outcome/reshape decisions (`input.md:16`). The following bounds are author proposals, not approved spending or added time. The total proposed cap is five engineer-days within the unchanged month, subject to separate execution authorization (`input.md:8-10`, `round-two-clarifications.md:68`). Lack of access, specifications or results within a cap is an unresolved failure, never inferred success.

| Spike / question / owner | Proposed bound and evidence to collect | Observable pass | Fail / decision impact |
| --- | --- | --- | --- |
| U-S1: Does the same development conversation remain usable through planning/building, reload and navigation under the combined session? / Engineering | Two engineer-days. Obtain persistence/session contract references, source revision and attributable before/after run records for reload during planning, after entering building, and navigating away/back. Capture conversation/session identity and relevant navigation state. | Each case retains the intended conversation and plan/build context, with no cross-session exposure or lost/duplicated content attributable to the transition. Record environment, steps and expected/actual outcomes. | Missing contract, lost continuity, identity mismatch, access failure or cap expiry leaves U-Q1 blocked. ProductOwner must stop or explicitly reshape U1, not rename broken persistence a risk. |
| U-S2: Does inline PreviewAPI content work and remain access-controlled in every supported auth mode? / Engineering | Two engineer-days. Obtain current preview/auth specification and explicit supported-mode inventory. Collect per-mode authorized-preview and denied/expired-session evidence, tied to source/environment revision. | Every documented supported mode displays permitted content and withholds unauthorized content; results remain correctly associated with the conversation. No untested mode. | Unknown inventory, unsupported mode, missing result or leaked content leaves U-Q2 blocked. U2 does not permit silently dropping modes or moving preview Later. ProductOwner must make any different core decision explicitly. |
| U-S3: Does retained persistence/preview/build continuity require the unfinished sub-agent feature once streaming activity is Later? / Engineering | One engineer-day. Trace only required dependencies from actual source/specification and collect completion/integration evidence for any required unfinished feature. | Evidence establishes either that core does not depend on unfinished functionality, or that every required dependency is complete and compatible. Deferring streaming alone is insufficient. | An unproven/unfinished required dependency leaves U-Q4 blocked. ProductOwner decides whether to reshape or walk away inside the month; no automatic extension or fabricated completion. |

Criteria above are proposed observations to collect, not facts about current internals. No endpoint, field name or implementation method is invented.

## Risk, mitigation and clearance

Persistence existence is not compatibility evidence; Engineering must supply U-S1 (`input.md:19-20`). Caller session authentication is not all-mode preview proof; Engineering must supply U-S2 (`input.md:18-22`). Moving streaming Later is not proof of dependency independence; Engineering must supply U-S3 (`input.md:25-26`, `round-two-clarifications.md:67-69`). Reusing the chat component cannot clear any of these risks (`round-two-clarifications.md:69`). All three clearances are missing.

## Exact next action and stop

Obtain Engineering's specifications and actual seam/dependency records. ProductOwner has now resolved core-preview and streaming-activity scope through U2; do not ask those same questions again or invent a completion-only implementation choice. A new exclusion of persistence, inline preview or an authentication mode would contradict U2 and require a changed fixture decision plus another G1 check. With scope unchanged, recheck G2 only when actual missing evidence is supplied. Until then stop at Research: no pitch, diagrams, contracts, security matrix or render request for this case. No stage-three score is assigned.
