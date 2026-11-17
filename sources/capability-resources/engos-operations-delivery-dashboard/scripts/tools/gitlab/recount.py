#!/usr/bin/env python3
"""AC7 check: recount each author with a different call (per_page=1, X-Total) and compare with rows in code_changes.csv.
Also confirms no duplicate changes and counts per person. GET only through tools/ro/ro."""
import argparse, csv, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glapi
ap = argparse.ArgumentParser(); ap.add_argument("--dir", default="data/extracts/gitlab"); ap.add_argument("--identity", default="data/identity.csv")
ap.add_argument("--only", default="")
a = ap.parse_args()
only = set(filter(None, a.only.split(",")))
asof = open(os.path.join(a.dir, "as_of.txt")).read().strip()
import datetime
start = (datetime.datetime.strptime(asof, "%Y-%m-%dT%H:%M:%SZ") - datetime.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
rows = list(csv.DictReader(open(os.path.join(a.dir, "code_changes.csv"))))
per = collections.Counter(r["author"] for r in rows)
dup = len(rows) - len({(r["project_id"], r["number"]) for r in rows})
out = []
for r in csv.DictReader(open(a.identity)):
    u = r["gitlab_username"]
    if only and u not in only: continue
    if r["gitlab_confidence"] not in ("exact", "overridden"):
        out.append([r["person"], u, r["gitlab_confidence"], "", "", "", "identity not exact: not pulled"]); continue
    s, h, d = glapi.get(f"/merge_requests?author_username={u}&scope=all&per_page=1&created_after={start}&created_before={asof}")
    total = int(h.get("x-total") or -1) if s == 200 else -1
    out.append([r["person"], u, "exact", per.get(u, 0), total, "match" if total == per.get(u, 0) else "MISMATCH",
                "zero changes in 12 months" if per.get(u, 0) == 0 else ""])
with open(os.path.join(a.dir, "author_recount.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["person", "gitlab_username", "confidence", "rows_in_extract", "recount_x_total", "result", "note"]); w.writerows(out)
mm = [o for o in out if o[5] == "MISMATCH"]
print("people", len(out), "exact", sum(1 for o in out if o[2] == "exact"), "mismatch", len(mm), "zero", sum(1 for o in out if o[6].startswith("zero")), "dups", dup)
for o in mm: print(o)
