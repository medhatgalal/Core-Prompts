# Phase resource routing

Read only the selected route plus its declared dependency closure in
`resource-map.json`; do not load every phase at start. Complete every selected
read. A route name is a retrieval selector, not a command or permission grant.
Load an additional route when its trigger occurs and record why in the work order.

Resolve each skill through the host registry or explicit controller-supplied
candidate binding: skill identity, entry file, resource root, revision/hash and
selected route. In this bundle, `registry(<slug>).resource_root` denotes that
resolved resource root, not a literal path, shell expression or registry API.
Use package-relative paths inside that root. Read the actual SKILL and required
resources before use; do not substitute memory or silently mix candidate and
installed versions. Record missing or conflicting bindings as dependencies.

| Trigger | Cross-skill read/action |
| --- | --- |
| Intake or frame | `engos-design-frame-from-vague` SKILL and matching resource route |
| Stage acceptance | `engos-quality-shaping-gate` SKILL and its current gate/receipt policy; rubric when applicable |
| Runtime invocation or recovery | Gate resource map's `runtime` route and selected `runtime.md`, then resolved `scripts/shaping_run.py --help` using the documented interpreter; subcommand help before execution |
| Shaped bundle | `engos-delivery-diagram-contract-artifacts` SKILL and its selected authoring/style resources |
| Independent pitch assessment | `engos-audit-pitch-review` SKILL plus the gate owner's current full-shaping integration and calibrated rubric |
| Approved placement | `engos-delivery-artifact-embed` SKILL and target-specific resources |
| Missing capability | This bundle's `fallback` route |

Do not encode trial-local paths, source failures or CLI workarounds in policy.
Record them in the run. Runtime interface documentation and canonical review
integration must agree with the bound work order before dependent acceptance.
No new agent registration, permission system or implicit external sharing follows
from resolving a dependency.
