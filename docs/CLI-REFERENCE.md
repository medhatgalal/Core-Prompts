# CLI Reference

Use this page when you need exact commands, paths, generated-surface locations, and deploy behavior. This is still a reference page, but it now includes task-oriented examples so the commands are easier to apply.

Preferred active runtime: Python `3.14`.
Minimum supported runtime: Python `3.11+`.

Preferred wrappers:

- `bin/capability-fabric` for build, validate, and deploy
- `bin/uac` for import, plan, judge, audit, explain, and apply

If local `python3` resolves to an older interpreter, set `PYTHON_BIN=python3.11` or `PYTHON_BIN=python3.14` before using the wrappers.

## Engineering report CLI

The installed `eng-report` launcher uses `~/.core-prompts-updater/scripts/eng-report.py`, so it survives source-checkout cleanup. It implements `run`; inspect `eng-report run --help` for its flags. Select a configured repository using `--config FILE --name NAME`, collect metrics using `--json`, and render using `--narrative-file FILE --output DIR`. JSON mode leaves the report directory and HTML/JavaScript artifacts untouched, but may fetch configured Git repositories. `--repo`, `--drive`, `--open`, and notification flags are not executable options. Ask `engos-audit-engineering-progress` for configuration, uploads, browser opening, or authorized notifications. Its terminal skill help starts no workflow.

## Common Commands

### Capability evaluation

```bash
bin/capability-eval compile --skill <slug>
bin/capability-eval compile --all --check
bin/capability-eval calibrate --static-only
bin/capability-eval probe
bin/capability-eval compare --skill <slug> --candidate <path> --profile <profile>
bin/capability-eval compare --skill <slug> --baseline <path> --candidate <path> --run-plan <path> --profile promotion --allow-model-calls --max-tokens 5000000
bin/capability-eval report --run <run-id>
```

Profiles are `static`, `native`, `routing-canary`, `canary`, `promotion`, `cross-host`, and `sweep`. The first two have a hard token cap of zero. `native` reports runtime availability only; it does not prove skill discovery or behavior. A live command also requires a closed run plan, explicit model-call authorization, conforming registered adapters, and a cap no larger than the profile limit. The protected promotion flow adds sealed data, independent scoring and judging, reproduction, signed receipts, and a cumulative token ledger.

| Command | Purpose | Mutates repo state |
| --- | --- | --- |
| `bin/capability-fabric build` | generate all CLI surfaces, bundled resources, and generated inspection views | no |
| `bin/capability-fabric validate --strict` | validate generated surfaces and contracts | no |
| `bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target --repair --dry-run` | preview ownership-aware installation JSON | no |
| `bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target --apply-plan PLAN.json` | apply an exact reviewed installation plan | yes |
| `bin/capability-fabric update --check-release` | check installed standalone bundle vs latest immutable release and update release-watch state | no |
| `bin/capability-fabric update --accept-release` | explicitly accept and apply a pending release from the synced mirror | yes |
| `bin/capability-fabric update --rollback previous` | restore the latest available installation recovery point | yes |
| `bin/capability-fabric update --list-snapshots` | list installation journals and older rollback snapshots | no |
| `python3 scripts/smoke-clis.py` | probe installed vendor CLIs and surface visibility | no |
| `bin/uac audit` | inspect current SSOT and generated surface alignment | no |
| `bin/uac plan <source...>` | show proposed landing shape for one or more sources | no |
| `bin/uac judge <source...> --quality-profile architecture` | run the built-in quality loop without writing repo state; may recommend bounded behavioral proof via `engos-optimization-auto-research` when structural quality is close but confidence is weak | no |
| `bin/uac apply <source...> --yes` | write canonical SSOT and descriptors, then build and validate | yes |
| `bin/uac apply <source...> --promotion-verdict <path> --promotion-trust-root <path> --approved-trust-policy-sha256 <sha256> --approved-trust-policy-revision <commit> --finalize-existing-candidate --yes` | finalize an already-canonical candidate only after current independent evidence and a pre-candidate approved trust policy pass every gate | yes |

## Task-Oriented Examples

### Validate Or Render An OpEx Digest Snapshot

From an emitted `engos-audit-opex-incident-review` skill directory:

```bash
python3 resources/opex_digest.py validate \
  --current <current-snapshot.json> \
  --previous <prior-snapshot.json>

python3 resources/opex_digest.py render \
  --current <current-snapshot.json> \
  --previous <prior-snapshot.json> \
  --output-dir <output-directory> \
  --format both
```

