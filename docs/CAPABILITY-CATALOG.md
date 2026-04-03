# Capability Catalog

Generated from canonical manifest and descriptor metadata. Use this page to see what Core-Prompts ships, what each capability is for, and where it lands.

- Capability count: `12`

## Start Here
- `architecture` — Architecture Studio: Architecture Studio for API design, database design, design-pattern selection, and system design with black-box boundaries, concrete artifacts, and migration-safe recommendations.
- `resolve-conflict` — Merge Conflict Resolution — Structured Conflict Analysis: Merge Conflict Resolution for structured conflict analysis, additive merging, and inversion-led trade-off handling.
- `testing` — Testing Studio — Test Design and Coverage Analysis: Testing Studio for unit-test generation, end-to-end test design, edge-case discovery, and coverage gap analysis.
- `gitops-review` — GitOps Review — Repo Hygiene, CI, Release, and Merge Gate: GitOps Review for repo hygiene, commit quality, PR readiness, CI state, packaging, changelog, merge, tag, push, and release gates across GitHub and GitLab.
- `supercharge` — SuperCharge — Prompt Engineering, Planning Hardening, and Graded Improvement: SuperCharge for prompt creation, prompt refinement, planning hardening, option comparison, grading, multi-pass critique, and structured execution-quality improvement across direct and agentic workflows.

## By CLI
- `claude`: `analyze-context`, `architecture`, `code-review`, `converge`, `docs-review-expert`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`
- `codex`: `analyze-context`, `architecture`, `code-review`, `converge`, `docs-review-expert`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`
- `gemini`: `analyze-context`, `architecture`, `code-review`, `converge`, `docs-review-expert`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`
- `kiro`: `analyze-context`, `architecture`, `code-review`, `converge`, `docs-review-expert`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`

## By Use Case
- `analysis`: `analyze-context`, `architecture`, `converge`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`
- `analyze`: `analyze-context`
- `architecture`: `analyze-context`, `architecture`, `code-review`, `converge`, `docs-review-expert`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `uac-import`
- `code`: `code-review`
- `context`: `analyze-context`, `architecture`, `code-review`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `threader`
- `debugging`: `analyze-context`, `architecture`, `code-review`, `converge`, `docs-review-expert`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`
- `docs`: `docs-review-expert`
- `expert`: `docs-review-expert`
- `gitops`: `gitops-review`
- `import`: `converge`, `uac-import`
- `packaging`: `converge`, `docs-review-expert`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `uac-import`
- `planning`: `architecture`, `converge`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`
- `prompting`: `analyze-context`, `architecture`, `code-review`, `converge`, `docs-review-expert`, `gitops-review`, `testing`, `threader`, `uac-import`
- `review`: `analyze-context`, `architecture`, `code-review`, `converge`, `docs-review-expert`, `gitops-review`, `mentor`, `resolve-conflict`, `supercharge`, `testing`, `threader`, `uac-import`
- `routing`: `analyze-context`, `mentor`, `resolve-conflict`, `supercharge`, `threader`, `uac-import`
- `testing`: `testing`
- `threader`: `threader`

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
- Summary: Iterative Analysis Workflow for multi-file, multi-source repo analysis with canonical memory files, anti-sprawl controls, and compaction-safe progress tracking.

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
- Summary: Architecture Studio for API design, database design, design-pattern selection, and system design with black-box boundaries, concrete artifacts, and migration-safe recommendations.

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
  - critique this proposal from several angles
  - grade this output and iterate it upward
  - design an agentic workflow or prompt stack
- Summary: SuperCharge for prompt creation, prompt refinement, planning hardening, option comparison, grading, multi-pass critique, and structured execution-quality improvement across direct and agentic workflows.

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
- Summary: UAC Import for capability intake, quality review, uplift, and canonical SSOT plus descriptor landing.
