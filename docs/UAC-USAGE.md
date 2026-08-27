# UAC Usage Guide

Use UAC, the capability intake and uplift workflow, when you want to bring new prompt-like source into canonical Core-Prompts state.

Do not start with UAC if your goal is just to use already installed Core-Prompts skills or agents. UAC is the second layer in the product model, after installed capabilities and before broader repo tooling.

Preferred shell entrypoints:

```bash
bin/uac --help
bin/capability-fabric --help
```

Direct Python entrypoint still works:

```bash
python3 scripts/uac-import.py --help
```

## What UAC Is For

Use UAC when you need to:

- inspect how an external prompt or prompt family would land in this repo
- decide whether the source should become a skill, an agent, or manual review
- benchmark a candidate before it mutates canonical repo state
- write canonical SSOT, descriptor, and baseline state after a successful review

## When Not To Use UAC

Do not start with UAC when you are:

- using installed Core-Prompts skills or agents in daily work
- browsing what already ships in the repo output
- rebuilding or validating existing canonical state without new capability intake
- copying generated surfaces into a target home after a build

For those cases, use [Getting started](GETTING-STARTED.md), [Examples](EXAMPLES.md), or [CLI reference](CLI-REFERENCE.md).

## Modes

| Mode | Use it when you want to... | Writes repo state |
| --- | --- | --- |
| `import` | inspect one or more sources without mutating the repo | no |
| `audit` | inspect current SSOT entries and generated surfaces | no |
| `explain` | print the capability model and deployment matrix | no |
| `plan` | see the proposed landing shape before writing files | no |
| `judge` | run the quality loop and get a ship or block decision | no |
| `apply` | write canonical repo state, then rebuild and validate | yes |

## The Typical Flow

```bash
bin/uac import /absolute/path/to/prompt.md
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
bin/uac apply /absolute/path/to/family-folder --yes
```

How to think about that sequence:

- `import` is the low-risk first look
- `plan` is the proposed landing shape
- `judge` is the quality and ship decision
- `apply` is the intentional repo mutation step

If `judge` finds the candidate is structurally close to ready but still needs bounded behavioral proof, keep the landing decision open and route that proof to `auto-research` before `apply`.

## Worked Examples

### Example: Plan A Landing Before You Touch Repo State

Command:

```bash
bin/uac plan /absolute/path/to/prompt-family
```

What you are asking UAC to do:

- inspect the candidate source
- cluster it into a coherent capability family
- decide the likely capability shape
- show how it would land into canonical repo state

Typical response shape:

```text
Source summary:
- 6 prompt files detected
- strongest theme: architecture review and migration safety

Proposed landing:
- slug: architecture
- likely capability type: both
- canonical targets:
  - ssot/architecture.md
  - .meta/capabilities/architecture.json
  - sources/ssot-baselines/architecture/baseline.md

Open concerns:
- one source file is mostly release-process guidance and may not belong in the same family
- benchmark fit looks strong for architecture profile, weak for generic prompting profile

Recommended next step:
- run judge with --quality-profile architecture
```

Use `plan` when you want the landing shape, naming, and overlap analysis before any repo mutation.

### Example: Judge Before Apply

Command:

```bash
bin/uac judge /absolute/path/to/prompt-family --quality-profile architecture
```

What you are asking UAC to do:

- compare the candidate against the selected benchmark
- resolve the baseline source
- produce pass or fail evidence
- stop short of mutating canonical repo state

Typical response shape:

```text
Quality status: ship

Judge summary:
- benchmark profile: architecture
- strongest scores: migration clarity, explicit boundaries, output contract
- weak areas: invocation hints are too short and examples need more concrete asks

Artifacts:
- reports/quality-reviews/architecture/LATEST.md

Decision:
- candidate is ready for apply after expanding invocation examples
```

Use `judge` when you want the quality decision, evidence, and blockers without changing the repo.

### Example: Judge Escalates To Behavioral Proof

Command:

```bash
bin/uac judge /absolute/path/to/prompt-family --quality-profile architecture
```

Typical escalation shape:

```text
Quality status: hold

Judge summary:
- structural quality is near ship
- behavioral confidence is still weak against baseline

Next step:
- route to auto-research with:
  - baseline artifact
  - candidate artifact or variants
  - claimed job
  - bounded task set
  - pass/fail threshold
```

Use this path when structural quality alone is not enough to justify landing.

### Example: Apply A Ship-Ready Capability

Command:

```bash
bin/uac apply /absolute/path/to/prompt-family --yes
```

What `apply` does:

- writes canonical repo state under:
  - `ssot/<slug>.md`
  - `.meta/capabilities/<slug>.json`
- materializes or preserves the fidelity baseline under:
  - `sources/ssot-baselines/<slug>/baseline.md`
- may persist quality-review artifacts under:
  - `reports/quality-reviews/`
- runs:
  - `bin/capability-fabric build`
  - `bin/capability-fabric validate --strict`

Typical response shape:

```text
Applied capability:
- slug: architecture
- updated:
  - ssot/architecture.md
  - .meta/capabilities/architecture.json
  - sources/ssot-baselines/architecture/baseline.md

Post-apply:
- build: success
- validate --strict: success

Next step:
- deploy only if you want generated surfaces copied into a target root
```

Use `apply` only when you intend to change canonical repo state.

### Example: Finalize An Existing Candidate After Behavioral Proof

