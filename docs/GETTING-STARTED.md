# Getting Started

Start with one real outcome, not a skill or framework name. The assistant uses
your intent, available artifacts and accepted work to recommend a first job and
the depth needed to produce the result. The available
`engos-route-intent` skill applies this method across the current
catalog. It asks a focused question only when an unknown would materially change
the route, always offering Other/free text. Use the [intent guide](INTENT-ROUTING.md) or
[portable visual guide](guide/index.html) when you are unsure where to start;
[skill flows](SKILL-FLOWS.md) explain conditional handoffs.

## Fast path: use what is already available

1. **Describe the outcome, context and scope.** For example: “Fix this demonstrated
   off-by-one error in the pagination helper; preserve sorting and permissions.”
   The assistant can choose `engos-delivery-implement-slice` and proceed with the
   authorized change. A clear one-step task needs no fresh specification or
   elaborate plan. A vague problem, unclear acceptance and competing proposals
   are different starts; see [the intent table](INTENT-ROUTING.md#find-the-first-missing-job).
2. **Check the selected package.** The assistant identifies the exact skill and
   effective package from this host's available skills, reads its complete entry,
   and loads only the resources needed for the job. You can still name a skill
   explicitly. Repository catalog presence alone does not establish native discovery.
3. **Inspect the result.** Expect the requested artifact and an honest account
   of what was checked, what remains uncertain and the next needed job. A patch
   should include actual verification; a test design is still `not_run`.

The routing explanation is brief: the recommended outcome and depth, why they
fit your context, one skill and a next handoff only if needed. You do not have to
choose "lightweight" versus "full" shaping. If that distinction matters and your
request leaves it open, the assistant describes practical result options and
recommends one, using an available question tool or focused inline choices.
It reuses known answers and does not interview you for a clear direct task.
An audit, incident review, attention queue, report or presentation uses the same
intake method and goes to its own current owner. If the router is unavailable,
report that and use only a bounded manual fallback; do not claim it was loaded
or install it automatically.
See [how intake adapts](INTENT-ROUTING.md#let-the-assistant-recommend-how-far-to-go).
Routing itself is not a new approval gate or additional execution permission.
Use the [contained package](INTENT-ROUTING.md#use-the-contained-skill-package)
through native discovery or explicit selection in any supported project. It does
not require another repository or home-global instruction changes.

If the requested job requires independent review, expect a real separate reviewer
and the skill's repair cycle. If that support is unavailable, the dependent review
gate remains incomplete. Neither a named package nor an author's checklist proves
independent review. [Direct and delegated examples](EXAMPLES.md#one-skill-in-the-main-session-or-an-independent-worker).

## Antigravity headless intake

After verifying/upgrading the existing `engos-route-intent` package, put your
complete request in a UTF-8 `request.txt`. Include the intended bounded result,
read-only scope and known facts. From the project you want AGY to read, run one
of these alternatives:

```bash
python3 "$HOME/.gemini/config/skills/engos-route-intent/resources/scripts/agy_intake.py" --prompt-file request.txt
```

Or send the same bytes through standard input:

```bash
python3 "$HOME/.gemini/config/skills/engos-route-intent/resources/scripts/agy_intake.py" < request.txt
```

Requires Python 3.11+, POSIX and a separately configured `agy` on PATH. The helper
passes the request unchanged, supplies the bundled schema and sibling skill root,
and preserves the complete native JSON stream. Inspect its final `selected_skill`,
`route_reason`, `bounded_result`, `unresolved_facts`, `questions` and
`awaiting_answer`. A clear bounded request should produce a result without an
interview; a material unknown permits one atomic question with Other/free text,
then stops. Native completion is not proof that these semantic requirements passed.

This mode has a total 240-second limit and does not run the selected downstream
workflow. It changes no model defaults, permissions or provider settings. It is
not a native question UI. Inside an existing AGY chat, ask for the routing skill
normally and use exposed question tools or inline Other/free text; do not launch
another AGY process to retrofit flags. [Examples](EXAMPLES.md#antigravity-bounded-intake)
and the [complete adapter contract](../.gemini/skills/engos-route-intent/resources/references/agy-intake.md)
explain output, interruption, scope and known evidence limits.
[Upgrade and rollback](INSTALL-PROFILES.md#upgrade-the-antigravity-intake-resource)
remain separate from invoking the command.

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
The [job map](SKILL-JOB-MAP.md) supports source-side lookup; the
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

For a long investigation that must survive session or worktree changes, use
`engos-memory-context-continuity`. Its bundled state helper resolves the canonical
`~/.analyze-context/<project>/<task-id>/` directory outside the repository; recover
the exact task's context, todo and insights files before continuing. Keep one
writer and checkpoint meaningful progress. Mark completion only after every TODO
is checked and insights contains the final summary; leave completed files in
place until later user-approved cleanup.

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