`validate` and `render` use local normalized snapshots and make no network calls. The renderer owns count reconciliation, section order, SLA labels, links, escaping, responsive/print CSS, and overwrite refusal. Live Jira and Drive collection remains a skill workflow with its own read-access and coverage requirements.

### Finalize A Behaviorally Proven Candidate

```bash
bin/uac apply /absolute/path/to/candidate-source \
  --promotion-verdict /absolute/path/to/public-bundle/promotion-verdict.json \
  --promotion-trust-root /absolute/path/to/public-bundle/evaluator-trust-store.json \
  --approved-trust-policy-sha256 <64-hex-policy-sha256> \
  --approved-trust-policy-revision <40-hex-policy-commit> \
  --finalize-existing-candidate \
  --yes
```

Use this only after the evaluator foundation and approved trust policy have landed on protected main, the policy revision is an ancestor of the evaluated baseline, and the candidate already exists unchanged in canonical SSOT. Success records `behavioral_status: promote`; `inconclusive`, `hold`, or `stale_evidence` leaves the behavioral baseline unchanged.

See [Capability evaluation](CAPABILITY-EVALUATION.md) for the protected trust model and [UAC usage](UAC-USAGE.md) for the full gate list.

### Rebuild Everything From Canonical State

```bash
bin/capability-fabric build
```

Use this when:

- SSOT or descriptor state changed
- you want regenerated skills, agents, and bundled resources
- generated inspection views need to refresh

Expected result:

- regenerated CLI surfaces
- refreshed generated inspection views
- updated build evidence under `reports/build-surfaces/`

### Validate Before PR Or Release

```bash
bin/capability-fabric validate --strict
```

Use this when:

- you changed canonical source, generated surfaces, or docs tied to current behavior
- you want to catch contract drift before merge
- a release gate needs strict validation evidence

Expected result:

- validation report under `reports/validation/`
- errors or warnings if contracts, paths, or schema expectations drifted

### Probe Local CLI Visibility

```bash
python3 scripts/smoke-clis.py
```

Use this when:

- you want to confirm the expected CLIs are visible locally
- generated surfaces may no longer be discoverable as expected
- packaged output health needs a quick local probe

Expected result:

- smoke evidence under `reports/smoke-clis/`
- visibility checks for supported discovery-backed surfaces

### Resolve Analyze Context State Safely

Use the helper bundled with the installed `engos-memory-context-continuity` skill instead of constructing state paths manually:

```bash
STATE_HELPER="<installed-engos-memory-context-continuity-skill>/resources/state_store.py"
python3 "$STATE_HELPER" paths --cwd "$(pwd)" --task-id <safe-task-id>
python3 "$STATE_HELPER" init --cwd "$(pwd)" --task-id <safe-task-id>
python3 "$STATE_HELPER" write --cwd "$(pwd)" --task-id <safe-task-id> \
  --kind todo --input /absolute/path/to/updated-todo.md
```

The helper derives a readable project slug plus a deterministic hash from the normalized Git common directory, so linked worktrees share one project ID while unrelated same-name repositories do not. Task IDs accept only 1–80 lowercase letters, digits, hyphens, or underscores and must start and end alphanumeric. State stays under `${ANALYZE_CONTEXT_STATE_HOME:-$HOME/.analyze-context}`, outside Git worktrees, with `0700` directories, `0600` files, one-writer locking, path-containment checks, and atomic replacement writes.

### Lint, Seal, And Check A Plan To Goal Packet

Run these from the installed `engos-design-plan-to-goal` skill directory after the skill has produced and materialized a packet:

```bash
bash resources/goal-lint \
  --tree /absolute/path/to/untouched-tree \
  --hostile-tree /absolute/path/to/cheapest-fake-tree \
  /absolute/path/to/packet

python3 resources/scripts/goal_packet.py lint /absolute/path/to/packet
python3 resources/scripts/goal_packet.py seal /absolute/path/to/packet
python3 resources/scripts/goal_packet.py check /absolute/path/to/packet
```

The packet must contain:

- `goal.txt`, `spec.md`, `baseline.json`, `verify.sh`, and `packet.json`
- `criterion-flips.json` plus separate present/absent fixture trees for every machine criterion
- `judge-amendments.json`, even when its initial amendment list is empty

`verify.sh --list-criteria` must print every machine criterion exactly once. With `CRITERION_ID=<id>`, the verifier must execute only that criterion, emit `CRITERION <id> PASS` with exit `0` when present, and emit `CRITERION <id> FAIL` with exit `1` when absent. Sealing binds packet artifacts and criterion fixture-tree hashes; `check` must pass immediately before launch.

