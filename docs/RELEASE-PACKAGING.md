# Release Packaging

This document defines the local release path for packaged Capability Fabric artifacts.

Preferred release runtime: Python `3.14`.
Minimum supported runtime: Python `3.11+`.

Prefer the repo wrappers for build and validate so the runtime selection stays consistent.

## Intent guide package contents

Source archives include `docs/INTENT-ROUTING.md`, `docs/GUIDE-HOSTING.md`, the offline `docs/guide/` files and canonical `.meta/intent-routing.json`. The runtime steering boundary includes `skill-routing.md` and its generated sibling `intent-routing.json`; installed routing does not depend on source-only docs. Regenerate with `python3 scripts/build-intent-guide.py` before the normal build and verify with `--check`. Packaging does not activate hosting or global routing. See the [hosting guide](GUIDE-HOSTING.md).

## Local Release Gate

Before any generator or source-generating test, verify the committed runtime
inventory without rebuilding it:

```bash
python3 -m pytest -q tests/test_install_bundle.py
python3 scripts/build-install-runtime.py --check
python3 scripts/build-legacy-catalog.py --check
```

An inventory mismatch identifies stale committed bytes or file modes. Preserve the
failure evidence, then regenerate from canonical sources and review the resulting
diff; a successful build cannot prove the prior committed inventory was valid.

First verify the comparison baseline and run the release build described below. The full test suite includes archive tests that require the generated `dist/consumer-shell` views. On a clean committed checkout, validate the checked-in surfaces before that build, as CI does.

```bash
env -u CORE_PROMPTS_RELEASE_BASE_REF python3 -m pytest -q
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
```

Keep the verified release-base override for actual release builds. The test suite
creates isolated Git repositories with their own tags; the per-command `env -u`
keeps the outer release tag out of those fixtures while leaving the shell's build
setting intact. During uncommitted release preparation, stage the intended new
source and generated resource files before testing: package fixtures enumerate
Git-tracked paths. Inspect the staged scope before running the gate.

## Release comparison baseline

Before each release build, verify and record the preceding published release on
both providers. Its tag object and commit must agree. Set that exact tag as the
comparison baseline and keep it set for every rebuild, including after merge.

For the prepared v1.18.1 patch, compare against published v1.18.0. The
controller verified both providers at preparation: tag object
`07259eb5a636d04688c12da89e3196ba5ff2a9a2` points to commit
`66507aa201ea6cac59d35fd99d38d19c085b95d3`. Reverify remote parity before
publication; this recorded preparation evidence is not a permanent live check.

```bash
export CORE_PROMPTS_RELEASE_BASE_REF=v1.18.0
bin/capability-fabric build
```

v1.18.1 publication is additionally held until the original vague and supplied-proposal comparison AGY
cases (`agy-2-vague` and `agy-3-competing-ideas`) meet their unchanged acceptance criteria with the reviewed cleanup repair.
Retain failed/incomplete runs and their consumed reservations. Deterministic tests,
prepared version bytes and successful source delivery do not waive that gate.
Do not tag or publish solely because the package can be built.

For another release, replace that value with its verified preceding published
tag. The generator supports this explicit baseline and otherwise selects the
latest distinct ancestor tag available locally. Fetch and verify the intended
baseline without replacing unrelated local tags. Missing tags can produce an
older cumulative comparison; resolve that gap before accepting the release view.
Check the recorded basis in `docs/RELEASE-DELTA.md` before packaging. Regenerate
this view instead of hand-editing capability counts or historical release notes.
Repeat the export in a new shell so later builds retain the reviewed baseline.

## Installation Preview (When In Scope)

