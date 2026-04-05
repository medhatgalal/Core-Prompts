# CLI Reference

Use this page when you need exact commands, paths, generated-surface locations, and deploy behavior. This is still a reference page, but it now includes task-oriented examples so the commands are easier to apply.

Preferred active runtime: Python `3.14`.
Minimum supported runtime: Python `3.11+`.

Preferred wrappers:

- `bin/capability-fabric` for build, validate, and deploy
- `bin/uac` for import, plan, judge, audit, explain, and apply

If local `python3` resolves to an older interpreter, set `PYTHON_BIN=python3.11` or `PYTHON_BIN=python3.14` before using the wrappers.

## Common Commands

| Command | Purpose | Mutates repo state |
| --- | --- | --- |
| `bin/capability-fabric build` | generate all CLI surfaces, bundled resources, and generated inspection views | no |
| `bin/capability-fabric validate --strict` | validate generated surfaces and contracts | no |
| `bin/capability-fabric deploy --dry-run --cli all` | preview copy-only deployment to a target root | no |
| `python3 scripts/smoke-clis.py` | probe installed vendor CLIs and surface visibility | no |
| `bin/uac audit` | inspect current SSOT and generated surface alignment | no |
| `bin/uac plan <source...>` | show proposed landing shape for one or more sources | no |
| `bin/uac judge <source...> --quality-profile architecture` | run the built-in quality loop without writing repo state | no |
| `bin/uac apply <source...> --yes` | write canonical SSOT and descriptors, then build and validate | yes |

## Task-Oriented Examples

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

### Preview A Deploy Without Mutating A Target

```bash
bin/capability-fabric deploy --dry-run --cli all
```

Use this when:

- you want the copy plan before touching a target root
- you are reviewing install behavior
- you want to scope deploy to specific CLIs or slugs

Example with slug targeting:

```bash
bin/capability-fabric deploy --dry-run --cli codex --slug autosearch --slug supercharge
```

Expected result:

- explicit copy plan
- no target mutation

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

- `apply` mutates canonical repo state only
- `deploy` copies generated artifacts to a target root
- deploy is copy-only and never creates symlinks
- deploy defaults to the repository root unless `--target` is provided
- `scripts/install-local.sh` is a compatibility wrapper around deploy and remains copy-only
- install and deploy do not rewrite capability metadata paths
- repeated no-op `build` and `validate` runs should not rewrite `.meta/manifest.json`; volatile run evidence belongs under `reports/`

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
- [Examples](EXAMPLES.md)
- [Capability catalog](CAPABILITY-CATALOG.md)
- [Release delta](RELEASE-DELTA.md)
- [Consumer status](STATUS.md)
- [UAC usage](UAC-USAGE.md)
- [Release packaging](RELEASE-PACKAGING.md)
