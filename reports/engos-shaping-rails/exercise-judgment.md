# Shaping-Rails Exercise Judgment

## Candidate and exercise

Candidate: `engos-delivery-diagram-contract-artifacts` plus
`engos-delivery-artifact-embed`, integrated with
`engos-audit-pitch-review`.

Exercise source: the real [PM Query Library Architecture Overview](https://docs.appian-stratus.io/process-mining/new-arch/).

## Iteration record

### Iteration 1 — failed completeness

The first draft rendered a component diagram and a request sequence and listed
API methods. It did not carry a data-flow diagram, a security-owner matrix, or a
surface receipt with source identity. The gate correctly treated this as
incomplete even though the diagram source parsed.

### Iteration 2 — adopted

The bundle now includes component, sequence, and data-flow Mermaid source; API
and security-owner tables; an evidence ledger; no-gos; a manifest; and separate
HTML and Google-Doc adapter receipts. The HTML path is a native Mermaid/Markdown
passthrough. The Google-Doc path stops at `human_step_required` with the
private-image insertion blocker and readback step named.

## Scorecard

| Dimension | Result | Evidence |
| --- | --- | --- |
| Team quality rubric | Pass for artifact completeness; live contract health is not claimed | `exercise-source/` bundle and `html-surface.md` |
| Shape Up rough/solved/bounded | Pass with caveat: diagrams stay macro, appetite/no-gos are explicit | `exercise-source/no-gos.md`, evidence ledger |
| Rabbit holes | Pass: Google-Doc blocker is named and mitigated with a human step | `google-doc-placement.md` |
| No fabricated internals | Pass: every artifact claim is tied to the exemplar or marked not proven | `evidence-ledger.md` |
| Surface abstraction | Pass for HTML passthrough; Google Doc adapter path is prepared but not live-placed | both receipts |
| Pixel/render proof | Pass for local HTML and Mermaid outputs after rendering; external Google-Doc pixels not available | `exercise-verification.md` |
| Repo authoring standard | Pass: UAC structural-ready, generated surfaces validated, skills-only | UAC apply receipts and surface validation |

## Judgment

The design is structurally ready and exercises the intended rails. It is not a
claim of behavioral promotion or live Google-Doc placement. The strongest
remaining gap is a private Google-Doc image-insertion/readback proof in the
target environment; the capability now fails loudly and names the human step
instead of rediscovering the blocker during shaping.
