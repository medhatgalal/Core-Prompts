## GitOps Design, Hygiene and Process ##

### Intent
- `uplift_existing_ssot`

### Purpose
- Establish durable repository rules for review timing, protected-branch hygiene, CI/CD gates, release hygiene, and GitHub/GitLab parity.

### Goals
- define when docs/GitOps reviews must occur
- align review triggers across commit, pull request, merge, and release
- preserve branch protection and required approvals as first-class design constraints
- improve existing review-oriented SSOT descriptions so user intents route better

### Sources
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
- https://docs.gitlab.com/user/project/codeowners/
- https://docs.gitlab.com/user/project/merge_requests/approvals/rules/

### Research Targets
- `~/Desktop/ai_repos/beads/docs/PROTECTED_BRANCHES.md`
- `~/Desktop/ai_repos/gemini-cli/docs/issue-and-pr-automation.md`
- `~/Desktop/ai_repos/gemini-cli/.gemini/skills/pr-creator/SKILL.md`
- `~/Desktop/ai_repos/codex-settings/prompts/github-pr-reviewer.md`

### Benchmarks In Repo
- `ssot/code-review.md`
- `docs/RELEASE-PACKAGING.md`
- `docs/ORCHESTRATOR-CONTRACT.md`

### Current Gaps
- GitOps expectations are split across scripts, AGENTS, and release docs
- no single durable maintainer rule set covers commit/PR/merge/release review timing
- existing skill descriptions do not consistently hint at GitOps-related invocation

### Proposed Public Name
- `GitOps Design and Hygiene`

### Proposed Slug
- `gitops-design-hygiene`

### Proposed Description
- Advisory guidance for protected-branch workflows, review timing, CI/CD gating, release hygiene, and GitHub/GitLab parity in AI-assisted repositories.

### Capability Type
- `research_only` for this slice; do not land as SSOT yet

### Role / Invocation Hints
- use when changing repo workflow, review policy, protected-branch behavior, CI triggers, release gates, or multi-remote process hygiene

### Required Inputs
- current workflow files
- branch protection and review constraints
- release and packaging flow

### Expected Outputs
- durable maintainer rules
- review trigger matrix
- recommended placement of GitOps guidance in repo docs or policy files
- selective SSOT description uplift recommendations

### Tool and Runtime Boundaries
- allowed: inspect workflows and process docs, recommend policy and placement, update maintainer docs and capability descriptions
- forbidden: runtime orchestration, inventing branch protection settings not backed by repo or platform docs

### Metadata Expectations
- if landed later, it must stay advisory and process-focused
- in this slice, the durable output belongs in maintainer docs and AGENTS guidance, not as a new SSOT capability

### Surface Expectations
- none in this slice

### Acceptance Criteria
- review timing is explicit for commit, pull request, merge, and release
- GitHub/GitLab parity expectations are documented
- process rules are durable and easy to locate
- the changes do not imply orchestration ownership

### Evaluation Examples
- request: “What checks and reviews should happen before merge and release?”
- good output: exact trigger matrix, file placements, and repo rule updates
- failure mode: vague Git advice with no mapping to current repo docs or CI files

### Recommended Landing Paths
- `docs/MAINTAINER-HYGIENE.md`
- `AGENTS.md`
- selected SSOT description updates

### Open Risks
- process material can sprawl if it is split across too many docs
- some external guidance is platform-specific and must be adapted to this repo, not copied wholesale
