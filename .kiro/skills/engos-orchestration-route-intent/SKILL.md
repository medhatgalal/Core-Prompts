---
name: "engos-orchestration-route-intent"
description: "Interpret a user's task across the current Core-Prompts catalog, recommend the first useful job and depth, ask only consequential missing questions with a free-text Other option, and prepare conditional handoffs without granting new authority. Use for vague requests, uncertain skill choice or workflow continuation across any supported domain; skip redundant intake for clear direct tasks."
---
# Find the Right Job and Next Step

## Purpose

Give the user one plain-language entry to the current Core-Prompts skill catalog.
Interpret the result they need, the material already available and the work still
missing. Recommend the needed depth instead of asking the user to understand skill
names, framework labels or the catalog's internal organization.

Apply the same intake method to every current catalog job, including analysis,
audits, incident support, communication triage, documents, presentations, skill
improvement and software delivery. Do not filter candidates to a fixed list or a
single domain. Honor a directly requested skill or established workflow; do not
make every unrelated task a Core-Prompts task.

## Primary Objective

Produce one supported recommendation: the first useful job, why it fits the actual
context, its expected output, required input or scope questions, and the next
conditional handoff. When the task is already authorized and the selected contract
is available, continue with that skill in the current assistant without a redundant
routing-approval turn. The recommendation itself grants no additional actions.

This skill owns intake and routing. Selected skills retain their artifact,
execution, review and acceptance responsibilities. Catalog inspection, a relationship
row or a plausible recommendation does not establish task completion or measured
routing effectiveness.

## Invocation Hints

- “Help me with this,” “I do not know where to start,” and “What should happen next?”
  use this skill when the current task or opted-in project asks for Core-Prompts help.
- “Help us understand the problem, investigate options and prepare a reviewed
  proposal for a team decision” can select the shaping conductor without the user
  saying “Shape Up.” Confirm only a material ambiguity the request leaves open.
- “Review this exact diff,” “make this bounded fix,” or a clear nonengineering
  request can select the relevant owner directly; do not impose a questionnaire.
- An explicit request for another skill is already a selection. Check its inputs
  and authority, report a material mismatch, and avoid a second router invocation.
- Use current skill names. Do not create aliases, new agent identities or provider
  invocation syntax. This skill does not install a global router.

## Required Inputs

Start with the user's sentence and any available conversation or artifacts. No
complete intake form, preselected workflow or repository is required.

Establish only what the task needs:

- Requested result, current context and known unresolved decisions.
- Supplied sources, actual artifacts and existing accepted work at their revisions.
- Scope, authority, constraints and effort limits already stated by the user or
  applicable project/host policies.
- A trusted Core-Prompts catalog root resolved by the host or user; optional explicit
  skill-package roots corresponding to this session.
- Current catalog observations and applicable relationship rows, with their binding
  status. Missing sources or native-discovery evidence remain explicit unknowns.

Read what is supplied before asking again. A reported acceptance, an artifact's
presence and verified acceptance are different facts. Do not guess appetite,
decision owners, completed work, provider access or a machine-specific root.

## Resource Delivery Contract

For a skill package, `<resource-root>` is its `resources` directory. Read
`resources/resource-map.json`, then the complete intake guidance at
`resources/references/intake-method.md` and the relevant relationship data in
`resources/routing-relations.json`. Load only the selected workflow dependencies;
do not load every skill body or run every resource loader.

The read-only standard-library inspector is
`resources/scripts/inspect_catalog.py`. Read its actual `--help` before use. Its
explicit root is `--root <trusted-core-root>`; repeat `--skills-root <actual-root>`
only for roots whose session relevance is established. Use `--skill <slug>` for
a focused skill and neighboring-relationship view; `--table` selects an explicitly
bound alternative table, not an arbitrary source found in model output. Invoke
it only when this read-only execution is permitted by the host and task. It makes no model calls,
network calls, installations, source edits or downstream dispatches.

If helper execution is unavailable or unauthorized, use bounded direct reads of
the same explicit catalog, relevant descriptors, relationship rows and selected
entry/resource files. State that fallback and its coverage; do not claim the helper
ran. If the required material cannot be read completely, hold conclusions that
depend on it and report the precise gap.

## Dynamic Catalog Contract

1. Inspect current `.meta/capabilities/*.json` under the explicit trusted root;
   do not hard-code the catalog's count, slugs or domains. Use current slug,
   summary, descriptor identity and reported source/entry paths for discovery.
   Resolve only paths established by the inventory or explicit root inputs.
