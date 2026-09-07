# Capability Catalog

Generated from canonical manifest and descriptor metadata. Use this page to see what Core-Prompts ships, what each capability is for, and where it lands.

- Capability count: `27`

## Start Here
- `engos-quality-docs-review` — Docs Review Expert — Documentation IA, Drift, and Release Hygiene: Review repository documentation for information architecture, stale commands, broken links, misplaced content, drift, and release hygiene. Use when docs quality or discoverability is the primary concern; do not use for ordinary sentence editing.
- `engos-design-architecture` — Architecture Studio: Design APIs, data models, patterns, or systems with explicit boundaries, trade-offs, failure modes, migration, rollback, and validation. Use for concrete architecture decisions; do not use for prompt hardening or behavioral evaluation.
- `engos-quality-testing-review` — Testing Studio — Test Design and Coverage Analysis: Design or generate tests, edge cases, and coverage-gap analysis for a defined behavior without claiming tests were run. Use when test design is the primary deliverable; use GitOps review for release readiness.
- `engos-quality-gitops-review` — GitOps Review — Repo Hygiene, CI, Release, and Merge Gate: Assess repository hygiene, commit and pull request or merge request readiness, CI, packaging, merge, tag, and release prerequisites across GitHub and GitLab. Use for release or merge gates; do not claim hosted state without current verification.
- `engos-delivery-resolve-conflict` — Merge Conflict Resolution — Structured Conflict Analysis: Analyze and plan the safe resolution of Git or document conflicts while preserving valuable content, exposing contradictions, and defining verification. Use when an actual merge or content conflict exists; do not use for ordinary proposal disagreement without conflict markers.

