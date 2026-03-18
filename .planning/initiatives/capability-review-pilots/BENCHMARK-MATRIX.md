# SSOT Benchmark Matrix

Scores use a 1-5 scale where 5 is strong and reusable.

| Slug | Name Clarity | Description Richness | Intent Coverage | Boundary Clarity | Inputs/Outputs | Metadata Usefulness | Surface Usefulness | UAC Audit Fit | Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| analyze-context | 3 | 2 | 3 | 3 | 2 | 3 | 3 | requires_adjustment | uplift now |
| architecture | 5 | 5 | 5 | 5 | 5 | 5 | 5 | manual_review | benchmark anchor |
| code-review | 5 | 5 | 5 | 5 | 5 | 5 | 5 | requires_adjustment | benchmark anchor |
| converge | 3 | 3 | 4 | 4 | 4 | 3 | 4 | manual_review | uplift now |
| docs-review-expert | 5 | 5 | 5 | 5 | 5 | 4 | 4 | pending build audit | new pilot landing |
| mentor | 3 | 4 | 3 | 2 | 3 | 3 | 3 | requires_adjustment | future cleanup |
| resolve-conflict | 5 | 5 | 5 | 5 | 5 | 5 | 5 | requires_adjustment | benchmark anchor |
| supercharge | 4 | 2 | 3 | 3 | 3 | 3 | 4 | manual_review | uplift now |
| testing | 5 | 5 | 5 | 5 | 5 | 5 | 5 | requires_adjustment | benchmark anchor |
| threader | 3 | 4 | 3 | 4 | 4 | 3 | 3 | fits_cleanly | future cleanup |
| uac-import | 5 | 5 | 5 | 5 | 5 | 5 | 5 | requires_adjustment | benchmark anchor |

## Immediate Uplift Targets
1. `supercharge`
2. `analyze-context`
3. `converge`

## Notes
- `architecture`, `code-review`, `resolve-conflict`, `testing`, and `uac-import` define the detail bar for this initiative.
- `mentor` remains useful but is overloaded with orchestration and local workflow assumptions; it should be reviewed later, not mixed into this slice.
- `threader` is structurally clearer than the other low-specificity entries, so it is not in the first uplift wave.
