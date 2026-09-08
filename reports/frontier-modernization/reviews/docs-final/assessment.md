# Independent docs and user-contract review

Reviewer: `/root/review_docs_final`. Base HEAD: `c9d6de07b4d1918970a5f70350cf50200a6a0ff4`; branch `AI/frontier-capability-modernization`; authorized worktree verified. Assessment: **changes requested** for three remaining reference/contract issues. File hashes in `snapshot.json` bind this assessment to the reviewed dirty candidate; this is not a review of later edits.

## Current State

Reviewed README, GETTING-STARTED, EXAMPLES, UAC-USAGE, CLI-REFERENCE, FRONTIER-MODERNIZATION, CHANGELOG; the three current SSOTs; all Supercharge module/shared/model/help resources; Auto-Research workflow/delivery/templates; current descriptors and selected topology/fixture output; the automation receipt and the saved local automation configuration. Read relevant UAC quality/review-binding code, topology compilation, and emitted loader behavior. No provider calls, delegation, implementation edits, installation, or release operations were performed.

## What Belongs Where

README and getting-started provide discovery and the initial invocation. EXAMPLES holds concrete asks and expected outputs. UAC-USAGE and CLI-REFERENCE own the exact intake/loader interface. FRONTIER-MODERNIZATION provides the cross-capability explanation and explicit evidence boundaries while linking to canonical SSOT/resources. CHANGELOG correctly places this work under Unreleased. This placement is appropriate; no document move is needed.

## Drift Findings

1. **P2: Current mode provenance points outside its claimed source.** `.meta/capabilities/engos-meta-supercharge.json:217-220` names `ssot/engos-meta-supercharge.md` and line 303 for ULT, but the current entry has 292 lines and the module lives in `sources/capability-resources/engos-meta-supercharge/references/modules/ult.md:1`. The same expanded-content offset issue affects every resource-extracted Supercharge mode and the topology mode summary (`evals/topologies/engos-meta-supercharge.json:33-36`). These are current source references, not historical baseline evidence. `src/core_prompts_eval/topology.py:117-120` concatenates resources before mode extraction, which loses the source-file boundary. Correct the generator to emit actual resource path and local line (or an explicitly identified virtual assembled source), then regenerate. Validation: each current mode reference resolves to the stated heading in its named file.

2. **P2: The current validation matrix still requires the replaced agentic heading.** `.meta/capabilities/engos-meta-supercharge.json:803-810` requires `### Agentic Orchestration (Core Principle, Not a Module)`, while the approved current contract is `### Independent Subagents (Core Principle, Not a Module)` at `ssot/engos-meta-supercharge.md:216`. Historical baseline scenario reports may retain the old text, but the top-level current `quality_validation_matrix` should validate the current approved contract. Update that one current marker while preserving all other curated matrix content and historical lineage, then regenerate. Validation: current matrix markers resolve in the effective package, with historical snapshots unchanged.

3. **P2: The UAC worked judge sample uses an obsolete status and implies readiness before repair.** `docs/UAC-USAGE.md:157-168` displays `Quality status: ship` and says the candidate is ready for apply after examples are expanded. The same guide says `structural_ready` replaces `ship`; current `run_quality_loop` returns `structural_ready` or `manual_review`, and changing the candidate requires fresh judgment/bindings. Use a consistent blocked example (`manual_review`, repair then rerun judge) or a passing example (`structural_ready`, no required remaining repair). Validation: the sample matches an actual status and never implies a changed candidate inherits prior approval.

Earlier findings fixed during this review and re-read: GETTING-STARTED:11 now states up to ten actual independently graded trials and plateau; the `basis_full` acceptance fixture now uses that budget; the retired global-stop fixture was replaced with help precedence while `/stop-ult` remains. No active global-stop/guaranteed-ten behavior remained in the scoped current human docs or resources after those corrections.

## Recommended Changes

Resolve the three findings above in their authoritative locations and regenerate affected derived metadata. No broader rewriting is needed. Recheck the snapshot after those changes and retain the distinction between historical baseline evidence and current requirements.

## Examples of Good Output

- `supercharge /ult /full <prompt>` has an explicit no-execution announcement; ULT persistence is preserved. Normal ULT displays the prompt then executes only within already authorized scope; draft/review-only suppresses execution.
- `/grade` uses actual inspectable candidates, independent grades, incumbent retention, the four unchanged section labels, and a documented target/plateau rule. The first successful rewrite cannot alone end it.
- Catchup table rows and visible validation text, contract QA JSON, and all 13 Gaslight technique IDs/names compare unchanged against HEAD. Basis, Simple Made Easy, and inversion have distinct task mechanisms. Gaslight efficacy is explicitly experimental.
- Auto-Research distinguishes original baseline, incumbent, trial, protected evaluator, actual execution, keep/discard, and search after both wins and losses. Trial acceptance remains separate from formal promotion.
- UAC review-binding prose matches hash/coverage/provenance checks in `uac_baselines.py`; identity strings and line-span coverage are explicitly not semantic authentication or behavioral proof. The resource loader examples for `/grade`, `/adversarial /debate /deep`, and `details` all returned valid bundles, exit 0, and `assembled_not_proof_of_consumption`. Plan/judge/apply help all accept `--requirement-review`.
- All local Markdown link targets in the seven scoped human documents exist. Focused diff whitespace checks passed.

## Review Timing

Repeat the focused docs/metadata check after these fixes and surface regeneration, before commit/PR/MR readiness. If adjacent upstream changes are integrated, recheck their effects. Any release or installation needs its separate current package, deployment, and readback evidence.

## Open Risks

This review verifies instruction contracts, current local implementation references, exact output preservation, CLI availability, and local saved automation configuration. It does not establish runtime obedience across native hosts, independent grading efficacy, protected behavioral promotion, model superiority, hosted CI, merge, installation, or release. External model/research links and their factual claims were not refreshed because provider calls were excluded from this review; the table labels its claims as dated provider guidance or locally unmeasured hypotheses.

The saved `model-guidance-refresh` heartbeat agrees with `automation-receipt.json`: active monthly schedule on day 1 at 09:00, canonical main-checkout model-table path, research only, proposed changes for review, no repository/model/install/experiment mutations, and quiet unchanged/non-actionable behavior. This proves saved configuration, not a successful scheduled run or future notification delivery.
