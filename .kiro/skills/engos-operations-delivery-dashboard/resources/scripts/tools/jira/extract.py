#!/usr/bin/env python3.14
"""Jira extractor. READ-ONLY (GET only) through the signed-in Atlassian tab of the Home browser (CDP 9222).
No model call. No free text stored (no summaries, descriptions, comments, labels).
Usage: extract.py pull [open|done]   (checkpointed, resumable)   |   extract.py build   (CSVs from checkpoints)
Run with: /opt/homebrew/opt/python@3.14/bin/python3.14 -I tools/jira/extract.py ...
"""
import sys, os, json, time, csv, datetime, glob, urllib.parse
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.environ.get("JIRA_EXTRACT_DIR") or os.path.join(ROOT, "data", "extracts", "jira"); CK = os.path.join(OUT, "checkpoints")
os.makedirs(CK, exist_ok=True)
BASE = cfg.BASE
BUDGET = 5000
CODE_TYPES = {"Story", "Task", "Bug"}   # lead ruling A5; Technical Debt = no_code_expected until the user answers
CF_WC = cfg.CF_WC   # Work Category (select). Kept OUT of jira_issues.csv: it goes to the side files jira_work_category*.csv (incremental.py)
FIELDS = "issuetype,status,assignee,priority,created,updated,resolution,resolutiondate,parent,%s,%s,statuscategorychangedate,%s" % (cfg.CF_MR, cfg.CF_GROUP, CF_WC)
JQLS = {  # pulls; the as-of cut is applied client-side (updated <= as-of) so no JQL timezone ambiguity
    "open": "filter = %d AND statusCategory != Done" % cfg.F_OPEN,
    "done": "filter = %d AND statusCategory = Done" % cfg.F_DASH,
}
def now(): return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
def utc(s):
    if not s: return ""
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
def jload(p, d=None):
    try: return json.load(open(p))
    except Exception: return d
def jsave(p, o):
    t = p + ".tmp"; json.dump(o, open(t, "w")); os.replace(t, p)

class Client:
    def __init__(self, pw):
        b = pw.chromium.connect_over_cdp("http://localhost:9222")
        self.pg = b.contexts[0].new_page()
        u = BASE + "/jira/filters"
        open(os.path.join(ROOT, "crew/agents/jira/nav.log"), "a").write(f"{now()} {u} (extract.py: then GET only)\n")
        self.pg.goto(u, wait_until="domcontentloaded"); self.pg.wait_for_timeout(2500)
        self.cs = os.path.join(OUT, "calls.json"); self.st = jload(self.cs, {"calls": 150, "note": "150 seeded = conservative estimate for earlier spike calls incl. the killed paginate", "errors": 0, "r429": 0})
    def get(self, path):
        for attempt in range(6):
            if self.st["calls"] >= BUDGET: raise SystemExit("BUDGET REACHED")
            s, ra, body = self.pg.evaluate("async u => {const r = await fetch(u,{headers:{Accept:'application/json'}}); return [r.status, r.headers.get('retry-after'), await r.text()]}", path)
            self.st["calls"] += 1; jsave(self.cs, self.st)
            try:
                import jget; jget.log_call(path, s)
            except Exception: pass
            if s == 200: return json.loads(body)
            if s == 429 or (s == 403 and ra):
                self.st["r429"] += 1; time.sleep(min(float(ra or 10) * (attempt + 1), 120)); continue
            if s >= 500 or s == 0: time.sleep(5 * (attempt + 1)); continue
            self.st["errors"] += 1; jsave(self.cs, self.st); raise RuntimeError(f"HTTP {s} {path[:80]}: {body[:200]}")
        self.st["errors"] += 1; jsave(self.cs, self.st); raise RuntimeError("retries exhausted " + path[:80])

