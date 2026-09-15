# FAQ

## What is the difference between a skill, an agent, and a prompt?

| Term | What it provides |
| --- | --- |
| Prompt | Instructions for a particular request. |
| Skill | Reusable instructions and supporting resources for a job. |
| Agent | A worker or session that follows instructions with its own execution settings. |
| Named agent | A saved configuration for a worker or session, such as its instructions, tools, or permissions. |

Start with the job and its skill. A named agent can make an execution configuration reusable; its name does not add intelligence or establish better results. One capability can have both packages without becoming two different capabilities. Prompt examples remain useful documentation; Core-Prompts does not emit a separate installable prompt package for those skill jobs.

Independent workers can isolate a review from the author's context and perform separate investigations concurrently. They also need context and resources, consume additional model and tool work, and can lose information during handoff. A generic independent worker can apply a skill when the host supports it, but must actually receive its instructions and required resources. It is not automatically equivalent to a named configuration: permissions, startup context, model settings, and delegation support can differ.

Choose a named configuration when those settings are useful for the task. Keep it when replacement behavior has not been verified. Core-Prompts currently generates agent adapters for Codex, Gemini, Claude, and Kiro. It emits skills for Grok but no Grok agent adapter; that is this repository's support boundary, not a statement that Grok cannot run subagents.

## Do I need agents installed to use Supercharge?

Use the Supercharge skill as the normal entry point. Ask “Supercharge this plan,” or select `engos-meta-supercharge` explicitly if your host does not discover it. Discovery and worker availability depend on the host; Core-Prompts does not install a universal router.

Supercharge's substantive reviews require real independent workers. A suitable generic worker can receive the skill and its resources without a matching named Supercharge package. If the host cannot provide the required independent review, the assistant must report that limitation. A named package alone does not prove independent review occurred. See [the direct and delegated examples](EXAMPLES.md#one-skill-in-the-main-session-or-an-independent-worker).

Fresh installs select skills by default. `--with-agents` opts into named configurations; existing saved selections remain in effect during routine updates. Do not remove existing packages solely because their names match skills. Review ownership and customizations through the [installation plan](INSTALL-PROFILES.md).

## Are Supercharge and Converge the same capability?

They overlap in comparing alternatives and producing a recommendation. Supercharge strengthens a prompt, plan, or workflow; Converge reconciles competing inputs with explicit conflicts, criteria, and decision outputs. Both remain available. Merging them requires evidence that their distinct controls and outputs survive. Neither replaces Auto-Research's measured behavioral experiments.

## What should I edit when I want behavior changes?
Edit `ssot/`. Generated surfaces and most descriptor details are derived.

## What is the difference between `apply`, `deploy`, and `package`?
- `apply`: writes canonical repo state and rebuilds surfaces
- `deploy`: copies generated surfaces to a target root
- `package`: creates release archives from the curated runtime/integration boundary

Use `deploy --surface-only --slug <slug>` for an intentionally narrow external-target copy that must not refresh the standalone updater, launcher, or local binaries.

## What does `judge` do?
`judge` runs the quality loop without landing canonical repo state. It is the safest way to see whether a candidate is ready for `apply`.

## What are `CAPABILITY-CATALOG.md`, `RELEASE-DELTA.md`, and `STATUS.md` for?
- `CAPABILITY-CATALOG.md`: generated inventory and lookup aid for what ships and where it lands
- `RELEASE-DELTA.md`: generated release-review aid for what changed versus the previous manifest
- `STATUS.md`: generated health snapshot for packaged output inspection

They are useful inspection views, not the first-stop onboarding docs.

## Do I need all CLI binaries installed?
No. They are only required for local smoke checks and target-specific deploy validation.

## Where should a future orchestrator start?
Read [ORCHESTRATOR-CONTRACT.md](ORCHESTRATOR-CONTRACT.md), then `.meta/capability-handoff.json`, then the per-capability descriptor files.

## Does Capability Fabric decide which capability should run?
No. Capability Fabric/UAC publish advisory metadata only. Routing and delegation stay outside.

## Do behavioral evals require users to return production review results?
No. Repository-owned synthetic diffs provide repeatable positive defects and matched safe controls for baseline-versus-candidate evaluation. De-identified field misses are useful additions when available, but the standing regression loop does not depend on users checking results back into Core-Prompts.
