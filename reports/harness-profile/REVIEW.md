# Harness deployment and Loopy packaging review

Baseline: `45c06d2d99129780a1864212c3ff4602a70950d6` in the assigned isolated worktree,
branch `AI/harness-profile-loopy`. Namespace and UAC integration remain pending.
No merge, tag, release, home installation, or paid model evaluation was performed.

## Source and write ownership

- Rules first: `.meta/surface-rules.json`; UAC surface matrix and target choices
  add native Grok skills. Codex/Gemini/Claude/Kiro support remains.
- Generated repository outputs are rebuilt from SSOT and canonical metadata.
  Skill descriptor links and auto-research's helper example use package-relative
  paths so a Codex home destination can move to `.agents` safely.
- `scripts/deploy-surfaces.sh` routes explicit/saved skills profiles to its
  receipt-protected deployment helper. No new updater or scheduler is introduced.
- Profile scope is skills only. Agents, registrations, shared client configs,
  launcher/updater refresh, and other owners' installers are separate write sets.
- Loopy's full seven-file package is pinned under `sources/intake/loopy/` with
  installer provenance and separately verified upstream MIT license. It is not
  accepted SSOT yet. Generic UAC rewriting was detected and not applied.

## Verification

- Strict surface validation passed after refreshing seven official documentation
  sources. Cache fetch failure was an environment result; a successful network
  refresh resolved it without weakening validation.
- Full regression run before the lifecycle guard: 674 tests and 122 subtests passed.
- Latest automatic updater/package subset: 21 tests passed; independent lifecycle test passed after polling/recovery fixes; profile/package prerequisite subset: 18 tests passed.
- Earlier deployment/package regression run: 39 tests passed.
- UAC capability/validator subset: 19 tests passed.
- Independent reviewer ran profile and portable-package tests: 17 passed.
- Independent review found and closed: mutating rollback dry-run, non-atomic
  writes, partial legacy package retirement, discarded profile-only changes,
  omitted state write-set metadata, retained-transaction retry collisions, and
  source-identity assertions that compared suffixes rather than full paths.
- Native reader probe: `native-readers.json`, zero assertion errors. Codex
  0.153.4 lists repository `.codex` and `.agents` and both home copies; exact
  legacy-home removal leaves the chosen home and repository identities intact.
- Grok 1.0.5 resolves native repo then native home, falls back to `.agents`, and
  honors an exact ignore path. Disabled Claude compatibility remains listed but
  tagged disabled; source-path and enabled-state checks are separate.
- Generated disposable install: 249 selected files copied, 26/26 Grok skills
  resolved from native home packages (`generated-install-readback.json`).
- Kiro 2.21.1 is installed. Native paths are documentation-verified; fresh
  authenticated skill activation is unperformed.

## Future home plan

`proposed-home-plan.json` is a read-only preview bound to this worktree's current
source hashes and current selected home inventories. It must be regenerated after
namespace/UAC integration and again before any authorized home turn. It is not
approval to deploy. The default profile contains no retirements. The current home has updater bundle identity
blockers; profile apply refuses all writes until a separately reviewed
standalone-bundle refresh establishes matching deployment code.

Unknown or customized packages are preserved as a whole. Identical bytes do not
establish ownership. Core-Prompts must not adopt GWS, third-party installer data,
unknown customizations, or the independently edited Kiro continuity package.
Initial ownership attribution for old installs remains a separate reviewed step.
The extracted-package lifecycle test verifies successful ordinary sync and
release acceptance using the saved profile and pinned verified bundle, without
a development checkout. Local customization and profile expansion are refused.
Release rollback restores the standalone version, selected skill, ownership, and
release-watch state without resurrecting the retired duplicate. No new scheduler
is introduced.
The dry-run includes selected copies, receipt/profile writes, exact transaction
artifact paths, and the atomic staging-file contract. Backups remain recoverable;
rollback checks hashes and preserves later edits.
