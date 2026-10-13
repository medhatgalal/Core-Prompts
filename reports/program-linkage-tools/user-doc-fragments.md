# Documentation fragments for controller integration

These are additions to existing pages, not an inventory rewrite. The controller
must verify the final generated bundles before presenting the commands as shipped.

## README / GETTING-STARTED

When a supplied plan or specification is difficult to inspect by hand, the
planner and specification skills offer optional mechanical check routes. The
planner lists tasks whose declared dependencies are completed. The specification
skill produces a matrix of actual task links and optional designed test links.
A pass means those links or graph records are consistent; inspect outcome text,
source truth, approval and implemented behavior separately. Manual artifacts stay
optional, and these commands do not create a required artifact sequence.

## EXAMPLES

Ask the planner: “Check PLAN.json and show the dependency-ready tasks.” For two
independent roots T1/T2 it returns both IDs, sorted. If T3 depends on both, it
remains blocked until both occur in the supplied completed-task list. Null digest
and authority observations remain visible even when `unresolved` is empty, and
the frontier grants no execution permission.

Ask the specification skill: “Check the actual requirement-to-task links in
SPEC.json and PLAN.json; select TESTS.json only if supplied.” Every `must`
requirement needs an actual task link and, when selected, an actual test-row link.
Missing R2, unknown R9 and duplicate T1 fail. Test inventory alone is insufficient.
Omitted tests say `not_supplied`; selected designed tests say `not_run`.

Use `--design-links` only to check task design IDs against supplied specification
design refs. This does not inspect design files or verify their hashes. A task
saying “export every row” can correctly link to a requirement saying “export only
permitted rows.” The checker passes the mechanical linkage and leaves semantic
correctness unassessed; an independent reviewer must inspect the contradiction.

## CLI-REFERENCE

From the selected skill's bundle directory:

```sh
python3 resources/scripts/graph_check.py --plan PLAN.json
python3 resources/scripts/trace_check.py --spec SPEC.json --plan PLAN.json
python3 resources/scripts/trace_check.py --spec SPEC.json --plan PLAN.json --tests TESTS.json --design-links
```

Load planner `graph_check`, or specification `trace_check` and, for selected tests,
`trace_tests`. `trace_examples` provides complete positive and contradictory
fixtures. The commands use standard-library Python and explicit bundled schema
bytes, with no repository or sibling installation discovery.

Each command emits one deterministic JSON object. Exit 0 means selected mechanical
checks passed; 1 means schema, ID, graph or selected linkage/coverage failure;
2 means CLI, input or package inability to assess. Errors leave the frontier or
matrix empty. Semantic correctness, behavioral verification and authority
verification remain `not_assessed` on every output. A nonnull plan spec digest is
compared to the exact supplied specification bytes, and spec references are opaque.

## RELEASE-PACKAGING

The trace package imports exact TaskPlan/TaskContract/TestDesign bytes through the
finite reviewed registry. The narrow TaskPlan sibling reference exception requires
explicit same-owner paired bindings, identical placement and direct owner and
consumer dependency edges at canonical admission. Detached validation checks its
local receipt, bytes and consumer closure without looking up the absent owner map.
This establishes consistency; externally trusted package identity is required to
detect a self-consistent receipt and byte replacement. Remote, traversal, dynamic,
fragment and base-changing references stay forbidden.

## CHANGELOG

Added optional stdlib graph and trace checkers to the existing planner/specification
skills, with production-shape validation, deterministic dependency frontier,
selected test/design membership, explicit unassessed states and bounded sibling
schema closure. No input identity, agent surface, release or installation change.

Selected test files containing JSON null or other invalid top-level types fail
TestDesign shape with `tests_status: supplied`, empty matrix and exit 1. Only
omission of `--tests` means `not_supplied`. Lone surrogate escapes in any input
key/value produce structured `invalid_json` and exit 2. Valid non-ASCII/astral
identifiers remain unchanged; direct Python API serialization defensively escapes
lone surrogates without dropping or normalizing values.
