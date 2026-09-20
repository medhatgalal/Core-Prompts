# engos-design-shaping research notes

## Research summary

The missing capability is gated progression from vague input through Framed,
Research, Shaped and Bet-ready. Existing artifact helpers cover only part of
Shaped. Upstream supplies valuable research, audit, slice and review contracts,
but its conductor has no separate solution-free Framed artifact. This report
precedes every draft in this design packet. Status: research completed for
workflow design; exercise code research and gate execution are still pending.

## Sources and authoring authority

Core-Prompts baseline: `ccf62d9188697fc4323c310ce37140a96f92cddc`.
Upstream docs/process-mining: `8a202bba974b8c66aa060128aa916eb4a7f2b2c5`.
Upstream appian/prod/pm-dev-tools: `3048d0fadd4438c81300d3d5b46c0b5b93b97d62`.
Paths prefixed `upstream/` below identify that pinned pm-dev-tools source.
Sources were read as reference data, not operating instructions.

Required pages were browsed in the requested order on 2026-09-17:

1. [Workflow](https://docs.appian-stratus.io/process-mining/ai-sdlc/workflow.html)
2. [Shaping](https://docs.appian-stratus.io/process-mining/ai-sdlc/shaping-workflow.html)
3. [Building](https://docs.appian-stratus.io/process-mining/ai-sdlc/building-workflow.html)
4. [AI-SDLC](https://docs.appian-stratus.io/process-mining/ai-sdlc/)
5. [Exemplar](https://docs.appian-stratus.io/process-mining/new-arch/)
6. [Diagram conventions](https://docs.appian-stratus.io/process-mining/diagram-style-guide.html)

The docs repo README:7-11 redirects authoring to pm-dev-tools. The older site
still refers to `.kiro/agents` and starting in process-mining-docs. The current
source README and plugin layout win when resolving files.

| Authoring fact | Checked source |
| --- | --- |
| Names encode the primary job as engos-category-name | Core-Prompts README.md:19-21 |
| Canonical source and generated outputs are distinct | Core-Prompts AGENTS.md, Source-of-truth policy; .kiro/steering/repo-workflow.md:20-25 |
| Draft-only work is a supported scope | .kiro/steering/repo-workflow.md:18 |
| UAC judges templates before canonical apply | docs/UAC-CAPABILITY-MODEL.md:5-11 |
| Skill body has purpose, objective, workflow, boundaries, inputs, outputs, examples and rubric | .meta/capability-templates/skill.json:1-28 |
| Added native agents need identity/provider approval and an independent execution-need assessment | docs/UAC-CAPABILITY-MODEL.md:31-35; .kiro/steering/agent-behavior.md:52-58 |
| Upstream plugins own installed agents and skills | upstream/README.md:3-5,40-68; upstream/kiro-plugins/README.md:29-46 |
| Upstream native agent uses a prompt file and explicit resource references | upstream/kiro-plugins/README.md:57-68; upstream/kiro-plugins/pm-work/agents/shaper.json |
| Step completion must be observable; disclose branch-specific references | upstream/kiro-plugins/starter-pack/skills/writing-for-agents/SKILL.md:31-61 |
| Upstream instruction-edit method locates the responsible source and changes it narrowly | upstream/.kiro/agents/improve-agents.md:9-22,35-62 |
| Run artifacts belong under reports rather than metadata | Core-Prompts AGENTS.md, Source-of-truth policy |

Conventions reconciled: retain conventional `SKILL.md`, `resource-map.json`,
`research-notes.md` and stage artifact filenames inside engos-named packages.
The namespace applies to capability/deliverable identities, not a renamed
`SKILL.md` that discovery cannot find. Core-Prompts' generated provider formats
remain authoritative; upstream's Kiro-specific unquoted-frontmatter and symlink
installation recipes are not copied into portable distribution rules.

## Current chain mapped to requested gates

Abbreviation P = upstream/kiro-plugins/pm-work.

| Requested stage | Existing source and behavior | Missing contract |
| --- | --- | --- |
| 0 Intake | P/agents/shaper.md:58-70 extracts problem, direction, repos and appetite; P/skills/shaping-preflight/SKILL.md:14-156 resolves paths/sources and knowledge | Explicit known/assumed/missing classification; preserve proposed mechanism as unendorsed input |
| 1 Framed | P/skills/shaping-decisions/SKILL.md:50-126 captures human decisions, but P/agents/shaper.md:82-109 drafts before clarification | Standalone solution-free frame, walk-away threshold, question IDs and pass receipt before design |
| 2 Research | P/skills/codebase-research/SKILL.md:45-69,80-149 distinguishes intent from feasibility and carries verified/assumed/undetermined claims | Each frame question needs a disposition; named spike must not masquerade as an answer |
| 3 Shaped | P/skills/pitch-artifacts/SKILL.md:11-145,186-239 supplies pitch/epics/contracts/traceability/report; P/skills/vertical-slicing/SKILL.md:11-98 defines proof slices | Complete component, sequence, data-flow, interface and security-owner coverage; rendered inspection and explicit negative responsibilities |
| 3 Audit | P/skills/pitch-audit/SKILL.md:16-79 verifies evidence, operations, scope and seven scores; :81-117 handles backward reconciliation | Bind verdict to actual artifact revision; missing visuals and unanswered questions must block despite average score |
| 4 Bet-ready | P/skills/pitch-review/SKILL.md:38-136 adds independent review and five pitch scores; :138-201 makes betting prep; P/agents/shaper.md:125-169 gives human review verbs | Verify placement and full content parity on chosen surfaces; distinguish review readiness from a human bet |
| Throughout | P/skills/knowledge-persistence/SKILL.md:11-47,128-171 separates system facts, task decisions and outputs | Select an explicit knowledge root, with freshness and revision evidence, independently of host/provider cwd |

`grill-pitch` in the older site is now `pitch-audit`. `decision-interview` has
become shaping-decisions plus starter-pack grilling. The source shaper's
artifact, research and audit skills are also used by epic-owner and review;
their responsibilities must survive any adaptation.

Core-Prompts' current pitch capability permits component lists and sequence
listings (ssot/engos-audit-pitch-review.md:69-75), while its appended gate demands
diagrams (:289-321). It has no five-stage conductor. Its historical four-week
product context (:103-108) cannot dictate a new pitch's appetite.

## Exemplar as an observable contract

The exemplar demonstrates: component responsibilities and boundaries; request
and preprocessing flow; in-process versus network interface distinction;
Method/Purpose and Method/Endpoint/Purpose tables; Responsibility/Owner/How
enforced security rows; explicit statements about responsibilities the library
does not own; data persistence and known gaps. It is a presentation/coverage
reference, not evidence that a proposed interface currently exists.

The stage-3 rubric will check those elements against the candidate's evidence.
It will require component, sequence AND data-flow diagrams as the user specified,
even though the exemplar uses a mixture of diagrams and narrative flows.

## Shape Up grounding and adaptation decisions

| Principle and primary source | Design decision |
| --- | --- |
| [Set boundaries](https://basecamp.com/shapeup/1.2-chapter-03) | Stage 1 fixes problem, appetite and limits before exploring solutions. Missing appetite is a human decision, not an inferred estimate. |
| [Rough, solved, bounded](https://basecamp.com/shapeup/1.1-chapter-02) | Stage 3 specifies macro flows and contracts, while leaving implementation details open. |
| [Risks and rabbit holes](https://basecamp.com/shapeup/1.4-chapter-05) | Trace each risk to evidence; mitigate, cut or block. A spike plan is not a completed spike. |
| [Betting table](https://basecamp.com/shapeup/2.2-chapter-08) | Stage 4 prepares a decision. Only the human makes the bet; no team allocation or ticket creation follows automatically. |
| [Map scopes](https://basecamp.com/shapeup/3.3-chapter-12) | Propose coarse workstreams and visible slices, while allowing scopes to be discovered during building. |
| [Show progress](https://basecamp.com/shapeup/3.4-chapter-13) | Track uncertainty explicitly. Completed documents or average scores do not establish downhill/implementation progress. |

The requested five-stage split is this capability's adaptation of Shape Up,
not a claim that the book prescribes these exact five gates. Potential tension:
stage 2 allows named spikes but stage 3 rejects unresolved questions. Resolution:
stage 2 may yield `needs_spike`, but advances only after a spike result or an
explicit, authorized scope exclusion removes the blocking dependency.

## Planned identities, composition and blast radius

| Identity | Why category | Trigger and responsibility |
| --- | --- | --- |
| engos-design-shaping | Design defines a bounded solution before building; matches engos-design-architecture boundary | Rough idea to complete five-stage process; conductor skill plus agent role design |
| engos-design-frame-from-vague | Framing is a design activity | Intake and solution-free Framed outputs |
| engos-quality-shaping-gate | Quality determines whether an artifact may advance | One reusable gate contract, called by conductor and existing pitch reviewer |
| engos-delivery-diagram-contract-artifacts | Delivery produces artifacts from evidence | Retain identity; adapt draft for full stage-3 coverage and no fabricated implementation |
| engos-delivery-artifact-embed | Delivery places authored output | Retain identity; adapt draft with actual target capability checks, full-table parity, style and tested private import |
| engos-audit-pitch-review | Existing owner of pitch judgment | Draft integration into the gate; independent review remains distinct from author audit |

Proposed shared resources: gate contract, stage templates, rubric, style recipe,
surface capability note. Each has one owner. No new production native agent or
provider registration is emitted in this design exercise. A conductor can run
in the invoking session or an independent host worker; a native adapter proposal
must justify any extra execution requirements before later admission.

## Exercise provenance and privacy

Use the real original Continuous Update brief under upstream/.kiro/knowledge/
shaping/continuous-update/brief.md. Human clarifications are input constraints;
the old shaped pitch is held as historical context rather than a generated
candidate. The historical pitch gives five weeks/two engineers; the user was
asked to confirm that exercise appetite and walk-away condition.

pm-core source was retrieved at 96745e9242ef716085358cd9903fe672a84970c2.
The local AE checkout is older than current upstream and must be labeled as
such; read current files before current-feasibility claims. Private code,
full exercise artifacts and reviewer excerpts stay outside this public repo.
HTML is local; the new Google Doc belongs to the verified work account.

## Evidence limits and pending steps

At completion of the research phase, no stage had yet been judged or advanced.
Subsequent observed gates and remaining work are recorded in validation-report.md;
this research note remains the pre-draft source map. No confidence score or
success is inferred from the earlier run. The earlier static fixture
files are not tests, and its claimed failed first iteration is not used as proof.
Research the current interfaces, draft the complete candidate set, independently
review semantics, run gates in order, inject failure cases, place and inspect
both surfaces, record an actual weakest-dimension iteration, and judge results.