## By CLI
- `claude`: `engos-audit-code-health`, `engos-audit-engineering-progress`, `engos-audit-feature-status`, `engos-audit-opex-incident-review`, `engos-audit-pitch-review`, `engos-audit-weekly-intel`, `engos-browser-demo-recorder`, `engos-content-dynamic-html-presentations`, `engos-delivery-address-code-review`, `engos-delivery-resolve-conflict`, `engos-design-architecture`, `engos-design-plan-to-goal`, `engos-memory-context-continuity`, `engos-memory-threader`, `engos-meta-instruction-editor`, `engos-meta-supercharge`, `engos-meta-uac-import`, `engos-operations-ic-assistant`, `engos-optimization-auto-research`, `engos-orchestration-batman`, `engos-quality-code-review`, `engos-quality-docs-review`, `engos-quality-gitops-review`, `engos-quality-testing-review`, `engos-reconciliation-converge`, `engos-triage-my-inbox-chat-pulse`, `loopy`
- `codex`: `engos-audit-code-health`, `engos-audit-engineering-progress`, `engos-audit-feature-status`, `engos-audit-opex-incident-review`, `engos-audit-pitch-review`, `engos-audit-weekly-intel`, `engos-browser-demo-recorder`, `engos-content-dynamic-html-presentations`, `engos-delivery-address-code-review`, `engos-delivery-resolve-conflict`, `engos-design-architecture`, `engos-design-plan-to-goal`, `engos-memory-context-continuity`, `engos-memory-threader`, `engos-meta-instruction-editor`, `engos-meta-supercharge`, `engos-meta-uac-import`, `engos-operations-ic-assistant`, `engos-optimization-auto-research`, `engos-orchestration-batman`, `engos-quality-code-review`, `engos-quality-docs-review`, `engos-quality-gitops-review`, `engos-quality-testing-review`, `engos-reconciliation-converge`, `engos-triage-my-inbox-chat-pulse`, `loopy`
- `gemini`: `engos-audit-code-health`, `engos-audit-engineering-progress`, `engos-audit-feature-status`, `engos-audit-opex-incident-review`, `engos-audit-pitch-review`, `engos-audit-weekly-intel`, `engos-browser-demo-recorder`, `engos-content-dynamic-html-presentations`, `engos-delivery-address-code-review`, `engos-delivery-resolve-conflict`, `engos-design-architecture`, `engos-design-plan-to-goal`, `engos-memory-context-continuity`, `engos-memory-threader`, `engos-meta-instruction-editor`, `engos-meta-supercharge`, `engos-meta-uac-import`, `engos-operations-ic-assistant`, `engos-optimization-auto-research`, `engos-orchestration-batman`, `engos-quality-code-review`, `engos-quality-docs-review`, `engos-quality-gitops-review`, `engos-quality-testing-review`, `engos-reconciliation-converge`, `engos-triage-my-inbox-chat-pulse`, `loopy`
- `grok`: `engos-audit-code-health`, `engos-audit-engineering-progress`, `engos-audit-feature-status`, `engos-audit-opex-incident-review`, `engos-audit-pitch-review`, `engos-audit-weekly-intel`, `engos-browser-demo-recorder`, `engos-content-dynamic-html-presentations`, `engos-delivery-address-code-review`, `engos-delivery-resolve-conflict`, `engos-design-architecture`, `engos-design-plan-to-goal`, `engos-memory-context-continuity`, `engos-memory-threader`, `engos-meta-instruction-editor`, `engos-meta-supercharge`, `engos-meta-uac-import`, `engos-operations-ic-assistant`, `engos-optimization-auto-research`, `engos-orchestration-batman`, `engos-quality-code-review`, `engos-quality-docs-review`, `engos-quality-gitops-review`, `engos-quality-testing-review`, `engos-reconciliation-converge`, `engos-triage-my-inbox-chat-pulse`, `loopy`
- `kiro`: `engos-audit-code-health`, `engos-audit-engineering-progress`, `engos-audit-feature-status`, `engos-audit-opex-incident-review`, `engos-audit-pitch-review`, `engos-audit-weekly-intel`, `engos-browser-demo-recorder`, `engos-content-dynamic-html-presentations`, `engos-delivery-address-code-review`, `engos-delivery-resolve-conflict`, `engos-design-architecture`, `engos-design-plan-to-goal`, `engos-memory-context-continuity`, `engos-memory-threader`, `engos-meta-instruction-editor`, `engos-meta-supercharge`, `engos-meta-uac-import`, `engos-operations-ic-assistant`, `engos-optimization-auto-research`, `engos-orchestration-batman`, `engos-quality-code-review`, `engos-quality-docs-review`, `engos-quality-gitops-review`, `engos-quality-testing-review`, `engos-reconciliation-converge`, `engos-triage-my-inbox-chat-pulse`, `loopy`

