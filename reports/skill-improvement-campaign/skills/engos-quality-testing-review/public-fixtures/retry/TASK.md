# Public task: retrying stream reads

Add a minimal useful `tests/test_generated.py` using the existing `unittest` stack.
Inspect `sut.py` and `tests/test_existing.py`. Import `read_with_retry` from `sut`.
Explain assumptions, risk priorities, uncovered cases, the command another operator
could run, and that tests have not been executed. Do not run tests, modify production
code, install dependencies, or claim measured coverage. Return test file and short
report separately. Use deterministic fakes for the supplied factory/stream protocol.

- R1: `read_with_retry(open_stream, attempts=2)` returns the first successful
  `stream.read()` result, including empty bytes. `attempts` is an integer supplied
  by the caller and counts total factory invocations, not retries after the first.
- R2: Reject `attempts < 1` with `ValueError` before invoking the factory.
- R3: An `OSError` from factory or read retries if attempts remain; exhaustion
  re-raises the last failure. Non-`OSError` exceptions propagate without retry.
- R4: Each successfully opened stream is closed exactly once, after read finishes
  or raises and before another factory call. A failed open creates no stream to
  close. The fixture's `close()` never raises. Do not invent a policy for close failure.
- R5: A subsequent independent call starts with a fresh attempt budget. There are
  no sleeps, network operations, global caches, or real files required.

Only the factory-call count and stream protocol effects are observable. Function
locals, retry-loop shape, error text, and private attributes are not API contracts.
There is no coverage artifact. Real filesystem integration and concurrent access
are outside this unit test task.
