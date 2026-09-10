# Install, migrate, and recover Core-Prompts

Use the current installer from a trusted release or verified source checkout for
fresh installs and historical repairs. An older installation does not need a
standalone updater, profile, or ownership receipt before it can be inspected.
The installer supplies the updater when absent. Scheduling remains a separate
opt-in step.

Author capabilities in `ssot/` and canonical resources; installed directories are
destinations, never authoring sources. Generated repository surfaces remain
available for every supported provider regardless of local installation selection.

## Preview and apply

From the current release directory, preview an existing Kiro installation:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --cli kiro --repair --dry-run > /tmp/core-prompts-install-plan.json
```

Review `selection`, `actions`, `outcomes`, `preserved`, `installation_preserved`,
and `blockers` in the JSON.
Apply the reviewed plan using the same release source and target:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --apply-plan /tmp/core-prompts-install-plan.json
```

`scripts/deploy-surfaces.sh` accepts the same external-target commands. Replace
`$HOME` with a disposable directory to rehearse first. Both wrappers require
`--allow-nonlocal-target` for an external target. The plan binds source identities,
selection, ownership state, and inspected destination files. Apply locks the
target and replans; changed inputs require a new preview. Copies use staged
per-file replacement, with recoverable journals for the whole transaction.

| Situation | Selection behavior |
| --- | --- |
| Fresh target, `--cli kiro` | Install current Kiro skills; add `--with-agents` to explicitly select skills and emitted agents. |
| Historical target without saved state | Recognize existing packages on selected providers, then migrate their same-surface successors. `--repair` makes this intent explicit. |
| Saved schema 1 skills profile | Normal sync carries forward its selected skills; explicit `--repair` also discovers independently recognized existing agents on its selected providers. |
| Saved schema 2 installation | Routine sync keeps saved provider, surface, and slug selection. Explicit `--repair` discovers additional recognizable installed packages within scope. |
| Explicit `--slug SLUG` | Select that current capability's emitted skills and agents; repeat for multiple slugs. |
| `--surface-only --slug SLUG` | Manage the selected surfaces and ownership state without refreshing the updater or launcher. |

`--cli` accepts `codex`, `kiro`, `claude`, `gemini`, `grok`, or `all`. On an initial
unprofiled run, `all` discovers providers through available CLI binaries or
existing surface directories. It is not a request to expand a saved selection.
Use a concrete provider for a fresh offline target. `--strict-cli` additionally
requires selected provider binaries to be present; it does not authenticate or
exercise them.

The optional schema 1 profile `.meta/install-profiles/codex-kiro-grok.json` remains
a skills-only selection input:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --profile .meta/install-profiles/codex-kiro-grok.json --dry-run \
  > /tmp/core-prompts-profile-plan.json
```

An empty profile `slugs` list selects current skills for those providers at
activation. The resulting concrete selection is saved in
`.core-prompts-state/installation.json`; later new catalog entries are not
automatically added. Do not edit ownership receipts to grant ownership.

## Historical recognition and preservation

The checked-in `.meta/install-profiles/legacy-installations.json` catalog binds
complete historical package inventories to exact hashes and modes. Its source
release refs are recorded in `legacy-release-refs.json`. Recognition uses this
trusted catalog or an existing valid ownership receipt, not a target-authored
manifest. The catalog covers 54 pinned release versions; the historical 24-skill
population is one fixture, not a limit on supported current capabilities.

Each skill and agent is recognized independently. A recognized Kiro skill does
not authorize installing an absent Kiro agent, and a package on one provider does
not authorize another provider. Recognized `autosearch` packages migrate to
`engos-optimization-auto-research`; `mentor` has no successor and is retired only
when its package ownership is recognized and no unresolved dependency
requires it. Replacement files are verified before predecessor files are removed.

Unknown, customized, and symlinked packages are preserved as whole packages,
including partial packages that fail ownership recognition. During schema-1
receipt conversion, matching present files can establish ownership even when
receipted members are missing; the reviewed plan may restore those members.
Inspect the plan's exact actions before applying it. A custom successor or unresolved reference from another agent preserves
the affected predecessor. Codex registration changes preserve unrelated custom
configuration; conflicts preserve affected agents. Third-party packages remain
with their own installers. In particular, an existing unreceipted third-party
Loopy copy is not adopted merely because its bytes match the bundled package.

Preservation is a reported incomplete migration, not installation parity:

- Exit `0`: current operation completed or no-op without preserved conflicts.
- Exit `2`: `applied-with-preserved` or `no-op-with-preserved`; inspect the report
  before claiming completion. Independent safe packages may have updated.
- Exit `1`: blocked or failed. Source/runtime integrity blockers prevent surface
  changes. An apply failure can leave an unfinished recoverable transaction; use
  its reported ID before attempting another installation.

`preserved` describes the current operation; `installation_preserved` retains
unresolved conflicts across the installation. A successful narrow operation does
not clear unrelated preserved packages or establish installation-wide parity.

## Routine updates and older updaters

The saved installation records package ownership and selected providers, surfaces,
and slugs. Routine updates reconcile resource additions and removals within those
unchanged owned packages. They preserve customization conflicts and do not expand
the installation to unrelated new catalog entries. The earlier addition-only
`--migrate` procedure is superseded by this package reconciliation.

The installed launcher remains `~/update_core_prompts.sh`:

```bash
~/update_core_prompts.sh
~/update_core_prompts.sh --check-release
~/update_core_prompts.sh --accept-release
```

Release checking compares the canonical remotes and prepares a verified release
mirror. Checking alone never installs. New-engine acceptance uses that mirror and
a recoverable installation transaction; it does not advance a development
checkout. Runtime parity and optional rendered consumer views are separate:
retained optional views are not certified current by a runtime update. Hash
verification assumes a trusted release source; it is not a signature guarantee.

Some compatible older profile engines can receive the new generated runtime
through their existing file allowlist. That invocation still executes the old
engine. The **next** ordinary or scheduled invocation runs the new engine and
converts saved selection. An immutable older engine whose scope guards reject the
bridge needs the current installer once, using the preview/apply commands above.
This is not universal self-upgrade support. Missing-updater installations use the
same current installer directly.

Create a schedule only when wanted:

```bash
~/update_core_prompts.sh --schedule-daily 09:00
# Disable automatic release acceptance; existing-bundle sync still runs:
~/update_core_prompts.sh --schedule-daily 09:00 --notify-only
```

Scheduled runs check releases first and auto-accept valid releases by default,
then perform routine sync. `--notify-only` disables automatic release acceptance
but still runs routine sync of the existing bundle. Existing schedules are preserved during install,
repair, and runtime refresh; they are not created or modified implicitly.

## Recover an installation

Use the transaction ID returned by apply. Preview recovery before restoring:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --list-transactions
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --rollback TRANSACTION_ID --dry-run
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --rollback TRANSACTION_ID
```

