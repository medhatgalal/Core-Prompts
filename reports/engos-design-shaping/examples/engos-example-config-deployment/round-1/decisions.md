# Configuration deployment — decisions

These are hypothetical supplied decisions, not invented approvals or production commitments. Source identity: `engos-example-config-deployment/input.md` (`input.md:3-4`).

| ID | Decision / constraint | State and provenance | Reason / consequence |
| --- | --- | --- | --- |
| C1 | One week, two engineers; stop if target overrides cannot be protected | Accepted fixture decision, `input.md:9-12` | Hard investment and walk-away boundary |
| C1-S | Include currency/activity definitions; exclude results, unrelated configuration, new roles | Accepted fixture scope, `input.md:10-12` | Bound work to the stated problem |
| C1-F | Preserve local edits by default; explicit force decision belongs to target admin | Accepted fixture authority, `input.md:11-12` | Author cannot authorize overwrite |
| C1-O | Older packages must work; omitted cost section leaves target unchanged | Supplied requirement/premise, `input.md:6-7`, `input.md:24-25` | Absence cannot delete configuration |
| C1-A | No reload or historical recomputation | Supplied constraint, `input.md:28-29` | Limit effects to ordinary future analysis |
| C1-T | No new transport/credentials; existing authorization applies | Supplied constraint, `input.md:32-33` | No new security authority |
| C1-E | Local HTML is eventual reference; no live mutation or integration test | Supplied teaching boundary, `input.md:35-36` | Current assignment stops at source draft |

No additional human decision is required for G1. Technical questions C-Q1 through C-Q6 remain for Research. Any later design choices are author proposals, not amendments to C1.
