#!/usr/bin/env python3.14
"""Jira incremental pull (AC36a). Plain shell, no agent, no model call. READ-ONLY GETs with the user's Jira API token from the environment
(variable names in data/config.json jira.auth; GET-only wrapper tools/jira/jget.py). No browser needed. Opt-in fallback: --browser reads through the
signed-in Atlassian tab of the Home browser (CDP 9222).

  bash tools/jira/refresh.sh --incremental --asof 2026-11-11T11:00:00Z

Pulls every issue in the dashboard scope (open items in the open-items filter, plus the dashboard filter) updated since the cursor
(minus a 1-hour overlap), with changelog. Upserts by stable Jira issue id into the saved CSVs; renames (changelog Key field) go into
key_aliases.csv; transitions are appended only when new. All outputs are written to temp files first and swapped in at the end, so a
failure leaves the saved CSVs untouched. cursor.json is written only after every swap succeeded.

Exit codes: 0 ok; 1 failure; 2 credential / sign-in / IP-block / network problem (plain message says what to fix: missing variable, 401, 403, IP block).
Env JIRA_EXTRACT_DIR points at a copy of data/extracts/jira (used by the tests).
Run with: /opt/homebrew/opt/python@3.14/bin/python3.14 -I tools/jira/incremental.py --incremental --asof <utc>
"""
import sys, os, json, csv, argparse, datetime, importlib.util, urllib.parse, zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cfg
for _i, _a in enumerate(sys.argv):   # --data-dir DIR is the same as JIRA_EXTRACT_DIR=DIR (tests on a copy)
    if _a == "--data-dir" and _i + 1 < len(sys.argv): os.environ["JIRA_EXTRACT_DIR"] = os.path.abspath(sys.argv[_i + 1])
spec = importlib.util.spec_from_file_location("jx", os.path.join(HERE, "extract.py"))
jx = importlib.util.module_from_spec(spec); spec.loader.exec_module(jx)
OUT = jx.OUT
TZ = zoneinfo.ZoneInfo("America/New_York")   # JQL date strings are read in the Jira user's time zone
FMT = "%Y-%m-%dT%H:%M:%SZ"
CONTAINERS = ("Epic", "Initiative")
ISSUE_HEAD = ["key","type","code_type_flag","status","status_category","assignee_id","assignee_id_at_final_done","priority","created","first_start","first_start_basis","final_done","final_done_source","updated","parent_key","mr_field_present","resolution","resolution_date",cfg.GROUP_COL,"population","changelog_total"]
TRANS_HEAD = ["issue","from_status","to_status","from_category","to_category","changed_at"]
ACHG_HEAD = ["issue","changed_at","from_assignee_id","to_assignee_id"]
ACCT_HEAD = ["assignee_id","display_name"]
WC_HEAD = ["key","type","wc_id","wc_value"]                             # side file: Work Category as of the last pull, one row per kept issue and per parent of a kept issue
WCC_HEAD = ["key","changed_at","from_id","from_value","to_id","to_value"]   # side file: its changelog items
WC_FILE, WCC_FILE = "jira_work_category.csv", "jira_work_category_changes.csv"
JOIN_FILE = "jira_work_category_join.csv"
JOIN_HEAD = ["key","parent_key","basis","wc_id","wc_value"]   # basis: epic_set | epic_blank | no_parent | parent_not_epic | parent_unread
# Xray types never appear in the main extract (filters exclude them; the build drops them). If one ever does, the run fails rather than carrying them silently.
XRAY_TYPES = {"Xray Test", "Test Execution", "Xray Test Plan", "Test Set", "Precondition", "Sub Test Execution", "Test Case", "Test Plan", "Test"}

def wc_at(chg_rows, now_row, t):
    """(id, value) of Work Category at finish time t (UTC ISO; '' = now): the current value with every later change undone, latest first.
    AC76 day rule: a change made ON the finish day (UTC date) counts as AFTER the finish, so it is undone."""
    v = (now_row[2], now_row[3])
    if t:
        for c in sorted(chg_rows, key=lambda c: c[1], reverse=True):
            if c[1][:10] >= t[:10]: v = (c[2], c[3])
    return v

