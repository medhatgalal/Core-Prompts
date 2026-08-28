# Capability Evaluation

Core-Prompts separates candidate production from behavioral promotion.

## Ownership

- UAC owns deterministic intake, overlap analysis, structural readiness, clarity diagnostics, candidate generation, and impact planning.
- `instruction-editor` owns auditable editorial candidates and preservation maps.
- Auto-Research owns behavioral experiments and promotion decisions.
- `capability-eval` enforces repo-owned contracts, profiles, budgets, evidence binding, and fail-closed statuses.
- Inspect AI, Inspect SWE, and direct host adapters are planned interchangeable execution mechanisms, not truth oracles. Inspect is not bundled or active in this release.

## What works now

- compile draft Goal Contracts and capability topologies for all skills
- detect known contract contradictions and generated drift
- run Google-derived clarity lint, structural controls, fixtures, and runtime availability probes with zero model calls
- validate public Code Review cases for correctness, low noise, resource lifecycle, initialization-time state, operational readiness, and API-contract compatibility, including matched positive and negative controls
- calculate the minimum allowed evaluation profile and hard token cap
- execute explicit baseline-versus-candidate run plans through registered Codex and Kiro adapters when an operator authorizes model calls
- seed a separate protected evaluator project from `tooling/protected-evaluator/`
- validate signed, hash-bound promotion evidence and reject missing, stale, self-authorized, or incomplete evidence
- finalize a candidate that is already canonical without rewriting its reviewed contract or topology

## What is still gated

- each live baseline-versus-candidate execution, which requires explicit operator authorization and protected provider credentials
- protected runner identities, purpose-separated signing keys, an external sealed bundle, and independently qualified semantic judges
- causal proof that Google-style rewriting improves people or agents
- behavioral promotion of any changed skill until its own current evidence passes every hard gate

The repository contains the evaluator and public orchestration template, not real credentials, private keys, sealed cases, labels, qualified judge implementations, or executed model results. Missing or non-conforming protected inputs return `inconclusive`; they never become an inferred pass.

The bundled Codex adapter is fail-closed and promotion-ineligible. It never passes `OPENAI_API_KEY` to candidate-influenced execution. Enabling authenticated Codex promotion runs requires a separately approved, bounded credential broker or an equivalent OS-enforced boundary; ordinary environment-variable authentication is rejected. `PromotionVerdict.v1` remains readable as legacy evidence, but only `PromotionVerdict.v2` can authorize promotion.

## Evidence flow

```mermaid
flowchart LR
  S["Canonical SSOT"] --> G["GoalContract.v1"]
  S --> T["CapabilityTopology.v1"]
  C["Candidate producer"] --> D["UACDelta.v1"]
  G --> I["EvalImpactPlan.v1"]
  T --> I
  D --> I
  I --> R["Paired evaluator run"]
  H["Independent sealed bundle"] --> R
  R --> V["PromotionVerdict.v2"]
  V --> A["Reviewed UAC apply"]
```

`structural_ready` is not `promote`. No score can compensate for a failed safety, authority, routing, state, output, resource, handoff, or critical-mutation gate.

## From `behavioral_pending` to `promote`

`behavioral_pending` means a structurally accepted candidate has not yet supplied independent evidence that authorizes a new behavioral baseline. The completed status is `promote`, not `done`.

| Status | Meaning | May advance the behavioral baseline |
| --- | --- | --- |
| `behavioral_pending` | structural apply completed without an accepted promotion verdict | no |
| `inconclusive` | the experiment could not establish a valid decision, including missing credentials, adapter drift, budget exhaustion, or incomplete evidence | no |
| `hold` | valid evidence did not meet the preregistered promotion bar | no |
| `promote` | a current, independently signed verdict passed every hard gate and UAC accepted its bindings | yes |

If the candidate is already present in canonical SSOT, finalize it with the signed public evidence bundle:

```bash
bin/uac apply <candidate-source> \
  --promotion-verdict <public-bundle>/promotion-verdict.json \
  --promotion-trust-root <public-bundle>/evaluator-trust-store.json \
  --approved-trust-policy-sha256 <64-hex-policy-sha256> \
  --approved-trust-policy-revision <40-hex-policy-commit> \
  --finalize-existing-candidate \
  --yes
```

Omit `--finalize-existing-candidate` when canonical SSOT still equals the evaluated baseline and the apply will introduce the candidate. UAC verifies the exact baseline and candidate commits, SSOT hashes, ancestry, current `HEAD`, contract and topology hashes, trust store, policy, verdict, and supporting evidence before writing. A refusal leaves the behavioral baseline unchanged.

## Protected evaluator trust model

