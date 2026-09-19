# engos-quality-implementation-instruction-review

Actual independent review. Markdown trailing hard-break whitespace normalized; wording retained. Historical source hashes are not upgraded after repair.

Review complete: three P2 instruction defects need correction. The dimension-specific rubric interpretation is sound for these synthetic controls; this is neither G3 approval nor formal calibration/promotion evidence.

Reviewed at HEAD `59488c0401e2d887f02a3f06af65387cd6f22f7b`. No writes, cloud calls, commits, implementation, or additional agents. Mutable scripts and `runtime.md` were excluded as requested.

1. **P2 — Conflicting workstream filename and ownership.**
   The conductor’s [template](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-design-shaping/templates/shaped-bundle.md:12) requires `epic-breakdown.md`, which the shaper produces as part of its complete bundle. The artifact helper’s [bundle resource](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-delivery-diagram-contract-artifacts/references/bundle.md:8) instead says the conductor supplies `workstreams.md`. No alias or mapping connects them. This can cause missing handoff inputs, duplicate authoring, or omitted exports.
   **Fix:** select one canonical filename and producer, and reference that contract from both resources.

2. **P2 — Full-pitch authoring leaks into standalone artifact requests.**
   The candidate [unconditionally loads `bundle.md`](/private/tmp/engos-full-shaping-design/reports/engos-design-shaping/implementation-candidates/engos-delivery-diagram-contract-artifacts.md:83). That resource [requires writing `pitch.md` and assumes conductor-supplied sidecars](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-delivery-diagram-contract-artifacts/references/bundle.md:7), despite explicitly supporting artifact-only mode. The original contract authors diagrams/tables from an existing solution; it does not require a conductor or another pitch document.
   **Fix:** scope pitch-level outputs and conductor dependencies to full-shaping mode. Preserve the original standalone artifact bundle and its partial-result behavior.

3. **P2 — G4 requires visual-target evidence for JSON-only delivery.**
   [G4](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-quality-shaping-gate/references/gates.md:13) requires saved-target pixel evidence without a representation exception. Yet the [representation contract](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-design-shaping/representations.md:13) explicitly supports JSON document exports verified by parsing and inventory comparison. A faithful JSON-only delivery has no rendered target diagram pixels to inspect.
   **Fix:** make target verification representation-specific: structured parity for JSON; saved visual evidence for HTML/Docs. Keep G3’s local diagram-render inspection separate.

The reviewed instructions otherwise preserve attributable human decisions, uncertainty closure, actual reviewer provenance, contamination holds, and the distinction between instructed context restrictions and observed/enforced host isolation. Human-led evidence follows the same sufficiency standard, including explicitly labeled private human review. The assistance ladder, effort checkpoints, source coverage, and preservation of external edits are coherent. These are instruction findings, not observed runtime outcomes.

| Existing skill | Requirement-preservation verdict |
|---|---|
| `engos-audit-pitch-review` | **Preserved with an explicit mode override.** Existing commands, standalone ten-point rubric, appetite scaling, integration-reference exceptions, outputs, and authority boundaries remain. Full-shaping mode expressly replaces scoring and combined readiness with G3/G4. |
| `engos-delivery-artifact-embed` | **Core requirements preserved; behavior expanded.** Meaning preservation, target authority, private placement, readback, blockers, and standalone use remain. Capability detection and fidelity checks affect all callers; the Google Docs matrix now favors private DOCX conversion. This is a behavioral change, not editorial equivalence. |
| `engos-delivery-diagram-contract-artifacts` | **Partial preservation.** No-fabrication, ownership gaps, three diagrams, contracts, partial bundles, and publication boundaries remain. Separate render receipts and richer contracts are deliberate changes. Finding 2 prevents a clean standalone-preservation verdict. |

The instruction-editor audit produced no edited artifact or applied edit ledger. Entry-file sizes, excluding newly added resources:

| Existing skill | Lines before → after | Words | Bytes |
|---|---:|---:|---:|
| Pitch review | 579 → 604 | 3,950 → 4,171 | 25,876 → 27,478 |
| Artifact embed | 151 → 180 | 1,131 → 1,380 | 7,572 → 9,505 |
| Diagram/contracts | 163 → 182 | 1,128 → 1,282 | 7,753 → 8,975 |

Model-token counts were not measured; size changes establish neither savings nor improved behavior.

**Independent synthetic calibration judgments**

