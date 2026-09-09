# Core-Prompts

Core-Prompts provides reusable skills for designing experiences, reviewing code, investigating systems, improving prompts, and delivering work. Use them in Codex, Gemini, Claude, Kiro, or Grok. This repository keeps their canonical source, generated packages, and release tooling aligned.

The current generated surfaces ship `28` skills across five supported CLIs and `11` agents on agent-capable surfaces. Start with a capability for your task; use UAC when authoring capabilities and repository tooling when maintaining the packages.

## Start with a real task

| Your task | Start here | Example ask and expected result |
| --- | --- | --- |
| Design or improve a report, web, desktop, or mobile experience | `engos-design-experience` | “Improve this comparison flow so I can choose confidently, preserve my draft, and understand what happened after saving.” Expect a rendered artifact, relevant alternatives, observed task checks, and clear limits. |
| Review a change before commit | `engos-quality-code-review` | “Review my staged changes for correctness, resource cleanup, concurrency, and API compatibility.” Expect evidence-based findings and merge guidance. |
| Understand a large subsystem without losing progress | `engos-memory-context-continuity` | “Investigate this subsystem and keep its context, todo, and insights current.” Expect durable task state under `~/.analyze-context/`; branch and worktree paths are metadata only. |
| Improve a prompt before using it | `engos-meta-supercharge` | “Supercharge /ult /full skip grade this prompt.” Expect an improved prompt and independent review without executing its task. |
| Turn a reviewed plan into a bounded goal | `engos-design-plan-to-goal` | “Compile this migration plan into a goal, specification, and verifier packet without starting execution.” Expect a researched packet and explicit verification limits. |
| Prepare an incident decision meeting | `engos-audit-opex-incident-review` | “Build today's Daily OpEx Digest against yesterday's snapshot.” Expect decisions, owner obligations, reconciled metrics, evidence gaps, and report paths. |
| Deliver an implementation with independent review gates | `engos-orchestration-batman` | “Batman: implement this correction through independent subagents, verification, docs, and authorized landing.” Expect a host-specific plan, review evidence, progress, and separate landing receipts. |
| Find or improve a repeatable agent loop | `loopy` | “Audit this loop and repair material weaknesses.” Expect a concise verdict and a bounded loop; running or publishing it remains a separate action. |

Use the full `engos-<category>-<skill-name>` name in native skill selection. The upstream-pinned `loopy` package keeps its own name. In Codex, start with `$engos-design-experience`; see [Getting started](docs/GETTING-STARTED.md#invoke-a-capability) for other surfaces.

[Copyable examples](docs/EXAMPLES.md) cover every skill. The [Skill Job Map](docs/SKILL-JOB-MAP.md) distinguishes neighboring capabilities, and the [generated catalog](docs/CAPABILITY-CATALOG.md) lists the emitted skill and agent surfaces.

## Design the whole experience

> Use `engos-design-experience` to improve this HTML report. Make the decision and its evidence easy to compare. Show meaningful alternatives where the structure is unsettled, then implement the selected direction and walk through the final result.

The capability covers composition, interaction, and connected behavior across reports and applications. It adapts to the existing product and platform, checks relevant API and state semantics, and uses failure probes when persistence or an unresolved action matters. A small correction can stay small. A browser simulation of a native flow does not establish native behavior; target-runtime checks remain explicit.

See the [report, application, native, and failure-probe examples](docs/EXAMPLES.md#engos-design-experience). For backend boundaries and migrations, use `engos-design-architecture`; for a slide deck and format exports, use `engos-content-dynamic-html-presentations`.

## Install or verify discovery

If the skills are already available in your host, use them directly. For a new installation, follow the [reviewed home-install quickstart](docs/quickstart.md) and [installation profiles](docs/INSTALL-PROFILES.md).

The selected Codex/Kiro/Grok profile installs skills to `.agents/skills`, `.kiro/skills`, and `.grok/skills` respectively. Generated repository packages remain intentional. Agent registration and application member rosters have their own discovery state; the [discovery guide](docs/INSTALL-PROFILES.md#discovery-and-member-registries) explains how to distinguish them.

## Author a capability with UAC

UAC inspects a source, proposes its canonical landing, and checks its quality before apply:

```bash
bin/uac plan /absolute/path/to/candidate
bin/uac judge /absolute/path/to/candidate
bin/uac apply /absolute/path/to/candidate --yes
```

Apply writes canonical repository state and regenerates surfaces. Deployment is separate. Follow the [UAC usage guide](docs/UAC-USAGE.md) and the [repository delivery workflow](.kiro/steering/repo-workflow.md) for an isolated change, same-slug updates, and paired-provider delivery.

A structurally accepted capability may ship with `behavioral_pending` during the advisory rollout. This does not establish behavioral promotion; the [evaluation guide](docs/CAPABILITY-EVALUATION.md) defines that separate evidence gate.

## Maintain the repository

Use Python 3.11 or later; Python 3.14 is preferred. After canonical changes, run generation and validation in order:

```bash
bin/capability-fabric build
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
```

[CLI reference](docs/CLI-REFERENCE.md) documents commands and their write effects. [Release packaging](docs/RELEASE-PACKAGING.md) covers comparison baselines, hosted checks, publishing, and installed release updates. [Maintainer hygiene](docs/MAINTAINER-HYGIENE.md) links the governing policy and review checks.

The [docs home](docs/README.md) routes the complete documentation set. Generated [release changes](docs/RELEASE-DELTA.md) and [status](docs/STATUS.md) are inspection snapshots; they do not establish the state of a user's installation.
