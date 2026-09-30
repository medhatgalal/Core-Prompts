# Resource delivery audit failure

The first author/assessor and follow-up workers were assigned relative resource
names with an explicit worktree instruction, but native host cwd remained the
primary checkout. The assessor's supplied hashes identify baseline resources.
Task-local session traces (actual custom_tool_call entries) confirm the wrong
working directory for resource reads and unexpected memory/file discovery.

Preserve these observations and outputs. Correct content is not evidence that the
new resource bundle was read. Prior candidate-specific success claims are withdrawn;
there is no measured comparative improvement. Prompt allowlists were not enforced
boundaries. This is a measurement/delivery defect, not a demonstrated instruction
regression or permission to modify global host policy.

Prevention for this task: absolute resource and input paths, explicit resource
hash output, fresh bounded workers with only raw fixture inputs, and verification
of actual native tool traces before accepting diagnostic evidence. Existing owner:
.kiro/steering/agent-behavior.md comparative-evaluation/resource-boundary rules and
the shaping work-order resource identities. No new generic agent framework.
