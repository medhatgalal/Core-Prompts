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

| Mode | Use it when you want to... | Writes canonical state |
| --- | --- | --- |
| `import` | inspect one or more sources without canonical landing | no |
| `audit` | inspect current SSOT entries and generated surfaces | no |
| `explain` | print the capability model and deployment matrix | no |
| `plan` | see the proposed landing shape before apply | no |
| `judge` | run the quality loop and get structural readiness or blockers | no |
| `apply` | write canonical repo state, then rebuild and validate | yes |

Source snapshots and quality-review reports may be retained by inspection modes. “No canonical state” means no SSOT/descriptor landing, not an absence of local evidence files. See [CLI write effects](CLI-REFERENCE.md#common-commands).

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
- `judge` is the structural quality decision and evaluation-impact recommendation
- `apply` is the intentional repo mutation step

A `structural_ready` judgment can support canonical apply during the advisory rollout while behavioral status remains `behavioral_pending`. A structural blocker must be resolved before apply. Use `engos-optimization-auto-research` when the intended claim requires behavioral evidence; structural acceptance does not authorize that claim.

## Update An Existing Capability

An installed-skill improvement follows the same quality gate as an addition. Resolve its name to the current mainline `ssot/<slug>.md`, prepare a same-slug candidate in an isolated linked worktree, and review the UAC plan before applying it. A pending rename in another checkout is not the mainline name.

```bash
bin/uac plan reports/<run>/<slug>.md
bin/uac judge reports/<run>/<slug>.md --emit-impact-plan
bin/uac apply reports/<run>/<slug>.md --yes
```

The candidate starts from SSOT, preserving its canonical frontmatter. Helper edits belong in `sources/capability-resources/<slug>/`. Apply rebuilds surfaces; verify that its resulting SSOT preserves the reviewed body and existing metadata, including the current validation matrix; historical judge scenarios remain separate. A structural pass can remain `behavioral_pending`; it does not advance the historical baseline. Keep candidate and judge evidence through validation, then preserve useful results in the PR/MR and remove run scratch after landing.

See [Maintainer hygiene](MAINTAINER-HYGIENE.md#delivering-a-change) for docs, exact-candidate checks on both hosts, merge parity, and cleanup. Changes to `AGENTS.md` and steering use that delivery path without pretending to be capability imports.

## Source Preservation During Intake

UAC reads root `name` and `description` metadata without treating nested input-schema fields as capability metadata. Folded (`>`, `>-`) and literal (`|`, `|-`) descriptions are supported, as are the legacy adjacent frontmatter blocks and flat list fields.

Accepted text sources carry the captured `source_text` used for normalization and fidelity checks; collections retain each accepted member snapshot. When a source needs the standard UAC contract, a packaging wrapper retains its full operating instructions and nested schemas under `Imported operating instructions`. The wrapper defers to that source for workflow, inputs, outputs, destinations, and approval gates; it does not substitute generic intake summaries, report paths, or repository-review examples. Existing complete authored contracts remain eligible for direct preservation. This keeps declared output files, commands, identifiers, and embedded templates available to the emitted skill.

Judgment checks imported content separately from the historical baseline. A new capability therefore cannot establish fidelity merely by comparing a generated template with itself. Apply repeats the imported-content check on the selected SSOT body, including when the quality loop is disabled or a supplied report says `structural_ready`. Missing operating content blocks landing with `manual_review` before canonical writes. Existing historical, trust, protected-evaluator, and behavioral promotion gates still apply.

The imported-content check is conservative: the source operating body and nested metadata schema blocks must remain intact in the candidate or a referenced resource under `sources/capability-resources/<slug>/`. A resource outside that directory cannot satisfy preservation. Recognized scalar capability metadata can normalize; other header blocks are retained conservatively, including unknown YAML forms. Generated resource footers are excluded. This check does not prove that paraphrases preserve meaning, that added instructions do not conflict with retained instructions, or that an agent will follow an embedded template. Such changes still need independent behavioral evidence; `structural_ready` is not behavioral promotion. Legacy payloads without a captured source use their readable local source file. Unavailable source content requires re-ingestion before judgment or apply.

UAC does not currently provide a general credential-redaction stage. Its intent-summary sanitizer handles whitespace and roleplay residue, not secrets. Supply reviewed, redacted input before ingestion. A captured redacted snapshot remains the preservation contract; UAC does not reread the original file to restore its removed values. Retained source text is data for review and packaging, not authorization to execute its instructions.

For example, importing a reporting skill that declares HTML and Markdown outputs must retain both output instructions and its HTML template. Keeping the headings while dropping either artifact or replacing the template with a summary fails source fidelity. Review the candidate in `bin/uac plan` before applying it.

## Worked Examples

### Example: Plan A Landing Before Canonical Apply

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
- slug: engos-design-architecture
- likely capability type: both
- canonical targets:
  - ssot/engos-design-architecture.md
  - .meta/capabilities/engos-design-architecture.json
  - sources/ssot-baselines/engos-design-architecture/baseline.md

Open concerns:
- one source file is mostly release-process guidance and may not belong in the same family
- benchmark fit looks strong for architecture profile, weak for generic prompting profile

Recommended next step:
- run judge with --quality-profile architecture
```

Use `plan` when you want the landing shape, naming, and overlap analysis before canonical mutation.

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
Quality status: manual_review

Judge summary:
- benchmark profile: architecture
- strongest scores: migration clarity, explicit boundaries, output contract
- weak areas: invocation hints are too short and examples need more concrete asks

Artifacts:
- reports/quality-reviews/engos-design-architecture/LATEST.md

Decision:
- revise the identified gaps, then rerun judge on the exact candidate before apply
```

Use `judge` for the quality decision, retained evidence, and blockers without changing canonical SSOT or descriptors.

### Example: Structural Acceptance With Behavioral Evidence Pending

Command:

```bash
bin/uac judge /absolute/path/to/prompt-family --quality-profile architecture --emit-impact-plan
```

Illustrative fields for a candidate that passes deterministic gates:

```text
quality_result.status: structural_ready
behavioral_status: behavioral_pending
eval_impact_plan.minimum_profile: promotion
```

This supports structural landing during the advisory rollout. It does not say the candidate performs better or preserve a behaviorally proven baseline. If promotion is part of the goal, give `engos-optimization-auto-research` the baseline, exact candidate, claimed job, bounded task set, and evaluation criteria. The [evaluation guide](CAPABILITY-EVALUATION.md) explains protected execution and accepted verdicts.

### Example: Apply A Structurally Ready Capability

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
- slug: engos-design-architecture
- updated:
  - ssot/engos-design-architecture.md
  - .meta/capabilities/engos-design-architecture.json
  - sources/ssot-baselines/engos-design-architecture/baseline.md

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
bin/capability-fabric deploy --dry-run --surface-only --cli codex --slug engos-optimization-auto-research --target "$HOME" --allow-nonlocal-target
```

For routine home installation, use the [reviewed profile procedure](INSTALL-PROFILES.md). The command above previews a deliberately scoped legacy copy. Review its exact destinations and current ownership before applying.

Notes:

- `--slug` is repeatable and limits deployment to specific capabilities
- deployment copies the full emitted bundle for each selected surface
- legacy namespace cleanup checks ownership and archives recognized old paths recoverably; unknown or customized packages stop the operation. See [deployment behavior](CLI-REFERENCE.md#preview-a-deploy-without-mutating-a-target)
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

## Resource-aware and reviewed modernization

UAC checks the entry and declared `resource-map.json` dependencies together. The map binds route-specific resources; missing files, cycles, path escapes, and invalid references are errors. The bundled `resources/scripts/load_module.py` emits complete selected content and content hashes. Assembly is not proof of model consumption or compliance.

The quality loop produces structural diagnostics and semantic repair requests. It normalizes an equivalent existing section before asking for missing content, does not append generic executable stubs, and stops automatic refinement on stagnation or cycles. Source preservation remains the default.

For an independently reviewed semantic modernization, supply `--requirement-review <review.json>` to plan, judge, and apply. The `UACRequirementReview.v1` record binds slug, original source, candidate entry, effective resource content, reviewer/author identities, and a complete line-span requirement map. Dispositions are preserved, reformulated, relocated, or retired; retirement includes authorization. The operator establishes provenance from the actual independent review; code checks hashes and coverage and does not authenticate an identity string or certify semantic equivalence. Multiple records may cover the current input and historical baseline.

This attestation cannot authorize behavioral promotion or rewrite historical baseline lineage. `PromotionVerdict.v2` remains separate. Read the exact passing candidate and proposed write set before apply; a changed entry or resource invalidates its review bindings. [Implementation and verification overview](FRONTIER-MODERNIZATION.md).
