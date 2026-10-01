# v1.16.3 documentation review inputs

Review the exact current docs and release notes against the already merged source
contracts at `64267f333fe457c1a3e07d23712725718a63a6e0`. The writer is `/root/writer`;
the same separate `/root/reviewer` reviews without editing. Publication and
installation remain controller-owned gates after independent zero-open review.

Changed public paths:

- `CHANGELOG.md`: fold both Unreleased review-loop groups into the existing v1.16.3
  release dated 2026-10-01; preserve all prepared shaping-recovery bullets. VERSION
  remains v1.16.3; package guard forbids a nonempty Unreleased section.
- `README.md`: explain released/installed activation and one usable architecture ask;
  link to the canonical examples and preservation guide.
- `docs/GETTING-STARTED.md`: one feature-status ask with preserved scope confirmation,
  distinct source review and the repair/stalemate cycle.
- `docs/EXAMPLES.md`: practical asks/expected work for all thirteen skills, including
  architecture, with route restrictions and preserved permissions.
- `docs/RELEASE-PACKAGING.md`: generic verified-previous-release selection; label the
  v1.16.3→v1.16.2 comparator as one example; retain baseline through rebuilds.
- `docs/INSTALL-PROFILES.md`: exact saved-selection preview, ownership-aware partial
  activation, runtime version versus individual package readback, preservation and
  rollback. Correct current capability count29→32 from manifest/source inspection.

Stable release notes: `reports/review-loop-release-v1163/release-notes.md`.
Original/candidate public-doc hashes are in `doc-review-inputs.json`. No SSOT,
resource, runtime or installer implementation is edited by this writer slice.

Review sources and invariants:

- All thirteen canonical skills under `ssot/`, especially their Recommendation Roles
  / Recommendation Artifact Review sections, source checks and route restrictions.
- `docs/GETTING-STARTED.md` and `docs/EXAMPLES.md` existing domain asks/outputs; no domain
  or permission change is introduced by the examples.
- `.kiro/steering/docs-governance.md`: one canonical human doc home, installed-first
  onboarding, concrete asks plus expected outputs and release-time discoverability.
- `scripts/package-surfaces.sh`: VERSION/changelog matching and Unreleased refusal.
- Installer/updater help inspected: `bash scripts/install-local.sh --help` and
  `python3 scripts/update-core-prompts.py --help` support the documented flags.
- `scripts/core_install/` selection/preservation semantics and existing installation
  guide; default invocation retains an existing saved selection, while repair/new
  profile/extra slugs have different selection effects.
- Local `git show v1.16.2:VERSION` returned v1.16.2. Controller verified provider tag
  object/commit parity and latest published comparator; broad old-tag conflicts were
  left untouched.
- Current manifest contains32 SSOT capabilities and160 generated skill entrypoints.

Evidence limits: practical examples describe source contracts and hypothetical
repair cases. They prove no measured model benefit or formal promotion. This doc
review does not itself prove release publication, downloaded bytes or home acceptance.
The preliminary saved181-selection/444-write/52-preservation install plan is not an
applied installation and is intentionally not baked into public guarantees.

Ask the writer for repairs through findings with severity, exact location, problem,
concrete repair, source evidence and open status. Preserve the same writer/reviewer
across rounds. No self-score or generic completion checklist substitutes for the
reviewer's zero-open finding list.
