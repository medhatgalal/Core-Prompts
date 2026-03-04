# Codebase Concerns

Analysis date: 2026-03-04

## Critical

1. TLS certificate verification is explicitly disabled during schema source fetch.
Evidence: `scripts/sync-surface-specs.py:50` uses `ssl._create_unverified_context()` with `urlopen`.
Impact: A MITM or compromised network path can poison cached schema metadata and downstream validation trust.
Practical fix: Use default TLS verification, add explicit CA handling only when needed, and fail closed in CI.

2. Schema sync can duplicate manifest entries on unexpected exceptions.
Evidence: `scripts/sync-surface-specs.py:156-164` appends the same error payload twice (`entries.append(...)` then `entries.append(entries[-1])`).
Impact: `source_count` and entry lists become inconsistent/noisy, making cache health diagnostics unreliable.
Practical fix: Remove the second append and add a regression test for one-entry-per-source behavior.

## High

3. Validation does not verify generated artifact content matches SSOT content.
Evidence: `scripts/validate-surfaces.py:162-173` checks format/required fields only; no comparison against `ssot/*.md` bodies/descriptions.
Impact: Generated surfaces can drift semantically from SSOT while still passing CI.
Practical fix: Deterministic rebuild + diff check in CI (or content-hash comparison in `.meta/manifest.json`).

4. CI validates without rebuilding, so stale generated files can pass.
Evidence: `.github/workflows/cli-surfaces-validate.yml:18-23` runs sync/smoke/validate but never `python3 scripts/build-surfaces.py`.
Impact: PRs that change `ssot/*` may pass even if generated surfaces are stale but structurally valid.
Practical fix: Add build step before validation and fail if `git diff --exit-code` after generation.

5. Frontmatter parsing is duplicated and ad-hoc across multiple scripts.
Evidence:
- `scripts/build-surfaces.py:45-73`
- `scripts/validate-surfaces.py:28-42`
- `scripts/smoke-clis.py:37-55`
- `.claude/get-shit-done/bin/lib/frontmatter.cjs:11-223`
All parse via string splitting/regex instead of a YAML parser.
Impact: Edge-case YAML (quoted colons, multiline blocks, nested structures) can be misread differently by different tools.
Practical fix: Centralize parsing with real YAML libs (Python + JS equivalents) and shared schema tests.

6. Deployment defaults to writing directly into the user home with forced overwrite semantics.
Evidence:
- `scripts/deploy-surfaces.sh:23` default target is `$HOME`
- `scripts/deploy-surfaces.sh:201` removes destination symlink via `rm -f`
- `scripts/deploy-surfaces.sh:205` overwrites via `cp -f`
Impact: Accidental runs can overwrite active local CLI setup with no backup/rollback.
Practical fix: Require explicit `--target` for non-dry-run, add confirmation guard, and create timestamped backups.

7. Codex config mutation is text-marker based, not TOML-aware.
Evidence: `scripts/deploy-surfaces.sh:253-307` rewrites `~/.codex/config.toml` by marker slicing instead of parsing TOML.
Impact: Existing config structure/comments/order can be corrupted; concurrent edits are race-prone.
Practical fix: Parse/merge TOML atomically and write through a temp file + rename.

## Medium

8. Schema cache stores only checksum text files, not source payload snapshots.
Evidence: `scripts/sync-surface-specs.py:140` writes only checksum to cache file; manifest keeps short snippet/metadata.
Impact: Hard to audit what changed in upstream docs when validation behavior shifts.
Practical fix: Store full normalized payload (or structured extracts) with size cap and retention policy.

9. Smoke checks are intentionally non-blocking for missing CLIs in default CI path.
Evidence:
- `.meta/surface-rules.json:15-47` marks all tools `"required": false`
- `.github/workflows/cli-surfaces-validate.yml:21` runs `scripts/smoke-clis.py` without `--strict`
- `scripts/smoke-clis.py:106-113` downgrades missing CLIs to warnings.
Impact: Toolchain regressions can go unnoticed until manual verification.
Practical fix: Enforce strict smoke on a matrix that installs each vendor CLI (or add per-surface contract tests).

10. Broad tool permissions and implicit shell hooks are generated into Kiro agents.
Evidence: `scripts/build-surfaces.py:137-145` emits `hooks.agentSpawn.command` and `tools: ['*']` for every Kiro agent.
Impact: Expands runtime capability surface; increases risk if prompts or agent context are compromised.
Practical fix: Principle-of-least-privilege tool lists per skill/agent and opt-in hooks.

11. Git-ignore check in GSD core sanitizes paths by stripping characters.
Evidence: `.claude/get-shit-done/bin/lib/core.cjs:140` runs `targetPath.replace(/[^a-zA-Z0-9._\-/]/g, '')` before `git check-ignore`.
Impact: Paths with spaces/special chars may be checked as different paths, producing false negatives/positives.
Practical fix: Use argument-array execution (no shell string) and pass raw path safely.

12. Brownfield code detection in init flow relies on shell pipeline heuristics.
Evidence: `.claude/get-shit-done/bin/lib/init.cjs:174-180` uses `find | grep | head` via `execSync`.
Impact: Non-portable behavior and brittle detection in atypical repos; unnecessary process overhead.
Practical fix: Replace with native `fs` traversal with explicit ignore rules.