After the baseline-bound build above, follow [installation preview and apply](INSTALL-PROFILES.md#preview-and-apply)
when installation is part of the release scope. Review the exact selection,
actions, preservation results, and blockers before applying the plan. A package
release alone does not require a home installation.

## Package
```bash
scripts/package-surfaces.sh --version "$(tr -d '[:space:]' < VERSION)"
```

`VERSION` is the canonical package version; a prepared value does not establish publication. Packaging fails if `--version` does not match `VERSION`, if the top `CHANGELOG.md` entry does not match `VERSION`, or if a nonempty `Unreleased` section remains. It also verifies the standalone runtime inventory before creating output directories or archives. A stale inventory fails with the mismatched path; packaging does not regenerate or repair it.

## Packaged Boundary
The package should include:
- generated surfaces under `.codex/`, `.gemini/`, `.claude/`, `.kiro/`, `.grok/`
- `.meta/manifest.json`
- `.meta/capability-handoff.json`
- `.meta/capabilities/`
- `.meta/install-bundle.json` and `.meta/install-profiles/`
- evaluation, clarity, descriptor, and plain-English job-map policy under `.meta/`
- `dist/consumer-shell/`
- `sources/ssot-baselines/`
- deploy/install scripts, the generated `scripts/deploy-profile.py` installation capsule, and `scripts/eng-report.py`; installed runtime execution is independent of the source checkout
- release-watch updater scripts, `VERSION`, and `RELEASE_SOURCE.env`
- any retained legacy local source checkout metadata; new-engine release acceptance does not advance a development checkout
- curated operator/integrator docs, including `docs/SKILL-FLOWS.md` and
  `AGENTS.md` with its packaged `.kiro/steering/` dependencies
- primary onboarding links resolved inside both archives; authoring `ssot/` and
  retained prompt donors are explicitly linked to the source repository
- generated consumer-shell docs (`docs/CAPABILITY-CATALOG.md`, `docs/RELEASE-DELTA.md`, `docs/STATUS.md`)
- capability-evaluation and Skill Job Map documentation
- `README.md`
- `CHANGELOG.md`

The package should not include:
- `.codex/config.toml`: generated local agent registrations can contain absolute checkout paths; keep this ignored local file and regenerate registrations at the installation target
- `.planning/`
- `reports/quality-reviews/`
- stray local artifacts such as `.DS_Store`

Both archive formats and standalone runtime inventories/copies exclude local Codex registration configuration. A runtime inventory claiming this local file is rejected; agent registration still generates configuration at the installation target. ZIP creation uses a fresh temporary archive before replacing the output, so excluded or retired members cannot survive from an earlier package with the same filename.

## Instruction context in both archives

The archives retain the exact canonical `AGENTS.md`, `agent-behavior.md` and
`repo-workflow.md` bytes. Their context guard separates a complete source checkout,
a verified distribution and an incomplete/ambiguous layout, including the
always-loaded steering path. Missing Git metadata alone does not select archive
mode. See the [first context check](GETTING-STARTED.md#check-your-core-prompts-context).

A distribution deliberately omits `ssot/`, `.meta/surface-rules.json`,
`scripts/build-surfaces.py` and `scripts/validate-surfaces.py`. Its bundled skills,
resources and portable installer support authorized use under the user's project
rules; authoring Core-Prompts requires a separately verified source checkout.
Runtime inventory checks remain mandatory, and all installation/publication holds
remain unchanged. TAR/ZIP tests check instruction bytes, context clauses, retained
source obligations and actual layout/inventory contents. These static checks do
not establish model compliance or native behavior.

## Shared-resource consumer packages

An importing skill ships as one complete generated package: its `SKILL.md`,
resource map, import-aware loader, imported resource bytes and
`resources/shared-resource-imports.json` provenance receipt travel together.
For `engos-design-architecture`, this includes the unchanged SpecContract schema
owned by `engos-design-specify-change`. The consumer is self-contained at runtime;
it does not search a source checkout, download the schema or require the owner
skill to be installed. Generated consumer copies are intentional delivery outputs,
not authored duplicates to remove.

Keep the loader, `shared_imports` declaration and `SharedResourceImportReceipt.v1`
in the same package replacement. An older loader rejects the new map field;
a missing or inconsistent receipt fails closed. Do not assemble a release from a
new map and an older loader, or omit imported bytes from either archive format.
Existing no-import packages retain their compatibility. A local receipt proves
consistency with bundled bytes; trusted package identity and canonical validation
provide the separate provenance checks.

When the owner changes, deliberately update the registry digest, regenerate the
consumer bundles and renew affected review/evaluation bindings before packaging.
Rollback restores the matching route, import declaration, registry binding and
instructions together, then regenerates and renews evidence. Follow the exact
[source-update and rollback procedure](CLI-REFERENCE.md#source-owned-shared-resources).
Keep whole-package replacement and recovery within the existing
[installation transaction](INSTALL-PROFILES.md#preview-and-apply); this contract
adds no installation selection or runtime sibling dependency. Documentation of
this package boundary is not evidence of a release or home installation.


The test-oracle reference has one canonical owner: D7,
`engos-quality-testing-review`. Its physical bytes enter the standalone D5
`engos-delivery-implement-slice` bundle through `test-oracles-v1`; D5 contains no
authored shadow copy and does not fetch a sibling at runtime. Detached D5 checks
its pinned snapshot, not the newest owner version. A changed D7 owner hash makes
the import stale until reviewed registry regeneration. The collector and optional
verifier remain owned by `engos-quality-code-review` and are used only for an
explicit committed-package request. These source changes do not claim publication,
main installation or release.

The trace package imports exact TaskPlan, TaskContract and TestDesign bytes
through a finite reviewed registry. Its narrow TaskPlan sibling-reference
exception requires explicit same-owner paired bindings, identical placement,
and direct owner and consumer dependency edges at canonical admission. Detached
validation checks its local receipt, bytes and consumer closure without looking
up the absent owner map. This establishes consistency; externally trusted package
identity is required to detect a self-consistent receipt and byte replacement.
Remote, traversal, dynamic, fragment and base-changing references remain
forbidden.

## Installation runtime verification

The editable installation engine is `scripts/core_install/`.
`python3 scripts/build-install-runtime.py` deterministically regenerates the
shipped `scripts/deploy-profile.py` capsule. Verify source/capsule parity before
building the bundle inventory. The standard build generates the capsule first,
then refreshes `.meta/install-bundle.json` through the existing inventory builder.
The capsule preserves the older v1.14 runtime path
allowlist; the modular source tree is not required at installation runtime.

Historical package recognition comes from the checked-in
`.meta/install-profiles/legacy-installations.json` catalog and its pinned
`legacy-release-refs.json` provenance. Source review must verify those release
identities; target-authored manifests do not establish ownership. Hash checks bind
the trusted package contents and modes, without claiming signed-release trust.

The migration candidate requires separate evidence for receipt-less historical
skills and agents, saved-profile conversion, missing-updater bootstrap, supported
old-engine bridging followed by the next invocation, repeat routine updates,
preserved conflicts, recovery, and both archive formats. A package's successful
extraction does not establish authenticated Kiro discovery, a home installation,
or hosted CI. Keep current run results under `reports/installation-migration/`;
this checklist does not assert that those gates have passed.

## Remote CI
Do not call the repo release-green until the hosted CI surface is green after push.

The GitLab Python container explicitly installs `zip` for the archive tests; GitHub's hosted Ubuntu runner already provides it.
GitLab also disables the Docker runner's permissive checkout umask and builds with `umask 022`, so recorded file modes survive safe TAR extraction. See [GitLab runner feature flags](https://docs.gitlab.com/runner/configuration/feature-flags/). Installer byte and mode verification remains strict.

- GitHub Actions:
  - runs on pushes to `main` and `AI/**`
  - runs on `pull_request`
  - refreshes external CLI schema/docs references as a non-blocking drift signal
  - validates generated repo surfaces with strict local checks while skipping live schema cache enforcement
- GitLab CI:
  - runs on branch pushes
  - runs on merge request pipelines

Both providers verify the committed installer inventory immediately after test
dependencies are installed, before any source-generating tests or build. They
validate the checked-in surfaces before building the distribution views required by the archive tests. This preserves drift detection on fresh checkouts.
Both pipelines also run five focused pre-generation regressions for the README
skill count, Batman advisory authority, a protected pilot marker and UAC
descriptor preservation/refresh. These fixtures use the existing Python test
dependencies and require no native provider command.

Local release gates retain `bin/capability-fabric validate --strict`, including schema cache checks, so transient hosted network or vendor-doc failures do not mask local schema drift review.

When using `validate --with-cli`, native validator results also honor error-output patterns declared in `.meta/surface-rules.json`. Kiro CLI 2.21.1 can print an `Error:` diagnostic while returning zero; this is a failure, including when ANSI color codes surround the diagnostic. The Kiro reference set includes the current configuration page and the versioned CLI 2.x reference; it does not imply that a CLI 3.x migration was performed.

## Recommended Release Order

The v1.18.1 preparation alone does not authorize merge or these publication steps. The
[publication and live-rollout hold](#publication-and-live-rollout-hold) must be
resolved before creating or pushing matching tags. The target is the future
reviewed release-preparation merge SHA with exact-SHA hosted checks and parity,
not the earlier source-main commit or this unmerged preparation branch.

1. run the local release gate
2. push the branch and wait for GitHub Actions and GitLab CI to go green
3. merge only after the hosted checks are green
4. verify `VERSION`, `CHANGELOG.md`, docs, and updater help all describe the same shipped version and release-watch contract
5. build the release package from the merged state
6. create the tag and push the same tag object to GitHub and GitLab
7. publish the release artifacts and checksums on both remotes
8. when installation is in scope, accept or install the released version, then verify installed `VERSION`, surface parity, release-watch state, and rollback metadata separately from repository release evidence

Publication verification includes independent downloads from both providers, as required by the [verification expectations](../.kiro/steering/repo-workflow.md#verification-expectations). The downloaded checksums and archives can be compared with the reviewed package digests and expected file/mode boundary. A successful CLI exit can still accompany an authentication page or other unexpected content; in v1.14.0 verification, authenticated upload-API downloads were needed to establish the private GitLab assets' byte identity. This is a content-verification lesson, not a claim that every download needs the same transport workaround.

## Installed Release Watch Contract

Normal installation supplies `~/.core-prompts-updater/` and
`~/update_core_prompts.sh` even when no updater existed before. The bundle includes
`VERSION`, `RELEASE_SOURCE.env`, portable runtime inputs, and generated packages.
The concrete selection and ownership live in
`~/.core-prompts-state/installation.json`.

`--check-release` checks canonical remotes, prepares the clean release mirror,
and records release-watch state without installing. New-engine `--accept-release`
uses that verified mirror and the saved installation selection in a recoverable
transaction. It does not advance the development checkout. Preserved package
conflicts return exit `2` and need attention even if runtime files were refreshed.
Optional retained consumer views are not certified current by runtime parity.

Existing schedules are preserved. Explicit `--schedule-daily HH:MM` creates or
changes a schedule; scheduled runs check first and auto-accept valid releases by
default. `--notify-only` disables automatic release acceptance while retaining
routine sync of the existing bundle. Scheduled runners supply
a deterministic executable path, and saved selections survive missing CLI
binaries in non-interactive environments.

A compatible older engine can receive the new capsule through its existing
allowlist; that invocation remains old-engine execution. The next invocation
uses the new engine. Older engines that reject changed scope need the current
installer once. Do not claim universal self-upgrade support or imply that a
missing-updater installation first needs a separate updater refresh.

New recovery journals live under `~/.core-prompts-state/install-transactions/`.
`--list-snapshots` and `--rollback previous` expose them through the existing
updater. Recovery checks exact package and installation-state identities, with the
[release-watch observation exception](INSTALL-PROFILES.md#recover-an-installation).
Journals remain retained, with advisory `retention_candidates` beyond the latest
two and no automatic pruning. `--snapshot-retention` applies only to older
snapshot compatibility paths. See [installation and recovery](INSTALL-PROFILES.md)
for reviewed repair and rollback commands.


### Resource-backed mode contracts

When adding capability resources, compare canonical and bundled per-mode descriptions, inputs, outputs and examples against the reviewed prior descriptor. The shared apply/build resolver retains matching curation over heading defaults while refreshing source identity, locations and invocations. Package byte equality alone cannot reveal a contract lost in every copy; review the before/after contract as well. See [UAC mode metadata](UAC-USAGE.md#mode-metadata-when-adding-resources).

## Program adoption readiness

The 32→36 source catalog adds four software jobs; future same-36 helper refreshes
need their own exact-byte and behavior evidence. Existing selections do not expand
without explicit [full/curated policy](INSTALL-PROFILES.md#choose-future-skill-membership).
Build the capsule and install inventory together from canonical installer sources.
State3 is accepted only by the new runtime; historical scope guards remain intact.
Keep package, detached updater and rollback evidence distinct. The source emits
five provider distributions; Antigravity is a sixth installation reader of the
portable Gemini package, not an extra generated tree. Runtime targets and native
case results need an explicit version-bound matrix. Historical Gemini CLI results
do not transfer to Antigravity; see the [unresolved root qualification](INSTALL-PROFILES.md#antigravity-cli-agy).
### Qualified adoption scope

Published v1.17.0 established the 36-skill catalog under the qualified
source-package and controlled-upgrade scope below. Published v1.17.1 retains that
catalog and skill names, membership and agent-surface boundaries. It clarifies
the existing implementation planner's unknown completion state and exact inline
plan binding; that wording change requires its own scoped native confirmation.
The landed installer fixes address shallow shared-root observation, shared-reader
consent for entrypoints in empty directories, exact missing-owned Grok recovery,
and its descriptor, publication, durability and FIFO safeguards. The earlier
qualified adoption evidence is retained with its original limits; it does not
substitute for current candidate checks or waive or regrade any native test.
Published v1.18.0 added `engos-route-intent` as the 37th skill, with contained routing,
on-demand references and receipt-owned rename support. Catalog growth does not
expand saved concrete membership or establish installation, discovery or task success.
Prepared v1.18.1 retains these 37 skill identities; cleanup and numerical-resource
repairs have separate current acceptance gates.
Historical native acceptance remains **18/25**, with the original cells and criteria unchanged.
No new native provider run or universal provider acceptance is claimed.

Controlled upgrade evidence covers six authentic owned 32-skill selections through
ordinary 32, explicit 36 and unchanged-repeat workflows. A4 retirement/recovery
acceptance reuses qualified synthetic evidence; it is not proof of universal
historical migration or live retirement. A5 accepts qualified manual package
loading for agy, not global catalog/slash-command discovery. The documented
checkout route is a path-only adaptation and has not been replayed as a native
acceptance run. Missing access remains a blocker; no trust/authentication change
is implied. Those earlier unresolved-root observations do not establish the
effective destination of another host/version. Global use requires its own bound
discovery, package, destination and authorized-write evidence. See the exact
[manual-use limits](INSTALL-PROFILES.md#temporary-manual-use-from-a-checkout).

These are source/package and controlled-adoption claims, not comparative skill
benefit, model superiority, installed-byte parity or fresh task success. Exact
candidate and merged-main hosted CI, reviewed archive contents and published
asset readback remain distinct release gates. Source/main checks do not authorize
publication, a tag, retirement, rename or home install.

### Publication and live-rollout hold

**Preparation alone authorizes no tag, publication, live installation or runner
restoration.** Each action requires its own authorization and verified gates;
any separately held runner stays held until explicitly restored. Dated execution
receipts, not this guide, establish a particular target's applied state.
v1.17.0 was published on both providers on 2026-10-17 from
`d76f1ff2761348b7fc7ed8a11f438765a6065c39`. That publication supersedes its historical
preparation-time tag/asset hold only. It does not establish installed parity or
authorize another release, a live install, a schedule change or AGY global use.

The watcher can discover matching remote tags before hosted assets exist. The
2026-10-16 assessment identified a daily 09:00 auto-accept path and six saved
32-skill readers, including agy. That historical exposure record is not current
scheduler-state proof or evidence of an applied release. Any separately held
runner remains held; this candidate does not restore it.

Publication needs separate authorization, fresh schedule/selection readback and
reviewed controls for tag-triggered acceptance. Reading or following the
preparation guide grants no schedule, global-profile, authentication, trust or
live-apply authority. Installer/updater changes are recorded in the changelog;
source preparation alone does not apply them to a host. Do not infer provider-selective safety from an unscoped
acceptance command. Merge remains a separate review decision. The eventual tag
target is the reviewed release-preparation merge SHA after parity and hosted gates;
version metadata and local package creation alone do not establish a release.
Historical references to `RELEASE.md` belong to this document; no obsolete alias
is recreated.

## Shared discovery and missing-package recovery runtime

Installer changes to shallow shared-root observation and exact Grok recovery travel in
the regenerated `scripts/deploy-profile.py` capsule and verified install-bundle inventory.
Validate source and extracted-distribution execution, both wrappers, selected/source
symlink guards, stale plans, exclusive recovery claims, no-clobber file publication and
journal rollback before publishing a runtime. A source fix or reviewed PR does not
update an installed runtime, approve a live plan, resolve protected packages, or resume
a held runner. Generate a fresh plan with the separately verified delivered engine.
See [exact recovery](INSTALL-PROFILES.md#restore-wholly-missing-owned-grok-skills).


Explicit unowned Claude skill adoption ships in the generated installer capsule;
run `python3 scripts/build-install-runtime.py --check` and the focused replacement,
transaction, capsule and bundle tests before packaging. These operations produce
schema3 transaction journals. Retain a compatible installer for rollback; older
engines reject these journals. Follow the [manifest-bound replacement contract](INSTALL-PROFILES.md#explicit-replacement-of-unowned-claude-skills)
for separate owner approval, installed after-image and subsequent scoped-sync
acceptance. Source landing or archive creation does not prove live adoption.

The same runtime includes planned Python cache retirement. Verify a real installed
helper import followed by ordinary scoped sync, inspect `cache_retirements` and
its before-image backups, and retain modified/unknown caches as conflicts. A
source test with bytecode globally suppressed does not satisfy this acceptance.