Use this path when a structurally ready candidate is already canonical with `behavioral_status: behavioral_pending`, and an independent protected evaluator later returns a signed `PromotionVerdict.v2` with `status: promote`. UAC may read a legacy `PromotionVerdict.v1`, but V1 cannot authorize promotion.

The trust policy must be landed first. Its protected-main revision must be an ancestor of the evaluated baseline; the candidate revision cannot authorize its own evaluator keys.

```bash
bin/uac apply /absolute/path/to/candidate-source \
  --promotion-verdict /absolute/path/to/public-bundle/promotion-verdict.json \
  --promotion-trust-root /absolute/path/to/public-bundle/evaluator-trust-store.json \
  --approved-trust-policy-sha256 <64-hex-policy-sha256> \
  --approved-trust-policy-revision <40-hex-policy-commit> \
  --finalize-existing-candidate \
  --yes
```

UAC accepts this only when:

- canonical `ssot/<slug>.md` exactly matches the verdict's candidate hash
- the verdict's baseline is an ancestor of its candidate, and the candidate is an ancestor of current `HEAD`
- current `HEAD` contains the same candidate SSOT
- the reviewed Goal Contract, topology, trust store, approved trust policy, receipts, ledger, judge qualifications, score report, and reproduction evidence all match their signed bindings
- every hard gate passed within the preregistered global token cap

On success, UAC records `behavioral_status: promote`, preserves the reviewed contract and topology, and materializes the promoted behavioral baseline. Invalid, stale, expired, incomplete, or self-authorized evidence returns a non-promote status and does not advance the baseline.

Do not use `--finalize-existing-candidate` when canonical SSOT still equals the evaluated baseline. In that case, use the same evidence arguments without the flag so apply can introduce the evaluated candidate.

The protected runner may return `inconclusive` before or during evaluation. Common causes include missing Codex or Kiro service credentials, adapter conformance failure, unavailable protected runner identity, token-cap exhaustion, incomplete usage or retry evidence, missing sealed data, or an unqualified judge. `inconclusive` is an honest stop, not a retry-shaped promotion.

## Deploy After Apply

`apply` does not deploy to CLI homes automatically. Deploy is a separate explicit step.

```bash
bin/capability-fabric deploy --cli codex --slug auto-research --target "$HOME" --allow-nonlocal-target
```

Notes:

- `--slug` is repeatable and limits deployment to specific capabilities
- deployment copies the full emitted bundle for each selected surface
- deploying `--slug auto-research` removes stale installed `autosearch` skill, agent, and resource paths for the selected CLIs
- deploy is copy-only and does not rewrite capability metadata paths
- for a narrowly approved repair or rollout, add `--surface-only`; it requires at least one `--slug` and skips the standalone updater, launcher, and local binary refresh

## Source Kinds

UAC can analyze:

- local files
- local folders
- raw public HTTPS URLs
- GitHub repo or folder URLs
- multiple `--source` values in one run
- repomix-reduced repo inputs

For a local generated skill named `SKILL.md`, UAC resolves the capability slug from frontmatter `name` before falling back to the filename. A same-slug update preserves canonical-only SSOT frontmatter and curated descriptor metadata instead of replacing them with generated-surface or generic intake defaults.

## Important Boundaries

- `structural_ready` replaces the old `ship` label and is structural evidence only.
- Google-derived clarity lint is always available, advisory, and backed by the reviewed local `instruction_clarity.v1` policy. UAC still rejects unsupported HTML ingestion.
- `--emit-impact-plan` selects the minimum safe evaluation profile; unknown impact escalates rather than guessing downward.
- Body changes that add safety, resource-lifecycle, concurrency, operational-readiness, or contract checks select the promotion profile and publish candidate clause identifiers; generated summary drift alone does not downgrade them to a description-only canary.
- `--promotion-verdict <path>` validates independent, hash-bound evidence during apply.
- `--promotion-trust-root <path>` selects the public purpose-separated evaluator trust store; it does not authorize that store by itself.
- `--approved-trust-policy-sha256` and `--approved-trust-policy-revision` provide explicit operator approval for an `ApprovedTrustPolicy.v1` already present on the evaluated baseline's ancestry.
- `--finalize-existing-candidate` is only for a candidate already present in canonical SSOT and requires exact candidate-to-`HEAD` ancestry and hash equality.
- UAC does not own sealed cases, behavioral judging, promotion, or waivers.
- A new behavioral baseline is materialized only after promotion. Historical baseline lineage is preserved.
- During the advisory rollout, apply without a promotion verdict may land structurally ready canonical state, but the result remains `behavioral_pending` and cannot advance the behavioral baseline.
- During the advisory rollout, apply also compiles a draft Goal Contract and topology so a newly added skill cannot silently skip the evaluation inventory.
- The protected evaluator template lives under `tooling/protected-evaluator/`, but real keys, credentials, sealed cases, labels, and private judge or scorer implementations stay outside Core-Prompts.

- UAC publishes advisory metadata and handoff artifacts only. It does not decide runtime routing or delegation.
- Direct exposure lands in each vendor `skills/<slug>/SKILL.md` path when a capability is classified for direct use.
- This repo does not use UAC to target direct `commands/` or `prompts/` deployment paths.

## Related Docs

- [Getting started](GETTING-STARTED.md)
- [Examples](EXAMPLES.md)
- [UAC capability model](UAC-CAPABILITY-MODEL.md)
- [Baseline source library](../sources/ssot-baselines/README.md)
- [CLI reference](CLI-REFERENCE.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
