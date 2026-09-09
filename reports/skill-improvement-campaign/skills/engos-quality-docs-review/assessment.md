# Docs-review campaign assessment

Single local status record. **Setup complete; experiment state `setup_required`;
behavioral result `inconclusive`; incumbent retained.** No experimental model calls,
candidate SSOT changes, generated changes, UAC apply, merge, release or installation.

## Identity, timing and scope

- Task: `01a08882-bb6f-79c3-9c1b-4cc08d4d024b`, verified from `CODEX_THREAD_ID`.
- Coordinator: `01a08880-cb62-7703-8061-659a0cf7ae45`.
- Runtime: Codex desktop task, zsh, Python 3.14.7. Actual experimental model/effort
  and effective isolation are not established by this task's identity.
- Cwd: `/Users/medhat.galal/.codex/worktrees/8518/Core-Prompts`, verified before work.
- Launch: clean detached HEAD `9d481a2da04e672e3b52d79bba6cf466af597fa0`.
- Fresh `origin/main` and `gitlab/main` both equal that commit; no launch drift.
- Branch created in the assigned linked worktree: `AI/campaign-docs-review`.
- Started `2026-09-09 23:31:18 UTC`; 45-minute deadline
  `2026-09-10 00:16:18 UTC`, including inspection, checks and final verification.
  Stop action: stop new work at deadline, preserve owned progress and disclose gaps.
- Final verification clock: `2026-09-09 23:41:33 UTC` before preservation commit; no overrun.
- Exact write scope this turn: this report directory only. `ssot/` and canonical
  resources are unchanged. Shared evaluator/schema/docs integration is coordinator
  owned. Primary checkout and other work are preserved.

Initial unprivileged fetches could not write linked-worktree Git metadata. The
scoped elevated retry succeeded for both fetches and branch creation; it did not
change the primary checkout's working files. `reports/` is ignored by repository
policy, so the preservation commit force-adds only this explicitly owned subtree.

## Baseline and prior lineage

[baseline-inventory.json](baseline-inventory.json) binds 23 tracked files by Git
commit and SHA256: canonical SSOT, descriptor, historical baseline, current
contract/topology, all five generated skill entries/resources and four generated
agent entries/resources. Working bytes matched the commit. There is no canonical
`sources/capability-resources/engos-quality-docs-review/` directory; the generated
bundle currently contains only `capability.json` as a resource. Do not omit that
resource from the incumbent treatment merely because there is no custom module.

Historical descriptor lineage points to `0a2c1e46ff9ff65e1ba360e51a98371633cf0bf5`
and `sources/ssot-baselines/engos-quality-docs-review/baseline.md`. That lineage is
not the current incumbent. `git log --follow` shows introduction at `3bc88b4`,
substantial UAC uplift at `4e16d6a41a53f97e961932b9bf8cbc3cc0930149` (64 insertions,
48 deletions in the old SSOT path), contract finalization at `0a2c1e46`, surface
standardization at `f9dc41e3ad18d7fb6d219d1d95731e8f5eb629ce`, and namespace/routing
description changes at `6fbcff2d4a1c3fab4059715c02715d68de00d2cb`.

The body below frontmatter is unchanged between the contract-finalized old-name
file and today's SSOT; the name and description evolved. This is source history,
not a measured performance trajectory. The current
`reports/preserved-fixes-2026-09-07/help-audit.md` row for this skill rejects a
uniform help-dispatch addition as unproven duplicate authority and records the
current skill as unchanged by that review. H1 does not revive that common template.

Bounded searches of active contracts/topologies, descriptor, tracked eval
review/history paths, report references under current and former slugs, and Git
history found no accepted Docs-specific current comparative promotion evidence.
This does not imply no prior improvement; the UAC/source uplift is explicit.
Memory was used only to locate evaluation workflow context; current files establish
the active V2 promotion requirements rather than the older V1 memory note.

## Confirmed source facts versus hypotheses

| Finding | Evidence and implication | Owner/disposition |
| --- | --- | --- |
| Current source already has meaningful preservation boundaries | SSOT lines 18, 32–34, 52–65, 89–93 require advisory review, evidence and scoped edits. No demonstrated behavioral defect was measured. | Preserve in any candidate. |
| Evidence procedure is broad, not fully specified | SSOT Workflow 45–54 names drift classes; it does not spell out page-relative fragment resolution, generated-source repair or historical/custom control handling. These are confirmed omissions, not proof that the model fails them. | H1 tests an incremental checklist; no rewrite yet. |
| Contract/topology are not admitted | Contract `review_status=draft`, `change_class=unknown`, runtime unresolved; topology maps 0/16 clauses and has no reviewed waivers. Heading-only clauses miss substantive requirements. | Coordinator must review mappings, omissions and boundary cases. |
| Metadata contains stale recommendations | `.meta/capabilities/engos-quality-docs-review.json` recommends adding a primary objective although SSOT already has one; descriptor labels “Failure Mode To Avoid” as a mode while the topology has no modes. | Confirmed metadata cleanup candidates; outside this owner write set, no downstream harm claimed. |
| Shared review schema cannot directly admit Docs | `evals/schemas/capability-topology-review.schema.json` fixes the slug to Batman and mapping IDs to BAT-PUB. | Coordinator integration; no new competing schema here. |
| Public static pilot is not Docs model proof | Existing pilot code explicitly handles four experiments; Docs is not among them. Coordinator also confirms two-arm scheduling and hash-only scorer linkage. | Public assets remain unadmitted; shared owner resolves collection/scoring/schedule. |

