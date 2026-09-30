# Synthetic Research candidate note

This is a controlled teaching fixture, not product research, a genuine accepted
workshop, or stage acceptance. No source was executed.

## U1 — What do the retained source and its checks establish about eligibility and route call sites?

- **Decision affected:** the description of current eligibility behavior and the
  call-site coverage represented by the supplied source.
- **Sufficiency:** inspectable supplied code and checks establish source-level
  behavior in the cited ranges; they do not establish observed runtime behavior.
- **Sources and coverage:** `source.py:1-14` (eligibility set and function,
  route function, sample, and test); `caller.py:1-4` (a separate caller);
  `rules.py:1-4` (callee implementation). These are the complete supplied
  source files, not a repository-wide search.
- **Claim / evidence:** E1, `source.py:1-14`, code inspection. The allowed set is
  `{"ready"}`; `eligible(state)` tests membership; `route(state)` returns that
  result. The sample calls `route("ready")`; the test calls it with both
  `"ready"` and `"paused"`, asserting true and false respectively
  (`source.py:3-14`). The draft's claim that `route("paused")` returns true is
  contradicted by the implementation and the supplied assertion; the supported
  source-level result is false.
- **Classification and limits:** inspected code and an assertion are source
  evidence, not an observed execution result. No execution was observed. The
  supplied files do not establish call sites outside these files.
- **Conflict, risk, mitigation:** the initial draft summary conflicts with its
  own quoted assertion. Corrected here against the supplied implementation and
  assertion. No separate operational risk is evidenced.
- **Owner / proposed disposition / next action:** synthetic Research author;
  ready as a bounded source-level answer, subject to independent review; retain
  the no-execution limitation.

## U2 — What calls and argument values do the listed inspected ranges cover?

- **Decision affected:** whether the described call-site coverage and argument
  values match the inspected source.
- **Sufficiency:** the cited ranges establish calls visible in those ranges only.
- **Sources and coverage:** E1, `source.py:9-10`, covers the sample call;
  E2, `source.py:12-14`, covers both test calls. The supplied `source.py` is
  inspected in full (`source.py:1-14`).
- **Claim / evidence:** E1 shows `sample()` calling `route("ready")`. E2 shows
  `test_route()` calling `route("ready")` and `route("paused")`. Across these
  cited calls, the values are therefore `"ready"` and `"paused"`, not only
  `"ready"`. All three visible calls in `source.py` are accounted for; the
  separate supplied caller is addressed under U3.
- **Classification and limits:** source-level occurrence inventory; not a
  repository-wide or dynamically observed call-site inventory. Comments and
  examples are not being counted as executable calls.
- **Conflict, risk, mitigation:** the follow-up draft's statement that “the
  opened ones use only the ready value” conflicts with E2. Corrected by naming
  the ranges and their respective values. No additional risk is evidenced.
- **Owner / proposed disposition / next action:** synthetic Research author;
  ready within supplied-file scope, subject to independent review; broader
  call-site claims require additional authorized source coverage.

## U3 — What existing behavior determines the route result?

- **Decision affected:** whether the supplied implementation already
  determines the result, within the inspected source scope.
- **Sufficiency:** caller and callee implementation are both needed for this
  source-level explanation; both are supplied and inspected.
- **Sources and coverage:** E3, `caller.py:1-4`, imports `eligible` and returns
  `eligible(state)` from `route(state)`. E4, `rules.py:1-4`, defines
  `ALLOWED_STATES = {"ready"}` and returns membership from `eligible(state)`.
  E1, `source.py:1-5`, shows the separate `route` implementation with the same
  delegation. These are supplied-file references, not proof of repository-wide
  ownership or uniqueness.
- **Claim / evidence:** for the supplied implementation, `route(state)` returns
  whether `state` belongs to `ALLOWED_STATES`; as supplied, only `"ready"` is
  in that set. Thus the implementation accounts for the `"ready"`/`"paused"`
  results shown in the source and checks. The follow-up draft's “callee has not
  been opened” and “result is unknown” claims are corrected: `rules.py` was
  supplied and inspected. The proposal that a new policy engine may be required
  is unsupported by this evidence and is not a Research conclusion.
- **Classification and limits:** inspected source establishes the stated
  implementation; no execution, design intent, external callers, or need for a
  replacement has been established.
- **Conflict, risk, mitigation:** the draft omitted the supplied callee and
  inferred a new component from that omission. Corrected by inspecting the
  provided callee and bounding the conclusion to supplied files. No load-bearing
  unknown requiring a spike is identified by this packet.
- **Owner / proposed disposition / next action:** synthetic Research author;
  ready as a bounded current-source account, subject to independent review.
  Any claim about other implementations or product scope needs separate
  authorized evidence or a human decision.

## Overall limitations and handoff

Evidence IDs E1-E4 refer only to the supplied source files and line ranges
above. No repository search, source execution, architecture assessment,
experiment, human decision, receipt, score, or stage verdict was performed or is
claimed. Return this candidate note for independent review; the conductor retains
all acceptance and state-transition authority.
