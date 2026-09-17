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
