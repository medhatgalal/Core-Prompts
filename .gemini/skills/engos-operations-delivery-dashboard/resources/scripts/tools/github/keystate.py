#!/usr/bin/env python3
"""Key state for every GitHub PR from the Jira extract and key_aliases.csv (no API calls, no model).
Per key: linked (key is in jira_issues.csv, or key_aliases.csv resolves it into the extract; alias_used = new key),
         other_project_key (alias says out_of_scope_* or older_than_window; default Q15), no_key-level 'not_found'.
Per PR:  linked if any key linked; else other_project_key if any key is other; else no_key.
primary_key = first key found in source order (title, branch, body, commit), as in the Definitions; primary_state is its state.
Outputs: data/extracts/github/github_pr_key_state.csv (per key) and github_pr_link_state.csv (per PR)."""
import csv, os, collections
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
import sys
G = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, "data", "extracts", "github"); J = os.path.join(R, "data", "extracts", "jira")
inext = {r["key"] for r in csv.DictReader(open(os.path.join(J, "jira_issues.csv")))}
alias = {r["old_key"]: r for r in csv.DictReader(open(os.path.join(J, "key_aliases.csv")))}
def state(k):
    if k in inext: return "linked", "", "in_extract"
    a = alias.get(k)
    if not a: return "not_in_alias_map", "", ""
    res = a["resolution"]
    if res == "in_extract": return "linked", a["new_key"], res
    if res.startswith("out_of_scope") or res == "older_than_window": return "other_project_key", a["new_key"], res
    return "not_found", "", res
keys = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(G, "github_pr_jira_keys.csv"))): keys[(r["repo"], r["number"])].append(r)
kr, pr_rows, cnt = [], [], collections.Counter()
for p in csv.DictReader(open(os.path.join(G, "github_prs.csv"))):
    ks = sorted(keys.get((p["repo"], p["number"]), []), key=lambda r: int(r["rank"])); sts = []
    for r in ks:
        st, al, res = state(r["key"]); sts.append(st)
        kr.append([r["repo"], r["number"], r["key"], r["source"], r["rank"], st, al, res])
    pst = "linked" if "linked" in sts else ("other_project_key" if "other_project_key" in sts else "no_key")
    if sts and pst == "no_key": cnt["keys_all_not_found"] += 1
    cnt[pst] += 1
    pr_rows.append([p["repo"], p["number"], p["class"], ks[0]["key"] if ks else "", sts[0] if sts else "no_key", pst, len(ks)])
def w(n, c, rows):
    with open(os.path.join(G, n), "w", newline="") as f: x = csv.writer(f); x.writerow(c); x.writerows(rows)
w("github_pr_key_state.csv", ["repo", "number", "key", "source", "rank", "key_state", "alias_used", "alias_resolution"], kr)
w("github_pr_link_state.csv", ["repo", "number", "class", "primary_key", "primary_state", "pr_state", "key_count"], pr_rows)
print(dict(cnt), "key rows", len(kr), collections.Counter(r[5] for r in kr))
print("primary state", collections.Counter(r[4] for r in pr_rows))
