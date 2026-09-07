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
The receipt and profile are saved under `.core-prompts-state/profile-install`.
Later calls through the existing updater use the saved approved profile. They
build and validate a concrete plan internally, update only receipt-owned unchanged
skills within the same file scope, and verify every written file afterward.
Changes to targets, selected file scope, or ownership require a reviewed migration.
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
