#!/usr/bin/env python3
"""v1.43 (inbox 165 item 2): Work Category per ticket, from jira's side files (data/extracts/jira/jira_work_category.csv: key, wc_id, wc_value now; jira_work_category_changes.csv: key, changed_at, from/to).
Rule (plan-copy6-v143 B3): an epic or initiative carries its OWN value; every other ticket takes its PARENT epic's value, valued AT THE TICKET'S FINISH DATE (today's value for open work), reconstructed from the changelog.
BUILT AGAINST THE SIDE FILES: jira's own join output (jira 46) is not used yet; swap load() for it when it lands. Pure Python, no network, no model call.
Offline selftest: python3 tools/sheet/workcat.py --selftest"""
import csv, os, sys


def load(jira_dir):
    now, chg = {}, {}
    p = os.path.join(jira_dir, "jira_work_category.csv")
    if not os.path.exists(p):
        return now, chg
    for r in csv.DictReader(open(p)):
        now[r["key"]] = r["wc_value"]
    q = os.path.join(jira_dir, "jira_work_category_changes.csv")
    if os.path.exists(q):
        for r in csv.DictReader(open(q)):
            chg.setdefault(r["key"], []).append((r["changed_at"], r["from_value"], r["to_value"]))
        for v in chg.values():
            v.sort()
    return now, chg


def value_at(key, when, now, chg):
    """the key's own Work Category at 'when' (ISO 'YYYY-MM-DDTHH:MM:SSZ', or None for now). AC76 day rule: a change made ON the finish day counts as AFTER it (it is undone); only changes on earlier UTC days count."""
    ch = chg.get(key)
    if not when or not ch:
        return now.get(key, "")
    day = when[:10]
    before = [c for c in ch if c[0][:10] < day]
    if before:
        return before[-1][2]
    return ch[0][1]          # every change is on the finish day or later: the value before the first change


def for_issue(r, when, now, chg, containers):
    """r: the issue row (key, type, parent_key). Containers (epic, initiative) use their own value; others use the parent's."""
    if r["type"] in containers:
        return value_at(r["key"], when, now, chg)
    return value_at(r["parent_key"], when, now, chg) if r.get("parent_key") else ""


def selftest():
    now = {"E-1": "Support", "E-2": "", "I-1": "Customer Feature"}
    chg = {"E-1": [("2026-06-01T00:00:00Z", "Ops & Maintenance", "Support")], "E-2": [("2026-09-01T00:00:00Z", "", "")]}
    C = ("Epic", "Initiative")
    ok = value_at("E-1", "2026-05-01T00:00:00Z", now, chg) == "Ops & Maintenance"          # before the change: the old value
    ok &= value_at("E-1", "2026-07-01T00:00:00Z", now, chg) == "Support" and value_at("E-1", None, now, chg) == "Support"
    ok &= value_at("E-1", "2026-06-01T23:59:00Z", now, chg) == "Ops & Maintenance"          # AC76: a change on the finish day counts as after it
    ok &= value_at("E-1", "2026-06-02T00:00:00Z", now, chg) == "Support"
    ok &= for_issue({"key": "T-1", "type": "Story", "parent_key": "E-1"}, "2026-05-01T00:00:00Z", now, chg, C) == "Ops & Maintenance"          # a ticket takes the parent's value at its finish date
    ok &= for_issue({"key": "T-2", "type": "Bug", "parent_key": "E-2"}, None, now, chg, C) == ""          # blank parent: blank
    ok &= for_issue({"key": "T-3", "type": "Bug", "parent_key": ""}, None, now, chg, C) == ""          # no parent: blank
    ok &= for_issue({"key": "I-1", "type": "Initiative", "parent_key": ""}, None, now, chg, C) == "Customer Feature"          # a container uses its own
    print("workcat selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    n, c = load(sys.argv[1] if len(sys.argv) > 1 else "data/extracts/jira")
    print(f"{len(n):,} keys, {sum(1 for v in n.values() if v):,} with a value, {len(c):,} keys with changes")
