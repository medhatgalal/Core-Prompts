# Core-Prompts / Capability Fabric

Better prompts, better outcomes, with deterministic capability publishing.

Core-Prompts is evolving into Capability Fabric: a practical capability-provider layer for people who use AI for writing, planning, research, product work, operations, and software delivery. It helps you move from vague asks to structured, reusable prompt workflows and publishable capabilities that orchestrators can consume safely.

## What You Can Do With It

- Turn rough ideas into high-quality prompts.
- Merge multiple drafts into one stronger direction.
- Get senior-style guidance for decisions and execution.
- Run long-form analysis without losing context.
- Export clean context handoffs between AI sessions and tools.
- Import one or more external prompt/spec source sets from files, folders, raw URLs, or GitHub folders and get deterministic UAC classification, manifests, and fit analysis.
- Audit existing SSOT entries and see whether each one should be a skill, an agent, both, or manual review.
- Publish advisory manifests and handoff contracts without taking over orchestration.

### Included Skills (Brief)

- `supercharge`: multi-pass prompt hardening and quality improvement.
- `converge`: synthesis engine for combining multiple sources into one decision-ready output.
- `mentor`: structured guidance for planning, prioritization, and de-risking.
- `analyze-context`: iterative analysis workflow with memory tracking for big scopes.
- `code-review`: commit review with scope control and over-engineering detection.
- `resolve-conflict`: structured merge-conflict analysis and resolution planning.
- `threader`: thread transcript and context export for handoffs.
- `uac-import`: ingest one local file, folder, raw URL, or GitHub folder, classify it, uplift it, and recommend the right target surface.

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

### `code-review`

**Run**

```text
/code-review
```

**Expected output**

- Findings grounded in the actual `git show` diff.
- Scope-creep and over-engineering warnings when the change is too broad.
- A merge-readiness recommendation with concrete fixes when needed.

### `resolve-conflict`

**Run**

```text
/resolve-conflict --preview main
```

**Expected output**

- Failure-mode-first conflict analysis.
- A logical merge order and verification checklist.
- Explicit decision points when the branches contain incompatible guidance.

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
- Skill vs agent vs both recommendation with rationale.
- Target-system packaging guidance for Codex, Gemini, Claude, and Kiro.

### Capability Fabric and UAC

UAC is the authoritative classifier and uplift subsystem inside Capability Fabric for imported sources and existing `ssot/` entries.

It classifies each source as:
- `skill`
- `agent`
- `both`
- `manual_review`

Then Core-Prompts derives the emitted surfaces for each CLI from that capability type.

Quick matrix:

| Capability Type | Codex | Gemini | Claude | Kiro |
| --- | --- | --- | --- | --- |
| `skill` | skill | command + skill | command | prompt + skill |
| `agent` | agent | agent | agent | agent |
| `both` | skill + agent | command + skill + agent | command + agent | prompt + skill + agent |
| `manual_review` | hold | hold | hold | hold |

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

`scripts/deploy-surfaces.sh` and `scripts/install-local.sh` are safe in partial or empty CLI environments: in non-strict mode they skip unavailable CLIs, print a summary, and exit successfully.

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

- Capability Fabric overview: [docs/CAPABILITY-FABRIC.md](docs/CAPABILITY-FABRIC.md)
- Architecture source assessment: [docs/ARCHITECTURE-SOURCE-ASSESSMENT.md](docs/ARCHITECTURE-SOURCE-ASSESSMENT.md)

- Docs home: [docs/README.md](docs/README.md)
- Getting started: [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)
- Full run examples: [docs/EXAMPLES.md](docs/EXAMPLES.md)
- Technical reference: [docs/README_TECHNICAL.md](docs/README_TECHNICAL.md)
- CLI reference: [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md)
- UAC capability model: [docs/UAC-CAPABILITY-MODEL.md](docs/UAC-CAPABILITY-MODEL.md)
- UAC usage guide: [docs/UAC-USAGE.md](docs/UAC-USAGE.md)
- FAQ: [docs/FAQ.md](docs/FAQ.md)
- Docs prompt-pack: [docs/prompt-pack/README.md](docs/prompt-pack/README.md)
