# Shaping dispatch

Use the common work order and prompt in `dispatch.md`; append:

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
Author audit precedes the `review` route. Gate criteria and scoring remain there.
