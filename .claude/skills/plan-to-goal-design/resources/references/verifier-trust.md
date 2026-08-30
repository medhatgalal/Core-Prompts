# Verifier Trust and Stop Conditions

## Trust Is Write Authority
A hash proves that a visible artifact changed. It does not make an executor-controlled verifier independent. Classify the actual authority topology before allowing the verifier to decide completion.

### `external_oracle`
The executor cannot modify the runner, expected values, sealed cases, or truth source. Examples include protected hosted CI, an operator-owned service, or a test harness outside the executor's writable scope.

### `operator_gate`
Machine checks cover part of the outcome, while a named person must observe or approve the remaining criteria. The terminal state before acknowledgement is `APPROVAL_REQUIRED`, not achieved.

### `sealed_visible`
The verifier is visible and its hash is sealed, but the executor can see its criteria or may have enough authority to replace the surrounding check. It may prove machine readiness when unchanged. It is not automatically an external completion oracle.

### `self_check`
The executor owns the verifier or success narrative. Use it for iteration feedback only. It never decides final completion.

## Baseline Falsifiability
Before execution, run the verifier on the untouched candidate state. Require:
- a nonzero exit code expected by the packet
- each named unmet criterion identifier in the output
- evidence that the relevant code path or artifact was actually inspected
- no failure caused solely by missing tools, malformed setup, or unrelated infrastructure

If the verifier returns zero, stop. Audit whether the outcome already exists and whether the verifier is permissive. Do not convert the result directly into `NO_GOAL_NEEDED`.

## Hostile Pass
Construct the cheapest tree that makes convenient mechanism checks look complete while leaving the outcome anchor unmoved. Run the same verifier against it. A zero exit is a blocking verifier defect. A nonzero exit caused only by malformed setup is also a defect; the output must name the unmet anchor or criterion.

Publish a truth table for misconfigured, untouched, cheapest-fake, partial, machine-ready/operator-pending, and achieved states. Test the verifier process directly rather than observing a downstream command in a pipe.

## Anti-Gaming Review
For each criterion, identify the cheapest way to make it pass without satisfying intent. Where relevant, check for deleted tests, new skips or xfails, weakened thresholds, hardcoded fixtures, empty logs, missing execution, one-sided paired surfaces, or changed verifier inputs.

## Exit Semantics
- `0`: machine criteria covered by this verifier passed
- `1`: named goal criteria remain unmet
- `2`: packet, environment, dependency, or verifier contract is invalid or stale
- `3`: machine-ready but operator acknowledgement is still required

The packet may declare additional nonzero baseline codes, but zero is never an expected untouched-tree failure.

Invoke Bash verifiers as `bash verify.sh`. Capability resources and packet verifiers may be mode 644; executable permission is not part of the trust contract.
