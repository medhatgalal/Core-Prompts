# Experience Design: reusable lessons and remaining work

This harvest records lessons from the experience-design work through candidate commit `1207981117c778f0d8f8dcd13fdb1563e5be7a8b`. It separates observations, reusable principles and proposed implementation. It is case evidence, not a new standing policy, a behavioral promotion verdict or a claim that the missing protections are already installed.

The [evidence manifest](learning-evidence/manifest.json) binds eight exact receipts retained from the original experiment records. They remain available in Git after temporary workspaces are cleaned. The product scenarios are synthetic. Raw native/hook logs and private reasoning are excluded; historical paths in receipts are provenance, not current run commands.

## What is already durable

- The design skill's [state-failure probes](../../sources/capability-resources/engos-design-experience/references/state-failure-probes.md) distinguish persisted work, temporary drafts, uncertain commitment and subsequent edits. Its [review guidance](../../sources/capability-resources/engos-design-experience/references/compare-edit-compare.md) asks for the final working state, while preserving judgment over layout and review effort.
- The shared evaluator already binds complete supplied entry/resource content in [runner.py](../../src/core_prompts_eval/runner.py) and tests it in [test_resource_delivery.py](../../tests/test_resource_delivery.py). Supplying bytes is explicitly weaker than proving model consumption or compliance.
- The protected evaluator already checks signed, receipt-derived completeness, token accounting and promotion conditions. [.meta/evaluation-policy.json](../../.meta/evaluation-policy.json) remains advisory for source shipping. A structurally valid release, an accepted development trial and formal behavioral promotion are separate decisions.
- The current documentation cleanup preserves one canonical home for reference material, complete capability examples and an explicit release-comparison baseline. Historical records remain historical rather than being rewritten into apparent successes.

These protections should be reused. Another private result format, budget engine or collection of always-loaded instructions would create more places for the same knowledge to drift.

## Lessons to carry forward

### L1. The effective runtime is part of the treatment

**Observed:** requested dynamic tools and a native credential-denial canary passed, but both live sessions exposed an additional Playwright MCP tool; one used it successfully. Unfrozen pre-tool hooks also ran. The [independent audit](learning-evidence/runtime-invalidation.json) found no observed sibling/grader read, but did not establish the shared browser or hook boundary. The trial stopped as inconclusive.

**Reusable principle:** a fresh model conversation does not establish isolated files, browser state, tools or hook context. Declared tool configuration is not the observed tool surface. Configuration getters prove configuration readback, not execution isolation. Zero-model checks need an execution-path check capable of revealing what they cannot establish.

**Remaining owner:** adapter conformance and preflight in [adapters.py](../../src/core_prompts_eval/adapters.py), with the corresponding [protected runner](../../tooling/protected-evaluator/protected_runner.py) and tests. A bounded ordinary loop also needs the applicable evidence in its ledger.

**Acceptance example:** an unexpected inherited tool, shared browser context or changed relevant hook causes admission or continued execution to fail before its output is scored. Preserve existing security guards; isolate or freeze their effective configuration and dependencies instead of disabling them for a cleaner-looking experiment. Runtime-version-specific flags belong in a dated adapter diagnostic, not a universal prompt rule.

### L2. Test the whole measurement path before expensive comparisons

**Observed:** the earlier generator's direct local API request failed. Its original renderer lacked the fault controls needed for the new probes. Shared controls were added prospectively to both arms. An actual API self-check then caught a missing response-status field that syntax checks could not detect. Later, individually tested verifier and scorer components disagreed about retaining a confirmed failure alongside an evidence gap.

**Reusable principle:** checking components separately is insufficient. A representative observation must travel through the actual tool, collection, normalization and scoring path. Both arms need comparable usable access to the observations on which they will be assessed.

**Remaining owner:** existing adapter and evaluator integration tests, plus task-specific fixtures. Preregister any model-mediated canary and count it; do not invent an unbudgeted setup phase after a failure. Such a canary is limited execution evidence, not proof of a complete tool catalog or every security boundary.

**Acceptance example:** an actual committed response, an actually fired storage fault and the resulting owner/UI states survive serialization and reach the scorer with required fields intact. A dead injection or an armed-but-unfired fault cannot pass.

### L3. Bind what was actually supplied, and start revision pairs from the same state

