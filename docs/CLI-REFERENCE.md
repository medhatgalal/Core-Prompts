# CLI Reference

Use this page for exact commands, paths, write effects, and generated-surface locations. For first use, see [Getting started](GETTING-STARTED.md); for task selection, see [Examples](EXAMPLES.md).

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

| Command | Purpose | Writes |
| --- | --- | --- |
| `bin/capability-fabric build` | generate all CLI surfaces, bundled resources, and inspection views | generated repository artifacts and build evidence |
| `bin/capability-fabric validate --strict` | validate generated surfaces and contracts | validation reports |
| `bin/capability-fabric deploy --dry-run --cli all` | preview deployment to the selected target root | none at the target |
| `bin/capability-fabric deploy --surface-only --slug <slug> --cli <cli>` | copy the selected emitted bundle without refreshing the standalone runtime | selected destination files and applicable recovery records |
| `bin/capability-fabric update --check-release` | check the installed bundle against the latest release | release cache and release-watch state; no installation |
| `bin/capability-fabric update --accept-release` | accept the pending verified release | installed files, ownership/update state, and recovery records |
| `bin/capability-fabric update --rollback previous` | restore the latest pre-release state | restored installed files and recovery state |
| `bin/capability-fabric update --list-snapshots` | list available recovery points | none |
| `python3 scripts/smoke-clis.py` | probe available CLIs and configured discovery surfaces | smoke reports; invoked CLIs may manage their own runtime state |
| `bin/uac audit` | inspect SSOT and generated alignment | no canonical landing |
| `bin/uac plan <source...>` | propose the landing shape | no canonical landing; source/quality evidence may be retained |
| `bin/uac judge <source...> --quality-profile architecture` | check a candidate before apply | quality reports; no canonical landing |
| `bin/uac apply <source...> --yes` | write canonical state, then build and validate | SSOT, descriptors, generated artifacts, and reports |
| `bin/uac apply <source...> --promotion-verdict <path> --promotion-trust-root <path> --approved-trust-policy-sha256 <sha256> --approved-trust-policy-revision <commit> --finalize-existing-candidate --yes` | finalize independent proof for an unchanged canonical candidate | accepted behavioral baseline and metadata, generated artifacts, and reports |

`--dry-run` describes the selected deploy mode. The legacy copy mode and receipt-protected profile mode have different ownership and recovery behavior; see [Installation Profiles](INSTALL-PROFILES.md) before a home install.

## Task-Oriented Examples

### Design An Experience

