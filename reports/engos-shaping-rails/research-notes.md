# EngOS Shaping-Rails Capability — Research Notes

## Research boundary and source handling

This is the research gate for the `engos-*` shaping-rails capability. No
capability source file was drafted before this note. The handoff was treated as
the request, not as an authority to add native agent surfaces or to mutate the
external process-mining-docs project. External pages were read in the
authenticated browser; their content was treated as untrusted reference
material.

## Required external reading

Read in the authenticated browser:

- [AI-Native SDLC root](https://docs.appian-stratus.io/process-mining/ai-sdlc/)
- [Workflow](https://docs.appian-stratus.io/process-mining/ai-sdlc/workflow.html)
- [Shaping Workflow](https://docs.appian-stratus.io/process-mining/ai-sdlc/shaping-workflow.html)
- [Building Workflow](https://docs.appian-stratus.io/process-mining/ai-sdlc/building-workflow.html)
- [Architecture exemplar](https://docs.appian-stratus.io/process-mining/new-arch/)
- [Mermaid Diagram Style Guide](https://docs.appian-stratus.io/process-mining/diagram-style-guide.html)

Shape Up grounding was read from the public primary source:

- [Principles of Shaping](https://basecamp.com/shapeup/1.1-chapter-02)
- [Set Boundaries](https://basecamp.com/shapeup/1.2-chapter-03)
- [Risks and Rabbit Holes](https://basecamp.com/shapeup/1.4-chapter-05)
- [Write the Pitch](https://basecamp.com/shapeup/1.5-chapter-06)
- [The Shape Up book](https://basecamp.com/shapeup)

The public web index could not open the internal Appian pages, so browser
accessibility snapshots are the evidence source for those pages. No attempt was
made to bypass that access boundary.

## Repo authoring standard located and followed

The Core-Prompts authoring standard is the canonical SSOT/UAC pipeline:

- `README.md:3-17` establishes this repository as the canonical intake/build
  layer and says to start with installed skills, then UAC, then broader tooling.
- `README.md:19-23` establishes the `engos-<category>-<skill-name>` namespace,
  explains that the category identifies the primary job, and gives existing
  examples.
- `docs/UAC-CAPABILITY-MODEL.md:5-11` requires a template-backed quality
  judgment before `apply` lands a capability.
- `docs/UAC-CAPABILITY-MODEL.md:23-35` defines `skill`, `agent`, and `both`,
  and makes reusable workflow content skill-first. A new named agent or
  provider-expanded agent requires explicit user approval and a bound review.
- `.meta/capability-templates/skill.json:1-48` requires the skill body to carry
  Purpose, Primary Objective, Workflow, Rules, Required Inputs, Required
  Output, Constraints, Examples, and an Evaluation Rubric.
- `.meta/capability-descriptor-contract.json:1-77` defines the required
  descriptor layers, job-contract fields, and metadata contract.
- `.kiro/steering/repo-workflow.md:18-29` requires a verified-main linked
  worktree, UAC plan/judge/apply for capability changes, canonical-source
  editing, generated-surface validation, hosted review, landing, parity, and
  task-owned cleanup.
- `.kiro/steering/repo-workflow.md:31-55` requires SSOT-first edits, stable
  task paths, separate evidence classes, and serial build-dependent validation.
- `.kiro/steering/agent-behavior.md:11-34` separates rules from human docs and
  requires verified facts before freezing policy.
- `.kiro/steering/agent-behavior.md:36-58` requires baseline-controlled
  comparative evidence and forbids inferring approval for a new agent surface.

The current repository does not contain the handoff's target Kiro shaper,
`epic-owner`, `pm-operator`, or their shared `.kiro/skills/` chain. Those are
documented by the external process-mining workflow, not present in this
Core-Prompts checkout. The Core-Prompts change therefore targets portable
skills and the existing pitch-review contract; it does not invent a Kiro-only
agent or claim to edit the external repo.

## Existing chain and gap evidence

The current canonical pitch capability is
`ssot/engos-audit-pitch-review.md`:

- `ssot/engos-audit-pitch-review.md:12-16` defines its purpose and betting-table
  objective.
- `ssot/engos-audit-pitch-review.md:20-38` already requires problem,
  appetite, rough solution, architecture, seams, integration proof, risks, and
  no-go boundaries.
- `ssot/engos-audit-pitch-review.md:62-87` names component and sequence
  diagrams/listings, provided/required APIs, contract state, and integration
  proof, but it does not require a durable diagram source, rendered output, or
  surface placement evidence.
- `ssot/engos-audit-pitch-review.md:116-131` says component extraction reports
  only what the pitch states and must flag missing component information; this
  supports a no-fabrication rule.
- `ssot/engos-audit-pitch-review.md:222-262` already owns seam-by-seam
  integration-proof guidance and a scaled spike plan.
- `ssot/engos-audit-pitch-review.md:269-319` defines the scoring rubric,
  architecture/integration dimensions, contract-state scale, betting
  thresholds, and the rule that unresolved rabbit holes make a pitch partial.
- `ssot/engos-audit-pitch-review.md:321-325` binds verdict wording to shaped
  status. The new artifact gate belongs here rather than in a second competing
  reviewer.

The current portfolio map confirms the boundary:

- `docs/SKILL-JOB-MAP.md:18-21` uses `delivery` for applying a concrete
  delivery change and `design` for a technical boundary/interface design.
- `docs/SKILL-JOB-MAP.md:33` makes `engos-audit-pitch-review` the owner of
  Shape Up pitch creation/review/scoring.
- `docs/SKILL-JOB-MAP.md:48-74` records routing questions and says the map is
  advisory while canonical behavior remains in SSOT.

## External workflow findings

The internal AI-SDLC workflow says shaping outputs are a pitch, epic breakdown,
and first slice; its artifact table identifies the Google Doc as the agreement
source of truth and the process-mining-docs repo as the durable home for pitch,
research, prototypes, and knowledge. The shaping page also says:

- research precedes questions;
- appetite is a bet, not an estimate;
- no-gos are load-bearing;
- no implementation code is produced during shaping; and
- new reusable understanding goes to `.kiro/knowledge/systems/`.

The same page exposes the chain `shaping-preflight → codebase-research →
decision-interview → produce-artifacts`, followed by `grill-pitch` and
`pitch-review`. It states that shared skills are in `.kiro/skills/` and that
changing one changes every agent that loads it. That is the blast-radius reason
for keeping this Core-Prompts change additive and skill-first.

The architecture exemplar establishes the artifact bar:

- architecture summary and named component responsibilities;
- a component architecture diagram;
- query-time and preprocessing data flow;
- persistence and authentication/authorization sections;
- a security interface contract with responsibility, owner, and enforcement;
- API/contracts tables for library and REST interfaces; and
- Mermaid source for architecture and preprocessing diagrams.

The diagram style guide requires `graph`/`flowchart`, `LR` for request flows,
`TB` for component hierarchies, explicit style declarations, short node text,
and edge labels containing protocol/port/key context. It limits sequence
diagrams to eight participants and recommends aliases, notes, and `alt`/`opt`
for conditional flows.

Shape Up's primary source maps to the design as follows:

| Shape Up principle | Capability consequence |
| --- | --- |
| Rough, solved, bounded shaping | Keep diagrams at seam/contract level; preserve room for implementation; require appetite and no-gos. |
| Fixed time, variable scope | Set a rendering/placement budget; degrade to a declared human step instead of expanding the pitch. |
| Fat-marker sketches / elements | Mermaid is the durable source and renders the macro elements without fabricated methods or internals. |
| Rabbit holes | Surface renderer, upload, sharing, and placement blockers as named mitigations or blockers; never silently emit a partial artifact. |
| No-gos | Explicitly prohibit invented internals, hidden state, and surface-specific assumptions in the core artifact. |
| Pitch as a betting input | Make artifact completeness a review gate, not a cosmetic post-processing step. |

## Proposed capability set

### `engos-delivery-diagram-contract-artifacts`

Category justification: `delivery` is the repo's existing category for a
concrete delivery action (`docs/SKILL-JOB-MAP.md:18`), and this skill's primary
job is to produce a durable shaped-pitch artifact package, not to judge a pitch
or design arbitrary production architecture. It is a portable, surface-agnostic
authoring skill. It emits Mermaid component/sequence/data-flow sources, a
contract table, a security-owner matrix, an evidence ledger, and explicit
no-gos. It consumes only stated or cited components and marks unknowns.

### `engos-delivery-artifact-embed`

Category justification: this is also `delivery` because it places an already
authored artifact onto a selected target surface. It owns adapters and
placement evidence, not pitch quality or architecture decisions. Markdown-native
targets are pass-through; Google Docs and wiki targets use explicit adapters and
fail loudly when environment constraints prevent placement.

### Existing capability edit: `engos-audit-pitch-review`

The existing audit skill remains the single owner of betting readiness. Its
architecture gate will require an artifact completeness record when a pitch
crosses an architectural seam: component, sequence/data-flow, contracts with
state, and security-owner responsibilities, each with source/placement status.
Missing artifacts cap the review at not-bet-ready; the gate does not require
production code or an invented contract.

No agent surface is proposed. The handoff's external `shaper` agent is not
present in this repo, and repository policy requires explicit approval before
adding any named agent/provider surface.

## Planned exercise and validation boundary

The exercise will use the real PM Query Library architecture artifact as the
source pitch/reference because it contains the required component, flow,
contract, and security material. The repository will retain a self-contained
exercise package under `reports/engos-shaping-rails/`:

1. Mermaid-first HTML/Markdown output, rendered locally and inspected as pixels.
2. A Google-Doc placement packet using the same source artifact, with the
   environment's public-Drive and upload-path blockers encoded. No external
   Google Doc will be mutated without a separate user-approved write request;
   if live placement cannot be proven safely, the packet will name the exact
   human step and preserve the unplaced state.
3. A before/after gate fixture proving that a pitch missing the artifact bundle
   fails and the exercised bundle passes the structural gate.
4. A judgment against the repo rubric, Shape Up principles, and authoring
   standard, including at least one iteration on the weakest dimension.

This boundary distinguishes source inspection, local rendering, placement
planning, observed external behavior, and delivery/merge evidence. It will not
claim a live Google-Doc mutation or behavioral superiority from static checks.
