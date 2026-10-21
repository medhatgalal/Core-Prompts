# Start with your intent

Describe the result you want and what you already have. The assistant can choose
one useful starting job, explain why it fits, and name the artifact you should
expect. You do not need to memorize 36 skill names or run them as a pipeline.

For example:

> Help me turn these rough notes into a clear problem statement. We have not
> agreed on a solution. Use the installed Core-Prompts skills that fit this job,
> preserve our project's rules, and explain your first step.

A suitable response starts with something like: “I’ll use
`engos-design-frame-from-vague` because the problem and outcome are still unclear.
You’ll get a solution-free frame. Once you accept it, we can decide whether a
specification or a full shaping workshop is useful.” The assistant then carries
out the work already authorized by your request. Selecting a skill is not a new
permission ceremony.

[Open the portable visual guide](guide/index.html) to browse routes and mark
work you say is already accepted. Those selections are context for a recommendation,
not proof of acceptance or task completion. The guide does not interpret free-form
language or execute skills; the assistant applies the
[intent-routing policy](../.kiro/steering/skill-routing.md) to the actual context.
The [full job map](SKILL-JOB-MAP.md) remains the lookup for all 36 names.

![Six common starting points: frame a vague problem, specify unclear acceptance, compare actual proposals, shape a full workshop, implement a clear change, or diagnose an unexplained failure.](guide/intent-flow.svg)

## Find the first missing job

| What you mean | First useful job | What you receive |
| --- | --- | --- |
| “We have a problem, but cannot yet explain it clearly.” | `engos-design-frame-from-vague` | A solution-free frame: people, outcome, appetite and open questions. |
| “We know the feature, but not its exact behavior or acceptance.” | `engos-design-specify-change` | Requirements, acceptance checks and unchanged behavior. |
| “These two actual proposals disagree; help us choose.” | `engos-reconciliation-converge` | An attributed comparison and recommendation. Missing inputs are requested, not invented. |
| “Guide a full Shape Up workshop.” | `engos-design-shaping` | Framing, research, shaping, review and delivery evidence under the existing stage gates; the human owner makes the betting decision. |
| “Make this small, clear change.” | `engos-delivery-implement-slice` | A bounded patch, actual checks and remaining limits. |
| “This fails, and the cause is unclear.” | `engos-debug-diagnose-failure` | A supported cause or bounded unknown and a repair handoff. |
| “These requirements are accepted; break the work down.” | `engos-design-plan-implementation` | Verifiable tasks, dependencies, interfaces and holds. |
| “We need a material technical decision.” | `engos-design-architecture` | A justified design with alternatives, risks and recovery. |
| “Review this actual diff.” | `engos-quality-code-review` | Candidate-bound findings and review limits. |
| “Review this finished pitch.” | `engos-audit-pitch-review` | Pitch gaps and a betting-readiness recommendation, without invented workshop history. |

The distinction is the missing decision or artifact, not a keyword. “Plan” can
mean clarify a problem, specify acceptance, compare proposals or break accepted
work into tasks. Your context tells the assistant which job is useful. If a fact
would materially change that choice, it can ask a focused question while
continuing work that already has sufficient inputs and authority.

Existing accepted work lets you start later. A small repair with a supported
cause can enter implementation directly. Architecture is useful only when a
material technical decision remains; an absent architecture document alone does
not require a design pass. A real diff or finished pitch can be reviewed directly.
If the requested work is already satisfied, the useful result may be a verified
no-op rather than another stage.

## Continue only when the next job is needed

A substantial feature often moves from **specification** to **architecture if
needed**, **useful task planning**, **one implementation slice**, and **review**.
Existing meaningful checks may make a separate test-design pass unnecessary.
Review feedback uses `engos-delivery-address-code-review` for selected actionable
comments. GitOps review assesses a requested merge/release gate; readiness does
not perform that external action. The [flow guide](SKILL-FLOWS.md) explains these
handoffs and their limits.

Full Shape Up work stays with the shaping conductor. Its existing G0/G1 framing,
G2 research, G3 review and G4 delivery contracts remain in force, together with
actual engineering agreement, team acceptance and human betting decisions.
A route card or checked box cannot replace those decisions or receipts. Draft-only
and frame-only requests retain their stopping points; changed uncertainty can
return work to an earlier stage. See the
[shaping workflow](engos-design-shaping.md) for the complete process.

Optional jobs stay optional:

- **Supercharge** strengthens an explicitly selected prompt, plan or proposal:
  `engos-meta-supercharge`.
- **Continuity** preserves a long investigation when you request a durable handoff:
  `engos-memory-context-continuity`.
