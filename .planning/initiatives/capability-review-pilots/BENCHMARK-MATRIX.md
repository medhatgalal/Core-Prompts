# SSOT Benchmark Matrix

Scores use a 1-5 scale where 5 is strong and reusable.

| Slug | Name Clarity | Description Richness | Intent Coverage | Boundary Clarity | Inputs/Outputs | Metadata Usefulness | Surface Usefulness | UAC Audit Fit | Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| analyze-context | 4 | 5 | 5 | 5 | 5 | 4 | 4 | pending rebuild audit | uplifted in recovery slice |
| architecture | 5 | 5 | 5 | 5 | 5 | 5 | 5 | manual_review | benchmark anchor |
| code-review | 5 | 5 | 5 | 5 | 5 | 5 | 5 | requires_adjustment | benchmark anchor |
| converge | 4 | 5 | 5 | 5 | 5 | 4 | 5 | pending rebuild audit | uplifted in recovery slice |
| docs-review-expert | 5 | 5 | 5 | 5 | 5 | 5 | 5 | pending rebuild audit | landed as `both` |
| gitops-review | 5 | 5 | 5 | 5 | 5 | 5 | 5 | pending build audit | landed as `both` |
| mentor | 3 | 4 | 3 | 2 | 3 | 3 | 3 | requires_adjustment | future cleanup |
| resolve-conflict | 5 | 5 | 5 | 5 | 5 | 5 | 5 | requires_adjustment | benchmark anchor |
| supercharge | 4 | 5 | 5 | 5 | 5 | 4 | 5 | pending rebuild audit | uplifted in recovery slice |
| testing | 5 | 5 | 5 | 5 | 5 | 5 | 5 | requires_adjustment | benchmark anchor |
| threader | 3 | 4 | 3 | 4 | 4 | 3 | 3 | fits_cleanly | future cleanup |
| uac-import | 5 | 5 | 5 | 5 | 5 | 5 | 5 | requires_adjustment | benchmark anchor |

## Immediate Uplift Targets
1. `mentor`
2. `threader`
3. any future external family that fails the new template-backed benchmark gate

## Notes
- `architecture`, `code-review`, `resolve-conflict`, `testing`, and `uac-import` define the detail bar for this initiative.
- `docs-review-expert` and `gitops-review` are the recovery-slice exemplars for `both` capabilities with explicit operating contracts and review timing.
- `mentor` remains useful but is overloaded with orchestration and local workflow assumptions; it should be reviewed in a later slice.
- `threader` is structurally clearer than the old weak set, but still below the new benchmark-grade body standard.
