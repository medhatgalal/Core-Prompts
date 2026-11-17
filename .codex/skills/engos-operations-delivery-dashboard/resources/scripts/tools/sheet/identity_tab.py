#!/usr/bin/env python3
"""v1.43g (AC84): the Identity tab, rebuilt from data/identity.csv on every refresh. Pure functions.
Columns: every column of the file in file order (cell for cell), then `no GitHub login` (yes when github_login is blank, else no), then `as of (UTC)` (one cell, row 2).
The tab is the one exception (AC84) to the rule that names, usernames, emails and account ids appear on Individual only: the scanners exempt it, nowhere else.
Selftest: python3 tools/sheet/identity_tab.py --selftest"""
import csv, os, sys

FLAG = "no GitHub login"
ASOF = "as of (UTC)"
TAB = "Identity"


def grid(path, asof_text):
    """-> [[header...], [row...]...]: file header + FLAG + ASOF; one row per file row, values as text, nothing dropped or reordered"""
    with open(path, newline="") as f:
        rd = list(csv.reader(f))
    head, body = rd[0], rd[1:]
    gi = head.index("github_login")
    out = [head + [FLAG, ASOF]]
    for i, r in enumerate(body):
        r = list(r) + [""] * (len(head) - len(r))
        out.append(r + ["yes" if not r[gi].strip() else "no", asof_text if i == 0 else ""])
    return out


def missing_count(rows):
    j = rows[0].index(FLAG)
    return sum(1 for r in rows[1:] if r[j] == "yes")


def sources_formula():
    """the Sources (Coverage) row: B is a formula over the Identity flag column, so it can never differ from the tab"""
    return ('="Identity tab (data/identity.csv): "&COUNTIF(Identity!O2:O,"yes")&" of "&COUNTA(Identity!A2:A)&" people have no GitHub login, so their code changes on GitHub cannot be matched to them. '
            'Count only here; the people are listed on the Identity tab."')


def selftest():
    import tempfile
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    real = os.path.join(root, "data", "identity.csv")
    g = grid(real, "2026-11-16 02:05:35Z")
    src = list(csv.reader(open(real, newline="")))
    ok = len(g) == len(src) == 117 and g[0][:-2] == src[0] and all(r[:-2] == s for r, s in zip(g[1:], src[1:]))          # 116 data rows, cell for cell
    ok &= missing_count(g) == sum(1 for s in src[1:] if not s[src[0].index("github_login")].strip()) == 28
    ok &= g[1][-1] == "2026-11-16 02:05:35Z" and all(r[-1] == "" for r in g[2:]) and g[0][-2:] == [FLAG, ASOF]
    ok &= all(len(r) == len(src[0]) + 2 for r in g)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as t:          # a short row and a whitespace login
        t.write("person,github_login\nA,\nB,  \nC,bc\nD\n")
    h = grid(t.name, "x"); os.unlink(t.name)
    ok &= [r[-2] for r in h[1:]] == ["yes", "yes", "no", "yes"] and missing_count(h) == 3
    ok &= "Identity!O2:O" in sources_formula() and "28" not in sources_formula()          # the number is never typed
    print("identity_tab selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 2)