**Observed:** the temporary harness initially validated a canonical job file without checking that the in-memory job actually dispatched was identical. The independent guard tests caught this. Earlier full redesigns also changed many artifact decisions at once, making small prompt effects difficult to distinguish from sampling variation.

**Reusable principle:** bind the actual supplied entry, selected resources, public task data and invocation payload. For revision comparisons, also bind equivalent starting product and environment state. Preserve repetitions, model settings and arm order; do not treat more judges as more independent builds.

**Already shared:** complete input/resource binding and paired call scheduling in [runner.py](../../src/core_prompts_eval/runner.py). **Remaining:** explicit initial-state receipts in adapter initialization/run plans and ordinary Auto-Research ledgers. Port the missing assertion into those contracts; do not replace the existing delivery mechanism.

**Acceptance example:** altered actual prompt bytes are rejected even when the canonical file is unchanged; a changed initial artifact, browser state or API fixture prevents a claimed matched pair. The V5.5 comparison used V5 plus shared public probes as its control; it was not a bare-model comparison.

### L4. Preserve confirmed failures even when the overall result is inconclusive

**Observed:** the independent [pre-fix check](learning-evidence/failure-loss-before-fix.json) reproduced a scorer dropping a confirmed failure when another evidence gap made the gate inconclusive. The [post-correction check](learning-evidence/failure-preservation-check.json) demonstrates that the failure is retained. The temporary implementation was corrected without changing the acceptance thresholds.

**Reusable principle:** observed failure and evaluation completeness are different facts. Missing evidence does not erase a defect already established. Empty collections, duplicated identities, blank explanations or an exit-success flag cannot stand in for proof.

**Remaining owner:** the existing public-result construction and tests in [protected_runner.py](../../tooling/protected-evaluator/protected_runner.py), plus the ordinary Auto-Research [scorecard template](../../sources/capability-resources/engos-optimization-auto-research/templates/scorecard.json.tmpl). Protected promotion already has strong completeness checks; the ordinary scorecard is weaker.

**Acceptance examples:** empty required gates cannot pass through `all([])`; duplicate judges cannot supply quorum; a confirmed state error plus a later collection gap returns an inconclusive run with the confirmed error still present. Keep detailed findings in protected evidence; expose only permitted aggregates or redacted references in public results. The shared public constructor currently omits this distinction, but that alone does not prove its protected evidence discarded a finding. Any public-result extension needs schema and disclosure-policy review.

### L5. Keep budget and time promises across failures

**Observed:** guard tests caught an insufficient whole-batch hold and a remaining-time check that trusted wall time while monotonic time had advanced. The [resolution receipt](learning-evidence/guard-resolution.json) records the unchanged 56-test suite passing after correction. After the live runtime mismatch, the [closeout](learning-evidence/interrupted-closeout.json) retained two incomplete charged turns and 1,399,235 reported tokens, with zero active turns or remaining holds.

**Reusable principle:** preserve actual spend, failed calls, unused reservations, the original clock and declared stopping rule. Reserve the planned comparison rather than letting an early arm consume another arm's opportunity. Reject work that cannot fit the remaining time. Do not quietly open replacement ledgers or reset deadlines to obtain a preferred outcome.

**Already shared:** preregistered call/token admission in [runner.py](../../src/core_prompts_eval/runner.py) and protected accounting. **Remaining:** an experiment-wide monotonic elapsed-time contract where time is a declared budget, integrated with the existing accounting and goal/ledger templates.

**Limit:** counted model tokens include cached/repeated input; they are not dollars or total project effort. Controller, authoring, setup, verification and review effort also matter. Budget that work prospectively rather than presenting a narrow token reduction as a complete efficiency win.

### L6. Judge the decision and its state owner, not only the initial screen

**Observed:** in the V6 development replay, both planning judges preferred the revised task support, but one preferred the earlier visual composition. The booking revision lost other composition/selection advantages. A [lost-reply probe](learning-evidence/lost-reply-observations.json) then reproduced a second distinct reservation while the UI confirmed only the later one. The [storage probe](learning-evidence/storage-observations.json) found a truthful page-only warning with an unexplained return of the older persisted plan; it did not show deletion of stored data.

**Already incorporated:** conditional context-at-action, final working-state review and selectable state-failure probes in Experience Design. Retain these principles without prescribing sticky panels, all facts above the fold, disabled editing everywhere or a fixed reviewer count.