def wc_join(issues, wc_rows, wc_chg):
    """One row per non-container ticket: its parent Epic and that Epic's Work Category at the ticket's finish date (now if not Done)."""
    ix = {h: i for i, h in enumerate(ISSUE_HEAD)}; out = []
    for r in sorted(issues, key=lambda r: r[0]):
        if r[ix["type"]] in CONTAINERS: continue
        pk = r[ix["parent_key"]]
        if not pk: out.append([r[0], "", "no_parent", "", ""]); continue
        p = wc_rows.get(pk)
        if p is None: out.append([r[0], pk, "parent_unread", "", ""]); continue
        if p[1] != "Epic": out.append([r[0], pk, "parent_not_epic", "", ""]); continue
        t = r[ix["final_done"]] if r[ix["status_category"]] == "done" else ""
        i_, v_ = wc_at(wc_chg.get(pk, []), p, t)
        out.append([r[0], pk, "epic_set" if i_ else "epic_blank", i_, v_])
    return out

def wc_fetch_parents(c, keys):
    """Read parent Epics (or any parent) by key: ids, type, Work Category and its changelog items. Test hook: JIRA_INCR_WC_PARENTS=json {key: {type, wc, wch}}."""
    fx = os.environ.get("JIRA_INCR_WC_PARENTS")
    if fx: d = json.load(open(fx)); return {k: d[k] for k in keys if k in d}
    out = {}
    for i in range(0, len(keys), 100):
        b = keys[i:i + 100]; tok = None
        while True:
            q = f"/rest/api/3/search/jql?jql={urllib.parse.quote('key in (%s)' % ','.join(b))}&maxResults=100&expand=changelog&fields=issuetype,{jx.CF_WC}" + ("&nextPageToken=" + urllib.parse.quote(tok) if tok else "")
            d = c.get(q)
            for it in d["issues"]:
                f = it["fields"]; ch = it.get("changelog", {}); hs = ch.get("histories", [])
                v = f.get(jx.CF_WC) if isinstance(f.get(jx.CF_WC), dict) else None
                w = jx.wc_items(hs)
                if ch.get("total", len(hs)) > len(hs):
                    w = []; jx.full_changelog(c, it["key"], wc=w)
                out[it["key"]] = {"type": f["issuetype"]["name"], "wc": [v.get("id", ""), v.get("value", "")] if v else ["", ""], "wch": w}
            tok = d.get("nextPageToken")
            if d.get("isLast", not tok) or not tok: break
    return out
IDS_HEAD = ["issue_id","key"]


class Fail(Exception):
    def __init__(self, msg, code=1): super().__init__(msg); self.code = code


class TokenClient:
    """Default path: GET-only Jira client with the user's API token from the environment (no browser). Interface of jx.Client."""
    class _P:
        def close(self): pass
    pg = _P()
    def __init__(self):
        import jget
        try: self.j = jget.JiraGet(base=cfg.API_BASE)
        except jget.NoAuth as e: raise Fail(str(e), 2)
        self.cs = os.path.join(OUT, "calls_incremental_run.json")
    @property
    def st(self): return {"calls": self.j.calls, "errors": self.j.errors, "r429": self.j.r429}
    def get(self, path):
        st, d, raw = self.j.get(path)
        if st == 200: return d
        body = self.j._scrub(raw)[:160].replace("\n", " ")
        if st == 401: raise Fail("Jira returned 401: the Jira API token or account email in the environment is wrong or expired (if it is a scoped token, set jira.api_base in data/config.json to https://api.atlassian.com/ex/jira/<cloudId>)", 2)
        if st == 403 and "IP" in raw: raise Fail("Jira blocked this machine's IP address (403: %s): ask the Atlassian admin to allow it, or use --browser" % body, 2)
        if st == 403: raise Fail("Jira returned 403: the token has no permission for this call (%s)" % body, 2)
        raise RuntimeError(f"HTTP {st} {path[:80]}: {body}")



