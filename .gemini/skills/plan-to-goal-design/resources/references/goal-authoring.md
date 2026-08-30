# Goal Authoring for Long-Running Coding Work

## Decision Rule
Keep the repeatedly injected goal small. Put repository evidence, requirements, file maps, task detail, and research in the specification. A large context window does not remove the cost of repeatedly interpreting a crowded objective.

Use one observable outcome. A conjunction is acceptable only when every part is judged by the same verifier and has no independent value, owner, or approval boundary.

Write the outcome anchor and freeze its identifier population before writing the implementation plan. Attack whether the anchor can move without the outcome, be forged, miscount awkward cases, or target an unreachable population.

## Size Contract
- portable compiler cap: 3,500 Unicode characters and 3,500 UTF-8 bytes
- target: about 800 characters
- measured post-extraction examples: 914-character goal and 968-character prompt
- warning above: 1,200 characters
- Kiro CLI 2.20.1 measured documentation limit: 4,000 characters
- Codex persisted objective limit: 4,000 characters

The preferred range is a heuristic. Validate it behaviorally instead of calling it universally optimal.

## Seven Labels
Use `OUTCOME`, `READ FIRST`, `BEFORE EDITING`, `WORK`, `GUARDRAILS`, `DONE`, and `STOP / REPORT` once and in order. Labels provide a portable review contract; no source establishes that Markdown itself improves every model.

Keep only:
- one outcome
- durable artifact paths
- the mandatory revalidation step
- the execution invariant
- three to five high-risk guardrails
- verifier, trust level, and manual gate
- terminal and receipt behavior

Move everything else to `spec.md`.

## Decomposition
Split when outcomes have separate value, verifiers, owners, or approvals, or when no one verifier can judge the whole result. Carry state through a compact receipt. A receipt summarizes completed evidence but never replaces re-reading current repository state.

Do not derive an iteration count from milestone arithmetic. Honor a user bound; otherwise use a verified native default and stop earlier on achievement, material drift, an approval boundary, or no progress.

## Verifier Design Order
1. Define the world-state outcome and frozen population.
2. Write the anchor criterion and baseline before mechanism tasks.
3. List the cheapest fake for each criterion and the corresponding block.
4. Build a cheapest-fake hostile tree that satisfies convenient mechanism checks without the outcome.
5. Require the verifier to fail on both untouched and hostile trees for a named anchor or criterion.
6. Publish the exit-gate truth table and answer PROXY, FORGERY, ARITHMETIC, ACHIEVABLE, and TRAP.

## Sources
- Kiro Goal: https://kiro.dev/docs/cli/chat/goal/
- OpenAI long-running work: https://learn.chatgpt.com/docs/long-running-work
- Codex goal file implementation: https://github.com/openai/codex/blob/main/codex-rs/tui/src/goal_files.rs
- Claude Code permission modes: https://code.claude.com/docs/en/permission-modes
- Gemini CLI Plan mode: https://geminicli.com/docs/cli/plan-mode/
- HIPIF: https://arxiv.org/abs/2606.10507
- Subgoal-driven long-horizon agents: https://arxiv.org/abs/2603.19685
- Coding agents as long-context processors: https://arxiv.org/abs/2603.20432
- Prompt-induced waste: https://arxiv.org/abs/2608.01347
- Prompt design at scale: https://arxiv.org/abs/2607.19257
- Goal-design lessons bundled with this skill: `resources/references/goal-design-lessons.md`

URLs were checked on 2026-08-29. Model- and host-dependent claims must be refreshed before changing adapters.
