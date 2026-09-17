# Unified chat — Framed

G0 passed. Source identity/raw statement: intake.md and `input.md:6`. Hypothetical exercise, not an implementation choice.

**Problem / why now.** Developers face separate planning/building conversations and lose navigation context on reload (`input.md:14-15`). U1 calls for continuity; no separate deadline or measured loss is supplied (`input.md:8-11`).

**Desired outcome / business win.** One persistent development conversation connects planning and building, survives reload and provides inline preview across all supported authentication modes. Less repeated orientation is the intended benefit, not a measured gain (`input.md:8-9`, `round-two-clarifications.md:66-67`).

**Appetite / walk-away.** One month, two engineers; walk away or reshape if the usable core cannot fit. U2 explicitly forbids extending the month (`input.md:8-10`, `round-two-clarifications.md:68`).

**In.** Persistence, continuity, reload/navigation and all-mode inline preview. **Out.** Cross-app work, an application-level planning product and broad performance hardening. **Later.** Streaming subagent activity; this is not permission to remove persistence/preview or to assume the core independent of unfinished work (`input.md:10-11`, `input.md:25-26`, `round-two-clarifications.md:66-69`).

**Authority.** ProductOwner selects outcomes; Engineering researches feasibility. Component reuse remains a candidate, not evidence of compatibility (`input.md:16`, `round-two-clarifications.md:69`).

| Question | Evidence needed |
| --- | --- |
| U-Q1 | Persistence API/session specification and recorded reload/navigation continuity through planning/building |
| U-Q2 | Current preview/auth specification, full supported-mode inventory and attributable positive/negative integration results |
| U-Q3 | Whether the previous prototype label has acquired actual supporting records |
| U-Q4 | Whether the retained core depends on unfinished sub-agent functionality despite streaming activity moving Later |

U2 resolves whether preview/all-mode support is core. These remaining questions concern feasibility, not permission to invent a design. No topology, endpoint, streaming replacement or implementation is selected.
