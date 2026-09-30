# Independent instruction review: Crucible shaping correction

Historical initial review. Its quoted examples and first-render observation are
preserved as evidence, not current skill requirements. The repository-neutral
follow-up and latest rendered-pixel judgment are recorded at the end of this file.

## Scope and method

Reviewed the three candidate instruction files and the specifically named current prose: conductor `stages/research.md`, `stages/shape.md`, `stages/review.md`, `routing.md`, and `templates/shaped-bundle.md`; gate `references/gates.md` and `references/rubrics.md`; diagram `references/diagram-style.md` and `references/presentation.md`. Compared the changed rubric text with its prior version to check score-count and threshold continuity.

This is a current-prose consistency review only. It does not establish model behavior, runtime enforcement, rendering behavior, or promotion readiness. No code or documentation outside this report was changed. The legacy ten-point pitch-review artifact was not opened or used as a scorer.

## Requirement coverage

| User requirement | Coverage and evidence | Review result |
| --- | --- | --- |
| Preserve twelve scores and floors 3/4 | Gate candidate requires all twelve scores and states per-dimension floor 3 and overall 4 (`engos-quality-shaping-gate.md:65-66, 76-82`). Rubric has seven team dimensions plus five pitch dimensions, reports all twelve, and retains those thresholds (`references/rubrics.md:9-23, 39-52`). Its diff from the prior rubric changes the Cost-3 anchor and iteration/selection rules, not the dimension inventory or thresholds. | Covered; no score dimension or floor change found. |
| Appetite restatement is Cost 3 | Gate candidate says a restatement such as “one send, one row, two reads” cannot earn 4 (`engos-quality-shaping-gate.md:76-77`). Rubric makes Cost 3 the appetite-restatement anchor and requires added supported workload/frequency/resource evidence for 4 (`references/rubrics.md:15, 25-28`). | Covered consistently. |
| Same-evidence average-only failure stops new pitches | Conductor blocks another pitch when every score is at least 3, average is below 4, and this is the only miss (`engos-design-shaping.md:112-117`). Review dispatch requires new evidence, a bounded named spike, or hold, and says a spike name alone does not clear the stop (`stages/review.md:45-50`). Gate requires newly opened evidence accepted in G2 before another G3 work order (`references/gates.md:25-29`); rubric also says same-source prose/filename changes cannot clear it (`references/rubrics.md:48-57`). | Covered consistently. The spike is a next step, not evidence by itself. |
| Confirmed behavior absent from opened code is a proposed extension | Conductor and gate candidate state this directly (`engos-design-shaping.md:87-89`; `engos-quality-shaping-gate.md:49-51`). Shape dispatch requires naming the existing seam separately from proposed behavior and grounding the proposal in researched basis claims (`stages/shape.md:11-15, 22-27`). Rubric says not to require the proposed write to exist (`references/rubrics.md:59-64`). | Covered. |
| Judge pieces as a set; empty selection is an unscored hold naming walk-away | Conductor says to judge the selected pieces together and stop before scoring when none are selected (`engos-design-shaping.md:87-89`). Gate candidate, shape dispatch, template, and rubric all repeat the unscored hold/walk-away rule (`engos-quality-shaping-gate.md:49-51`; `stages/shape.md:14-20`; `templates/shaped-bundle.md:14`; `references/rubrics.md:59-60`). | Covered consistently. |
| Proof observes the frame’s requested stop | Conductor rule requires observing the requested stop, including the post-send job when applicable (`engos-design-shaping.md:120-121`). Shape dispatch specifies terminal-state observation and distinguishes a future check from an executed result (`stages/shape.md:56-59`). Gate, template, and rubric preserve the same requirement (`engos-quality-shaping-gate.md:50-51`; `templates/shaped-bundle.md:32-38, 58-63`; `references/gates.md:101-104`; `references/rubrics.md:64`). | Covered consistently. |
| False or unopened material claims return to Research before G3; research/code disagreement still fails | Research says notes that disagree with opened code fail and must be repaired in Research (`stages/research.md:47-54`). Shape dispatch routes missing/false facts to G2 before reviewer dispatch and keeps the code-agreement standard (`stages/shape.md:22-27`). Conductor and gate candidate likewise return false citations or unopened material facts to G2/Research (`engos-design-shaping.md:90-94`; `engos-quality-shaping-gate.md:79-82`). Gate policy states both cases (`references/gates.md:18-23`). | Covered. “Unopened” is scoped to load-bearing existing facts, which is consistent with the stated material-claim requirement. |
| Sequence diagram constraints and reviewer pixel inspection | Diagram candidate keeps a real `sequenceDiagram`, omits `alt`/`else`, requires short labels and white background, and uses role bands plus a legend when actor fills remain gray (`engos-delivery-diagram-contract-artifacts.md:87-90, 114-116`). Diagram-style and presentation references carry the same constraints and require the independent reviewer to open rendered pixels (`references/diagram-style.md:28-36, 60-63`; `references/presentation.md:23-26, 42-48`). Gate also requires reviewer pixel inspection (`references/gates.md:87-94`). | Covered consistently. |
| No preferred reviewer verdict | Review dispatch excludes author self-grades and preferred verdicts from the initial work order and dispatch prompt (`stages/review.md:16-24`); the prompt says not to infer a verdict from the author (`stages/review.md:26-36`). Gate candidate states that no conductor message supplies the preferred verdict (`engos-quality-shaping-gate.md:81-82`). | Covered. |
| Legacy ten-point pitch-review is not a second scorer | Review dispatch expressly says the workshop does not load it and makes the gate the sole owner of predicates, scores, and thresholds (`stages/review.md:3-9`). Routing confines the legacy review to standalone requests (`routing.md:26`); the conductor says not to substitute its combined verdict (`engos-design-shaping.md:104-106`). | Covered. The legacy artifact was not inspected. |

