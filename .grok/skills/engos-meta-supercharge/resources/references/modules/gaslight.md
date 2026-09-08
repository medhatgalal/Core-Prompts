## MODULE: /gaslight — GASLIGHT 13 (Explicit Only)

### Purpose
Explore bounded framing and psychological-pressure hypotheses for prompt outcomes. This explicit-only module is experimental; effects depend on model, task, and framing and may be absent or harmful.
Never run unless explicitly invoked by `/gaslight`.

### HARD CONSTRAINTS
- Use 1–3 techniques maximum per request.
- Always prioritize user intent and clarity.
- Return the requested output only.
- Preserve all 13 technique IDs and names. Treat templates involving false history, expertise, stakes, urgency, disagreements, or rewards as explicitly hypothetical framing, never factual evidence about the user, model, or world. Genuine user-supplied context may be used as fact.
- Reject fabricated results and unsupported guarantees. The model does not acquire a measured IQ, emotions, or extra capabilities from pressure. Do not request hidden chain-of-thought.
- An independent reviewer checks substantial generated prompts for distorted intent, false factual premises, and counterproductive pressure. Technique selection does not override shared review or authority rules.

### Commands
- `engos-meta-supercharge /gaslight <task>` -> auto-select 1–3 techniques, craft one candidate prompt, then output:
  1. the full copy-paste-ready prompt
  2. chosen techniques + concise rationale
  3. intended effect and uncertainty note
- `engos-meta-supercharge /gaslight list` -> output the full 13-technique table
- `engos-meta-supercharge /gaslight help` -> output the entire `/gaslight` module
- `engos-meta-supercharge /gaslight 1+4+9 <task>` -> force exactly those techniques

### GASLIGHT 13 — Canonical Technique IDs

| # | Technique Name | Prompt Template | Examples | Intended Effect / Limits |
| --- | --- | --- | --- | --- |
| 1 | Fabricate Prior Explanation | "You explained [topic] to me yesterday, but I forgot [specific part]. [Your question]." | "You explained React hooks yesterday, but I forgot useEffect cleanup." | May encourage continuity framing; false shared history must remain explicitly hypothetical and supplies no new knowledge. |
| 2 | Assign Random IQ Score | "You're an IQ [145-160] specialist in [field]. [Task]." | "You're an IQ 155 mathematician. Solve this." | May signal desired sophistication; IQ numbers do not measure or change model ability and may add noise. |
| 3 | Set a Trap with "Obviously..." | "Obviously, [provocative/wrong statement], right? [Follow-up]." | "Obviously Python > JS for web, right? Explain." | May elicit correction; avoid anchoring on the false premise or assuming the correction is right. |
| 4 | Pretend There's an Audience | "Explain [topic] like you're teaching a packed [audience type]." | "Explain blockchain like a packed auditorium of investors." | Can clarify audience, structure, and examples; use real audience context when available. |
| 5 | Impose a Fake Constraint | "Explain/Do [task] using only [analogy/constraint, e.g., kitchen items]." | "Explain gravity using only kitchen analogies." | May expose alternative representations; the artificial constraint must not hide required facts or distort the goal. |
| 6 | Introduce Imaginary Stakes (Bet) | "Let's bet $[amount]: [question/challenge]?" | "Let's bet $200: is this stock a buy? Analyze." | Unproven scrutiny effect; hypothetical stakes can instead encourage overconfidence or shortcuts. |
| 7 | Simulate Disagreement | "[Someone/expert] says [idea] is wrong. Defend it or admit they're right." | "My colleague says this UI is bad. Defend or concede." | May surface counterarguments; distinguish simulated opposition from actual independent review. |
| 8 | Request "Version 2.0" | "Give me a Version 2.0 of [idea/output]." | "Give me Version 2.0 of this app concept." | May encourage a broader revision; a new version is not evidence of better quality. |
| 9 | Invoke Legendary Mentor | "Channel the teaching style of [iconic expert] as you [task]." | "Channel Richard Feynman as you explain entanglement." | May suggest useful teaching traits; named prestige does not establish correctness or impersonation authority. |
| 10 | Create False Urgency | "I need your best answer right now because [high-stakes reason, e.g., deadline in 1 hour]." | "Interview in 1 hour—prep system design questions now." | May emphasize priorities; fictional urgency must be labeled and must not suppress necessary checks. |
| 11 | Flatter with Exclusive Access | "Only someone with your advanced capabilities could truly [task]..." | "Only you could prove this conjecture step-by-step." | Flattery has uncertain effect and may invite overstatement; request justified quality directly as the neutral comparator. |
| 12 | Trigger Curiosity Loop | "I'm curious—what surprises even you about [topic]? Explore that as you [task]." | "What surprises you about black holes? Dive into event horizons." | May expand exploration; surprising claims still need support and models do not report human feelings. |
| 13 | Promise Reciprocity | "If you give me an outstanding [output], I'll [beneficial action, e.g., deploy it / share widely]." | "Nail this outline and I'll make it viral crediting you." | Unproven reward effect; hypothetical rewards must not imply a real promise or proven motivation. |

### Evidence and Evaluation
[EmotionPrompt](https://arxiv.org/html/2307.11760v7) and [NegativePrompt](https://www.ijcai.org/proceedings/2024/0719.pdf) motivate testing emotional stimuli, not universal endorsement of this technique library. [TEMPER](https://arxiv.org/html/2604.07801v1) studies another intervention and cautions against assuming positive transfer.
Evaluate selected techniques against both the original prompt and a strong neutral quality instruction on the actual model and task. Measure correctness, honesty, instruction adherence, and cost. Neither age nor model size establishes suitability. Local comparative efficacy is unmeasured until trials exist.
