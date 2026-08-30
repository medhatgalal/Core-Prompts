# Goal Design Lessons

This reference supersedes the earlier single-sided preflight guidance for goal/spec/verifier authoring. It is distilled from a live goal that passed twice with green CI while its stated outcome remained unmet. The operational lesson is simple: a goal is satisfied by its verifier, so verifier design controls whether the goal is honest.

## Three Failure Classes

### Artifact boundaries collapse
The goal, prompt, and response restate the specification until different actors measure different text. Keep the goal and prompt short and reference `spec.md`; do not compress the specification into the goal.

Measured examples: one goal fell from 4,062 to 914 characters after extraction, and one prompt fell from 5,379 to 968 characters after it referenced rather than repeated the specification.

### The metric is not the outcome
Designing the metric after the plan encourages convenient mechanism checks. Write the outcome anchor first. Exactly one load-bearing criterion must express a world-state delta against a frozen identifier set. It must never sit in an advisory block. Measure the population before setting the target, and refuse dispatch when the outcome cannot be checked.

Common failures include forgeable records, counts distorted by set churn or cascades, status movement without work, proxies that move without the outcome, and targets that are arithmetically or operationally unreachable.

### The judge is part of the system under test
Negative checks may pass on a tree that never contained the work. Text matching invites code to be reformatted for the judge. Cwd-derived evidence roots shape execution around the measurement. Piped tests may observe the wrong process exit code.

Require an explicit evidence root, introspect API shape, measure the verifier process directly, and pin the verifier hash when it remains inside the executor's writable scope.

## Two Highest-Leverage Rules

1. Design the metric before the plan, then attack the metric rather than polishing the plan.
2. Give the verifier more adversarial review than the implementation because it decides whether "done" is true.

## Two-Sided Verifier Validation

Falsifiability asks whether the verifier fails on the untouched tree. Hostile pass asks whether the cheapest fake implementation can pass without the outcome. Both are blocking.

For each criterion, record the cheapest fake and its block:

| Fake | Required block |
| --- | --- |
| hand-edit tracked state | a departure without a bound receipt fails |
| emit evidence from a probe | a run id without an execution receipt fails |
| record one item for a cascade | undisposed children fail |
| move status without work | no post-baseline change fails |
| delete tests | new skips/xfails or a lower test count fail |
| reformat for a regex | API shape is introspected instead of grepped |

Publish an exit-gate truth table covering misconfiguration, untouched state, cheapest fake, partial work, machine-ready/operator-pending, and achieved.

## Five Written Answers

No generic tool can answer these design questions. A blank answer blocks sealing and dispatch.

### PROXY
Could the metric move while the outcome does not? Name the concrete scenario.

### FORGERY
Who besides real work can write the evidence? What binds it to a run that happened?

### ARITHMETIC
Walk one awkward instance end to end. Does the metric add up for cascades or partial work?

### ACHIEVABLE
Measure the population. Which members can reach the target, and which require another disposition?

### TRAP
If every implementation step landed and the anchor did not move, does the verifier fail?

## Round 2: Four Author-Side Failures

### Anchor granularity
Do not combine proving a route with draining its entire backlog. Prove the mechanism over a small measured sample with real work evidence, then put bulk execution under a policy or routine owned by the actor who can authorize it. If the author cannot grant a permission required by the anchor, the artifact is a queue rather than a runnable goal.

### Per-criterion flip testing
Whole-suite hostile testing does not prove that each criterion discriminates its own condition. Inventory every machine criterion, execute the exact criterion logic against synthetic condition-present and condition-absent trees, and require exits `0` and `1` respectively. Equal verdicts, inverted verdicts, or error exits block sealing even when printed output looks correct.

The observed failure used a recursive/count grep whose zero-match output contained both a filename-prefixed count and an appended zero. An integer comparison then failed on a non-integer while displaying zero, making the complete suite impossible to satisfy.

### Population versus exclusions
Before freezing the anchor sample, intersect it with every exclusion and do-not-touch list. Any overlap is a contradictory specification and blocks the baseline. Repeated implementer questions about the same contradiction are defect reports about the spec.

### Judge-fix disclosure
A verifier repair after dispatch has the shape of moving the goalposts. Publish an amendment with the one-line diff, previous and new hashes, changed and unchanged criterion IDs, and an instruction to diff before trusting the next green run. The implementer reports judge defects; the author repairs and discloses them.

## Known Gaps

- `goal-lint` mechanizes artifact checks, population/exclusion intersection, and per-criterion flip behavior. Arithmetic and forgery still require written reasoning.
- Hash pinning detects writable-verifier tampering only when another actor checks the hash. Prevention needs an oracle outside executor write authority or an operator-owned run.
- Goal-iteration conventions remain practitioner folklore unless a task-specific budget is supplied or a host default is measured.
- These rules are evidence-informed but the complete bundle has not yet earned behavioral promotion through controlled comparison.

## Evidence Status

Measured in the source incident: five records split into two real dispatches and three phantom drops; a frozen failed set of 53 items included 19 with neither worktree nor branch; one status departure had no post-run commit; goal and prompt size reductions are listed above. Treat these as provenance for the rules, not as universal thresholds for unrelated repositories.
