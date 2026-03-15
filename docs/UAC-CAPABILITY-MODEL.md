# UAC Capability Model

UAC is the authoritative classifier for both imported sources and existing SSOT entries.

## Capability Types

| Capability Type | Simple Meaning | Automatic Deploy? |
| --- | --- | --- |
| `skill` | Reusable prompt/workflow with clear task guidance and bounded output | Yes |
| `agent` | Delegated specialist with explicit control-plane behavior or agent-only runtime semantics | Yes |
| `both` | One SSOT source that should emit both workflow surfaces and agent surfaces | Yes |
| `manual_review` | Mixed, weak, or config-heavy content that should not deploy automatically | No |

## Decision Rubric

### `skill`
Use when the source is mainly a reusable workflow or prompt asset.

Common signals:
- explicit objective, in-scope, out-of-scope, constraints, or acceptance sections
- workflow/process framing
- usage examples or output format sections
- `SKILL.md`-style structure

### `agent`
Use when the source behaves like a delegated specialist rather than only a reusable prompt.

Common signals:
- `kind: agent` or `role: agent`
- tool or control-plane metadata
- sub-agent/delegation language
- explicit operating identity, responsibilities, or mission

### `both`
Use when both sets of signals are strong.

This means:
- keep one canonical SSOT entry
- emit workflow/skill surfaces and agent surfaces from the same source
- do not duplicate the source into two SSOT files

### `manual_review`
Use when the source is too weak, too mixed, or too config-heavy to package safely.

Common signals:
- wrapper/config without a clear prompt body
- missing objective/scope structure
- conflicting evidence for multiple shapes

## Commands Are Not Capability Types

`command` is an invocation surface, not a peer capability type.

That means UAC decides:
- `skill`
- `agent`
- `both`
- `manual_review`

Then Core-Prompts derives the right surfaces for each CLI.

## Deployment Matrix

| Capability Type | Codex | Gemini | Claude | Kiro |
| --- | --- | --- | --- | --- |
| `skill` | `codex_skill` | `gemini_command`, `gemini_skill` | `claude_command` | `kiro_prompt`, `kiro_skill` |
| `agent` | `codex_agent` | `gemini_agent` | `claude_agent` | `kiro_agent` |
| `both` | `codex_skill`, `codex_agent` | `gemini_command`, `gemini_skill`, `gemini_agent` | `claude_command`, `claude_agent` | `kiro_prompt`, `kiro_skill`, `kiro_agent` |
| `manual_review` | none | none | none | none |

## Existing SSOT Behavior

Existing SSOT entries are audited using the same rubric as external imports.

For each SSOT entry, UAC compares:
- declared capability in frontmatter
- inferred capability from content and structure
- expected generated surfaces
- actual generated surfaces on disk

Audit statuses:
- `aligned`
- `missing_agent_surface`
- `missing_skill_surface`
- `over-generated`
- `manual_review`
- `frontmatter_mismatch`
