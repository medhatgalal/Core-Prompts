# Skill-first Supercharge pilot

## Lineage and immutable scope

User-approved S3 implementation in task `01a0a475-49f8-7900-9d50-9782b47545c5`, based on verified main `55f9ed0de75ac3d62afb5d3756cac81915e7a003`. The target is provider-specific Supercharge adapters; no other agents may be retired by extrapolation. The original unchanged named route is A; generic independent worker with identical complete skill/resources is B. Grok has no repository named A and its comparison is inapplicable.

## Budget and stop

At most 60 minutes end-to-end after the explicit `start` command, including setup, waiting, coordination, calls, and synthesis. Setup allows 2 minutes; Codex, Claude, Gemini, Kiro, Grok each allow at most 10 minutes; synthesis allows 8 minutes. Run providers in that order. Release unused allowances; do not wait to fill them or transfer them. The task collector opens each provider's nonrenewable window at its first probe and enforces the overall deadline. The controller accounts for setup and synthesis. Stop new work at any deadline and kill each owned local process group immediately. Remote cancellation and complete usage accounting must be verified separately before admitting model calls.

## Frozen evaluation

`fixtures.json` binds cases, ordering, repetitions, protected behavior, and all admission gates. `preparation.json` hashes the actual fixture, collector, and existing adapter registry before live diagnostics. The live controller must additionally bind actual provider version, executable, native route, model/shared settings, prompt bytes, complete resource bytes, and starting state. Baseline A must remain unchanged, including its failures. A repaired coordinator is a future treatment.

Preflight must demonstrate positive and deliberately missing required-resource observations and permitted/blocked harmless disposable-fixture actions through the actual collection/scoring path. An absent trace is not a successful block. A claimed receipt is not delivery. Only native evidence admits model work; help output only identifies candidates. Registry unavailability establishes a limitation of that collector, not absence of native provider capability.

After successful native admission: direct control; independent review A/B then B/A; full multi-review A/B then B/A; help; conflicting terminal requests. Supply the complete Supercharge contracts unchanged even if they cannot fit the allowance. Blind route labels when judging. Record unfinished/crashed/timed-out work and native tokens, never zero tokens for unknown usage.

## Acceptance and disposition

Require both repetitions of both delegated cases, protected behaviors, actual negative controls/native boundaries, migration tests, no additional corrections, and a measured reduction in discovery or owned packages. Both candidate token and elapsed medians must be no more than 1.10 times baseline for each delegated case. Missing metrics, unsupported comparison, incomplete cases, or any gate failure means retain. Planning judgments and offline safety tests cannot promote a runtime adapter.

## Current tooling boundary and commands

The task-local `pilot.py` only collects non-model version/help admission diagnostics. It does not implement a new native model adapter or weaken existing disabled adapters. Current CLI help/probe evidence must be inspected before deciding whether a safe actual preflight route is available. If one cannot be admitted, report **admission-only hold**, not a completed comparison.

From this worktree:

```sh
python3 reports/skill-first-capabilities/test_pilot.py
python3 reports/skill-first-capabilities/pilot.py prepare --state /private/tmp/skill-first-pilot-clock.json
python3 reports/skill-first-capabilities/pilot.py start --state /private/tmp/skill-first-pilot-clock.json
python3 reports/skill-first-capabilities/pilot.py probe --state /private/tmp/skill-first-pilot-clock.json --provider codex
```

Repeat the last command with `claude`, `gemini`, `kiro`, `grok` in order. Capture each JSON result in the task evidence directory. Start is exclusive-create and refuses to overwrite an earlier clock. Start and every probe verify frozen collector/fixture/registry hashes and the clock-bound preparation hash. After code, fixture, or registry changes, explicitly prepare again after review; an already-started clock cannot accept changed preparation. Process-group cleanup runs even after successful probes, but detached descendants remain unverified and model admission remains false. Final pipe draining is bounded; lingering pipes produce containment_unverified. The collector records null native tokens because diagnostic results establish no model usage accounting capability.
