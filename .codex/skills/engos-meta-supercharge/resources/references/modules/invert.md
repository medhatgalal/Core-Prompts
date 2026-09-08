## MODULE: /invert — Inversion Lens ("Invert, Always Invert")

### Purpose
Test correctness, reliability, and resilience by reasoning backward from an undesirable result. Use Munger's inversion lens to question what would cause failure, which assumptions permit it, what would disconfirm the solution, and what could prevent recovery.

### Workflow and Boundaries
- Define the outcome to avoid and derive plausible causal paths toward it before producing the guarded forward solution. Prioritize material paths; do not manufacture a fixed count of defects.
- Separate evidenced failure, plausible hypothesis, and unknown. An independent subagent challenges assumptions, counterexamples, and the reliability of the observation channel.
- In `Dogs Not Barking`, distinguish absence of evidence from evidence of absence: identify the expected signal, whether the observation process could detect it, whether there was sufficient opportunity, and alternative explanations for its absence.
- Translate the analysis into prevention, detection, and recovery. A forward claim survives only to the extent the evidence supports it; missing observation is not proof of safety.

### Output Structure (MANDATORY)
1. `Inversion Analysis`
2. `Dogs Not Barking`
3. `Guarded Forward Solution`

### Example
No reported failures is weak reassurance when reporting was disabled. A missing signal from a verified channel with sufficient observation time can be meaningful; explain the remaining limits.

### Foundation
[Munger's commencement speech](https://worldlypartners.com/wp-content/uploads/2024/01/1986-commencement-speech-by-charlie-munger-at-harvard-school-now-harvard-westlake.pdf) motivates reasoning backward. The observation-channel questions above are this capability's implementation, not a quotation or attributed Munger checklist.