**Acceptance examples:** old/current meaning remains understandable at the relevant action; a lost reply is treated as an unknown outcome rather than a failed operation; retrying an existing intent and creating a new one have distinct, visible consequences. Viewport captures can show co-visibility; full-page images show content and ordering. Browser simulations do not establish native-app behavior.

### L7. Keep conclusions proportional to the comparison

The [V6 results](learning-evidence/v6-comparison.json) contain local gains and regressions. They do not identify which prompt sentence caused either. The later invalidated runtime does not prove V5.5 is a bad candidate. Conversely, a good generated artifact does not prove a generally better skill.

Keep visual quality, task support, correctness and cost separate. Preserve negative ratings and disagreements. Known development cases are not untouched validation, same-model judges are not human participants, ordinal ratings are not percentages, and a few unsuccessful revisions do not establish a theoretical ceiling. Stop according to the declared bounded search rule; change a weak method explicitly rather than adding instructions until a score improves.

**Remaining owner:** ordinary Auto-Research experiment and ledger resources, with these distinctions carried into evaluation reports. This is a reporting and experimental-design improvement, not a new claim of statistical significance.

### L8. Decide the release basis explicitly; do not invent a universal blocker

The repository permits a reviewed source release as `structural_ready` / `behavioral_pending`. Formal promotion requires different evidence. This work's draft hold reflected its chosen measured-improvement bar, not a repository-wide prohibition on advisory releases.

Future plans need to distinguish three questions: whether a development trial improved its control, whether reviewed guidance is acceptable to ship with limits, and whether the formal behavioral baseline may advance. Establish the applicable authority and evidence before the run. Do not silently raise an advisory release into a formal-promotion requirement or lower an agreed measured bar after seeing results.

**Already canonical:** [.meta/evaluation-policy.json](../../.meta/evaluation-policy.json), [UAC usage](../../docs/UAC-USAGE.md) and [Capability Evaluation](../../docs/CAPABILITY-EVALUATION.md). Reuse these homes; the harvest adds no new release authority.

### L9. Documentation contracts should protect meaning and discovery

The docs work removed duplicated reference material, completed examples for all capabilities, corrected command write effects and fixed a second unpinned build that silently replaced the intended release-comparison baseline. Tests were updated to protect canonical contract content and working discovery links rather than requiring the same paragraphs everywhere.

**Already incorporated:** current docs and [test_public_docs_contract.py](../../tests/test_public_docs_contract.py). Stage the exact reviewed new-file inventory before tests that model Git-backed release mirrors; do not weaken package scope checks to accommodate untracked files. Retain timing failures and diagnose/rerun the affected check before claiming a clean full suite. Direct large machine reports to evidence files and inspect concise summaries.

Keep current guidance, immutable history and generated inventory distinct. Correct an active concept; do not rewrite a historical failure as success or create duplicate authoritative guides.

## Smallest next integration sequence

| Priority | Work | Current disposition | Completion evidence |
| --- | --- | --- | --- |
| 1 | Effective runtime/tool/hook inventory and execution-path admission | Missing shared protection; version-specific diagnosis exists | Actual admitted surface matches observed exposure; safety guards preserved; unexpected providers/context rejected |
| 2 | Ordinary per-gate evidence and retained confirmed-failure fields | Proven in temporary harness; partly present in protected path | Ported tests reject empty/mismatched proof and retain known failures under inconclusive |
| 3 | Same-start state receipts and total elapsed-time admission | Partial shared support | Paired state equality and monotonic remaining-time negative tests in existing adapters/ledger |
| 4 | Ordinary Auto-Research templates and focused usage documentation | Proposed; not applied by this harvest | Templates record the implemented contracts and evidence limits, with no new parallel framework |

Each follow-up belongs in its listed canonical owner with an appropriate focused regression, review and normal repository delivery. Changes to skill behavior still follow SSOT/UAC and regeneration; this document does not implement or waive that work. Candidate and failed-study identities stay preserved. Remove temporary working areas only after useful evidence has a durable, verifiable location.

The parts worth generalizing are the supported principle and its preventive check. Runtime-version specifics, unmeasured hypotheses and case judgments remain qualified evidence. This is how the next task can reuse the work without inheriting a larger prompt or an unsupported rule.
