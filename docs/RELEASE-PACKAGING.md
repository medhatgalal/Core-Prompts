# Release Packaging

This document defines the local release path for packaged Capability Fabric artifacts.

Preferred release runtime: Python `3.14`.
Minimum supported runtime: Python `3.11+`.

Prefer the repo wrappers for build and validate so the runtime selection stays consistent.

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

One example of the pattern: the v1.16.3 release compares against the verified
published v1.16.2 tag:

```bash
export CORE_PROMPTS_RELEASE_BASE_REF=v1.16.2
bin/capability-fabric build
```

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

`VERSION` is the canonical shipped release version. Packaging fails if `--version` does not match `VERSION`, if the top `CHANGELOG.md` entry does not match `VERSION`, or if a nonempty `Unreleased` section remains. It also verifies the standalone runtime inventory before creating output directories or archives. A stale inventory fails with the mismatched path; packaging does not regenerate or repair it.

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
- curated operator/integrator docs
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

Local release gates retain `bin/capability-fabric validate --strict`, including schema cache checks, so transient hosted network or vendor-doc failures do not mask local schema drift review.

When using `validate --with-cli`, native validator results also honor error-output patterns declared in `.meta/surface-rules.json`. Kiro CLI 2.21.1 can print an `Error:` diagnostic while returning zero; this is a failure, including when ANSI color codes surround the diagnostic. The Kiro reference set includes the current configuration page and the versioned CLI 2.x reference; it does not imply that a CLI 3.x migration was performed.

## Recommended Release Order
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
Missing mandatory native cases leave the program release on HOLD. Source/main
checks do not authorize publication, a tag, retirement, rename or home install.
Historical `RELEASE.md` resolves to this document; no obsolete alias is recreated.