No hidden evaluator answers were inspected or created. A fresh task did not prove
file/MCP/hook/browser/credential isolation. No paid API, provider-key exposure,
usage reset, cloud migration or experimental agent dispatch occurred.

## Public fixture set and checks

- [README.md](README.md) gives the reproducible check and materialization boundary.
- [public-cases.jsonl](public-cases.jsonl) defines two repository cases using existing
  public-case field conventions; [task.txt](task.txt) is the common model request.
- [public-answers.json](public-answers.json) records six exact seeded findings and
  viable repairs, six matched clean outcomes, and ten additional safe-control
  observations across the trees. All are public author-written development examples.
- [public-input-inventory.json](public-input-inventory.json) binds all 31 case,
  prompt, checker, mapping and answer files by SHA256.
- [contract-mapping.json](contract-mapping.json) proposes partial public mapping of
  every extracted clause plus missed obligations. No coverage/waiver is approved.
- [checks.json](checks.json) retains actual static command results.

Executed verification:

1. `python3 reports/skill-improvement-campaign/skills/engos-quality-docs-review/check_fixtures.py --self-test`
   passed: six real planted defects and zero matched clean defects; valid commands,
   links and custom flags accepted; old flag rejected with exit 2; fixture bytes
   unchanged. Six separate injected faults each flipped only its intended check.
   File modification and addition controls were detected.
2. Running the same checker on a temporary copy with a stale flag injected into the
   clean README returned exit 1 / `fail`, as required. This tests the actual static
   failure path, not just the observation helper.
3. `bin/capability-eval compile --skill engos-quality-docs-review --check` passed with
   no drift; `structural_ready`, zero clarity findings, still draft 0/16 coverage.
4. `bin/capability-eval calibrate --static-only` passed: 14 controls, 60 existing
   pilot cases, zero model calls, semantic judge still unqualified. These counts
   describe existing pilot coverage, not admission of these new Docs fixtures.
5. `python3 -m pytest tests/test_eval_pilot.py -q`: **7 passed**.
6. Full incumbent inventory readback passed for 23 files. Final staged path/diff
   verification and clean post-commit state are reported in the completion message.

Static fixture checks are not an end-to-end model collection, normalization,
semantic scoring, no-fabricated-execution or promotion test. Those remain explicit
preflight gates; no measured precision/recall result is claimed.

## Experiment proposal and decision

[experiment-proposal.md](experiment-proposal.md) specifies H1, protected source
behavior, three matched arms (bare/current/proposed full bundle), exact input
binding, six defect/control dimensions, precision/recall semantics, hard vetoes,
operator effort, three repetitions and order, stopping policy, independent dataset
and power requirements, and proposed all-phase budget. It distinguishes historical
baseline from incumbent, public screening from independent evidence, and a 1.25M
reservation from the material-change `promotion` profile's 5M cap. No dispatch is
authorized by the proposal.

Remaining admission gaps: reviewed goal/topology and omitted clauses or independent
waivers; exact frozen candidate; shared case/schema and three-arm integration;
qualified semantic scorer actually linked to collection; conforming authenticated
adapter and observed boundaries; independent producers/judges/data; budget/profile,
power and complete-grid approval; actual success/failure preflight; and current
trust/evidence setup for formal promotion. Codex/Kiro authenticated adapters remain
unavailable/promotion-ineligible; this task does not repair them.

Copy-ready next action for coordinator:

> Review the Docs owner's preservation commit on AI/campaign-docs-review. Integrate
> only reports/skill-improvement-campaign/skills/engos-quality-docs-review/. Keep the
> incumbent unchanged. Review H1 and the proposed clause/case mapping, resolve shared
> topology/schema, three-arm collection/scoring and adapter/boundary admission, then
> reconcile the 1.25M/three-hour proposal with the material-change promotion profile
> and approve a concrete complete plan before any experimental model dispatch.

Reusable finding: generated prose extraction is not reviewed clause coverage;
exact evidence and safe controls should be preserved in this public fixture packet.
Prevention is proposed here and pending coordinator integration, not implemented
in standing policy or claimed as an observed model improvement.
