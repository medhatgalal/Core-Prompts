# Ask through the tools this session actually provides

Load this reference only when a material clarification is needed and the question
mechanism is uncertain. This is a recognition guide, not a tool registry, permission
grant or promise that a particular harness exposes a tool. Do not load it for a
clear direct task or merely because a tool name appears in the table.

## Recognizable question mechanisms

| Host family | Recognizable names | Free-text handling | Evidence and limits |
| --- | --- | --- | --- |
| Codex | `request_user_input`; some clients expose `request_user_input_async` | Follow the actual schema. In the observed session the client adds Other/free text; do not add a duplicate option when the schema forbids it. | Session-dependent names, modes and restrictions. The public app-server describes the `tool/requestUserInput` bridge; that bridge is not a model-tool name to invent. Tool exposure does not prove a routing-skill call occurred. |
| Grok Build | `ask_user_question` | Confirm Other/free text in the current tool/UI contract; otherwise use inline Other. | Official configuration documents this tool family and configurable timeouts. That is documented support, not proof of the user's current Grok Bot session or a completed interaction. |
| Claude Code | `AskUserQuestion` | Official documentation describes the native Other row and notes/custom text. | Availability depends on the actual session. A terminal, extension, SDK or headless client need not expose or handle the same interactive mechanism. |
| Other or unidentified host | Use an exposed equivalent only after reading its description/schema. | Preserve a free-form answer or use the inline fallback. | Do not infer a tool from a provider/model name, install a tool, change flags, or invent a wrapper to make the table appear complete. |

The table records documented mechanisms and a dated observation, not a permanent
compatibility claim. Resolve current support from the host-supplied tools and their
actual contracts. Ordinary skill installation does not add a question tool.

## Choose the mechanism

1. Reuse the request, prior answers and accepted work first. Ask only if the missing
   answer would change the next useful result, depth, required input or scope.
2. Check tools already supplied by the host, using its supported discovery if needed.
   Read the selected tool's actual schema, mode limits and input support. Do not
   inspect hidden settings or change configuration to obtain it.
3. Prefer a suitable question tool. Supply the actual required fields, relevant
   outcome choices, an honest context-based recommendation and a free-text path.
   A documented native Other field counts. If the needed input type is unsupported,
   such as an attachment in a text-only question tool, ask inline instead.
4. Read the real result. Pending, skipped, declined, timed-out and unanswered states
   are not a submitted choice. A displayed recommendation or default is not consent.
   Preserve permission/approval mechanisms; this reference concerns clarification.
5. If no suitable mechanism is exposed or allowed, ask the same focused question
   inline. Use two or three relevant A/B/C options when helpful, explain the
   recommendation briefly, and include **Other — describe what you mean**, a
   correction or “not sure.” Stop intake when the next bounded job is clear.

## What verification establishes

Keep these separate: provider documentation; observed session tool exposure;
observed tool invocation; displayed question UI; and a returned answer (including
Other). The routing skill's catalog inspector observes skills and relationship
bindings, not question tools. Printed tool names and inline rehearsals do not prove
native UI invocation. For a live check, use a permitted interactive session and
record the actual event and answer without changing authentication, trust or
provider settings to obtain a pass.

## Sources and review date

Reviewed October 21, 2026. Recheck the current session schema when using a tool;
these links are supporting references rather than required network reads per task.

- [OpenAI skills and implicit/explicit selection](https://developers.openai.com/codex/skills/)
- [OpenAI app-server user-input bridge](https://developers.openai.com/codex/app-server/)
- [Grok Build tool configuration](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/05-configuration.md)
- [Claude Code question-tool behavior](https://code.claude.com/docs/en/tools-reference#askuserquestion-tool-behavior)
