# Writer repair responses

## Round 5

- Finding: `R5-01`.
- Status: `addressed`.
- What changed: before-after wording now states exact original operating-body containment excluding package frontmatter, matching the preservation test. It separately states that the full immutable source file and pinned companions remain unchanged. The ledger uses the same precise operating-body scope. No candidate, snapshot or companion file was changed for this wording repair.
- Additional lifecycle clarification: before-after.md is a comparison of baseline 99c380b and independently reviewed text; apply, validation and mainline delivery use separate PR/MR/check receipts. It claims no measured improvement.

## Historical OpEx binding test repair

- Status: `addressed` (controller-diagnosed focused check failure; independent repair review pending).
- What changed: the historical briefing receipt's source binding now verifies an exact historical source fixture, recovered from receipt-introducing commit a5458d6ce798eb8f881591c97ab82d9b43637e94 and checked against its original SHA-256. The test reads the fixture/provenance directly, requiring no Git command or additional runner tool.
- What stays: historical receipt bytes, renderer identity, old 45-pass result, formal behavioral_pending status and live-Doc/PDF limitations; unchanged exporter/reference/schema resources are still checked against their recorded hashes.
- Evidence boundary: source identity preservation only. No old outcome was rehashed as current evidence, no new semantic/model behavior was inferred, and no product/runtime/release files changed.
