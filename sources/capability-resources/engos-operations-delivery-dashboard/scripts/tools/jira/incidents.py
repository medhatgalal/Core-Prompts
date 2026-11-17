#!/usr/bin/env python3.14
"""Incident extract (v1.21 AC5a): the incident projects named in data/config.json (jira.incident_projects), status history only.
Own files in data/extracts/jira/incidents/ (never mixed into jira_issues.csv). GET only through tools/jira/jget.py, every call logged to
incidents/jira-calls.log. NO free text, NO assignee, NO assignee id, NO reporter, NO customer field, NO parent: counts and flow only (AC65).
  bash tools/jira/refresh.sh --incidents [--asof 2026-11-11T22:19:35Z]
      as-of = the pull start time unless --asof pins it to an earlier time (an issue updated after the as-of is left out and listed in the gap file); recorded in incidents/as_of.txt
Outputs: jira_incidents.csv (one row per issue), jira_incident_transitions.csv (status history), jira_incident_late_updates.csv (gap),
         as_of.txt, calls.json, jira-calls.log. Written to temp files first, swapped in at the end.
Exit codes: 0 ok; 1 failure; 2 credential, sign-in or IP-block problem.
"""
import sys, os, json, csv, argparse, datetime, importlib.util, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cfg
BASE_OUT = os.environ.get("JIRA_EXTRACT_DIR") or os.path.join(cfg.ROOT, "data", "extracts", "jira")
OUT = os.path.join(BASE_OUT, "incidents"); os.makedirs(OUT, exist_ok=True)
os.environ["JIRA_CALL_LOG"] = os.path.join(OUT, "jira-calls.log")      # logged separately from the main extract
spec = importlib.util.spec_from_file_location("jx", os.path.join(HERE, "extract.py")); jx = importlib.util.module_from_spec(spec); spec.loader.exec_module(jx)
# only these fields are requested: nothing that holds a name, free text or a customer value
FIELDS = "issuetype,status,priority,created,updated,resolution,resolutiondate,statuscategorychangedate,project,%s,%s" % (cfg.CF_GROUP, cfg.CF_TEAM)
HEAD = ["key", "issue_id", "project", "type", "status", "status_category", "priority", "created", "first_start", "final_done", "resolution", "resolution_date", "updated", "group", "team"]
THEAD = ["issue", "from_status", "to_status", "from_category", "to_category", "changed_at"]


def team_name(i):
    """Name of the Atlassian Team on the issue (an org unit). Nothing else from that object is kept."""
    t = (i.get("fields") or {}).get(cfg.CF_TEAM)
    return (t.get("name") or "") if isinstance(t, dict) else (t or "")


def main():
    projects = cfg.INCIDENT_PROJECTS
    if not projects: print("jira incidents: jira.incident_projects is empty in data/config.json", file=sys.stderr); return 1
    ap = argparse.ArgumentParser(); ap.add_argument("--asof", default=""); a = ap.parse_args()
    asof = jx.now()
    if a.asof:
        try: pinned = datetime.datetime.strptime(a.asof, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError: print("jira incidents: --asof must look like 2026-11-11T22:19:35Z", file=sys.stderr); return 1
        if a.asof > asof: print("jira incidents: --asof is in the future", file=sys.stderr); return 1
        asof = a.asof
    open(os.path.join(OUT, "as_of.txt"), "w").write(asof + "\n")
    jql = "project in (%s) AND (statusCategory != Done OR statusCategoryChangedDate >= -365d)" % ", ".join(projects)
    try:
        c = jx.TokenClient()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2
    c.cs = os.path.join(OUT, "calls.json"); c.st = {"calls": 0, "errors": 0, "r429": 0}; c._base = (0, 0, 0)
    cats = {s_["id"]: s_["statusCategory"]["key"] for s_ in c.get("/rest/api/3/status")}   # fresh status-to-category map (one call), kept in memory only
    rows, trows_all, late, tok = [], [], [], None
    try:
        while True:
            q = f"/rest/api/3/search/jql?jql={urllib.parse.quote(jql)}&maxResults=100&expand=changelog&fields={FIELDS}"
            if tok: q += "&nextPageToken=" + urllib.parse.quote(tok)
            d = c.get(q)
            for i in d["issues"]:
                r = jx.slim(i)
                if r["cl_total"] > r["cl_n"]: r["hist"] = jx.full_changelog(c, r["key"]); r["cl_n"] = r["cl_total"]
                if jx.utc(r["updated"]) > asof: late.append([r["key"], jx.utc(r["updated"])]); continue    # changed after the pull started: the gap
                irow, trows, _arows, _acc = jx.convert_issue(r, cats, "open" if r["cat"] != "done" else "done")   # assignee rows and accounts are dropped here
                proj = r["key"].split("-")[0]
                rows.append([r["key"], r["id"], proj, r["type"], r["status"], r["cat"], r["prio"] or "", irow[8], irow[9], irow[11], irow[16], irow[17], irow[13], r["grp"] or "", team_name(i)])
                trows_all += trows
            tok = d.get("nextPageToken")
            if d.get("isLast", not tok) or not tok: break
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        print("jira incidents failed: " + str(e)[:200], file=sys.stderr); return 1
    miss = sum(1 for t in trows_all if not t[3] or not t[4])
    def w(name, head, data):
        p = os.path.join(OUT, name); t = p + ".tmp"
        with open(t, "w", newline="") as fh:
            cw = csv.writer(fh); cw.writerow(head); cw.writerows(data)
        return p, t
    outs = [w("jira_incidents.csv", HEAD, rows), w("jira_incident_transitions.csv", THEAD, trows_all), w("jira_incident_late_updates.csv", ["key", "updated"], late)]
    for p, t in outs: os.replace(t, p)
    jx.jsave(os.path.join(OUT, "calls.json"), c.st)
    per = {p: sum(1 for r in rows if r[2] == p) for p in projects}
    print(f"jira incidents as-of {asof}: rows {per}, transitions {len(trows_all)}, updated after as-of (gap) {len(late)}, unknown-status transitions {miss} (must be 0), calls {c.st['calls']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