def read_csv(name):
    p = os.path.join(OUT, name)
    if not os.path.exists(p): return None, []
    with open(p, newline="") as fh:
        r = list(csv.reader(fh))
    return (r[0] if r else None), r[1:]


def parse_utc(s):
    return datetime.datetime.strptime(s, FMT).replace(tzinfo=datetime.UTC)


def run(asof_s, browser=False):
    asof = parse_utc(asof_s)
    cur_p = os.path.join(OUT, "cursor.json")
    cur = jx.jload(cur_p)
    note = ""
    if cur and cur.get("cursor"): cursor = parse_utc(cur["cursor"])
    else:
        cursor = parse_utc(open(os.path.join(OUT, "as_of.txt")).read().strip())
        note = " (no cursor.json yet: starting from the saved extract's as-of)"
    if asof < cursor: raise Fail(f"--asof {asof_s} is before the cursor {cursor.strftime(FMT)}")
    gap = (asof - cursor).days
    if gap > 365: raise Fail(f"gap of {gap} days is over 365: run the full Jira refresh (bash tools/jira/refresh.sh)")
    if gap > 30: print(f"large gap: {gap} days; this will take about as long as a full pull", flush=True)
    start = (cursor - datetime.timedelta(hours=1)).astimezone(TZ).strftime("%Y/%m/%d %H:%M")
    # the third clause also catches epics/initiatives that left the open-items filter (for example Done with no resolution), so they can be dropped
    scope = 'SBU = Automation OR cf[%s] in (%s)' % (cfg.CF_GROUP.split("_")[1], ", ".join('"%s"' % v for v in sorted(cfg.SCOPE_GROUPS)))
    jql = f'(filter = {cfg.F_OPEN} OR filter = {cfg.F_DASH} OR (issuetype in ({", ".join(CONTAINERS)}) AND ({scope}))) AND updated >= "{start}"'

    # ---- load saved state
    ihead, issues = read_csv("jira_issues.csv")
    if ihead != ISSUE_HEAD: raise Fail("jira_issues.csv is missing or has an unexpected header: run the full Jira refresh")
    _, trans = read_csv("jira_transitions.csv"); _, achg = read_csv("jira_assignee_changes.csv")
    _, accts = read_csv("jira_accounts.csv"); ahead, aliases = read_csv("key_aliases.csv")
    _, ids = read_csv("jira_issue_ids.csv")
    cats = jx.jload(os.path.join(OUT, "status_categories.json"))
    if cats is None: raise Fail("status_categories.json is missing: run the full Jira refresh")
    # Work Category side files. Written only when jira_work_category.csv already exists (the one-time backfill creates it), so a partial file never appears.
    wc_on = os.path.exists(os.path.join(OUT, WC_FILE))
    wc_rows = {r[0]: r for r in read_csv(WC_FILE)[1]} if wc_on else {}
    wc_chg = {}
    for r_ in (read_csv(WCC_FILE)[1] if wc_on else []): wc_chg.setdefault(r_[0], []).append(r_)
    by_key = {r[0]: i for i, r in enumerate(issues)}
    id_to_keys = {}
    for r_ in ids: id_to_keys.setdefault(r_[0], []).append(r_[1])
    acct = {r[0]: r[1] for r in accts}
    from collections import Counter
    tkey = lambda r_: (r_[0], r_[5], r_[1], r_[2]); akey = lambda r_: (r_[0], r_[1], r_[2], r_[3])
    tcnt = Counter(tkey(r_) for r_ in trans); acnt = Counter(akey(r_) for r_ in achg)   # counts, not sets: a repeated identical row is real and stays
    alias_by_old = {r[0]: i for i, r in enumerate(aliases)} if aliases else {}
    new_to_old = {}
    for r_ in aliases or []:   # an old key that Jira (or the alias map) says is now another key: a stored row under the old key is the same issue
        if len(r_) > 2 and r_[1] and r_[0] != r_[1] and r_[2] not in ("not_found", "none"): new_to_old.setdefault(r_[1], []).append(r_[0])

    # ---- pull
    from playwright.sync_api import sync_playwright
    calls_p = os.path.join(OUT, "calls_incremental.json")
    pw_cm = None
    moved = {}   # old key -> current key, for every rename or fold this run (children point at the old key until re-pointed)
    aliases_touched = False
    stats = dict(parents_read=0, pulled=0, added=0, updated=0, unchanged=0, renamed=0, dropped=0, later_than_asof=0, folded=0, parents_repointed=0)
    try:
        fixture = os.environ.get("JIRA_INCR_FIXTURE")   # test only: merge these saved slim() records instead of calling Jira
        if fixture:
            class _P:
                def close(self): pass
            class _C:
                pg = _P(); cs = os.path.join(OUT, "calls_incremental_run.json"); st = {"calls": 0, "errors": 0, "r429": 0}
            c = _C(); incoming = json.load(open(fixture))
        else:
            if browser:   # opt-in fallback: the signed-in Atlassian tab of the Home browser
                pw_cm = sync_playwright()
                pw = pw_cm.__enter__()
                try:
                    c = jx.Client(pw)
                except Exception as e:
                    raise Fail("Jira: cannot reach the Home browser on port 9222 or open Jira: start it and sign in to Atlassian (%s)" % str(e)[:80], 2)
                if "login" in c.pg.url or "id.atlassian" in c.pg.url:
                    raise Fail("Jira: the Atlassian tab is not signed in: sign in to Atlassian in the Home browser", 2)
                c.cs = os.path.join(OUT, "calls_incremental_run.json"); c.st = {"calls": 0, "errors": 0, "r429": 0}
                jx.BUDGET = 10 ** 12   # no call cap on incremental runs
            else:
                c = TokenClient()
            token, incoming = None, []
            while True:
                q = f"/rest/api/3/search/jql?jql={urllib.parse.quote(jql)}&maxResults=100&expand=changelog&fields={jx.FIELDS}"
                if token: q += "&nextPageToken=" + urllib.parse.quote(token)
                try: d = c.get(q)
                except RuntimeError as e:
                    if "HTTP 401" in str(e) or "HTTP 403" in str(e):
                        raise Fail("Jira returned %s: sign in to Atlassian in the Home browser" % str(e).split()[1], 2)
                    raise
                for i in d["issues"]:
                    r = jx.slim(i)
                    if r["cl_total"] > r["cl_n"]:
                        wch2 = []
                        r["hist"], kh2 = jx.full_changelog(c, r["key"], with_keys=True, wc=wch2); r["kh"] = kh2; r["cl_n"] = r["cl_total"]; r["wch"] = wch2
                    incoming.append(r)
                token = d.get("nextPageToken")
                if d.get("isLast", not token) or not token: break
        stats["pulled"] = len(incoming)

        # ---- merge (in memory)
        new_aliases = []
        extra_acct = {}
        for r in incoming:
            if jx.utc(r["updated"]) > asof_s: stats["later_than_asof"] += 1; continue   # next run's overlap picks it up
            # which stored rows are this issue? by its key, by the stable issue id, by the changelog Key field, by the alias map
            cands = []
            def _add(k):
                if k and k in by_key and k not in cands: cands.append(k)
            _add(r["key"])
            for k_ in id_to_keys.get(r["id"], []): _add(k_)
            for pair in r.get("kh", []):
                for k_ in pair: _add(k_)
            for k_ in new_to_old.get(r["key"], []): _add(k_)
            cur_key = cands[0] if cands else None
            extras = cands[1:]
            if r["cat"] == "done" and r["type"] in CONTAINERS:   # done epics/initiatives are not part of the extract
                for k_ in cands:
                    idx = by_key.pop(k_); issues[idx] = None
                if cands: stats["dropped"] += 1
                wc_rows[r["key"]] = [r["key"], r["type"] or ""] + list(r.get("wc") or ["", ""])   # a dropped Epic can still be somebody's parent: keep its category current
                wc_chg[r["key"]] = [[r["key"]] + [jx.utc(w_[0])] + list(w_[1:]) for w_ in sorted(r.get("wch") or [])]
                continue
            pop = "open" if r["cat"] != "done" else "done"
            irow, trows, arows, acc = jx.convert_issue(r, cats, pop)
            irow = [str(x) for x in irow]
            for k_ in extras: moved[k_] = r["key"]
            if cur_key is not None and cur_key != r["key"]: moved[cur_key] = r["key"]
            for k_ in extras:   # the same issue is stored under another key too: drop that row and its history rows (the pulled history below restores what belongs)
                issues[by_key.pop(k_)] = None; stats["folded"] += 1
                trans[:] = [x for x in trans if x[0] != k_]; achg[:] = [x for x in achg if x[0] != k_]
                tcnt = Counter(tkey(x) for x in trans); acnt = Counter(akey(x) for x in achg)
            if cur_key is not None and cur_key != r["key"]:   # stored under an old key: re-key it
                stats["renamed"] += 1
                for row in trans + achg:
                    if row[0] == cur_key: row[0] = r["key"]
                tcnt = Counter(tkey(x) for x in trans); acnt = Counter(akey(x) for x in achg)
                by_key[r["key"]] = by_key.pop(cur_key)
            for old in {x for pair in r.get("kh", []) for x in pair if x and x != r["key"]} | (({cur_key} if cur_key and cur_key != r["key"] else set()) | set(extras)):
                row = [old, r["key"], "jira_resolved", asof_s, "in_extract", r["type"] or "", r["grp"] or "", ""]
                if old not in alias_by_old and old not in {a[0] for a in new_aliases}: new_aliases.append(row)
                elif old in alias_by_old and aliases[alias_by_old[old]][1] != r["key"]:
                    aliases[alias_by_old[old]][:8] = row; aliases_touched = True   # an earlier not_found/other row for this old key is now answered
            for k_ in cands:   # Work Category follows the issue: old keys give way to the current one
                if k_ != r["key"]: wc_rows.pop(k_, None); wc_chg.pop(k_, None)
            wc_rows[r["key"]] = [r["key"], r["type"] or ""] + list(r.get("wc") or ["", ""])
            wc_chg[r["key"]] = [[r["key"]] + [jx.utc(w_[0])] + list(w_[1:]) for w_ in sorted(r.get("wch") or [])]
            if r["key"] in by_key:
                idx = by_key[r["key"]]
                if issues[idx] != irow: issues[idx] = irow; stats["updated"] += 1
                else: stats["unchanged"] += 1
            else:
                by_key[r["key"]] = len(issues); issues.append(irow); stats["added"] += 1
            for rows_, store, cnt, kf in ((trows, trans, tcnt, tkey), (arows, achg, acnt, akey)):
                want = Counter(kf(x) for x in rows_); seen_n = Counter()
                for x in rows_:
                    k = kf(x); seen_n[k] += 1
                    if seen_n[k] > cnt[k]: store.append([str(y) for y in x]); cnt[k] += 1   # only rows beyond what is already stored
            for k_, v_ in acc.items():
                if k_ not in acct: acct[k_] = v_
            if r["id"]: id_to_keys[r["id"]] = [r["key"]]   # one issue, one current key
        issues = [x for x in issues if x is not None]
        if moved:   # a child still pointing at a parent's old key is re-pointed to the parent's current key
            pi = ISSUE_HEAD.index("parent_key")
            final = {}
            for o_, n_ in moved.items():
                while n_ in moved and moved[n_] != n_: n_ = moved[n_]
                final[o_] = n_
            for row in issues:
                if row[pi] in final: row[pi] = final[row[pi]]; stats["parents_repointed"] += 1
        if wc_on:   # parents of kept tickets that have no row yet (a new Epic): read them by key
            need = sorted({r_[ISSUE_HEAD.index("parent_key")] for r_ in issues if r_[ISSUE_HEAD.index("parent_key")]} - set(wc_rows))
            for k_, d_ in (wc_fetch_parents(c, need) if need else {}).items():
                wc_rows[k_] = [k_, d_["type"]] + list(d_["wc"]); wc_chg[k_] = [[k_] + [jx.utc(w_[0])] + list(w_[1:]) for w_ in sorted(d_["wch"])]
            stats["parents_read"] = len(need)
        c.pg.close()
    except Fail: raise
    except SystemExit: raise
    except Exception as e:
        msg = str(e)
        if browser and ("connect" in msg.lower() or "ECONNREFUSED" in msg or "9222" in msg):
            raise Fail("Jira: cannot reach the Home browser on port 9222: start it and sign in to Atlassian", 2)
        raise Fail("Jira pull failed: " + msg[:200])
    finally:
        try:
            if pw_cm is not None: pw_cm.__exit__(None, None, None)
        except Exception: pass

    xr = sorted({r_[ISSUE_HEAD.index("type")] for r_ in issues} & XRAY_TYPES)
    if xr: raise Fail("the main extract must hold no Xray types, but found: %s (the filters or the build changed: do not carry them)" % ", ".join(xr))
    # ---- write temp files, then swap (nothing is replaced unless every temp was written)
    def temp(name, head, rows):
        p = os.path.join(OUT, name); t = p + ".incr.tmp"
        with open(t, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(head); w.writerows(rows)
        return p, t
    live_keys = {r_[0] for r_ in issues}
    ids_rows = sorted(([i_, k_] for i_, ks_ in id_to_keys.items() for k_ in dict.fromkeys(ks_) if k_ in live_keys), key=lambda x: (int(x[0]) if x[0].isdigit() else 0, x[1]))
    outs = [temp("jira_issues.csv", ISSUE_HEAD, issues), temp("jira_transitions.csv", TRANS_HEAD, trans),
            temp("jira_assignee_changes.csv", ACHG_HEAD, achg),
            temp("jira_accounts.csv", ACCT_HEAD, sorted(acct.items())),
            temp("jira_issue_ids.csv", IDS_HEAD, ids_rows)]
    if wc_on:
        keep = {r_[0] for r_ in issues} | {r_[ISSUE_HEAD.index("parent_key")] for r_ in issues if r_[ISSUE_HEAD.index("parent_key")]}
        outs.append(temp(WC_FILE, WC_HEAD, [wc_rows[k] for k in sorted(wc_rows) if k in keep]))
        outs.append(temp(WCC_FILE, WCC_HEAD, [x for k in sorted(wc_chg) if k in keep for x in wc_chg[k]]))
        outs.append(temp(JOIN_FILE, JOIN_HEAD, wc_join(issues, wc_rows, wc_chg)))
    if (new_aliases or aliases_touched) and ahead is not None:
        out_rows = []
        for r in aliases + [x for x in new_aliases]:
            out_rows.append(r + [""] * (len(ahead) - len(r)))
        outs.append(temp("key_aliases.csv", ahead, out_rows))
    changed = []
    for p, t in outs:
        same = os.path.exists(p) and open(p, "rb").read() == open(t, "rb").read()
        if same: os.remove(t)
        else: os.replace(t, p); changed.append(os.path.basename(p))
    calls = c.st["calls"]
    summary = {"asof": asof_s, "cursor_used": cursor.strftime(FMT), "jql_from": start, "calls": calls, "errors": c.st["errors"], "r429": c.st["r429"],
               **stats, "files_changed": changed, "finished_at": jx.now()}
    jx.jsave(calls_p, summary)
    if os.path.exists(c.cs): os.remove(c.cs)
    jx.jsave(cur_p, {"cursor": asof_s, "written_at": jx.now()})     # only now: every swap succeeded
    print(f"jira incremental {asof_s}: +{stats['added']} new, {stats['updated']} updated, {stats['unchanged']} unchanged, "
          f"{stats['renamed']} renamed, {stats['folded']} folded, {stats['parents_repointed']} child links re-pointed, {stats['dropped']} dropped, {stats['pulled']} pulled ({calls} calls){note}", flush=True)
    return 0


def backfill_ids():
    """One-time repair on an existing extract (use a COPY: --data-dir): give EVERY stored issue its Jira issue id, resolve keys that were
    renamed or moved since the extract was built, and fold any issue that is stored twice under two keys into one row.
    Writes jira_issue_ids.csv (every issue), jira_id_duplicates.csv (the key pairs found sharing an issue id, by name), updates
    key_aliases.csv, jira_issues.csv, jira_transitions.csv and jira_assignee_changes.csv with the same temp-file-then-swap rule."""
    ihead, issues = read_csv("jira_issues.csv")
    if ihead != ISSUE_HEAD: raise Fail("jira_issues.csv is missing or has an unexpected header")
    _, trans = read_csv("jira_transitions.csv"); _, achg = read_csv("jira_assignee_changes.csv"); ahead, aliases = read_csv("key_aliases.csv")
    c = TokenClient()
    keys = [r[0] for r in issues]
    got = {}          # stored key -> (issue id, current key)
    for i in range(0, len(keys), 100):
        batch = keys[i:i + 100]
        d = c.get("/rest/api/3/search/jql?jql=" + urllib.parse.quote("key in (%s)" % ",".join(batch)) + "&maxResults=100&fields=key")
        cur = {x["key"]: x["id"] for x in d["issues"]}
        for k in batch:
            if k in cur: got[k] = (cur[k], k)
    lonely = [k for k in keys if k not in got]       # not returned under their own key: renamed, moved, or gone
    for k in lonely:
        try: d = c.get("/rest/api/3/issue/%s?fields=key" % urllib.parse.quote(k))
        except RuntimeError: continue                 # 404: gone or not visible; left as it is, listed below
        got[k] = (d["id"], d["key"])
    by_id = {}
    for k, (i_, cur_k) in got.items(): by_id.setdefault(i_, []).append(k)
    dup_rows = [[i_, a, b] for i_, ks in by_id.items() if len(ks) > 1 for a, b in [(ks[0], k_) for k_ in ks[1:]]]
    renamed = {k: v[1] for k, v in got.items() if v[1] != k}
    # fold: keep the row stored under the CURRENT key when it exists, else re-key the old one
    drop, rekey = set(), {}
    for i_, ks in by_id.items():
        cur_k = got[ks[0]][1]
        if cur_k in ks:
            for k_ in ks:
                if k_ != cur_k: drop.add(k_); rekey[k_] = cur_k
        else:
            keep = ks[0]; rekey[keep] = cur_k
            for k_ in ks[1:]: drop.add(k_); rekey[k_] = cur_k
    new_issues = []
    pi = ISSUE_HEAD.index("parent_key"); repointed = []
    for r in issues:
        k = r[0]
        if k in drop: continue
        if k in rekey and rekey[k] != k: r = [rekey[k]] + r[1:]
        if r[pi] in rekey and rekey[r[pi]] != r[pi]: repointed.append((r[0], r[pi], rekey[r[pi]])); r = r[:pi] + [rekey[r[pi]]] + r[pi + 1:]   # child of a re-keyed parent
        new_issues.append(r)
    def rk(row): return ([rekey.get(row[0], row[0])] + row[1:])
    new_trans = [rk(t) for t in trans if t[0] not in drop]     # the kept row already carries that issue's history
    new_achg = [rk(a) for a in achg if a[0] not in drop]
    existing = {r_[0] for r_ in aliases}
    ts = jx.now()
    add_alias = [[old, new, "jira_resolved", ts, "in_extract", "", "", ""] + [""] * (len(ahead) - 8) for old, new in rekey.items() if old != new and old not in existing]
    final_keys = {r_[0] for r_ in new_issues}
    id_rows = sorted(({(i_, rekey.get(k, k)) for k, (i_, _) in got.items() if rekey.get(k, k) in final_keys}), key=lambda x: (int(x[0]), x[1]))
    missing = sorted(k for k in final_keys if k not in {kk for _, kk in id_rows})
    def temp(name, head, rows):
        p = os.path.join(OUT, name); t = p + ".incr.tmp"
        with open(t, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(head); w.writerows(rows)
        return p, t
    outs = [temp("jira_issues.csv", ISSUE_HEAD, new_issues), temp("jira_transitions.csv", TRANS_HEAD, new_trans), temp("jira_assignee_changes.csv", ACHG_HEAD, new_achg),
            temp("jira_issue_ids.csv", IDS_HEAD, [list(x) for x in id_rows]), temp("jira_id_duplicates.csv", ["issue_id", "key_a", "key_b"], dup_rows)]
    if add_alias: outs.append(temp("key_aliases.csv", ahead, aliases + add_alias))
    for p, t in outs: os.replace(t, p)
    if os.path.exists(c.cs): os.remove(c.cs)
    print(f"jira backfill-ids: {len(new_issues)} issues, {len(id_rows)} ids ({len(missing)} not found: {missing[:10]}), {len(renamed)} stored under an old key {sorted(renamed.items())[:10]}, "
          f"{len(dup_rows)} issues stored twice (folded): {dup_rows[:20]}, child links re-pointed {len(repointed)}: {repointed[:20]}, calls {c.st['calls']}", flush=True)
    return 0


def repair_parents():
    """No Jira call. Re-point every stored child whose parent_key is an OLD key (per key_aliases.csv, resolved by Jira or by changelog) to
    the parent's current key when that key is stored. Use on a COPY (--data-dir); lists every change by name; temp file then swap."""
    ihead, issues = read_csv("jira_issues.csv")
    if ihead != ISSUE_HEAD: raise Fail("jira_issues.csv is missing or has an unexpected header")
    _, aliases = read_csv("key_aliases.csv")
    stored = {r[0] for r in issues}
    pi = ISSUE_HEAD.index("parent_key")
    new_of = {}
    for r in aliases:
        if len(r) > 2 and r[1] and r[0] != r[1] and r[2] not in ("not_found", "none") and r[1] in stored and r[0] not in stored: new_of[r[0]] = r[1]
    changes = []
    for r in issues:
        if r[pi] in new_of: changes.append((r[0], r[pi], new_of[r[pi]])); r[pi] = new_of[r[pi]]
    if changes:
        p = os.path.join(OUT, "jira_issues.csv"); t = p + ".incr.tmp"
        with open(t, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(ISSUE_HEAD); w.writerows(issues)
        os.replace(t, p)
    print(f"jira repair-parents: {len(changes)} child links re-pointed: {changes[:30]}", flush=True)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--incremental", action="store_true")
    ap.add_argument("--backfill-ids", action="store_true", help="repair an existing extract COPY: give every issue its Jira id, fold issues stored twice")
    ap.add_argument("--repair-parents", action="store_true", help="no Jira call: re-point children whose parent_key is an old key (use on a copy)")
    ap.add_argument("--data-dir", default="", help="same as JIRA_EXTRACT_DIR (use a copy)")
    ap.add_argument("--asof", default="", help="UTC, e.g. 2026-11-11T11:00:00Z")
    ap.add_argument("--browser", action="store_true", help="opt-in fallback: read through the signed-in Home browser instead of the API token")
    a = ap.parse_args()
    if a.repair_parents:
        try: return repair_parents()
        except Fail as e: print("jira repair-parents failed: " + str(e), file=sys.stderr); return e.code
    if a.backfill_ids:
        try: return backfill_ids()
        except Fail as e: print("jira backfill-ids failed: " + str(e), file=sys.stderr); return e.code
    if not a.incremental: print("jira: use --incremental --asof <utc> (or --backfill-ids on a copy)", file=sys.stderr); return 1
    try: parse_utc(a.asof)
    except ValueError: print("jira incremental: --asof must look like 2026-11-11T11:00:00Z", file=sys.stderr); return 1
    try: return run(a.asof, browser=a.browser)
    except Fail as e:
        print("jira incremental failed: " + str(e), file=sys.stderr); return e.code
    except SystemExit as e:
        print("jira incremental stopped: " + str(e), file=sys.stderr); return 1


if __name__ == "__main__":
    sys.exit(main())
