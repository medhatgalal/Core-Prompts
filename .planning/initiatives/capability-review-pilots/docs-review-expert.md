## Docs Review Expert ##

### Intent
- `new_ssot_capability`

### Purpose
- Review and improve repository documentation so it remains readable, accurate, linkable, explainable, and aligned with the actual architecture and workflows.

### Goals
- keep README focused on orientation and quick-start flow
- keep durable docs in clear canonical homes
- detect doc drift on commits, pull requests, merges, and releases
- produce examples and evaluation criteria for what good documentation looks like
- keep docs legible to both humans and AI tools

### Sources
- https://github.com/thibaultyou/prompt-library/tree/main/prompts/documentation_specialist_agent
- https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/docs
- https://diataxis.fr/
- https://www.writethedocs.org/

### Research Targets
- stronger docs IA patterns from Diataxis and Write the Docs
- repo-level doc layout examples from `~/Desktop/ai_repos/get-shit-done` and `~/Desktop/ai_repos/gemini-cli`

### Benchmarks In Repo
- `docs/README.md`
- `docs/UAC-CAPABILITY-MODEL.md`
- `ssot/architecture.md`
- `ssot/code-review.md`

### Current Gaps
- no explicit docs-review specialist exists in SSOT
- durable doc hygiene rules are implied in multiple places but not centralized
- there is no single capability focused on IA, linking, drift, and docs review timing

### Proposed Public Name
- `Docs Review Expert — Documentation IA and Drift Guard`

### Proposed Slug
- `docs-review-expert`

### Proposed Description
- Documentation Review Expert for information architecture, readable technical writing, repo doc layout, drift detection, and documentation quality gates across commits, pull requests, merges, and releases.

### Capability Type
- `skill`

### Role / Invocation Hints
- use when the user asks to review docs, simplify docs structure, clean up repo docs, improve onboarding, fix stale docs, or decide where documentation belongs

### Required Inputs
- current README and docs structure
- target audience
- changed code or changed workflows when drift is suspected

### Expected Outputs
- current-state docs assessment
- recommended IA/layout changes
- file placement recommendations
- rewrite examples or section outlines
- drift findings with evidence
- commit/PR/merge/release review checklist

### Tool and Runtime Boundaries
- allowed: inspect docs, compare docs to code/workflows, recommend structure and wording, write or update docs when requested
- forbidden: orchestration, delegation policy, runtime control, pretending docs are current when they are not

### Metadata Expectations
- explicit documentation-focused display name and summary
- advisory-only boundary
- expected outputs centered on review and IA outcomes, not code execution

### Surface Expectations
- `codex_skill`, `gemini_command`, `gemini_skill`, `claude_command`, `kiro_prompt`, `kiro_skill`

### Acceptance Criteria
- the capability can distinguish README vs docs vs technical docs vs research docs
- it flags drift against real repo behavior
- it provides examples and evaluation criteria, not only critique
- it remains documentation-focused and non-orchestrating

### Evaluation Examples
- request: “Review the docs tree after this release and tell me what belongs in README vs docs/.”
- good output: IA assessment, exact file moves, rewritten section examples, and a review checklist
- failure mode: generic “improve documentation” advice with no file placement or drift evidence

### Recommended Landing Paths
- `ssot/docs-review-expert.md`
- `.meta/capabilities/docs-review-expert.json`
- generated surfaces under `.codex/`, `.gemini/`, `.claude/`, `.kiro/`

### Open Risks
- externally sourced prompts are verbose or template-heavy and need normalization
- overlap with `architecture` and `code-review` must stay explicit and bounded