## By Use Case
- `address`: `engos-delivery-address-code-review`
- `analysis`: `engos-delivery-resolve-conflict`, `loopy`
- `architecture`: `engos-audit-pitch-review`, `engos-design-architecture`, `engos-quality-docs-review`
- `assistant`: `engos-operations-ic-assistant`
- `audit`: `engos-audit-code-health`, `engos-audit-engineering-progress`, `engos-audit-feature-status`, `engos-audit-opex-incident-review`, `engos-audit-pitch-review`, `engos-audit-weekly-intel`
- `auto`: `engos-optimization-auto-research`
- `batman`: `engos-orchestration-batman`
- `browser`: `engos-browser-demo-recorder`
- `chat`: `engos-triage-my-inbox-chat-pulse`
- `code`: `engos-audit-code-health`, `engos-delivery-address-code-review`, `engos-quality-code-review`
- `conflict`: `engos-delivery-resolve-conflict`
- `content`: `engos-content-dynamic-html-presentations`
- `context`: `engos-memory-context-continuity`, `engos-memory-threader`
- `continuity`: `engos-memory-context-continuity`
- `converge`: `engos-reconciliation-converge`
- `debugging`: `engos-design-architecture`
- `delivery`: `engos-delivery-address-code-review`, `engos-delivery-resolve-conflict`
- `demo`: `engos-browser-demo-recorder`
- `design`: `engos-design-architecture`, `engos-design-plan-to-goal`
- `docs`: `engos-quality-docs-review`
- `dynamic`: `engos-content-dynamic-html-presentations`
- `editor`: `engos-meta-instruction-editor`
- `engineering`: `engos-audit-engineering-progress`
- `engos`: `engos-audit-code-health`, `engos-audit-engineering-progress`, `engos-audit-feature-status`, `engos-audit-opex-incident-review`, `engos-audit-pitch-review`, `engos-audit-weekly-intel`, `engos-browser-demo-recorder`, `engos-content-dynamic-html-presentations`, `engos-delivery-address-code-review`, `engos-delivery-resolve-conflict`, `engos-design-architecture`, `engos-design-plan-to-goal`, `engos-memory-context-continuity`, `engos-memory-threader`, `engos-meta-instruction-editor`, `engos-meta-supercharge`, `engos-meta-uac-import`, `engos-operations-ic-assistant`, `engos-optimization-auto-research`, `engos-orchestration-batman`, `engos-quality-code-review`, `engos-quality-docs-review`, `engos-quality-gitops-review`, `engos-quality-testing-review`, `engos-reconciliation-converge`, `engos-triage-my-inbox-chat-pulse`
- `feature`: `engos-audit-feature-status`
- `gitops`: `engos-quality-gitops-review`
- `goal`: `engos-design-plan-to-goal`
- `health`: `engos-audit-code-health`
- `html`: `engos-content-dynamic-html-presentations`
- `import`: `engos-meta-uac-import`
- `inbox`: `engos-triage-my-inbox-chat-pulse`
- `incident`: `engos-audit-opex-incident-review`
- `instruction`: `engos-meta-instruction-editor`
- `intel`: `engos-audit-weekly-intel`
- `loopy`: `loopy`
- `memory`: `engos-memory-context-continuity`, `engos-memory-threader`
- `meta`: `engos-meta-instruction-editor`, `engos-meta-supercharge`, `engos-meta-uac-import`
- `operations`: `engos-operations-ic-assistant`
- `opex`: `engos-audit-opex-incident-review`
- `optimization`: `engos-optimization-auto-research`
- `orchestration`: `engos-orchestration-batman`
- `packaging`: `engos-reconciliation-converge`
- `pitch`: `engos-audit-pitch-review`
- `plan`: `engos-design-plan-to-goal`
- `planning`: `engos-browser-demo-recorder`, `engos-delivery-resolve-conflict`, `engos-design-plan-to-goal`, `engos-meta-supercharge`, `engos-meta-uac-import`
- `presentations`: `engos-content-dynamic-html-presentations`
- `progress`: `engos-audit-engineering-progress`
- `prompting`: `engos-design-architecture`, `engos-meta-supercharge`, `engos-meta-uac-import`
- `pulse`: `engos-triage-my-inbox-chat-pulse`
- `quality`: `engos-quality-code-review`, `engos-quality-docs-review`, `engos-quality-gitops-review`, `engos-quality-testing-review`
- `reconciliation`: `engos-reconciliation-converge`
- `recorder`: `engos-browser-demo-recorder`
- `research`: `engos-optimization-auto-research`
- `resolve`: `engos-delivery-resolve-conflict`
- `review`: `engos-audit-code-health`, `engos-audit-engineering-progress`, `engos-audit-feature-status`, `engos-audit-opex-incident-review`, `engos-audit-pitch-review`, `engos-audit-weekly-intel`, `engos-delivery-address-code-review`, `engos-meta-instruction-editor`, `engos-quality-code-review`, `engos-quality-docs-review`, `engos-quality-gitops-review`, `engos-quality-testing-review`, `loopy`
- `status`: `engos-audit-feature-status`
- `supercharge`: `engos-meta-supercharge`
- `testing`: `engos-quality-testing-review`
- `threader`: `engos-memory-threader`
- `triage`: `engos-triage-my-inbox-chat-pulse`
- `weekly`: `engos-audit-weekly-intel`

