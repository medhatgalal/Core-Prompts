# Core-Prompts / Capability Fabric

Core-Prompts ships installed skills and advisory agents you use directly in Codex, Gemini, Claude, and Kiro. This repository is the canonical source, intake, build, validation, and release layer that keeps those shipped capabilities aligned.

The right mental model is simple:

1. installed capabilities first
2. UAC, the capability intake and uplift workflow, second
3. broader repo tooling third

If you are already using Core-Prompts in a CLI, start there. If you are importing a new capability family, go to UAC next. If you are rebuilding surfaces, validating state, deploying, or preparing release work, use the repo tooling after that.

The current generated surfaces ship `14` skills across all supported CLIs and `8` advisory agents on agent-capable surfaces.

## Installed Capabilities First

Start with the shipped capabilities when you want direct help on a real task.

### Full Skill Index

These are the currently shipped skills with a concrete starter ask for each one:

| Skill | Use it when you need to... | Starter ask | What good output looks like |
| --- | --- | --- | --- |
| `analyze-context` | work through a broad repo investigation without losing context | "Use `analyze-context` to inspect this subsystem over several files and keep a durable analysis trail before you recommend changes." | file map, durable findings trail, unresolved questions, and a scoped change plan |
| `architecture` | design or review interfaces, boundaries, and migration safety | "Use `architecture` to recommend the safest design for this capability layout." | options, tradeoffs, migration guidance, and a rollback-aware recommendation |
| `autosearch` | improve a prompt, workflow, or system through experiments | "Use `autosearch` to improve our review prompt so it catches more behavioral regressions without increasing noise." | goal contract, evaluation plan, experiments, and a winner only after evidence |
| `code-review` | review a commit for scope, message quality, and over-engineering | "Use `code-review` to review the latest commit for scope creep, risky changes, and weak commit messaging." | findings first, scope risks, commit-quality feedback, and residual questions |
| `converge` | compare competing proposals and force one recommendation | "Use `converge` to compare these rollout plans and recommend one." | overlap map, explicit conflicts, decision criteria, and one final recommendation |
| `docs-review-expert` | fix docs structure, drift, and explainability | "Use `docs-review-expert` to tell me what belongs in `README.md` versus `docs/`, what drifted, and what to fix first." | doc placement, drift findings, rewrite targets, and review timing |
| `gitops-review` | judge branch, PR, merge, or release readiness | "Use `gitops-review` to tell me whether this branch is ready for PR and what blockers remain." | gate type, blockers, required companion reviews, and next actions |
| `mentor` | get senior sequencing and workflow guidance | "Use `mentor` to tell me the next reversible move on this branch." | the next move, why it is next, and what not to mix in |
| `resolve-conflict` | analyze a merge conflict or competing edits | "Use `resolve-conflict` to compare these conflicting branch edits and tell me what should survive." | conflict map, additive merge opportunities, explicit tradeoffs, and a recommended resolution |
| `supercharge` | harden a rough prompt, plan, or proposal before execution | "Use `supercharge` to turn this rough feature brief into an implementation plan with tradeoffs and failure modes." | sharper framing, stronger constraints, execution plan, and failure-mode coverage |
| `testing` | decide what to test first and what edge cases matter | "Use `testing` to identify the highest-value tests and edge cases for this change." | prioritized tests, edge cases, and coverage gaps |
| `threader` | export a conversation or create a durable handoff | "Use `threader` to turn this chat into a reusable handoff for another engineer or model." | durable summary, preserved decisions, and next-step continuity |
| `uac-import` | import and uplift new capability source into canonical state | "Use `uac-import` to inspect this external prompt family and tell me how it should land into SSOT before apply." | landing shape, classification, overlap concerns, and the next UAC step |
| `weekly-intel` | build a weekly report from multiple sources | "Use `weekly-intel` to produce a weekly status report from these sources." | executive summary, technical appendix, and fact-check audit |

### High-Value Skill Examples

