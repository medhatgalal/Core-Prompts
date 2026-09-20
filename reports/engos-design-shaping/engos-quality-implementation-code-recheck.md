# engos-quality-shaping code recheck

Readiness: blocked only on the confirmed empty-target policy issue below. The original seven findings are closed on the reviewed canonical bytes; no additional P1/P2 finding was reproduced.

1. **[P2] Frame-only and draft-only runs incorrectly require publication targets.**
   [shaping_run.py:200](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-quality-shaping-gate/scripts/shaping_run.py:200) and [runtime.schema.json:58](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-quality-shaping-gate/schemas/runtime.schema.json:58) reject an otherwise valid policy containing `delivery_targets: []`. Actual `init` returned exit 2, `targets cannot be empty`, without creating the state pointer. This conflicts with the [reviewed plan’s G1/G3 stopping points](/private/tmp/engos-full-shaping-design/reports/engos-design-shaping/engos-design-shaping-operating-plan.md:192).

   Minimum fix: keep `delivery_targets` required and type-checked as an array, but permit an empty array in policy validation and its schema. Retain per-target validation and duplicate rejection. Update initialization help/documentation accordingly.

   **Preserve G4’s existing nonempty, exact-coverage requirement** at [shaping_run.py:633](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-quality-shaping-gate/scripts/shaping_run.py:633), its receipt-schema minimum, and delivery-intent membership checks. The example policy should retain both original pilot targets.

   Add regressions proving empty-target initialization and G1/G3 completion, followed by rejection of empty-target G4 acceptance and unrequested delivery. An in-memory-only validator relaxation demonstrated precisely these outcomes: G1/G3 advanced; G4 held with the pointer unchanged. No source repair was applied.

Independent verification:

| Original finding | Observed recheck |
|---|---|
| Policy-binding bypass | Both original policy/rubric probes now hold |
| Symlinked render destination | Rejected before renderer invocation; destination untouched |
| DOCX concurrent overwrite | Existing replacement preserved; export refused |
| DOCX image substitution | Verified original image bytes embedded |
| Renderer bounds | Timeout at approximately 0.155 seconds; diagnostics bounded; positive exit works |
| Delivery-only drift | Content remains ready; delivery becomes pending |
| Fenced-code corruption | Literal operators and backticks preserved |

The partial-render probe retained only the completed PNG, removed temporary scratch, and produced no success manifest. A source-change probe also refused success.

I independently ran **107 passing tests**, with three DOCX tests skipped in the default interpreter. Those **three DOCX tests separately passed** using the actual bundled document runtime. Both CI configurations install the optional dependencies and explicitly invoke all three modules; hosted execution was not verified.

Scope and intended commit message remain appropriate. No repository writes, staging, delegation, or cloud operations occurred. Generated resources, real Mermaid visuals, human-pilot behavior, and broader packaging readiness remain outside this verdict.

HEAD remained `59488c0401e2d887f02a3f06af65387cd6f22f7b`. These SHA-256 hashes were unchanged between initial and final verification:

```text
shaping_run.py
b44f1934dd4ffc77f44759a9689309f955c20291c882d92017744be1eb81701c
schemas/policy.example.json
b03ae35b04ea16cbc370122c7c7c5dfddecb38764c5e0b3dd3655567afd44a9f
schemas/runtime.schema.json
615ff641fc2ffc89d6bed6db0b244e138ac1ab3f39feb06ae3ac6dcf3317735e
references/runtime.md
04ce51de8d94060f6d2fbf555228f1000552dc8d85fe7af2225ecaf345baf2bf
artifact_export.py
120ea72d98c4abf10d7779be422be36d03c24aac9367c2c01993fb16c1ddfd5c
references/export.md
5be3ce3cdfcd595a66efa494f286a156613dc27f45ac9a51b6dfa614ed1c80d2
tests/test_shaping_runtime.py
cd7ce9e55e761f1dbeb52307badb0d58d3b8ddb1bfbfdc4ed288ad6fca999ac7
tests/test_shaping_export.py
dee3557e8155e5143ace0fade82391edced0b9c4c8648a6d51ef4614bc45dee7
tests/test_shaping_export_docx.py
54def1a9ed0925c2606721d31b2c1ab0acce2d3beb11249a8075708fa411b52f
engos-design-shaping-operating-plan.md
1bfb7f01766dbaf8b7c134d3515bd2cf6ebe7162c43cee666e58dd59942b5766
.github/workflows/cli-surfaces-validate.yml
ff87d52eb98b07c043947d7337364c02a13c383d0dd3af484d0fd7da09abdd91
.gitlab-ci.yml
256186d1dd712c6cad37ea1af812f223ea932461959e01c848263527fab98aa1
```
