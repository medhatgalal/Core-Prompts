# Selected skill installation profiles

Keep authoring in `ssot/` and canonical packaged resources. Build outputs under
`.codex`, `.kiro`, `.grok`, `.claude`, and `.gemini` are generated repository
artifacts. Selecting a local install profile does not remove any supported build
surface.

The `codex-kiro-grok.json` profile installs **skills only**. Existing agent files,
agent registrations, shared harness configuration, launchers, and updater bundles
are outside this profile's write set. The existing release/updater machinery
remains responsible for those artifacts; this feature does not add a scheduler
or another updater.

| Reader | Generated skill package | Selected home destination | Discovery considerations |
| --- | --- | --- | --- |
| Codex | `.codex/skills/<slug>` | `.agents/skills/<slug>` | Codex 0.153.4 lists same-named `.agents` and legacy `.codex` home copies separately. Generated repository copies remain legitimate. |
| Kiro | `.kiro/skills/<slug>` | `.kiro/skills/<slug>` | Default agent discovers native skills; custom agents require skill resource configuration. |
| Grok | `.grok/skills/<slug>` | `.grok/skills/<slug>` | Native and `.agents` paths participate in discovery. Repository definitions can override home definitions. Claude/Cursor compatibility and `[skills] ignore` also affect the result. |
| Claude | `.claude/skills/<slug>` | Not selected by this profile | Build and legacy install support retained. |
| Gemini | `.gemini/skills/<slug>` | Not selected by this profile | Build and legacy install support retained. |

These are skills, not permission grants. Descriptive tool metadata never overrides
platform permissions, approval rules, or runtime configuration. Grok receives
native skill packages; this does not claim native Grok subagent support.

## Review and apply a plan

For initial adoption, an existing standalone updater must match the source
package's portable `.meta/install-bundle.json` inventory. Old or customized
updater files block profile activation until a separate reviewed bundle refresh.
The initial plan pins both the selected skill scope and standalone bundle ownership.

Use a disposable target first. Review all `actions`, `state_actions`, preserved
packages, and transaction artifacts in the JSON plan:

```bash
scratch="$(mktemp -d)"
bash scripts/deploy-surfaces.sh --profile .meta/install-profiles/codex-kiro-grok.json \
  --target "$scratch" --allow-nonlocal-target --dry-run > /tmp/skill-install-plan.json
bash scripts/deploy-surfaces.sh --profile .meta/install-profiles/codex-kiro-grok.json \
  --target "$scratch" --allow-nonlocal-target --apply-plan /tmp/skill-install-plan.json
```

The plan binds the source manifest, every selected source file's hash and mode,
profile, current destination inventory, ownership receipt, and optional reader
evidence. Apply refuses a stale plan. Copy uses staged atomic file replacement.

