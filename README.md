# Core-Prompts / Capability Fabric

Reusable skills for Codex, Gemini, Claude, Kiro, Grok and Antigravity (`agy`).
Core-Prompts supplies the skills and their resources; your project's rules and
host retain control of tools, permissions, routing and delivery.

**Describe the result you want; the assistant recommends the job and depth.**
You do not need to memorize skill names or choose between a brief frame and a full
workshop yourself. The assistant uses your context and accepted work, explains
its recommendation, and asks a focused outcome question only when the answer
would materially change the route, with an Other/free-text answer path.
`engos-route-intent` provides intake across the current catalog,
including nonengineering jobs. A clear direct task needs no new interview.

The intake skill is included in the prepared v1.18.0 source. Check the package available in
your session; pulling source, publishing a release and updating a live installation
are separate steps. Missing intake support uses the documented manual fallback.

Start with [your intent](docs/INTENT-ROUTING.md), browse the
[portable visual guide](docs/guide/index.html), or use the copyable request
below. These are conditional routes, not an automatic skill chain.

## What changes in everyday use

The earlier expansion from 32 to 36 skills added four focused software jobs.
Those names remain; catalog-wide adaptive intake now helps select these and other
current jobs without requiring users to learn the list:

| Instead of a broad ask… | Ask now… | Expect |
| --- | --- | --- |
| “Work out what this feature means and build it.” | `engos-design-specify-change`: define observable acceptance in our existing format. | Requirements, unchanged behavior and open decisions. |
| “Turn this into a goal.” for an ordinary task list | `engos-design-plan-implementation`: break down these accepted requirements. | Verifiable tasks, dependencies, interfaces and checks. |
| “Keep retrying this failing test.” | `engos-debug-diagnose-failure`: explain the failure before repair. | Reproduction and supported cause, or a bounded unknown. |
| “Use the full delivery factory for this small fix.” | `engos-delivery-implement-slice`: make this bounded authorized change. | A patch, actual checks and remaining limits. |

