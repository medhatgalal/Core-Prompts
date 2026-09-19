# Configuration deployment — decision provenance

| ID | Decision / state | Source | Effect versus round 1 |
| --- | --- | --- | --- |
| C1 | Accepted fixture appetite: one week, two engineers; stop if override protection fails | `input.md:9-12` | Unchanged, no real funding approval |
| C1-S | Currency/activity definitions In; results/unrelated config/new roles Out; target admin owns force | `input.md:10-12` | Unchanged |
| C2 | Accepted fixture semantics: absent and explicit empty both preserve; valid nonempty requires checks; deletion Out; intervening target edit must conflict | `round-two-clarifications.md:38-42` | Supersedes round-1 author proposal rejecting an empty section; sharpens race requirement |
| C3 | Existing transaction compares revision at commit and rolls back all package changes on conflict | `round-two-clarifications.md:44-46` | Resolves timing ambiguity with new fixture evidence, not a race-test result |
| C3-V | Zero/positive costs valid; negative/unsupported currency invalid; unrelated settings intact; next normal analysis run | `round-two-clarifications.md:47-49` | Supplies previously missing validity premises |
| C4-capacity | Added fixture decision: supported package ≤100 processes, ≤200 activity entries/process, ≤4,000 other records; proposed one-currency-record/process representation gives ≤24,100 records; reject larger packages intact | `round-two-clarifications.md:51-56` | Newly resolves C-CAPACITY; never attributed to original input or an executed test |
| C4-states | Added fixture semantics: valid currency-only updates currency, empty activities preserve activities, absence preserves both, failed read aborts export, malformed data fails validation | `round-two-clarifications.md:57-62` | Resolves distinct C-EMPTY cases without nonempty minimum |
| C-B | No new credentials/transport, reload/history recompute or live deployment/testing | `input.md:28-36` | Unchanged authority boundary |

Withdraw round-1 unconditional fit/spare-capacity conclusion. Original input establishes 100 processes, at most 200 activity entries each and support for 25,000 configuration records (`input.md:30-31`), but not other-record occupancy. C4 now adds the missing bound and accepts the proposed currency representation: 20,000 activity + 100 currency + 4,000 other = 24,100, leaving 900 below stated capacity (`round-two-clarifications.md:51-56`). Intact rejection is a new scenario obligation, not an observed existing overflow policy. It did not retroactively justify round-1 G2.

Human investment decisions required for G1 are supplied. Research questions remain in framed.md. Any later contract proposal must be labeled and must not waive C2/C3/C4.