The existing updater also exposes recovery through `--list-snapshots` and
`--rollback previous`. Rollback verifies stored preimages and current files,
restores prior package bytes and modes, and removes only files added by that
transaction. Later edits to ordinary package files or `installation.json` block
restoration.

The operational `release-watch.json` has one narrow exception when a transaction
updated an existing release-watch file: later release observations and timestamps
are preserved, `installed_version` is restored, and `pending_version` and `status`
are recomputed from the retained latest-release observation. Another installed-version
transition or a changed file mode still blocks rollback. This exception does not
relax package or installation-state ownership checks.

Multi-file application is recoverable, not atomic; an interrupted transaction
must be recovered before another apply.

Journals and backups live under `.core-prompts-state/install-transactions/`.
They are retained. `retention_candidates` is advisory for intact older journals
beyond the latest two; no automatic pruning or `--snapshot-retention` cleanup is
performed for these transactions. Older snapshot formats remain a separate
compatibility path. Empty directories may remain after exact-file retirement.

## Provider discovery and evidence

| Provider | Installed skill root | Agent root |
| --- | --- | --- |
| Codex | `.agents/skills/` | `.codex/agents/`, with target-local registrations |
| Kiro | `.kiro/skills/` | `.kiro/agents/` |
| Claude | `.claude/skills/` | `.claude/agents/` |
| Gemini | `.gemini/skills/` | `.gemini/agents/` |
| Grok | `.grok/skills/` | No native agent surface claimed |

Installed bytes, native CLI discovery, and authenticated capability execution
require separate verification. For Kiro, inspect agents both from a neutral
directory and from the project: workspace definitions can override global names.
Consult [Kiro skills](https://kiro.dev/docs/skills/) and
[custom-agent configuration](https://kiro.dev/docs/custom-agents/configuration-reference/)
for the reader configuration applicable to the installed CLI version. Static hash
parity does not establish account access or runtime activation, and this migration
does not perform a general Kiro version/configuration upgrade.

## Discovery and member registries

KiroCrew's Crew Members roster is separate application state. Its saved names can
survive native package retirement. Core-Prompts does not rewrite that registry,
preferences, favorites, bindings, or history. Verify and manage those through the
application separately before claiming old roster names are gone.

## Portable source and package boundary

Runtime source lives under `scripts/core_install/`. The deterministic
`scripts/build-install-runtime.py` generator compiles it into the shipped
`scripts/deploy-profile.py` capsule, keeping the older v1.14 runtime path allowlist
compatible. Do not patch the generated capsule as the lasting source fix.

Skill resources that must stay relative to `SKILL.md`, including `references/`
and `agents/openai.yaml`, originate in `sources/skill-package-resources/<slug>/`.
Other canonical capability resources originate in
`sources/capability-resources/<slug>/`. Generated manifests bind the complete
emitted packages. Loopy retains its pinned upstream `loopy` identity and companion
resources; source inclusion does not grant ownership of existing third-party
installations. See [release packaging](RELEASE-PACKAGING.md) for delivery gates.
