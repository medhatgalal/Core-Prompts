# Core-Prompts / Capability Fabric

Core-Prompts ships reusable skills for Codex, Gemini, Claude, Kiro, and Grok, with no shipped named-agent configurations. This repository is the canonical source, intake, build, validation, and release layer that keeps those shipped capabilities aligned.

Install or repair an existing setup with the current installer, even if it has no updater or receipts. It recognizes complete historical skill and agent packages, migrates their current identities, and preserves custom files. Your selected providers, surfaces, and capabilities persist across routine updates. See [installation and recovery](docs/INSTALL-PROFILES.md).

**Start by asking for the job:** “Supercharge this plan.” Use the installed skill as the normal entry point; the assistant arranges independent review when the capability requires it. You do not need to choose a second capability called an agent. If your host does not discover the skill, select its full name, such as `engos-meta-supercharge`.

The shipped setup is skills-only. Generic independent workers can apply these skills; future named-agent surfaces require your explicit approval. See [skills, agents, and prompts](docs/FAQ.md#what-is-the-difference-between-a-skill-an-agent-and-a-prompt) for the distinction and its limits. Explicit-only workflows such as Batman still require an explicit request.

Use this repository in this order:

1. installed capabilities first
2. UAC, the capability intake and uplift workflow, second
3. broader repo tooling third

If you are already using Core-Prompts in a CLI, start there. If you are importing a new capability family, go to UAC next. If you are rebuilding surfaces, validating state, deploying, or preparing release work, use the repo tooling after that.

The current generated surfaces ship `32` skills across all supported CLIs and `0` named-agent configurations. Capability Fabric metadata is advisory; explicit invocation follows the selected capability's operating contract.

First-party skills use the `engos-<category>-<skill-name>` namespace so Core-Prompts capabilities stay together in CLI and app autocomplete. The upstream-pinned Loopy package retains the single name `loopy`, without an alias package. The category identifies the primary job; the final segment identifies the capability. For example, use `engos-memory-context-continuity` for durable investigation state, `engos-quality-code-review` for diff review, and `engos-triage-my-inbox-chat-pulse` for Gmail and Chat triage.

Conversational `Supercharge /full` and stacked forms such as `supercharge /simple /invert /contract <task>` remain supported by `engos-meta-supercharge`. Use the full namespaced name for native skill selection; no separate short-name package or native menu alias is emitted. Ask `supercharge help` or `supercharge /help examples` for the bundled terminal guide; help does not execute examples. `/full` includes a budget of up to ten real, independently graded candidate trials unless you say `skip grade`; it never executes the target prompt. `/ult` prints the improved prompt and runs it within your authorized scope, while `/ult /full` reviews it without execution. `/stop-ult` still exits persistent ULT mode; the legacy global `/stop` command is retired. Detailed module instructions are loaded from bundled resources before use. See [modernization and evidence boundaries](docs/FRONTIER-MODERNIZATION.md).

Supercharge responds inline unless a file is requested. Requested Supercharge and Auto-Research deliverables use stable project paths and Git revision history; they do not require timestamped prompt archives.

For Git activity, ask `engos-audit-engineering-progress help` for usage and examples without starting a report. Its `eng-report run --json` pass preserves existing reports; see the [metrics-first example](docs/EXAMPLES.md#engos-audit-engineering-progress).

For review work, pick the capability by intent:

For a rough product or engineering idea, start with `engos-design-shaping`:
“Help us frame and shape this; here are our notes.” It coordinates framing,
AI-led or human-led research, independent review and verified output delivery.
You do not need to orchestrate its helpers. See the [guided Shape Up runbook](docs/engos-design-shaping.md)
for inputs, questions, teammate handoffs, resume and current pilot limitations.
Ask “Where are we, what is blocking us, and what do you need from me?” for an
as-of progress view. Accepted content, newer drafts and saved-target verification
remain distinct; a polished export is not an approved bet.
Ask it to check what already exists before proposing new components. Technical
shaping includes evidence-backed reuse or non-reuse decisions and conditionally
uses architecture, code-health and testing advice without requiring a full audit.

| Intent | Use | Boundary |
| --- | --- | --- |
| Review staged changes, a diff, or a commit before committing, pushing, merging, or releasing | `engos-quality-code-review` | Read-only review gate; covers correctness, scope, resource lifecycle, concurrency, operational readiness, API compatibility, and merge guidance |
| Implement selected reviewer comments from an existing PR/MR | `engos-delivery-address-code-review` | Mutating action workflow; edits only files tied to selected review feedback |

Antigravity CLI (`agy`) can install the same portable skills under `~/.gemini/config/skills` using `--cli agy`.

Codex and Gemini share installed skills under `~/.agents/skills`; Gemini settings
and agents remain under `~/.gemini`. See [installation and migration](docs/INSTALL-PROFILES.md)
for exact previews, preservation reports, and rollback.

## Installed Capabilities First

Start with the shipped capabilities when you want direct help on a real task.

### Full Skill Index

These are the currently shipped skills with a concrete starter ask for each one:

| Skill | Use it when you need to... | Starter ask | What good output looks like |
| --- | --- | --- | --- |
| `engos-design-shaping` | guide a rough idea through framing, evidence and a shaped pitch | "Help us frame and shape this from these notes; guide product and engineering through the missing decisions." | accepted stage, source-backed documents, scoped worker/reviewer handoffs and honest delivery status |
| `engos-design-frame-from-vague` | frame an idea without choosing its solution | "Frame this problem only; identify missing appetite and boundaries without inventing answers." | original intake, solution-free frame, attributable decisions and useful open questions |
| `engos-quality-shaping-gate` | assess a shaping stage or resumed handoff | "Check this stage against its actual evidence and tell us whether it can advance." | predicate-level verdict, current bindings, actionable holds and no invented approval |
| `engos-memory-context-continuity` | work through a broad repo investigation without losing context | "Use `engos-memory-context-continuity` to inspect this subsystem over several files and keep its context, todo, and insights files current until the work is complete." | one three-file task set under `~/.analyze-context/<project>/<task-id>/`, accumulated findings, checked progress, and a scoped next action; branch and worktree paths are metadata only |
| `engos-design-architecture` | design or review interfaces, boundaries, and migration safety | "Use `engos-design-architecture` to recommend the safest design for this capability layout." | options, tradeoffs, migration guidance, and a rollback-aware recommendation |
| `engos-optimization-auto-research` | improve a prompt, workflow, or system through experiments | "Use `engos-optimization-auto-research` to improve our review prompt so it catches more behavioral regressions without increasing noise." | goal contract, evaluation plan, experiments, and a winner only after evidence |
| `engos-orchestration-batman` | implement through subagent-driven development with blocking review gates | "Batman: verify this request, publish the Host-Fit Plan, then implement this shipped-defect correction through subagent-driven TDD, blocking milestone reviews, verification, docs, PR, authorized merge, release, install, and cleanup." | instruction-integrity result, host-fit decisions, independent subagent evidence, provenance-qualified red and mutation checks, milestone decisions, progress reports, and state-specific landing receipts |
| `engos-audit-code-health` | audit brownfield structural health without changing the repo | "Use `engos-audit-code-health` to audit this repo for LOC hotspots, god objects, coupling, dead code, and drift from this prior audit block." | verified structural findings, drift analysis, and slice-ready remediation |
| `engos-quality-code-review` | review staged changes, diffs, or commits before commit, push, merge, or release | "Use `engos-quality-code-review` to review my staged changes, including resource cleanup, concurrency, operational readiness, and API/schema compatibility." | evidence-based findings, scope risks, message-quality feedback, and merge readiness |
| `engos-delivery-address-code-review` | apply selected fixes for existing PR/MR reviewer comments | "Use `engos-delivery-address-code-review` to inspect the open review comments on this MR and address the selected fixes only." | comments found, selected fixes, changes applied, commit guidance, and follow-up review |
| `engos-delivery-diagram-contract-artifacts` | turn a shaped solution into durable Mermaid diagrams, API/contracts, and security ownership artifacts | "Use `engos-delivery-diagram-contract-artifacts` on this shaped pitch and produce the component, sequence, data-flow, contract, and security-owner bundle without inventing internals." | source-backed artifact manifest, Mermaid sources, contract/security tables, evidence ledger, no-gos, and completeness judgment |
| `engos-delivery-artifact-embed` | place the authored artifact bundle on an HTML, PR/MR, chat, Google Doc, or wiki surface | "Use `engos-delivery-artifact-embed` to put this shaping bundle into the HTML site and Google Doc, preserving the source identity and naming any human step." | target adapter, source-preserving placement receipt, visual verification, or an explicit blocker/human step |
| `engos-reconciliation-converge` | compare competing proposals and force one recommendation | "Use `engos-reconciliation-converge` to compare these rollout plans and recommend one." | overlap map, explicit conflicts, decision criteria, and one final recommendation |
| `engos-browser-demo-recorder` | automate polished demo recordings with Playwright scripts | "Use `engos-browser-demo-recorder` to create a Playwright demo of the agent feedback feature on our Swagger UI." | demo plan, complete Playwright script with recording enabled, run command, and output path |
| `engos-content-dynamic-html-presentations` | create polished standalone slide decks with optional PNG and PPTX delivery | "Use `engos-content-dynamic-html-presentations` to turn this quarterly review into interactive HTML, 1920×1080 PNGs, and an image-faithful PPTX." | narrative-first HTML deck, validated images, optional flattened PPTX, and explicit export evidence |
| `engos-quality-docs-review` | fix docs structure, drift, and explainability | "Use `engos-quality-docs-review` to tell me what belongs in `README.md` versus `docs/`, what drifted, and what to fix first." | doc placement, drift findings, rewrite targets, and review timing |
| `engos-audit-engineering-progress` | generate a git-derived engineering progress report | "Use `engos-audit-engineering-progress` to generate an HTML progress report for this repo since 2026-06-01." | deterministic git metrics, local or Drive report path, and narrative clearly tied to the data |
| `engos-audit-opex-incident-review` | audit an Operational Excellence incident estate against the prior snapshot | "Use `engos-audit-opex-incident-review` to build today's Daily OpEx Digest for Blocker and Critical incidents, compared with yesterday." | decision queue, owner obligations, reconciled metrics, progress and correction ledger, stalled cohorts, DPA tracker, all-open board, evidence caveats, and optional incident drill-downs |
| `engos-audit-feature-status` | audit a feature against its stated scope and proof sources | "Use `engos-audit-feature-status` to compare this feature's engos-audit-pitch-review, HLD, OAS, code, and tests, then tell me what is complete, what drifted, and what is blocking ship." | evidence-backed status tables, spec drift findings, gap analysis, and prioritized recommendations |
| `engos-quality-gitops-review` | judge branch, PR, merge, or release readiness | "Use `engos-quality-gitops-review` to tell me whether this branch is ready for PR and what blockers remain." | gate type, blockers, required companion reviews, and next actions |
| `engos-operations-ic-assistant` | keep an Incident Commander on-process with generic guidance by default and internal runbook mode only on request | "Use `engos-operations-ic-assistant` to track this incident, identify the current phase, and tell me the next required action." | mode, current phase, next action, status-update timer, and overdue or escalation flags |
| `engos-audit-pitch-review` | create, review, score, or improve Shape Up pitches | "Use `engos-audit-pitch-review` to review this Shape Up engos-audit-pitch-review for appetite, risks, and betting readiness." | shaped problem, appetite fit, risks, score, and concrete improvement guidance |
| `engos-design-plan-to-goal` | turn a researched implementation plan into a bounded goal packet | "Use `engos-design-plan-to-goal` to inspect this migration plan and repo, then produce a compact goal, durable spec, bounded anchor, per-criterion flip fixtures, and a sealed verifier packet." | research receipt, goal/spec/baseline packet, criterion-flip results, verifier trust, honest terminal state, and a host-correct launch command only when supported |
| `engos-triage-my-inbox-chat-pulse` | triage Gmail and Google Chat noise into clear priorities | "Use `engos-triage-my-inbox-chat-pulse` to tell me what needs my attention across Gmail and Google Chat, then propose the next actions without sending anything." | priority-classified comms table, source summary, and proposed next actions for the hot items |
| `engos-delivery-resolve-conflict` | analyze a merge conflict or competing edits | "Use `engos-delivery-resolve-conflict` to compare these conflicting branch edits and tell me what should survive." | conflict map, additive merge opportunities, explicit tradeoffs, and a recommended resolution |
| `engos-meta-supercharge` | harden a rough prompt, plan, proposal, first-principles audit, or adversarial decision before execution | "Use `engos-meta-supercharge /adversarial /debate /deep` to run a Bull/Bear/Decider debate on this engos-design-architecture decision, then list flip conditions." | sharper framing, stronger constraints, execution plan, failure-mode coverage, `/basis` accounting, or Bull/Bear/Decider debate when requested |
| `engos-quality-testing-review` | decide what to test first and what edge cases matter | "Use `engos-quality-testing-review` to identify the highest-value tests and edge cases for this change." | prioritized tests, edge cases, and coverage gaps |
| `engos-memory-threader` | export a conversation or create a durable handoff | "Use `engos-memory-threader` to turn this chat into a reusable handoff for another engineer or model." | durable summary, preserved decisions, and next-step continuity |
| `engos-meta-uac-import` | import and uplift new capability source into canonical state | "Use `engos-meta-uac-import` to inspect this external prompt family and tell me how it should land into SSOT before apply." | landing shape, classification, overlap concerns, and the next UAC step |
| `engos-audit-weekly-intel` | build a weekly report from multiple sources | "Use `engos-audit-weekly-intel` to produce a weekly status report from these sources." | executive summary, technical appendix, and fact-check audit |

Use `engos-audit-opex-incident-review briefing <ticket...>` for complete meeting preparation, including linked fixes, verified recurrence, customer counts, and coaching for every confirmed selected incident. OpEx incident drill-downs supplied in the normalized snapshot appear in both HTML and Markdown. They retain facts, risk, Five Whys, preventive action, talking points, and follow-up questions.

### High-Value Skill Examples

| Capability | Start with it when you need to... | Example ask | What good output looks like |
| --- | --- | --- | --- |
| `engos-optimization-auto-research` | improve a prompt, workflow, or system through bounded experiments | "Use `engos-optimization-auto-research` to improve our review prompt so it catches more behavioral regressions without increasing noise." | a goal contract, experiment plan, evaluation criteria, and a winner only after evidence |
| `engos-orchestration-batman` | deliver a contract, metric, safety path, or shipped-defect correction through independent implementation subagents | "Batman: verify instruction integrity, select the live host's language and test tools, then implement this safety path with independent subagents and report initial, stage, blocker, and 15-minute progress." | one controller-owned flow, a Host-Fit Plan, bounded subagent briefs, all applicable blocking milestone gates, independent evidence, and authorized landing |
| `engos-audit-code-health` | find structural brownfield risk without mutating code | "Use `engos-audit-code-health` to audit this repo for LOC hotspots, god objects, coupling, likely dead code, and drift." | metric-backed findings, prior-claim verification when provided, and slice-ready remediation |
| `engos-meta-supercharge` | harden a rough prompt, plan, proposal, first-principles audit, or adversarial decision before execution | "Use `engos-meta-supercharge /adversarial /debate` to compare the strongest case for and against this rollout plan before we choose." | sharper framing, stronger constraints, clearer sequencing, first-principles accounting, and debate-mode decision pressure when requested |
| `engos-reconciliation-converge` | compare competing options and force one recommendation | "Use `engos-reconciliation-converge` to compare these rollout plans and recommend one." | explicit conflicts, common comparison criteria, and one final recommendation |
| `engos-quality-docs-review` | fix docs structure, drift, and explainability | "Use `engos-quality-docs-review` to tell me what belongs in `README.md` versus `docs/`, what drifted, and what to fix first." | placement decisions, drift findings, rewrite guidance, and review timing |
| `engos-quality-gitops-review` | judge branch, PR, merge, or release readiness | "Use `engos-quality-gitops-review` to tell me whether this branch is ready for PR and what blockers remain." | gate type, blockers, companion reviews, and exact next actions |
| `engos-quality-testing-review` | decide what to test first and what edge cases matter | "Use `engos-quality-testing-review` to identify the highest-value tests and edge cases for this change." | prioritized test ideas, edge cases, and coverage gaps |
| `engos-design-architecture` | review interfaces, boundaries, and migration safety | "Use `engos-design-architecture` to recommend the safest design for this capability layout." | tradeoffs, boundary decisions, migration thinking, and rollback-aware recommendations |

### Independent Workers

Use the same skill in the main session or supply it and its required resources to a fresh independent worker. No matching named-agent package is required. If the host cannot provide the independent review a capability requires, report the limitation and stop the dependent gate.

Batman remains explicitly invoked. It checks the request and live host, preserves controller/implementer/reviewer separation, and reports local, hosted, release, and installation evidence separately. See [the delivery contract](docs/GETTING-STARTED.md#how-batman-starts-and-resolves-companions).

### If You Only Try Three Things

1. Use `engos-quality-docs-review` on a docs surface that feels bloated or unclear.
2. Use `engos-quality-gitops-review` on your current branch before you open a PR.
3. Use `engos-meta-supercharge /basis` to audit irreducible work, or `engos-meta-supercharge /adversarial /debate /deep` to stress-test a high-stakes decision, then use `engos-optimization-auto-research` when a measured experiment is needed.

Long-running `engos-memory-context-continuity` tasks now consolidate context and insights at a milestone or size threshold, keeping verified current state first and reporting before/after counts. See the [active-task example](docs/EXAMPLES.md#consolidate-an-active-task).

### Scenario Starters

Use these as copy-paste starting points when you want to exercise the higher-leverage skills:

| Scenario | Ask |
| --- | --- |
| Evidence-gated delivery | "Batman: verify instruction integrity, publish the Host-Fit Plan, then implement this shipped-defect correction through independent subagents. Show provenance-qualified red and mutation evidence, pass every applicable milestone review, distinguish offline checks from hosted or live proof, report progress against the written plan, and land only with current CI and explicit authority." |
| First-principles release audit | "Use `engos-meta-supercharge /basis` to audit our release process. Find irreducible steps, stale ceremony, actual-to-minimum ratio, and what should be automated or deleted." |
| Adversarial release debate | "Use `engos-meta-supercharge /adversarial /debate /deep` to run a Bull/Bear/Decider debate on this release plan. Include risks, mitigants, flip conditions, and the evidence that would change the decision." |
| Release plan hardening | "Use `engos-meta-supercharge /full` to harden the v1.9.2 release plan before I tag it. Include risks, failure modes, verification gates, and rollback." |
| Measured prompt or skill improvement | "Use `engos-optimization-auto-research` to compare the old autosearch prompt behavior against auto-research v2.0 on five representative improvement tasks, with a scorecard and promotion packet." |
| Release strategy decision | "Use `engos-reconciliation-converge /mcda /conflicts` to compare three release strategies: tag from this branch, merge then tag from main, or publish package-only. Recommend one and reject the others explicitly." |
| Release gate review | "Use `engos-quality-gitops-review` to judge whether this branch is ready for PR, CI, merge, tag, and release. Include exact blockers and commands." |
| Release docs drift check | "Use `engos-quality-docs-review` to review README, Getting Started, CLI reference, release delta, and changelog for v1.9.2 drift before release." |

### Where The Deeper Examples Live

If you want fuller examples for the shipped skills highlighted in this README, with "use when", concrete asks, expected outputs, and a good follow-up ask, go to [docs/EXAMPLES.md](docs/EXAMPLES.md). Treat this README and [docs/CAPABILITY-CATALOG.md](docs/CAPABILITY-CATALOG.md) as the authoritative full index of everything currently shipped.

### Sample Transcript: Docs Review First

This is the shape of a real ask a user might make:

```text
User:
Use `engos-quality-docs-review` to review our onboarding docs, identify drift, tell me what belongs in README.md versus docs/, and recommend the smallest rewrite that restores clarity.

Good response shape:
- Current State
- What Belongs Where
- Drift Findings
- Recommended Changes
- Review Timing
- Open Risks
```

This is often the best first move when the problem is not "we need more docs" but "we no longer know which docs are trustworthy."

### Sample Transcript: GitOps Review Before PR

```text
User:
Use `engos-quality-gitops-review` to tell me whether this branch is ready for PR and what blockers remain.

Good response shape:
- Current State
- Gate Type
- Findings
- Required Companion Reviews
- Recommended Commands or Actions
- Release / Merge Readiness
- Open Risks
```

This is often the best first move when you think the work is done but want an actual gate instead of a vague opinion.

### Sample Transcript: Improve A Weak Workflow

```text
User:
Use `engos-optimization-auto-research` to improve our review workflow so it catches more behavioral regressions without increasing false positives.

Good response shape:
- Goal Contract
- Evaluation Criteria
- Candidate Variants
- Minimum Experiment Set
- Promotion Decision Only After Evidence
```

This is often the best first move when the problem is "our process is weak" rather than "we already know the right replacement."

### Sample Transcript: Pick The Right Capability First

```text
User:
I am not sure whether this is a docs problem, a branch-readiness problem, or just a sequencing problem. Tell me which capability to use first and why.

Good response shape:
- Best first capability
- Why it is first
- What not to use yet
- The next capability to use after the first answer lands
```

This is the right starting move when the user is uncertain which installed capability should lead.

## UAC Second

UAC reports `structural_ready`, not behavioral promotion. It runs deterministic `instruction_clarity.v1` lint and can emit an `EvalImpactPlan.v1`. Auto-Research and `bin/capability-eval` are the behavioral-proof path. Live comparisons are explicit and fail closed; promotion additionally requires a separately operated protected evaluator with conforming adapters, protected credentials and runner identities, external sealed data, qualified judges, reproduction, and signed evidence.

```bash
bin/uac audit --clarity on
bin/uac plan ./candidate.md --emit-impact-plan
bin/uac judge ./candidate.md
bin/capability-eval compile --skill engos-quality-code-review
bin/capability-eval compare --skill engos-quality-code-review --candidate ./candidate.md --profile static
```

Normal CI uses only the zero-token `static` profile. The Code Review pilot validates seeded lifecycle defects and matched safe controls without relying on user telemetry. A structurally applied candidate stays `behavioral_pending` until UAC accepts an independent, current `PromotionVerdict.v2` with `status: promote`. `PromotionVerdict.v1` remains readable for historical evidence but cannot authorize promotion. Missing credentials, adapter conformance, sealed data, judge qualification, receipts, or reproduction returns `inconclusive`, never an inferred pass. See [Capability evaluation](docs/CAPABILITY-EVALUATION.md#from-behavioral_pending-to-promote) for the two-stage trust prerequisite and finalization command.

In plain English: this release adds the checklist, contracts, static controls, and cost brakes. It does not claim that Google-style rewriting, `engos-meta-instruction-editor`, UAC rewrites, or any other skill change has already beaten its baseline in live model trials.

Use UAC, the capability intake and uplift workflow, when adding or changing canonical capability behavior. Existing-skill improvements use the [same-slug update flow](docs/UAC-USAGE.md#update-an-existing-capability).

Do not start with UAC if your goal is just to use what is already installed. Start with an installed skill for that.

Use UAC when you need to:

- inspect how an external prompt or prompt family would land in this repo
- improve an existing skill or agent without automatically expanding its surfaces
- package new reusable workflows as skills; require your explicit approval and independent execution-need review before adding any agent surface
- benchmark a candidate before it mutates canonical repo state
- write canonical SSOT, descriptor, and baseline state after a successful review

### Practical UAC Flow

```bash
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
bin/uac apply /absolute/path/to/family-folder --yes
```

What each step is for:

- `plan`: show the proposed landing shape without writing repo state
- `judge`: run the quality loop and report structural readiness, revision needs, or blockers without writing repo state
- `apply`: write canonical repo state, then rebuild and validate

Typical UAC examples:

- local import planning:

```bash
bin/uac plan /absolute/path/to/prompt-family
```

- GitHub source planning:

```bash
bin/uac plan https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/architecture
```

- benchmark before landing:

```bash
bin/uac judge /absolute/path/to/prompt-family --quality-profile architecture
```

Use [docs/UAC-USAGE.md](docs/UAC-USAGE.md) for the full intake and uplift guide.

If `judge` finds a candidate is structurally close to ready but still needs bounded behavioral proof, route that proof step to `engos-optimization-auto-research` instead of treating structural quality alone as evidence.

### Sample Transcript: UAC Planning

```text
User:
I found a strong external prompt family. Use `engos-meta-uac-import` to inspect it and tell me how it should land into SSOT before apply.

Good response shape:
- source summary
- proposed capability type
- proposed slug and landing targets
- overlap or conflict concerns
- recommended next UAC step
```

## Repo Tooling Third

Use the broader repo tooling when you need to verify, rebuild, deploy, package, or release what Core-Prompts emits.

### Fast Verification Loop

```bash
bin/capability-fabric build
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
```

What this proves:

- `build` regenerates skills, agents, bundled resources, and generated user views from canonical repo state
- `validate --strict` checks generated surfaces, manifests, and contract integrity
- `smoke-clis.py` probes local vendor CLIs and expected surface visibility where supported

### Install Or Repair

From a trusted current release or verified checkout, preview your home installation:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --cli kiro --repair --dry-run > /tmp/core-prompts-install-plan.json
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --apply-plan /tmp/core-prompts-install-plan.json
```

Review the JSON before applying. The shipped setup contains skills only. Repair
recognizes historical skills and agents without requiring an old updater and plans
owned agent retirements with the same capability’s skill as successor. Customized
or unowned packages are preserved and reported as incomplete migration.
`--with-agents` remains compatible but selects only emitted agents (currently none);
it cannot authorize creating an agent surface.
Use `--cli all` for initial provider discovery or omit it to keep saved selection.

### Installed Release Watch

Installation supplies `~/.core-prompts-updater/` and `~/update_core_prompts.sh`.
Existing schedules are preserved; creating one is a separate choice.

```bash
~/update_core_prompts.sh --check-release
~/update_core_prompts.sh --accept-release
~/update_core_prompts.sh --list-snapshots
```

Checking never installs. Scheduled runs auto-accept valid releases by default;
`--schedule-daily HH:MM --notify-only` disables automatic release acceptance;
routine sync of the existing bundle still runs. New-engine
updates use the saved installation and verified release mirror. Preserved conflicts
return exit `2`; runtime freshness alone does not prove every package migrated.
[Installation and recovery](docs/INSTALL-PROFILES.md) explains older-updater bridge
limits, explicit repair, rollback, and separate native CLI verification.

## Generated Inspection Views

Yes, [docs/CAPABILITY-CATALOG.md](docs/CAPABILITY-CATALOG.md) and [docs/RELEASE-DELTA.md](docs/RELEASE-DELTA.md) still serve a purpose, but they are not the first-stop docs.

Use them like this:

- [docs/CAPABILITY-CATALOG.md](docs/CAPABILITY-CATALOG.md): generated inventory and lookup aid for what ships, where it lands, and which surfaces exist now
- [docs/RELEASE-DELTA.md](docs/RELEASE-DELTA.md): generated release-review aid for what changed versus the previous manifest
- [docs/STATUS.md](docs/STATUS.md): generated health snapshot for packaged output inspection

They help maintainers, release reviewers, and packaged users answer "what ships," "what changed," and "is the build healthy" without reading raw manifests or generated directories. They should stay secondary to real usage docs.

## What Ships

- canonical authored source in [`ssot/`](ssot/)
- preserved strongest baselines in [`sources/ssot-baselines/`](sources/ssot-baselines/)
- machine-readable descriptors in [`.meta/capabilities/`](.meta/capabilities/)
- generated surfaces under [`.codex/`](.codex/), [`.gemini/`](.gemini/), [`.claude/`](.claude/), and [`.kiro/`](.kiro/)
- generated user-facing views in [docs/CAPABILITY-CATALOG.md](docs/CAPABILITY-CATALOG.md), [docs/RELEASE-DELTA.md](docs/RELEASE-DELTA.md), and [docs/STATUS.md](docs/STATUS.md)

## Documentation Map

Use the docs in the same order as the product model:

1. [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md): installed capabilities first, then UAC, then repo verification
2. [docs/EXAMPLES.md](docs/EXAMPLES.md): deeper scenario-style asks for current capabilities and maintainers
3. [docs/UAC-USAGE.md](docs/UAC-USAGE.md): intake, uplift, plan, judge, and apply
4. [docs/SKILL-JOB-MAP.md](docs/SKILL-JOB-MAP.md): plain-English purpose, boundaries, neighbors, and portfolio recommendation for every skill
5. [docs/CAPABILITY-EVALUATION.md](docs/CAPABILITY-EVALUATION.md): goal contracts, topologies, selective proof, budgets, and promotion
6. [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md): exact commands, paths, generated surfaces, and deploy behavior
7. [docs/MAINTAINER-HYGIENE.md](docs/MAINTAINER-HYGIENE.md): human maintainer guide and review checklist

## Maintainer Fast Path

When you are intentionally working on canonical capability source, validation, or release behavior:

```bash
bin/uac --help
bin/capability-fabric --help
```

Then go to:

- [docs/UAC-USAGE.md](docs/UAC-USAGE.md)
- [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md)
- [docs/RELEASE-PACKAGING.md](docs/RELEASE-PACKAGING.md)
- [docs/MAINTAINER-HYGIENE.md](docs/MAINTAINER-HYGIENE.md)

## Selected local skill targets

Choose Codex, Kiro, and Grok with an explicit skills-only profile. Codex skills install
under `.agents/skills`; Grok gets native `.grok/skills` packages. Preview the exact
write set and preserve unknown or customized copies before applying. See
[installation profiles and rollback](docs/INSTALL-PROFILES.md).

### Loopy: bounded agent loops

Use `$loopy` in Codex or `/loopy` in Kiro and Grok to find, audit, craft, run, or
debrief a loop. For example: “Use Loopy to audit this loop and repair only material
weaknesses.” Expect a concise verdict and a minimally repaired loop; execution,
scheduling, and publication retain their separate authorization boundaries.

Routine updates automatically remove identified retired Core-Prompts agents,
including locally modified copies, while retaining skills and third-party agents
such as Kiro Crew. See [installation cleanup](docs/INSTALL-PROFILES.md#automatic-agent-cleanup-on-update).
