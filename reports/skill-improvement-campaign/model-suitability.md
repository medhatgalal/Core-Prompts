# Model and runtime suitability for the four-skill campaign

Research status: **documented shortlist and verified native metadata; no comparative model experiment dispatched**. Astra/high is a configured author setting, not evidence that it best serves these skills. No model wins this study because downstream trials have not run.

## Scope, identity, clock, and evidence boundaries

- Owner: coordinator subagent `/root/model_suitability`; sole write target is this report. Other owners' work is preserved.
- Verified cwd: `/Users/medhat.galal/.codex/worktrees/6c79/Core-Prompts`; branch `AI/campaign-broad-scope`; HEAD `0d1b07e157763f1f78223894c339c4dc295dbbb5`. Initial dirty state was the coordinator's `reports/skill-improvement-campaign/owner-brief.md`.
- Research clock anchor: **2026-09-10 00:08:43 UTC** (September 9, 20:08:43 EDT). Target/deadline: **00:43:43 UTC**, 35 minutes including inspection, source retrieval, analysis, report verification and handoff. At the limit, stop new research and report remaining uncertainty. This is the shared research phase, not a reset of earlier campaign accounting.
- Read repository AGENTS, agent-behavior steering, capability-evaluation documentation, evaluator implementation and native adapter registry. Used OpenAI Docs and its model-selection reference. Read the three shorter canonical skills and Architecture's mode, workflow and deliverable structure; this report does not replace each owner's full content review.
- Provider pages were actually fetched/opened on September 10 UTC; facts below distinguish provider documentation, native metadata, configured settings, and unverified execution.
- No paid API, experimental model invocation, authentication change, reset, credential inspection, privileged harness, cloud workload, or shared config/evaluator edit occurred. Research itself uses the existing assistant and tools; its token consumption is **unavailable**, not zero. Experimental producer/judge calls are **zero**.

## What this runtime establishes

| Layer | Current evidence | What it does not establish |
| --- | --- | --- |
| Native installed commands | `codex --version`: `codex-cli 0.153.4`; `kiro-cli --version`: `kiro-cli 2.21.2` | Account invocation success, suitability, isolation or conformance |
| Local model catalog | `~/.codex/models_cache.json`, `fetched_at=2026-09-10T00:09:42.656334Z`, `client_version=0.153.4`; six requested models listed | A successful inference request, immutable backend snapshot or guaranteed account entitlement |
| Native CLI interface | `codex exec --help` exposes `--model`, `--json`, `--ephemeral`, `--ignore-user-config`, `--strict-config`, `--sandbox`, `--output-schema` | Whether all effective tools, hooks, browser state, resources, credentials and inherited context are confined |
| Checked-in adapters | Codex conformance pin `0.150.1`; Kiro pin `2.20.0`; both authenticated adapters explicitly unavailable and promotion-ineligible | Neither current native version matches the pin; updating a version string would not prove conformance |
| Task's native tool metadata | Astra, Sol, Terra, Luna, 5.5 and Spark exposed as selectable model identifiers with supported effort lists | No tool call was made to test those model selections |

The Codex PATH entry is a Volta native shim. Its resolved package entrypoint was inspected before invocation; it forwards arguments to the vendor executable. Kiro is a symlink to its application-native binary. Codex version/help returned success but warned that PATH alias creation was denied by the sandbox. Thus even help had an attempted incidental write; no escalation or repair followed. No blanket `capability-eval probe` ran because it would also execute Gemini/Claude wrappers that were outside the verified native probe set.

### Native catalog details

| Model | Catalog default effort | Catalog effort choices | Catalog context | Inputs / API metadata |
| --- | --- | --- | ---: | --- |
| `gpt-6-astra` | medium | low, medium, high, xhigh, max, ultra | 272,000 | text/image; API true |
| `gpt-5.6-sol` | low | low, medium, high, xhigh, max, ultra | 272,000 | text/image; API true |
| `gpt-5.6-terra` | medium | low, medium, high, xhigh, max, ultra | 272,000 | text/image; API true |
| `gpt-5.6-luna` | medium | low, medium, high, xhigh, max | 272,000 | text/image; API true |
| `gpt-5.5` | medium | low, medium, high, xhigh | 272,000 | text/image; API true |
| `gpt-5.3-codex-spark` | high | low, medium, high, xhigh | 128,000 | text only; API false |

