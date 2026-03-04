# Coding Conventions

## Scope and Source of Truth
- Behavioral changes start in `ssot/*.md`; generated outputs in `.codex/`, `.gemini/`, `.claude/`, and `.kiro/` are derived artifacts.
- Canonical artifact rules live in `.meta/surface-rules.json` and generated artifact mapping/provenance lives in `.meta/manifest.json`.
- Do not hand-edit generated surfaces; regenerate with `python3 scripts/build-surfaces.py`.

## Language and File Patterns
- Python automation/validation logic is in `scripts/*.py`.
- Shell deployment/packaging wrappers are in `scripts/*.sh`.
- Prompt content is markdown with frontmatter in `ssot/*.md` and generated markdown/toml/json under dot-surface folders.

## Python Style Patterns (`scripts/*.py`)
- Files use shebang plus postponed annotations: `#!/usr/bin/env python3` and `from __future__ import annotations` (for example `scripts/build-surfaces.py`, `scripts/validate-surfaces.py`, `scripts/smoke-clis.py`, `scripts/sync-surface-specs.py`).
- Paths are handled with `pathlib.Path` and repo-root constants (for example `ROOT = Path(__file__).resolve().parent.parent`).
- Text I/O is explicit UTF-8 (`read_text(encoding='utf-8')`, `write_text(..., encoding='utf-8')`).
- Type hints are used in function signatures (`list[str]`, `dict[str, str]`, `tuple[int, str]`).
- CLIs use `argparse` with explicit flags and predictable exit codes (`0` success, `2` validation failure patterns in `scripts/validate-surfaces.py` and `scripts/smoke-clis.py`).
- Determinism is preferred: sorted iteration over files/slugs (for example `sorted(SSOT_DIR.glob('*.md'))`, sorted set handling in multiple scripts).
- JSON output is normalized with indentation and trailing newline (`json.dumps(..., indent=2) + '\n'`).

## Bash Style Patterns (`scripts/*.sh`)
- Scripts are strict mode: `set -euo pipefail` (`scripts/deploy-surfaces.sh`, `scripts/install-local.sh`, `scripts/package-surfaces.sh`).
- CLI UX pattern is consistent: `usage()` function + heredoc + `while [[ $# -gt 0 ]]; do case ... esac` parsing.
- Quoting is defensive for paths and args (`"$TARGET_ROOT"`, `"${ARGS[@]}"`).
- `scripts/deploy-surfaces.sh` enforces copy-only deployment and handles symlink replacement explicitly.

## Markdown and Frontmatter Patterns (`ssot/*.md`)
- SSOT entries are markdown documents with frontmatter keys such as `name`, `description`, and optional `kind`/`role`.
- Frontmatter parsing in generators/validators is intentionally simple string parsing (not full YAML), so keep key/value lines simple and avoid YAML-only advanced constructs (`scripts/build-surfaces.py`, `scripts/validate-surfaces.py`).
- Long-form prompt bodies are preserved and mirrored into generated surfaces (`.codex/skills/*/SKILL.md`, `.gemini/commands/*.toml`, `.kiro/agents/*.json`, etc.).

## Linting and Formatting Rules
- There is no repo-level Python linter/formatter config in root (no `pyproject.toml`, `ruff.toml`, `pytest.ini`, `tox.ini`, `setup.cfg` discovered at repo root).
- Style enforcement is operational rather than formatter-driven:
  - `python3 scripts/validate-surfaces.py --strict` validates structure/required fields.
  - `python3 scripts/smoke-clis.py --strict` validates CLI availability/discovery behavior.
  - `.github/workflows/cli-surfaces-validate.yml` runs schema sync, smoke checks, and strict validation on push/PR.
- A minimal Node config exists only at `.claude/package.json` (`{"type":"commonjs"}`), not as a project-wide JS tooling stack.

## Practical Change Boundaries
- If you change SSOT semantics in `ssot/*.md`, run: `python3 scripts/build-surfaces.py` then `python3 scripts/validate-surfaces.py --strict`.
- If you change rule definitions in `.meta/surface-rules.json`, refresh schema cache and re-run strict validation (`python3 scripts/sync-surface-specs.py --refresh`, then validate).
- If you change deployment behavior in `scripts/deploy-surfaces.sh`, verify copy-only behavior and dry-run output (`scripts/deploy-surfaces.sh --dry-run --cli all`).
