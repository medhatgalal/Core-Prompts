# Choose a boundary from the risk

Start from a concrete user/system consequence, the changed boundary and existing
evidence. Prioritize loss/corruption, invalid access, duplicate effects, failed
recovery or an unavailable critical journey when relevant. Do not infer those risks
merely because a function name sounds important.

| Needed observation | Useful starting level | What it cannot establish by itself |
| --- | --- | --- |
| Pure calculation, validation or local state transition | Unit test with controlled inputs | Real serialization, database or network behavior |
| Collaborators agree on wire/schema assumptions | Consumer/provider or adapter contract test | Correct persistence and business side effects |
| A transaction, retry or adapter produces the intended real effect | Integration test across that boundary | The complete user journey through all interfaces |
| A user completes a critical journey | E2E with semantic outcomes and isolated data | Every branch or all operational failure modes |
| A capacity, latency, accessibility or security requirement | Targeted specialist test design | A universal pass from generic assertions |

These are choices, not mandatory layers or test-count ratios. A one-line pure
function need not acquire a test strategy document; an interface change may need
integration evidence even when its unit coverage is complete. Explain when a mock
removes the very interaction at risk. Do not demand a live external service when a
local real adapter or disposable database can establish the same bounded claim.

Prefer adding the missing observation to an existing well-placed test over creating
another equivalent scenario. Recommend consolidation only after mapping which
distinct behavior and diagnostic signal each existing test protects. Keep removal
advisory unless explicitly within the edit scope.

Practice basis: [Google testing strategy](https://testing.googleblog.com/2021/06/how-much-testing-is-enough.html)
and [Pact contract/functional distinction](https://docs.pact.io/consumer/contract_tests_not_functional_tests),
reviewed 2026-09-10. They motivate the distinctions; repository facts decide the level.
