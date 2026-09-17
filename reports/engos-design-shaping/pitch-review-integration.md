# engos-audit-pitch-review integration design

Status: proposed change, not applied to canonical SSOT. This overlay is mandatory
when selected by this design packet's candidate-map.json; it governs the experiment.

Load the base canonical skill, then this overlay and engos-quality-shaping-gate
with both resources. For a full shaping run, this overlay's separate G3/G4,
12-dimension rubric and hard-failure precedence supersede the base skill's
8-dimension ten-point score and combined shaped/bet-ready terminology. G3 review
assesses approved source content and local renders only; saved-target placement
is assessed at G4 after the adapter runs. Other base modes retain their behavior.

The existing skill retains review, score, improve, compare and export. A vague
brief routes to engos-design-shaping; artifact formatting does not pretend to
perform the earlier stages. When reviewing a full shaping folder, load
engos-quality-shaping-gate and validate predecessor receipts and G3/G4 using
the actual artifacts. Report both the team's and pitch-specific scorecards.

The author uses audit mode and cannot self-certify independent review. A real
independent reviewer rechecks citations, reports weakest dimensions, top fixes
and betting-table questions. If unavailable, mark review_pending. No native
agent configuration is required merely to provide a second reviewer.

Replace the earlier appended artifact-only gate with a pointer to the single
gate owner. Reconcile historical 'diagram or list' allowances, four-week product
defaults and 'resolved rabbit hole' language with the new protocol: the current
human appetite is authoritative; risks require evidence and mitigations; critical
open questions block; artifact requirements follow this run's full-shaping contract.
For a legacy pitch review without a full folder, assess what is present and name
unassessed upstream stages without fabricating historic gate receipts.

Blast radius: any host or independent worker invoking this skill gets the revised
review boundary after a future canonical apply. The proposed new gate is also
used by the conductor. Existing diagram/embed names remain stable. Upstream
pm-dev-tools files and installed bundles are not edited in this design exercise.