The protected evaluator is a separate execution project, not a privileged mode inside UAC:

- candidate submission is signed separately from evaluator evidence
- model jobs receive prompt-only inputs and bounded provider credentials, never sealed labels or signing keys
- scoring, judging, verdict construction, and signing run tools-off in separate trust domains
- primary and reproduction runs use distinct protected runner identities and preregistered seeds
- one Ed25519 key is used for each of six purposes: adapter conformance, execution receipts, global token ledger, judge qualification, sealed bundle, and promotion verdict
- one signed cumulative token ledger covers conformance, primary, reproduction, and adjudication under the profile's global cap
- only aggregate, redacted, hash-bound public evidence returns to Core-Prompts

The public orchestration template and setup contract live in [`../tooling/protected-evaluator/README.md`](../tooling/protected-evaluator/README.md).

## Two-stage trust prerequisite

Promotion requires the evaluator trust policy to predate the candidate's authority boundary:

1. Land the evaluator foundation, reviewed public trust store, and `ApprovedTrustPolicy.v1` on protected main. This policy revision must be an ancestor of the later evaluation baseline.
2. Create and evaluate the candidate from that baseline. The signed verdict must bind the same policy revision and hash supplied explicitly to UAC.

A candidate revision cannot introduce the policy that authorizes its own evaluator keys. If the policy is missing, expired, changed, not on baseline ancestry, or does not exactly match the selected trust store, UAC returns `stale_evidence` and does not promote.

## Selective profiles

| Profile | Model calls | Hard raw-token cap | Intended use |
| --- | ---: | ---: | --- |
| `static` | no | 0 | contracts, topology, schemas, clarity lint, deterministic controls |
| `native` | no | 0 | CLI availability, version, validation, and discovery probes |
| `routing-canary` | yes | 0.3M | name, description, invocation-hint changes |
| `canary` | yes | 1.25M | bounded module or shared-engine changes |
| `promotion` | yes | 5M | new skills and behavior, safety, state, authority, or merge proof |
| `cross-host` | yes | 12M | required deployment-envelope evidence |
| `sweep` | yes | 30M | explicitly approved model, effort, and host research |

Reaching a cap returns `inconclusive`. The runner cannot silently reduce trials or omit cells.

## Current rollout state

Structural enforcement remains separate from behavioral promotion. Draft extraction is not human approval: every normative clause must be mapped to a case or reviewed waiver before topology closure.

Live execution is available only through explicit run plans and protected operator setup. It is disabled by default. The checked-in project intentionally cannot run a promotion by itself because it contains no provider credentials, private signing material, sealed labels, or qualified judge implementation.

The first paid pilot is deliberately narrower than the available public cases. It asks four questions:

1. Does SuperCharge preserve modules, stacking, terminal controls, and state?
2. Does Code Review find seeded correctness and lifecycle defects with good evidence while remaining quiet on matched safe controls?
3. Can routing distinguish product completeness (`feature-status`), repository activity (`eng-report`), and structural code health (`codebase-health-audit`)?
4. Does UAC Import preserve agent-useful metadata and its HTML safety boundary without claiming behavioral proof?

Architecture, Instruction Editor, Pulse, and Weekly Intel cases remain available but are deferred from the first paid run. Static pilot-fixture validation runs in ordinary CI at zero tokens. A model-mediated run proceeds only after its adapters conform, its judge qualifies on a separate preregistered gold set, and every protected input is current.

## Google-style experiment

`instruction_clarity.v1` is a source-linked local policy that summarizes selected Google developer documentation guidance. It does not weaken UAC's HTML ingestion boundary and does not copy the full style guide.

The causal experiment has four blinded arms: baseline, UAC without clarity, clarity only, and UAC plus clarity. Human clarity and behavioral fitness remain separate scorecards. Default rewriting stays off until the sealed, powered ablation proves human gain, behavioral non-inferiority, routing preservation, critical-mutation coverage, and holdout survival.

## Evidence staleness

A verdict binds baseline, candidate, Goal Contract, topology, dataset, scorer, evaluator, adapter, CLI, model, effort, tool-policy, and runtime hashes or versions. Any bound change makes the verdict `stale_evidence`; historical records remain intact but cannot authorize a new apply.

## Historical evaluation archives

Preserve released evaluation evidence under `evals/history/<slug>/<candidate>/`. Its manifest binds every archived file by byte hash and declares `archive_only: true`, `auto_discovery: false`, and `promotion_eligible: false`.

When canonical SSOT changes, rebuild the active Goal Contract, topology, and review overlay for the new body. An archived verdict remains historical evidence and cannot authorize the current body. Keep structural maintenance fixtures outside the promotion corpus; they make zero behavioral-promotion claim.
