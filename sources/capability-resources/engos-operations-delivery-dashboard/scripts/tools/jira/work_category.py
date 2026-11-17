#!/usr/bin/env python3.14
"""READ-ONLY (GET via jget.py, every call logged). Work Category (select; field id in config) for the jira_wide_1111 keys and their parents, value AT the as-of from the changelog.
Writes data/extracts/work_category_1111/: issues.csv (key, type, project, in_scope, parent_key, parent_type, wc_id_at_asof, wc_value_at_asof, wc_id_now), changes.csv (key, changed_at, from_id, from_value, to_id, to_value).
Ids, keys and option values only: no titles, no text, no people. Usage: python3.14 -I tools/jira/work_category.py 2026-11-11T22:19:35Z"""
import sys, os, csv, json, urllib.parse, importlib.util, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import cfg, jget
T = sys.argv[1]; OUT = os.path.join(cfg.ROOT, "data", "extracts", os.environ.get("WC_OUT", "work_category_1111")); os.makedirs(OUT, exist_ok=True)
os.environ["JIRA_CALL_LOG"] = os.path.join(OUT, "jira-calls.log"); jget.LOG = os.environ["JIRA_CALL_LOG"]
def utc(s): return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
j = jget.JiraGet(base=cfg.API_BASE)
def get(p):
    st, d, raw = j.get(p)
    if st != 200: raise RuntimeError("HTTP %s %s" % (st, p[:60]))
    return d
F = cfg.CF_WC; FIELDS = "issuetype,parent,project,created,%s" % F
def hist_full(key):
    out, start = [], 0
    while True:
        d = get("/rest/api/3/issue/%s/changelog?startAt=%d&maxResults=100" % (key, start)); out += d["values"]; start += len(d["values"])
        if d.get("isLast", start >= d.get("total", 0)): return out
def fetch(keys):
    rows, chg = {}, []
    for i in range(0, len(keys), 100):
        b = keys[i:i + 100]; tok = None
        while True:
            q = "/rest/api/3/search/jql?jql=%s&maxResults=100&expand=changelog&fields=%s" % (urllib.parse.quote("key in (%s)" % ",".join(b)), FIELDS)
            if tok: q += "&nextPageToken=" + urllib.parse.quote(tok)
            d = get(q)
            for it in d["issues"]:
                f = it["fields"]; cl = it.get("changelog") or {}; hs = cl.get("histories", [])
                if cl.get("total", len(hs)) > len(hs): hs = hist_full(it["key"])
                v = f.get(F) if isinstance(f.get(F), dict) else None; p = f.get("parent")
                rows[it["key"]] = {"type": f["issuetype"]["name"], "project": f["project"]["key"], "parent": (p or {}).get("key", ""), "ptype": ((p or {}).get("fields") or {}).get("issuetype", {}).get("name", ""),
                                   "now_id": v.get("id", "") if v else "", "now_val": v.get("value", "") if v else "", "created": utc(f["created"]),
                                   "items": [(utc(h["created"]), x.get("from") or "", x.get("fromString") or "", x.get("to") or "", x.get("toString") or "") for h in hs for x in h["items"] if (x.get("fieldId") or x.get("field")) == F]}
            tok = d.get("nextPageToken")
            if not tok: break
    return rows
scope = [r["key"] for r in csv.DictReader(open(os.path.join(cfg.ROOT, "data", "extracts", os.environ.get("WC_WIDE", "jira_wide_1111"), "jira_issues.csv")))]
rows = fetch(scope)
parents = sorted({r["parent"] for r in rows.values() if r["parent"] and r["parent"] not in rows})
prow = fetch(parents) if parents else {}
allr = dict(prow); allr.update(rows)
# grandparents (Epic -> Initiative) for the parents just read
gp = sorted({r["parent"] for r in prow.values() if r["parent"] and r["parent"] not in allr})
if gp: allr.update(fetch(gp))
def at(r):
    v = (r["now_id"], r["now_val"])
    for t, fi, fs, ti, ts in sorted(r["items"], reverse=True):
        if t > T: v = (fi, fs)
    return v
w1 = lambda name, head, data: (lambda fh: (csv.writer(fh).writerow(head), csv.writer(fh).writerows(data), fh.close()))(open(os.path.join(OUT, name), "w", newline=""))
iss, ch = [], []
for k, r in sorted(allr.items()):
    if r["created"] > T: continue
    wid, wv = at(r); pt = allr.get(r["parent"], {}).get("type", "") if r["parent"] else ""
    iss.append([k, r["type"], r["project"], "Y" if k in rows else "N", r["parent"], pt, wid, wv, r["now_id"]])
    for t, fi, fs, ti, ts in sorted(r["items"]): ch.append([k, t, fi, fs, ti, ts])
with open(os.path.join(OUT, "issues.csv"), "w", newline="") as fh: w = csv.writer(fh); w.writerow(["key","type","project","in_scope","parent_key","parent_type","wc_id_at_asof","wc_value_at_asof","wc_id_now"]); w.writerows(iss)
with open(os.path.join(OUT, "changes.csv"), "w", newline="") as fh: w = csv.writer(fh); w.writerow(["key","changed_at","from_id","from_value","to_id","to_value"]); w.writerows(ch)
open(os.path.join(OUT, "as_of.txt"), "w").write(T + "\n")
print("scope", len(rows), "parents read", len(prow), "grandparents", len(gp), "rows", len(iss), "changes", len(ch), "calls", j.calls)
