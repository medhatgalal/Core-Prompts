# v1.16.3 — 2026-10-01

Substantial recommendation artifacts now receive independent source-based acceptance.
A coordinator dispatches and counts; one writer owns the artifact and its repairs;
a different reviewer checks the sources and writes findings. Revisions resume the
same writer and reviewer until the reviewer reports zero open findings.

Findings carry severity, location, the problem, a concrete repair and source evidence.
The writer responds `addressed`, technically justified `wontfix`, or `needs-user-input`.
The reviewer replaces the current finding list, dropping fixed defects and keeping
bad repairs or new defects open. There is no artifact-review round cap; a reopened
technical refusal goes to the user for a final ruling. Architecture's author-filled
scorecard is removed as the acceptance gate.

The change covers architecture, code-health, feature-status, OpEx incident reports,
weekly intelligence, demo scripts, HTML presentations, conflict recommendations,
goal packets, authored test plans, executed documentation rewrites, converged
proposals and Loopy Craft output. Existing domain checks and permissions remain:

- Documentation inspection stays advisory unless execution was requested.
- Test-design acceptance establishes neither test execution nor measured coverage.
- Demo review does not run the script or read credentials.
- Code-health reports remain inline and target-read-only.
- Goal packet lint, sealing, trust and execution limits remain required.
- Loopy uses this only for substantial Craft output; its original package identity,
  compact output, execution limits and separate run/publication authority remain.
- Narrow help, lookup and conversion routes retain their existing behavior.
  Existing host review identity, path and capped-return protocols remain unchanged.

[Practical examples for all thirteen routes](https://github.com/medhatgalal/Core-Prompts/blob/v1.16.3/docs/EXAMPLES.md#review-an-authored-artifact)
show a real ask, expected artifact and preserved boundary for each skill.

This release also retains the prepared shaping evidence/recovery corrections:
current policy bindings govern floor-only review classification; valid older
history remains preserved; unverifiable history requires recovery; and Research
authors check source contradictions, scoped occurrences, citation referents and
material callee claims before handoff. Existing twelve-score thresholds remain.
Policy migration and source-bound recovery have explicit user guidance.

Install the released v1.16.3 package for your selected provider to activate these
instructions. Shared updater version and individual skill content are separate:
a customized or unowned package preserved by the installer retains its prior
behavior. Preview the exact saved selection, keep custom and third-party packages,
and verify the requested skill's installed files after apply. An unreceipted
third-party Loopy package is not adopted automatically. See
[activation and preservation](https://github.com/medhatgalal/Core-Prompts/blob/v1.16.3/docs/INSTALL-PROFILES.md#activate-a-released-skill-update).

The release comparison is bound to the preceding published v1.16.2 tag. Publication,
downloaded package identity and home installation have separate verification
receipts. Source-contract review and deterministic checks do not establish measured
model improvement, savings or formal behavioral promotion; no new PromotionVerdict
is claimed by these documentation or review-loop changes.