The [preservation check](../.kiro/steering/repo-workflow.md#verification-expectations)
also distinguishes changes already present before apply from changes caused by the
installer. A stale baseline for an unrelated, untouched configuration can be refreshed
after its drift is recorded. That does not waive a stale write-set preimage, grant
ownership, or permit a profile change. Post-apply comparison uses the reviewed plan,
transaction afterimages, and that current preservation baseline; a subsequent no-op
plan and rollback dry-run add evidence without undoing the accepted installation.

The receipt and profile are saved under `.core-prompts-state/profile-install`.
Later calls through the existing updater use the saved approved profile. They
build and validate a concrete plan internally, update only receipt-owned unchanged
skills within the same file scope, and verify every written file afterward.
Changes to targets, selected file scope, or ownership stop routine sync and require
separate review. The addition-only migration below handles new resource files
within unchanged approved packages.
Local customizations and unknown files block the routine update before any writes.

Release checking pins the bundle inventory from the clean tagged mirror after the
existing dual-remote tag check. Release acceptance verifies that inventory and
all runtime file hashes, then refreshes the standalone bundle, selected skills,
ownership receipt, and release-watch state in one recoverable transaction. It
uses the verified release mirror, with no development-checkout fallback for profiles.
Optional `dist/consumer-shell` views are distribution extras rather than updater
runtime inputs; tagged Git mirrors do not contain them, and existing extras are
preserved. Release receipts label verification as `managed_runtime` and optional
views as `retained_unverified`; later release polling reports only `release_version`
verification. Retained rendered views are never certified as current release data.
The existing scheduler and `--accept-release`/`--rollback` commands remain in use.
The updater's rollback menu includes profile transactions; later edits block restore.
Initial adoption and legacy retirement still require an exact reviewed plan.

Unknown or customized members preserve the **whole skill package**. Identical
bytes alone do not establish Core-Prompts ownership. An initial migration therefore
requires separately reviewed provenance before existing installations can become
managed. The installer never adopts unknown packages automatically and never
rewrites `.agents/.skill-lock.json`. A preserved package is an unresolved migration
item, not successful installation parity.

`slugs` may restrict the profile to canonical entries. An empty list selects all
canonical skill entries for the selected clients. No home skill directory is used
as a source. GWS and other third-party packages remain owned by their installers.

## Routine legacy namespace migration

The standalone routine updater recognizes an older Core-Prompts installation by
checking a closed list of historical skill and agent paths against the installed
standalone bundle's manifest and file identities. When it finds proven entries,
that run installs only their namespaced successors for the selected CLI targets.
For example, a v1.12.2 bundle has the historical 24-skill population, so it
targets those 24 successors rather than every capability added since v1.12.2.
Later historical identities are included only when their exact installed package
is present and proven.

`mentor` is retired rather than renamed. Its skill, agent, and agent-resource
surfaces are moved into the existing recoverable stale archive only when they
match the old bundle. Missing, partial, customized, symlinked, or unproven
packages are preserved and reported; routine updates never adopt them or delete
them by name. KiroCrew's separate member registry remains outside this write set.

## Migrate new resources within the saved profile

When a release adds resource files to already approved skill packages, use the
existing profile engine's explicit `--migrate` mode. It retains the exact saved
profile, targets, slugs, and approved profile hash. Existing selected files and
standalone runtime files must still match their prior ownership identities. New
skill files must be absent and declared by the generated manifest; new runtime
files must be absent and declared by the verified standalone bundle inventory.
The same transaction refreshes owned skills and runtime files and extends their
receipt. Ordinary `--sync` continues to reject changes to selected file scope.

Run the direct Python CLI from the verified release source. The shell wrappers
do not expose `--migrate`. Use the saved profile and review the full plan before
applying it:

```bash
python3 scripts/deploy-profile.py --repo "$PWD" --target "$HOME" \
  --profile "$HOME/.core-prompts-state/profile-install/profile.json" \
  --migrate --dry-run > /tmp/skill-migration-plan.json
python3 scripts/deploy-profile.py --repo "$PWD" --target "$HOME" \
  --profile "$HOME/.core-prompts-state/profile-install/profile.json" \
  --migrate --apply-plan /tmp/skill-migration-plan.json
```

Both commands require `--migrate`; a plan cannot grant this authority by itself.
Apply regenerates the plan in the explicitly selected mode and rejects changes
to the source, destination, saved profile, receipt, or inspected package inventory.
All `blockers` must be empty. Review `actions`, `state_actions`, and transaction
artifacts, including runtime refreshes and receipt changes, before applying.

This mode rejects removals, legacy retirement, changed targets or slugs, new skill
packages even when the profile selects all slugs, missing prior owned files, and
unknown or customized package members. It preserves symlink boundaries and never
adopts an existing unowned file, even if its bytes match the source. Those cases
need a separately scoped migration; changing the saved profile or ownership
receipt manually does not establish provenance. Rollback uses the same transaction
commands below, restoring prior bytes and modes and removing only files that the
transaction added. Later edits still block rollback.

## Retire and recover exact managed files

`retire` is an explicit list of legacy `.codex/skills/<slug>/...` files. It defaults
to empty. Before listing any files, verify the prior Core-Prompts ownership receipt,
all package members, customization state, every relevant reader and its configured
source, and the retained `.agents` package identity. Record that bounded readback in
a repo-relative `reader_evidence` file referenced by the local profile. The plan
binds its hash; it does not manufacture or independently certify that evidence.

Retirement requires every existing legacy package member to be listed, receipt-owned,
and byte/mode-identical to its retained destination. Any unknown, customized,
symlinked, or unlisted member preserves the legacy entry point. No directory or
broad glob is removed. Empty directories may remain. Preimages are saved in the
transaction before exact files leave discovery.

Review rollback before applying it, using the transaction ID returned by install:

```bash
bash scripts/deploy-surfaces.sh --target "$scratch" --allow-nonlocal-target \
  --rollback TRANSACTION_ID --dry-run
bash scripts/deploy-surfaces.sh --target "$scratch" --allow-nonlocal-target \
  --rollback TRANSACTION_ID
```

Rollback verifies preimage backups and current file hashes before restoring.
Later edits block rollback instead of being overwritten. Transaction journals
and backup files are retained for inspection. Temporary staging files are created
beside written destinations and removed after replacement.

## Discovery evidence and limits

Official documentation checked on 2026-09-06:

- [Codex skill locations and metadata](https://learn.chatgpt.com/docs/build-skills)
- [Kiro CLI native skills and custom-agent resources](https://kiro.dev/docs/cli/skills/)
- [Grok native skill packages and descriptive tool metadata](https://docs.x.ai/build/features/skills-plugins-marketplaces)

The installed Grok user guide `08-skills.md` additionally documents `.agents`,
compatibility switches, path ignore rules, and `inspect --json` source paths.
Disposable-home runtime probes confirmed Grok 1.0.5 native repository and native
home selection, `.agents` fallback, exact-path ignore behavior, and Codex 0.153.4 dual home discovery. Compatibility-disabled Claude skills remain listed with `disabled: true`; a listed skill is not necessarily active. The probe compares complete resolved source paths. These results do not certify
a user's existing home configuration. Kiro 2.21.1 is installed here; its skill
activation has not been proven in a fresh authenticated session. No model invocation,
behavioral promotion, home installation, release, or tag is implied by these checks.

## Complete portable packages

Resources that must remain relative to `SKILL.md`, including `references/` and
`agents/openai.yaml`, belong in `sources/skill-package-resources/<slug>/`. The builder
copies them without changing their relative paths into every emitted skill package.
They are listed in the generated manifest and copied by both deployment paths.
The reserved generated files `SKILL.md` and `resources/capability.json` cannot be
shadowed by package resources. Existing `sources/capability-resources/<slug>/`
continues to supply resources under the generated `resources/` directory.

Loopy's seven-file installed package and installer receipt are pinned under
`sources/intake/loopy/` as intake evidence. Normal UAC intake passed with only a
descriptive display-title addition: the original operating body and all companion
files remain intact. Canonical `ssot/loopy.md` and its package resources generate
one `loopy` skill per supported client, retaining `$loopy` and `/loopy`. Loopy is
an upstream-named, hash-pinned exception to first-party `engos-*` naming; no alias
package is emitted. The pin is the preserved installed package, not a claim of
byte parity with an unverified historical upstream checkout. Structural
acceptance remains distinct from behavioral promotion and home ownership adoption.

Reproduce the optional no-model reader checks with explicit native executable paths:

```bash
python3 scripts/probe-skill-readers.py --codex /path/to/native/codex \
  --grok /path/to/grok --output /tmp/native-readers.json
```

Legacy namespace deployment also preflights old paths before any copy or
registration: every old package member must match its recorded standalone bundle
and manifest. Unknown, customized, or symlinked packages stop the operation and
remain discoverable until the controller resolves them explicitly.

## Discovery and member registries

A capability can emit both a skill and an agent. These are different invocation
surfaces for one SSOT definition, not competing canonical skills. Repository and
home copies are intentional; `kiro-cli agent list` inside this repository may warn
that its same-named workspace agent overrides the global one. Run the list from a
neutral directory as well to distinguish global and workspace discovery.

KiroCrew's Crew Members roster is separate from Kiro CLI's discovered agent files.
A renamed JSON file does not necessarily rename a previously saved crew member.
Check both `.kiro/agents` and the application's configured member registry before
claiming old names are fully retired. Do not infer duplicate skill packages from
an agent roster screenshot, or treat `Built-in` as proof that Kiro ships that agent.

A local KiroCrew investigation found old Core member names retained alongside their
namespaced successors: its roster reads saved `agents` configuration, adds newly
discovered names, and prunes missing package rows but retains rows marked `builtin`.
This is an application-registry migration, outside the Core skills profile's write
set. Use supported application management after checking member preferences,
favorites, bindings and active sessions. Preserve history and avoid wholesale
config/cache deletion. A routine Core update must not rewrite KiroCrew's config.

Example: `ic-assistant` maps to `engos-operations-ic-assistant`. Verify that the new
agent is available and that the old name is absent from native CLI discovery,
then reconcile the saved application member separately. Installed bytes, native
CLI discovery and the application's roster require separate verification.
