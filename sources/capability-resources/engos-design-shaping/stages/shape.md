# Shaping dispatch

Use the common work order and prompt in `dispatch.md`; append:

Read architecture-fit.md. Include evidence-backed reuse/non-reuse decisions for
material capabilities/seams in pitch.md, with conditional specialist contributions.
No positive reuse finding or implementation refactor is required to shape a pitch.

## Select one supported set

A confirmed decision that opened code does not perform is a proposed extension.
Name the existing seam and the proposed behavior separately. Do not invent an
existing capability, but do not confuse its absence with an exclusion of a grounded
extension. One example of this pattern is proposing a confirmed state change that
the opened implementation does not yet perform, rather than selecting nothing.
Judge the pieces together:
one piece too small alone does not discard a set that delivers the accepted frame.

Record selected piece IDs and existing/proposed-extension claims in shape-set.json
under the current runtime policy. A set that selects nothing is a hold naming the
load-bearing walk-away item, not a pitch for the twelve scores. Stop before review.
Do not manufacture a trivial selected piece to bypass this semantic check.

Before reviewer dispatch, check each load-bearing existing claim against accepted
G2 research-coverage.json and the actual opened source. A missing or false fact
returns to G2; do not spend G3 review to discover an already visible research gap.
Proposed extensions need grounded existing basis claims; their new behavior need
not be implemented during shaping. An unsupported assumption masquerading as a
proposal remains a research gap. Keep research reviews' code-agreement standard.
Recheck material callee claims before reviewer dispatch: a caller citation alone
does not establish the callee body. Return an unopened implementation dependency
to Research rather than spending the pitch review to discover it. An inaccessible
body requires the assigned evidence route and an honest gap, not invented behavior.

> Act as the shaper. Verify the current passing frame/research and accepted
> decisions, then compare bounded options and rough out the smallest supported
> solution. Explain why it fits the actual appetite and walk-away. Write the
> complete shaped bundle using templates/shaped-bundle.md and the resolved
> artifact author's resources. Challenge dependencies, usability, security, cost
> and recovery; cite risks or mark concerns as hypotheses. Separate proposed seams
> from existing behavior. Return candidate artifacts, evidence, unanswered material
> questions and decision requests. Do not score your work as independent review,
> publish, implement or approve a bet.

Keep component, sequence and data-flow diagrams, full contract and security tables
even for a small appetite under this full-shaping profile. If the appetite cannot
support the required set, expose that conflict; do not silently omit artifacts.
Use Mermaid source and the artifact helper's style; an alternative requires a
documented expressiveness limit and retained source. Inspect actual rendered pixels.

The conductor uses the team decision pause in ways-of-working.md only within
the requested scope. A bet may be offered only when component.mmd, a real
sequenceDiagram in sequence.mmd, and the data contract exist with meaningful,
consistent content. Empty files and headings do not count. The full data-flow
and security bundle remains required; a package with a known material gap is not
eligible for the bet question. This completeness check is not G3, G4 or a human bet.

Only if the team already sizes work by layer, use its own layer names and scale.
Each named layer needs an owner and a size with provenance, or an explicit decision
that it is not involved. An empty size stays unknown and missing. Do not infer zero,
require a fixed layer count, prescribe a non-involvement code or calculate capacity.
Record applicable sizing in the existing bundle, not a new tracker.

The contract's interface entry is a cited interface, an identified in-process
interface, or the exact token no API. A network API is optional. Input/output
meaning, producer, consumer, state, evidence and owner remain required. Do not invent an endpoint, method
or schema when the person asks to add an API; missing basis evidence returns to
Research. The builder will choose is not a sequence, a component, or a data contract.

Cover component/caller identity, input/output meaning, material failure/timeout/
retry and consistency semantics, trust boundaries, enforcement owners, persistence
and non-responsibilities. Compare diagrams and table rows for semantic agreement,
not just counts. An unassigned critical security owner or contradictory sequence
is a gap even when every file exists. Leave non-load-bearing internals to builders.

Include In/Out/Later, ordered safe cuts, mitigations and load-bearing No-Gos.
Cuts must preserve core outcome, usability, quality and security; state when no
safe further cut remains. Design one pitch-wide proof slice and coarse workstreams
with observable first slices, not a production ticket breakdown. A new technical
unknown returns to Research; changed outcome/scope/appetite returns to Framed.
The proof slice must observe the accepted frame's requested completion or stop
condition, not merely an intermediate action. One example of this pattern is a
proof that observes initiation but never observes the required user-visible result;
that proof is insufficient. Describe the observation as a future
acceptance check unless it actually ran. No proof or ownership is invented.
Every proposed in-item also needs one proof sentence stating its observable
completion. Record each deferred item with a reason and its need for a separate
pitch; retain forbidden lines verbatim. Safe cuts are shaping proposals only:
after table acceptance nobody may drop a build-these line. Write no downstream
spec, requirements, design, architecture document, plan or task list.
Author audit precedes the `review` route. Gate criteria and scoring remain there.
