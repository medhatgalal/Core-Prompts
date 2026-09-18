# engos-quality-presentation-instruction-review

Actual independent reviewer: 01a0b418-c8a0-7b40-9d18-9a8112e6dbba.
Baseline bf6c44e; semantic scope is the five presentation candidates and routed
controller/author instructions, not concurrently implemented helper correctness.
Original findings and scoped recheck are retained below in chronological order.

Found four P2 instruction issues. The additions preserve authority, privacy and simulation boundaries explicitly, but leave conflicting obligations in these paths:

1. **Framed-only rendering still routes into a Shaped-only input contract.** Embed candidate:184–187 (historical private candidate `engos-delivery-artifact-embed.md:184`, not a published link) prohibits fabricated Shaped bundles, while its retained required inputs at line 37 demand a complete artifact bundle and workflow lines 75–76 reject incomplete bundles. Conductor candidate:142–144 (historical private candidate `engos-design-shaping.md:142`, not a published link) also routes Framed presentation through author guidance belonging to a skill whose required input is a shaped solution. Define an explicit Framed input/representation route that bypasses Shaped completeness requirements. Distinguish local rendering from any separately authorized publication; the existing publication route still requires G3.

2. **Standalone framing acquires a mandatory conductor dependency.** Frame candidate:115–116 (historical private candidate `engos-design-frame-from-vague.md:115`, not a published link) says to ask the conductor for progress, without qualification. Its retained lines 40–42 explicitly support direct use without a runtime or gate. Condition projection retrieval on an existing run/conductor; otherwise report an unaccepted draft and unavailable gate state without creating a workflow solely for status.

3. **Mandatory PNG generation conflicts with the retained conditional rendering rule.** [Presentation reference:14–18](../../sources/capability-resources/engos-delivery-diagram-contract-artifacts/references/presentation.md) (review-time line 14) requires both SVG and PNG. The author candidate:102–104 (historical private candidate `engos-delivery-diagram-contract-artifacts.md:102`, not a published link) permits SVG-to-PNG only when the target cannot accept Mermaid or SVG. Because presentation guidance is loaded by the shared author route, this also affects standalone native-Mermaid requests. Scope mandatory derivatives to the selected rich presentation profile and explicitly reconcile the older rule.

4. **Authoring guidance requires downstream saved-target inspection.** [Presentation reference:35–39](../../sources/capability-resources/engos-delivery-diagram-contract-artifacts/references/presentation.md) (review-time line 35) unconditionally requires inspecting every required target, including saved document pages. The retained author handoff:174–178 (historical private candidate `engos-delivery-diagram-contract-artifacts.md:174`, not a published link) requires local render evidence before review and permits placement only after G3. Applied during authoring, the new obligation creates a circular prerequisite and crosses the author/publisher boundary. Assign local visual inspection to authoring/G3 and saved-target inspection to the publisher/G4.

Required final interface checks, once concurrent implementation settles:

- Bind candidates, resource maps, schemas and actual helper commands to consistent revisions; verify Framed-only, Shaped and standalone inputs separately.
- Verify projection fields and behavior for accepted versus draft revisions, queued versus observed activity, stale attempts, corrupt/missing state, simulation, stopping points and remote freshness. Status reads must not advance gates or publish.
- Verify SVG validation, source/asset hashes, curated-layout provenance, field-preserving table mappings and profile-specific dependencies.
- Verify local presentation evidence remains separate from target delivery receipts, with target-specific authority, preserved edits and no implicit sharing.

Reviewed read-only using the complete skill-creator guidance. No edits, network, nested workers or installed/global changes. Unfinished helper behavior and transient missing resources were not treated as defects. This is semantic review, not UAC promotion.

---

All four findings are resolved at the instruction level. No material residual findings in the bounded recheck.

1. **Framed-only routing:** The embed candidate, lines 37–42 and 82–86 (historical private candidate `engos-delivery-artifact-embed.md:37`, not a published link) explicitly limits inputs and completeness checks to framing prose and local output. The conductor, lines 142–146 (historical private candidate `engos-design-shaping.md:142`, not a published link) explicitly excludes invoking the Shaped author for Framed output.

2. **Standalone progress:** The frame candidate, lines 115–118 (historical private candidate `engos-design-frame-from-vague.md:115`, not a published link) conditions projection use on an existing conductor run and preserves standalone unaccepted drafts without creating a runtime.

3. **Requested derivatives:** The author candidate, lines 102–105 (historical private candidate `engos-delivery-diagram-contract-artifacts.md:102`, not a published link) and [presentation reference, lines 14–22](../../sources/capability-resources/engos-delivery-diagram-contract-artifacts/references/presentation.md) (review-time line 14) now scope derivatives to the request/profile and preserve native-Mermaid-only use.

4. **Inspection ownership:** The [presentation reference, lines 38–44](../../sources/capability-resources/engos-delivery-diagram-contract-artifacts/references/presentation.md) (review-time line 38) explicitly separates local author/G3 inspection from subsequent authorized publisher/G4 inspection.

The repairs preserve target-specific publication authority and privacy restrictions, standalone artifact scope, and the distinction between observation and acceptance. [Progress guidance, lines 21–36](../../sources/capability-resources/engos-design-shaping/progress.md) (review-time line 21) retains controller-bound observations, simulation disclosure, remote-freshness limits and explicit external-update authority.

Final binding checks remain: actual Framed profile inputs/outputs and receipt semantics; profile-specific asset validation and provenance; projection schema/command compatibility and stale-state behavior; and local-versus-saved-target evidence separation. Helper implementation was not inspected or verified in this recheck.

Read-only semantic review; no UAC promotion verdict.
