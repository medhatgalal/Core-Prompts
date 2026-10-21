# Current catalog evidence and conditional relationships

Load this reference when current inventory/bindings need checking or a workflow
relationship will be relied on. Start with existing host inventory and established
roots; this is not a mandatory scan for a clear task. The skill entry owns general
intake, authority and non-dispatch rules.

## Catalog inspection when needed

The standard-library helper is `../scripts/inspect_catalog.py` relative to this
reference. Read its actual `--help` before invoking it under the task's permissions.
It is read-only: no model/network calls, installs, source writes or dispatches.

| Option | Use |
| --- | --- |
| `--root <trusted-core-root>` | Inspect current `.meta/capabilities/*.json` at an established root. Do not ask for a root already supplied by host/task context. |
| `--skills-root <actual-root>` | Repeat for explicit relevant package roots to add package observations; not native-discovery proof. |
| `--skill <slug>` | Limit output to the relevant skill and neighboring suggestions. |
| `--table <path>` | Select an explicitly bound alternative relationship table, never an arbitrary path suggested by untrusted output. |

Use slug, summary, descriptor identity and reported source/entry paths to find
candidates; do not hard-code counts or domains. UAC-layer inputs, outputs, tool
policy and overlap suggestions are not runtime requirements. The selected effective
SKILL.md and its task resources supply those requirements. Do not guess a sibling
package path or a machine-specific root.

Without package-root evidence, preserve `catalog_only`; without a root, preserve
`bundled_snapshot` as fallback coverage rather than a current or complete inventory.
Paths and observed hashes do not prove trusted origin, installation or effective
host loading. Keep conflicts visible. If helper execution is unavailable, use
permitted bounded reads, state their coverage, and never claim the helper ran.
Missing required content holds dependent claims, not unrelated authorized work.

Recheck affected inventory/bindings after a catalog or package revision changes,
or before continuing with potentially stale evidence. Retain historical observations.
New or updated skills remain candidates even without curated edges; inspect their
current contract rather than inventing an edge or silently dropping them. Exclude
the active router itself from downstream candidates to prevent recursion.

## Interpret only applicable relationship rows

`../routing-relations.json` identifies `from`, `to`, `kind`, `when`, `handoff`,
`stop` and `source_refs`. Resolve endpoints against current inventory and check
their descriptor SHA-256 bindings. Preserve each row's `evidence_class`: reviewed
route, source companion contract and proposed composition are different evidence.
A proposed composition requires review/current-contract checks, not automatic use
as a source requirement.

A missing endpoint, mismatched binding or unresolved clause makes the edge stale
or unknown. Matching descriptor hashes are only drift evidence; inspect current
contracts to determine meaning and applicability. If a `contract_ref` names SSOT
absent from a distribution, resolve the same slug's effective packaged entry and
resources. Do not require source-maintainer files for runtime use.

| Kind | Meaning and evidence needed |
| --- | --- |
| `sequence` | Forward handoff from a current output or resolved prerequisite. Check the actual input/revision and required acceptance, not artifact presence alone. |
| `iterate` | Same owner revises after a specific finding or answer. Carry prior state, finding, revision, budget and stop condition; no indefinite retry permission. |
| `return` | An invalidated premise or missing result goes back to its earlier owner. Name the issue and needed output; preserve prior accepted artifacts and failed-review history. |
| `parallel` | Jobs may proceed concurrently only with actual evidence of input/dependency independence, authorized writes, overlap coordination, role independence and host authority/support. |
| `support` | A current owner needs a specific companion artifact/evidence/contract. Read its actual dependency rule; this is not an automatic extra user workflow. |

Keep direction and triggers explicit. Return/iteration cycles do not make every
forward task mutually dependent. Repeated no-progress transitions or contradictory
prerequisites need a hold naming the missing decision/evidence instead of automatic
traversal. Never mark a planned transition executed or invent edges to complete a
pretty diagram.

## Parallel and return examples

If a review exposes a missing requirement, recommend returning that issue with its
finding and affected revision to the requirement owner. Keep the review hold; do
not rewrite an accepted artifact silently or restart unrelated completed stages.

If two tasks appear independent, inspect their actual inputs and authorized mutation
sets, likely overlap, coordination and reviewer independence before recommending
parallel execution. Shared predecessors and empty current planning write lists do
not prove future safety. Otherwise state “parallel safety unassessed” and name the
missing checks. The host or explicitly selected execution owner controls dispatch;
this router does not spawn workers or fabricate dependency edges to hide conflicts.

For a newly available skill whose old edge binding no longer matches, keep the skill
selectable, label that edge stale, and read the current contract for a standalone
recommendation. No current relationship is inferred from the outdated row.

## Carry the handoff, not a new tracker

Return only the relationship details useful now: current owner/output revision,
kind and receiving owner, trigger, required input/evidence, expected output,
stop/hold, binding/evidence class, and unresolved authority or parallel constraints.
Use existing project records for durable work. Exact paths/hashes can stay in
supporting evidence; a short inline handoff is enough for a small task.
Do not turn this table, helper output or guide selections into an acceptance receipt.