## All Capabilities
### Address Code Review — PR/MR Feedback Resolution
- Slug: `engos-delivery-address-code-review`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - address the review comments
  - fix the MR feedback
  - resolve PR comments
  - apply the requested changes from reviewers
  - address code review
  - address selected reviewer comments
  - implement requested changes from MR discussions
- Summary: Apply selected pull request or merge request feedback with tightly scoped edits, then prepare the fix for re-review. Use only when actionable reviewer comments already exist; use code review for pre-commit or pre-push judgment.

### Analyze Context — Durable Multi-File Investigation
- Slug: `engos-memory-context-continuity`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - analyze several files or transcripts over a long session
  - keep durable analysis notes that survive context loss
  - continue an investigation after its branch or worktree was removed
  - process a broad repo investigation one item at a time
  - recover and continue a previously interrupted analysis
  - preserve progress across a long research or audit workflow before a later recommendation step
- Summary: Maintain durable context, todo, and insight state for a multi-file or multi-source investigation that must survive compaction, session changes, branch changes, or worktree removal. Use when analysis must be resumed; do not use for a one-off report or final decision.

### Architecture Studio
- Slug: `engos-design-architecture`
- Type: `both`
- Install target: `global`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - design or review an API contract
  - propose a schema, indexing plan, or data model
  - choose between design patterns or refactor directions
  - design a system topology, reliability model, or scale strategy
  - produce a migration-safe architecture recommendation with rollback guidance
- Summary: Design APIs, data models, patterns, or systems with explicit boundaries, trade-offs, failure modes, migration, rollback, and validation. Use for concrete architecture decisions; do not use for prompt hardening or behavioral evaluation.

### Auto-Research — Goal-Driven Improvement Research, Evaluation, and Promotion
- Slug: `engos-optimization-auto-research`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Version: `v2.0`
- Invocation hints:
  - improve this prompt, workflow, tool, or system and prove it got better
  - search for a better version of this component
  - compare these prompt or capability variants behaviorally
  - prove this imported or revised capability is better than baseline
  - tell me whether this candidate is good enough to promote
  - run experiments against a goal and tell me what actually wins
  - turn our failures into future eval cases
  - optimize this system without regressing quality
  - guide me from setup to experiments to commit and merge
- Summary: Run bounded, baseline-controlled experiments to improve prompts, skills, workflows, tools, or code and decide whether a candidate is ready for promotion. Use when better behavior must be measured; do not use for unmeasured brainstorming.

### Batman — Evidence-Gated Delivery Controller
- Slug: `engos-orchestration-batman`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - Use `engos-orchestration-batman` for end-to-end implementation through subagent-driven development and blocking review gates.
  - Use Batman for a contract, metric, safety path, shipped defect, or other implementation that requires independent evidence and landing.
  - Do not invoke Batman for advice, a one-pass edit, or a review that excludes implementation.
- Summary: Run the explicitly requested, evidence-gated delivery protocol through independent subagents, TDD, blocking reviews, verification, documentation, Git health, and authorized landing. Use for implementation work that requires controller-owned sequencing and evidence.

### Codebase Health Audit — Brownfield Structural Risk Report
- Slug: `engos-audit-code-health`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - audit this codebase for structural health
  - find LOC hotspots, god objects, coupling, or likely dead code
  - verify whether prior codebase-health findings still hold
  - compare this repo against a previous audit snapshot
  - produce a read-only brownfield health report
  - identify slice-ready refactors from concrete structural metrics
  - detect structural drift since the last audit
  - inventory generated, backup, and temporary-file cruft without deleting it
- Summary: Perform a read-only structural audit of a brownfield codebase, measuring hotspots, coupling, god objects, dead-code candidates, prior findings, and drift. Use for repository health; do not use for feature completeness or diff review.

### Commit Review — Git Commit Quality Gate
- Slug: `engos-quality-code-review`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - review the latest commit
  - review my staged changes before I commit
  - review this diff before I push
  - check whether this diff is too broad
  - judge whether AI-generated changes are over-engineered
  - tell me if this commit message and change scope are strong enough to merge