- **Goal packets** compile reviewed intent when you explicitly want one:
  `engos-design-plan-to-goal`. Compiling does not launch the goal.
- **Batman** provides its controller-led delivery protocol when explicitly selected:
  `engos-orchestration-batman`. It is not the default route for a small fix.

Converge is directly useful when you supply competing inputs; it is not a compulsory
hop between ordinary stages. Audit, incident, documentation, presentation and other
jobs remain available through the [full job map](SKILL-JOB-MAP.md).

## A copyable request for any assistant

Replace the brackets and provide a trusted Core-Prompts root if the assistant
does not already have this guidance:

```text
Outcome: [what I want]
Context and existing accepted work: [inputs, decisions, design, plan or patch]
Authorized scope: [inspection, specific edits/checks, or other allowed actions]

Use the available Core-Prompts skills when they fit this request. Read
<CORE_ROOT>/.kiro/steering/skill-routing.md and resolve the routing data it
names for this source checkout or verified runtime. Human docs are optional
when the installed support root does not include them.
Choose one first missing job from my intent and accepted work. Briefly name
its exact skill, why it fits, the expected artifact and the next conditional
handoff. Then proceed with the work already authorized above.

Confirm the package this session can actually use. Read its complete SKILL.md
and only the resources needed for this job. Preserve my project, host and
home policies and existing review/approval gates. Do not invent missing inputs,
completed stages or new permission. Do not launch a chain of skills or a goal
just because the route mentions a next step.
```

This is a plain-language request, not a provider CLI flag. If you prefer a named
skill, keep using the documented host selector: Codex uses `$<skill-name>` and
Grok uses `/<skill-name>`. Other hosts use their current supported skill interface;
check session discovery rather than borrowing invocation syntax from another
provider. [Discovery and troubleshooting](GETTING-STARTED.md#verify-discovery-on-your-host).

## Opt in from a consumer project

The guide is portable, but its presence does not install a global router.
Core-Prompts' root `AGENTS.md` points at the policy for Core-Prompts work. Installing
skill packages or opening an HTML page does not prove that another project's
harness has loaded that pointer.

For a one-off session, paste the request above or explicitly provide the policy
and its routing data. Human docs and the visual guide can help when available;
they are not prerequisites for using an installed support root. For continuing use, a project owner can add a short pointer to the
project instruction file that their harness actually supports, such as `AGENTS.md`
where supported. Use a trusted, version-identified source checkout or verified
distribution as `<CORE_ROOT>`; keep it separate from the project being worked on.
A sample opt-in pointer is:

```text
This project opts into Core-Prompts intent routing when its skills fit the task.
Trusted Core-Prompts root: <CORE_ROOT>.
For Core skill selection, read <CORE_ROOT>/.kiro/steering/skill-routing.md
and use the source or runtime routing data it names. Human docs are optional;
do not require them in an installed support root. Apply this project's rules
and applicable host/home policies. This
pointer grants no additional actions and does not make every task a Core task.
```

The project owner chooses that integration; this change does not edit consumer,
home or provider configurations. Dotfiles remains the owner of home-global rules.
Ordinary use in a consumer project follows that project's workflow, not
Core-Prompts' source-maintenance UAC/worktree/PR/MR prerequisites.

Kiro's [official steering documentation](https://kiro.dev/docs/steering/) describes
workspace steering and always-included `AGENTS.md`; custom agents require explicit
steering resources. Therefore a custom agent's effective resource list must be
checked separately. This guide does not claim global autoloading or modify it.

## Where this guidance lives

- [Canonical routing policy](../.kiro/steering/skill-routing.md): selection and
  authority rules for opted-in contexts.
- [Compact route catalog](../.meta/intent-routing.json): shared descriptive data
  for common route cards and model lookup; not an executable classifier.
- [Existing source job map](../.meta/skill-job-map.json): all 36 current skill
  identities and boundaries for source-side lookup. Runtime packages instead use
  the available skill inventory and relevant bundled
  [capability descriptors](../.meta/capabilities/).
- [Generated runtime route copy](../.kiro/steering/intent-routing.json): the same
  compact catalog beside the steering policy, available without human docs or the
  source-only job map. The selected skill's own contract remains authoritative.
- [Examples](EXAMPLES.md#start-without-a-skill-name): plain-language requests and
  the handoff to expect.

The [hosting guide](GUIDE-HOSTING.md) explains preview and publication choices;
no hosting activation follows from this document.

The visual guide is a presentation of this data. Static consistency checks can
verify names, links and generated content; they do not establish improved model
routing, native discovery or successful task execution.
