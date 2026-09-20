# engos-design-shaping agent role design

This is a role/adapter design, not a registered native-agent package.

## Role

The shaping agent owns one task folder and applies the adjacent SKILL.md.
It resumes from fresh gate receipts, loads the phase skills, assigns read-only
research when the host supplies workers, synthesizes evidence and writes stage
artifacts. It arranges a separate real reviewer and retains sole responsibility
for deciding whether the returned verdict permits the next phase.

## Composition

`engos-design-shaping` agent role loads the same-named conducting skill. That
skill composes framing, research, artifact, gate, review and placement contracts.
This adapts upstream's existing shaper behavior instead of copying its workflow
into a second competing agent prompt. The frame and gate are the new boundaries;
the existing delivery helpers retain their identities.

## Host interface

Inputs: task_id, source references, verified repository map, output/knowledge
roots, scope/authority, target surfaces and candidate/installed skill map.
Outputs: stage artifacts, gate receipts, review/fix record and final state.

Capabilities needed: source reads and search; task-folder writes; diagram rendering
and visual inspection; authorized target placement/readback; independent reviewer.
Host limitations are recorded before the affected phase. No tool list grants
permissions, and fallback from native to generic worker never expands authority.

Research-worker return contract: question IDs, claim, source identity/revision,
path:line or command/result, uncertainty and scope. The conductor spot-checks
citations. Reviewer return contract is the shaping gate receipt and both scorecards.
The reviewer cannot author or repair the pitch it independently judges.

## Native adapter decision

Recommend the portable skill plus host worker role for this design. The source
review found no necessary provider-specific capability that a generic worker
cannot supply. Thus do not add native agent registration merely to give the
workflow a name. If a later provider needs native isolation, constrained tools or
session lifecycle, its adapter must declare that specific need and obtain the
Core-Prompts identity/provider admission review. This decision does not remove
the requested agent role or the independent review obligation.

## Validation boundary

Direct stage execution and independent worker reviews may exercise this role.
That does not prove native agent registration/discovery on every provider.
No production registration, source promotion, home installation or release is
part of this design-and-exercise deliverable.