- Summary: Review a staged change, diff, commit, or branch for correctness, scope, simplicity, lifecycle risk, and merge readiness before commit, push, merge, or release. Use for judgment; do not use to apply reviewer feedback.

### Converge — Multi-Source Synthesis, Conflict Surfacing, and Final Recommendation
- Slug: `engos-reconciliation-converge`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - compare these ideas and pick one
  - synthesize these documents into one proposal
  - converge on the best plan
  - tell me what to keep, what to reject, and why
  - surface the real conflicts before we decide
- Summary: Compare multiple sources, drafts, or proposals, surface conflicts and gaps, and produce one defensible recommendation with explicit trade-offs. Use when competing inputs must converge; do not hide incompatible ideas in a blended summary.

### Demo Recorder — Automated Playwright Demo Generation
- Slug: `engos-browser-demo-recorder`
- Type: `skill`
- Install target: `global`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - "Use `engos-browser-demo-recorder` to create a Playwright demo of the agent feedback feature on our Swagger UI."
  - "Use `engos-browser-demo-recorder` to generate a recorded walkthrough of the new dashboard."
  - "Use `engos-browser-demo-recorder` to script a demo that creates a resource, runs it, and shows the trace output."
- Summary: Plan and generate a complete Playwright browser walkthrough with authentication, realistic pacing, and video capture. Use when the goal is a shareable product demo; do not use for test coverage or CI.

### Docs Review Expert — Documentation IA, Drift, and Release Hygiene
- Slug: `engos-quality-docs-review`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - judge the repo documentation quality or organization
  - tell me what belongs in `README.md` versus `docs/`
  - check whether release docs, setup docs, or examples drifted
  - make docs cleaner, more linkable, or more readable
  - review a PR or release for documentation hygiene
- Summary: Review repository documentation for information architecture, stale commands, broken links, misplaced content, drift, and release hygiene. Use when docs quality or discoverability is the primary concern; do not use for ordinary sentence editing.

### Dynamic HTML Presentations
- Slug: `engos-content-dynamic-html-presentations`
- Type: `skill`
- Install target: `global`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Compatibility: HTML works in modern browsers; bundled PNG exporter requires macOS 13+; PPTX helper requires Python 3.9+.
- Summary: Create a self-contained HTML presentation and, when requested, validated PNG or image-only PPTX exports from a topic, outline, or source material. Use for visual narrative deliverables; do not use for browser demos or plain reports.

### Engineering Progress Report
- Slug: `engos-audit-engineering-progress`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - generate an engineering progress report from git history
  - summarize team velocity, code churn, release timeline, or architecture movement
  - build a local or Drive-hosted HTML report for one repo or a configured fleet
  - refresh author-scoped report configuration from an organization directory
  - sync previously generated reports from Drive to the local report folder
- Summary: Generate a Git-derived engineering progress dashboard for one repository or a configured fleet, including activity, churn, authors, and releases. Use for periodic engineering activity audits; do not use for Jira story points, feature completeness, code review, or code-quality approval.

### EngOS Audit — Operational Excellence Incident Review
- Slug: `engos-audit-opex-incident-review`
- Type: `skill`
- Install target: `global`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Version: `3.0.0`
- Author: `Amol Shah; uplifted for Core-Prompts`
- Summary: Generate an evidence-backed Daily OpEx Digest and optional incident drill-downs from current Jira incidents, prior snapshots, DPAs, and postmortems. Use for decisions, owner accountability, daily progress, stalled work, estate patterns, SLA tracking, Five Whys, and executive meeting preparation.

### Feature Status — Deep Completeness Analysis
- Slug: `engos-audit-feature-status`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - how complete is this feature
  - what is left to ship
  - compare scope vs implementation
  - find gaps in this feature
  - feature readiness check
  - what is blocking this feature from shipping
  - audit this feature against the spec
  - what's the gap between spec and code
  - pre-ship readiness check for this feature
