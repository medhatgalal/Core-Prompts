# Current Model Guidance

Last checked: 2026-09-08. This table records provider guidance, not local proof of skill efficacy or a model ranking. Read it when adapting an artifact or diagnosing model behavior; do not inject every row into every prompt. Recheck changing claims before relying on them for a new version.

| Model/version | Relevant capability or behavior | Prompting implication | Evidence and last checked |
| --- | --- | --- | --- |
| Fable 5.1 / Mythos 5.1 | Effort and resource use differ across versions; long work depends on continuity and tool context. | Test effort on the actual task; preserve decisions through compaction, support focused visual inspection, and correct observed behavior rather than copying all remedies. | [Provider guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1), 2026-09-08; provider guidance, locally unmeasured. |
| Sol 5.6 | Redundant scaffolding can be unnecessary; task outcomes, constraints, and useful tool context remain important. | Test removal of redundant instructions incrementally; retain substantive requirements, examples where helpful, and stopping conditions. | [Provider guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6), 2026-09-08; provider guidance, locally unmeasured. |
| Astra / GPT-6 | Strong instruction following makes conflicts and excessive process consequential. | Resolve precedence, preserve authorized scope, and make clarification and verification proportionate to the task. | [Provider guide](https://developers.openai.com/api/docs/guides/latest-model), 2026-09-08; provider guidance, locally unmeasured. |
| Grok 4.6 | Reasoning settings and agent tools are exposed by its runtime. | Test the actual model, effort, tools, and tasks; do not transfer another provider's preferred settings or assume future 4.6+ releases behave identically. | [Provider documentation](https://docs.x.ai/developers/grok-4-6), 2026-09-08; capability documentation, prompting implications are hypotheses. |

## One Refresh Workflow
Run a research-only refresh monthly, or when a newly available/selected model or updated official practice is identified. Use one workflow for both triggers. If the user has authorized scheduling, configure one host-supported monthly check; this resource does not itself create an automation. Do not browse on every skill invocation.

Read official version and prompting guidance, compare it with this table, and report only meaningful changes with exact model/version, source, checked date, expected consequence, and evidence class. Keep provider recommendations separate from locally demonstrated remedies. If unchanged, stay quiet unless a report was requested. Propose table edits and any narrowly affected skill edits for review; never silently rewrite skills, change model selection, or claim experiments were run. Failed retrieval preserves the dated row and labels it stale/unverified rather than manufacturing an update.

## Evaluation Before Adopting a Remedy
Use representative tasks plus a strong native baseline with the same context and tools. Record exact model/effort, prompt and resource identity, tool access, quality, cost, latency, and user intervention. Instruction deletion, targeted examples, tool repair, and leaving the prompt unchanged are all eligible interventions. General benchmarks motivate difficult tasks; they do not prove prompt-specific improvement.
