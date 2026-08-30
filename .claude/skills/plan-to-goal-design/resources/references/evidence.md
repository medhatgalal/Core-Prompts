# Evidence and Research Contract

## Evidence Classes
- `FACT`: directly observed in the current repository, runtime, command output, or primary source
- `INFERENCE`: a conclusion supported by facts and paired with a falsifier
- `CONTRADICTION`: two claims cannot both control the packet; identify the authoritative current evidence
- `UNKNOWN`: missing evidence that affects scope, safety, ownership, or verification

## Local Research
Record exact repository identity before interpreting the plan. Read applicable instruction files, then trace the relevant behavior through entrypoints, callers, tests, build/CI configuration, generated outputs, and runtime or provider boundaries. File names from a plan are hypotheses until they exist in the current tree.

Record likely, owned, protected, generated, and out-of-scope paths separately. Generated paths are evidence or outputs, not edit targets, unless the generator itself is broken.

## External Research
Use current primary sources when the task depends on versioned APIs, host commands, standards, safety claims, or model-dependent behavior. Record:
- URL and title
- publisher or authors
- publication/update date when available
- retrieval date
- exact decision affected
- confirming and disconfirming evidence
- measured, documented, inferred, or heuristic status

Do not collect sources that do not change the packet. Do not turn a search snippet, unavailable page, or secondary repetition into a hard constraint.

## Completion Evidence
Static collection, configuration, local tests, hosted CI, merge, deployment, and live acceptance are separate facts. Match each requirement to evidence with the same scope. A narrow green command does not prove a broad outcome.

## Key Research
- Progress Mirage: https://arxiv.org/abs/2607.25152
- Verification Horizon: https://arxiv.org/abs/2606.26300
- Ledger execution state: https://arxiv.org/abs/2608.00808
- SpecBench: https://arxiv.org/html/2605.21384

These sources support explicit state and verification boundaries. They do not prove this capability's preferred prose range or behavioral superiority.
