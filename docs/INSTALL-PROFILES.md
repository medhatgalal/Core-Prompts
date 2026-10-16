# Install, migrate, and recover Core-Prompts

Use the current installer from a trusted release or verified source checkout for
fresh installs and historical repairs. An older installation does not need a
standalone updater, profile, or ownership receipt before it can be inspected.
The installer supplies the updater when absent. Scheduling remains a separate
opt-in step.

Author capabilities in `ssot/` and canonical resources; installed directories are
destinations, never authoring sources. Generated repository surfaces remain
available for every supported provider regardless of local installation selection.

## Upgrade from verified main before the next release

A source merge does not update installed skills. The release watcher follows
matching immutable release tags; it does not fetch unreleased `main`. A matching
tag can be accepted by an existing schedule before release assets are published;
see the [publication and live-rollout hold](RELEASE-PACKAGING.md#publication-and-live-rollout-hold). To adopt the
latest accepted source before a release, use the current installer from a trusted
checkout once. An older installed updater is not a substitute for this step.

First inspect the checkout and its remote:

```bash
git status --short --branch
git remote get-url origin
```

Keep local work intact. If the checkout has changes or `main` has local commits,
resolve that separately before continuing; do not reset it to force an upgrade.
The following example uses `origin`; substitute your trusted Core-Prompts remote
if it has another name:

```bash
git fetch origin main
git switch main
git merge --ff-only origin/main
git rev-parse HEAD
```

Record the resulting commit. A failed fast-forward needs inspection, not a forced
update. Run the preview below from that checkout. The installer checks its runtime
inventory before planning; an identity mismatch means this source is unusable.
Obtain a corrected verified source rather than rebuilding hashes to bypass it.

For a saved 32-skill installation, ordinary sync refreshes its selected packages
and resources but keeps 32 members. To add the four new skills, explicitly choose
[full-catalog membership](#choose-future-skill-membership), or keep `curated` and
add only named skills. Preview and apply from the same source and target. Review
preserved packages afterwards; a preserved copy may still contain older content.

After an authorized apply, verify installed package/resource identity, then use
the [first-use checks](GETTING-STARTED.md#fast-path-use-what-is-already-available)
and [skill flows](SKILL-FLOWS.md). Native discovery and a successful task are
separate observations. See [recovery](#recover-an-installation) for the exact
transaction rollback path. Source-only work or an installation hold stops before
apply; refreshing the checkout alone changes no live skills or schedules.

### Copyable AI upgrade handoff

> Inspect this trusted Core-Prompts checkout and my selected installation scope.
> Keep unrelated work and customized, unowned or ambiguous packages intact.
> Identify the source commit and saved provider/skill membership. Preview with
> the current source installer, then show the exact additions, updates,
> preservations, recognized Core-agent retirements and blockers. Ask me to choose
> full-catalog versus curated membership if that intent is missing; do not expand
> a shared Codex/Gemini reader without explicit joint consent. Apply only within
> my installation authority using the reviewed plan. Report package/resource
> parity, preservation notices, native discovery and an observed first task
> separately. Do not release, schedule, change provider settings or force cleanup.
> Show the transaction recovery command and any remaining limitations.

## Preview and apply

From the trusted current release directory or verified source checkout, preview
an existing Kiro installation:

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
| Fresh target, `--cli kiro` | Install current Kiro skills. `--with-agents` selects only emitted agents, currently none. |
| Historical target without saved state | Recognize existing packages on selected providers, then migrate declared successors, including retired agent-to-skill transitions. `--repair` makes this intent explicit. |
| Saved schema 1 skills profile | Normal sync carries forward its selected skills; explicit `--repair` also discovers independently recognized existing agents on its selected providers. |
| Saved schema 2 installation | Routine sync keeps saved selection except declared retirement transitions. Explicit `--repair` discovers additional recognizable installed packages within scope. |
| Explicit `--slug SLUG` | Select that current capability's emitted skills and agents; repeat for multiple slugs. |
| `--surface-only --slug SLUG` | Manage the selected surfaces and ownership state without refreshing the updater or launcher. |

`--cli` accepts `agy`, `codex`, `kiro`, `claude`, `gemini`, `grok`, or `all`. On an initial
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

A newly supplied explicit profile with empty `slugs` selects current skills
once for its named providers. An automatically loaded saved empty profile uses
only the historical membership proven by its profile-bound ownership receipt.
Missing, tampered or unmappable proof blocks conversion before any writes; restore
the original receipt or review an exact concrete selection rather than editing it
to claim ownership. The resulting concrete selection is saved in
`.core-prompts-state/installation.json`; later new catalog entries are not
automatically added. Do not edit ownership receipts to grant ownership.

## Choose future skill membership

A complete saved list of 32 skills does not authorize the four additions in the
36-skill catalog. Routine sync keeps the prior concrete membership. Choose a
future policy explicitly when you want new skills to join later updates:

```bash
bash scripts/install-local.sh --target <fixture-target> --allow-nonlocal-target \
  --cli kiro --selection-policy full-catalog --dry-run > /tmp/core-policy-plan.json
bash scripts/install-local.sh --target <fixture-target> --allow-nonlocal-target \
  --apply-plan /tmp/core-policy-plan.json
```

Replace `full-catalog` with `curated` to freeze the currently selected skills.
A later `--cli kiro --selection-policy curated --slug engos-design-specify-change`
adds only that named skill. A fresh curated activation requires concrete slugs.
Switching full to curated retains existing selections; it does not uninstall.
An empty saved curated selection stays empty. Neither policy selects agents,
changes provider configuration or enrolls another provider.

Review `selection_before`, `selection`, `policy_before`, `policy_after`,
`membership_changes`, `legacy_choices`, `shared_exposure` and
`shared_resource_changes` alongside actions and preservation reports.
State schema3 records explicit intent; undecided installations retain schema2.
The transaction plan remains schema2, persisted journal schema1 and transaction
receipt schema2. Old schema2 engines reject state3 before writes. The policy flag
cannot combine with repair, agents, surface-only or transaction controls; apply
uses the policy embedded in the exact reviewed plan.

Codex and Gemini share `.agents/skills`: logical ownership is not native exclusion.
A mixed full/curated expansion blocks with `SHARED_SURFACE_POLICY_CONFLICT` if it
would expose skills beyond an affected reader's approved selection. To choose
full catalog jointly, supply a schema1 skills profile whose `targets` name exactly
the known shared readers, `slugs` is empty, and pass
`--profile <joint-profile.json> --selection-policy full-catalog`. Review the
physical union and both logical policy changes together. `--cli all` is not a
joint consent shortcut. Existing shared exposure is reported even when unchanged.
A joint curated profile lists concrete skills. Profiles cannot combine with
`--cli` or `--slug`.

The four additions are `engos-design-specify-change`,
`engos-design-plan-implementation`, `engos-debug-diagnose-failure`, and
`engos-delivery-implement-slice`. Updating a later helper inside an existing one
of the 36 packages is a resource refresh within saved scope, not another catalog
addition. Customized and third-party packages remain protected. A successful
runtime update or `applied-with-preserved` result does not prove their new bytes
or native invocation are active.

Use the current installer bridge when an archived engine refuses a changed
standalone bundle scope. The v1.14.0 guard and addition-only migration remain
unchanged; v1.16.3 capsule acceptance must be observed on the actual archived
engine. No universal old-version self-upgrade is promised. The new runtime is
written before schema3 state using the existing recoverable transaction. A failed
multi-file update needs its retained journal and rollback; later user edits or
invalid preimages block unsafe restoration. Installation, main landing, release
publication and five-provider native acceptance are separate evidence.

## Activate a released skill update

The v1.16.3 independent artifact-review examples apply after that released package
is installed for the selected provider and the requested skill has updated.
Publication, shared updater `VERSION`, saved selection and individual package
readback are distinct checks. A runtime update can succeed while a customized or
unowned skill is preserved and continues using its previous instructions.

One example of the pattern: update an existing saved selection from a verified
release directory without asking for another provider or a broader profile:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --dry-run > /tmp/core-prompts-release-install-plan.json
```

Inspect the exact `selection`, `actions`, preserved packages and blockers, then
apply that reviewed plan with the existing `--apply-plan` workflow above. Avoid
adding `--repair`, a new profile or extra slugs merely to activate these examples;
those choices change the discovery or selection scope described earlier.

After apply, read the installed runtime version and the requested skill's actual
package through the selected provider path. Confirm its review section and compare
its owned files with the released package's hashes and modes. Inspect the operation
and persistent preservation reports before saying the behavior is active everywhere.
For `applied-with-preserved` or `no-op-with-preserved`, report which selected packages
updated and which retain prior content. Preserve custom and third-party packages;
resolve any desired replacement explicitly through the existing ownership workflow.
An unreceipted third-party Loopy copy is not adopted by this update.

Keep the transaction ID and recovery metadata. Use [recovery](#recover-an-installation)
if the reviewed update fails; a published archive alone proves no home acceptance.

## Historical recognition and preservation

The checked-in `.meta/install-profiles/legacy-installations.json` catalog binds
complete historical package inventories to exact hashes and modes. Its source
release refs are recorded in `legacy-release-refs.json`. Recognition uses this
trusted catalog or an existing valid ownership receipt, not a target-authored
manifest. The catalog covers 56 pinned release versions; the historical 24-skill
population is one fixture, not a limit on supported current capabilities.

The exact v1.16.3 donor adds receipt-only membership records for historical
artifact-embed, frame-from-vague and Loopy packages. These records prove the scope
of a bound saved profile; they never authorize receiptless adoption of matching
copies. A saved v1.16.3 Gemini profile can own the shared `.agents/skills`
layout with canonical `.codex/skills` source identities: the archived engine
checked provider byte equivalence before creating that receipt. Migration maps
those trusted identities only to providers actually named by the saved profile.
Empty curated policy participants remain affected readers even with no selected
skills; a second provider cannot expose new shared skills without joint consent.
Malformed catalogs cannot promote receipt-only records into normal recognition
or duplicate inventory records across registry containers. The previous historical pin set and ownership behavior remain intact.

Each skill and agent is recognized independently. A recognized Kiro skill does
not authorize installing an absent Kiro agent, and a package on one provider does
not authorize another provider. Recognized `autosearch` packages migrate to
`engos-optimization-auto-research`; `mentor` has no successor and is retired only
when its package ownership is recognized and no unresolved dependency
requires it. Replacement files are verified before predecessor files are removed.

The v1.15.0 retirement (2026-09-15) covers all 11 first-party named-agent variants
on Codex, Gemini, Claude, and Kiro (44 entrypoints). The v1.16.5 release contains
32 skills; the v1.17.0 source preparation dated 2026-10-16 contains 36. Both retain
skills-only distribution; catalog growth alone does not expand a saved concrete
selection (see [future skill membership](#choose-future-skill-membership)).
The existing historical catalog and ownership receipts identify the affected
packages; no second registry is needed. A recognized owned retired agent maps
to the exact same capability's skill on the same provider. Its skill is retained
or installed before removal, including for an agent-only saved selection.
Routine updates also remove locally modified copies of the exact retired `engos-*`
identities when the definition name and bundled capability metadata identify the
Core-Prompts package. Exact `.bak` and `.bak.N` definition backups are removed too.
An existing customized skill is retained without being overwritten or adopted;
it does not keep an identified retired agent active. Symlinks, ambiguous identity,
configuration conflicts, and external file dependencies still stop affected removals.
Kiro Crew and other third-party agents are outside the retirement list.
Owned removals and registration updates use the existing recoverable transaction.
A source retirement alone does not clean an installation: apply and verify that
target's reviewed plan before claiming it has no remaining agents.

`--with-agents` remains a compatibility selector for emitted agent packages. It
selects none in the current inventory and cannot authorize UAC to create an agent.
Future added or reintroduced agent surfaces require explicit user approval and
independent execution-need review before they can be emitted.


Unknown and symlinked packages are preserved as whole packages, including partial
packages that fail ownership recognition. Customized skills and custom non-Core
agents remain preserved. Only local modifications are exempted from preservation
for exactly identified retired Core-Prompts agents; symlink, ambiguous-identity,
configuration, and dependency protections still apply as described above. During schema-1
receipt conversion, matching present files can establish ownership even when
receipted members are missing; the reviewed plan may restore those members.
Inspect the plan's exact actions before applying it. A custom successor normally preserves its predecessor; the explicit Core-agent
retirement above retains the custom skill and removes the agent. An unresolved
reference from another agent still preserves the affected predecessor. Codex registration changes preserve unrelated custom
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

For this skills-only transition, the tested v1.14 updater rejects the smaller
bundle with `standalone bundle file scope was removed; reviewed migration required`.
Its old `--migrate` path only adds files and cannot retire the removed agent files.
Use the **current installer once with `--repair`**, reviewing its dry-run JSON and
applying that exact plan as shown above. Do not claim that an old ordinary or
scheduled update has removed the agents. The current installer can bootstrap the
replacement runtime and perform the ownership-aware migration in one transaction.

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

The agent paths below are historical cleanup and future-adapter locations; the
current package emits no named agents.

| Provider | Installer destination (native discovery verified separately) | Agent root |
| --- | --- | --- |
| Codex | `.agents/skills/` | `.codex/agents/`, with target-local registrations |
| Kiro | `.kiro/skills/` | `.kiro/agents/` |
| Claude | `.claude/skills/` | `.claude/agents/` |
| Gemini | `.agents/skills/` | `.gemini/agents/` |
| agy | `.gemini/config/skills/` | No named-agent translation |
| Grok | `.grok/skills/` | No repository-generated agent surface |

Codex and Gemini share the portable generated skill package, including bundled
resources. Provider selection still controls agents and configuration. A scoped
skill update refreshes existing shared ownership records for both clients.
Recognized legacy `.gemini/skills` packages migrate through the exact installation
plan; customized copies are preserved. The repository still emits `.gemini/skills`
as distribution artifacts. Gemini settings and agents remain under `.gemini`.

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


### Automatic agent cleanup on update

Once this installer is installed, `~/update_core_prompts.sh` automatically reconciles
retired Core-Prompts agents in the saved provider scope. No archive command or
per-agent approval flag is required. Removals use the ordinary installation recovery
journal and fresh hash checks. A repeated update proposes no further cleanup.
Older installed updaters keep their older behavior until upgraded; a source merge
alone does not update them. Check the installed result before claiming cleanup.



## Antigravity CLI (agy)

The current repository installer accepts `--cli agy` and places the portable
Gemini skill package at `~/.gemini/config/skills`. This is the configured installer
destination, not a claim that every installed Antigravity CLI discovers it.
There are five generated distributions and six installer readers; no `.agy`
generated surface or named-agent translation is added.

A previously inspected embedded customization guide describes a global `.gemini/config` root and
project `.agents/skills` with project precedence, while the [current CLI skills
documentation](https://antigravity.google/docs/skills) lists
`~/.gemini/antigravity-cli/skills`. That historical guide is not proof of the current executable. The effective global root needs a version-bound
native probe before installation or migration is recommended. A changelog heading
or historical version label does not establish the running executable's version.
Do not reinterpret historical Gemini CLI evidence as Antigravity acceptance.

### Temporary manual use from a checkout

While the global destination is unresolved, a current package can be supplied
explicitly without installing it. For example, ask agy:

> Read `<absolute-Core-Prompts-checkout>/.gemini/skills/engos-design-specify-change/SKILL.md`
> and its selected package-local resources. Specify this change in our existing
> format; preserve unchanged behavior and keep open decisions visible.

Use the complete trusted package directory, not `SKILL.md` alone. Resolve resource
paths from that directory and invoke any helper by its absolute path or with that
directory as its working directory. This is a path-only adaptation of explicit
package loading, not native catalog or slash-command discovery, and the checkout
placement has not been replayed as a native acceptance run. If the host denies
checkout access, report the missing permission; do not silently change trust or
copy over an existing installation. Global installation, migration and cleanup
remain on hold until their destination and write set are verified.

### Investigate the global destination

For an authorized setup investigation, begin with the current installer preview:

```bash
bash scripts/install-local.sh --cli agy --target "$HOME" --allow-nonlocal-target --dry-run > agy-plan.json
```

Review destination, selection and preservation notices before any apply. Keep
application on hold while the native destination remains unresolved. The general
[preview/apply](#preview-and-apply) and [recovery](#recover-an-installation) workflows
apply once the intended root and write set have evidence and installation is in
scope. Explicit `--cli agy` adds current skills when selecting AGY as a new
reader. For an existing AGY reader with legacy or curated policy, repeating it
retains saved membership, including a saved 32-skill selection or an empty curated
selection. A saved full-catalog policy continues adopting current and future
skills during ordinary sync without restating the flag. Use
`--selection-policy full-catalog` to opt into that policy, or `--slug` to add a
named skill while retaining curated policy. These membership choices are distinct
from native discovery.

The executable is `agy`, not `agy cli`. Native `/skills` and `/<skill>` controls
are documented, but only an actual bound observation establishes discovery or
use. Record executable identity/version, working directory, effective skill root,
package digest and observed result. [Plan mode](https://antigravity.google/docs/cli/modes/)
is instruction-based and does not itself enforce read-only execution; configured
permissions still apply, including in [headless mode](https://antigravity.google/docs/cli/headless/).

Preserve existing `~/.gemini/antigravity-cli/settings.json`, `mcp_config`,
authentication, trust, plugins and permission settings. The skill installation
flow does not translate or grant these controls. This guide records the unresolved
root distinction without changing the installer or awarding native-test credit.
