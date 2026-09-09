# Public task: expiring leases

Add a minimal useful `tests/test_generated.py` using the existing `unittest` stack.
Inspect `sut.py` and `tests/test_existing.py`. Import only `LeaseBook` from `sut`;
use its public methods. Explain assumptions, risk priorities, uncovered cases, the
command another operator could run, and that the tests have not been executed.
Do not run tests, modify implementation, install dependencies, or report measured
coverage. Return the test file and a short report as separate artifacts.

Contract (single-threaded, finite numeric timestamps supplied by the caller):

- L1: `acquire(key, owner, now, ttl)` succeeds with `True` when the key has no live
  lease, creates a lease ending at `now + ttl`, and otherwise returns `False`
  without modifying the existing lease. Even the same owner cannot reacquire a
  live lease. Keys and owners are nonempty strings supplied by the caller.
- L2: A lease is live while `now < expiry`; at exactly expiry it can be acquired
  by another owner. Expiry uses no wall clock, sleep, or background cleanup.
- L3: `renew(key, owner, now, ttl)` returns `True` only for that owner's live
  lease, replacing expiry with `now + ttl`. Failed renewals change nothing.
  Expired leases cannot be revived by renewal.
- L4: `release(key, owner)` returns `True` and removes the lease only for the
  recorded owner, or `False` without changes for another owner/missing key.
  Release does not consult time, so the recorded owner may release an expired lease.
- L5: Both acquire and renew raise `ValueError` for `ttl <= 0`, before changing
  state, including missing keys and wrong owners. No extra type validation is
  required. Different keys and separate `LeaseBook` instances are independent.

Internal data structures and eager/lazy expiry cleanup are not part of the API.
Concurrency and monotonic-clock enforcement are outside scope; tests should not
invent either guarantee. There is no coverage report available.
