# UAC Capability Model

UAC is the authoritative classifier for imported sources and existing SSOT entries.

## Capability Types

| Capability Type | Meaning | Auto deploy? |
| --- | --- | --- |
| `skill` | Reusable prompt/workflow with clear task guidance and bounded output | Yes |
| `agent` | Delegated specialist with explicit control-plane behavior | Yes |
| `both` | One source that should emit workflow and agent surfaces | Yes |
| `manual_review` | Weak, mixed, or conflicting content | No |

## Not Capability Types
These are wrapper or invocation surfaces, not peer capability classes:
- commands
- plugins
- powers
- extensions

## Layered Manifest
Every accepted capability should produce three layers.

### Minimal
- capability type
- role
- tags
- inputs/outputs
- tool policy
- resources
- packaging profile
- install target
- emitted surfaces
- provenance
- confidence/rationale/review status

### Expanded
- relationship suggestions
- dependencies
- overlap candidates
- migration notes
- adjustment recommendations

### Org Graph
- org role
- reports/delegates/collaborates suggestions
- authority tier
- work-graph impact

Rule: expanded and org-graph layers are advisory. Orchestrators decide whether to use them.

## Anti-Complecting Check
Every import/plan/apply run compares the candidate against the current library and emits:
- duplicate risk
- overlap report
- conflict report
- fit assessment
- required existing adjustments
- required new-entry adjustments
- work-graph change summary

If unresolved overlap/conflict is too high, the result must fall to `manual_review`.

## Install Target
Supported install scopes:
- `global`
- `repo_local`
- `both`

Default behavior:
- infer likely target
- show recommendation in plan/import output
- require confirmation before apply writes

## Deployment Matrix

| Capability Type | Codex | Gemini | Claude | Kiro |
| --- | --- | --- | --- | --- |
| `skill` | `codex_skill` | `gemini_command`, `gemini_skill` | `claude_command` | `kiro_prompt`, `kiro_skill` |
| `agent` | `codex_agent` | `gemini_agent` | `claude_agent` | `kiro_agent` |
| `both` | `codex_skill`, `codex_agent` | `gemini_command`, `gemini_skill`, `gemini_agent` | `claude_command`, `claude_agent` | `kiro_prompt`, `kiro_skill`, `kiro_agent` |
| `manual_review` | none | none | none | none |

Wrapper examples:
- Codex plugin wrapper
- Gemini extension wrapper
- Claude plugin wrapper
- Kiro power wrapper

Those wrappers are additive deployment forms only.