2. Treat descriptor summaries as candidate-selection hints. UAC-layer input/output,
   tool-policy, overlap and relationship suggestions are not authoritative runtime
   contracts. Read the selected effective SKILL.md and required resources before
   relying on its behavior, inputs, output or permissions.
3. Keep catalog presence, package presence, effective package identity, host-native
   discovery and observed behavior separate. Without actual package-root evidence,
   report `catalog_only`; supplying a path alone does not prove host discovery.
   Inspection proves observed bytes and relationships only, not trusted origin,
   installation success or effective session loading. If no root is supplied, the
   inspector's `bundled_snapshot` is a fallback reference, not a current inventory.
   Identify that coverage gap and do not label it live or complete. Conflicting
   catalog/package identities remain explicit instead of selecting a convenient copy.
4. Include new or updated skills in candidate consideration even if no curated
   relationship row covers them. Read their current contract for a standalone
   recommendation. No edge does not mean no skill. Do not invent workflow links
   to make the catalog appear complete.
5. Recheck inventory and affected bindings after a catalog/package revision changes
   or before a dependent continuation when the previous observation may be stale.
   Do not overwrite historical observations or silently reuse a stale relationship.
6. Exclude this routing skill from its own downstream recommendations. A request
   for routing is already being handled here; do not recurse through another copy.
   If no available catalog skill fits, state the gap and retain the host's normal
   task handling rather than forcing the nearest Core skill.

## Workflow

1. **Use known context.** Read the task, conversation and supplied material. Identify
   the next desired result, accepted work, uncertainty and allowed scope. Do not
   turn every task into a survey or re-ask settled facts.
2. **Recommend one useful job and depth.** Explain the practical outcome first,
   then the exact skill and why it fits now. Choose the smallest depth that fulfills
   the user's request while preserving the selected skill's required evidence and
   reviews. Do not default to either a minimal answer or an elaborate full stack.
3. **Ask only a consequential missing question.** If two plausible routes or depths
   would materially change the output, effort, research or handoff and current
   context does not decide between them, explain the relevant options, recommend
   one with an honest rationale and ask one focused question. After the answer,
   update the recommendation and ask only the next still-material question.
4. **Keep every answer space open.** Every user question must provide an explicit
   free-text **Other — describe what you need** path. A documented native Other
   field satisfies this requirement; do not duplicate it. If a question tool cannot
   provide free text, use inline choices plus Other instead. Open-ended questions
   must also explicitly welcome another answer, correction or “not sure.” Never
   force the user to pick the least-wrong option.
5. **Use actual host support.** Prefer an available question tool when it supports
   the needed clarification under the host's contract. Otherwise use the same
   focused question inline, with plain-language A/B/C choices when useful and the
   free-text Other path. Do not invent a tool, assume its result, or use clarification
   tooling to bypass a permission or approval mechanism.
6. **Respect uncertain scope.** An unanswered or unknown response is not approval.
   Do not expand into deeper work whose scope remains materially unresolved. Explain
   what the recommended next artifact would establish; continue only shared work
   whose inputs and authority are already established. Human appetite, scope,
   acceptance and investment decisions remain with their actual owners.
7. **Read the selected contract and continue within authority.** Confirm the current
   package and load the complete selected entry/resources. Carry forward relevant
   evidence, decisions, unresolved items and the requested stopping point. Proceed
   with already authorized work without a new permission ceremony solely for
   routing; hold genuine prerequisites or approval gaps under their existing rules.
8. **Reassess on new evidence.** A response, finding, changed source or failed check
   can change the useful job or return work to an earlier owner. Explain the reason
   and preserve the current artifact/revision and its status; do not mark a planned
   transition as executed.

## Distinctions That Inform Intake

Use these as examples of semantic distinctions, not a fixed routing menu:

| Missing result | Likely owner and boundary |
| --- | --- |
| A clear problem, affected people and outcome before a solution | `engos-design-frame-from-vague`; a concise frame still retains its own evidence and acceptance requirements. |
| Defined behavior and acceptance for an identifiable change | `engos-design-specify-change`; a missing document alone is not missing acceptance. |
| A decision among actual supplied proposals or sources | `engos-reconciliation-converge`; request missing inputs rather than inventing alternatives. |
| Framing, research, shaping and a reviewed proposal for a team decision | `engos-design-shaping`; plain-language outcome can establish this depth, with its existing G0–G4 and human decisions retained. |
| A supported bounded change, unexplained failure, accepted task breakdown or actual review target | The current implementation, diagnosis, planning or review owner directly; skip redundant upstream intake. |
| A periodic multi-source brief, operational incident support, attention queue or presentation | The current report, incident, triage or content owner; do not impose an engineering workflow because the same router serves engineers. |

