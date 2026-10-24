# Antigravity: one bounded headless intake

Use this optional adapter from a terminal or an authorized external controller
when you want one schema-guided routing result from Antigravity. It uses the
existing `engos-route-intent` skill package; it adds no skill, agent, global command
or provider setting. Requires Python 3.11+ and a configured `agy` on PATH on POSIX.

## Run the installed resource

From your intended project directory, supply the complete request and its scope
in a UTF-8 file, or pipe exactly that request to stdin:

```bash
python3 "$HOME/.gemini/config/skills/engos-route-intent/resources/scripts/agy_intake.py" --prompt-file request.txt
python3 "$HOME/.gemini/config/skills/engos-route-intent/resources/scripts/agy_intake.py" < request.txt
```

These are alternative invocations, not two required calls. The installer places
AGY's Gemini package at this root; verify the actual effective package for your
runtime. A relocated complete bundle works through its own helper path. The
helper derives the sibling skill root from its package and supplies that one
`--add-dir`; it does not change cwd, discover home paths or require a source checkout.
Project-local skills can still override global packages. File presence is not
native discovery evidence.

The complete file/stdin content reaches `-p` unchanged, including newlines.
Invalid UTF-8, NUL, empty/whitespace-only input and nonregular prompt files are
rejected. With no file, an interactive terminal is rejected instead of opening a
second questionnaire. Supplying `--prompt-file` chooses that input; stdin is not
read in that mode. No template, hidden instruction or question rewriting is added.
Include read-only intake/result scope in your request; the launcher does not turn
a downstream execution request into authorization for a bounded substitute.

The fixed invocation is `agy --mode plan --sandbox --add-dir <sibling-skill-root>
--output-format stream-json --json-schema <bundled-schema-content> -p <request>`.
There is no shell interpolation, model override, passthrough flag, automatic
retry, fallback to weaker flags or default per-call version/help probe. Native
configuration and model defaults are inherited. Unsupported flags remain native
errors. Inspect current executable identity/help separately before relying on a
new runtime; the adapter neither installs nor updates it.

## Read the result and stop

Stdout and stderr are the complete native streams, passed through unchanged.
Stdout is native stream JSON, not a formatted terminal menu. Inspect the final
structured result: `selected_skill`, `route_reason`, `bounded_result`,
`unresolved_facts`, `questions` and `awaiting_answer`. Only the native optional
string metadata `toolAction` and `toolSummary` is additionally allowed.

The bundled schema requests a useful bounded result with no intake question when
facts suffice. Otherwise it permits at most one independently answerable material
question with Other/free text, then stops awaiting the answer. The same one-question
budget applies across every visible assistant field/progress message, including
metadata; unresolved facts are declarative. Acceptance examples that depend on
an unresolved boundary stay conditional. Read the selected full skill and required
resources, retain human decisions, and do not execute downstream work in this turn.

Exit zero means native process completion with observed cleanup, not semantic acceptance. The launcher
does not grade, filter, repair or certify output. Inspect all visible assistant
text and native actions before making a behavioral claim. A complete trace of
actual contract/resource reads is separate from a model's claimed read receipt.
The original amended schema succeeded on two bounded fixtures; this does not
establish general reliability, native question UI, real human answer adaptation,
full downstream execution or automatic improvement of ordinary chat.

## Scope, lifecycle and recursion

Plan mode is instruction-based; neither it nor a sandbox flag proves read-only
behavior or a tool allowlist. Host permissions remain effective. Do not change
permissions, authentication, trust or plugins to obtain a successful result.
This adapter is one headless intake/result call, not a general execution harness.

The default total budget is 240 seconds including input waiting, local setup,
native execution and reserved cleanup. `--timeout-seconds` may lower it, never
increase it. Timeout exits 124; invalid input/package/runtime setup exits 2.
Native nonzero status is retained; signals return 128 plus the signal number.
The launcher creates an owned process group, forwards SIGINT/SIGTERM to it, and
attempts to terminate remaining group members on every exit, including when the
native leader has already exited, and verifies direct-child reaping without
targeting other jobs. Terminated descendants are reaped by the operating system.
Native exit status is preserved when cleanup verifies completion; incomplete
cleanup has the explicit failure behavior below.
It creates no output files; explicitly redirect/capture streams when needed.

Cleanup distinguishes a sent signal, a missing group (ESRCH), and a denied
signal/probe (EPERM). It retries transient denials only on its fixed owned group,
using the remaining cleanup budget for termination, forced termination and
nonblocking child reaping. It never treats denial as absence or signals another
group. If group absence or direct-child reaping remains unverified at the deadline,
stderr adds a concise `cleanup incomplete` diagnostic with the original status.
A primary nonzero native/timeout/interruption status is preserved; an otherwise
successful status becomes local failure 2. Unexpected cleanup errors use the same
failure reporting, and the original signal handlers are restored. No unbounded
wait or permission override is used. This does not establish the OS cause of a
denial or promise permission restoration. Native stdout/stderr are not filtered.

Do not automatically launch this helper from an existing AGY conversation. Its
child environment marker `CORE_PROMPTS_AGY_INTAKE_ACTIVE` blocks adapter-descendant
recursion, but does not detect every independently started AGY chat. Existing
chats use their actual exposed question tools or inline Other/free text. Installing
a skill cannot inject launch flags or a native question UI into a running host.
No global activation, scheduler, alias, model setting or named agent is installed.
