# Executed Improvement Loop

Read this complete resource before an experiment-mode mutation. A dry-run, drafted candidate matrix, or simulated score is not an executed trial. Record actual tools, runtime/model settings, candidate content identity, and evaluator results. If required execution or judging is unavailable, state the limitation instead of fabricating trials.

## State and Evaluation Boundary
Preserve three identities: original baseline (immutable reference), incumbent (best accepted state), and trial (isolated candidate derived from the incumbent). Protect evaluator code, evaluation data, scoring rules, limits, and comparison settings from trial edits. Changing the measurement system requires a separately declared experiment; do not improve the score by changing its definition.

Define acceptance before mutation: quality gains within hard constraints, or demonstrated equivalent quality with worthwhile speed/cost/simplicity gains when those are objectives. Define regression limits, tie behavior, repetitions for noisy outcomes, and stopping rules. An aggregate score cannot hide a hard failure. For nondeterministic evaluations repeat enough to resolve the declared decision or report inconclusive.

## Loop
1. Run and record the original baseline; initialize the incumbent from it.
2. Form the next plausible improvement hypothesis. Mutate one or several coordinated elements within the editable scope, recording the exact set and joint hypothesis. Use single-factor changes when attribution matters; acknowledge interactions when several changes are combined.
3. Execute the protected evaluation on the isolated trial under comparable conditions. Record invalid/crashed trials separately from quality regressions; fix the harness only through its own controlled work, not by disguising a measurement change as a candidate win.
4. Compare against the incumbent and original baseline using the declared objective. A real gain advances the incumbent. A tie follows the declared rule (for example, retain equivalent quality at lower verified complexity). A regression or unresolved result does not advance it.
5. Record the decision and evidence before changing state. Discard only rejected trial-owned active changes, retaining its scores, trace references, hypothesis, and useful lesson. Restore the incumbent as the next starting state. Never reset unrelated work or broadly delete evidence.
6. Explore again after both wins and losses, using lessons to choose the next hypothesis. Stop only under the agreed trial limit, budget, target, plateau, or user interruption.
7. Recheck the retained best against the original baseline and required regressions. Report no improvement or inconclusive when justified. Keeping an incumbent is distinct from formal promotion, installation, release, or merge.

## Stopping and Evidence
A diagnostic task can end with a verified explanation and fix. An optimization request continues through trials until its declared boundary; the first win alone does not finish it. A plateau requires the agreed number of distinct unsuccessful hypotheses under a stable evaluation. It means no improvement was found in the explored space, not proof of a global optimum.

Keep candidate generation separate from evaluators and, where judgment is needed, use independent reviewers or qualified scorers. Do not expose held-out evaluation answers to candidate generation. Trial acceptance is provisional to the evaluated scope; claims of transfer require separate evidence.

## Foundation and Deliberate Adaptations
[Karpathy's original program instructions](https://raw.githubusercontent.com/karpathy/autoresearch/master/program.md), checked 2026-09-08, motivate repeated mutation, execution, scoring, keep/discard, and further search. The original targets a specific training script and fixed evaluation budget. This skill generalizes the mechanism to prompts, skills, tools, and workflows with task-specific limits, noise handling, authority boundaries, and independent judging. Its bounded stopping and promotion controls are deliberate adaptations, not attributed original requirements.
