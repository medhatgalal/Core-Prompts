# Core-Prompts / Capability Fabric

Reusable skills for Codex, Gemini, Claude, Kiro, Grok and Antigravity (`agy`).
Core-Prompts supplies the skills and their resources; your project's rules and
host retain control of tools, permissions, routing and delivery.

**Returning user? Start with the job you are missing.** A clear small change can
go directly to `engos-delivery-implement-slice`. You do not need to run every
skill in a sequence, invoke Batman, or create new planning documents first.

## What changes in everyday use

The catalog grew from 32 to 36 skills. Existing names remain; four focused jobs
make it easier to ask for exactly the missing work:

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

The [job map](docs/SKILL-JOB-MAP.md) lists **all 36 current names**, their
boundaries and neighbors. It is a lookup aid; read the chosen skill's complete
entry and selected resources before using it. `loopy` retains its upstream name;
first-party skills use `engos-*`. No proposed rename or alias is needed.

## Use this with AI

From a trusted source checkout or verified distribution, replace the brackets:

> Help me use Core-Prompts for [job] in [project and allowed scope]. Read this
> Core-Prompts root's AGENTS.md and applicable guidance, then docs/GETTING-STARTED.md
> and the relevant route in docs/SKILL-FLOWS.md; use docs/SKILL-JOB-MAP.md to
> resolve nearby jobs. Follow my project's rules and the host's authority.
> Reuse accepted work and choose the first missing job, using the smallest
> relevant skill and its complete entry plus selected resources. Check the exact
> package available in this session. Explain the artifact and actual verification
> or acceptance status. Report missing setup or evidence rather than guessing.
> Do not install, publish, release, schedule or send messages unless my request
> authorizes that action.

This is a copyable request, not installed global routing policy. Core-Prompts
does not install a universal automatic Core-first router or replace your harness.
Ordinary use in another project does not require Core-Prompts source-maintainer
tools, UAC or its PR/MR workflow. [First successful use](docs/GETTING-STARTED.md).

## Install or refresh your setup

If the skill is already available, try it before changing setup. Otherwise use
[installation and recovery](docs/INSTALL-PROFILES.md) from a trusted release or
verified source checkout: inspect the target, preview, review, then apply only
within your authorization. Old installations do not need a working updater first.

A saved 32-skill selection stays at 32 on routine sync. Explicitly choose
[all 36 and future additions, or named curated additions](docs/INSTALL-PROFILES.md#choose-future-skill-membership).
Codex and Gemini share `~/.agents/skills`; expansion needs the documented joint
consent when both readers are affected. Six readers use five generated
provider distributions; `agy` reads the Gemini package.

Preview identity-based historical Core cleanup and inspect preservation notices.
Customized and third-party skills/agents, including Addy packages, retain their
protections. Do not clean by name glob. Missing selected Grok packages have
[exact recovery](docs/INSTALL-PROFILES.md#restore-wholly-missing-owned-grok-skills);
recovery is separate from native discovery. [Transaction listing and rollback](docs/INSTALL-PROFILES.md#recover-an-installation)
provide the recovery path.

## Skills, workers and larger delivery

The current generated surfaces contain `36` skills and no shipped named-agent configurations.
Use the same skill in your main session or supply it and required resources to a
real independent worker when requested or required by its contract. A second
answer from the same author does not establish independent review. [Examples](docs/EXAMPLES.md#one-skill-in-the-main-session-or-an-independent-worker).

Invoke `engos-orchestration-batman` explicitly when you want its controller-led
delivery protocol. Keep ordinary planning with `engos-design-plan-implementation`;
use `engos-design-plan-to-goal` for a separately wanted durable goal/spec/verifier
packet. Compiling a packet does not start a goal. [Longer work](docs/SKILL-FLOWS.md#long-horizon-and-repeatable-work).

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
