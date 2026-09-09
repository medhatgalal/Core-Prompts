# Getting Started

Start with a capability that matches your task. This page covers first use; [Examples](EXAMPLES.md) contains complete asks and expected outputs. If you need an installation first, use the [home-install quickstart](quickstart.md).

## Invoke a capability

Core-Prompts generates skill packages for Codex, Gemini, Claude, Kiro, and Grok. Use the full `engos-<category>-<skill-name>` name; the upstream-pinned `loopy` package retains its own name.

| Host | First use |
| --- | --- |
| Codex | Select `$engos-design-experience` and describe your task. The selected home profile uses `.agents/skills`. |
| Claude | Select `/engos-design-experience` or ask Claude to use the named installed skill. |
| Gemini | Ask Gemini to use `engos-design-experience`; `gemini skills list` checks listed skills. |
| Kiro | Select `/engos-design-experience` in a skill-enabled session. Custom agents need the appropriate skill resources configured. |
| Grok | Select `/engos-design-experience`; native packages live under `.grok/skills`. |

The invocation forms follow the official [Claude skills](https://code.claude.com/docs/en/skills), [Gemini skills](https://geminicli.com/docs/cli/skills/), and [Kiro skills](https://kiro.dev/docs/skills/) guidance, checked on 2026-09-09. Skill availability depends on the installed package and host configuration. Check the [installation and discovery guide](INSTALL-PROFILES.md#discovery-evidence-and-limits) when a skill is missing or duplicated. A listed skill, registered agent, and successfully exercised task are distinct evidence.

Some capabilities also emit an agent surface. Ask the host to delegate to the named agent when available; otherwise use the installed skill within the host's supported workflow. The [catalog](CAPABILITY-CATALOG.md) shows which surfaces each capability emits. Grok has a native skill surface only.

## Complete your first task

Give the skill an outcome, the relevant input or artifact, and any scope constraint:

> Use `engos-design-experience` to improve this comparison report. Keep the supplied data, make the trade-offs easy to scan, and retain access to the full evidence. Compare meaningful alternatives where needed, then revise and inspect the final artifact.

Expect the artifact plus its advantages, trade-offs, observed checks, and remaining uncertainty. The skill uses the existing product foundation, selects methods according to the decision, and preserves settled directions. Stateful work aligns displayed status and available actions with the actual API contract. Static reports may need no failure probes; saving and retry flows often do.

For web, desktop, or mobile work, name the real target and available source. A browser simulation can explore a native flow, but its handoff identifies which target-runtime checks remain unverified. See the [worked experience-design examples](EXAMPLES.md#engos-design-experience).

## Choose the next capability

| Need | Capability | Expected result |
| --- | --- | --- |
| Durable investigation across files and sessions | `engos-memory-context-continuity` | context, todo, and insights under `~/.analyze-context/<project>/<task-id>/`, with current findings and preserved history |
| Documentation placement and drift review | `engos-quality-docs-review` | exact findings, rewrite targets, and navigation fixes |
| Pre-commit correctness review | `engos-quality-code-review` | findings tied to the diff, lifecycle and contract risks, and readiness guidance |
| Existing PR/MR feedback applied | `engos-delivery-address-code-review` | selected comments addressed with scoped edits and follow-up verification |
| Git-derived engineering report | `engos-audit-engineering-progress` | deterministic metrics and a report tied to them; start with the skill's `help` |
| Daily incident decision digest | `engos-audit-opex-incident-review` | decisions, owner obligations, progress versus corrections, source caveats, and local reports |
| A reviewed plan made executable as a bounded goal | `engos-design-plan-to-goal` | researched goal/specification/verifier packet without automatically launching it |
| Prompt improvement and independent review | `engos-meta-supercharge` | a revised prompt; `supercharge /ult /full skip grade <prompt>` does not execute the target task |
| Measured improvement over candidate trials | `engos-optimization-auto-research` | a bounded experiment, retained best candidate, and evidence-qualified outcome |
| Implementation through independent subagents and gates | `engos-orchestration-batman` | a Host-Fit Plan, milestone evidence, progress, and separate delivery receipts |
| Bounded reusable agent loops | `loopy` | loop discovery, audit, creation, execution, or debrief within the requested scope |

Use the [Skill Job Map](SKILL-JOB-MAP.md) for neighboring boundaries and [Examples](EXAMPLES.md) for every capability. Supercharge and Auto-Research keep requested deliverables at stable project paths; their [workflow guide](FRONTIER-MODERNIZATION.md) explains independent review and evidence limits.

## Install selected skills

The [installation profile guide](INSTALL-PROFILES.md) is the canonical procedure for previewing, applying, verifying, and rolling back selected Codex/Kiro/Grok skills. It explains ownership checks, preserved customizations, resource additions, and source-path discovery. Agent registrations and standalone updater enrollment are separate from a disposable skills-only preview.

For an existing installation, [release-watch commands](CLI-REFERENCE.md#check-or-accept-installed-releases) describe checking, accepting, scheduling, and rollback. Scheduled runs auto-accept valid releases by default; use `--notify-only` for a check-only schedule. The [release guide](RELEASE-PACKAGING.md#installed-release-watch-contract) explains the saved-profile and legacy paths.

## Author or maintain capabilities

For an intentional capability addition or update, follow [UAC usage](UAC-USAGE.md). An authorized same-slug apply can land structurally ready state with `behavioral_pending`; independent promotion remains a separate result described in [Capability evaluation](CAPABILITY-EVALUATION.md).

For repository maintenance, run the following after canonical edits and completed generation, in order:

```bash
bin/capability-fabric build
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
```

Build writes generated packages and inspection views. Validation checks their contracts and records local evidence. Smoke probes available CLIs and configured discovery surfaces; missing or skipped runtime checks remain visible. These checks do not establish hosted CI, installation, or authenticated use.

The [CLI reference](CLI-REFERENCE.md) explains exact commands and paths. The [maintainer guide](MAINTAINER-HYGIENE.md) and [release guide](RELEASE-PACKAGING.md) cover delivery and publishing.
