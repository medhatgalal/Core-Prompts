# Harness deployment and Loopy packaging review

Baseline: `45c06d2d99129780a1864212c3ff4602a70950d6` in the assigned isolated worktree,
branch `AI/harness-profile-loopy`. UAC integration at `8b1efb1ba05f272ddd437aa90f014091c5049861` and accepted OpEx integration at `8ccdd810f615c5c9cad0b349373a692b41d7380d` are complete.
Namespace integration remains pending its accepted main.
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
  installer provenance and separately verified upstream MIT license. Normal UAC intake on accepted fix
  `8b1efb1` passed after a descriptive display-title normalization. The complete
  original body and companion files are preserved; behavioral evidence remains
  pending. Earlier generic rewriting was detected and not applied.

## Verification

- Strict surface validation passed after refreshing seven official documentation
  sources. Cache fetch failure was an environment result; a successful network
  refresh resolved it without weakening validation.
- Initial regression run before the lifecycle guard: 674 tests and 122 subtests passed.
- Integrated UAC/Loopy run: 712 passed and 122 subtests passed, with four docs/package failures; corrected stale README count and dated changelog parsing then all eight affected docs/package checks passed.
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
or unknown customizations. The approved continuity improvement is included from
accepted main; final namespace-aligned home comparison must preserve any extra
unrecognized delta and the unchanged `.analyze-context` data location.
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

Both small resource-link changes also completed same-slug UAC plan/judge/apply
with structural_ready and preserved source fidelity. The accepted continuity
helper is byte-identical in generated Grok output (SHA-256
`f0c6a6d56194185df8b5c8426c53365234c4664425faa516714a5b45b86f976e`).
Loopy keeps its upstream name as a documented exception to first-party
`engos-*` names. Its installed ownership transfer remains a later home action.

After accepted OpEx integration and final same-slug UAC readbacks, the focused
OpEx/continuity/Loopy/package/public-doc suite passed 39 tests. Strict validation
and all contract checks passed. The final exact-commit full-run result is recorded
in the PR/MR; earlier full-run evidence above remains explicitly scoped.

Exact commit `619ccb98d83e55d51b1870e9dd922d83c94150eb`: full regression
passed 720 tests and 122 subtests; GitHub hosted surface validation succeeded.
A subsequent clean tracked-tree probe exposed optional dist views in the runtime
inventory. The final correction removes only those optional views from runtime
ownership and adds a tracked-only release fixture plus preservation assertions.

Final runtime-inventory correction: 37 focused profile/package/updater tests
passed, and the independent reviewer passed both tracked-release tests. Existing
optional consumer views are preserved. No new material review findings remain.
Namespace integration remains a coordinator-owned pre-merge hold.

The final scope-label delta also passed the 37-test focused suite and independent
static review. Acceptance certifies managed runtime only; optional views are
retained_unverified, and polling is labeled release_version observation.
