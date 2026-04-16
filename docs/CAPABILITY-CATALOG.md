# Capability Catalog

Generated from canonical manifest and descriptor metadata. Use this page to see what Core-Prompts ships, what each capability is for, and where it lands.

- Capability count: `15`

## Start Here
- `docs-review-expert` — Docs Review Expert — Documentation IA, Drift, and Release Hygiene: Documentation Review Expert for information architecture, explainable technical writing, repo doc layout, drift detection, and documentation quality gates across commits, pull requests, merges, and releases.
- `gitops-review` — GitOps Review — Repo Hygiene, CI, Release, and Merge Gate: GitOps Review for repo hygiene, commit quality, PR readiness, CI state, packaging, changelog, merge, tag, push, and release gates across GitHub and GitLab.
- `architecture` — Architecture Studio: Designs APIs, schemas, patterns, and system topology with explicit boundaries and trade-offs. Use for concrete architecture decisions, interface design, or rollback-aware system plans.
- `uac-import` — UAC Import — Capability Intake, Quality Review, and Uplift: Inspects external prompt-like sources and maps them into Core-Prompts plan, judge, and apply flows. Use when importing, planning, judging, or applying a new or updated capability.
- `testing` — Testing Studio — Test Design and Coverage Analysis: Testing Studio for unit-test generation, end-to-end test design, edge-case discovery, and coverage gap analysis.

## By CLI
- `claude`: `analyze-context`, `architecture`, `autosearch`, `code-review`, `converge`, `docs-review-expert`, `feature-status`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`, `weekly-intel`
- `codex`: `analyze-context`, `architecture`, `autosearch`, `code-review`, `converge`, `docs-review-expert`, `feature-status`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`, `weekly-intel`
- `gemini`: `analyze-context`, `architecture`, `autosearch`, `code-review`, `converge`, `docs-review-expert`, `feature-status`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`, `weekly-intel`
- `kiro`: `analyze-context`, `architecture`, `autosearch`, `code-review`, `converge`, `docs-review-expert`, `feature-status`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`, `weekly-intel`

## By Use Case
- `analysis`: `analyze-context`
- `analyze`: `analyze-context`
- `architecture`: `architecture`, `docs-review-expert`
- `autosearch`: `autosearch`
- `code`: `code-review`
- `conflict`: `resolve-conflict`
- `context`: `analyze-context`, `threader`
- `converge`: `converge`
- `docs`: `docs-review-expert`
- `expert`: `docs-review-expert`
- `feature`: `feature-status`
- `gitops`: `gitops-review`
- `import`: `uac-import`
- `intel`: `weekly-intel`
- `mentor`: `mentor`
- `planning`: `uac-import`
- `prompting`: `mentor`, `uac-import`
- `resolve`: `resolve-conflict`
- `review`: `code-review`, `docs-review-expert`, `gitops-review`, `weekly-intel`
- `status`: `feature-status`
- `supercharge`: `supercharge`
- `testing`: `testing`
- `threader`: `threader`
- `weekly`: `weekly-intel`

## All Capabilities
### Analyze Context — Iterative Multi-File Analysis Workflow
- Slug: `analyze-context`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - analyze several files or transcripts over a long session
  - keep durable analysis notes that survive context loss
  - process a broad repo investigation one item at a time
  - recover and continue a previously interrupted analysis
  - preserve progress across a long research or audit workflow before a later recommendation step
- Summary: Maintains durable analysis state for long-running multi-file investigations. Use when repo analysis must survive compaction or interruption, not for design, imports, or behavioral comparison.

### Architecture Studio
- Slug: `architecture`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - design or review an API contract
  - propose a schema, indexing plan, or data model
  - choose between design patterns or refactor directions
  - design a system topology, reliability model, or scale strategy
  - produce a migration-safe architecture recommendation with rollback guidance
- Summary: Designs APIs, schemas, patterns, and system topology with explicit boundaries and trade-offs. Use for concrete architecture decisions, interface design, or rollback-aware system plans.

### Autosearch — Goal-Driven Improvement Search, Evaluation, and Promotion
- Slug: `autosearch`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Version: `v1.1`
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
- Summary: Optimizes prompts, skills, tools, workflows, and code with minimal-loop investigation, bounded search, and baseline comparison. Use for experiments, behavioral variant comparison, or proof that a candidate beats baseline.

### Commit Review — Git Commit Quality Gate
- Slug: `code-review`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - review the latest commit
  - check whether this diff is too broad
  - judge whether AI-generated changes are over-engineered
  - tell me if this commit message and change scope are strong enough to merge
- Summary: Commit Review for git commit quality gates, scope control, and over-engineering detection.