This is more precise selection, not a required new process. Your older asks still
work when they identify the job. Use the [flow guide](docs/SKILL-FLOWS.md) for
handoffs and [daily examples](docs/EXAMPLES.md#everyday-requests-before-and-now)
for bugs, features, design, refactoring, CI and larger delivery.

## Choose the job you need now

| You already have… / need… | Start here |
| --- | --- |
| A clear one-step change | `engos-delivery-implement-slice` |
| A failure with an uncertain cause | `engos-debug-diagnose-failure` |
| An unclear behavior or acceptance condition | `engos-design-specify-change` |
| A material technical choice | `engos-design-architecture` |
| Accepted requirements needing breakdown | `engos-design-plan-implementation` |
| An actual candidate to judge | `engos-quality-code-review` |
| Selected actionable reviewer comments | `engos-delivery-address-code-review` |
| A rough product problem or a finished pitch | [Shaping and pitch review](docs/SKILL-FLOWS.md#framing-and-shaping) |
| A stronger artifact, competing sources, or resumable work | [Optional jobs](docs/SKILL-FLOWS.md#optional-jobs-around-the-main-flow) |

The [job map](docs/SKILL-JOB-MAP.md) describes skill names, boundaries and neighbors.
The intake skill inspects the current catalog; new or updated jobs remain eligible
even when a curated relationship is missing or stale. It is a lookup aid; read the chosen skill's complete
entry and selected resources before using it. `loopy` retains its upstream name;
first-party skills use `engos-*`. No proposed rename or alias is needed.

For competing proposals, Converge distinguishes source-supported preferences from
illustrative scores. Its [numerical comparison checks](docs/EXAMPLES.md#verified-numerical-comparison)
verify arithmetic and scoped sensitivity claims, preserve ties/counterexamples,
and fall back to qualified qualitative reasoning when a model cannot be checked.

## Use this with AI

After installation and native discovery, say:

> Use `engos-route-intent` to help me choose the next useful step for [situation].
> Reuse the context and accepted work I supplied. Explain your recommendation and
> ask only questions that would change the approach, using Other/free text.
> Continue within [authorized scope].

Native skill discovery may select it from an uncertain request without an explicit
name. Clear direct work bypasses the interview. The [contained usage guide](docs/INTENT-ROUTING.md#use-the-contained-skill-package)
explains explicit invocation and tool support. No external repository, global-rule
activation or service is required. Core supplies the skill and its resources;
your project and harness retain their workflow and permissions.

For Antigravity from a terminal, the same skill also bundles an optional
[one-turn headless intake command](docs/GETTING-STARTED.md#antigravity-headless-intake).
Supply your request once; inspect the native structured result or one question
with Other/free text. It adds no global command, interactive question UI or
settings change. An already running AGY chat keeps its current tools and flags.

## Install or refresh your setup

If the skill is already available, try it before changing setup. Otherwise use
[installation and recovery](docs/INSTALL-PROFILES.md) from a trusted release or
verified source checkout: inspect the target, preview, review, then apply only
within your authorization. Old installations do not need a working updater first.

A saved 32-skill selection stays at 32 on routine sync. Explicitly choose
[the current catalog and future additions, or named curated additions](docs/INSTALL-PROFILES.md#choose-future-skill-membership).
Codex and Gemini share `~/.agents/skills`; expansion needs the documented joint
consent when both readers are affected. Six readers use five generated
provider distributions; `agy` reads the Gemini package.

Preview identity-based historical Core cleanup and inspect preservation notices.
Customized skills and non-Core agents, including Addy packages, retain their
protections. The [exact retired Core-agent exception](docs/INSTALL-PROFILES.md#historical-recognition-and-preservation)
can retire locally modified agents identified by definition name and bundled
metadata, with a same-job skill replacement and recoverable transaction. Symlink,
identity, configuration and dependency conflicts still guard removal. Review the
exact preview; do not clean by name glob. Missing selected Grok packages have
[exact recovery](docs/INSTALL-PROFILES.md#restore-wholly-missing-owned-grok-skills);
recovery is separate from native discovery. [Transaction listing and rollback](docs/INSTALL-PROFILES.md#recover-an-installation)
provide the recovery path.

## Skills, workers and larger delivery

The current generated surfaces contain `37` skills and no shipped named-agent configurations.
Use the same skill in your main session or supply it and required resources to a
real independent worker when requested or required by its contract. A second
answer from the same author does not establish independent review. [Examples](docs/EXAMPLES.md#one-skill-in-the-main-session-or-an-independent-worker).

Invoke `engos-orchestration-batman` explicitly when you want its controller-led
delivery protocol. Keep ordinary planning with `engos-design-plan-implementation`;
use `engos-design-plan-to-goal` for a separately wanted durable goal/spec/verifier
packet. Compiling a packet does not start a goal. [Longer work](docs/SKILL-FLOWS.md#long-horizon-and-repeatable-work).

For resumable investigations, use `engos-memory-context-continuity` and its bundled
state helper to resolve one context, todo and insights set under
`~/.analyze-context/<project>/<task-id>/`, outside every checkout. Keep one writer
per task; branch and worktree paths are metadata only. Checkpoint before context
loss or worktree cleanup, and retain completed files until later user-approved
cleanup. See the [continuity example](docs/EXAMPLES.md#engos-memory-context-continuity).

## Source, installation and release are separate

Merged source does not update installed skills. Installed bytes do not prove a
fresh session discovers them; project-local copies may override global ones.
A published release, an installed source revision, native discovery and an
observed task result each need their own evidence. Check the actual version and
revision for your target rather than inferring them from this page. See
[current release gates](docs/RELEASE-PACKAGING.md#publication-and-live-rollout-hold)
for publication, live installation and runner holds. Updating skills does not
resume a paused runner or change schedules.

## UAC and repository maintenance

For importing or improving capability source, use
[`engos-meta-uac-import` and UAC](docs/UAC-USAGE.md). For precise instruction edits,
use [`engos-meta-instruction-editor`](docs/EXAMPLES.md#engos-meta-instruction-editor).
The lasting fix belongs in canonical source and resources, then generated
surfaces; installed bundles are destinations. Maintainers follow
[repository workflow](.kiro/steering/repo-workflow.md),
[maintainer hygiene](docs/MAINTAINER-HYGIENE.md) and
[CLI reference](docs/CLI-REFERENCE.md). These are maintenance paths, not setup
requirements for every user task.

## Optional documentation recipes

Use `engos-quality-docs-review` for ordinary documentation review. Name
`readme-authoring` when you want only README_vNext.md ending in Claim Notes;
choose `docs-bundle` for the README, technical README, visuals plan and factual
audit together. See [all recipe asks and exact outputs](docs/EXAMPLES.md#optional-documentation-recipes).

For candidate-bound ship evidence, use `engos-quality-gitops-review` with
`docs-release-readiness`. The `factual-audit` recipe's original E verdict checks
documentation content: E content PASS does not establish hosted readiness.
Merge/release readiness needs independently reproduced committed candidate bytes
and exact-head hosted checks; dirty snapshot bytes with green HEAD CI cannot pass.
Recipe selection and proposed commands add no commit, merge or release authority.

## Documentation map

- [Getting started](docs/GETTING-STARTED.md): first use, context and setup checks.
- [Skill flows](docs/SKILL-FLOWS.md): next job, what to skip and what to carry forward.
- [Examples](docs/EXAMPLES.md): copyable requests and expected results.
- [Docs home](docs/README.md): author, operator and maintainer paths.
- [Operational incident review](docs/EXAMPLES.md#engos-audit-opex-incident-review):
  use `engos-audit-opex-incident-review` for the Daily OpEx Digest and incident drill-downs.
- [FAQ](docs/FAQ.md): skill/agent distinctions, selection and evidence limits.
- [Orchestrator contract](docs/ORCHESTRATOR-CONTRACT.md): advisory metadata for external harnesses.
- [Capability catalog](docs/CAPABILITY-CATALOG.md), [release delta](docs/RELEASE-DELTA.md)
  and [status](docs/STATUS.md): generated inspection views, secondary to usage guidance.