| Capability | Start with it when you need to... | Example ask | What good output looks like |
| --- | --- | --- | --- |
| `autosearch` | improve a prompt, workflow, or system through bounded experiments | "Use `autosearch` to improve our review prompt so it catches more behavioral regressions without increasing noise." | a goal contract, experiment plan, evaluation criteria, and a winner only after evidence |
| `supercharge` | harden a rough prompt, plan, or proposal before execution | "Use `supercharge` to turn this rough feature brief into an implementation plan with tradeoffs and failure modes." | sharper framing, stronger constraints, clearer sequencing, and a more executable prompt or plan |
| `converge` | compare competing options and force one recommendation | "Use `converge` to compare these rollout plans and recommend one." | explicit conflicts, common comparison criteria, and one final recommendation |
| `docs-review-expert` | fix docs structure, drift, and explainability | "Use `docs-review-expert` to tell me what belongs in `README.md` versus `docs/`, what drifted, and what to fix first." | placement decisions, drift findings, rewrite guidance, and review timing |
| `gitops-review` | judge branch, PR, merge, or release readiness | "Use `gitops-review` to tell me whether this branch is ready for PR and what blockers remain." | gate type, blockers, companion reviews, and exact next actions |
| `testing` | decide what to test first and what edge cases matter | "Use `testing` to identify the highest-value tests and edge cases for this change." | prioritized test ideas, edge cases, and coverage gaps |
| `architecture` | review interfaces, boundaries, and migration safety | "Use `architecture` to recommend the safest design for this capability layout." | tradeoffs, boundary decisions, migration thinking, and rollback-aware recommendations |

### Advisory Agents Available Now

These current advisory agents are emitted by the repo and available on agent-capable surfaces:

| Agent | Use it for | Example ask | What good output looks like |
| --- | --- | --- | --- |
| `mentor` | next-step guidance and risk-aware sequencing | "Use `mentor` to tell me the next reversible move on this branch." | pragmatic step order, scope control, and risk-aware sequencing |
| `docs-review-expert` | documentation IA, drift review, and release-facing docs checks | "Use `docs-review-expert` to review our onboarding docs for drift and weak entrypoints." | concrete doc findings and rewrite targets |
| `gitops-review` | repo hygiene, CI, merge, and release gates | "Use `gitops-review` to judge whether we are ready to merge and release." | a go or no-go recommendation with evidence and next actions |
| `autosearch` | experiment-driven improvement loops | "Use `autosearch` to improve this workflow and prove which variant wins." | bounded experiments, evaluation, and promotion guidance |
| `supercharge` | plan or prompt hardening before execution | "Use `supercharge` to tighten this operating prompt before we ship it." | stronger prompt structure and clearer failure handling |
| `converge` | synthesis across competing proposals | "Use `converge` to synthesize these competing proposals into one decision." | overlap map, decision logic, and one coherent recommendation |
| `architecture` | architecture review and migration-safe design | "Use `architecture` to review this interface change for rollback risk." | architecture findings and a defensible direction |
| `weekly-intel` | multi-source weekly reporting | "Use `weekly-intel` to produce a weekly status report from these sources." | executive summary, technical appendix, and fact-check audit |

### If You Only Try Three Things

1. Use `docs-review-expert` on a docs surface that feels bloated or unclear.
2. Use `gitops-review` on your current branch before you open a PR.
3. Use `supercharge` or `autosearch` on a prompt or workflow you know is underperforming.

### Where The Deeper Examples Live

If you want fuller examples for every shipped skill, with "use when", concrete asks, expected outputs, and a good follow-up ask, go to [docs/EXAMPLES.md](docs/EXAMPLES.md). That file now covers all 14 currently shipped skills.

### Sample Transcript: Docs Review First

This is the shape of a real ask a user might make:

