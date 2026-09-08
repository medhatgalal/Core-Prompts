# Frontier capability modernization — verification report

Implemented the approved Supercharge, UAC, and Auto-Research changes on an isolated branch from c9d6de07. The original task was clarified before execution: every claim is tied to reproducible evidence and its limits; no claim of irrefutability or universal model superiority is made.

## Results

- **913 tests and 122 subtests passed** in the clean full-suite run.
- Build, strict surface validation, complete topology/contract checks, and static calibration passed. CLI smoke completed; Gemini discovery timed out locally and is recorded as a warning.
- Independent source reviewers accounted for the current and historical requirements. Earlier findings and corrected revisions are preserved.
- Independent UAC review verified 138 selected tests and 14 real review-lifecycle cases after resolving seven findings.
- Independent resource review verified 225 route assemblies across 18 emitted helpers and four actual subprocess deliveries. Original source locations and stale/missing-resource rejection were checked.
- Live Supercharge demonstrations used real subagents: two actual candidate trials (improvement then tie), a four-pass review, execution suppression, an authorized write of exactly `42`, and independent plain-English catchup verification. All 34 final checks passed.
- Live Auto-Research ran three genuine trials: correctness improved from 6/16 to 16/16; correct candidate AST sizes fell 60 → 19 → 14. Separate controls exercised rejection, ties, disposal, continuation, and evaluator integrity. Independent reviews performed 155 initial and 76 transition checks. These are fixture results, not speed or generalization benchmarks.
- One monthly research-only model-guidance heartbeat is configured, quiet when unchanged. Future scheduled execution has not yet been observed.

## Element-by-element evidence

The [32-item register](acceptance-register.json) preserves S01–S19, U01–U07, and A01–A06 with evidence classes and limits.

| Scope | Independent evidence |
| --- | --- |
| Supercharge S01–S19 | [Source review](reviews/supercharge/review.md), [live demonstrations](live-checks/REPORT.md) |
| Auto-Research A01–A06 | [Source review](reviews/auto-uac/final-review.md), [actual experiment and controls](live-auto-research/report.md) |
| UAC U01–U07 | [Code review](reviews/uac-code/FINAL-REVIEW.md), [resource/evaluator review](reviews/resources-final/RECHECK.md) |
| Documentation and discovery | [Independent final assessment](reviews/docs-final/final-assessment.md) |
| Canonical application | [Readback](canonical-readback.json), [compact UAC receipts](uac-application-receipts.json) |
| Local checks | [Full-suite result](verification-suite-status.json), [test log](verification-suite.log), [JUnit](verification-suite.xml), [validation](final-validation.log) |
| Monthly refresh | [Saved configuration receipt](automation-receipt.json) |

## Limits

Source review, structural tests, resource assembly, actual transport delivery, model behavior in bounded demonstrations, hosted CI, installation, and formal promotion are distinct. These changes remain **behavioral_pending** under the protected evaluation policy. No Fable/Sol/Astra/Grok-wide superiority, guaranteed resource comprehension, native discovery across every host, home installation, or versioned release is claimed.

Hosted PR/MR and post-merge parity evidence is supplied in the delivery receipt and task response after those gates complete. Historical raw plan/judge/apply outputs and diagnostic logs are retained in raw-evidence.tar.gz; reports are evidence, never canonical rebuild input.