Use the current inventory to find other owners. Optional hardening, continuity,
goal-packet, orchestration and loop jobs remain separately wanted outcomes, not
mandatory add-ons. An explicit request can be plain language. A goal packet does
not start a goal; a crafted loop does not run or schedule it.

## Conditional Relationship Contract

`resources/routing-relations.json` is the curated conditional relationship table.
Each edge identifies `from`, `to`, `kind`, `when`, `handoff` and `stop`, with
`source_refs` tied to current descriptor SHA-256 values and relevant contract
clauses. Supported kinds are `sequence`, `iterate`, `return`, `parallel` and
`support`. Preserve each row's `evidence_class`: a reviewed route, source companion
contract and proposed composition do not have the same evidentiary status. A
proposed composition is a hypothesis requiring review and current-contract checks,
not an established source requirement. None is an execution graph or permission grant.

| Kind | Meaning | Required boundary |
| --- | --- | --- |
| `sequence` | An accepted output or resolved prerequisite can support the next owner's job. | Check the actual input, current acceptance evidence and authorized scope before recommending the handoff. Artifact existence is insufficient. |
| `iterate` | The same owner may revise its artifact after a concrete finding or answer. | Preserve the prior state, finding, revision and stop/budget conditions. A loop is not permission to retry indefinitely. |
| `return` | New evidence can send a specific unresolved issue back to an earlier owner. | Name the invalidated premise or missing evidence and the needed result. Do not silently rewrite accepted artifacts or claim the return happened. |
| `parallel` | Two jobs may be considered concurrently when neither consumes the other's unfinished output. | Verify actual dependencies, inputs, mutation sets, coordination needs, role independence, host support and authority. A suggestive graph or empty planning write list does not establish safe parallel execution. |
| `support` | A selected owner may need a specific companion's artifact, evidence or contract. | Read the owner's actual dependency rule and the companion's contract; this does not automatically turn the companion into a new user workflow or grant execution. |

Resolve edge endpoints against the current catalog. A missing endpoint, mismatched
binding or unresolved clause makes the edge stale or unknown. Do not use it as an
established relationship, exclude an otherwise valid updated skill, or fabricate
replacement edges. Descriptor equality is a drift check, not proof of the clause's
meaning; inspect selected current contracts before relying on an edge. A source
`contract_ref` may name SSOT that is absent from a distribution: resolve the same
slug to the effective package's complete SKILL.md/resources rather than requiring
source-maintainer files or guessing a sibling path.

Preserve direction. Conditional return/iteration cycles are not evidence that all
forward tasks depend on each other. For a proposed continuation, name its trigger,
needed input/output and stop condition; carry actual acceptance and authority holds
separately from graph readiness. Repeated no-progress transitions or contradictory
prerequisites require an explicit hold and the missing decision/evidence, not
another automatic pass through the same cycle.

Recommend parallel work only when the required facts are established, otherwise
state “parallel safety unassessed” and name the missing checks. This router does
not spawn workers or schedule execution. The host or explicitly selected execution
owner performs authorized dispatch while preserving required independent-review
roles. Do not add fake dependencies merely to conceal shared-write risk.

## Required Output

For a clear request, keep the user-facing response short:

- Recommended result and depth, exact selected skill, and a context-based reason.
- Expected next artifact and the relevant input or acceptance holds.
- Already authorized action to continue, or the one focused question with an Other
  free-text path when a material answer is missing.
- The next conditional handoff, if useful, with its trigger and stopping boundary.

For an ongoing workflow, add only the needed relationship rows: current owner,
relationship kind, next/return owner, required evidence and unresolved authority or
parallel-safety conditions. Carry source revisions, accepted decisions, requested
scope and review findings into the receiving skill. An inline explanation is
sufficient for a small request; use the project's existing tracker or artifact
format for durable work instead of mandating new sidecars.

Keep exact inventory paths/hashes, edge status and coverage in supporting evidence
when needed. Identify catalog-only, missing or stale evidence honestly. Do not turn
helper output, UI selections or an unexecuted handoff into a completion receipt.

## Rules

- Allowed: read authorized context and current catalog/package evidence, run the
  bounded read-only inspector when permitted, ask focused questions, recommend
  conditional relationships, and hand off within the current task's authority.
- Forbidden: invoke all catalog skills, treat task words as a complete classifier,
  invent inputs or approvals, infer permissions from route choice, launch goals or
  loops, spawn workers, install packages, change provider/home settings, write to
  external systems or publish merely because the routing artifact mentions them.