```text
User:
Use `docs-review-expert` to review our onboarding docs, identify drift, tell me what belongs in README.md versus docs/, and recommend the smallest rewrite that restores clarity.

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
Use `gitops-review` to tell me whether this branch is ready for PR and what blockers remain.

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
Use `autosearch` to improve our review workflow so it catches more behavioral regressions without increasing false positives.

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

Use UAC, the capability intake and uplift workflow, when you are bringing new prompt-like source into canonical Core-Prompts state.

Do not start with UAC if your goal is just to use what is already installed. Start with installed skills and agents for that.

Use UAC when you need to:

- inspect how an external prompt or prompt family would land in this repo
- decide whether the source should become a skill, an agent, or manual review
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
- `judge`: run the quality loop and produce a ship or block decision without writing repo state
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

If `judge` finds a candidate is structurally close to ready but still needs bounded behavioral proof, route that proof step to `autosearch` instead of treating structural quality alone as evidence.

### Sample Transcript: UAC Planning

```text
User:
I found a strong external prompt family. Use `uac-import` to inspect it and tell me how it should land into SSOT before apply.

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

### Deploy Dry Run

```bash
bin/capability-fabric deploy --dry-run --cli all
```

Use deploy after review when you want generated surfaces copied to a target root. Deploy is copy-only. It does not classify sources and it does not mutate canonical SSOT.

## Generated Inspection Views

Yes, [docs/CAPABILITY-CATALOG.md](docs/CAPABILITY-CATALOG.md) and [docs/RELEASE-DELTA.md](docs/RELEASE-DELTA.md) still serve a purpose, but they are not the first-stop docs.

Use them like this:

- [docs/CAPABILITY-CATALOG.md](docs/CAPABILITY-CATALOG.md): generated inventory and lookup aid for what ships, where it lands, and which surfaces exist now
- [docs/RELEASE-DELTA.md](docs/RELEASE-DELTA.md): generated release-review aid for what changed versus the previous manifest
- [docs/STATUS.md](docs/STATUS.md): generated health snapshot for packaged output inspection

They help maintainers, release reviewers, and packaged users answer "what ships," "what changed," and "is the build healthy" without reading raw manifests or generated directories. They should stay secondary to real usage docs.

## What Ships

- canonical authored source in [`ssot/`](/Users/medhat.galal/Desktop/Core-Prompts/ssot)
- preserved strongest baselines in [`sources/ssot-baselines/`](/Users/medhat.galal/Desktop/Core-Prompts/sources/ssot-baselines)
- machine-readable descriptors in [`.meta/capabilities/`](/Users/medhat.galal/Desktop/Core-Prompts/.meta/capabilities)
- generated surfaces under [`.codex/`](/Users/medhat.galal/Desktop/Core-Prompts/.codex), [`.gemini/`](/Users/medhat.galal/Desktop/Core-Prompts/.gemini), [`.claude/`](/Users/medhat.galal/Desktop/Core-Prompts/.claude), and [`.kiro/`](/Users/medhat.galal/Desktop/Core-Prompts/.kiro)
- generated user-facing views in [docs/CAPABILITY-CATALOG.md](/Users/medhat.galal/Desktop/Core-Prompts/docs/CAPABILITY-CATALOG.md), [docs/RELEASE-DELTA.md](/Users/medhat.galal/Desktop/Core-Prompts/docs/RELEASE-DELTA.md), and [docs/STATUS.md](/Users/medhat.galal/Desktop/Core-Prompts/docs/STATUS.md)

## Documentation Map

Use the docs in the same order as the product model:

1. [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md): installed capabilities first, then UAC, then repo verification
2. [docs/EXAMPLES.md](docs/EXAMPLES.md): deeper scenario-style asks for current capabilities and maintainers
3. [docs/UAC-USAGE.md](docs/UAC-USAGE.md): intake, uplift, plan, judge, and apply
4. [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md): exact commands, paths, generated surfaces, and deploy behavior
5. [docs/MAINTAINER-HYGIENE.md](docs/MAINTAINER-HYGIENE.md): human maintainer guide and review checklist

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
