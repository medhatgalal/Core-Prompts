# Question and uncertainty register

Maintain linked candidate events and accepted snapshots, not repeated chat asks.
An uncertainty has a stable ID independent of question wording. Before asking,
inspect accessible relevant evidence and check prior answers. Engineering questions
test constraints/failure cases without imposing a design: freshness, tolerated
delay, volume, access boundaries, dependencies and recovery consequences.

| Record | Required fields |
| --- | --- |
| Uncertainty | ID, claim/gap, decision affected, source gap, included dependencies, blocking/advisory reason, evidence requirement set before research, owner or owner_unassigned, status, closure evidence or exclusion decision/dependency check, history |
| Question | ID, uncertainty ID, wording/version, why it matters, suggested respondent, acceptable evidence, proposed/accepted-for-investigation/answered/disputed/deferred/excluded status, answer provenance, next action |
| Question decision event | Actor/source/time, accept/edit/reject/defer, reason, prior wording and replacement ID/version; uncertainty effect explicitly separate |

Propose one to three high-value questions per turn. Give grounded options and a
recommendation with consequences when evidence supports them; allow “I don't
know,” delegate, defer or stop. Do not invent preference answers or turn a question
catalog into a mandatory interview. Optional refinements go to Later.

Count distinct decisions/evidence requests, including delegated teammate messages,
not numbered bullets or question marks. Do not hide six investigations in one
three-bullet card. Forwarding one existing artifact without requesting additional
investigation is one evidence request; separate requests to determine behavior,
find contacts or choose a preference each consume the question budget. Fill known
card metadata yourself and defer lower-priority asks to the next agreed checkpoint.

## Assistance ladder

1. Classify the gap as unknown fact, undecided preference or unknown owner.
2. For a fact, inspect existing evidence, explain its effect in the user's own
   scenario, then draft the smallest observable request. Supply a proposed
   hypothesis, likely source/expertise and safe inspection steps; label guesses.
3. For a preference, offer supported alternatives and consequences without
   choosing on the person's behalf. Identify the decision that needs authority.
   Give a concrete contrast when the user lacks vocabulary. For a freshness
   complaint, illustrate retrospective review of a completed period versus taking
   an action that depends on recent changes: the first can tolerate older complete
   data, while the second may not. Label these as examples, not known user behavior
   or a chosen threshold. Explain the trade-off, offer an appropriate choice, and
   accept unknown rather than forcing it. Do not prescribe polling, streaming or UI.
4. For an owner, explain the expertise/authority needed and help identify a person.
   Retain `owner_unassigned` until confirmed. Use `human-evidence` for a shareable
   card; do not send it automatically or require the novice to design the protocol.
5. If evidence is unavailable, offer a narrower request or scope decision. Finish
   independent work, then hold the dependent stage with owner and next action.

## Total effort checkpoint

Offer short-session or deeper-workshop effort, record the selected bound and
included phases. If none is chosen, explicitly label a default checkpoint after
two question rounds; it is a pilot default, not an inferred user requirement.
Track rounds and actual effort. At the bound show the next decision, settled facts
and few blocking gaps; offer continue, narrow, delegate or hold. Do not silently
extend. Stop asking when evidence suffices for the decision at the chosen scope;
optional precision is not a new blocker. Show the complete catalog only on request.

## Closure discipline

Rejecting/editing a question preserves its uncertainty and history. Deferred
blocking uncertainty still blocks. Closure needs an answer meeting the declared
evidence standard, or a confirmed scope decision plus dependency check showing
that included work no longer depends on it. Proposed closure stays candidate until
acceptance. Risk acceptance cannot manufacture facts or waive mandatory gates.
Conflicts stay disputed until resolved by the appropriate authority/evidence.
