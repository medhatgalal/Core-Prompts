# Core-Prompts

Better prompts, better outcomes.

Core-Prompts is a practical prompt system for people who use AI for writing, planning, research, product work, operations, and software delivery. It helps you move from vague asks to structured, reusable prompt workflows that are easier to trust.

## What You Can Do With It

- Turn rough ideas into high-quality prompts.
- Merge multiple drafts into one stronger direction.
- Get senior-style guidance for decisions and execution.
- Run long-form analysis without losing context.
- Export clean context handoffs between AI sessions and tools.
- Import one external prompt/spec source and get deterministic UAC classification and packaging guidance.

### Included Skills (Brief)

- `supercharge`: multi-pass prompt hardening and quality improvement.
- `converge`: synthesis engine for combining multiple sources into one decision-ready output.
- `mentor`: structured guidance for planning, prioritization, and de-risking.
- `analyze-context`: iterative analysis workflow with memory tracking for big scopes.
- `threader`: thread transcript and context export for handoffs.
- `uac-import`: ingest one local file or raw URL, classify it, uplift it, and recommend the right target surface.

## Examples (Usage + Expected Output)

### `supercharge`

**Run**

```text
supercharge /ult /realism Improve this prompt:
"Design our docs strategy."
```

**Expected output**

- A stronger copy-ready prompt with clearer constraints.
- Immediate execution output from that improved prompt.
- Assumptions called out explicitly when context is missing.

### `converge`

**Run**

```text
converge intent: "Choose one strategy for Q2."
source A: <paste>
source B: <paste>
source C: <paste>
```

**Expected output**

- One merged recommendation instead of stitched summaries.
- Explicit trade-offs and rationale.
- Clear open questions and next actions.

### `mentor`

**Run**

```text
/mentor Validation failed after my SSOT edits. Output: <paste>
```

**Expected output**

- Triage of probable root causes.
- Ordered recovery steps.
- A concrete next-action checklist.

### `analyze-context`

**Run**

```text
Use analyze-context to audit all ssot/*.md files for drift.
```

**Expected output**

- Memory files in `.analyze-context-memory/`.
- Item-by-item progress tracking.
- Final findings and recommended fixes.

### `threader`

**Run**

```text
/threader export
```

**Expected output**

- Transcript export file when supported.
- Safe fallback output when file export is unavailable.
- Chronology preserved for reliable handoff.

### `uac-import`

**Run**

```text
Use uac-import on `/absolute/path/to/prompt.md`.
```

**Expected output**

- Deterministic source summary and uplift.
- Skill vs agent recommendation with rationale.
- Target-system packaging guidance for Codex, Gemini, Claude, and Kiro.

## Installation

```bash
git clone https://github.com/medhatgalal/Core-Prompts.git
cd Core-Prompts
python3 scripts/build-surfaces.py
python3 scripts/validate-surfaces.py --strict
```

Optional deployment to local CLI homes:

```bash
scripts/deploy-surfaces.sh --cli all
```

## Quick AI Handoff Snippet

```text
You are working in <repo_path>/Core-Prompts.
This repo is prompt-first. Source of truth is ssot/.
If behavior changes are needed, edit ssot files first, then run:
1) python3 scripts/build-surfaces.py
2) python3 scripts/validate-surfaces.py --strict
Do not hand-edit generated files under .codex/.gemini/.claude/.kiro.
```

## Additional Links

- Docs home: [docs/README.md](docs/README.md)
- Getting started: [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)
- Full run examples: [docs/EXAMPLES.md](docs/EXAMPLES.md)
- Technical reference: [docs/README_TECHNICAL.md](docs/README_TECHNICAL.md)
- CLI reference: [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md)
- FAQ: [docs/FAQ.md](docs/FAQ.md)
- Docs prompt-pack: [docs/prompt-pack/README.md](docs/prompt-pack/README.md)
