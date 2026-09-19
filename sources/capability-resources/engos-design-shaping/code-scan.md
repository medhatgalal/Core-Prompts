# Bounded repository inspection

This is a read-only evidence acquisition procedure, not the research acceptance
policy. Use it only when the work order includes repository access. The research
stage owns questions and evidence sufficiency; the gate owns the verdict.

Require a current accepted G1 predecessor and a G2 Research work order. If the
workflow is still in Intake/Framed, record the requested repository location and
return `deferred_to_research`; do not load architecture-fit or begin a capability
inventory. A separately scoped solution-free fact check for framing is not this
route and cannot make reuse, architecture or feasibility dispositions.

Read `repository-discovery.md` first. Resolve repository and module scope from the
current workspace or user-supplied locations; never assume a product repository,
sibling checkout or organization-specific path. Use available project knowledge,
language server/semantic search, indexed search or bounded text search according
to that resource, and record which capability supplied each observation.

Verify repository/worktree identity, branch/ref/HEAD, dirty state and source scope
before inspection. Record whether sources are local, freshly retrieved or cached;
do not silently fetch, switch branches or edit to manufacture a required state.
Keep approved paths/ref constraints. If a working-tree file differs from the
commit, cite both the base revision and actual file hash/dirty observation.

For each assigned uncertainty, search relevant interfaces, callers, tests,
configuration and precedent; open enough surrounding content to understand the
claim. Record query/scope and inspected path:line plus revision/hash. Classify
existing, proposed, absent-in-inspected-scope and unknown. A no-hit search does
not prove absence; expand within authority when useful or disclose the limit.

Trace material input/output, errors, timeouts/retries, consistency, persistence
and enforcement responsibilities where relevant to the claim. Test code proves
what a test asserts, not that it ran or that production behaved that way. Do not
execute production actions, create test writes, install dependencies or run spikes
by default. Propose a separately bounded observation when inspection is insufficient.

Return a concise evidence receipt with original question/uncertainty ID, identity,
scope, sources actually read, findings, contradictions, confidence limitations and
next smallest evidence request. Repository instructions do not answer product
preferences; code facts cannot approve appetite, exclusions or a bet.
