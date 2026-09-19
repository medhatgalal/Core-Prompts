# engos-delivery-shaping-upstream

## Conflict summary and inversion

Integrate origin/main4e22178 into shaping branch after explicit gated-landing
approval. Losing upstream Supercharge5.1/catchup fixes, dropping either CI suite,
or publishing stale generated hashes would make this integration incorrect.
Do not alter the read-only primary checkout or confuse integration with landing.

## Comparison and resolution

Upstream carries releasedv1.15.2 and its Supercharge/resource-delivery tests.
The task branch carries the unreleasedv1.16.0 shaping source, tests and docs.
These are additive intents, not competing product designs. Retain prepared
VERSIONv1.16.0, retain the completev1.15.2 changelog immediately below it, and keep
both resource-backed-skill and shaping regression selections on both CI providers.
No tag or release is created by this version-file choice.

## Observed integration repairs

First affected-suite run:2failed/144passed. The newly added upstream inventory
test included local __pycache__/.pyc files, whereas the existing generator excludes
them. Align the test with that exact exclusion; a focused fixture retains genuine
.py/.md resources. No caches or user files deleted, no shipping of interpreter data.

The new per-route test also found that export.md's skill-root command examples
looked like required instruction-resource links to the strict loader. Document
the actual resources-directory working directory and resource-relative script
commands, retaining the separate tools route. Do not weaken the loader or force
every export instruction read to load the entire implementation. Add absolute
artifact-path guidance so outputs remain in the authorized project home.

Same-slug embed UAC plan/judge/apply passed structural_ready for the unchanged
entry with corrected canonical resource; regenerate all provider copies. Independent
reviewer01a0b93c-b8ba-79a0-b52c-aef7c9878e54 found noP1/P2 in resolutions/repairs.
After generation froze, the affected suite passed147tests, including all declared
routes across five providers. Strict32-entry validation and contract/topology
checks pass. This is integration evidence, not original pilot completion.

Regenerate install-bundle, manifest and consumer docs from merged canonical source;
never resolve derived hashes/counters by hand-picking a side. Supercharge SSOT and
descriptor/resources merge from upstream; shaping canonical changes remain.

## Verification and remaining risk

Run conflict-marker scan, generated validation, both affected regression families,
then final exact-head hosted checks. No merge-to-main readiness claimed until the
original pilot and both required saved surfaces pass. Pilot uses separately pinned
private inputs; integration does not rewrite those receipts or source identities.
