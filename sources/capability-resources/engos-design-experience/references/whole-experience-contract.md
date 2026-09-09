# Keep meaning through the whole experience

Use when a task spans views, services, or revisions. Keep the smallest useful contract in existing design notes or implementation; no separate document is required. One owner integrates shared decisions when contributors divide the work.

| Concern | What needs one coherent meaning |
| --- | --- |
| Object | Stable identity of the item being read, compared, edited, or committed. |
| State | Authority for source facts, local draft, persisted state, and derived display. |
| Decision | Comparison basis, current proposal, relevant conditions, and the meaning of the action. |
| Continuation | Selection, unfinished input, return context, and recovery that matter after a transition. |
| Foundation | Vocabulary, visual encodings, navigation, and target conventions. |

Preserving context does not mean keeping every source paragraph permanently visible. Preserve **meaning and access** across transitions; choose how much is visible for the current task.

## Distinguish identity, evidence, and detail

In a plan comparison, short unambiguous names establish saved and draft membership. Exact changes establish the quantitative difference. A concise explanation of the added and omitted benefit establishes the practical exchange. Full descriptions and operational notes remain available without rebuilding the comparison in memory.

Place decision-changing qualifications beside the claims they affect, with enough prominence to survive scanning. “85 hours, if existing rails fit” is different from an unqualified “85 hours” with a remote note. Further explanation can open in context or have a clear return path. Do not conceal a disqualifying condition merely to shorten the page.

At commitment, replacement, or retry, check access to the baseline/current basis and the decisive exchange in the actual task state. When a short summary would prevent reconstructing the comparison, place it before the action. Inspect this relationship in narrow and focused states where relevant to the target; an initial overview does not establish useful context later. Full background detail can remain elsewhere with a useful return.

A compact summary should not become a second dense document. If persistent context crowds the evidence or controls, consider a smaller state readout, an adjacent review step, or platform-native navigation. No sticky treatment, simultaneous visibility, or above-the-fold placement is universally required. Test the actual transition and return; a link somewhere on the page does not establish useful access.

## Trace a change, not every possible state

Follow **fact → derived meaning → prominence → available action → dependent states**. A changed requirement may alter suitability without replacing the selected object or erasing its draft. A changed report question may alter comparison order without changing source facts.

A saved snapshot and editable draft remain distinct even when values match. A pending service operation remains different from success even when the optimistic appearance matches it. Inspect the affected dependencies and use [API guidance](api-and-state-design.md) for service-backed behavior. Preserve independent choices and still-valid evidence.
