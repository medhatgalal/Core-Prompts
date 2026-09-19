# engos-design-shaping worked-example library

Start with [the visual reference library](engos-design-shaping-examples.html).
It contains the original inputs, both rounds, solution-free frames, evidence,
shaped drafts where reached, native Mermaid diagrams and complete tables.
Open the full-size diagram links or pan rather than shrinking long diagrams.
Mermaid 11.17.2 loads from its pinned CDN; PNG references also work offline.

These are **constructed teaching cases**, informed by real document comparison.
They are not verbatim company pitches, production proof or approved bets.

## What the two rounds actually showed

| Example | Complexity / initial vagueness | Round 1 | Round 2 | Learn from it |
| --- | --- | --- | --- | --- |
| [Model capacity](engos-example-model-capacity/round-2/pitch.md) | Low / low | Shaped draft; 3.92/5, overlong, sequence failed rendering | 589-word coherent draft; same 3.92/5; rendered repairs | Exact absence semantics and a small, indivisible core; better prose is not new feasibility evidence |
| [Insight visibility](engos-example-insight-visibility/round-2/pitch.md) | Low / high | Correct G1 stop: missing outcome, appetite, success and kill decision | Explicit new I1/I2 premises permit G1/G2 and a 526-word shaped draft; 3.92/5 | Ask for intent, research facts; do not turn “useful” into invented ranking work |
| [Configuration deployment](engos-example-config-deployment/round-2/pitch.md) | High / low | Reviewer rejected G2 closure on race, empty-state and capacity gaps; 2.83/5 draft | New C2–C4 premises resolve those gaps; 550-word draft; 3.92/5 | Trace failure states and ownership across boundaries; don't count unsupported assumptions as research |
| [Unified chat](engos-example-unified-chat/round-2/research-notes.md) | High / high | Correct G2 needs_spike | Still needs_spike; clearer scope and three bounded evidence requests | A “Shaped” title, reusable component or named spike is not feasibility proof |

Three round-two drafts have passing G0–G2 content conditions within their
fictional premises. None passes G3's numeric threshold: each has eleven 4s and
Confidence 3, giving 47/12 = 3.9167. Unified chat's last passing gate is G1.
No G4 pass, Google Doc placement or end-to-end Bet-ready success is claimed.

## How to use these references

1. Read input.md and round-1/intake.md. Classify facts, assumptions and decisions.
2. Read the frame before the pitch. Check that it bounds the problem without
   selecting a mechanism.
3. Predict the gate verdict before opening the journal/review. A correct stop
   is part of the exercise, not an incomplete answer to hide.
4. Read round-two-clarifications.md and compare both rounds. New hypothetical
   evidence is explicitly attributed; it never retroactively validates round 1.
5. For advanced drafts, trace one open question through research, a contract,
   a security owner, a diagram and an observable acceptance criterion.
6. Use these as annotated drafts, not copy-and-paste certification. Replace
   fictional premises with current source evidence and actual decisions.

## Evidence and limits

- [First independent review](review-round-1-content.json) and [second review](review-round-2-content.json)
  preserve actual scores, rationale, identities and source hashes.
- [Visual observations](engos-quality-example-render-observations.md) record
  nine rendered and pixel-inspected PNGs plus further sequence/layout repairs.
  Native HTML produced nine SVGs with zero Mermaid error elements; representative
  target views were inspected, not a complete G4 parity review.
- The capacity example's ten actual schema checks cover only optional positive
  integers and rejected shapes. They do not test a working product integration.
- Two authors each handled two cases in both rounds. Separate reviewers assessed
  each batch. This is an observed teaching experiment, not statistical validation.
- Model capacity's score did not improve. Configuration improved with **new
  inputs**; that does not establish a better capability under fixed conditions.

## Next design question, not a silent waiver

The current gate holds three content-complete drafts solely below its numeric
threshold, while the reviewer says unchanged, bounded seams need no production
test merely for shaping. This warrants calibration against the authoritative
team rubric and Shape Up: distinguish uncertainty requiring a spike from normal
builder acceptance work. Do not inflate Confidence, lower the threshold after
seeing results, or build production code simply to force these examples green.
Keep these results as the baseline for a separately specified calibration test.

The original real-input exercise remains separate at G1, awaiting explicit
appetite/walk-away provenance. This library does not replace that acceptance
requirement or the requested two-surface demonstration.