| Control | Judgment |
|---|---|
| **A — Supported optional scalar** | **Simplicity 5:** one smallest sufficient addition using the stipulated applicable pattern. **Security 5:** the trusted premises establish no new attack surface. **Cost 5 at the stated operation-volume level:** `10,000 × 100 × 1 = 1,000,000` local lookups/day, with no added provider calls or storage; this does not establish dollar cost or measured latency. **Confidence 3:** supported precedent warrants the proposal, but no integrated spike/MVP demonstrates it. Clear future acceptance is not an executed result. Missing implementation alone does **not** force every dimension below 5. No overall score or G3 verdict is warranted from this abbreviated control. |
| **B — Unsupported new auth compatibility** | **Hold G2; G3 cannot pass. Feasibility capped at 2; Confidence 1** for the weakest material claim. The asserted compatibility has no supporting evidence. Do not inherit A’s Security 5 automatically after changing authentication. Next action: specify a bounded, separately authorized compatibility observation with attributable results—or remove that dependency through a confirmed scope decision and dependency check. |
| **C — Missing security matrix** | **Fail G3’s mandatory artifact predicate regardless of prose quality or self-score.** The missing required security assessment scores **1** under the rubric. Return the missing matrix, responsibilities, enforcement evidence, and unresolved owners as concrete repairs. Preserve unaffected prior gates; rerun affected G3 checks after repair. |

These judgments follow the different anchors in the pinned sources rather than a universal “implementation required” rule. The new rubric is an adaptation, not a literal copy: it narrows claim handling to material/load-bearing claims and reframes technical-spec quality as contract quality. The critical compatibility cap and readiness thresholds remain. Actual team-exemplar calibration and host-specific behavioral proof remain outside this review.

Reviewed SHA-256 bindings follow. Candidate and resource-set hashes were checked twice and remained unchanged.

```text
CANDIDATES — reports/engos-design-shaping/implementation-candidates/
engos-audit-pitch-review.md
  9c3b03b32fb6c493edcd09b462ea9728a69485ad6361b5260e425f22e8e8f2f9
engos-delivery-artifact-embed.md
  d1f7106c9c35fb7673de1737bbe37ef3594abcfeddade9d98597528647854d9f
engos-delivery-diagram-contract-artifacts.md
  dedc3b5ea277b7624299fce91d9837c275547b15dc1e3d70efed12670c1b99e1
engos-design-frame-from-vague.md
  e0fd856f624ccd9d875ba4553e5a4d5e87ef35b704846fdd24bb3209a9bcb067
engos-design-shaping.md
  59d319508260bb5993899c48fb5149b76c85deca955db2cb480111048b1b4414
engos-quality-shaping-gate.md
  06c054d91d4fc732e17ad3a53b3e0c7cdc38d18367643393d710f05d85cfe31a

ORIGINALS — ssot/
engos-audit-pitch-review.md
  ca6ddabc14caee2cf1bf3a3f47fcc7971cff27830a4027471e25a048b6ad6bd3
engos-delivery-artifact-embed.md
  32773e71e5a87bfba82046253c673536c4174e935c7ee20e168bdb8bad2c97ff
engos-delivery-diagram-contract-artifacts.md
  3b4f723779b4b9298366efeaf15827173bd06004c28f8e8872b7da93c5fa024e

OPERATING PLAN
  1bfb7f01766dbaf8b7c134d3515bd2cf6ebe7162c43cee666e58dd59942b5766
NEW references/rubrics.md
  1bda77f900893734bb6d708f7dbe5486492f34614c998a019c5279c45f76d2a9
PRIVATE PINNED quality-score.md
  04db643cd2a78b9e519c1f646ef8be93dbd017ac4d1647e3b48fd5fa379588fa
PRIVATE PINNED pitch-review/SKILL.md
  4eaf72bd78c556fe7a2a80b17c32385457c8b9396c56780ffe8b10973cc2b5f9

CANONICAL RESOURCE-SET DIGESTS
engos-design-shaping
  eb7848b09a0f3e568e4af0b3ea09052709bdb5d6a2e25fd5f3e905722d26bcdd
engos-design-frame-from-vague
  5c5ebd54eb97c9000fbad4fdb89e87da55c24d7c0a9a1727f9659f4b0e4d0755
engos-quality-shaping-gate
  f4e31c102080cfebcd8fdc5c3e0f71c1f9da19c13976bb9722f9c789fbc62403
engos-delivery-artifact-embed
  35ac03bee70c76ecc2b1575d7ec2dc9bcd4f9e1ecfe0791157d21a51801f29ac
engos-delivery-diagram-contract-artifacts
  545799a3c10406be7e179031bbd6e525e6c6c655c5f7b430f0152dbb61a97d61
```

Each resource-set digest hashes the `shasum -a 256` manifest of its repository-relative paths, sorted under `LC_ALL=C`, including `resource-map.json` and Markdown resources, excluding `runtime.md` and all scripts.