class TokenClient:
    """Default client: GET-only Jira calls with the user's API token (tools/jira/jget.py, logged to jira-calls.log). No browser, no call cap.
    Same interface as Client. Exit 2 with a plain message when the credential is missing or rejected."""
    class _P:
        def close(self): pass
    pg = _P()
    def __init__(self):
        import jget
        try: self.j = jget.JiraGet(base=cfg.API_BASE)
        except jget.NoAuth as e: print("jira: " + str(e), file=sys.stderr); sys.exit(2)
        self.cs = os.path.join(OUT, "calls.json"); self.st = jload(self.cs, {"calls": 0, "errors": 0, "r429": 0})
        self._base = (self.st["calls"], self.st["errors"], self.st["r429"])
    def get(self, path):
        st, d, raw = self.j.get(path)
        self.st["calls"] = self._base[0] + self.j.calls; self.st["errors"] = self._base[1] + self.j.errors; self.st["r429"] = self._base[2] + self.j.r429
        jsave(self.cs, self.st)
        if st == 200: return d
        if st in (401, 403):
            print("jira returned %d: %s" % (st, "the API token or account email in the environment was rejected" if st == 401 else self.j._scrub(raw)[:160]), file=sys.stderr); sys.exit(2)
        raise RuntimeError(f"HTTP {st} {path[:80]}")

import contextlib
@contextlib.contextmanager
def client_ctx():
    """Token client by default; JIRA_BROWSER=1 opts in to the signed-in Home browser instead."""
    if os.environ.get("JIRA_BROWSER") == "1":
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            c = Client(pw)
            try: yield c
            finally: c.pg.close()
    else:
        yield TokenClient()

def wc_items(histories):
    """Work Category changelog items only: (changed_at, from_id, from_value, to_id, to_value). Ids and option values, no free text."""
    return [(h["created"], it.get("from") or "", it.get("fromString") or "", it.get("to") or "", it.get("toString") or "")
            for h in histories for it in h["items"] if (it.get("fieldId") or "") == CF_WC or it.get("field") == "Work Category"]

def slim(i):
    f = i["fields"]; ch = i.get("changelog", {})
    st, asg, par = f.get("status") or {}, f.get("assignee"), f.get("parent")
    hist = []
    for h in ch.get("histories", []):
        its = [{"f": it["field"], "from": it.get("from"), "to": it.get("to"), "fs": it.get("fromString"), "ts": it.get("toString")}
               for it in h["items"] if it["field"] in ("status", "assignee")]
        if its: hist.append({"at": h["created"], "items": its})
    kh = [(it.get("fromString"), it.get("toString")) for h in ch.get("histories", []) for it in h["items"] if it["field"] == "Key"]
    wcv = f.get(CF_WC) if isinstance(f.get(CF_WC), dict) else None
    return {"wc": [wcv.get("id", ""), wcv.get("value", "")] if wcv else ["", ""], "wch": wc_items(ch.get("histories", [])),
            "id": i.get("id"), "kh": kh, "key": i["key"], "type": (f.get("issuetype") or {}).get("name"), "status": st.get("name"), "status_id": st.get("id"),
            "cat": (st.get("statusCategory") or {}).get("key"),
            "asg": asg and asg.get("accountId"), "asg_name": asg and asg.get("displayName"),
            "prio": (f.get("priority") or {}).get("name"), "created": f.get("created"), "updated": f.get("updated"),
            "res": (f.get("resolution") or {}).get("name"), "resdate": f.get("resolutiondate"), "scc": f.get("statuscategorychangedate"),
            "parent": par and par.get("key"), "mr": f.get(cfg.CF_MR) not in (None, "", []),
            "grp": (f.get(cfg.CF_GROUP) or {}).get("value") if isinstance(f.get(cfg.CF_GROUP), dict) else f.get(cfg.CF_GROUP),
            "cl_total": ch.get("total", 0), "cl_n": len(ch.get("histories", [])), "hist": hist}