### Converge — Multi-Source Synthesis, Conflict Surfacing, and Final Recommendation
- Slug: `converge`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - compare these ideas and pick one
  - synthesize these documents into one proposal
  - converge on the best plan
  - tell me what to keep, what to reject, and why
  - surface the real conflicts before we decide
- Summary: Universal Synthesis and Convergence for multi-source proposal comparison, conflict surfacing, decision analysis, and one coherent final recommendation.

### Docs Review Expert — Documentation IA, Drift, and Release Hygiene
- Slug: `docs-review-expert`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - judge the repo documentation quality or organization
  - tell me what belongs in `README.md` versus `docs/`
  - check whether release docs, setup docs, or examples drifted
  - make docs cleaner, more linkable, or more readable
  - review a PR or release for documentation hygiene
- Summary: Documentation Review Expert for information architecture, explainable technical writing, repo doc layout, drift detection, and documentation quality gates across commits, pull requests, merges, and releases.

### Feature Status — Deep Completeness Analysis
- Slug: `feature-status`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
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
- Summary: [BenK] Deep feature completeness analysis — scope vs. proof with prioritized recommendations

### GitOps Review — Repo Hygiene, CI, Release, and Merge Gate
- Slug: `gitops-review`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - judge the repo organization or GitOps hygiene
  - make sure my commits are logically scoped and messages are strong
  - check whether my PR is ready to merge
  - confirm CI is green on GitHub and GitLab
  - merge, push, package, tag, release, or clean up branches
  - update changelog or release notes as part of a release gate
- Summary: GitOps Review for repo hygiene, commit quality, PR readiness, CI state, packaging, changelog, merge, tag, push, and release gates across GitHub and GitLab.

### Mentor — Senior Engineering Oversight and Workflow Guidance
- Slug: `mentor`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - what should I do next
  - help me plan this change safely
  - check repo health and tell me the next reversible move
  - supervise execution across several capabilities
  - turn this rough request into a sharper plan or higher-quality prompt
- Summary: [Medhat] Senior engineering oversight, planning, and workflow guidance.

### Merge Conflict Resolution — Structured Conflict Analysis
- Slug: `resolve-conflict`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - help me resolve this merge conflict
  - compare these conflicting branch edits and tell me what survives
  - preview how to merge this branch safely
  - tell me what content is orthogonal versus contradictory
- Summary: Merge Conflict Resolution for structured conflict analysis, additive merging, and inversion-led trade-off handling.

### SuperCharge — Prompt Engineering, Planning Hardening, and Graded Improvement
- Slug: `supercharge`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Version: `v4.0`
- Invocation hints:
  - make this prompt better
  - harden this plan
  - compare these options and converge on one recommendation
  - compare these prompt variants, then tell me whether behavioral proof is needed
  - critique this proposal from several angles
  - grade this output and iterate it upward
  - design an agentic workflow or prompt stack
- Summary: Hardens prompts, plans, and workflows through structured critique and graded refinement. Use when the user wants a better artifact or a sharper comparison before measured evaluation.

### Testing Studio — Test Design and Coverage Analysis
- Slug: `testing`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - generate unit tests
  - design end-to-end tests
  - find edge cases we are missing
  - show me coverage gaps
  - tell me what to test first for this change
- Summary: Testing Studio for unit-test generation, end-to-end test design, edge-case discovery, and coverage gap analysis.

### Threader — Full-Thread Transcript Export and Recall Capture
- Slug: `threader`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - export this thread
  - give me a transcript of this conversation
  - create a durable handoff file from the current chat
  - prepare this thread for another model, reviewer, or archive system
- Summary: [Medhat] Context Threader & Exporter (Memory Management)

### UAC Import — Capability Intake, Quality Review, and Uplift
- Slug: `uac-import`
- Type: `skill`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - import a prompt, prompt pack, or capability into this repo
  - classify whether this source should become a skill, agent, or manual review
  - explain how this external source would land into SSOT and descriptors
  - judge whether a candidate is ready to apply
  - tell me whether this import needs stronger behavioral proof before landing
- Summary: Inspects external prompt-like sources and maps them into Core-Prompts plan, judge, and apply flows. Use when importing, planning, judging, or applying a new or updated capability.

### Weekly Intelligence — Multi-Source Progress Report with Fact-Check Audit
- Slug: `weekly-intel`
- Type: `both`
- Install target: `repo_local`
- Supported CLIs: `claude, codex, gemini, kiro`
- Invocation hints:
  - what happened this week / last week / since Tuesday
  - weekly status report for my team
  - summarize progress across these chat spaces and repos
  - give me something I can share with leadership
  - pull together what we accomplished and what's at risk
- Summary: Multi-source weekly intelligence gathering, convergence, fact-check audit, and single-document report generation (exec narrative body + technical appendices) for any team, project, or time window.