See [Plan to Goal Design](EXAMPLES.md#engos-design-plan-to-goal) for a two-criterion example. These commands establish deterministic packet integrity only. Behavioral promotion still requires independent qualified evaluation.

### Preview And Apply An Installation

The external-target path is shared by `install-local.sh` and `deploy-surfaces.sh`:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --cli kiro --repair --dry-run > /tmp/core-prompts-install-plan.json
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --apply-plan /tmp/core-prompts-install-plan.json
```

Review `selection`, `actions`, `outcomes`, `preserved`, and `blockers`. Apply
replans under the target lock and rejects changed source, state, or destination
identities. No old updater or receipt is required for trusted historical recognition.

| Option | Meaning |
| --- | --- |
| `--cli codex\|kiro\|claude\|gemini\|grok\|all` | Select a provider; initial `all` discovers available or existing providers, while saved selection persists on routine calls. |
| `--repair` | Adopt independently recognized existing skills and agents within the selected providers. |
| `--with-agents` | Explicitly select current skills and emitted agents; fresh default is skills. |
| `--slug SLUG` | Select emitted skills and agents for a capability; repeat for multiple slugs. |
| `--surface-only` | Require a slug and skip updater/launcher refresh while recording surface ownership. |
| `--profile PATH` | Use a schema 1 skills selection input; do not combine with CLI/slug/surface-only selection. |
| `--dry-run` | Print a JSON plan without installation writes. |
| `--apply-plan PATH` | Apply a reviewed plan for this source and target. |
| `--strict-cli` | Require selected CLI executables; no runtime or account proof implied. |
| `--list-transactions` | List installation transaction IDs and status. |
| `--rollback ID --dry-run` | Check exact recovery preconditions before restoration. |
| `--rollback ID` | Restore transaction preimages if later edits do not conflict. |

Fresh installs save concrete provider/surface/slug selection in
`.core-prompts-state/installation.json`. Existing schema 1 profiles retain their
skill scope on ordinary sync; explicit repair can add independently recognized
existing agents on those providers. Routine updates reconcile resources within
owned selected packages, without adding unrelated catalog entries.

Whole unknown, custom, symlinked, or unrecognized partial packages are preserved. Exit `2`
reports `applied-with-preserved` or `no-op-with-preserved`; it is not full parity.
Exit `1` reports blockers or failures. Source/runtime blockers prevent surface
changes, while interrupted apply requires recovery using its reported transaction.

Historical retirement, including `mentor` and namespace predecessors, is based
on trusted historical identities or valid ownership receipts and dependency checks.
Schema-1 receipt conversion may restore missing receipted files; see
[recognition and preservation](INSTALL-PROFILES.md#historical-recognition-and-preservation).
Exact preimages
are journaled; the new engine does not remove files solely because their names
appear on an old prune list. See [installation and recovery](INSTALL-PROFILES.md).

### Check Or Accept Installed Releases

```bash
~/update_core_prompts.sh --check-release
~/update_core_prompts.sh --accept-release
~/update_core_prompts.sh --list-snapshots
~/update_core_prompts.sh --rollback previous
```

`bin/capability-fabric update` exposes the same updater options from a checkout.
Checking fetches release tags, prepares the dedicated mirror, and updates
`.core-prompts-state/release-watch.json`, without installing. New-engine acceptance
uses the verified mirror and saved installation scope in a recoverable transaction;
it does not update a development checkout.

Use `--schedule-daily HH:MM` to explicitly create or change a schedule; scheduled
runs auto-accept valid releases by default. Add `--notify-only` to disable automatic
release acceptance; routine sync of the existing bundle still runs. Installation
and repair preserve existing schedules.

The updater exposes new installation journals alongside older recovery formats.
New journals live under `.core-prompts-state/install-transactions/` and are not
automatically pruned. `retention_candidates` identifies eligible older journals
beyond the latest two for separately reviewed cleanup. `--snapshot-retention N`
applies only to the older snapshot path, not new transactions.

Recovery uses exact package and installation-state identities, with a narrow
[release-watch observation exception](INSTALL-PROFILES.md#recover-an-installation).

## Canonical Inputs

- SSOT: `ssot/`
- descriptors: `.meta/capabilities/`
- manifest: `.meta/manifest.json`
- handoff contract: `.meta/capability-handoff.json`
- baseline sources: `sources/ssot-baselines/`
- validation evidence: `reports/validation/latest.json` and timestamped reports under `reports/validation/`
- build provenance: `reports/build-surfaces/latest.json`
- smoke evidence: `reports/smoke-clis/latest.json`

## Generated Inspection Views

- `dist/consumer-shell/capability-catalog.json`
- `dist/consumer-shell/release-delta.json`
- `dist/consumer-shell/status.json`
- `docs/CAPABILITY-CATALOG.md`
- `docs/RELEASE-DELTA.md`
- `docs/STATUS.md`

These generated views are derived from canonical metadata and reports. They are inspection aids, not a separate source of truth.

## Generated Surfaces

| CLI | Direct skill surface | Bundled skill resource | Agent surface | Bundled agent resource |
| --- | --- | --- | --- | --- |
| Codex | `.codex/skills/<slug>/SKILL.md` | `.codex/skills/<slug>/resources/capability.json` | `.codex/agents/<slug>.toml` | `.codex/agents/resources/<slug>/capability.json` |
| Gemini | `.gemini/skills/<slug>/SKILL.md` | `.gemini/skills/<slug>/resources/capability.json` | `.gemini/agents/<slug>.md` | `.gemini/agents/resources/<slug>/capability.json` |
| Claude | `.claude/skills/<slug>/SKILL.md` | `.claude/skills/<slug>/resources/capability.json` | `.claude/agents/<slug>.md` | `.claude/agents/resources/<slug>/capability.json` |
| Kiro | `.kiro/skills/<slug>/SKILL.md` | `.kiro/skills/<slug>/resources/capability.json` | `.kiro/agents/<slug>.json` | `.kiro/agents/resources/<slug>/capability.json` |

## Direct Surface Standard

Direct exposure is standardized on `skills/<slug>/SKILL.md` for every supported CLI. This repo does not deploy direct exposure into vendor `commands/` or `prompts/` directories.

## Deploy Contract

- `apply` in UAC changes canonical repository source; installation `--apply-plan` changes the reviewed target.
- External-target install and deploy use the same ownership-aware engine and create no symlinks.
- An explicit external `--target` requires `--allow-nonlocal-target`; use `build` for repository surfaces.
- Normal installation supplies the standalone runtime and `update_core_prompts.sh`; `--surface-only --slug SLUG` skips runtime refresh.
- Historical packages require trusted catalog identities or valid receipts; customization and dependency conflicts preserve affected packages.
- Plans bind exact identities; transactions retain recoverable preimages and verify replacements before retirement.
- Install and deploy do not rewrite portable capability metadata paths.
- Repeated no-op build/validation should not rewrite `.meta/manifest.json`; run evidence belongs under `reports/`.

## Smoke Checks

- version and help probes run for configured CLIs
- filesystem checks verify expected generated surfaces per CLI
- discovery checks run only for discovery-backed surfaces:
  - Gemini skills
  - Claude agents
  - Kiro agents

## Validation Contract Notes

- persisted local source references inside canonical metadata and bundled `capability.json` resources must be repo-relative, not absolute machine paths
- every SSOT entry must satisfy the canonical contract sections enforced by validation: purpose, primary objective, workflow contract, boundaries, invocation hints, required inputs, required output, examples, and an evaluation rubric or scorecard-equivalent

## Related Docs

- [Getting started](GETTING-STARTED.md)
- [Capability evaluation](CAPABILITY-EVALUATION.md)
- [Examples](EXAMPLES.md)
- [Capability catalog](CAPABILITY-CATALOG.md)
- [Release delta](RELEASE-DELTA.md)
- [Consumer status](STATUS.md)
- [UAC usage](UAC-USAGE.md)
- [Release packaging](RELEASE-PACKAGING.md)

## Selected local skill targets

Choose Codex, Kiro, and Grok with an explicit skills-only profile. Codex skills install
under `.agents/skills`; Grok gets native `.grok/skills` packages. Preview the exact
write set and preserve unknown or customized copies before applying. See
[installation profiles and rollback](INSTALL-PROFILES.md).

## Resolve a module resource package

From an emitted skill directory:

```bash
python3 resources/scripts/load_module.py --route /grade --format text
python3 resources/scripts/load_module.py --route "/adversarial /debate /deep" --format json
```

The helper is read-only and uses the standard library. It emits the selected dependency closure and bound content identifiers; output can be large because required text is not summarized. On agent surfaces, locate the helper relative to the directory containing the bundled `capability.json`.

For reviewed semantic intake, `bin/uac judge <candidate> --requirement-review <review.json>` and `bin/uac apply <candidate> --requirement-review <review.json> --yes` accept independently reviewed, hash-bound requirement dispositions. They do not imply behavioral promotion. See [UAC usage](UAC-USAGE.md#resource-aware-and-reviewed-modernization).