def pull(which):
    with client_ctx() as c:
        sp = os.path.join(CK, f"{which}_state.json"); s = jload(sp, {"token": None, "page": 0, "done": False, "started": now()})
        if s["done"]: print(which, "already complete"); return
        while True:
            q = f"/rest/api/3/search/jql?jql={urllib.parse.quote(JQLS[which])}&maxResults=100&expand=changelog&fields={FIELDS}"
            if s["token"]: q += "&nextPageToken=" + urllib.parse.quote(s["token"])
            d = c.get(q)
            rows = [slim(i) for i in d["issues"]]
            for r in rows:   # changelog truncated on the search page: fetch the rest
                if r["cl_total"] > r["cl_n"]:
                    r["hist"] = full_changelog(c, r["key"]); r["cl_n"] = r["cl_total"]; r["full_fetch"] = True
            s["page"] += 1
            with open(os.path.join(CK, f"{which}_{s['page']:04d}.jsonl"), "w") as fh:
                for r in rows: fh.write(json.dumps(r) + "\n")
            s["token"] = d.get("nextPageToken"); s["done"] = d.get("isLast", not s["token"]) or not s["token"]
            jsave(sp, s); print(now(), which, "page", s["page"], len(rows), "calls", c.st["calls"], flush=True)
            if s["done"]: break
            time.sleep(0.2)
        c.pg.close()

def full_changelog(c, key, with_keys=False, wc=None):
    out, kh, start = [], [], 0
    while True:
        d = c.get(f"/rest/api/3/issue/{key}/changelog?startAt={start}&maxResults=100")
        for h in d["values"]:
            its = [{"f": it["field"], "from": it.get("from"), "to": it.get("to"), "fs": it.get("fromString"), "ts": it.get("toString")}
                   for it in h["items"] if it["field"] in ("status", "assignee")]
            kh += [(it.get("fromString"), it.get("toString")) for it in h["items"] if it["field"] == "Key"]
            if wc is not None: wc += wc_items([h])
            if its: out.append({"at": h["created"], "items": its})
        start += len(d["values"])
        if d.get("isLast", start >= d.get("total", 0)): return (out, kh) if with_keys else out

def strict_final_done(moves, cat_now, scc_utc=""):
    """STRICT final Done (user ruling D126). moves = [(changed_at, from_category, to_category)] oldest first, status changes only.
    final_done = the time of the move INTO the Done category from a NOT-Done category, the last such move (a reopen then Done
    counts from the Done after the reopen). A Done-to-Done move (for example Done to Closed) does NOT reset the date. An item that
    never left Done after its first Done entry keeps that first entry. No move into Done at all: the status-category-changed date."""
    if cat_now != "done": return "", "none"
    into = [m for m in moves if m[2] == "done"]
    real = [m for m in into if m[1] != "done"]
    if real: return real[-1][0], "changelog"
    if into: return into[0][0], "changelog"
    if scc_utc: return scc_utc, "statuscategorychangedate"
    return "", "none"