- Summary: Audit a feature’s stated scope against code, tests, configuration, specifications, tickets, and Git history, then report completion states, drift, gaps, and shipping priorities. Use for feature readiness; do not use for repository-wide health or Git-only activity reports.

### GitOps Review — Repo Hygiene, CI, Release, and Merge Gate
- Slug: `engos-quality-gitops-review`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - judge the repo organization or GitOps hygiene
  - make sure my commits are logically scoped and messages are strong
  - check whether my PR is ready to merge
  - confirm CI is green on GitHub and GitLab
  - merge, push, package, tag, release, or clean up branches
  - update changelog or release notes as part of a release gate
- Summary: Assess repository hygiene, commit and pull request or merge request readiness, CI, packaging, merge, tag, and release prerequisites across GitHub and GitLab. Use for release or merge gates; do not claim hosted state without current verification.

### Incident Commander Assistant
- Slug: `engos-operations-ic-assistant`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - track an active incident and prompt for next steps
  - validate incident artifacts and process compliance
  - guide through Incident Commander tier escalation
  - generate handoff briefings for IC transfer
  - determine if executive communication is required
  - remind about overdue status updates or postmortem deadlines
  - use the internal incident runbook for this Appian incident
  - switch to generic incident commander guidance
- Summary: Guide an Incident Commander through phase tracking, status cadence, artifact checks, escalation prompts, handoff, resolution, and postmortem work without making incident decisions. Use during an active incident or postmortem.

### Instruction Editor
- Slug: `engos-meta-instruction-editor`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - remove AI-ish, Claude-ish, ChatGPT-ish, corporate, or exhausting phrasing
  - apply Google developer documentation style to a prompt or skill
  - tighten or shorten instructions without changing behavior
  - clarify actors, conditions, commands, or outputs
  - audit an instruction artifact for readability or translation risk
  - compare an edited instruction against its original contract
- Summary: Audit, rewrite, diff, or verify prompts, skills, and agent instructions for clarity while preserving commands, authority, safety boundaries, and behavior. Use when instruction preservation is the central task; do not use for general prose editing.

### Loopy — Bounded Agent Loops
- Slug: `loopy`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Summary: Discover, find, compare, audit, repair, adapt, craft, run, debrief, and prepare repeatable AI-agent loops for publication. Use when a user asks to analyze code or coding threads for recurring work, find a published loop, interview them to turn a goal into a bounded loop, review a loop for weak checks or unsafe authority, execute a loop with an evidence receipt, learn from completed runs, or validate and submit a loop to Loop Library.

### Merge Conflict Resolution — Structured Conflict Analysis
- Slug: `engos-delivery-resolve-conflict`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - help me resolve this merge conflict
  - compare these conflicting branch edits and tell me what survives
  - preview how to merge this branch safely
  - tell me what content is orthogonal versus contradictory
- Summary: Analyze and plan the safe resolution of Git or document conflicts while preserving valuable content, exposing contradictions, and defining verification. Use when an actual merge or content conflict exists; do not use for ordinary proposal disagreement without conflict markers.

### Pitch — Shape Up Pitch Creation, Review, Scoring, and Improvement
- Slug: `engos-audit-pitch-review`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Version: `v1.1`
- Invocation hints:
  - create a pitch / write a pitch / scaffold a pitch
  - review this pitch / critique this pitch
  - score this pitch / rate this pitch
  - improve this pitch / make this pitch better / harden this pitch
  - compare these pitches
  - which pitches need work / pitch audit / pitch status
  - is this pitch ready to bet on
  - bootstrap a pitch from this goal
  - what does good integration proof look like / how do I prove integration / what spike do I need
- Summary: Create, review, score, improve, or export Shape Up pitches by checking problem framing, appetite, architecture, dependencies, integration proof, risks, and betting readiness. Use for pitch artifacts; do not use for feature status or general proposal synthesis.

