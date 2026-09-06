# UAC source-integrity regression evidence

`original-skill.md` preserves the original OpEx skill verbatim from the coordinator's saved 2026-09-06 fixture. `lossy-candidate.md` is the exact `quality_result.final_candidate_text` from that day's `opex-uac-plan.json`, which reported `structural_ready` while losing the HTML template and operational details.

These are test inputs, not canonical capabilities or evaluator baselines. Tests use an unregistered slug to prevent skill-specific rules or existing historical baselines from masking the defect. The source skill and shipped OpEx capability are not modified by this repair.

`loop-package/` preserves all seven pinned Loopy package files from the independent harness lane for cross-skill checks. They are reference inputs, not installed capabilities. The preservation wrapper is tested against both sources with deliberately incorrect inferred outputs.