def convert_issue(r, cats, pop):
    """One slim() record (with full changelog) -> (issue row, transition rows, assignee-change rows, {account id: name}).
    Shared by the full build and the incremental merge so both derive every column the same way."""
    u = utc(r["updated"]); accts = {}
    hist = sorted(r["hist"], key=lambda h: h["at"])
    st, ac = [], []
    for h in hist:
        at = utc(h["at"])
        for it in h["items"]:
            if it["f"] == "status":
                st.append((at, it["from"], it["to"], it["fs"], it["ts"]))
            else:
                ac.append((at, it["from"], it["to"]))
                for i, n in ((it["from"], it["fs"]), (it["to"], it["ts"])):
                    if i and n: accts.setdefault(i, n)
    if r["asg"]: accts.setdefault(r["asg"], r["asg_name"])
    trows = [[r["key"], fs, ts, cats.get(f, ""), cats.get(t, ""), at] for at, f, t, fs, ts in st]
    arows = [[r["key"], at, f or "", t or ""] for at, f, t in ac]
    first_start, basis = "", ""
    for at, f, t, fs, ts in st:
        if cats.get(t) == "indeterminate": first_start, basis = at, "in_progress"; break
    if not first_start:
        for at, f, t, fs, ts in st:
            if cats.get(f) == "new" and cats.get(t) != "new": first_start, basis = at, "skip_in_progress"; break
    final_done, fsrc = strict_final_done([(at, cats.get(f, ""), cats.get(t, "")) for at, f, t, fs, ts in st], r["cat"], utc(r["scc"]) if r["scc"] else "")
    # assignee at the moment of final Done: last assignee change at or before it, else the first change's "from", else current
    a_done = ""
    if final_done:
        prior = [x for x in ac if x[0] <= final_done]
        if prior: a_done = prior[-1][2] or ""
        elif ac: a_done = ac[0][1] or ""
        else: a_done = r["asg"] or ""
    irow = [r["key"], r["type"], "Y" if r["type"] in CODE_TYPES else "N", r["status"], r["cat"], r["asg"] or "",
            a_done, r["prio"] or "", utc(r["created"]), first_start, basis, final_done, fsrc, u, r["parent"] or "",
            "Y" if r["mr"] else "N", r["res"] or "", utc(r["resdate"]), r["grp"] or "", pop, r["cl_total"]]
    return irow, trows, arows, accts

def build():
    asof = open(os.path.join(OUT, "as_of.txt")).read().strip()
    catp = os.path.join(OUT, "status_categories.json")
    cats = jload(catp)
    if cats is None:
        with client_ctx() as c:
            cats = {s["id"]: s["statusCategory"]["key"] for s in c.get("/rest/api/3/status")}
        jsave(catp, cats)
    issues, trans, achg, accts, late, idrows = [], [], [], {}, [], []
    seen = set()
    for pop in ("open", "done"):
        for fp in sorted(glob.glob(os.path.join(CK, f"{pop}_0*.jsonl"))):
            for ln in open(fp):
                r = json.loads(ln)
                if r["key"] in seen: continue
                seen.add(r["key"]); u = utc(r["updated"])
                if u > asof: late.append((r["key"], u)); continue
                irow, trows, arows, acc = convert_issue(r, cats, pop)
                if r.get("id"): idrows.append([r["id"], r["key"]])
                issues.append(irow); trans.extend(trows); achg.extend(arows)
                for k_, v_ in acc.items(): accts.setdefault(k_, v_)
    def w(name, head, rows):
        with open(os.path.join(OUT, name), "w", newline="") as fh:
            cw = csv.writer(fh); cw.writerow(head); cw.writerows(rows)
    w("jira_issues.csv", ["key","type","code_type_flag","status","status_category","assignee_id","assignee_id_at_final_done","priority","created","first_start","first_start_basis","final_done","final_done_source","updated","parent_key","mr_field_present","resolution","resolution_date",cfg.GROUP_COL,"population","changelog_total"], issues)
    w("jira_transitions.csv", ["issue","from_status","to_status","from_category","to_category","changed_at"], trans)
    if idrows: w("jira_issue_ids.csv", ["issue_id","key"], idrows)   # stable id for every issue, so the incremental never depends on a partial map
    w("jira_assignee_changes.csv", ["issue","changed_at","from_assignee_id","to_assignee_id"], achg)
    w("jira_accounts.csv", ["assignee_id","display_name"], sorted(accts.items()))
    w("jira_late_updates.csv", ["key","updated"], late)
    print("issues", len(issues), "transitions", len(trans), "assignee_changes", len(achg), "accounts", len(accts), "late(updated>as_of)", len(late))

if __name__ == "__main__":
    if sys.argv[1] == "pull": pull(sys.argv[2])
    elif sys.argv[1] == "build": build()
