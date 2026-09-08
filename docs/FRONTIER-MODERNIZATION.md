# Modernized improvement workflows

Supercharge retains its Swiss Army Knife roles: prompt improvement and execution,
first-principles reasoning, decomplecting, inversion, adversarial review, council
debate, contract review, grading, and plain-English catchup. Auto-Research runs
measured experiments. UAC remains exhaustive onboarding and uplift tooling.

## What changed for users

- Substantive Supercharge reviews use real independent subagents. A failed reviewer
  launch leaves review incomplete; simulated perspectives cannot replace it.
- Initial reviewers receive the task, criteria, evidence, and artifact without the
  author's preferred verdict or self-grade. Council rebuttals follow that first pass.
- `/ult` prints the improved prompt, then runs it within the requested authority.
  Draft-only requests and `/ult /full` do not execute the target task.
- `/basis` derives a sufficient design from outcomes, facts, constraints, and
  challenged assumptions. `/simple` removes coupling between independent concepts.
  `/invert` works backward from failure and examines whether missing evidence could
  have been observed.
- `/grade` retains Rubric, Iteration Ladder, Final Artifact, and Top 3 Remaining
  Gaps. Its default budget is up to ten actual candidate trials, independently
  graded. The best candidate survives rejected attempts; the first win alone does
  not end the search. A documented plateau and independent check can finish early.
- `/full` keeps the documented pass order, explicit `/basis` opt-in and `skip grade`.
  `/catchup` keeps its existing tables and visible verification in plain English.
- `/gaslight` remains explicit-only with thirteen selectable technique IDs. Claimed
  effects are hypotheses unless tested on the relevant task and model.
- The legacy global `/stop` is retired. `/stop-ult` and persistent ULT remain.

Canonical behavior is in [Supercharge](../ssot/engos-meta-supercharge.md) and its
declared resources; this page explains the changes rather than adding rules.

## Complete resources, explicit evidence

The entry contains routing and shared requirements. A `resource-map.json` selects
the complete dependencies for a module or stack. The bundled read-only helper can
assemble them:

```bash
python3 resources/scripts/load_module.py --route /grade --format text
python3 resources/scripts/load_module.py --route details --format json
```

Package checks show that files exist and match their source. Helper output shows
which bytes were assembled. Host request records or complete read-tool results show
which content was supplied. Independent evaluation shows whether behavior follows
that content. No self-written receipt or hash proves model comprehension.

Native skill hosts still need to execute the loader/read route and supply its full
output. Controlled evaluator requests can bind and inject resources explicitly;
this does not make an uninstrumented host mechanically enforce resource use.

## Measured exploration

For [Auto-Research](../ssot/engos-optimization-auto-research.md), distinguish the
original baseline, current best accepted candidate, and active trial. A trial may
change one thing or a coordinated set under a stated hypothesis. It executes against
a protected evaluator and scorecard; acceptance advances the incumbent, rejection
restores it, and the result is retained as evidence. Search continues after wins and
losses until the declared target, budget, plateau rule, or interruption.

Equal-quality simplicity or cost improvements can win when the objective allows
them. A plateau means no further improvement was found within this search; it is
not proof of global optimality. A diagnostic fix can finish earlier than an
explicit optimization request.

## Exhaustive UAC uplift

UAC diagnoses structure, style, ambiguity, contradictions, details, references,
outputs, boundaries, and preservation. It repairs the authoritative location and
reuses equivalent content instead of inserting generic executable stubs. Required
semantic repairs are explicit review work; structural heuristics cannot certify
semantic truth. [Reviewed modernization](UAC-USAGE.md#resource-aware-and-reviewed-modernization)
uses hash-bound requirement dispositions without rewriting historical baseline lineage.

## Model guidance maintenance

One [dated table](../sources/capability-resources/engos-meta-supercharge/references/model-guidance.md)
records relevant capabilities, prompting implications, sources, and evidence class.
One research-only monthly refresh checks for meaningful changes; the same workflow
can be invoked when a new model or revised practice is identified. Proposed changes
receive review, rather than silently changing skills or model selection.

## Verification scope

Deterministic tests, source review, actual host demonstrations, hosted CI, and formal
behavioral promotion are different evidence. A successful UAC apply remains
`behavioral_pending` without the independent protected promotion evidence described
in [Capability Evaluation](CAPABILITY-EVALUATION.md). No cross-model superiority is
inferred from better documentation, higher structural scores, or one demonstration.
