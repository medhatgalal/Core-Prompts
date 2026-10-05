# Attack Surface

Independent hostile implementation review of the future shaping review-evidence protocol, its runtime, schemas, canonical rules and focused tests. Final review state: **pass within this scope; no remaining blocking implementation finding identified**. This is not a numeric capability grade, behavioral promotion, delivery approval or review of the protected live run.

Reviewed the supplied request and applicable steering. No protected-run, installed-skill or product files were accessed. No build, commit, merge or installation was performed by this reviewer. Counterexamples used labelled fake fixtures in temporary run directories. The reviewer-owned file is the only repository write made by this review.

The complete Supercharge `/adversarial` resource bundle and `shared-review.md` were loaded for the final resource-dependent pass, after the initial implementation findings. Loader manifest SHA256: `56fee7ec78e0bac117fb3f517e8577890cfa638c3ac3a758f236ec64ee3df91f`; assembled payload SHA256: `c3f30d7f21780d99ee0666e2aa1c4f8fb4a9a7ba57065ea1d9699673402f47b9`. Resource delivery is not proof of comprehension or behavior.

The attack covered packet/source/span substitution, exact accepted-proof binding, host observations, revision contributors, fixer origin/consent, contradictory repair routes, finding ownership, prerequisite cycles, schema/version compatibility, retained-history/progress paths, numeric validation and passive rendered-artifact compatibility.

Final inspected identities:

| Canonical file | SHA256 |
| --- | --- |
| `sources/capability-resources/engos-quality-shaping-gate/scripts/shaping_run.py` | `815f89346b87ee97dd77b31c3c2a3b2b3e59f34d7bd1724b0c7b88ed1085c70d` |
| `sources/capability-resources/engos-quality-shaping-gate/schemas/runtime.schema.json` | `87f9f2770b7b6a7ce1e3d0ceb527420059fe4054d6ce04f200130c3da80f5023` |
| `sources/capability-resources/engos-quality-shaping-gate/schemas/review-evidence.schema.json` | `4ca1aa64d6ad0b0583eb3d712573e6221eedee5b84d06cb18215a6eb0428d137` |
| `tests/test_shaping_review_evidence.py` | `8732ae48d61a857008f9095e08a3c5c5da22ffaa0f0d9a96c5d1f12ce8abdfad` |

# Contradictions / Gaps

The following findings were raised during implementation and corrected before this final disposition. No item below remains an open acceptance bypass in the inspected final code.

| ID | Concrete failure and consequence | Disposition |
| --- | --- | --- |
| R01 | V2 seals added retained files/inputs and a packet, while floor-only history still required the schema-1 seal envelope and recomputed its older hash. A future retry entered recovery on a legitimate recorded v2 review. | Fixed: deliberate seal fields and noncircular hash payload are validated; retained v2 history is exercised after its mutable receipt source disappears. |
| R02 | A missing-predicate receipt accepted both research and shaping routes for the same seam/check. An unowned extra item also passed. | Fixed: every route/check/item must belong to the derived structured failure inventory; direct counterexamples now hold. |
| R03 | Two findings could depend on each other, forming an impossible repair prerequisite cycle. | Fixed: prerequisite graphs reject cycles as well as unknown/self references. Independent final counterexample held. |
| R04 | Opt-in G3 work orders advertised the schema-1 return contract although acceptance required v2. A conforming worker could return an impossible-to-accept receipt. | Fixed: opt-in G3 dispatch advertises the exact v2 schema; legacy gates retain their original contract. |
| R05 | The review plan supplied a free proof string, with only an independently hashed source quote; seams and questions could all bind to the substituted string. | Fixed: prepare pins the exact proof text to an accepted G2-owned quote; plans must match that controller binding. Final plan/proof substitution held. |
| R06 | Pre-prepare participation alone did not attest the final sealed revision's contributors. Receipt-held host claims also needed a separately retained controller observation. | Fixed: the post-seal controller sidecar binds packet/openings/render/answer observations and final contributor inventory; changed contributors require fresh prepare. Host authenticity remains external. |
| R07 | Repair records supplied free original author/reviewer names without binding the real failed order and finding, permitting origin substitution. | Fixed: contributing repair records must bind an observed failed order, return hash, finding and its actual assigned identities, plus prior consent. An independent lifecycle probe successfully prepared a consented fixer revision with a fresh grader and rejected that same stable fixer as the next grader. |
| R08 | Progress reconstructed only file hashes, but v2 review verification needed retained bytes; valid observed v2 reviews raised `KeyError: base64`. | Fixed: progress uses retained v2 files. Independent verification of the final positive receipt returned no failure. |
| R09 | The root schema's new external v2 reference was unresolved by the existing plain JSONSchema validator, including validation of a policy example. | Fixed: portable self-contained definitions resolve under the ordinary published-schema invocation; independent policy validation succeeded. |
| R10 | The first coverage fix equated every existing factual shape claim with a technical receiving seam, rejecting supported nontechnical existing workflows. Conversely, omitted seam inventories needed explicit ownership. | Fixed: controller-pinned applicability and coverage preserve explicit nontechnical treatment while preventing author relabeling of a pinned existing technical seam. Semantic correctness of that classification remains review-owned. |
| R11 | Audit contradiction routes could bypass the normal subject route: a dependent question routed to research, a missing seam to shaping, and an established mismatch to research. All three concrete counterexamples initially passed. | Fixed: special contradiction route/check must match the structured subject failure. All three independently rerun counterexamples held. |
| R12 | After R11, `assessment:<check>` could alias those same special defects into a generic shaping contradiction. Both question and predicate counterexamples passed. An initial broad rejection then prevented independently owned generic findings sharing that check. | Fixed: shared assessment-explanation aliases hold; mixed generic score contradictions require cited source spans disjoint from the special seam/question spans, with identical hashes recognized across different paths. Separate generic findings remain legal. Scope/meaning independence still requires semantic review. |
| R13 | The initial SVG whitelist rejected passive `<style>` and definitions used by the existing exporter, making valid rendered Mermaid artifacts unusable in review. This compatibility finding was supplied by the controller and independently rechecked. | Fixed: passive exporter-compatible SVG is supported; styled SVG validation succeeded and active CSS regressions reject imports, remote resources, animation and expressions. |

