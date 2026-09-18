# Bounded repository inspection

This is a read-only evidence acquisition procedure, not the research acceptance
policy. Use it only when the work order includes repository access. The research
stage owns questions and evidence sufficiency; the gate owns the verdict.

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
