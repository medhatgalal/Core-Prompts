#!/usr/bin/env python3
"""Derive the Sheet's data tabs from the saved extracts. Pure Python, no network, no model call (AC55).

Reads: data/config.json (and the paths it names), roster, history, identity, thresholds, extracts.
Writes: <derived>/<Tab>.csv (one per data tab, numbers as written to the Sheet) and meta.json.
Timestamps are written as ISO-8601 UTC text in the CSVs; build.py turns them into Sheet datetime serials.
"""
import csv, json, os, sys, datetime as dt, math, collections

UTC = dt.timezone.utc
EPOCH = dt.datetime(1899, 12, 30, tzinfo=UTC)


def rd(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pt(s):
    """parse ISO timestamp (with or without millis, Z) to aware datetime; '' -> None"""
    if not s:
        return None
    s = s.strip().replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        d = dt.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d.astimezone(UTC)


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ") if d else ""


def days(a, b):
    """(b - a) in days, rounded to 4 places; None if either missing"""
    if a is None or b is None:
        return None
    return round((b - a).total_seconds() / 86400.0, 4)


def hours(a, b):
    if a is None or b is None:
        return None
    return round((b - a).total_seconds() / 3600.0, 3)


def week_start(d):
    d0 = dt.datetime(d.year, d.month, d.day, tzinfo=UTC)
    return d0 - dt.timedelta(days=d0.weekday())


def pct_inc(vals, p):
    """linear interpolation percentile (NumPy default, equals PERCENTILE.INC)"""
    v = sorted(vals)
    if not v:
        return None
    k = (len(v) - 1) * p
    f = math.floor(k)
    c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def n(x, d=4):
    return "" if x is None else (round(x, d) if isinstance(x, float) else x)


class Roster:
    def __init__(self, cfg):
        P = cfg["paths"]
        self.rows = rd(P["roster"])
        self.hist = collections.defaultdict(list)
        to_chart0 = {r["name"]: r["chart_name"] for r in self.rows}   # history uses the directory spelling (roster `name`)
        for r in rd(P["roster_history"]):
            r = dict(r)
            r["person"] = to_chart0.get(r["person"], r["person"])
            self.hist[r["person"]].append(r)
        for p in self.hist:
            self.hist[p].sort(key=lambda r: r["effective_from"])
        # roster.csv is the source of truth: if a person's current group/team differs from the last history row (a roster edit not yet
        # in the history file), the new value applies from the as-of date (see Data_Dictionary: Roster_History)
        self.asof_date = None
        self.names = {r["chart_name"] for r in self.rows}
        self.cfg = cfg
        L = cfg["labels"]
        self.L = L
        self.groups = cfg["groups"]
        ident = rd(P["identity"])
        self.by_jira, self.by_gl, self.by_gh = {}, {}, {}
        to_chart = {r["name"]: r["chart_name"] for r in self.rows}    # identity.csv uses the directory spelling (roster `name`)
        for r in ident:
            p = to_chart.get(r["person"], r["person"])
            if r.get("jira_account_id") and r.get("jira_confidence") in ("exact", "overridden"):
                self.by_jira[r["jira_account_id"]] = p
            if r.get("gitlab_username") and r.get("gitlab_confidence") in ("exact", "overridden"):
                self.by_gl[r["gitlab_username"].lower()] = p
            if r.get("github_login") and r.get("github_confidence") in ("exact", "overridden"):
                self.by_gh[r["github_login"].lower()] = p
        # identity_overrides.csv (written by `roster set-identity`) takes effect on the next derive, with no live lookup
        ov = os.path.join(os.path.dirname(P["identity"]) or ".", "identity_overrides.csv")
        if os.path.exists(ov):
            maps = {"jira": self.by_jira, "gitlab": self.by_gl, "github": self.by_gh}
            for r in rd(ov):
                h = (r.get("handle") or "").strip()
                m_ = maps.get(r.get("system", ""))
                if not h or m_ is None:
                    continue
                who = to_chart.get(r["person"], r["person"])
                for k_ in [k for k, v in m_.items() if v == who]:
                    del m_[k_]
                m_[h if r["system"] == "jira" else h.lower()] = who
        # people whose end date is on or before the as-of are not on the roster for open work (their past events keep their dated team)
        self.end = {r["chart_name"]: r["end_date"] for r in self.rows if r.get("end_date")}

    def reconcile(self, asof):
        """Return the number of synthesized history rows. Called once as-of is known."""
        ds = asof.strftime("%Y-%m-%d")
        n = 0
        for r in self.rows:
            p = r["chart_name"]
            h = self.hist.get(p)
            cur = (r["group"], r["team"])
            if not h:
                self.hist[p] = [{"person": p, "effective_from": "0000-00-00", "effective_to": "", "group": r["group"], "team": r["team"], "_synth": 1}]
                n += 1
                continue
            last = h[-1]
            if (last["group"], last["team"]) != cur and not last["effective_to"]:
                last["effective_to"] = ds
                h.append({"person": p, "effective_from": ds, "effective_to": "", "group": r["group"], "team": r["team"], "_synth": 1})
                n += 1
        return n

    def ended(self, person, asof):
        e = self.end.get(person)
        return bool(e) and e <= asof.strftime("%Y-%m-%d")

    def tg(self, person, date):
        """(group, team) for a roster person on a date (a datetime), using dated history."""
        L = self.L
        h = self.hist.get(person)
        if not h:
            return L["other"], L["no_team"]
        ds = date.strftime("%Y-%m-%d")
        pick = None
        for r in h:
            if r["effective_from"] <= ds and (not r["effective_to"] or ds < r["effective_to"]):
                pick = r
        if pick is None:
            pick = h[-1]      # D36 #11: an event before the first history row uses the person's current row
        g, t = pick["group"], pick["team"]
        if not g:
            return L["other"], L["no_team"] if False else L["no_team"]
        return g, (t or L["no_team"])

    def group_from_field(self, v):
        L = self.L
        if not v:
            return L["unknown"]
        return v if v in self.groups else L["other"]


PRIO_ORDER = ["Blocker", "Critical", "Highest", "Major", "High", "Medium", "Minor", "Low", "Lowest", "Trivial", "Not Set"]      # Jira priority names, most urgent first


# v1.43 (user ruling 14 Nov): Xray types never reach an item tab. Jira issue type ids 10170 to 10175, 10006, 10007, 10037; the extract carries the NAME only, so the names are matched.
XRAY_TYPES = {10170: "Xray Test", 10171: "Test Set", 10172: "Xray Test Plan", 10173: "Test Execution", 10174: "Precondition", 10175: "Sub Test Execution", 10006: "Test Case", 10007: "Test Plan", 10037: "Test"}


import re as _re
XRAY_PAT = _re.compile(r"xray|precondition|^test( set| plan| case| execution)?$|^sub test execution$|test execution", _re.I)


def is_xray(type_name):
    """AC74: an Xray issue type by its known name OR by pattern, so a type not in the list is still excluded"""
    return type_name in XRAY_TYPES.values() or bool(XRAY_PAT.search(type_name or ""))


def incident_scope(ours_event, ours_created):
    """G4 (q92): an incident that was ours when created but is not ours at its event date (retagged later: IA-1822) must still count as CREATED (A71, AC78(b)). -> None (not ours at all: no row),
    "event" (ours at its event date: the usual row), "created_only" (a row for the created counts only: no resolved, won't-do, open, level or Group/Team of its own)."""
    if ours_event:
        return "event"
    return "created_only" if ours_created else None


def drop_subtasks(issues, trans):
    """AC74 (G1, q92): sub-tasks are not items: they leave every ticket count, list and the Work items tab. Their code links roll up to the parent in subtasks.remap (from the wide file), not through this list.
    -> (issues without Sub-task rows, transitions without theirs, number dropped)"""
    keys = {r["key"] for r in issues if r.get("type") == "Sub-task"}
    return [r for r in issues if r["key"] not in keys], [t for t in trans if t["issue"] not in keys], len(keys)


def assert_no_subtask(tabs):
    """backstop: no Sub-task row may reach a tab"""
    for tab, rows in tabs.items():
        bad = sum(1 for r in rows if isinstance(r, dict) and r.get("type") == "Sub-task")
        if bad:
            raise SystemExit(f"STOP: {bad} Sub-task rows reached {tab}; sub-tasks are not items (AC74)")


def assert_no_xray(tabs):
    """tabs {tab: [row dicts with 'type']} -> raises SystemExit naming the tab and the count when any row has an Xray type name. Jira found 0 in the main extract (v143-data.md); this keeps it so."""
    for tab, rows in tabs.items():
        bad = [r.get("type") for r in rows if isinstance(r, dict) and is_xray(r.get("type"))]
        if bad:
            raise SystemExit(f"STOP: {len(bad)} Xray-type rows ({sorted(set(bad))}) reached {tab}; Xray types are dropped (ids {sorted(XRAY_TYPES)}): fix the pull, not the Sheet")


def derive(cfg, out_dir):
    import ladder as LDR, jira_guard as JG
    P = cfg["paths"]
    JG.check(P["jira_dir"])          # inbox 187: never read a Jira folder with GUARD_FAILED.txt or without as_of.txt
    L = cfg["labels"]
    J = cfg["jira"]
    os.makedirs(out_dir, exist_ok=True)
    asof = pt(open(os.path.join(P["jira_dir"], "as_of.txt")).read().strip())
    wdays = cfg["window_days"]
    wstart = asof - dt.timedelta(days=wdays)
    R = Roster(cfg)
    R.reconcile(asof)
    T = {}   # thresholds are NOT used here (they live only in the Sheet)

    # ------------------------------------------------------------------ weeks
    first_mon = week_start(wstart)
    if first_mon < wstart:
        first_mon += dt.timedelta(days=7)
    weeks = []
    w = first_mon
    while w + dt.timedelta(days=7) <= asof:
        weeks.append(w)
        w += dt.timedelta(days=7)

    # ------------------------------------------------------------------ Jira
    issues = rd(os.path.join(P["jira_dir"], "jira_issues.csv"))
    _xr = [r for r in issues if is_xray(r["type"])]          # AC74: Xray types are EXCLUDED from every count, list and link (the assert below is the backstop)
    issues = [r for r in issues if not is_xray(r["type"])]
    trans = rd(os.path.join(P["jira_dir"], "jira_transitions.csv"))
    issues, trans, _n_sub = drop_subtasks(issues, trans)          # AC74 (G1): the wide extract holds the sub-tasks; none may count as a ticket
    by_key = {r["key"]: r for r in issues}
    code_types = set(J["code_types"])
    containers = set(J["container_types"])
    wd, dup = J["series_resolutions"]["wont_do"], J["series_resolutions"]["duplicate"]
    IP, DONE = J["in_progress_category"], J["done_category"]
    # W1: the 12-month window starts at as-of minus 12 months. The extracts keep items from earlier, wider pulls; a finished item whose final Done is before the window start is not in any population.
    dropped_jira = {r["key"] for r in issues if r["status_category"] == DONE and r["final_done"] and pt(r["final_done"]) < wstart}
    issues = [r for r in issues if r["key"] not in dropped_jira]
    trans = [t for t in trans if t["issue"] not in dropped_jira]
    GF = J["group_field_column"]
    _alias = {}          # moved Jira keys (old key -> new key), from the verified extract's alias table; used for the people-lens composition only
    _ap = os.path.join(os.path.dirname(os.path.normpath(P["jira_dir"])), "jira", "key_aliases.csv")
    if os.path.exists(_ap):
        for _r in csv.DictReader(open(_ap, newline="")):
            if _r.get("old_key") and _r.get("new_key"):
                _alias[_r["old_key"]] = _r["new_key"]
    LAD = LDR.Ladder(cfg, P["jira_dir"], R.rows) if cfg.get("ladder") else None          # v1.34: the A53 ladder at the event date replaces the owner-roster Group and Team of a ticket
    SBU_ONLY = cfg["labels"].get("sbu_only", "SBU only")
    pcomp = collections.defaultdict(collections.Counter)          # AC29 (A56): per roster person, composition of their tickets and changes in the period: ours, Other (by owning SBU or Group), untagged
    pother = collections.defaultdict(collections.Counter)
    oitems = []          # A74: the few tickets of our people that are tagged outside Automation or untagged (not in Jira_Issues): counts only, no title or person; the Jira key is kept (v1.43f, AC65)

    def _comp(x):
        cls = "ours" if x["ours"] else ("untagged" if x["untagged"] else "other")
        lab = x["sbu"] if (x["sbu"] and x["sbu"] != "Automation") else (x["grp_tag"] or x["team_tag"] or "Other")
        return cls, lab

    import workcat as WC          # v1.43: Work Category from jira's side files (epic's value at the finish date); BUILT AGAINST THE SIDE FILES until jira's join output lands
    _wc_now, _wc_chg = WC.load(P["jira_dir"])
    # --- per issue base
    jrows = []
    for r in issues:
        cr, fs, fd, up = pt(r["created"]), pt(r["first_start"]), pt(r["final_done"]), pt(r["updated"])
        is_wi = r["type"] not in containers
        done = r["status_category"] == DONE
        is_open = not done
        aid = r["assignee_id_at_final_done"] if done else r["assignee_id"]
        if not aid:
            owner, kind = L["ownerless"], "ownerless"
            fg = R.group_from_field(r[GF])
            g, t = fg, L["ownerless"]
        elif aid in R.by_jira and not (is_open and R.ended(R.by_jira[aid], asof)):
            owner, kind = R.by_jira[aid], "person"
            g, t = R.tg(owner, fd if (done and fd) else asof)
        else:
            owner, kind = L["unmapped"], "unmapped"
            g, t = R.group_from_field(r[GF]), L["unmapped"]
        if (LAD is not None and kind == "person" and is_wi and r.get("project") not in J.get("incident_projects", ["EA", "IA"])
                and (not done or r["resolution"] not in (wd, dup))):
            _cl, _lb = _comp(LAD.at(r, fd if (done and fd) else asof))
            pcomp[owner]["wi_" + _cl] += 1
            if _cl == "other":
                pother[owner]["wi|" + _lb] += 1
            if _cl != "ours":
                oitems.append({"kind": _cl, "type": r["type"], "status_category": r["status_category"], "created": cr, "final_done": fd if done else None, "owning": _lb if _cl == "other" else "", "key": r["key"]})
        lad_p = lad_c = None
        if LAD is not None and r.get("project") in J.get("incident_projects", ["EA", "IA"]):
            continue                                                    # incidents have their own measures (I1, I2); they are not work items
        if LAD is not None:
            lad_p = LAD.at(r, fd if (done and fd) else asof)          # the tag at the finish date, or at the as-of for open work
            lad_c = LAD.at_creation(r, asof) if cr else lad_p          # A71: the settled tag at the end of the 24 h window after creation (created counts)
            if not lad_p["ours"]:
                continue                                                # not ours at the date it counts: not in any population
            g = lad_p["group"] or SBU_ONLY                              # SBU-only tickets count in the SBU row only, never in a Group or Team row (A59)
            t = lad_p["team"] or L["no_team"]
        series = ""
        if done and is_wi:
            series = "wont_do" if r["resolution"] == wd else "duplicate" if r["resolution"] == dup else "main"
        in_cycle = int(done and is_wi and series == "main" and fs is not None and fd is not None)
        wip = int(is_wi and r["status_category"] == IP)
        d = {
            "key": r["key"], "type": r["type"], "is_work_item": int(is_wi),
            "is_code_type": int(r["type"] in code_types), "status": r["status"],
            "status_category": r["status_category"], "population": r["population"],
            "owner": owner, "owner_kind": kind, "team": t, "group": g,
            "field_group": r[GF], "priority": r["priority"],
            "created": cr, "first_start": fs, "first_start_basis": r["first_start_basis"],
            "final_done": fd, "updated": up, "parent_key": r["parent_key"],
            "mr_field_present": r["mr_field_present"], "resolution": r["resolution"], "series": series,
            "created_week": iso(week_start(cr)) if cr else "",
            "done_week": iso(week_start(fd)) if fd else "",
            "wip": wip, "in_cycle_pop": in_cycle,
            "cycle_days": days(fs, fd) if in_cycle else None,
            "lead_days": days(cr, fd) if (done and is_wi and series == "main") else None,
            "age_days": days(cr, asof) if is_open else None,
            "age_whole_days": int(math.floor((asof - cr).total_seconds() / 86400.0)) if (is_open and cr) else None,
            "start_age_days": days(fs, asof) if (wip and fs) else None,
            "days_since_update": days(up, asof) if is_open else None,
            "_asg_done": r["assignee_id_at_final_done"],
            "work_category": WC.for_issue(r, (fd if (done and fd) else None).strftime("%Y-%m-%dT%H:%M:%SZ") if (done and fd) else None, _wc_now, _wc_chg, containers),
        }
        if lad_p is not None:
            d.update({"level": lad_p["level"], "tag_conflict": int(lad_p["conflict"]), "sbu": lad_p["sbu"], "project": r.get("project", ""),
                      "ours_c": int(lad_c["ours"]), "group_c": (lad_c["group"] or SBU_ONLY) if lad_c["ours"] else "", "team_c": (lad_c["team"] or L["no_team"]) if lad_c["ours"] else ""})
        jrows.append(d)
    jidx = {d["key"]: d for d in jrows}
    # v1.43c AC75: stalled epics and initiatives. The clock is the Jira `updated` field (UTC, at the as-of) of the OPEN child TICKETS (closed child tickets and sub-tasks are ignored). Epic: its child tickets; initiative: the tickets under any child epic.
    # stalled_days = days since the newest update among those open tickets; an open container with no child tickets at all counts its own age (created) instead. An open container whose child tickets are ALL done has no clock: blank, and
    # kids_done = 1 (the 'open epics whose child tickets are all done' count). Blank for everything that is not an open epic or initiative.
    _typ = {r["key"]: r["type"] for r in issues}
    _upd = {r["key"]: pt(r["updated"]) for r in issues}
    _open_t = {r["key"]: r["status_category"] != DONE for r in issues}
    _kids = collections.defaultdict(list)
    for r in issues:
        if r["parent_key"]:
            _kids[r["parent_key"]].append(r["key"])
    def _tickets(k):
        return [c for c in _kids.get(k, []) if _typ.get(c) not in containers]
    def _clock(tk):
        o = [_upd[c] for c in tk if _open_t.get(c) and _upd.get(c)]
        return max(o) if o else None
    for d in jrows:
        d["stalled_days"] = None; d["kids_done"] = None
        if d["type"] not in ("Epic", "Initiative") or d["status_category"] == DONE:
            continue
        tk = _tickets(d["key"]) if d["type"] == "Epic" else [t for e in _kids.get(d["key"], []) if _typ.get(e) == "Epic" for t in _tickets(e)]
        if not tk:
            d["stalled_days"] = days(pt(by_key[d["key"]]["created"]), asof); d["kids_done"] = 0
        else:
            c = _clock(tk)
            d["kids_done"] = int(c is None)
            d["stalled_days"] = days(c, asof) if c else None

    # group P85 cycle (linear interpolation); fewer than 30 finished items -> SBU P85
    cyc_by_g = collections.defaultdict(list)
    for d in jrows:
        if d["in_cycle_pop"]:
            cyc_by_g[d["group"]].append(d["cycle_days"])
    all_cyc = [x for v in cyc_by_g.values() for x in v]
    sbu_p85 = pct_inc(all_cyc, 0.85)
    gp85 = {}
    for g in set(list(cyc_by_g) + R.groups + [L["other"], L["unknown"]]):
        v = cyc_by_g.get(g, [])
        gp85[g] = (pct_inc(v, 0.85), len(v) >= 30)
    for d in jrows:
        p, ok = gp85.get(d["group"], (None, False))
        use = p if (ok and p is not None) else sbu_p85
        d["group_p85_cycle_days"] = use
        d["p85_basis"] = "group" if ok else "sbu"
        d["age_over_group_p85"] = (int(d["start_age_days"] > use) if (d["wip"] and d["start_age_days"] is not None and use is not None) else None)

    # state one week before the as-of (for the week-over-week change beside the in-progress headlines)
    prev_wk = asof - dt.timedelta(days=7)
    achg = collections.defaultdict(list)
    ap_ = os.path.join(P["jira_dir"], "jira_assignee_changes.csv")
    for r in (rd(ap_) if os.path.exists(ap_) else []):
        achg[r["issue"]].append(r)
    # hygiene J1, J3 (J2 uses the Sheet threshold), J4, J5, J6
    for d in jrows:
        wi = d["is_work_item"]
        d["j1_pass"] = (int(d["owner_kind"] != "ownerless") if d["wip"] else None)
        d["j3_pass"] = (1 - d["age_over_group_p85"]) if d["age_over_group_p85"] is not None else None
        done_wi = wi and d["status_category"] == DONE
        d["j4_pass"] = (int(bool(d["resolution"])) if done_wi else None)
        d["j5_pass"] = (int(bool(d["_asg_done"])) if done_wi else None)
        d["j6_pass"] = (int(bool(d["parent_key"])) if (wi and d["status_category"] != DONE) else None)

    # ------------------------------------------------------------------ transitions
    tdata = collections.defaultdict(list)
    for r in trans:
        tdata[r["issue"]].append(r)
    trows = []
    for k, lst in tdata.items():
        lst.sort(key=lambda r: r["changed_at"])
        j = jidx.get(k)
        prev = j["created"] if j else None
        for r in lst:
            at = pt(r["changed_at"])
            fdn = j["final_done"] if j else None
            if fdn and prev:
                # A40: time in status stops at the strict final Done
                dd = None if prev >= fdn else days(prev, min(at, fdn))
            else:
                dd = days(prev, at) if prev else None
            trows.append({
                "issue": k, "from_status": r["from_status"], "to_status": r["to_status"],
                "from_category": r["from_category"], "to_category": r["to_category"],
                "changed_at": at, "days_in_from_status": dd,
                "in_cycle_pop": j["in_cycle_pop"] if j else 0,
            })
            prev = at

    # v1.23 K1: blocked items = open work items whose current status is in the blocked list; blocked age = as-of minus the time the item last entered a blocked status
    blocked_list = set(J.get("blocked_statuses", ["Blocked"]))
    for j in jrows:
        isb = bool(j["is_work_item"] and j["status_category"] != DONE and j["status"] in blocked_list)
        j["blocked"] = int(isb)
        j["blocked_age_days"] = None
        if isb:
            since = None
            for x in tdata.get(j["key"], []):
                if x["to_status"] in blocked_list:
                    at_ = pt(x["changed_at"])
                    if at_ and at_ <= asof and (since is None or at_ > since):
                        since = at_
            j["blocked_age_days"] = days(since or j["created"], asof)
    for j in jrows:
        evs = [(pt(x["changed_at"]), x["to_category"]) for x in tdata.get(j["key"], [])]
        cat = "new" if (j["created"] and j["created"] <= prev_wk) else None
        for at, c_ in evs:
            if at <= prev_wk:
                cat = c_
        wp = int(j["is_work_item"] == 1 and cat == IP)
        asg = None
        ch = sorted(achg.get(j["key"], []), key=lambda r: r["changed_at"])
        if ch:
            asg = ch[0]["from_assignee_id"]
            for r in ch:
                if pt(r["changed_at"]) <= prev_wk:
                    asg = r["to_assignee_id"]
        else:
            asg = by_key[j["key"]]["assignee_id"]
        j["wip_prev_week"] = wp
        j["no_owner_wip_prev_week"] = int(wp == 1 and not asg)

    # ------------------------------------------------------------------ daily status counts (work items)
    # per issue category timeline from transitions; Done counted by final Done only (see Data_Dictionary)
    dates = []
    d0 = dt.datetime(wstart.year, wstart.month, wstart.day, tzinfo=UTC)
    if wstart > d0:          # item 8: the daily series starts on the first whole day inside the window (2025-11-12 for a window start of 2025-11-11 22:19)
        d0 += dt.timedelta(days=1)
    d = d0
    while d <= asof:
        dates.append(d)
        d += dt.timedelta(days=1)
    daily = collections.defaultdict(lambda: [0, 0, 0])  # day -> new, indeterminate, done (snapshot at 00:00 UTC of that day, D36 #13)
    for j in jrows:
        if not j["is_work_item"] or not j["created"]:
            continue
        evs = [(pt(x["changed_at"]), x["to_category"]) for x in tdata.get(j["key"], [])]
        cur, since, ei = "new", j["created"], 0
        for day in dates:
            while ei < len(evs) and evs[ei][0] < day:
                cur, since = evs[ei][1], evs[ei][0]
                ei += 1
            if j["created"] >= day:
                continue
            if cur == DONE:
                if since >= wstart:        # Done counts only items that entered Done on or after the window start
                    daily[day][2] += 1
            else:
                daily[day][0 if cur == "new" else 1] += 1
    drows = []
    for day in dates:
        for i, c in enumerate(["new", IP, DONE]):
            drows.append({"date": iso(day)[:10], "status_category": c, "count": daily[day][i]})

    # ------------------------------------------------------------------ code changes (unified)
    glc = rd(os.path.join(P["gitlab_dir"], "code_changes.csv"))
    ghp = rd(os.path.join(P["github_dir"], "github_prs.csv"))
    ghls = {(r["repo"], r["number"]): r for r in rd(os.path.join(P["github_dir"], "github_pr_link_state.csv"))}
    ghrev = collections.defaultdict(list)
    for r in rd(os.path.join(P["github_dir"], "github_pr_reviews.csv")):
        ghrev[(r["repo"], r["number"])].append(r)

    def norm_state(s, merged=None):
        if s in ("opened", "open"):
            return "open"
        if s == "merged" or merged is True:
            return "merged"
        return "closed"

    crows = []
    glsha = set()
    # W1: a merged or closed change whose end is before the window start is left out (open changes of any age stay)
    dropped_ids = set()
    glc_keep = []
    for r in glc:
        if norm_state(r["state"]) != "open" and pt(r["merged_or_closed"]) is not None and pt(r["merged_or_closed"]) < wstart:
            dropped_ids.add(f"gitlab:{r['project_id']}!{r['number']}")
        else:
            glc_keep.append(r)
    glc = glc_keep
    dropped_code = len(dropped_ids)
    for r in glc:
        cid = f"gitlab:{r['project_id']}!{r['number']}"
        st = norm_state(r["state"])
        opened = pt(r["opened"])
        end = pt(r["merged_or_closed"])
        person = R.by_gl.get(r["author"].lower())
        if person:
            g, t = R.tg(person, end if end else asof)
            ak = "person"
        else:
            g, t, ak = L["unknown"], L["unmapped"], "unmapped"
        fr = pt(r["first_review_at"])
        la = pt(r["last_activity_at"])
        lines = int(r["lines"] or 0)
        lx = int(r["lines_excl_lockfiles_generated"] or 0)
        crows.append({
            "change_id": cid, "platform": "gitlab", "project": r["project"], "number": r["number"],
            "author": person or L["unmapped"], "author_kind": ak, "team": t, "group": g,
            "class": r["class"], "state": st, "draft": int(r["draft"] or 0), "counted": int(r["mirror_primary"] or 1),
            "opened": opened, "merged_at": end if st == "merged" else None, "closed_at": end if st == "closed" else None,
            "lines": lines, "lines_excl": lx, "desc_nonws_len": int(r["desc_nonws_len"] or 0),
            "merged_by": r["merged_by"] if st == "merged" else "", "self_merged": (int(r["self_merged"]) if st == "merged" else None),
            "head_sha": r["head_sha"], "mirror_key": r["mirror_key"],
            "first_review_at": fr, "approvals": int(r["approvals"] or 0), "review_detail": r["review_detail"],
            "last_activity_at": la, "key_state": r["key_state"], "primary_key": r["primary_key"],
        })
        glsha.add(r["head_sha"])
    seen_mirror = set()
    for r in sorted(ghp, key=lambda x: (x["created_at"], int(x["number"]))):
        cid = f"github:{r['repo']}#{r['number']}"
        merged = r["merged"] == "True"
        st = "merged" if merged else ("open" if r["state"] == "open" else "closed")
        opened = pt(r["created_at"])
        end = pt(r["merged_at"]) if merged else pt(r["closed_at"])
        if st != "open" and end is not None and end < wstart:         # W1
            dropped_ids.add(f"github:{r['repo']}#{r['number']}")
            dropped_code += 1
            continue
        person = R.by_gh.get(r["author"].lower())
        if person:
            g, t = R.tg(person, end if end else asof)
            ak = "person"
        else:
            g, t, ak = L["unknown"], L["unmapped"], "unmapped"
        ls = ghls.get((r["repo"], r["number"]))
        ks = ls["pr_state"] if ls else "no_key"
        revs = ghrev.get((r["repo"], r["number"]), [])
        appr = sum(1 for x in revs if x["state"] == "APPROVED")
        counted = 1
        if r["mirror_key"] in seen_mirror or r["head_sha"] in glsha:
            counted = 0
        seen_mirror.add(r["mirror_key"])
        lines = int(r["additions"] or 0) + int(r["deletions"] or 0)
        lx = int(r["lines_excl"]) if r.get("lines_excl") not in (None, "") else lines
        nonws = int(r["body_nonws_len"]) if r.get("body_nonws_len") not in (None, "") else int(r["body_len"] or 0)
        mby = r.get("merged_by", "") if merged else ""
        selfm = (int(mby.lower() == r["author"].lower()) if mby else None) if merged else None
        times = [pt(x["submitted_at"]) for x in revs if x["reviewer"].lower() != r["author"].lower() and x["reviewer_type"] == "User" and pt(x["submitted_at"])]
        fr = pt(r["first_review_at"])
        crows.append({
            "change_id": cid, "platform": "github", "project": r["repo"], "number": r["number"],
            "author": person or L["unmapped"], "author_kind": ak, "team": t, "group": g,
            "class": r["class"], "state": st, "draft": int(r["draft"] == "True"), "counted": counted,
            "opened": opened, "merged_at": end if st == "merged" else None, "closed_at": end if st == "closed" else None,
            "lines": lines, "lines_excl": lx, "desc_nonws_len": nonws,
            "merged_by": mby, "self_merged": selfm,
            "head_sha": r["head_sha"], "mirror_key": r["mirror_key"],
            "first_review_at": fr, "approvals": appr, "review_detail": "fetched",
            "last_activity_at": pt(r["updated_at"]), "key_state": ks, "primary_key": r["primary_key"],
        })
    # D36 #9 mirrors: the same head SHA in a different project is one change; the earliest opened is kept
    by_sha = collections.defaultdict(list)
    for c in crows:
        if c["state"] == "open" and c["author_kind"] == "person" and R.ended(c["author"], asof):
            c["author"], c["author_kind"], c["team"], c["group"] = L["unmapped"], "unmapped", L["unmapped"], L["unknown"]
        c["counted"] = 1
        if c["head_sha"]:
            by_sha[c["head_sha"]].append(c)
    for lst in by_sha.values():
        if len(lst) > 1:
            lst.sort(key=lambda c: (c["opened"], c["change_id"]))
            keep = lst[0]
            keep["counted"] = 1
            for c in lst[1:]:
                c["counted"] = 0 if c["project"] != keep["project"] else 1
    for c in crows:
        c["open_age_days"] = days(c["opened"], asof) if c["state"] == "open" else None
        c["days_since_activity"] = days(c["last_activity_at"], asof) if c["state"] == "open" else None
        c["open_to_merge_days"] = days(c["opened"], c["merged_at"]) if c["merged_at"] else None
        c["hours_to_first_review"] = hours(c["opened"], c["first_review_at"]) if c["first_review_at"] else None
        c["merged_week"] = iso(week_start(c["merged_at"])) if c["merged_at"] else ""
        c["created_week"] = iso(week_start(c["opened"]))
        end = c["merged_at"]
        # C flags (1 pass, 0 fail, '' not applicable); thresholds applied by the Sheet (C5, C6, C7, C8)
        norm = c["class"] == "normal" and c["counted"] == 1
        c["c1_pass"] = int(c["key_state"] == "linked") if norm else None
        c["c2_pass"] = int(c["desc_nonws_len"] >= 20) if norm else None
        if norm and c["state"] == "merged":
            c["c3_pass"] = int(c["first_review_at"] is not None and c["first_review_at"] <= end)
            c["c4_pass"] = (int(not (c["self_merged"] == 1 and not c["c3_pass"])) if c["self_merged"] is not None else None)
        else:
            c["c3_pass"] = c["c4_pass"] = None
        c["lines_for_c5"] = c["lines_excl"] if norm else None

    # ------------------------------------------------------------------ links & per-issue alignment
    gl_links = rd(os.path.join(P["gitlab_dir"], "code_jira_links.csv"))
    gh_keys = rd(os.path.join(P["github_dir"], "github_pr_key_state.csv"))
    lrows = []
    for r in gl_links:
        lrows.append({"change_id": r["change_id"], "jira_key": r["jira_key"], "source": r["source"],
                      "primary": int(r["primary"] or 0), "key_check": r["key_check"],
                      "resolved_jira_key": r["resolved_jira_key"] if r["key_check"] == "linked" else "",
                      "alias_source": r["alias_source"]})
    for r in gh_keys:
        lrows.append({"change_id": f"github:{r['repo']}#{r['number']}", "jira_key": r["key"], "source": r["source"],
                      "primary": int(r["rank"] == "1"), "key_check": r["key_state"],
                      # a direct key (alias_used empty, alias_resolution in_extract) resolves to the key itself (G1): linked means it exists in the Jira extract
                      "resolved_jira_key": ((r["alias_used"] or (r["key"] if r["alias_resolution"] == "in_extract" else "")) if r["key_state"] == "linked" else ""),
                      "alias_source": r["alias_resolution"]})
    cidx = {c["change_id"]: c for c in crows}
    lrows = [l for l in lrows if l["change_id"] not in dropped_ids]
    # v1.41 (AP-81082): a key check made BEFORE the ticket existed leaves the link 'not_found' although the ticket is in this extract; the link then counted for nothing and the ticket showed as quiet.
    # When the key is in the Jira extract the link resolves to it (the key check itself is left as recorded).
    for l in lrows:
        if l["key_check"] == "not_found" and not l["resolved_jira_key"] and l["jira_key"] in jidx:
            l["resolved_jira_key"] = l["jira_key"]            # W1: links of changes left out of the window go with them
    import subtasks as ST          # v1.43c AC74: a link to a sub-task rolls up to the parent ticket; a sub-task with its parent outside the extract is ignored
    _st_parent, _st_ignored = ST.load(P.get("jira_wide_file", ST.WIDE))
    _st_ru, _st_ig = ST.remap(lrows, _st_parent, _st_ignored)
    if LAD is not None:
        # v1.34 (A53): a change is ours by its PRIMARY linked ticket (the first key named) at the merge date; else by its author's roster Group and Team at that date; else unmapped.
        prim_key = {}
        for l in lrows:
            if l["primary"] == 1 and l["change_id"] not in prim_key:
                prim_key[l["change_id"]] = l["resolved_jira_key"] or l["jira_key"]
        for c in crows:
            when = c["merged_at"] or c["closed_at"] or asof
            tk = by_key.get(prim_key.get(c["change_id"], ""))
            tk_c = tk if tk is not None else by_key.get(_alias.get(prim_key.get(c["change_id"], ""), ""))          # composition only: a moved key (the jira_resolved alias) is resolved before the in-pull test; the attribution below is unchanged
            if c["counted"] and c["state"] == "merged" and c["class"] == "normal" and c["author_kind"] == "person":
                if tk_c is not None:
                    _cl, _lb = _comp(LAD.at(tk_c, when))
                else:
                    _cl, _lb = "ours", ""          # no linked ticket in the extract: the author's roster Group decides, so it is ours
                c["comp_kind"] = _cl
                pcomp[c["author"]]["ch_" + _cl] += 1
                if _cl == "other":
                    pother[c["author"]]["ch|" + _lb] += 1
            c["attrib"] = "author"
            if tk is not None:
                lt = LAD.at(tk, when)
                if lt["ours"]:
                    c["group"], c["team"], c["attrib"] = lt["group"] or SBU_ONLY, lt["team"] or L["no_team"], "ticket"
                    c["level"] = lt["level"]
                    continue
            if c["author_kind"] == "person" and c["group"] not in R.groups:
                c["group"], c["team"], c["level"] = SBU_ONLY, L["no_team"], "SBU"          # a roster person outside the 4 Groups: ours at SBU level only (A53 rule 3), in the SBU row and no Group row
            elif c["author_kind"] == "person":
                c["level"] = "Team" if (c["team"] and c["team"] not in (L["no_team"], L["unmapped"], L["other"], L["unknown"])) else "Group"
            else:
                c["level"] = ""
    per_issue = collections.defaultdict(lambda: {"n": 0, "merged": 0, "open": 0, "last": None, "last_all": None, "seen": set(), "seen_all": set(), "merged_all": 0})
    for l in lrows:
        k = l["resolved_jira_key"]
        c = cidx.get(l["change_id"])
        if not k or not c:
            continue
        pi = per_issue[k]
        if l["change_id"] not in pi["seen_all"]:      # D39 / F3: code evidence counts mirror copies too (the same commit merged)
            pi["seen_all"].add(l["change_id"])
            if c["state"] == "merged":
                pi["merged_all"] += 1
        la_ = c["last_activity_at"]       # G3 (D96): activity on an uncounted mirror copy is real work, so it counts as linked activity for A2
        if la_ and (pi["last_all"] is None or la_ > pi["last_all"]):
            pi["last_all"] = la_
        if not c["counted"]:
            continue
        if l["change_id"] in pi["seen"]:
            continue
        pi["seen"].add(l["change_id"])
        pi["n"] += 1
        if c["state"] == "merged":
            pi["merged"] += 1
        elif c["state"] == "open":
            pi["open"] += 1
        la = c["last_activity_at"]
        if la and (pi["last"] is None or la > pi["last"]):
            pi["last"] = la
    for j in jrows:
        pi = per_issue.get(j["key"])
        j["linked_changes"] = pi["n"] if pi else 0
        j["linked_merged"] = pi["merged"] if pi else 0
        j["linked_open"] = pi["open"] if pi else 0
        j["linked_merged_incl_mirrors"] = pi["merged_all"] if pi else 0
        j["days_since_linked_activity"] = days(pi["last_all"], asof) if (pi and pi["last_all"]) else None
        # A3: open issue whose linked changes are all merged; A4: done code-type issue with no merged change
        isopen = j["status_category"] != DONE
        j["a3_status_lag"] = (int(j["linked_changes"] > 0 and j["linked_merged"] == j["linked_changes"]) if (isopen and j["is_work_item"]) else None)
        j["a4_no_code"] = (int(j["linked_merged_incl_mirrors"] == 0) if (j["status_category"] == DONE and j["is_work_item"] and j["is_code_type"]) else None)

    # ------------------------------------------------------------------ reviews: one row per review event by a roster person on a change that is not their own
    # GitLab: approvals and non-system notes. GitHub: reviews of roster-authored pull requests (the reviewed-by search rows carry no review time and are not used).
    gl_raw_author = {}
    for r in glc:
        gl_raw_author[f"gitlab:{r['project_id']}!{r['number']}"] = r["author"].lower()
    for r in rd(os.path.join(P["gitlab_dir"], "reviewed_others.csv")):
        gl_raw_author.setdefault(r["change_id"], r["author"].lower())
    vrows = []
    seen_ev = set()

    def add_ev(cid, platform, who, at, typ):
        g, t = R.tg(who, asof)         # reviewer's team and group as of the as-of date
        vrows.append({"change_id": cid, "platform": platform, "reviewer": who, "reviewer_team": t, "reviewer_group": g,
                      "review_time": at, "review_week": iso(week_start(at)), "review_type": typ})
    for r in rd(os.path.join(P["gitlab_dir"], "code_reviews.csv")):
        who = R.by_gl.get(r["reviewer"].lower())
        if not who or r["reviewer_bot_guess"] == "1":
            continue
        if gl_raw_author.get(r["change_id"]) == r["reviewer"].lower():
            continue
        at = pt(r["review_time"])
        if at is None:
            continue
        k = (r["change_id"], r["reviewer"], r["review_time"], r["review_type"])
        if k in seen_ev:
            continue
        seen_ev.add(k)
        add_ev(r["change_id"], "gitlab", who, at, r["review_type"])
    for (repo, num), lst in ghrev.items():
        cid = f"github:{repo}#{num}"
        auth = cidx.get(cid, {}).get("author")
        for r in lst:
            who = R.by_gh.get(r["reviewer"].lower())
            if not who or r["reviewer_type"] != "User" or who == auth:
                continue
            at = pt(r["submitted_at"])
            if at is None:
                continue
            add_ev(cid, "github", who, at, {"APPROVED": "approval"}.get(r["state"], "comment"))
    vrows.sort(key=lambda v: (v["review_time"], v["change_id"], v["reviewer"]))
    vrows = [v for v in vrows if v["change_id"] not in dropped_ids]            # W1: reviews of changes left out of the window go with them

    # ------------------------------------------------------------------ incidents (v1.21): counts only plus the Jira key (v1.43f, AC65), one row per incident, measured at the Sheet's as-of
    inc_rows = []
    ipath = os.path.join(P["jira_dir"], "incidents", "jira_incidents.csv")
    iprojects = J.get("incident_projects", ["EA", "IA"])
    if LAD is not None and cfg.get("incidents", True):
        # v1.34 (A53): incidents are ordinary tickets of the projects EA (customer) and IA (internal); ours by the ladder at their event date, from the same extract
        wd_names = {J["series_resolutions"]["wont_do"], J["series_resolutions"]["duplicate"]}
        for r in issues:
            if r.get("project") not in iprojects:
                continue
            cr, fd = pt(r["created"]), pt(r["final_done"])
            if cr is None or cr > asof:
                continue
            res = r["status_category"] == DONE and fd is not None and fd <= asof
            lad_i = LAD.at(r, fd if res else asof)
            lad_c = LAD.at_creation(r, asof)          # A71, A67(b): created incidents use the tag at creation (blank = untagged: no Group or Team row, not in the created counts)
            _sc = incident_scope(lad_i["ours"], lad_c["ours"])
            if _sc is None:
                continue
            _ev = _sc == "event"          # created_only: counted as created (ours_c, group_c, team_c) and nowhere else
            inc_rows.append({"project": r["project"], "split": "customer" if r["project"] == iprojects[0] else "internal", "type": r["type"], "priority": r["priority"],
                             "created": cr, "final_done": fd if (res and _ev) else None, "resolution": r["resolution"] if (res and _ev) else "",
                             "wontdo_dup": int(_ev and res and r["resolution"] in wd_names), "open_at_asof": int(_ev and not res),
                             "age_days": days(cr, asof) if (_ev and not res) else None, "ttr_days": days(cr, fd) if (_ev and res) else None,
                             "group": (lad_i["group"] or SBU_ONLY) if _ev else "", "team": lad_i["team"] if _ev else "", "level": lad_i["level"] if _ev else "",
                             "ours_c": int(lad_c["ours"]), "group_c": (lad_c["group"] or SBU_ONLY) if lad_c["ours"] else "", "team_c": (lad_c["team"] or L["no_team"]) if lad_c["ours"] else "", "key": r["key"]})
    elif os.path.exists(ipath) and cfg.get("incidents", True):
        wd_names = {J["series_resolutions"]["wont_do"], J["series_resolutions"]["duplicate"]}
        ros_groups = set(R.groups)          # A43: the 4 SBU Groups (data/roster_config.json); a Team counts only when it is on a roster row under one of them
        ros_teams = {x["team"] for x in R.rows if x.get("team") and x.get("group") in ros_groups}
        for r in rd(ipath):                  # D126/D127: the extract's final Done is the strict one (Done-to-Done moves do not move it), so the stored values are measured at the Sheet as-of
            cr, fd = pt(r["created"]), pt(r["final_done"])
            if cr is None or cr > asof:
                continue
            g_raw, t_raw = (r.get("group") or "").strip(), (r.get("team") or "").strip()
            t_raw = J.get("team_aliases", {}).get(t_raw, t_raw)          # A45: a Jira Team name that the roster spells differently (a Team renamed in the roster; config jira.team_aliases)
            if g_raw not in ros_groups and t_raw not in ros_teams:        # v1.28: an incident counts only with a roster Group or Team tie; blank or other Groups and Teams are not ours
                continue
            res = fd is not None and fd <= asof
            fd = fd if res else None
            inc_rows.append({"project": r["project"], "split": "customer" if r["project"] == iprojects[0] else "internal", "type": r["type"], "priority": r["priority"],
                             "created": cr, "final_done": fd if res else None, "resolution": r["resolution"] if res else "",
                             "wontdo_dup": int(res and r["resolution"] in wd_names), "open_at_asof": int(not res),
                             "age_days": days(cr, asof) if not res else None, "ttr_days": days(cr, fd) if res else None,
                             "group": g_raw if g_raw in ros_groups else "Other Group (tied by Team)", "team": t_raw if t_raw in ros_teams else "", "key": r.get("key", "")})
    # ------------------------------------------------------------------ State_History: state at the end of each of the last 6 complete weeks and 12 complete months, by replay
    snaps = []
    for w_ in weeks[-6:]:
        snaps.append(("week", "Week of " + w_.strftime("%b %-d"), w_ + dt.timedelta(days=7)))
    first = dt.datetime(asof.year, asof.month, 1, tzinfo=UTC)
    for i in range(12, 0, -1):
        y, m_ = first.year, first.month - i
        while m_ <= 0:
            y, m_ = y - 1, m_ + 12
        st_ = dt.datetime(y, m_, 1, tzinfo=UTC)
        en_ = dt.datetime(y + (m_ == 12), (m_ % 12) + 1, 1, tzinfo=UTC)
        snaps.append(("month", st_.strftime("%b %Y"), en_))
    snaps.append(("asof", "As-of", asof))
    edge = {"no_transitions_in_progress_now": 0, "items_with_assignee_changes": 0, "items_reopened": 0, "items_without_changelog_rows": 0}
    shist = []
    cnt = {}     # (snapshot index, group, team) -> [open, in progress, no owner, stuck]
    for j in jrows:
        if not j["is_work_item"] or not j["created"]:
            continue
        evs = sorted(((pt(x["changed_at"]), x["to_category"]) for x in tdata.get(j["key"], [])), key=lambda e: e[0])
        ch = sorted(achg.get(j["key"], []), key=lambda r: r["changed_at"])
        if ch:
            edge["items_with_assignee_changes"] += 1
        if any(evs[i][1] != DONE and evs[i - 1][1] == DONE for i in range(1, len(evs))) or (evs and evs[0][1] != DONE and False):
            edge["items_reopened"] += 1
        if not evs:
            edge["items_without_changelog_rows"] += 1
            if j["status_category"] == IP:
                edge["no_transitions_in_progress_now"] += 1
        cur_asg = by_key[j["key"]]["assignee_id"]
        init_asg = ch[0]["from_assignee_id"] if ch else cur_asg
        init_cat = "new"
        if not evs and j["status_category"] in (IP, DONE) and not j["final_done"]:
            init_cat = j["status_category"]        # no history rows: the status the item has now is the status it started with
        for si, (k_, l_, t_) in enumerate(snaps):
            if j["created"] > t_:
                continue
            cat = init_cat
            for at, c_ in evs:
                if at <= t_:
                    cat = c_
                else:
                    break
            if not evs and j["status_category"] == DONE and j["final_done"] and j["final_done"] <= t_:
                cat = DONE
            asg = init_asg
            for r in ch:
                if pt(r["changed_at"]) <= t_:
                    asg = r["to_assignee_id"]
            # attribute the item to the Group and Team its owner had AT THIS SNAPSHOT (dated roster history, as the other tabs do), not the current ones
            if LAD is not None:
                lad_s = LAD.at(by_key[j["key"]], t_)
                if not lad_s["ours"]:
                    continue
                g_s, t_s = (lad_s["group"] or SBU_ONLY), (lad_s["team"] or L["no_team"])
            elif asg:
                if asg in R.by_jira and not R.ended(R.by_jira[asg], t_):
                    g_s, t_s = R.tg(R.by_jira[asg], t_)
                else:
                    g_s, t_s = R.group_from_field(j["field_group"]), L["unmapped"]
            else:
                g_s, t_s = R.group_from_field(j["field_group"]), L["ownerless"]
            c4 = cnt.setdefault((si, g_s, t_s), [0, 0, 0, 0])
            if cat != DONE:
                c4[0] += 1
            if cat == IP:
                c4[1] += 1
                if not asg:
                    c4[2] += 1
                age_ = days(j["first_start"], t_) if j["first_start"] and j["first_start"] <= t_ else None
                p85_, ok_ = gp85.get(g_s, (None, False))       # D95: tested against the P85 of the Group the item counted in at this date (the as-of P85 value)
                lim_ = p85_ if (ok_ and p85_ is not None) else sbu_p85
                if age_ is not None and lim_ is not None and age_ > lim_:
                    c4[3] += 1
    pairs_ = sorted({(g_, t2_) for (_, g_, t2_) in cnt})
    for si, (k_, l_, t_) in enumerate(snaps):
        def put_(level, g_, t2_, vals):
            shist.append({"kind": k_, "label": l_, "snapshot_at": t_, "level": level, "group": g_, "team": t2_, "open_work_items": vals[0],
                          "in_progress": vals[1], "in_progress_no_owner": vals[2], "in_progress_stuck": vals[3]})
        agg = lambda sel: [sum(cnt.get((si, g_, t2_), [0] * 4)[i] for (g_, t2_) in pairs_ if sel(g_, t2_)) for i in range(4)]
        put_("SBU", "*", "*", agg(lambda g_, t2_: True))
        for g_ in sorted({p[0] for p in pairs_}):
            put_("Group", g_, "*", agg(lambda a, b, g_=g_: a == g_))
        for g_, t2_ in pairs_:
            put_("Team", g_, t2_, cnt.get((si, g_, t2_), [0] * 4))
    meta_edge = edge

    _pc = {p_: {**dict(c_), "other_by": {k_[3:]: v_ for k_, v_ in pother[p_].items() if k_.startswith("wi|")}, "ch_other_by": {k_[3:]: v_ for k_, v_ in pother[p_].items() if k_.startswith("ch|")}} for p_, c_ in pcomp.items()}
    meta = {"people_comp": _pc, "window_dropped": {"jira_done_before_window": len(dropped_jira), "code_ended_before_window": dropped_code}, "as_of": iso(asof), "window_start": iso(wstart), "weeks": [iso(x)[:10] for x in weeks],
            "groups": R.groups, "p85_by_group": {g: [v[0], v[1]] for g, v in gp85.items()}, "sbu_p85": sbu_p85,
            "teams": sorted({r["team"] for r in R.rows if r["team"]}),
            "counts": {"jira_issues": len(jrows), "jira_transitions": len(trows), "code_changes": len(crows),
                       "code_jira_links": len(lrows), "xray_excluded": len(_xr), "links_rolled_up_from_subtasks": _st_ru, "links_ignored_subtask": _st_ig, "code_reviews": len(vrows), "daily": len(drows), "state_history": len(shist), "incidents": len(inc_rows)},
            "state_history_edges": meta_edge,
            "incidents_enabled": bool(cfg.get("incidents", True)),
            "inc_priorities": sorted({x["priority"] for x in inc_rows if x["priority"]}, key=lambda x: (PRIO_ORDER.index(x) if x in PRIO_ORDER else 99, x)),
            "inc_types": sorted({(x["split"], x["type"]) for x in inc_rows}, key=lambda t: (t[0] != "customer", t[1])),
            "bug_priorities": sorted({j["priority"] for j in jrows if j["type"] == "Bug" and j["priority"]}, key=lambda x: (PRIO_ORDER.index(x) if x in PRIO_ORDER else 99, x))}
    assert_no_xray({"Jira_Issues": jrows, "Incident_Issues": inc_rows, "Other_Items": oitems})
    assert_no_subtask({"Jira_Issues": jrows, "Incident_Issues": inc_rows, "Other_Items": oitems})
    return R, {"Jira_Issues": jrows, "Jira_Transitions": trows, "Daily_Status_Counts": drows,
               "Code_Changes": crows, "Code_Jira_Links": lrows, "Code_Reviews": vrows, "State_History": shist, "Incident_Issues": inc_rows, "Other_Items": oitems}, meta, asof


def selftest_xray():
    iss = [{"key": "A-1", "type": "Story"}, {"key": "A-2", "type": "Sub-task"}, {"key": "A-3", "type": "Epic"}]
    tr = [{"issue": "A-1"}, {"issue": "A-2"}]
    i2, t2, n2 = drop_subtasks(iss, tr)
    ok = incident_scope(True, True) == "event" and incident_scope(True, False) == "event" and incident_scope(False, True) == "created_only" and incident_scope(False, False) is None          # G4: IA-1822 is (False, True)
    ok &= [r["key"] for r in i2] == ["A-1", "A-3"] and t2 == [{"issue": "A-1"}] and n2 == 1 and drop_subtasks([], [])[2] == 0
    try:
        assert_no_subtask({"Jira_Issues": iss}); ok = False
    except SystemExit as e:
        ok &= "Jira_Issues" in str(e)
    assert_no_subtask({"Jira_Issues": i2})
    ok &= all(is_xray(t) for t in ("Xray Test", "Test Execution", "Some New Xray Thing", "Precondition")) and not any(is_xray(t) for t in ("Story", "Epic", "Technical Debt", "Task", "Bug"))
    assert_no_xray({"Jira_Issues": [{"type": "Story"}, {"type": "Epic"}], "Incident_Issues": [], "Other_Items": [{"kind": "other"}]})          # clean rows pass
    for nm in XRAY_TYPES.values():
        try:
            assert_no_xray({"Jira_Issues": [{"type": "Story"}, {"type": nm}]}); ok = False
        except SystemExit as e:
            ok &= "Jira_Issues" in str(e) and nm in str(e)
    print("derive xray assert selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest-xray" in sys.argv:
        sys.exit(selftest_xray())
    cfg = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "data/config.json"))
    R, tabs, meta, asof = derive(cfg, cfg["paths"]["derived"])
    print(json.dumps(meta["counts"], indent=1))