## Conflicts and omissions

- No material contradiction was found across the requested candidate and companion prose for the listed requirements.
- The phrase “new fact, a named spike, or a hold” can be read in isolation as though merely naming a spike clears the stop. The immediately following review text says it does not, and gate/rubric wording requires new accepted evidence; this is resolved in context, not a blocking conflict (`stages/review.md:45-50`; `references/gates.md:25-29`; `references/rubrics.md:52-57`).
- The gate candidate summarizes “before scoring” for unopened load-bearing facts; the stage-specific instructions make the control point more concrete: validate coverage and opened source before dispatch, and return a gap to G2. No missing route was identified (`engos-quality-shaping-gate.md:79-82`; `stages/shape.md:22-27`).
- The diagram candidate’s short summary mentions role-colored bands for gray actors, while the referenced style supplies the operational detail: labeled bands, legend, source-bound rendering, and reviewer pixel inspection. The dependency is explicit and the companion prose covers it (`engos-delivery-diagram-contract-artifacts.md:83-90`; `references/diagram-style.md:30-36, 60-63`).
- The rubric version advances from v3 to v4 to encode the requested Cost anchor and iteration/selection corrections. The current prose still has the same twelve dimensions and 3/4 thresholds; historical scores are explicitly not retroactively changed (`references/rubrics.md:1-7, 9-23, 39-52`).

## Rendered sequence pixel check

Opened `reports/crucible-shaping/sequence.png` and compared it with `reports/crucible-shaping/sequence.mmd` and the limited-renderer requirements in `references/diagram-style.md:28-36, 60-63`.

- Source and rendered type: the source declares `sequenceDiagram` with User, App, and Store participants (`sequence.mmd:1-5`); the image visibly renders three sequence lifelines and message arrows, not a flowchart.
- Actors: the User, App, and Store boxes are gray. This matches the documented renderer limitation.
- Role bands: blue, pale green, and pale amber message bands are visibly filled. Each has an in-band role label: “UI - proposed send,” “Store - proposed write,” and “Async - observe stop” (`sequence.mmd:6-18`). I do not see a separate legend mapping the band colors to roles. The role labels are present, but the documented explicit-legend criterion is not visibly met by this image.
- Background and labels: the canvas is white, consistent with the source's `#ffffff` theme setting (`sequence.mmd:1`). Labels are short and readable at the supplied image size: “Send,” “Save job,” “Job row,” “Read job,” and “Terminal state.”
- Visible order: User → App: Send; App → Store: Save job; Store → App: Job row; User → App: Read job; App → User: Terminal state (`sequence.mmd:7-18`).
- Interpretation limit: this is the explicitly illustrative proposed sequence described by the diagram-style reference (`references/diagram-style.md:60-63`). The image establishes what was rendered, not whether any product implements these actions or their behavior.

## Conclusion

The current instruction prose covers each supplied requirement without a material cross-file conflict. The one potential ambiguity about a named spike is explicitly resolved by the review and gate instructions. The requested image conforms on diagram type, gray actors, visible role-band fills, white background, readable short labels, and message order; its separate-legend criterion is not visibly satisfied. This is a pixel observation, not a preferred content-review verdict, promotion score, or model-behavior claim.
# Repository-neutral follow-up review — September 29

Independent reviewer Franklin (gpt-6-luna, medium), identity
01a0ef9a-31a4-7012-b34c-081a556ea91d, examined the three final candidate
entrypoints, canonical routed resources, workshop runbook and shaping examples.
Disposition: PASS for instruction preservation, not product-pitch acceptance or
formal behavioral promotion. No named product/repository contamination remained
in instruction prose; existing runtime work-order identifiers remain compatible.

The four failure patterns remain generic: unchanged-evidence average-only retries
stop; empty sets hold without scores while grounded extensions remain valid;
unopened load-bearing facts return to Research before review; renderer limitations
cannot turn a sequence into a flowchart. Completion proof observes the accepted
frame's outcome. All twelve scores, floor3 and mean4 remain unchanged. New examples
are explicitly illustrations of patterns, not prescribed product architectures.

The reviewer opened the updated sequence.png pixels: real sequence with lifelines,
gray actors, blue/green/amber bands, explicit readable legend and white background;
no flowchart substitution or visible alt/else. Rendering used the retained generic
sequence.mmd source and cached Mermaid CLI. No further contradiction was found.