All six catalog entries advertise 95% effective-context percentage, unified execution shell, and a 10,000-token truncation policy. The first five advertise a priority/Fast tier; Spark lists none. Descriptions such as "2x speed" are catalog claims, not measured latency. The context figures are catalog defaults, not this task's observed effective window.

**Unresolved context discrepancy:** provider API capacity is 1,050,000 tokens for Astra/Sol/Terra/Luna/5.5; the observed native catalog default is 272,000. Local configuration details are omitted from this public report. Do not resolve this by choosing the largest figure. Record the effective producer window, remaining input headroom, compaction policy and actual compaction events at admission. Use bounded fixtures well below the lowest relevant envelope initially. [API comparison](https://developers.openai.com/api/docs/models/compare), [GPT-5.5](https://developers.openai.com/api/docs/models/gpt-5.5).

Official Codex documentation distinguishes **Ultra as automatic subagent work**, while Max is more reasoning on one task. Ultra would change topology and call accounting, so exclude it from a model-only experiment. An effort label is not an equal-compute guarantee across models; freeze the label for an initial comparison and report the claim as "model at this effort." [Codex models](https://developers.openai.com/codex/models).

## Provider facts useful for selection

| Model | Documented role / limit relevant here | Standard API input / cached input / output USD per million tokens |
| --- | --- | --- |
| Astra | Complex multistep reasoning, coding, research and document work; API effort low through max | 10 / 1 / 50 |
| Sol | Complex professional work; `gpt-5.6` aliases Sol; API none through max | 4 / 0.40 / 20 |
| Terra | Intelligence/cost balance; API none through max | 2 / 0.20 / 12 |
| Luna | Cost-sensitive, high-volume work; API none through max | 0.20 / 0.02 / 1.20 |
| 5.5 | Previous-generation comparison anchor; API none through xhigh | 5 / 0.50 / 30 |
| Spark | Text-only coding research preview; separate limits; no general API access claimed | No applicable API price established |

Sources: [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra), [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna), [5.5](https://developers.openai.com/api/docs/models/gpt-5.5), [Spark availability](https://developers.openai.com/codex/models). These are vendor descriptions and API reference prices, not measurements, purchase authorization, or the cost of subscription-native calls.

All five general models document text/image input, text output, function calling, structured outputs and relevant Responses tools including search, shell, apply-patch, skills and MCP. This removes an obvious API feature disqualifier; it does not demonstrate equal tool-selection reliability or expose those tools automatically in a particular host. Their API output limit is 128,000 tokens. Models and routing aliases may change; capture the returned backend version where exposed and otherwise disclose that only the selectable identifier was bound. The fetched 5.5 page publishes snapshot `gpt-5.5-2026-04-23`; the newer model pages expose their bare identifiers as current snapshots. Sources are the individual API model pages above.

Long prompts over 272k receive increased API pricing; cache writes and service tiers also affect cost. Token savings, task completion and corrections therefore matter more than a per-token price ranking. Subscription usage depends on model, task, context, reasoning, retrieval, tools and caching. Local and cloud work share allowances; Spark has separate preview limits. We did not inspect this account's remaining allowance. [Astra pricing notes](https://developers.openai.com/api/docs/models/gpt-6-astra), [plan usage](https://learn.chatgpt.com/docs/pricing).

Cloud is a distinct runtime factor: the fetched Codex model table lists Sol as Codex-cloud available, Astra/Terra/Luna/5.5/Spark as unavailable there, and says the cloud default cannot currently be changed. Desktop/web model selection and Codex cloud are different surfaces. Do not substitute a cloud run for a matched local run. Rollout/client/sign-in differences still apply. [Codex models](https://developers.openai.com/codex/models).

## Criteria map and justified shortlist

These are task-based hypotheses. The owner should refine case contents from full-capability research before locking a run.

| Skill and major jobs | Model/runtime properties that matter | Meaningful outcome evidence | Initial model shortlist and flip condition |
| --- | --- | --- | --- |
| Docs: information architecture, command/link drift, targeted authorized rewrite, release/navigation review | Precise cross-file retrieval; distinguish implementation evidence from prose; preserve audience and canonical home; resist attractive but unnecessary rewrites | Correct actionable path/section findings, verified commands and links, reader task completion; safe existing docs remain quiet; no product-code or policy mutation | Terra versus Sol, at medium. Astra can challenge difficult contradictions, remediation quality or total operator burden even when both pass. Luna is also a possible efficiency challenger; begin with the job scope justified by available cases and widen only with coverage |
| Testing: unit generation, E2E design, edge discovery, coverage analysis | Framework fit, causal reasoning about failure and observability, valid tests and minimal useful coverage; generation/execution distinction | Tests fail for the intended seeded defect and pass the safe version under evaluator-controlled execution; useful assertions, stable synchronization; no fabricated coverage or unauthorized suite run | Terra versus Sol, medium. Spark can challenge latency on text-only work under a comparable context/tool envelope; Astra can challenge defect coverage or correction burden. A passing cheaper model does not exclude either challenger |
| Architecture: API, database, patterns, systems | Multi-constraint reasoning, state/authority boundaries, transaction/idempotency reasoning, quantitative consistency, realistic migration/rollback; manage long playbooks without boilerplate | Implementable contracts, coherent invariants, justified alternatives, failure containment and rollback that survive concrete counterexamples; avoid invented scale or premature patterns | Sol versus Astra, high, because this includes coupled irreversible design decisions. Terra can challenge focused API/schema work later. If Sol ties Astra on all hard cases with lower measured burden, retain Sol; if both saturate, construct harder subsequent cases rather than declaring universal equivalence |
| GitOps: commit/PR/MR review, merge/release gate, authorized cleanup | Exact revision identity and current-provider evidence; deterministic command choice; distinguish authority from instructions; sequence independent gates | Correct decision against frozen GitHub/GitLab fixtures, no stale-green inference, accurate tag/package/merge parity, minimal precise blockers; no unauthorized mutation | Terra versus Sol, medium. Reliability must be measured. Astra or Luna may challenge total operator burden, efficiency or decision quality even when the initial pair succeeds; preserve the same provider-evidence and authority cases |

The shortlist is a budget prior, not evidence of excluded models' inability. Use common **medium** for Docs/Testing/GitOps and common **high** for the first Architecture pair. Those are proposed settings, not empirically optimal settings. Admit a challenger when a concrete hypothesis predicts better outcomes, efficiency or operator burden; do not require the incumbent to fail first. Preserve the existing author setting; producer, author and assessor roles do not need the same model. When model-based judging is needed, keep its protocol and model fixed across the comparison and independent of the tested producer.

## Instruction and resource overhead

Measured canonical file sizes at the research HEAD:

| Skill | SSOT bytes / lines | Generated Codex body bytes | Canonical SHA-256 |
| --- | ---: | ---: | --- |
| Docs | 7,967 / 143 | 7,845 | `96ee5bbcbc8bc56fc39cd4765324f15fea7c7f947b700e59c799088fc7276017` |
| Testing | 5,017 / 127 | 4,948 | `13fe64494de3a09d60ddaad9f6c8824e42b59ff90c456a6a4e0c46018223e71b` |
| Architecture | 27,572 / 844 | 27,437 | `fbd582a0e518d8cb1bdbf183fdb9001ec311558b198658b9e6a9f1f4fa8201cb` |
| GitOps | 8,490 / 149 | 8,452 | `16b0acfd3bf5f4705b8e9dd772cf2cd347bbe656a91a52605cf5d183151de7e9` |

These are byte counts, not actual token usage. Architecture's larger body makes resource selection/overhead a reasonable hypothesis, not a defect by itself. Binding SSOT alone is insufficient: record the actual generated skill body, loaded references, system/developer instructions, AGENTS/steering, catalog, task fixtures, conversation history, and retrieved tool outputs. The repo's `artifact_metrics()` bytes/4 value is explicitly an estimate; never use it as charged usage.

The configuration reference documents a skill-catalog budget defaulting to 2% of model context, a cap of 10,000 for explicit settings, a project-document byte limit, and tool-output truncation controls. Full loaded skill resources and tools add separate context. It also documents that shell-network restrictions do not automatically govern apps/MCP/web tools. Native flags and a fresh conversation do not prove a bare arm lacks the incumbent skill or that external boundaries are enforced. [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

## Smallest supported development route and exact missing admission

`docs/CAPABILITY-EVALUATION.md` explicitly permits a short development receipt binding treatment/control requests, selected resources, public task data, starting state and runtime. It does **not** require a new general evaluator or a signed PromotionVerdict for every useful development comparison. Use the existing public fixtures, resource manifests/hashes, deterministic verifiers, scorecards and receipt concepts where they fit; ordinary reviewed candidate preparation can continue now.

The executable protected path is more constrained: `bin/capability-eval compare --allow-model-calls --run-plan ...` reaches `run_model_comparison()` and requires current plan/resource/runtime/credential/conformance bindings. `execute_adapter()` rejects any adapter carrying `unavailable_reason` before launching it. Both Codex and Kiro have that reason; the code also requires them to remain unavailable. Their current native version drift is an additional blocker. The fake adapter cannot prove model behavior, and the experimental Claude entry is not an admitted substitute. References: `src/core_prompts_eval/cli.py`, `runner.py`, `adapters.py`, `run_plan.py`, and `evals/adapters/registry.json`.

**Proposed first route:** an explicitly admitted, existing native local producer with public synthetic task inputs, no external provider mutations, and a narrow per-skill development receipt. Collect native JSONL/usage and artifact hashes through existing host capabilities; reuse task-specific verification/scoring without changing the protected promotion runner. This route is a proposal, not a claim that today's broad desktop tool surface is sufficiently isolated.

Before dispatch, the coordinator must establish:

1. The exact native entrypoint/model/effort/service tier and permitted public input/output paths, with evidence for material tool, file, hook, browser/MCP and skill-loading boundaries. No copying auth into candidate-accessible homes or opening broader cloud access.
2. An observation route that captures actual model ID/version if available, loaded treatment/resources, start state, complete output/artifacts, completion/failure, raw input/output/reasoning/cache usage where provided, and successful cancellation/timeout. An unavailable field stays unavailable; it does not become zero.
3. An enforceable dispatch-count and wall-time policy, a documented token/usage observation limit, and independent assessment that candidates cannot read or influence. Native metadata has not established an exact per-call raw-token ceiling or visibility of all billed subcalls. If the operator requires a hard raw-token cap, that missing control blocks admission under that requirement. An explicitly accepted native development allowance with disclosed unknown billing does not itself require the full promotion infrastructure; it simply cannot support a claim that an unobserved raw-token cap was enforced.
4. A locked per-skill matrix and the specific bounded dispatch tranche authorized by the operator. Current research permission does not supply this admission.

If existing native tools cannot establish these boundaries, report the specific missing observation/control. Propose the smallest scoped adapter/receipt change for coordinator review; do not silently repair the protected registry or build a privileged general harness. Formal behavioral promotion, canonical shipping, installed behavior and cloud acceptance remain separate decisions.

## Factor-separated experiment plan

**A. Provisional model screen:** freeze full incumbent skill plus exact selected resources, public case, starting state, host/tools, effort, speed tier and output contract. Change only the preregistered model identifier and counterbalance order. The case count comes from the owner's claimed jobs and discriminating cases. A four-case, two-model, one-repetition screen would require eight producer attempts; this is a sizing example, not a prescribed matrix. It estimates model suitability for the incumbent on those cases only. It cannot establish the best model for a redesigned candidate or whole-skill reliability.

**B. Skill effect at a fixed model:** freeze the provisionally selected model/settings and runtime. Compare (1) public task without the skill, (2) full incumbent, (3) complete candidate and selected resources. Bare still receives the same necessary common task instructions and safety boundary; verify it cannot auto-load the incumbent. Cover the owner's major jobs and preservation, safe, routing, missing-evidence and authority controls with the smallest sufficient case set. Eight cases × three arms × one repetition would require 24 attempts, but owners must justify both coverage and repetition before locking their actual matrix. Counterbalance arm order. Never compare a bare small-model run against an Astra candidate and attribute the difference to the skill.

**C. Confirmation and model interaction:** confirm a promising candidate on new independently authored cases spanning claimed improvements and vulnerable preserved behavior, with repetitions chosen for the observed noise. Avoid treating authored demonstration answers as held-out evidence. Four new cases × incumbent/candidate × two repetitions would require 16 attempts; again this is a sizing example. The default conclusion remains limited to the tested model/settings and covered jobs.

When a candidate substantially changes instruction load, resource selection, tool workflow or required reasoning, or when a model-independent recommendation is intended, add a bounded finalist crossover: test the incumbent and candidate on both finalist models using the same selected interaction-sensitive cases and controls. Two cases × two skill versions × two models × one repetition would require eight attempts. If reused cells are genuinely identical and preregistered as reusable, count only the added attempts; otherwise use fresh matched cells. A ranking reversal or different skill effect by model becomes a model-specific result, not a universal winner. This confirmation is conditional work that must enter the budget before dispatch; it is not an automatic full-factorial sweep.

**Acceptance belongs to the domain contracts.** There is no shared ordinal score or generic gain rule that can authorize adoption. The previous rule could accept two one-point gains alongside six one-point losses; it is withdrawn. Each owner must freeze primary outcome(s), the useful-result floor, preservation gates/non-inferiority margins, material gain, allowed burden tradeoffs and independent confirmation criteria before comparison. For example, Testing needs meaningful defect/safe-control behavior and framework fit; GitOps needs correct gate decisions against current evidence; Docs needs accurate actionable changes and reader utility; Architecture needs valid implementable contracts and preserved invariants. These examples do not supply numeric acceptance thresholds: those are **unresolved until the corresponding owner contract is reviewed**.

A demonstrated unauthorized action, fabricated execution/provider state, invalid critical contract or corrupted artifact is a domain failure and remains recorded. Missing material runtime evidence instead invalidates the affected comparison; it is not a poor model-quality score. Preserve any independently established defect even if the overall comparison is inconclusive. No gain in presentation can compensate for a failed preservation gate, and an improvement on one job does not silently offset losses on another. Publish individual paired outcomes and judge disagreements with the limited scope of the evidence. Retain the current development incumbent on ties, invalid comparisons or unresolved acceptance criteria.

For model selection, compare total measured burden only among candidates satisfying the owner's useful floor and preservation gates. Operator repairs, elapsed time, observed tokens and account usage may point to different choices; preregister the accepted tradeoff rather than aggregating incomparable measures after seeing results. Conflicting independent judgments material to the decision require adjudication or an uncertain conclusion.

## Bounded exploration beyond the first candidate

One candidate comparison is one round, not the campaign. Each owner should prioritize a small set of distinct hypotheses from research, such as better mode selection, evidence acquisition or resource organization. A proposed initial exploration bound is **up to three distinct hypotheses per skill**, with at most one evidence-led revision of a rejected hypothesis; the coordinator must ratify or replace that limit alongside the actual phase budget. This is a ceiling, not a quota, and creates no automatic calls.

For each round, retain the immutable original baseline, current development incumbent, candidate/resources, hypothesis, expected improvement, case coverage and previous results. Keep a candidate only when the reviewed domain contract and confirmation pass; reject it on demonstrated unacceptable regression; retain the incumbent on ties or inconclusive results. A kept candidate may become the next development comparator only after its identity and acceptance are recorded. This does not advance the formal behavioral baseline, authorize canonical shipping, or rewrite earlier results.

Stop when the owner-defined target is met, the admitted call/time/usage budget is exhausted, the hypothesis limit is reached, or **two consecutive distinct hypotheses yield no accepted improvement**. An inconclusive boundary or collection failure pauses dependent trials for diagnosis; it does not count as evidence of a performance plateau. Do not repeat the full three-arm/model matrix for every revision: select the changed mechanism's discriminating cases plus preservation controls, then confirm any broader claimed gain with sufficient coverage. A new distinct hypothesis or changed criterion needs a separately bound prospective round; prior failed evidence stays intact.

## Prospective accounting and smallest useful preflight

The earlier 64k/128k per-dispatch values, 512k first tranche and 18.944M/256-dispatch total had no observed sizing or enforcement basis. They are withdrawn as proposed reservations. The large total described one illustrative candidate round across four skills, not full campaign accounting. No fixed aggregate experimental budget is established by this report.

**First useful preflight:** choose one skill, one representative public fixture, and one success/failure pair through the actual native observation → collection → normalization → verification → assessment → receipt path. Size the input from that fixture and its actual selected instructions/resources. The failure must be observable at the seam being tested, with proof it occurred; a fabricated invalid final artifact can test scoring but cannot by itself establish producer fault handling. A deterministic check and an independent assessment are sufficient when they establish the expected outcomes. There is no automatic requirement for two model judges, a second model, or duplicate preflight for all skills. Add model-specific preflight only when a changed runtime/model interface could alter collection, tools, usage, failure or cancellation behavior.

If both observations need native model production, the basic pair is **two producer dispatches**. A deterministic observation may require none; declare the actual path and what it proves. Any required model-mediated assessment, cancellation canary, retry or extra observation adds explicit calls before admission. Preparation and research consumption remain recorded separately. This minimal preflight proves the chosen observation path at the tested boundary, not the skill's superiority or general runtime isolation.

Before admitting even that pair, assemble a concrete sizing receipt:

1. Hash the exact fixture, selected skill/resources and common task instructions. Record known byte counts, available tokenizer-based input counts and the model's effective context limit; keep token estimates distinct from observed native usage. Inventory host-added instructions/catalog/tool schemas where observable. Missing host overhead is an uncertainty to disclose, not a reason to invent a 64k cap.
2. Reuse relevant prior native usage/timing metadata only when the same entrypoint and envelope make it comparable. Otherwise label the first pair a measurement preflight and set the smallest authorized count and cancellable wall deadline suitable for the fixture. Observe its native usage before sizing a later batch.
3. Declare supported output/step limits and what they actually limit. A prompt asking for short output is not a provider-enforced token limit. Record unknown billing/subcalls explicitly. If a hard raw-token cap is required but unsupported, do not claim compliance or dispatch under that requirement; if a bounded native allowance is explicitly accepted despite those unknowns, the development result can remain useful without invoking the protected promotion system.
4. Reserve separate wall time for fixture/setup checks, each producer observation, collection and verification, independent assessment, cancellation, final receipt and coordination/waiting. Write the actual UTC start and deadline before dispatch and stop new work early enough to use the cancellation/closeout reserve. No elapsed-time values in the earlier sizing example are measurements.

The concrete fixture, effective request overhead, native limit/cancellation behavior and domain assessment path have not yet been selected and verified together. Therefore **the first tranche's token estimate and wall deadline remain unresolved**, and no experimental dispatch is admitted here. The next reviewable artifact should contain this one-pair sizing receipt, not a generalized harness or an automatically multiplied campaign matrix.

### Full phase accounting template

| Phase | What must enter the prospective record | Accounting basis |
| --- | --- | --- |
| Research and current candidate preparation | Existing owner/controller work, source retrieval, authoring and review already performed | Actual usage where available; otherwise explicitly unknown, never reset to zero |
| Fixture/protocol preparation | Cases, instructions/resources, verifiers, expected observations, case inventory and independent assessment work | Actual static time and any separately declared author/assessor calls |
| Success/failure preflight | Smallest observations exercising the actual path; any materially different runtime canary | Actual planned producer/assessor/cancellation-canary counts, fixture-sized input/output estimates and supported limits |
| Model screen | Fixed skill protocol, models, cases and repetitions | Models × cases × repetitions, plus individually justified extra observations |
| Skill round | Bare/incumbent/candidate, cases, repetitions and coverage claim | Arms × cases × repetitions; author/refinement calls counted separately |
| Candidate confirmation | New independent cases, compared arms and repeats | Confirmation cases × arms × repetitions |
| Conditional model crossover | Only the interaction claim requiring it | Selected cases × skill versions × models × repetitions, minus only preregistered identical reusable cells |
| Assessment and adjudication | Deterministic work, independent human/agent assessment and material disagreement resolution | Count every actually needed model call; no fixed judge quota |
| Failures and retries | Partial/charged attempts, cancellation, replacement decisions and unused reservations | No retry outside the admitted reserve; never erase a confirmed failure |
| Closeout | Artifact/receipt verification, final status, remaining reservations, waiting and coordination | Separately reserved time and observed or unknown controller usage |

For a locked tranche, total dispatch count is the sum of its actual author, producer, assessor, retry and canary calls. Estimated input/output consumption is summed from the fixture-specific per-call estimates; actual usage is summed from the available native records, including repeated context and relevant tool/continuation effects. The campaign ledger then accumulates completed, in-flight and explicitly reserved future tranches across owners. Do not multiply one round's matrix by a hypothetical candidate count and call that an admitted campaign budget.

For every attempted observation, retain phase/arm/case/repetition, attempt ID, start/end and wall elapsed, waiting, selected/returned model, effective settings, request/resource/output hashes, input/output/reasoning/cache usage where exposed, estimate provenance, reservations/releases where meaningful, retry/partial/error/cancel state, tool calls, operator corrections and any available account-usage delta. Avoid double-counting cached input or reasoning when already included in parent token fields. Do not convert native subscription use into an invented API invoice. Hidden or unavailable fields restrict token/cost conclusions; they do not automatically negate an otherwise evidenced task-quality comparison.

At a hard phase deadline, stop new dispatches, cancel only owned active work with the admitted mechanism, preserve partial/charged attempts and established defects, and complete the bounded closeout. If cancellation cannot be confirmed, report it as unresolved rather than released capacity or unused reservation. Missing material execution boundaries or outcome evidence make dependent comparisons inconclusive; missing billing metadata specifically limits accounting/cost claims. Neither condition establishes a skill loss or permits an inferred pass.

## Verification and remaining work

Observed checks: branch/HEAD/dirty-state identity; read-only wrapper inspection; Codex version and exec help; Kiro version; timestamped catalog metadata; canonical body hashes/bytes; current evaluator refusal path; actual official model, configuration and pricing pages. No installation or configuration was changed to make an assumed route work.

Initial report checkpoint: **2026-09-10 00:16:13 UTC**, 7 minutes 30 seconds after the recorded anchor. Its arithmetic and all four canonical hashes were checked directly; the numerical reservations were subsequently withdrawn for lack of sizing evidence. The coordinator advanced HEAD to `eac8bd5f3602c4c5df5e0e0d2e286809adda2f04` during research; skill measurements remain bound to the original base and their hashes matched at this checkpoint. This new report is ignored by the repository's `reports/` rule and requires explicit coordinator staging if it is to be committed; no shared index changes were made by this owner.

Independent review correction: `/root/model_plan_challenge`, relayed by the coordinator, identified six plan defects. This revision removes the permissive shared ordinal acceptance rule; delegates acceptance to reviewed domain outcomes and preservation gates; narrows model-screen conclusions and adds conditional interaction confirmation; withdraws unsupported numerical reservations in favor of fixture-sized accounting; distinguishes one round from bounded multi-hypothesis exploration; and removes automatic duplicate model preflights/judge calls and unsupported shortlist exclusions. Missing runtime evidence and missing billing metadata now have distinct consequences. Verified source/native findings are preserved. No experiment, shared evaluator/config edit or additional model research was introduced by these corrections.

Revision checkpoint: **2026-09-10 00:23:31 UTC**, 14 minutes 48 seconds after the original research anchor, within its unchanged 35-minute target. This revision is ready for the same independent reviewer's recheck; it does not claim that recheck has passed.

Remaining: owners must finalize and review domain acceptance contracts, representative cases and candidate resources; coordinator must obtain the independent plan recheck; native admission needs a fixture-sized success/failure receipt with verified material boundaries, count/time controls, available usage observations and cancellation. No downstream performance, reliability, latency or cost-per-task claim is established. The current conclusion is a **conditional shortlist and a concrete path to a small admitted comparison**.


Publication note: local configuration/security details and private context-provenance references have been omitted. Public provider facts, catalog metadata, source measurements, research criteria and the independently corrected plan remain; no effective runtime admission is claimed.
