# engos-design-shaping observed design iteration

## Initial candidate review

Independent worker 01a0b044-6673-7ad2-8bc5-df9e9df0dcae inspected the candidate
files and reported six blocking execution-contract gaps. Full original result
and original hashes are retained in design-review-initial.json. This was an
actual review observation, not a reconstructed failed run.

Weakest dimension: dependency ordering and content/review identity, despite
otherwise explicit five-stage semantics.

## Applied design repairs

| Observed defect | Repair |
| --- | --- |
| G3 checked targets that G4 creates | G3 source/local render coverage; G4 saved target coverage |
| Betting prep first written after gate requiring it | Write prep before G4 and define sidecar placement |
| Research gate needed decisions first created at Shaped | Initialize during framing and append during research |
| Old pitch reviewer semantics still reachable | Explicit candidate map and mandatory overlay precedence |
| Whole-folder hashes invalidated by added receipts | Enumerated immutable content; append observations separately |
| Empty target list could pass placement vacuously | Draft-only stops at shaped_draft; G4 requires real target |

Second independent review returned PASS on the bounded semantic recheck, with
all six findings resolved. Its response and current hashes are preserved in
design-review-revised.json. That verdict does not certify full-run behavior.

## Gate execution observations

A separate worker executed seven explicitly synthetic probes against the initial
gate contract. The five injected failures were rejected and two controls passed.
Observed result and input hashes are in probes/observed.json. This supplies
bounded behavioral smoke evidence, not a statistically qualified comparison or
native-runtime enforcement proof. Repairing dependency rules changed the gate
resource hash; the initial result retains its old binding and must not be silently
relabeled as a test of the revised contract. A fresh independent worker then
executed the seven unchanged cases plus three preregistered dependency cases
against the revised contract: 10/10 expected decisions. See
probes/observed-revised.json for exact input/rule hashes and limitations.

The real input passed G0 under another independent worker. G1 returned
decision_pending for appetite and walk-away provenance. No full-run success or
later-stage exercise is claimed. Private full receipts remain with the local
exercise, outside this public repository.

## Supplemental reference exercise

The user's request to compare actual framed/shaped examples and Discovery work
produced a bounded source comparison and four constructed cases across two
independent axes: complexity and initial vagueness. Two authors each handled two
cases, retaining two rounds; independent reviewers assessed each batch.

Round 1 caught missing framing decisions, unresolved critical chat seams,
configuration race/empty/capacity gaps, overlong pitches and actual Mermaid
sequence parser failures. Round 2 used explicit new scenario inputs, shortened
the decision pitches and resolved the configuration contract gaps. The independent
review supports G0–G2 for three cases but holds G3 at 47/12; chat still holds G2.
Configuration rose from 34/12, with new inputs as an explicit confounder. Capacity
remains 47/12 despite useful editorial improvements and a limited schema check.

The controller then inspected all nine PNGs, repaired overflowing sequence notes
and one ignored palette, rerendered three sequences and recorded final hashes.
Native HTML rendered nine SVGs; long diagrams now pan instead of shrinking into
unreadability. No Google Doc or Bet-ready receipt was fabricated. The full
before/after findings and a rubric-calibration question are in examples/README.md.
