# engos-quality-shaping code review

Actual independent review of the initial implementation. Author test passes did not waive these findings. Wording retained; Markdown trailing whitespace normalized.

Readiness: blocked before canonical packaging. I found one P1 and six P2 defects. The 100 existing focused tests passed, but the additional probes below reproduced failures.

Commit under review: the explicitly named untracked files in `/private/tmp/engos-full-shaping-design`, branch `AI/engos-full-shaping-design`, HEAD `59488c0401e2d887f02a3f06af65387cd6f22f7b`. All nine listed input hashes remained unchanged throughout review.

1. **[P1] Ordinary input hashes can mask changed policy bindings.**
   [shaping_run.py:383](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-quality-shaping-gate/scripts/shaping_run.py:383) overwrites pinned policy bindings with work-order input hashes. Repro: initialize with minimum overall 4, change the policy file to require 5, then include that file in `inputs`. A score-4 G3 receipt is accepted; status reports `content_ready: true` and no drift. Changing an enumerated rubric reference also bypasses detection.
   Fix: check policy, current-order and predecessor bindings independently, rejecting conflicting hashes for overlapping paths. Apply the same correction to `status`. Add both policy-file and rubric-reference regression tests.

2. **[P2] Rendering writes through a symlinked output parent before rejecting it.**
   [artifact_export.py:169](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-delivery-artifact-embed/scripts/artifact_export.py:169) creates the output directory and invokes the renderer before `write_new` checks the manifest path. With `link → outside` and output `link/new`, my probe wrote all three PNGs under `outside/new`, then returned exit 2 for the symlink.
   Fix: validate the entire output path before creating directories or invoking the renderer, with appropriate protection against component replacement. Test that rejection causes zero renderer calls and zero destination writes.

3. **[P2] DOCX can overwrite an output created during conversion.**
   [artifact_export.py:291](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-delivery-artifact-embed/scripts/artifact_export.py:291) saves by filename after an existence check much earlier. Injecting a user file immediately before `save` resulted in its replacement and exit 0. A late symlink presents the same check/use problem.
   Fix: serialize to a buffer or private temporary file, then publish using an exclusive, non-following, no-clobber operation. Test concurrent destination creation and destination substitution.

4. **[P2] DOCX embeds image bytes other than those it verified.**
   [artifact_export.py:279](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-delivery-artifact-embed/scripts/artifact_export.py:279) reopens image paths after their hashes were checked at lines 196–202. Changing `component.png` between verification and document construction produced exit 0 and a DOCX containing the changed, unverified image.
   Fix: retain verified image bytes and use those same buffers for dimensions and embedding. Add a deterministic mutation-between-check-and-use test.

5. **[P2] Renderer execution has no timeout or bounded diagnostic capture.**
   [artifact_export.py:176](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-delivery-artifact-embed/scripts/artifact_export.py:176) uses `subprocess.run(..., capture_output=True)` without a timeout. A sleeping renderer required my external watchdog to terminate the process group; the helper emitted no structured result. Verbose renderer output is also accumulated without a bound.
   Fix: impose a finite execution limit, terminate renderer descendants, bound diagnostics, and return the documented operational error while retaining diagnostic partial output without a success manifest. Test timeout, nonzero exit and partial output.

6. **[P2] Delivery-only dependency drift revokes content readiness.**
   [shaping_run.py:349](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-quality-shaping-gate/scripts/shaping_run.py:349) calculates content readiness using the latest accepted snapshot’s inputs, including G4-only dependencies. Repro: enumerate HTML readback as a G4 input, accept G4, then change that readback. `content_ready` becomes false although every G3 source remains unchanged.
   Fix: calculate content readiness from G3 dependencies and delivery readiness from G4 dependencies plus delivery records. Test this with readback explicitly included in G4 `inputs`.

7. **[P2] DOCX silently changes fenced-code content.**
   [artifact_export.py:277](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-delivery-artifact-embed/scripts/artifact_export.py:277) sends code blocks through paragraph formatting. A fenced shell example containing `> output.txt` and ``echo `whoami` `` became `output.txt` and `echo whoami`, changing its meaning.
   Fix: handle code blocks separately, preserving literal text without quote, link or inline-format transformations. Add DOCX text-readback assertions for these cases.

Verification: I ran the two requested test modules locally with bytecode/cache writes disabled: **100 passed in 12.80 seconds** on Python 3.14.7. Additional temporary diagnostics used synthetic mechanical receipts, a controlled renderer stub, and the bundled DOCX/Pillow runtime. Reproductions remain in [the temporary review directory](/private/tmp/shaping-independent-review-e1fm1G).

The reviewed acceptance path keeps artifacts, questions and decisions within one committed snapshot. Existing checks exercised replay, interrupted pointer commits, corruption, generation/predecessor rejection, score arithmetic and representation-specific delivery evidence. I found no additional blocker in standalone semantics within this scope. Runtime TOCTOU assessment respects its explicit requirement to quiesce source/candidate writers. File reads and retained history have no hard quotas; large-run exhaustion was not tested.

Scope and message assessment: the reviewed additions fit the intended `feat: add guided Shape Up workflow with versioned stage checks and portable artifacts` title. This is a source review only—not approval of the broader commit, canonical packaging, hosted CI, real Mermaid rendering, visual quality or human-pilot behavior. No repository files were modified, staged or committed; no delegation or cloud operations occurred.

SHA-256 inputs, unchanged at final verification:

```text
shaping_run.py
685e3a40e22d820ef9e5e7d89cf0df6529af938be166625674b2be4a2050b3e8
schemas/policy.example.json
b03ae35b04ea16cbc370122c7c7c5dfddecb38764c5e0b3dd3655567afd44a9f
schemas/runtime.schema.json
615ff641fc2ffc89d6bed6db0b244e138ac1ab3f39feb06ae3ac6dcf3317735e
references/runtime.md
7d38eab132354b807258a5c1fa0e891fe09752c8b6090926adeab30f5f45e89c
artifact_export.py
9f80917e97159c380b8b92b0d7c7a0cac6ae5e93697a4dd1f969afd5daa4813e
references/export.md
32094f3c4eae9c8afeb4bb443fcc7e6219ae98672a8435359d86b2e33f9231d4
tests/test_shaping_runtime.py
724760c488c32a2ac1fe71c88125f53311af74d93223685fe46bc2c694dc3c3b
tests/test_shaping_export.py
00c7c159b242875323c03d0593abff21a7399536e1ff13f91903cd9d64ebff43
engos-design-shaping-operating-plan.md
1bfb7f01766dbaf8b7c134d3515bd2cf6ebe7162c43cee666e58dd59942b5766
```
