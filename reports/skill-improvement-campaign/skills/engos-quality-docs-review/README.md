# Public docs-review development fixtures

These are author-written, synthetic PUBLIC assets. The answers are intentionally
visible. They are neither sealed nor independent validation, and the check script
does not grade a model or issue promotion evidence.

From the Core-Prompts repository root:

```bash
python3 reports/skill-improvement-campaign/skills/engos-quality-docs-review/check_fixtures.py --self-test
```

Expected: exit 0, six `true` seed observations for `drift`, six `false` observations
for `clean`, safe controls passing, unchanged fixture trees, and eight passing
failure controls. The rejected old CLI flag exits 2; current and customized
commands exit 0. The helper executes only the checked-in synthetic CLI/help and
stdout generator, never commands parsed from Markdown. No credentials, network,
model calls, or publication are involved. Failure controls modify disposable
temporary copies only.

`public-cases.jsonl` follows the existing public case field conventions in
`evals/cases/public/code-review/core.jsonl`; it is not automatically admitted to
the existing pilot or its schema. `public-answers.json` names each seeded defect,
exact evidence, a scoped repair, and safe controls. `contract-mapping.json` is a
draft proposal for coordinator review, not a reviewed topology overlay.

For a later authorized trial, materialize just one `fixtures/<case>/` tree into
an isolated repository, initialize and freeze its Git tree and full file hashes,
then supply `task.txt` as the common task. Fixture-local `AGENTS.md` is part of
every arm. Do not expose this report directory, answer file, check script,
candidate-author history, or other case to the model. The case itself includes
everything needed to inspect the documentation. For the bare arm, also exclude
all target skill resources and automatic discovery of the target skill. Effective
isolation must be demonstrated by the coordinator; copying these files or making
a fresh task does not prove it.

The link check supports only the simple unique ASCII headings in these fixtures.
It is not a production Markdown link validator. The audience and release checks
confirm planted text against explicit fixture policy and source, not arbitrary
semantic correctness. Read-only hashing here checks bytes and path additions;
the future execution boundary must also cover modes, symlinks, Git state, files
outside the fixture, tools, hooks, browser state, and credentials.

Only `assessment.md` is the local status record. The proposal, inventories, cases,
answers and check receipt are supporting evidence.
