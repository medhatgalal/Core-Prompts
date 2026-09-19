# Repository-neutral shaping validation

Date: 2026-09-19
Branch: `AI/engos-full-shaping-design`
Pre-change HEAD: `a491bd4818c2ddba5725e7aedebbb283a60fb6cf`

## Outcome

PASS for the scoped repository-neutral behavior change. Product repositories,
modules and search tools are runtime inputs rather than shipped defaults. The
familiar Appian integration example remains in `docs/EXAMPLES.md` for readers and
is absent from the executable pitch-review skill.

## Implemented contract

- Intake/Framed registers a supplied repository but does not start code-scan or
  architecture-fit before accepted G1. A narrowly necessary solution-free fact
  check remains possible and must be recorded.
- G2 resolves the current workspace or explicitly supplied roots. It asks which
  folders/modules matter only when scope is ambiguous.
- Inspection prefers project knowledge, then active language-server/semantic
  indexes, host-native indexed search, bounded `rg`, then a human evidence request.
  It does not install/start an indexer, assume siblings or scan outside scope.
- Evidence records repository/revision, selected modules, search capability,
  queries/symbols, opened paths/lines, coverage, exclusions and no-hit limits.
- Documents-only shaping records repository inspection as not applicable.

## Red/green evidence

Initial focused tests failed as expected: `repository-discovery.md` was absent from
the code-scan route and the Appian worked example lived in the shipped pitch skill.
After same-slug UAC plan/judge/apply and generated-surface rebuild, the route and
docs-only relocation checks pass.

Independent instruction review initially failed on residual Appian product context,
brittle tests and a contributor-applicability defect. Three bounded repairs removed
runtime product defaults, retained reader examples in docs, and corrected Product
decision-authority semantics. Final review reported PASS with no P1/P2 findings.
The same non-author reviewer was reused because the host had no fresh worker slot;
this is independent authorship review, not a fresh blind-context claim.

## Behavioral exercises

Private fixtures and results:
`/private/tmp/engos-repo-neutral-behavior/`.

| Case | Initial observation | Repair/final observation | Verdict |
| --- | --- | --- | --- |
| Clear single repository | Worker inspected the repo during the opening frame when the user asked for inspection. | Reloaded skill registers the repo and defers inspection until accepted G1/G2. | PASS after one iteration |
| Ambiguous monorepo | Opening framing correctly avoided repo claims but did not yet need module selection. | At Research, inspected only the supplied root/module READMEs, found three plausible owners and asked which notification/module applies before tracing. | PASS |
| Documents only | Read the supplied note, asked framing/appetite/authority questions and used no repository discovery, LSP, index or text search. | No repair needed. | PASS |

Workers were reused completed subagent contexts due host slot limits. They reloaded
the generated skill and were forbidden from reading prior fixture results, but this
is not OS-enforced isolation or a real-user usability study. The exercises prove
the scoped observable routing behavior, not model superiority or every repository.

## Verification

- `python3 -m pytest -q tests/test_shaping_repository_fit.py tests/test_resource_backed_skill_surfaces.py tests/test_public_docs_contract.py`
  - `40 passed`
- `python3 -m pytest -q tests/test_shaping*.py`
  - `276 passed, 13 skipped` (optional renderer skips)
- `bin/capability-fabric validate --strict`
  - PASS, `32` SSOT entries
- Same-slug UAC plan/judge/apply:
  - `engos-design-shaping`: structural ready and applied
  - `engos-audit-pitch-review`: structural ready and applied

Generated resources were rebuilt on Codex, Gemini, Claude, Kiro and Grok surfaces.
No home installation, native-agent surface, product-repository mutation, merge,
tag or release occurred in this validation slice.
