#!/usr/bin/env python3
"""AC8 call projection for GitHub, computed from the pull's own CSVs (no API calls).
calls(login) = authored searches + 1 recount + 3 state recounts + reviewed searches
             + sum over its PRs of: 1 detail + 1 files (if files_checked) + 1 reviews (if merged)
               + 1 merge-commit read (if merged and the key was not found in title, branch or body)
               + 1 head-commit read (every PR; AC53 fix, all four key sources)
               + 1 commits-list read (every PR; v1.12 any commit message; PRs over 100 commits need more pages, not counted)
Writes data/extracts/github/projection.csv and prints totals."""
import csv, json, math, os, collections
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(R, "data", "extracts", "github")
ck = {}
for f in os.listdir(os.path.join(D, "checkpoints")):
    if f.endswith(".json"): ck[f[:-5]] = json.load(open(os.path.join(D, "checkpoints", f)))
rows = []
tot = collections.Counter()
for login, c in sorted(ck.items()):
    A = len(c["prs"]); Rv = c["reviewed_rows"]
    det = A; files = sum(1 for p in c["prs"] if p["files_checked"]); rev = sum(1 for p in c["prs"] if p["merged"])
    com = sum(1 for p in c["prs"] if p["merged"] and not any(s in ("title", "branch", "body") for _, s in p["keys"]))
    head = sum(1 for p in c["prs"] if p.get("head_commit_checked"))
    com += sum(1 for p in c["prs"] if p.get("all_commits_checked"))  # v1.12: commits list per PR
    com += head
    s_auth = max(1, math.ceil(A / 100)) + 1 + 3 + max(0, c["authored_windows"] - 1)
    s_rev = max(1, math.ceil(Rv / 100)) + 1
    t = det + files + rev + com + s_auth + s_rev
    rows.append([login, A, rev, Rv, det, files, rev, com, s_auth, s_rev, t])
    for k, v in zip(("A", "merged", "R", "detail", "files", "reviews", "commit", "search_auth", "search_rev", "total"), rows[-1][1:]): tot[k] += v
with open(os.path.join(D, "projection.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["login", "authored", "merged", "reviewed_by", "detail_calls", "files_calls", "reviews_calls", "commit_calls", "search_authored", "search_reviewed", "total_calls"]); w.writerows(rows)
print(dict(tot)); print("logins", len(rows), "per PR", round(tot["total"] / tot["A"], 2))