## Constraints

- The selected downstream skill and host/project rules govern any authorized
  implementation, tool use, independent review or external action. A required
  review remains required; unavailable support makes that dependent gate incomplete.
- Explicit user scope and applicable host, project and home policies remain in
  force. Dotfiles owns home-global policy. This capability adds a skill surface
  only; it neither creates an agent surface nor configures global autoloading.

## Examples

### Clear bounded work: no interview

Request: “Fix this reproduced off-by-one in the pagination helper; preserve sorting
and permissions. You may edit the helper and run its regression check.”

Response shape: recommend the current bounded implementation owner, explain the
patch/check output, read its selected contract and perform the authorized task.
Do not ask the user to choose a workflow depth or repeat the supplied constraints.

### Vague intent: a recommendation with open choices

Request: “Help me shape our onboarding idea,” with notes that describe complaints
but no desired decision artifact.

Response shape: “Your notes do not yet state the outcome to improve, so I recommend
clarifying the problem first. What result do you need next? A) a clear problem and
outcome, B) defined feature behavior and acceptance, C) researched options and a
reviewed proposal for a team decision, or Other — describe what you need, correct
my premise, or say you are unsure.” Adapt to the actual answer. If the user already
specified one of these outcomes, do not ask this question.

### A complete shaping request without a framework name

Request: “Work with us to clarify the problem, investigate alternatives and prepare
a reviewed pitch for the team to make an investment decision.”

Response shape: recommend the shaping conductor and begin authorized intake. Keep
its actual appetite, engineering/team acceptance, review and betting gates. Ask
only for still-missing material inputs, always with a free-text Other path; do not
require a “Shape Up” incantation or fabricate the human decision.

### Nonengineering jobs stay direct

Request: “Create six HTML slides from this source report for the leadership review.”

Response shape: select the current presentation owner from the live catalog, read
its contract and produce the authorized deliverable. Do not add specification,
architecture or implementation stages. A weekly multi-source status report instead
uses its report owner; active incident coordination and retrospective incident
analysis remain different jobs.

### Missing alternatives are not an invented comparison

Request: “Choose between these proposals,” but only one proposal is supplied.

Response shape: identify the comparison owner and ask for the missing proposal or
a corrected intended task, explicitly offering Other/free text. Do not synthesize
an imaginary opponent or infer a full research workshop from the missing file.

### Updated catalog, stale edge

Observation: a newly installed skill fits the requested artifact, but a previous
relationship row names an older descriptor hash.

Response shape: keep the skill in the candidate set, label the edge stale, read the
current entry/resources and make only the supported standalone recommendation.
Do not drop the skill, claim the old edge is current, or invent its next owner.

### Review return or possible parallel work

Observation: review identifies a missing requirement, while two other tasks appear
independent in a plan.

Response shape: recommend returning the specific requirement issue to its owner
with the finding and affected revision. Preserve the actual review hold. Describe
parallel execution only as a candidate until actual dependency, write-set,
coordination, role-independence and host-authority checks are established. Do not
start workers or manufacture dependencies to disguise uncertainty.

## Evaluation Rubric

| Check | Passing evidence |
| --- | --- |
| Catalog scope | Current inventory is inspected without a fixed count/domain filter; new skills remain selectable without curated edges. |
| Contract authority | Selected full entry/resources determine behavior; stale UAC-layer fields or advisory summaries do not override them. |
| Adaptive depth | Recommendation follows supplied outcomes/artifacts/uncertainty; clear requests avoid redundant intake. |
| Question quality | Only material unanswered questions are asked; every question offers Other/free text through an actual tool or inline fallback. |
| Human decisions | Unknown/silence is not approval; real scope, appetite, acceptance and investment decisions remain with their owners. |
| Relationship fidelity | Sequence, iterate, return, parallel and support relations are explicit and conditional; evidence class, stale/unknown bindings and current applicability remain distinct. |
| Execution boundary | Handoffs, graph readiness and recommendations grant no new permission, dispatch, goal, install or external write. |
| Parallel and cycle safety | Actual dependencies/write authority/role independence and stops are checked; uncertain parallelism and no-progress cycles stay held. |
| Output usefulness | One first job, rationale, expected artifact and conditional next step are clear without a catalog wall or mandatory new sidecar. |
| Evidence honesty | Source inspection and mechanical checks are distinguished from native discovery, actual task success and measured routing improvement. |


Capability resource: `resources/capability.json`
