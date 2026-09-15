# Explicit agent approval and skills-only distribution

## Source result

Core-Prompts ships 27 capabilities as 135 skill entrypoints and zero named-agent entrypoints. Eleven stock agent variants were retired across Codex, Claude, Gemini and Kiro; Grok already had no stock agent package. Skill bodies are unchanged for those eleven retirements. UAC's own instructions now preserve requested surface scope and require explicit user approval before adding an agent.

## Approval boundary

A recommendation, quality score, independent review, declaration of `both`, or `--yes` does not authorize a new agent surface. The existing UAC requirement-review record carries a separate `user_approval` with source, decision, capability slug, provider identities, and actual request reference. These are scoped attestations, not authenticated identity tokens; operators must not invent approval.

Existing agent improvements can carry an actual prior approval through fresh independent review bound to the current source and resources. Retirement clears old admission records; restoring the former agent text cannot silently reactivate approval. Git release history cannot grandfather explicitly retired registrations back into existence. No additional registry was introduced.

## Retirement and preservation

The existing catalog identifies the exact retired agent kind/provider/slug, while skill successors remain active. Recognized agent-only installations migrate to the skill for the same job before the old files are removed. Unknown, customized, symlinked, missing-counterpart and dependency-conflicted packages are preserved. Ownership, selection, registration changes, rollback and standalone runtime integrity use the existing transaction engine.

The metadata-only UAC path reports `user_directed_agent_retirement`: only capability_type changes, all other committed source bytes stay identical, and the catalog must explicitly identify the retirement. It does not claim a new template pass or runtime equivalence. Generic independent workers remain available.

Actual v1.14 routine and addition-only migration refuse removed bundle scope without changing target state. Tests verify upgrading through the current installer's reviewed repair plan, followed by operation without source-checkout access and reverse-order recovery.

## Verification

- Final combined regression run: **539 passed, 16 subtests passed** in 189.27 seconds.
- Strict surface validation: passed, 27 SSOT sources.
- Contract compilation: passed, no drift.
- Static calibration: passed, zero model calls; semantic judge qualification is not claimed.
- Installer capsule and historical catalog: verified.
- Scoped registration pruning and package privacy checks: passed.
- Subsequent approval-lifecycle recheck: 16 passed, including direct generator retirement revoking old admission as well as UAC apply.
- Independent review found and verified fixes for retired-identity grandfathering, approval reuse during improvements, and stale approvals surviving retirement.

Removing an adapter does not prove generic-worker behavioral equivalence. No new native behavioral comparison is claimed. Existing historical source-fidelity review requirements, including Supercharge's historical heading check, have not been waived or promoted.

## Pre-merge home checkpoint

This is a historical preview, not a claim of installed parity. The five-harness preview has no global blockers. Eleven owned Codex agent definitions are eligible for removal. Thirty-three unrecognized Core-named agent packages (86 files across Claude, Gemini and Kiro) require the user's separate archive choice; no external agent-file dependency or named default setting was detected for that set. Other unrecognized/customized skills, including the installed Claude UAC copy, remain preserved. No home write had occurred at this checkpoint.

Raw home plans and custom-package contents are private and are not committed here. Source UAC receipts are summarized in `uac-receipts.json`. Subsequent delivery and installed-state evidence belongs in the PR/MR for branch `AI/explicit-agent-approval` and its verification comments.
