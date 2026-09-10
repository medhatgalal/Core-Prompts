# Make the test's claim inspectable

For each high-risk behavior, connect the requirement to a controllable precondition,
action and externally observable result. A useful test can fail for a concrete
violation while allowing a valid alternative implementation. Name unresolved
requirements; do not derive the only oracle from the code being tested.

Distinguish four statements: a scenario was suggested; a test was generated; a
runner executed it; and the observed result supports a particular behavior. Preserve
provided revision/environment/command evidence and state which steps remain unrun.
Do not upgrade one statement into the next without evidence.

Read assertions as well as coverage. A test that only calls a function, checks a
mock was invoked, or snapshots a large object may not protect the behavior at risk.
Conversely, public dependency call counts can be the correct oracle for a bounded
retry contract. Decide from the contract, not a blanket ban on mocks or snapshots.

If implementation and requirement conflict, expose the disagreement. A regression
test may intentionally fail the current implementation; label the expected failure
and the proposed behavior instead of presenting it as a verified passing test.
For an already-correct implementation, needless tests are not an improvement.

Use examples, properties or a small independent state model as appropriate. Explain
why the chosen oracle is independent enough to catch the suspected error; a second
copy of the same algorithm is weak assurance. Do not add framework dependencies
just to satisfy a preferred testing technique.
