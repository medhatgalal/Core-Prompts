# engos-design-shaping capability knowledge

This design note is scoped to the shaping packet. A future canonical apply would
bundle reusable rules under sources/capability-resources for the owning skill;
task-specific observations remain in reports. It does not create another tracker
or update Codex memory. Upstream reusable PM knowledge remains owned by the
pm-dev-tools knowledge directory; this exercise does not mutate that repository.

## Verified now

- Upstream docs moved agent/skill authoring to pm-dev-tools. Resolve its README
  before relying on the older site's native file paths.
- The current source has a pitch-audit skill and shaping-decisions checklist,
  replacing older names used by site prose. See research-notes.md citations.
- The runtime supplies real independent workers. The observed G0 and failure
  matrix judgments identify actual worker IDs; author self-assessment is separate.
- Workspace credentials work with existing Keychain access outside the restricted
  shell. Sandbox decrypt failure did not require new login, scopes or a backend.
- Current gws drive.files.create schema supports Google Doc conversion on import;
  installed global CLI flags include --upload. No document conversion has yet been
  attempted in this new exercise, so schema support is not runtime placement proof.
- Core-Prompts is public. Private exercise/code evidence stays local and on the
  requested work-account surface. Public reports carry sanitized observations.

## Not yet proven

Private DOCX import/image placement, native table completeness and target pixels
in this run; wiki macro support; chat Mermaid support; five-stage success from
the real input. The earlier session's HTML rendering does not discharge these.

## Durable lessons represented in the candidate

1. A named spike records uncertainty but cannot pass Research as if executed.
2. Distinguish immutable reviewed source from appended render/placement receipts.
3. Do not make an earlier gate depend on an artifact first created after it.
4. Bind the reviewer overlay explicitly; otherwise old score/readiness semantics
   can override the new process while the call still appears successful.
5. Keep final content inventory complete across surfaces, not merely visible.
6. Separate historical context and proposed defaults from actual human decisions.

Prevention status: encoded in design candidates; not installed or production
promoted. Behavioral smoke observations and unresolved full-run criteria are
listed in the validation report, not replaced with a general success label.
