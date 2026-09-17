# Configuration deployment — Framed

Source identity/raw statement: intake.md, `input.md:6-7`. G0 passed before this artifact. All decisions are hypothetical.

**Problem / why now / people.** The customer re-enters cost settings after each deployment; target administrators need their local settings preserved (`input.md:6-13`).

**Outcome / business win.** Carry currency and activity-cost definitions forward without repeated entry, inadvertent target overwrite or older-package regression. Benefit is reduced manual work, not measured savings (`input.md:6-13`).

**Appetite / walk-away.** One week, two engineers; stop if target override protection cannot hold (`input.md:9-12`).

**In.** Currency/activity definitions, old-package compatibility and protection of target edits, including edits made during deployment. Absent or explicitly empty supplied costs preserve target costs; nonempty valid input may apply only after authorization, compatibility and override checks (`input.md:6-12`, `round-two-clarifications.md:38-42`).

**Out.** Deletion, unrelated configuration, results/customer transactions, new permission roles/credentials/transport, full reload and historical recomputation (`input.md:10-12`, `input.md:23`, `input.md:28-33`, `round-two-clarifications.md:41`). No expanded product feature is committed for Later.

**Source constraints, not selected mechanisms.** Target admin retains explicit force authority; unrelated target settings survive. Zero and positive activity costs are valid, negative costs and unsupported currencies are invalid. Analysis refreshes on its normal schedule (`input.md:11-12`, `round-two-clarifications.md:47-49`). C4 limits the supported package to 100 processes, 200 activity entries each and 4,000 other configuration records; larger packages must be rejected intact. Valid currency-only input preserves target activities; absent costs preserve both; an empty activity list preserves activities; failed source reads abort export (`round-two-clarifications.md:51-62`).

| Question | Research must establish |
| --- | --- |
| C-Q1 | What prevents an intervening target edit from being silently overwritten at commit, including around force decisions? |
| C-Q2 | How do absent, explicit empty and nonempty definitions differ, and how are they associated with a process? |
| C-Q3 | Which values are valid and what happens to the whole package on conflict or validation failure? |
| C-Q4 | When does analysis see committed settings and which security responsibilities remain elsewhere? |
| C-Q5 | Does C4 now bound the complete package below the supplied transaction capacity, and what rejection obligation is new rather than existing behavior? |

No selected topology, API, algorithm or implementation steps appear in this frame. C2/C3/C4 are supplied outcome/contract constraints.
