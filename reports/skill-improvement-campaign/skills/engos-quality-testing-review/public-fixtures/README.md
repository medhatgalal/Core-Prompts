# Public development fixtures

These are author-created synthetic examples, including their answers and illustrative
mutants. They are **not held-out data**, independent validation, model outputs, or
promotion evidence. No skill candidate has produced tests for them in this setup.

The two miniature repositories use Python 3.11+ and standard-library `unittest`.
Run the trusted fixture self-check from the repository root:

```sh
python3 reports/skill-improvement-campaign/skills/engos-quality-testing-review/public-fixtures/check_public_fixtures.py
```

It executes the public example suites against reference and alternative correct
implementations, checks each public mutant causes its declared assertion failure,
and exercises an ineffective suite and an always-failing suite. It repeats the
matrix twice in fresh temporary directories and compares normalized outcomes.
Exit 0 means these development controls behaved as declared; exit 1 means the
fixtures need repair. JSON is printed to stdout. Timing is deliberately excluded
from equality checks. `unittest` itself collects and executes tests.

This script accepts no submitted test path and makes no capability score or promotion
decision. It runs only these reviewed, local, trusted examples. Temporary directories
are workspace hygiene, **not a security boundary** for untrusted generated code.
The coordinator must use the existing evaluator and approved execution boundary for
later model-generated tests; this helper must not grow into a second evaluator.

For a later public development task, deliver only a case's `TASK.md`, `sut.py`, and
`tests/test_existing.py` to each producer. Export the files into a separate admitted
runtime; pointing at this directory exposes all public answers. Keep the same public
input set for all three arms. The evaluator receives the producer's emitted
`tests/test_generated.py` and separate unrun report, then executes the tests on
correct implementations and mutants. The producer must not run them or claim they
passed. No test output is supplied to a subsequent producer in a frozen comparison.

`public-controls/` contains explicitly public answers: one example suite and one
behaviorally equivalent implementation per case. `mutants.json` lists exact,
single-site substitutions with contract IDs and expected failing example tests.
Each substitution must match exactly once and result in compilable Python. Mutation
IDs and answers are development aids, not labels to supply as an independent test.
The retry-count mutant changes the loop bound and terminal condition together;
this is one conceptual off-by-one fault represented by two declared substitutions.

The two cases cover boundary values, state transitions, exception recovery, and
resource cleanup. They do not cover browser E2E, concurrency, real storage, multiple
test frameworks, or a production test suite. See `../assessment.md` for the proposed
experiment, contract mapping, limits, and remaining admission work.
