# Scenario clarifications for the second author round

These are explicitly authored exercise inputs, not real human decisions or
observed runtime results. Round-one authors must finish before consuming them.
The same quality criteria apply in both rounds; these facts resolve or sharpen
the scenario, not redefine a previous score to make it pass.

## engos-example-model-capacity

M2: Missing capacity must be represented as absent/unknown, never zero, unlimited
or a guessed default. Do not expose output-token capacity under the same name.
Keep valid older callers functioning without requiring them to handle a new
mandatory field. Preserve known positive input values exactly. The only
acceptable cuts are optional presentation polish; do not cut these semantics.
Keep the two-engineer-day appetite and original walk-away. Address the review's
weakest actual finding even if the first proposal already anticipated M2.

## engos-example-insight-visibility

I1: The hypothetical requester wants product managers to see daily adoption
counts without filing support requests; improving generated-insight content or
ranking is out of scope. Appetite is one week with one engineer. Kill the bet
if publication needs customer text, new metric computation or a new analytics
service. Success is that the existing viewed/generated daily counts appear in
the existing internal reporting tool for permitted product-manager users.

I2 fixture facts: an approved aggregate schema S1 already contains pseudonymous
account ID, UTC date, viewed count and generated count. The existing daily intake
accepts S1 and replaces the same account/day record idempotently. Metric reads use
the existing service credential; product managers use the existing platform role.
Only aggregate counts and a pseudonymous ID may cross; no document text or prompts.
Source aggregates retain 30 days. Scenario volume: 1,000 accounts/day; the approved
platform quota is 10,000 records/day. Publish from activation forward; history is
Later, not a hidden completeness requirement. No live observations are asserted.

## engos-example-config-deployment

C2: Distinguish an absent section (preserve target), an explicit empty list
(also preserve under this additive-only bet), and a nonempty valid payload
(apply only after authorization, compatibility and override checks). Configuration
deletion is Out. A target edit between validation and commit must produce the
existing conflict outcome; it cannot be overwritten silently.

C3 fixture clarification: the existing transaction's revision comparison occurs
at commit, not only at initial validation. It rolls back all package changes on
conflict. This is a scenario contract premise, not a newly executed race test.
Both zero and positive activity-cost values are valid, but negative values and
unsupported currencies fail validation. Unrelated target settings remain intact.
The analysis refresh occurs on its next normal scheduled run; no resync is added.

C4 (added in response to the actual C-CAPACITY and C-EMPTY review findings):
the hypothetical decision-maker limits the supported package to 100 processes,
200 activity entries per process and at most 4,000 other configuration records.
With the proposed one-currency-record-per-process representation, the maximum is
24,100 total records. Larger packages are outside this example's supported
envelope and must be rejected intact; never split an atomic package silently.
Valid currency-only input updates currency while preserving target activity
entries. An absent cost configuration preserves both. A present empty activity
list preserves target activities; deletion is excluded. A failed source read
aborts export rather than being represented as absence. Malformed values fail
validation. These are explicit added scenario constraints, not facts retroactively
attributed to round one's input or claims that a runtime test was executed.

## engos-example-unified-chat

U2: The hypothetical requester confirms persistence and inline preview as core;
all supported authentication modes remain required. Streaming subagent activity
can be Later. Keep the one-month box; do not extend it. The existing chat component
is a possible reuse candidate, not proof that the combined session works.

No prototype, current preview/auth API specification or reload integration
evidence is supplied in round two. The correct outcome remains blocked at
Research if those material questions cannot be resolved. Improve the named
spikes' question, owner role, bound, observable pass/fail and decision impact;
do not pretend the missing artifacts were provided merely to reach a happy ending.