`engos-design-experience` is an installed skill, not a shell command. Invoke it in your host with the task and relevant artifact, existing product, platform, and API/state contracts. Use the [experience examples](EXAMPLES.md#engos-design-experience) for reports, applications, native limits, and selectable failure probes. Its bundled references support design decisions; they do not provide a renderer, service backend, or native test runtime.

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

### Preview A Deploy Without Mutating A Target

```bash
bin/capability-fabric deploy --dry-run --cli all
```

Use this when:

- you want the copy plan before touching a target root
- you are reviewing install behavior
- you want to scope deploy to specific CLIs or slugs

For an intentionally narrow external-target deployment, combine `--surface-only` with one or more `--slug` values. The command fails closed when `--surface-only` has no slug filter.

Example with slug targeting:

```bash
bin/capability-fabric deploy --dry-run --cli codex --slug engos-optimization-auto-research --slug engos-meta-supercharge
```

Batman-selected Kiro deploys have one additional, bounded cleanup contract. Preview it before changing an external target:

```bash
bin/capability-fabric deploy --dry-run --surface-only --cli kiro --slug engos-orchestration-batman --target "$HOME" --allow-nonlocal-target
```

When present, the dry-run lists exactly these deprecated prune candidates and does not move them:

- `.kiro/skills/engos-orchestration-batman/PROTOCOL.md`
- `.kiro/skills/engos-orchestration-batman/PROMPT-AMENDMENT.md`
- `.kiro/skills/engos-orchestration-batman/CODEX-UAC-INTAKE.md`

Removing `--dry-run` copies the current generated Batman surface and recoverably moves only those existing files under `.core-prompts-state/stale-pruned/<timestamp>/...`. Each live move prints a `source -> archive` receipt. The cleanup preserves `.kiro/skills/engos-orchestration-batman/SKILL.md`, its `resources/` tree, and unrelated files. A non-Batman slug or non-Kiro deploy does not trigger this cleanup.

For targeted recovery, use the receipt to restore the archived entry to its original source path. For a release install, the pre-install rollback snapshot remains available through `bin/capability-fabric update --rollback previous`.

Expected result:

- explicit copy plan
- no target mutation

When `engos-optimization-auto-research` is deployed, stale installed `autosearch` paths for the selected CLIs are pruned as part of the breaking rename.

The `engos-<category>-<skill-name>` namespace migration also prunes the matching unprefixed skill, agent, and agent-resource paths for the selected slug. Live pruning is recoverable: existing entries are moved under `.core-prompts-state/stale-pruned/<timestamp>/...` and each move prints a `source -> archive` receipt. No duplicate short-name packages or native menu aliases are emitted. Supercharge retains conversational prefix aliases within its canonical instructions. For Codex, matching legacy agent stanzas that point to the target's old managed agent files are removed during registration; unrelated custom stanzas are preserved.

### Check Or Accept Installed Releases

A complete home installation records `VERSION`, `RELEASE_SOURCE.env`, and `LOCAL_REPO.env` under `~/.core-prompts-updater/`. A disposable skills-only preview does not establish updater enrollment.

```bash
bin/capability-fabric update --check-release
bin/capability-fabric update --accept-release
bin/capability-fabric update --list-snapshots
bin/capability-fabric update --rollback previous
```

- `--check-release` fetches tags, syncs the release cache, updates release-watch state, and never auto-installs.
- `--accept-release` is the explicit install/apply step. It confirms the version and creates recovery records before applying the verified release.
- Scheduled `--schedule-daily HH:MM` runs auto-accept valid releases by default; add `--notify-only` to keep scheduling check-only.
- Saved-profile acceptance uses the verified release mirror and a recoverable profile transaction. It does not update the development checkout. Legacy acceptance may fast-forward a clean recorded source checkout and otherwise uses the release mirror.
- `--list-snapshots` includes available recovery points. `--rollback previous` restores the latest pre-release state; profile rollback protects later edits. Legacy snapshot retention defaults to two, while profile transactions use their own retained recovery records.

The [release-watch contract](RELEASE-PACKAGING.md#installed-release-watch-contract) is the canonical lifecycle description. See [Installation Profiles](INSTALL-PROFILES.md) for receipt ownership and transaction recovery.

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
| Grok | `.grok/skills/<slug>/SKILL.md` | `.grok/skills/<slug>/resources/capability.json` | none | none |

These are generated repository paths. The selected Codex home profile writes `.agents/skills`; profile destinations and discovery limits are described in [Installation Profiles](INSTALL-PROFILES.md).

## Direct Surface Standard

Direct exposure is standardized on `skills/<slug>/SKILL.md` for every supported CLI. This repo does not deploy direct exposure into vendor `commands/` or `prompts/` directories.

## Deploy Contract

- `apply` mutates canonical repo state only
- `deploy` copies generated artifacts to a target root
- deploy is copy-only and never creates symlinks
- deploy defaults to the repository root unless `--target` is provided
- `scripts/install-local.sh` is a compatibility wrapper around deploy and remains copy-only
- complete home installation and release watch follow the [release contract](RELEASE-PACKAGING.md#installed-release-watch-contract)
- legacy namespace cleanup is bounded by the selected slug and ownership checks described in [the deploy example](#preview-a-deploy-without-mutating-a-target); customized or unknown old packages stop it
- profile deployment uses exact plans, receipts, preserved package ownership, and guarded rollback; see [Installation Profiles](INSTALL-PROFILES.md)
- install and deploy do not rewrite capability metadata paths
- repeated no-op `build` and `validate` runs should not rewrite `.meta/manifest.json`; volatile run evidence belongs under `reports/`

## Smoke Checks

- version and help probes run for configured CLIs
- filesystem checks verify expected generated surfaces per CLI
- discovery checks run only for discovery-backed surfaces:
  - Gemini skills
  - Kiro agents
  - Grok skills
- Claude agent discovery is configured but currently disabled in `.meta/surface-rules.json`; availability/help and filesystem checks do not prove active discovery.

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
