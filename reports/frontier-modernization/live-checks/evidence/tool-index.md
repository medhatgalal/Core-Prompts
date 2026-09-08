# Observable host evidence index

These are references to actual tool events in this demonstration task, not a claim that file hashes prove comprehension. Loader stdout files are captured from actual subprocess output. Independent review records cite their own delivery calls.

| Event | Actual tool result reference | Evidence |
| --- | --- | --- |
| Runtime/source preflight | exec_command chunk dff596 | cwd/root/branch/HEAD/Python; dirty output was truncated so no exhaustive dirty inventory claim |
| Initial combined read | exec_command chunk 335bc4 | Truncated source; not accepted as complete delivery |
| Complete source + map + /grade recovery | exec_command chunk fa5884 | Full SSOT and map, shared review and grade payload |
| Frozen manifest and stdout capture | exec_command chunk 1eb109 | Python 3.14.7, skill v5.0, HEAD and exact resource hashes |
| Complete /ult, /full, /catchup delivery | exec_command chunk d9f4b3 | Full selected shared/module payloads before dependent work |
| Baseline independent grading dispatch | collaboration.spawn_agent task /root/verify_live_skill_behaviors/grade_harbor | Fresh context, no scores or round labels |
| Review-only marker precheck and frozen full contract | exec_command chunk ee1fd4 | exists=false and lexists=false, no marker mutation |

The exposed collaboration interface reports canonical task names, not opaque host outcome UUIDs. Those task names and each tool chunk ID are the actual identifiers available here. Do not invent missing IDs. Exact model snapshot is not exposed by this interface; reviewers inherit the configured model without override.

| Later event | Actual tool result reference | Evidence |
| --- | --- | --- |
| Real first candidate creation | exec_command chunk a72954 | C1 and neutral meadow copies exist separately from baseline |
| First fresh pair review | grade_meadow; delivery c76000 | 9.8 versus 2.6, independent improvement verdict |
| Real second candidate creation | exec_command chunk d4fec9 | C2 and neutral cedar copies, new fixed output strategy |
| Fresh second pair review | grade_cedar; delivery e7dc67; thread 01a0823c-a467-7173-938b-6c5cbead3781 | 9.8 tie and retain meadow verdict |
| Rebuilt helper capture and comparison | exec_command chunk 97cc5e | Only descriptor/helper changed; route stdout identical; combined display truncated |
| Rebuilt /full delivery recovery | exec_command chunk 420473 | Complete standalone final helper payload |
| Targeted SIMPLE worked-example repair | exec_command chunk b428a7 | Preserves draft and revised artifact separately |
| Grade finalization | exec_command chunk f8833b | Exactly two real trials and C1 retained, no invented regression |

Capacity failures: actual collaboration followup/spawn calls returned `agent thread limit reached`. The same authorized independent roles were later successfully dispatched; no fallback self-grading or simulated role was used.
