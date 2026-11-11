# Design freshness sweep

Scope: add a skill plus required execution inside specify-change, plan-implementation,
and shaping's technical Research after frame acceptance. Stop at open PR/MR;
no merge, installation, release, or external message delivery.

Base: cfb7f03b88f1126591f92abfd429fac7e52793cb, verified equal on GitHub/GitLab main.
Open-MR check: !82 adds other discipline skills; !156 changes UAC in-flight checks;
neither implements this job. Preserve both.

Decision: `new` receiving owner `engos-design-freshness-sweep`; `harvest` for
three existing caller gates. Existing source fidelity/revision clauses do not
require full discussions or a cross-repository fourteen-day merge sweep.
Use the finite shared-resource registry for a single procedure/checker owner,
physically bundled in all four packages, with no sibling installation dependency.

Acceptance:
- Explicit live read workflow: full recursive linked-ticket discussions, full MR
  discussions (including resolved/outdated/system notes), two weeks of owners'
  merges across every involved repo; pagination to exhaustion, no status shortcut.
- Owner/repository provenance, stable UTC window, full-body evidence and exact
  source links; failures remain incomplete and hold dependent handoff only.
- Required What changed since this was designed / simpler path that exists today
  section reconciles old assumptions, lifted blockers and existing APIs.
- No technical blocked verdict without attributable current owner's exact quote;
  lack of access or silence is incomplete. No unsolicited owner messages.
- A stdlib executable checks normalized tool evidence, pagination/graph coverage,
  window and quote binding and renders the section. It does not fetch remotely,
  authenticate an owner, prove model reading or judge semantic equivalence.
- Re-run on resume/material drift and before dependent handoff. Shaping keeps
  framing solution-free and the existing gate owner; no source-gate bypass.
- Focused executable failure/success tests; packaged detached-consumer checks;
  UAC plan/judge/independent hash-bound review/apply; generated surfaces and docs.

Verification: focused tests first; shared resource/UAC/public docs contracts;
serial generation/strict surface checks; exact candidate hosted checks on both
hosts. Evidence of admission is not measured behavioral improvement; retain
behavioral_pending. Required reviewer is independent of the author.

Admission findings and repairs:
- Independent review required distinct discussion endpoint/thread receipts, ticket
  description bindings and rejection of empty ordinary comment bodies.
- Confirmation currency is source-backed; fourteen days limits merges, not quotes.
- Human-led shaping retains complete attributable source-tool pages and receipts
  with identical coverage requirements; unsupported summaries remain incomplete.
- Initial UAC strict validation hit unhealthy official-doc caches; authorized
  refresh restored all eight sources.
- Curated neighbor_handoff references require rebinding reviewed passages after
  SSOT edits. Retain their meaning and keep the validation gate active.
- Validation dependencies absent locally (docx/Pillow) are supplied in a task-local
  test venv; no global Python or installed skill changes.
Prevention is implemented in the shared procedure/checker, caller gates and
tests/test_design_freshness.py. Comparative agent efficacy remains unmeasured.

UAC sequencing note: existing self-bound neighbor_handoff references validate
against current disk bytes in preview, then become stale after apply writes a
new SSOT. The scoped recovery uses UAC's preserved partial write, rebinds reviewed
passages in canonical metadata, and reruns apply/validation. No UAC implementation
or validation rule is changed; a general transactional tool repair is not in scope.

Local test coverage: the initial full pytest run was interrupted after observing
a canonical-loader test failure. The planner/shaping canonical test fixtures now
use registry-aware assembly while retaining all original schema/frame exclusions;
freshness closure assertions were added. Final local verification runs relevant
CI-path modules, with full hosted CI checked on the candidate. No full local-suite
pass is claimed.

Current delivery checkpoint:
- All four UAC applies: applied, structural_ready, behavioral_pending.
- Independent authored review: zero findings; 46 freshness cases plus routing and
  three edited canonical-loader/frame-boundary tests independently passed.
- Relevant CI-path run: 570 passed, then process-only packaging failure because
  git ls-files omitted new unstaged files. Complete reviewed patch is now staged;
  packaging failure and remaining modules are being rerun.
- Upstream advanced to 66036267b7cf8d585ebcaab07097ad6e2742c278 with two unrelated
  accepted skills; both GitLab main pipelines passed. GitHub mirror was safely
  fast-forwarded to that accepted tip; main parity is restored. No freshness merge.
- Next: finish local gates, commit checkpoint, merge current upstream into this
  task branch, regenerate counts/catalogs (46 total), renew affected checks/review,
  commit integration, push identical candidate to both hosts, open PR/MR and
  verify hosted checks. Stop at open review; do not merge/install/release.

Pre-integration verification complete:
- Relevant CI-path selection completed across invocations: 570 passing cases, then
  55 after staging the new tracked inventory, plus four remaining packaging cases.
- Compile/check, static calibration, CLI smoke, strict validation, installer and
  historical catalog checks, intent guide: passed. Missing Gemini binary is the
  existing non-fatal startup observation; no native discovery claim.
- Independent final review approved both test fixes; explicit frame exclusion passed.
