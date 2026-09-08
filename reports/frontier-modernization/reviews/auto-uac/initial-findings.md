# Auto-Research and UAC independent source review

Reviewer: `review_autoresearch_uac_admission`. Authors: `implement_skills` for Auto-Research and `root` for UAC. Scope is candidate source, current and historical baseline preservation, and Auto-Research resources. No source/code mutation, experiment, deployment, delegation, or behavioral promotion is part of this review.

First-pass decision: revisions required. These findings preceded inspection of any author grade or change map.

## Substantive findings

1. **AR-R1: The mandatory experiment resource is absent from effective-content binding.** Auto-Research has a new required `references/experiment-loop.md` but no `resource-map.json`. `effective_capability_text` therefore returns only the entry text. A review could remain apparently current after the execution contract or templates changed. Declare the loop, helper, and template dependencies and include them in the effective hash before attestation.
2. **AR-R2: The new agent resource path has an extra segment.** Mode 4 asks an agent to resolve `resources/references/experiment-loop.md` relative to the directory containing `capability.json`; agent bundles place that descriptor at the resource root. Resolve `references/experiment-loop.md` beneath that root, while retaining the skill-relative path for skill surfaces.
3. **UAC-R1: `judge` loses its explicit no-landing boundary.** Current baseline workflow step 11 requires reports without landing repo state. Candidate step 11 replaces that with mechanical repairs and leaves the repair destination unclear. Preserve the prohibition on canonical writes and limit repairs to staged candidate/report artifacts.
4. **UAC-R2: The historical apply sequence is not fully represented.** Historical baseline line 61 requires canonical SSOT plus descriptor writes, persisted quality reviews, then rebuilt and validated generated surfaces. Preserve this sequence alongside the newer structural and behavioral gates. Naming `capability-fabric` among entrypoints does not establish that these actions are required.
5. **UAC-R3: Output and contradiction scope need explicit qualifications.** U02/U03 require operative output-contract checks and contradiction review under applicable scope and precedence. The candidate says to inspect outputs and contradictions, but does not explicitly separate quoted examples from obligations or active-resource conflicts from apparent differences resolved by scope. Qualify the existing judge rule instead of appending generic source obligations.
6. **UAC-R4: Advisory delegation prohibition conflicts with the new review process unless scoped.** The retained universal instruction to never make orchestration or delegation decisions can be read as prohibiting the new separate-subagent semantic review. Preserve the restriction on imported runtime/control-plane policy and identify that the host invoking agent supplies independent review.

## Content already supported

Auto-Research A01-A06 are substantively present in the source and loop resource: actual trial execution; immutable baseline/incumbent/trial identities; joint hypotheses; protected measurement; objective-based acceptance with invalid trials distinguished from regressions; and continuation after both wins and losses until a declared limit. Diagnosis retains its early stopping exception. Resource-binding and resource-path findings prevent the first-pass package approval.

UAC retains its sources, modes, classification, canonical SSOT/descriptor boundaries, companion routing, required outputs, apply/deploy distinction, and structural/behavioral distinction. Targeted repair, independent review, exact requirement bindings, resource validation, stagnation, idempotence, and explicit issue dispositions are added. These statements are source-contract findings; UAC implementation and behavioral efficacy require separate evidence.

## Intermediate candidate identities

- Auto-Research: `f9d3574fad092eb9b62c26dd4c2dd76efdd0b99d089b1dd68fd839efac1634a3`.
- UAC: `8b3a8cba6c6eb5ac8477bb9cabacd4d84405bd125bc5fb8e5e01a3ea30ed9b42`.

These identities were captured while the authors were applying the reported corrections; they are not frozen reproductions of every first-pass defect. Final attestations bind the revised exact candidate and effective content after the complete re-review.
