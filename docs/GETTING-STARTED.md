# Getting Started

Choose one real task and the first missing job. If your skill is already
available, the fast path below is enough. Use [skill flows](SKILL-FLOWS.md) for
conditional handoffs and [examples](EXAMPLES.md#everyday-requests-before-and-now)
for copyable everyday asks.

## Fast path: use what is already available

1. **Name the outcome and scope.** For example: “Use
   `engos-delivery-implement-slice` to fix this off-by-one error in the pagination
   helper; preserve sorting and permissions.” A clear one-step change needs no
   new specification or elaborate plan.
2. **Check the session's package.** Select the exact skill name using the host's
   available skill list. Ask the assistant to identify the effective package,
   read its complete entry and load only the resources selected for this job.
   Repository catalog presence alone does not establish native discovery.
3. **Inspect the result.** Expect the requested artifact and an honest account
   of what was checked, what remains uncertain and the next needed job. A patch
   should include actual verification; a test design is still `not_run`.

If the requested job requires independent review, expect a real separate reviewer
and the skill's repair cycle. If that support is unavailable, the dependent review
gate remains incomplete. Neither a named package nor an author's checklist proves
independent review. [Direct and delegated examples](EXAMPLES.md#one-skill-in-the-main-session-or-an-independent-worker).

## Returning from the 32-skill catalog

Four new jobs make everyday selection more precise:

| Missing work | Current exact name | You can skip it when… |
| --- | --- | --- |
| Define behavior and acceptance | `engos-design-specify-change` | Accepted requirements already cover the change. |
| Break accepted scope into verifiable tasks | `engos-design-plan-implementation` | The authorized change is already one useful bounded task. |
| Establish a cause | `engos-debug-diagnose-failure` | Cause and repair boundary are already supported by evidence. |
| Make a bounded change | `engos-delivery-implement-slice` | You asked only for analysis, planning or review. |

Keep existing names. Ordinary planning is now clearly separated from
`engos-design-plan-to-goal`, which compiles a separately requested durable packet.
Architecture is useful for a material design choice; it is optional when an
accepted design already answers that question. Batman remains explicitly selected.
The [job map](SKILL-JOB-MAP.md) covers all 36 names; the
[flow guide](SKILL-FLOWS.md) explains the next handoff.

Routine updates preserve saved membership. To expand an old 32-skill selection,
choose [full catalog or named curated additions](INSTALL-PROFILES.md#choose-future-skill-membership)
explicitly. A checkout update alone does not activate those skills.

## Check your Core-Prompts context

The same AGENTS and steering files travel with source and release archives.
Their [execution-context rules](../.kiro/steering/agent-behavior.md#execution-context)
separate ordinary use from maintaining Core-Prompts itself.

- A complete source layout contains canonical `ssot/` entries,
  `.meta/surface-rules.json`, `scripts/build-surfaces.py` and
  `scripts/validate-surfaces.py`. Source maintenance also needs verified source
  identity and Git readiness.
- A distribution omits those authoring inputs and includes the portable installer,
  capsule and runtime inventory. From its trusted extracted root, inspect the
  existing inventory without installing:

  ```bash
  python3 -B -c 'from pathlib import Path; import sys; sys.path.insert(0, "scripts"); import install_bundle; print(len(install_bundle.verified(Path.cwd())), "verified runtime paths")'
  ```

  Consistency is separate from trusted origin, discovery and permission to install.
- A partial layout or missing/failed inventory is a setup gap. Missing `.git`
  alone does not establish a distribution. Report the gap; do not rebuild hashes
  or edit the bundle to make it pass.

For ordinary work in your authorized project, follow that project's rules and the
selected bundled skill/resources. You do not need Core-Prompts SSOT, UAC, a source
build, a new Core-Prompts worktree or its PR/MR workflow. Changing Core-Prompts
itself needs a separately verified complete source checkout.
[Distribution example](EXAMPLES.md#use-a-distribution-in-your-project).

## Safe path: verify setup before changing it

Use [installation and recovery](INSTALL-PROFILES.md) as the command authority.
From a trusted current release or verified source checkout, preview a Kiro repair:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --cli kiro --repair --dry-run > /tmp/core-prompts-install-plan.json
```

Review exact selection, actions, preserved content and blockers. Apply only with
installation authority, using the same source, target and reviewed plan:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --apply-plan /tmp/core-prompts-install-plan.json
```

Repair recognizes historical Core identities; it does not authorize blanket
cleanup or membership expansion. Preserve customized/unowned skills and unrelated
packages, including Addy packages. Do not use broad name globs to remove old
skills or agents. Explicit Claude adoption and wholly missing selected Grok
recovery have separate guarded previews in the installation guide.

For accepted source ahead of a release, follow
[upgrade from verified main](INSTALL-PROFILES.md#upgrade-from-verified-main-before-the-next-release).
Record the source revision and compare actual installed packages/resources,
including preserved differences. Check publication and runner status in the
[release gates](RELEASE-PACKAGING.md#publication-and-live-rollout-hold); do not
infer either from a source merge or an installer success.

## Verify discovery on your host

Six installation readers use five generated distributions. Codex and Gemini
share the global `~/.agents/skills` directory; `agy` reads the portable Gemini
package through its separately documented target. Other providers have their
own targets. [Exact roots, consent and native checks](INSTALL-PROFILES.md).

Use the current host's skill listing/help and installed package instructions to
verify invocation; Codex uses `$<skill-name>` and Grok exposes `/<skill-name>`.
A conversational “Use engos-delivery-implement-slice…” is a request to your
assistant, not a new provider CLI flag. Do not assume Kiro or `agy` invocation
flags from another provider. Check their documented, version-bound behavior.

After installation, test in a fresh session. Check whether a project-local copy
shadows the global package and identify which bytes the session loaded. Explicitly
reading a package can support a manual workflow; it does not prove native discovery.
A successful package recovery likewise does not prove discovery or task success.

## What success looks like

You can identify the skill used, its effective package, the requested artifact
and the evidence obtained. A specification separates accepted behavior from open
decisions. A plan preserves unfinished work and names verifiable outcomes. A
repair reports its actual patch/checks. An unexplained failure stays unknown.
Continue only to the next missing job and applicable repository delivery boundary;
installation, release and schedules remain separate actions.

Optional contracts such as `SpecContract.v1`, `TaskPlan.v1` and `SliceReceipt.v1`
help interchange but do not require a new document system. Existing issue and
tracker formats remain valid. A schema or graph check proves declared structure,
not approval, behavioral correctness or completion.

## Troubleshooting

| Symptom | Next useful check |
| --- | --- |
| Skill name is absent | Inspect saved membership and the exact provider/root; preview a named addition if wanted. |
| Updated package still behaves like the old one | Inspect preserved differences, session age and project-local overrides. |
| Installer reports preserved content | Read each preservation reason; success with preserved files is not full package parity. |
| A selected Grok package is wholly absent | Use [exact missing-package recovery](INSTALL-PROFILES.md#restore-wholly-missing-owned-grok-skills), then verify discovery separately. |
| A task needs unavailable tools or a separate reviewer | Report the missing support and hold the dependent step. |
| An install needs undoing | [List transactions and preview rollback](INSTALL-PROFILES.md#recover-an-installation); later edits can block restoration. |

## How Batman starts and resolves companions

Use `engos-orchestration-batman` only when explicitly requested. Expect instruction
integrity and host-fit checks, a controller, bounded implementers and independent
reviewers. It resolves companions against current available skills/resources;
missing required support remains a hold. [Full example](EXAMPLES.md#engos-orchestration-batman).

## How Batman reports proof and landing state

Its contract distinguishes local verification, hosted checks, merge, publication,
installation and cleanup. The job stops at the authorized boundary; a local pass
cannot establish a release or live rollout. [Delivery examples](EXAMPLES.md#engos-orchestration-batman).

## Optional documentation recipes

Use `engos-quality-docs-review` for ordinary documentation review. Name
`readme-authoring` when you want only README_vNext.md ending in Claim Notes;
choose `docs-bundle` for the README, technical README, visuals plan and factual
audit together. See [all recipe asks and exact outputs](EXAMPLES.md#optional-documentation-recipes).

For candidate-bound ship evidence, use `engos-quality-gitops-review` with
`docs-release-readiness`. The `factual-audit` recipe's original E verdict checks
documentation content: E content PASS does not establish hosted readiness.
Merge/release readiness needs independently reproduced committed candidate bytes
and exact-head hosted checks; dirty snapshot bytes with green HEAD CI cannot pass.
Recipe selection and proposed commands add no commit, merge or release authority.

## Next docs

- [Skill flows](SKILL-FLOWS.md): skip conditions, artifacts and optional neighbors.
- [Examples](EXAMPLES.md): focused asks, shaping, reviewed artifacts and recipes.
- [Operational incident review](EXAMPLES.md#engos-audit-opex-incident-review):
  `engos-audit-opex-incident-review` for the Daily OpEx Digest and evidence-backed drill-downs.
- [FAQ](FAQ.md): skills, workers and provider boundaries.
- [Installation and recovery](INSTALL-PROFILES.md): exact selection, preview,
  recovery, updater and optional schedule commands.
- [UAC usage](UAC-USAGE.md): capability authoring and improvement.
- [CLI reference](CLI-REFERENCE.md) and [maintainer hygiene](MAINTAINER-HYGIENE.md):
  source maintenance and validation.