### Plan to Goal Design
- Slug: `engos-design-plan-to-goal`
- Type: `skill`
- Install target: `global`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - turn this approved plan into a goal
  - prepare a copyable Goal-mode objective and iteration setting
  - convert this implementation brief into a durable goal packet
  - make this long-running goal research the repository before it edits
  - create a goal, spec, and verifier without assuming every CLI has `/goal`
- Summary: Compile a reviewed plan or intent into a host-aware goal, durable specification, and task-specific verifier with explicit trust, drift, stop, and rollback conditions. Use when a bounded long-running goal packet is needed; do not use for ordinary one-step implementation.

### Pulse — Comms Triage
- Slug: `engos-triage-my-inbox-chat-pulse`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - check my email / inbox / messages
  - what needs my attention
  - any urgent messages
  - triage my comms / communications
  - what's new in chat
  - pulse, engos-triage-my-inbox-chat-pulse /hot, engos-triage-my-inbox-chat-pulse /email, engos-triage-my-inbox-chat-pulse /chat
- Summary: Triage Gmail and Google Chat into a deterministic attention queue with priority, links, and approved follow-up actions. Use when deciding what communications need attention; triage is read-only and actions require explicit approval.

### SuperCharge — Prompt Engineering, Planning Hardening, and Graded Improvement
- Slug: `engos-meta-supercharge`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Version: `v4.2`
- Invocation hints:
  - make this prompt better
  - harden this plan
  - compare these options and converge on one recommendation
  - compare these prompt variants, then tell me whether behavioral proof is needed
  - critique this proposal from several angles
  - run adversarial debate, Bull/Bear/Decider analysis, or `/debate /deep`
  - grade this output and iterate it upward
  - design an agentic workflow or prompt stack
- Summary: Harden a prompt, plan, proposal, or workflow through the smallest useful sequence of simplification, inversion, adversarial critique, contract checks, debate, or grading. Use when the artifact needs stronger reasoning or execution guidance; use behavioral evaluation for proof.

### Testing Studio — Test Design and Coverage Analysis
- Slug: `engos-quality-testing-review`
- Type: `skill`
- Install target: `global`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - generate unit tests
  - design end-to-end tests
  - find edge cases we are missing
  - show me coverage gaps
  - tell me what to test first for this change
- Summary: Design or generate tests, edge cases, and coverage-gap analysis for a defined behavior without claiming tests were run. Use when test design is the primary deliverable; use GitOps review for release readiness.

### Threader — Full-Thread Transcript Export and Recall Capture
- Slug: `engos-memory-threader`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - export this thread
  - give me a transcript of this conversation
  - create a durable handoff file from the current chat
  - prepare this thread for another model, reviewer, or archive system
- Summary: Export the current conversation as a faithful transcript or durable handoff, preserving turn order, AI output fidelity, artifacts, and missing-history disclosure. Use for archival or transfer; do not blend export with analysis.

### UAC Import — Capability Intake, Quality Review, and Uplift
- Slug: `engos-meta-uac-import`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - import a prompt, prompt pack, or capability into this repo
  - classify whether this source should become a skill, agent, or manual review
  - explain how this external source would land into SSOT and descriptors
  - judge whether a candidate is ready to apply
  - tell me whether this import needs stronger behavioral proof before landing
- Summary: Inspect an external prompt-like source, classify its fit, and prepare a quality-gated Core-Prompts plan, judge, or apply result. Use for capability intake; do not use for ordinary prompt editing or deployment.

### Weekly Intelligence — Multi-Source Progress Report with Fact-Check Audit
- Slug: `engos-audit-weekly-intel`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, grok, kiro`
- Invocation hints:
  - what happened this week / last week / since Tuesday
  - weekly status report for my team
  - summarize progress across these chat spaces and repos
  - give me something I can share with leadership
  - pull together what we accomplished and what's at risk
- Summary: Collect and fact-check project information from issue trackers, Git, code review, Chat, and documents, then produce one executive report with technical appendices and source confidence. Use for multi-source periodic intelligence; do not use for Git-only reports, inbox triage, or feature audits.