# Mitigations / Fixes

Independent verification commands:

- `python3 -m pytest -q tests/test_shaping_review_evidence.py tests/test_shaping_runtime.py` — **163 passed in 57.13s**. Source/test bytes changed during this combined run, so this is supporting integration evidence rather than a claim that every case ran against one stable final digest.
- `python3 -m pytest -q tests/test_shaping_review_evidence.py` — **72 passed in 23.73s** for the preceding candidate, followed by the final mixed-finding adjustment.
- `python3 -m pytest -q tests/test_shaping_review_evidence.py` — **75 passed in 17.40s** for the final candidate. Runtime/test digests listed above were unchanged before and after this run, including independent mixed-finding acceptance and overlapping/shared-explanation alias rejection.
- `git diff --check` — passed before report authoring.
- Ordinary `jsonschema.Draft202012Validator(runtime_schema).validate(policy_example)` — passed without a custom registry.
- `shaping_run.py review-observation --help` — verified the newly exposed controller command and its run-relative record contract.

Independent temporary-run probes also verified rejection of direct and generic contradiction route substitutions, unowned extra returns, cyclic prerequisites and accepted-proof substitution; positive progress verification; a real controller-journal failed receipt bound to a consented fixer revision; rejection of that fixer's stable identity as grader; and acceptance of passive styled SVG.

The focused regressions retain numeric floors, finite-number/boolean rejection, aggregate recomputation, current assessed-state binding, packet/hash/span checks, render failures, concurrent independent defects and immutable historical interpretation. Supplied historical facts remain labelled supplied/unverified, with unavailable historical dimensions explicitly absent and the valid synthetic vector separately labelled. The stored historical pass is not regraded.

# Residual Risk

Host identity, complete contribution attribution, actual ordered openings, respondent authority and user consent remain trusted host/controller observations. The Python helper binds and retains those records; it cannot authenticate a person or determine whether the host actually opened a file. A host without those capabilities must hold review. Protection of the controller store and observation provenance must be supplied by the host.

Receiving-function/read-field grounding, proof dependence, source/contract/sequence agreement, visual labels/connectors and rationale truth remain independent semantic judgments. The tests deliberately use fake judgments and pixels. They prove mechanical consistency and negative routing, not truthful review, actual reading, rendered source agreement, live applicability or superiority over the historical policy. Hashes, schemas and test counts do not establish those semantic outcomes.

Disjoint source spans allow independently owned generic and specific findings to share an assessment check. Span separation establishes separate evidence bytes, not substantive independence: a semantic reviewer must still reject an unrelated quote or disguised copy of the same defect. The helper cannot infer that distinction from rationale prose. Shared assessment-explanation aliases and overlapping source-span aliases are mechanically held.

The PNG decoder supports the documented bounded noninterlaced 8-bit profiles; other formats/profiles hold. SVG parsing and a bound PNG do not prove that a host rasterization corresponds to the SVG or Mermaid source. That agreement still needs real host rendering and independent pixel inspection through the existing exporter path.

This review does not cover final generated surfaces, UAC outcomes, hosted CI, PR/MR review, merge parity, cleanup, publication or home installation. Those remain separate controller-owned delivery gates. No numeric skill grade was assigned.
