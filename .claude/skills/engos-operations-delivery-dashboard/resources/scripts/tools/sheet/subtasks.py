#!/usr/bin/env python3
"""v1.43c AC74: sub-tasks are not items. Their code changes roll up to the parent ticket; a sub-task whose parent is outside the extract is IGNORED (not counted, not rolled up).
Source: the wide extract (data/extracts/jira_wide_1111/jira_issues.csv), the only extract that holds sub-tasks (the main extract has none). 'Outside the extract' = the parent key is not in the wide extract (5 at 11 Nov 2026,
listed in crew/subtask-out-of-scope-parent-5.md). Pure Python. Selftest: python3 tools/sheet/subtasks.py --selftest (also recomputes that list file)."""
import csv, os, re, sys

WIDE = "data/extracts/jira_wide_1111/jira_issues.csv"
LIST_FILE = "crew/subtask-out-of-scope-parent-5.md"


def load(wide=WIDE):
    """-> (parent {sub-task key: parent key} for sub-tasks whose parent is in the wide extract, ignored {sub-task key: parent key} for those whose parent is not)"""
    if not os.path.exists(wide):
        return {}, {}
    rows = list(csv.DictReader(open(wide, newline="")))
    keys = {r["key"] for r in rows}
    parent, ignored = {}, {}
    for r in rows:
        if r["type"] == "Sub-task" and r["parent_key"]:
            (parent if r["parent_key"] in keys else ignored)[r["key"]] = r["parent_key"]
    return parent, ignored


def remap(links, parent, ignored):
    """links: link dicts with jira_key / resolved_jira_key. A link to a sub-task rolls up to the parent ticket (resolved_jira_key = parent, rolled_up = the sub-task key); a link to an ignored sub-task resolves to nothing.
    -> (rolled up count, ignored count)"""
    ru = ig = 0
    for l in links:
        k = l.get("resolved_jira_key") or l["jira_key"]
        if k in parent:
            l["rolled_up_from"] = k; l["resolved_jira_key"] = parent[k]; ru += 1
        elif k in ignored:
            l["rolled_up_from"] = k; l["resolved_jira_key"] = ""; l["ignored_subtask"] = 1; ig += 1
    return ru, ig


def selftest():
    doc = open(LIST_FILE).read() if os.path.exists(LIST_FILE) else ""
    listed = set(re.findall(r"^\| ([A-Z]+-\d+) \|", doc, re.M))
    m = re.search(r"Source: (data/extracts/jira_wide_\d+/jira_issues\.csv)", doc)
    named = m.group(1) if m else WIDE                      # the list file names its own extract (16 Nov: jira_wide_1116)
    parent, ignored = load(named)
    ok = set(ignored) == listed and bool(listed) and doc.startswith("as of ") and f"extract: {len(listed)}" in doc.splitlines()[0]   # the list file equals the recompute on the extract it names
    ign11 = load("data/extracts/jira_wide_1111/jira_issues.csv")[1]                  # separate 11 Nov case: the earlier extract gives the earlier 5 (the list minus the 16 Nov addition)
    ok &= len(ign11) == 5 and set(ign11) <= listed
    L = [{"jira_key": "S-1", "resolved_jira_key": ""}, {"jira_key": "S-2", "resolved_jira_key": "S-2"}, {"jira_key": "T-9", "resolved_jira_key": "T-9"}]
    ru, ig = remap(L, {"S-1": "P-1"}, {"S-2": "Q-1"})
    ok &= (ru, ig) == (1, 1) and L[0]["resolved_jira_key"] == "P-1" and L[1]["resolved_jira_key"] == "" and L[2]["resolved_jira_key"] == "T-9"
    print(f"subtasks ({named}): {len(parent)} roll up, {len(ignored)} ignored; list file {len(listed)}; 11 Nov extract {len(ign11)}; selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 0)
