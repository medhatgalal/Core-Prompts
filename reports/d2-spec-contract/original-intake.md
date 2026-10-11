# D2.S1 original new-job intake

This is the original intake seed for a new capability, not a historical skill,
current SSOT baseline, behavioral baseline, or independent review attestation.

1. Create engos-design-specify-change as a focused portable skill only.
2. Default to requirements-first; accept design-first and bugfix entry.
3. Design-first extracts supplied-design assumptions and reconciles acceptance before task approval.
4. Bugfix preserves current, expected and unchanged behavior without inventing reproduction.
5. Own SpecContract.v1: schema_version, id, source_refs, authority_ref, entry_order, requirements with id/condition/behavior/acceptance/unchanged_behavior/priority, non_goals, assumptions with id/text/status, and design_refs with id/path/sha256.
6. Check unique IDs, preserve source references, and reconcile material assumptions before dependent task approval. Shape and IDs prove neither truth nor authority, approval, semantics or implementation.
7. Preserve repository formats. Create sidecars/adapters only when machine interchange needs them.
8. Architecture owns material design; planning and implementation remain separate; typo-only work does not require a spec. Preserve existing shaping source and acceptance.
9. Bundle resource-map.json, templates/requirements.md, references/requirements-first.md, references/design-first.md, references/bugfix.md, schemas/spec-contract.schema.json and templates/trace-matrix.json using the existing loader.
10. The trace template is an empty or supplied-link ledger only, with no trace checker or test coverage proof.
11. Do not implement shared resource imports, a TraceResult schema, trace_check.py, new consumer skills, or D2.S2/S3 work.
12. Use an independently expressed, attributed synthesis of the pinned Addy spec-driven-development source and public Kiro guidance. Preserve licenses where applicable and make no native Kiro equivalence claim.
13. Prepare candidate/resources/docs/tests for independent review before canonical apply; do not create a self-attestation or fake baseline. No merge or install is authorized.
