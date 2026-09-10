# Public GitOps controls

These **16 authored, synthetic, public** cases cover the incumbent's major jobs and the proposed candidate mechanisms. `cases.jsonl` contains requests/evidence only; `expected.json` is a public author-visible expectation guide. Neither is a held-out benchmark. Repeated letters stand for illustrative Git IDs; artifact digests are synthetic. No referenced provider, artifact, path, test, review or action was actually executed.

For a future producer, supply the selected case, [task-contract.md](task-contract.md), and only its assigned treatment. Do not supply this README, expected outcomes, fixture checker, research or author assessment. Because these controls are public, isolation from the answer file does not make them held out. An independent owner must create new confirmation cases outside candidate access and author history.

| Controls | What they distinguish |
| --- | --- |
| G01/G02 | Focused staged readiness versus mixed commit/PR scope, unrelated state and specialized handoffs |
| G03/G04 | Required GitHub status satisfied by its policy-permitted skipped conclusion, without preview execution, versus obsolete success after source change |
| G05/G07 | Allowed nonblocking failure versus failed required execution; actual cause versus invented flaky test |
| G06/G08 | Valid replacement train despite canceled old run versus inaccessible required provider |
| G09/G10 | Missing resource/wrong subject plus a second negative variant with matching identity but disallowed build parameters, versus valid package without required attestation |
| G11/G12 | Required commit/tag/asset parity violated versus publication complete with old installation |
| G13/G14 | Active/unique/offline-owned state retained versus safe squash-merge cleanup plan |
| G15/G16 | Focused current companion reviews versus partial authorized synthetic-action receipt and safe recovery |

Run `python3 reports/skill-improvement-campaign/skills/engos-quality-gitops-review/public-controls/check_fixtures.py` from the repository. It checks corpus integrity and that the declared distinguishing facts are present. Its output is static fixture evidence only. It does not evaluate a model, certify Git/provider behavior, judge semantic actionability or exercise a native producer/collector boundary.

`negative-output-controls.json` supplies seven deliberately wrong proposed claims for future independent assessor checks. Its current checker validates structure and case references only; **no assessor calibration has run or passed**. A future assessor must reject those claims for the stated reason and accept equivalent correct wording. G03's preview is a required status check whose skipped conclusion is permitted by policy, not an optional check; it did not execute. G09's extra variant is assessed within the existing G09 response, so there remain 16 producer cases. These authored controls are not evidence that a native injected fault fired. The proposed actual observation preflight is described in [evaluation-plan.md](../evaluation-plan.md).
