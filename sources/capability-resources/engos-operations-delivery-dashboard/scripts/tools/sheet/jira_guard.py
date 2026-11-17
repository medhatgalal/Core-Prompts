#!/usr/bin/env python3
"""Inbox 187 (verify-d #96 FAIL-2): a build never reads a Jira folder whose pull failed its guard.
wide_extract.py writes GUARD_FAILED.txt into the folder on a failed guard but leaves the CSVs in place; nothing read the marker. check(folder) stops with the folder path when
GUARD_FAILED.txt is there, or as_of.txt is missing (a pull that never finished). Called first in derive.derive (every build and recompute reads the folder through it) and at the
start of build.py, before any Sheet read or write.   Selftest: --selftest (red then green)."""
import os, sys


def problem(folder):
    """-> None when the folder is usable, else the reason (with the path)"""
    if not os.path.isdir(folder):
        return f"the Jira folder {folder} does not exist"
    g = os.path.join(folder, "GUARD_FAILED.txt")
    if os.path.exists(g):
        first = (open(g).read().strip().splitlines() or [""])[0][:200]
        return f"the Jira pull in {folder} FAILED its guard ({g}): {first}. Do not build from it; re-pull or remove the marker only after the cause is fixed"
    if not os.path.exists(os.path.join(folder, "as_of.txt")):
        return f"the Jira folder {folder} has no as_of.txt (the pull did not finish)"
    return None


def check(folder):
    p = problem(folder)
    if p:
        sys.exit("stop: " + p)


def selftest():
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as d:
        ok &= "no as_of.txt" in (problem(d) or "") and d in (problem(d) or "")                                  # red: no as_of.txt
        open(os.path.join(d, "as_of.txt"), "w").write("2026-11-16T20:21:10Z\n")
        ok &= problem(d) is None                                                                              # green: as_of.txt only
        open(os.path.join(d, "GUARD_FAILED.txt"), "w").write("GUARD FAILED: AIPL-1 missing\n")
        ok &= "FAILED its guard" in (problem(d) or "") and "AIPL-1 missing" in (problem(d) or "") and d in (problem(d) or "")   # red: marker, CSVs left in place
        try:
            check(d); ok = False
        except SystemExit as e:
            ok &= str(e).startswith("stop:") and d in str(e)
        os.remove(os.path.join(d, "GUARD_FAILED.txt")); ok &= problem(d) is None                              # green again
    ok &= "does not exist" in (problem("/nonexistent/x") or "")
    for real in ("data/extracts/jira_wide_1116c", "data/extracts/jira_wide_1116b"):                           # the saved pulls the real Sheet was built from pass
        if os.path.isdir(real):
            ok &= problem(real) is None
    print("jira_guard selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 0)
