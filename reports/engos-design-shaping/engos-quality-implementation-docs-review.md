# engos-quality-shaping documentation review

Actual independent initial review. Wording retained; Markdown trailing whitespace normalized.

Found three actionable documentation defects. Documentation readiness remains pending these fixes.

1. **[P2] The release archive omits the new runbook.** [README.md:34](/private/tmp/engos-full-shaping-design/README.md:34), getting-started and examples link to `docs/engos-design-shaping.md`, but the explicit [packaging list](/private/tmp/engos-full-shaping-design/scripts/package-surfaces.sh:112) excludes it. Archive users lose the instructions for inputs, resume and pilot limitations. Smallest fix: add the runbook to `INCLUDE_PATHS` and the package-membership check.

2. **[P2] The evidence link works only in this worktree.** [docs/engos-design-shaping.md:10](/private/tmp/engos-full-shaping-design/docs/engos-design-shaping.md:10) directs readers to a report that is untracked, ignored by `.gitignore:11`, and excluded from packaging. It therefore fails in a fresh checkout as well as a release archive—even after fixing finding 1. Smallest fix: put a concise, public-safe validation-status summary in the tracked runbook; make detailed evidence an optional durable link. Explicitly distinguish simulated preflight from the pending real-human pilot and saved Google Docs verification.

3. **[P2] Runtime examples name the wrong working directory.** [runtime.md:73](/private/tmp/engos-full-shaping-design/sources/capability-resources/engos-quality-shaping-gate/references/runtime.md:73) says to run `scripts/shaping_run.py` from the capability root. From the generated skill root, that command fails with “No such file”; `resources/scripts/shaping_run.py --help` succeeds. Smallest fix: specify the resolved **resource root (`<skill>/resources`)** as the working directory. Make the correction canonically and regenerate during implementation.

Otherwise, the inspected documentation is consistent with the source contracts on first-use inputs, framing, human decisions, handoffs, resumable holds, Markdown ownership, derived exports, and separate content/delivery acceptance. Standalone pitch review and artifact placement retain their scoped behavior. Export help matches its documented interface. These are documentation findings, not behavioral proof.

This remains a source candidate: real participants, private Docs upload approval, GitLab access and hosted CI remain pending; the running main regression was not assessed. No edits, regeneration, staging, network, subagents or costly tests were performed. Recheck the corrected links and commands before merge, and archive contents before release.

Review fingerprints:

- HEAD: `59488c0401e2d887f02a3f06af65387cd6f22f7b`
- Six-file staged docs diff SHA-256, unchanged across review: `1055346c192c493499f6993694cca6105be3f81b4b87f787aacd09f290875cec`
- Entire staged binary-diff fingerprint—not a whole-change approval: `dc4b3d0384d802579527e23fd52f43f79877ef45548d448a0e05fb3d11c558da`
