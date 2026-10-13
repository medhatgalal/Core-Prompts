# Actual red observations retained

The first source check ran before the new consumption reference existed: `tests/test_review_package.py::test_d6src001_progressive_route_closure` failed with ResourceContractError for missing `references/review-package-consumption.md`; 113 passed, 1 skipped, 1 failed in 80.95s. This is incomplete-construction red evidence, not a claimed algorithm regression or test-first proof. The complete route now passes the actual loader checks.

`focused-tests.txt` preserves the next complete captured run: 336 passed, 1 skipped, 1 failed in 85.18s. `test_slice_receipt_optional_route_and_template` incorrectly applied the detached loader to canonical D5 after adding an authored-owner import, failing on absent authored D5 oracle path. Fixed that test to canonical `load_capability_bundle`, preserving no shadow copy. `resource-batman-tests.txt` records the passing relevant rerun.

No preimplementation failing exact-binding test was recorded. Verifier correctness evidence consists of actual matching and fault-fired rejection tests, preserved source baseline, and required independent review. No TDD/mutation protocol completion is claimed from these red observations.
