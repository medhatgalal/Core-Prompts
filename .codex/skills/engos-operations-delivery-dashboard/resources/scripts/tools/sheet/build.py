#!/usr/bin/env python3
"""Build or rebuild the dashboard Sheet from the saved extracts. No model call.
Usage: build.py [--config data/config.json] [--target real|scratch|<spreadsheet id>] [--keep-tabs Insights,canvas] [--dry-run]
Steps: derive -> (re)create tabs -> named ranges -> values and formulas -> charts -> protection -> self-check."""
import argparse, json, os, sys, time, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import derive as D
import tabs as TB
import metrics as MT
import panels as PN
import charts as CH
from sheetlib import sheets, batch, write_grid, write_diff, a1, col_letter, STATS, get_meta, values_get

DATA_TABS = ["Jira_Issues", "Jira_Transitions", "Daily_Status_Counts", "Code_Changes", "Code_Jira_Links", "Code_Reviews", "State_History", "Incident_Issues", "Other_Items"]
OUR_TABS = ["Dashboard", "Alert details", "Coverage", "Metrics", "Individual", "Thresholds", "Roster", "Roster_History", "README", "Data_Dictionary",
            "Prompt_Library", "Run_Log", "canvas_source", "Failing_Lists", "Identity"] + DATA_TABS
ORDER = ["README", "Dashboard", "Alert details", "Coverage", "Metrics", "Individual", "Insights", "Thresholds", "Roster", "Roster_History", "Data_Dictionary", "Identity",
         "Prompt_Library", "Run_Log", "canvas_source", "Failing_Lists"] + DATA_TABS


REMOVED_TABS = ["Charts (detail)"]      # v1.22: deleted when present (with every chart on it); no formula, name or link points at it


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def nice_steps():
    return [m * 10 ** e for e in range(-1, 6) for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8)]


def win612(G, sid):
    """Axis windows for the 6/12 flow charts (D1 flow and B1 bugs): weekly on the left, monthly on the right, with zero at the same height on both so the break-even
    line is true for both parts. Chart settings, not Sheet values (like v4_cap). Returns {range name: (left min, left max, right min, right max)}."""
    out = {}

    def align(name):
        src = ["d_inc612_chart_customer", "d_inc612_chart_internal"] if name == "I1" else [name]      # I1 draws both splits on one chart: one window for both
        wk, mo = [], []
        for nm_ in src:
            r0, c0, r1, c1 = G.names[nm_]
            rows = values_get(sid, f"Metrics!{col_letter(c0 + 1)}{r0 + 2}:{col_letter(c0 + 6)}{r1 + 1}", "UNFORMATTED_VALUE")
            num = lambda v: v if isinstance(v, (int, float)) else None
            wk += [num(r[j]) for r in rows[:6] for j in range(3) if len(r) > j and num(r[j]) is not None]
            mo += [num(r[j]) for r in rows[7:19] for j in range(3, 6) if len(r) > j and num(r[j]) is not None]
        wmax, wmin, mmax, mmin = max(wk), min(0, min(wk)), max(mo), min(0, min(mo))
        best = None
        for n_up in range(2, 7):
            for k in range(0, 4):
                if (wmin < 0 or mmin < 0) and k == 0:
                    continue
                def fit(mx, mn):
                    need = max(mx * 1.08 / n_up, (-mn * 1.08 / k) if k else 0)
                    return next(x for x in nice_steps() if x >= need)
                sw, sm = fit(wmax, wmin), fit(mmax, mmin)
                score = (n_up * sw / wmax) + (n_up * sm / mmax) + 0.15 * (n_up + k)
                if best is None or score < best[0]:
                    best = (score, n_up, k, sw, sm)
        _, n_up, k, sw, sm = best
        out[name] = (-k * sw, n_up * sw, -k * sm, n_up * sm)

    for nm in ("d_flow612", "d_bugs612_chart") + (("d_inc612_chart_customer", "d_inc612_chart_internal") if G.names.get("d_inc612_chart_customer") else ()):
        try:
            align(nm)
        except Exception as e:
            log(f"axis windows not set for {nm}: {e}")
    try:       # D5: hours on both parts, so both get the same range
        q0, qc0, q1, _ = G.names["d_review612"]
        rv = values_get(sid, f"Metrics!{col_letter(qc0 + 1)}{q0 + 2}:{col_letter(qc0 + 2)}{q1 + 1}", "UNFORMATTED_VALUE")
        hv = [x for r in rv for x in r if isinstance(x, (int, float))]
        top = next(x for x in nice_steps() if x >= max(hv) * 1.08)
        out["d_review612"] = (0, top, 0, top)
    except Exception as e:
        log(f"common range not set for the review chart: {e}")
    return out or None


def v4_cap(G, sid):
    """left-axis cap for V4: a little above the second-largest bin so the first bin does not swamp the others (chart setting, not a Sheet value)"""
    try:
        r0, c0, r1, c1 = G.names["m_cycle_bins"]
        vals = [r[0] for r in values_get(sid, f"Metrics!{col_letter(c0 + 2)}{r0 + 2}:{col_letter(c0 + 2)}{r1 + 1}", "UNFORMATTED_VALUE") if r and isinstance(r[0], (int, float))]
        vals = sorted(vals, reverse=True)
        return int(-(-vals[1] * 1.25 // 100) * 100) if len(vals) > 1 else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="data/config.json")
    ap.add_argument("--target", default="scratch")
    ap.add_argument("--only", default="", help="comma list of steps to run: data,formulas,charts (default all)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-items-hook", action="store_true", help="v1.41: do not rebuild the item tabs at the end of a layout build (the run driver runs items_build --build as its own gated step)")
    ap.add_argument("--apply-thresholds", action="store_true", help="v1.41: the Thresholds tab takes the values in data/thresholds.csv (the user's limits); without it a rebuild keeps the values already on the tab")
    ap.add_argument("--layout", action="store_true", help="layout build (once): pack the Metrics blocks, add at least 50%% spare rows to each and to each data tab, write data/layout.json, then build everything")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    data_only = a.only == "data"          # refresh the data tabs and everything derived from them; the Dashboard tab (cells, charts, widths) is left exactly as it is
    if data_only and not a.layout and not os.path.exists("data/layout.json"):
        sys.exit("stop: --only data (the daily path) needs data/layout.json; it never falls back to the full path (D412)")
    import jira_guard as _JG
    _JG.check(cfg["paths"]["jira_dir"])          # inbox 187: refuse to start (before any Sheet read or write) on a failed or unfinished Jira pull
    if data_only:
        for lst_ in (OUR_TABS, ORDER):
            if "Dashboard" in lst_:
                lst_.remove("Dashboard")
    if not cfg.get("incidents", True):        # incidents=false: the incident data tab and charts are left out of this build
        for lst_ in (DATA_TABS, OUR_TABS, ORDER):
            if "Incident_Issues" in lst_:
                lst_.remove("Incident_Issues")
        TB.SPECS.pop("Incident_Issues", None)
    sid = {"real": cfg["sheet_id"], "scratch": cfg["scratch_sheet_id"]}.get(a.target, a.target)
    import itemfilters as _IFreg
    _IFreg.use_registry_for(sid)          # D417: this Sheet's saved-view registry (never the v141 default); stops before any write when it is missing
    started = D.iso(dt.datetime.now(dt.timezone.utc))
    log(f"derive (target {a.target})")
    R, T, meta, asof = D.derive(cfg, cfg["paths"]["derived"])
    L = cfg["labels"]
    J = T["Jira_Issues"]
    meta["statuses"] = sorted({t["from_status"] for t in T["Jira_Transitions"] if t["in_cycle_pop"]})
    meta["open_statuses"] = sorted({j["status"] for j in J if j["population"] == "open" and j["is_work_item"]})
    meta["open_types"] = sorted({j["type"] for j in J if j["population"] == "open"})
    meta["n_gitlab"] = sum(1 for c in T["Code_Changes"] if c["platform"] == "gitlab")
    meta["n_github"] = sum(1 for c in T["Code_Changes"] if c["platform"] == "github")
    meta["n_wip"] = sum(j["wip"] for j in J)
    meta["n_noowner"] = sum(1 for j in J if j["wip"] and j["owner_kind"] == "ownerless")
    meta["n_open_normal"] = sum(1 for c in T["Code_Changes"] if c["counted"] and c["state"] == "open" and c["class"] == "normal")
    nrows = {t: len(T[t]) for t in DATA_TABS}
    ind_n = len(R.rows)
    item_lvl, item_warn = "ok", []
    if not a.layout and (os.path.exists("data/items_layout.json") or os.environ.get("ITEMS_LAYOUT")):          # item tabs (AC70, A69): warn at 80 percent of a grid, refuse before a spill would fail
        import items_build as _IB
        _lay = json.load(open(_IB.LAY))
        _wi = len(T["Jira_Issues"]) + len(T["Incident_Issues"]) + len(T["Other_Items"])
        item_lvl, item_warn = _IB.capacity_status(_wi, len(T["Code_Changes"]), _lay)
        for _m in item_warn:
            log(("REFUSED " if item_lvl == "refuse" else "WARNING ") + _m)
    meta["health_untagged"] = sum(v.get("wi_untagged", 0) for v in meta.get("people_comp", {}).values())
    meta["health_people_tickets"] = sum(v.get("wi_ours", 0) + v.get("wi_other", 0) + v.get("wi_untagged", 0) for v in meta.get("people_comp", {}).values())          # v1.41: base of the untagged-ticket share (tickets credited to our people)
    if item_lvl == "warn":          # the Dashboard freshness line (A2) reads this cell: a plain sentence for a reader (A69)
        _pct = max(100 * _wi / _lay["wi_rows"], 100 * len(T["Code_Changes"]) / _lay["cc_rows"])
        meta["item_guard"] = f"Item lists are {_pct:.0f}% full: a layout rebuild is due."
    elif item_lvl == "refuse":
        meta["item_guard"] = "REFUSED: " + "; ".join(item_warn)[:280]
    else:
        meta["item_guard"] = ""
    layout_path = os.path.join("data", "layout.json")          # one layout for the real Sheet and every copy of it
    manifest = None
    if a.layout:
        MT.MANIFEST = None
        G0 = MT.build(meta, R.rows, cfg, nrows, ind_n)
        starts = G0.blocks + [("(end)", G0.row)]
        new, shift = [], 0
        for i, (key, st) in enumerate(starts[:-1]):
            size = starts[i + 1][1] - st
            new.append([key, st + shift])
            shift += max(5, -(-size // 2))          # at least 50% spare rows after each block
        import collections as _c
        _cnt = _c.Counter(r_["group"] for r_ in T["Incident_Issues"] if r_.get("group") and not r_["group"].startswith("Other Group") and r_["group"] in cfg["groups"])          # v1.34: the 4 Groups only; SBU-only incidents are in the SBU row
        _tc = {sp_: _c.Counter(r_["team"] for r_ in T["Incident_Issues"] if r_["split"] == sp_ and r_.get("team")) for sp_ in ("customer", "internal")}
        _tkey = {r_["team"]: (cfg["groups"].index(r_["group"]), r_["team"]) for r_ in R.rows if r_.get("team") and r_.get("group") in cfg["groups"]}
        manifest = {"blocks": new, "end": starts[-1][1] + shift, "incident_groups": [g_ for g_ in cfg["groups"] if _cnt.get(g_)],          # fixed Group order everywhere (AC69): the config order, never most-common-first
                    
                    "incident_teams": {sp_: sorted(_tc[sp_], key=lambda t_: _tkey.get(t_, (99, t_))) for sp_ in _tc},          # fixed order: Group order, then Team name (AC69)
                     "data_rows": {t: max(50, -(-nrows[t] * 3 // 2)) for t in DATA_TABS},
                    "note": "written by build.py --layout; pins every Metrics block start row and the data-tab range sizes (AC70)"}
        json.dump(manifest, open(layout_path, "w"), indent=1)
        log(f"layout written: {len(new)} blocks, {manifest['end']} Metrics rows reserved, data capacities {manifest['data_rows']}")
    elif os.path.exists(layout_path):
        manifest = json.load(open(layout_path))
    MT.MANIFEST = manifest
    try:
        G = MT.build(meta, R.rows, cfg, nrows, ind_n)
    except MT.LayoutError as e:
        sys.exit(f"LAYOUT: {e}")
    cap = {t: (manifest["data_rows"][t] if manifest else nrows[t]) for t in DATA_TABS}
    if item_lvl == "refuse":          # the one write a refused run makes: the guard text, so the Dashboard says why the data stopped (A69); nothing else is written
        if not a.dry_run and "item_guard" in G.names:
            from sheetlib import values_update as _vu
            r0_, c0_ = G.names["item_guard"][:2]
            _vu(sid, f"Metrics!{col_letter(c0_)}{r0_ + 1}", [[meta["item_guard"]]], "RAW")
        sys.exit("LAYOUT: " + "; ".join(item_warn))
    over = [t for t in DATA_TABS if nrows[t] > cap[t]]
    if over:
        sys.exit(f"LAYOUT: data tab {over[0]} has {nrows[over[0]]} rows, over its reserved {cap[over[0]]}: run the layout build (no write was made)")
    daily = bool(data_only and manifest and not a.layout)          # the daily data path: values only, no tab, chart, named range or rule is created or deleted
    G.meta_names = G.lv["names"]
    log(f"metrics grid {max(r for r, _ in G.cells)+1} rows; levels {len(G.meta_lv)}")
    if a.dry_run:
        json.dump(meta, open(os.path.join(cfg["paths"]["derived"], "meta.json"), "w"), indent=1, default=str)
        print("dry run ok", meta["counts"])
        return

    if a.only == "charts":
        m = get_meta(sid)
        ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in m["sheets"]}
        dels = [{"deleteEmbeddedObject": {"objectId": c["chartId"]}} for s in m["sheets"] for c in s.get("charts", [])]
        batch(sid, dels)
        head = PN.dashboard_header(G, meta, cfg)
        reqs, extras = CH.chart_requests(G, ids, meta, cfg, len(head), v4_cap(G, sid), win612(G, sid))
        batch(sid, reqs)
        log("charts rebuilt")
        return
    # ---------------------------------------------------------------- tabs
    m = get_meta(sid)
    existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in m.get("sheets", [])}
    old_named = {n["name"]: n["range"] for n in m.get("namedRanges", [])}          # before the rebuild: where each range was (used to re-point the Dashboard's charts in a data-only refresh)
    cur_thr = {}
    if "Thresholds" in existing:     # the Thresholds tab is the only place a threshold lives: keep the user's values on rebuild (read before any tab is deleted)
        cur_thr = None
        for attempt in range(4):
            try:
                cur_thr = {r[0]: r[1] for r in values_get(sid, "Thresholds!A:B") if len(r) > 1}
                break
            except Exception as e:
                log(f"threshold read attempt {attempt + 1} failed: {str(e)[-120:]}")
                time.sleep(4)
        if cur_thr is None:
            sys.exit("cannot read the existing Thresholds tab; stopping so the user's threshold values are not overwritten")
    # In place: a tab that exists keeps its sheetId (so the canvas link, tab colours, filter views, protections and viewers' comments survive);
    # it is cleared and resized. A tab is added only when missing. Named ranges and charts on our tabs are removed and re-added.
    full = sheets("get", params={"spreadsheetId": sid, "fields": "sheets(properties(sheetId,title),charts(chartId),protectedRanges(protectedRangeId))"})
    ours_present = {t: i for t, i in existing.items() if t in OUR_TABS}
    ids_pre = dict(existing)
    our_ids = set(ours_present.values())
    reqs = []
    for nr_ in m.get("namedRanges", []):
        if nr_.get("range", {}).get("sheetId", 0) in our_ids or "sheetId" not in nr_.get("range", {}) or (data_only and nr_.get("range", {}).get("sheetId") == existing.get("Dashboard")):
            reqs.append({"deleteNamedRange": {"namedRangeId": nr_["namedRangeId"]}})
    for s_ in full.get("sheets", []):
        if s_["properties"]["title"] in OUR_TABS or s_["properties"]["title"] in REMOVED_TABS:
            for c_ in s_.get("charts", []):
                reqs.append({"deleteEmbeddedObject": {"objectId": c_["chartId"]}})
    for t, i in ours_present.items():
        reqs.append({"unmergeCells": {"range": {"sheetId": i}}})
        reqs.append({"updateCells": {"range": {"sheetId": i}, "fields": "userEnteredValue,userEnteredFormat,note"}})
    for t, i in existing.items():
        if (t.startswith("Sheet") and t not in OUR_TABS) or t in REMOVED_TABS:
            reqs.append({"deleteSheet": {"sheetId": i}})
    holder = "_holder"
    if not existing or all(t.startswith("Sheet") or t in OUR_TABS for t in existing) and not ours_present:
        reqs = [{"addSheet": {"properties": {"title": holder}}}] + reqs
    sizes = {t: (cap[t] + 1, len(TB.SPECS[t][1])) for t in DATA_TABS}
    mrows = G.to_rows()
    _ig = json.load(open("data/items_layout.json"))["gid"] if os.path.exists("data/items_layout.json") else None
    ind = PN.individual_rows(R, asof, meta.get('people_comp'), window_start=meta['window_start'][:10], gids=({"W": _ig["Work items"], "C": _ig["Code changes"]} if _ig else None))
    thr = PN.thresholds_rows(cfg)
    if cur_thr and not a.apply_thresholds:
        for row in thr[1:]:
            if row[0] in cur_thr:
                try:
                    v = float(cur_thr[row[0]])
                    row[1] = int(v) if v == int(v) and "." not in str(cur_thr[row[0]]) else v
                except ValueError:
                    pass
    ros = PN.roster_rows(R)
    his = PN.history_rows(R)
    readme = PN.readme_rows(cfg, max((h['effective_from'] for hs in R.hist.values() for h in hs if not h.get('_synth')), default=''), len(R.rows))
    dic = PN.dictionary_rows(G)
    people_sorted = sorted(R.rows, key=lambda x: x["chart_name"])
    cand = {j["owner"] for j in J if j["owner_kind"] == "person" and j["population"] == "open"} & {c["author"] for c in T["Code_Changes"] if c["state"] == "merged"}
    pick = next(((p_["chart_name"], i_ + 2) for i_, p_ in enumerate(people_sorted) if p_["chart_name"] in cand), None)
    prm = PN.prompt_rows(G, meta, cfg, pick)
    can = PN.canvas_rows(G)
    fail = PN.failing_rows()
    runl = PN.scrub_grid(PN.run_log_rows(cfg, meta, STATS, started))
    for _m in item_warn:          # the 80 percent warning goes into the Log tab too
        runl.append([runl[-1][0] if runl and runl[-1] else "", "item tab capacity", "", "", "", "", _m])
    dash_head = PN.dashboard_header(G, meta, cfg)
    cov = PN.coverage_tab_rows(G, cfg)
    import identity_tab as IDT          # v1.43g AC84: the Identity tab, every column of data/identity.csv, rebuilt on every refresh
    ident = IDT.grid(cfg["paths"]["identity"], str(meta["as_of"]).replace("T", " "))
    sizes.update({"Metrics": (len(mrows) + 5, max(len(r) for r in mrows) + 2), "Individual": (len(ind) + 2, len(ind[0])),
                  "Thresholds": (len(thr) + 2, 4), "Roster": (len(ros) + 2, len(ros[0])), "Roster_History": (len(his) + 2, 5),
                  "README": (len(readme) + 2, 1), "Data_Dictionary": (len(dic) + 2, 6), "Prompt_Library": (len(prm) + 2, 7),
                  "Run_Log": (len(runl) + 2, 7), "Failing_Lists": (PN.FAIL_ROWS, len(PN.FAIL_LISTS) * 3), "canvas_source": (len(can) + 2, len(can[0])), "Dashboard": (len(dash_head) + 330, 30), "Coverage": (len(cov) + 2, 4), "Identity": (len(ident) + 2, len(ident[0])), "Alert details": (3 + max(PN.ALERT_CAPS), 52)})          # v1.41: 3 header rows + the largest block capacity (the capacities already hold the 50% spare)
    import tabsize as _TS
    if not (data_only and manifest and not a.layout) or not (manifest or {}).get("tab_sizes"):
        if a.layout and manifest is not None:          # layout build: reserve at least 50 percent spare rows on the text tabs and pin them
            _res = _TS.reserve(sizes)
            _res["Alert details"] = list(sizes["Alert details"])          # no extra spare on top of the block capacities
            manifest["tab_sizes"] = _res
            json.dump(manifest, open(layout_path, "w"), indent=1)
            sizes.update({t_: tuple(v_) for t_, v_ in _res.items()})
    else:          # daily path: never resize a text tab; refuse before any write when the text would overflow
        _sz, _msgs = _TS.apply_daily(sizes, manifest["tab_sizes"])
        if _msgs:
            sys.exit("LAYOUT: " + "; ".join(_msgs))
        sizes.update(_sz)
        _g = sheets("get", params={"spreadsheetId": sid, "fields": "sheets(properties(title,gridProperties(rowCount,columnCount)))"})          # v1.43 B4: the daily path refuses before any write that would pass 9.5M cells
        _act = {s_["properties"]["title"]: (s_["properties"]["gridProperties"]["rowCount"], s_["properties"]["gridProperties"]["columnCount"]) for s_ in _g.get("sheets", []) if "gridProperties" in s_["properties"]}
        _ns, _nn = _TS.no_shrink({t_: v_ for t_, v_ in sizes.items() if t_ in OUR_TABS}, _act)          # D415: the daily path never shrinks a tab (rows or columns)
        sizes.update(_ns)
        for _n in _nn:
            log("NO SHRINK: " + _n)
        log(f"tab sizes: {len(_nn)} computed below the actual size and kept")
        _tot, _cm = _TS.cell_guard({s_["properties"]["title"]: (s_["properties"]["gridProperties"]["rowCount"], s_["properties"]["gridProperties"]["columnCount"]) for s_ in _g.get("sheets", []) if "gridProperties" in s_["properties"]},
                                   {t_: v_ for t_, v_ in sizes.items() if t_ in OUR_TABS})
        if _cm:
            sys.exit("; ".join(_cm))
    defs = []     # (name, tab, r0, c0, r1, c1)
    for t in DATA_TABS:
        pre, spec = TB.SPECS[t]
        for j, (cn, kind, unit, d) in enumerate(spec):
            defs.append((f"{pre}_{cn}", t, 1, j, cap[t], j))
        defs.append((f"tab_{pre}", t, 0, 0, cap[t], len(spec) - 1))
    for i in range(1, len(thr)):
        defs.append((thr[i][0], "Thresholds", i, 1, i, 1))
    for j, c in enumerate(PN.IND_COLS):
        defs.append((f"ind_{c[0]}" if j >= 1 else "ind_person", "Individual", 1, j, len(ind) - 1, j))
    for nm, (r0, c0, r1, c1) in G.names.items():
        defs.append((nm, "Metrics", r0, c0, r1, c1))
    defs.append(("roster_names", "Roster", 1, 0, len(ros) - 1, 0))
    defs.append(("freshness", "Dashboard", 1, 0, 1, 0))
    prefix = cfg.get("name_prefix", "") if a.target not in ("real",) else ""
    pf = lambda v: v
    if prefix:
        import re
        allnames = sorted({d[0] for d in defs}, key=len, reverse=True)
        name_pat = re.compile(r"(?<![A-Za-z0-9_.!'])(" + "|".join(re.escape(x) for x in allnames) + r")(?![A-Za-z0-9_(!'])")

        def pf(v):
            if isinstance(v, str) and v.startswith("="):
                parts = v.split('"')
                for i in range(0, len(parts), 2):
                    parts[i] = name_pat.sub(lambda m_: prefix + m_.group(1), parts[i])
                return '"'.join(parts)
            return v
        for grid in (mrows, ind, prm, can, dash_head, fail):
            for row in grid:
                for i, v in enumerate(row):
                    row[i] = pf(v)
        defs = [(prefix + d[0],) + d[1:] for d in defs]
    if daily:
        # AC70: nothing is created or deleted. Every range must already sit where this run computes it, every tab must exist, and nothing may exceed its reserved size.
        import daily_ranges as DR          # D414: a Metrics block may grow or shrink inside its reserved space; start, columns and tab must still match
        missing = [t for t in OUR_TABS if t not in ours_present]
        mism, resized, over = DR.classify(defs, old_named, ids_pre, manifest["blocks"] + [["(end)", manifest["end"]]])
        if missing or mism or over:
            sys.exit(f"LAYOUT: the Sheet does not match the layout (missing tabs {missing}, ranges not at their anchor {mism[:5]}, ranges growing past their block {over[:5]}); run the layout build. No write was made.")
        _nrid = {n_["name"]: n_["namedRangeId"] for n_ in m.get("namedRanges", [])}
        _resize = [{"updateNamedRange": {"namedRange": {"namedRangeId": _nrid[nm_], "name": nm_, "range": dict(old_named[nm_], endRowIndex=ne_)}, "fields": "range"}} for nm_, ne_, _oe in resized]
        log(f"named ranges resized in place (end row only): {len(resized)}")
        reqs = [r_ for r_ in reqs if "unmergeCells" in r_ or "updateCells" in r_] + _resize          # values only plus the in-place resize of ranges whose block grew or shrank (nothing created or deleted)
        # no clearing of the tabs the Dashboard reads (charts would be empty for minutes): their values are written over, and any leftover tail is cleared after the write
        keep_ids = set(ours_present.values())          # daily path: no tab of ours is cleared (values, formats and notes stay; the writes below only change differing rows)
        reqs = [r_ for r_ in reqs if not (("unmergeCells" in r_ and r_["unmergeCells"]["range"]["sheetId"] in keep_ids) or ("updateCells" in r_ and r_["updateCells"]["range"]["sheetId"] in keep_ids))]
    if reqs:
        batch(sid, reqs)
    # purge by name (also removes names left dangling by an earlier deleted tab)
    purge = [] if daily else [{"deleteNamedRange": {"namedRangeId": d[0]}} for d in defs]
    for k in range(0, len(purge), 200):
        batch(sid, purge[k:k + 200])
    reqs = []
    order_t = []
    for t in OUR_TABS:
        r_, c_ = sizes[t]
        froz = 0 if t in ("README", "Dashboard") else 1
        if t in ours_present:
            reqs.append({"updateSheetProperties": {"properties": {"sheetId": ours_present[t], "gridProperties": {"rowCount": max(r_, 2), "columnCount": max(c_, 2), "frozenRowCount": froz}},
                                                   "fields": "gridProperties.rowCount,gridProperties.columnCount" + ("" if daily else ",gridProperties.frozenRowCount")}})
        else:
            reqs.append({"addSheet": {"properties": {"title": t, "gridProperties": {"rowCount": max(r_, 2), "columnCount": max(c_, 2), "frozenRowCount": froz}}}})
        order_t.append(t)
    resp = batch(sid, reqs)
    ids = dict(ours_present)
    if data_only and "Dashboard" in existing:
        ids["Dashboard"] = existing["Dashboard"]
    for rep, t in zip(resp["replies"], order_t):
        if "addSheet" in rep:
            ids[t] = rep["addSheet"]["properties"]["sheetId"]
    # drop the holder / default sheet
    m = get_meta(sid)
    dels = [{"deleteSheet": {"sheetId": s_["properties"]["sheetId"]}} for s_ in m["sheets"]
            if s_["properties"]["title"] == holder or (s_["properties"]["title"].startswith("Sheet") and s_["properties"]["title"] not in OUR_TABS)]
    if dels:
        batch(sid, dels)
    log("tabs created")

    # ---------------------------------------------------------------- named ranges
    nr = [{"addNamedRange": {"namedRange": {"name": nm, "range": {
        "sheetId": ids[tab], "startRowIndex": r0, "endRowIndex": r1 + 1, "startColumnIndex": c0, "endColumnIndex": c1 + 1}}}}
          for (nm, tab, r0, c0, r1, c1) in defs]
    if not daily:
        for k in range(0, len(nr), 150):
            batch(sid, nr[k:k + 150])
    log(f"named ranges {len(nr)}" + (" (unchanged: daily path)" if daily else ""))

    # ---------------------------------------------------------------- data tabs
    fmt = []
    for t in DATA_TABS:
        rows = TB.tab_rows(t, T[t])
        if daily:
            write_diff(sid, t, rows, "RAW", log)
        else:
            write_grid(sid, t, rows, option="RAW", log=log if len(rows) > 5000 else None)
        if daily:          # clear the rows below the new data (the tab was not cleared first)
            batch(sid, [{"updateCells": {"range": {"sheetId": ids[t], "startRowIndex": len(rows), "endRowIndex": cap[t] + 1}, "fields": "userEnteredValue"}}])
        pre, spec = TB.SPECS[t]
        for j, (cn, kind, unit, d) in enumerate(spec):
            if kind in ("dt", "date"):
                pat = TB.FMT_DT if kind == "dt" else TB.FMT_DATE
                fmt.append({"repeatCell": {"range": {"sheetId": ids[t], "startRowIndex": 1, "endRowIndex": nrows[t] + 1, "startColumnIndex": j, "endColumnIndex": j + 1},
                                           "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE_TIME" if kind == "dt" else "DATE", "pattern": pat}}},
                                           "fields": "userEnteredFormat.numberFormat"}})
        log(f"{t}: {nrows[t]} rows")
    batch(sid, fmt)

    # ---------------------------------------------------------------- simple tabs
    (write_diff(sid, "Thresholds", thr, "USER_ENTERED", log) if daily else write_grid(sid, "Thresholds", thr))
    def small(name, rows, option="USER_ENTERED"):
        """daily path: only changed rows are written and rows below the new end are cleared; layout path: written in full"""
        if not daily:
            return write_grid(sid, name, rows, option=option)
        write_diff(sid, name, rows, option, log)
        if name in ids:
            batch(sid, [{"updateCells": {"range": {"sheetId": ids[name], "startRowIndex": len(rows)}, "fields": "userEnteredValue"}}])
    small("Roster", ros, "RAW")
    small("Roster_History", his, "RAW")
    small("Identity", ident, "RAW")
    small("README", readme)
    small("Data_Dictionary", dic, "RAW")
    small("Run_Log", runl, "RAW")
    log("static tabs written")
    # ---------------------------------------------------------------- Individual then Metrics (formulas)
    small("Individual", ind)
    mfmt = []
    (write_diff(sid, "Metrics", mrows, "USER_ENTERED", log) if daily else write_grid(sid, "Metrics", mrows, log=log))
    if daily:          # rows below the last written Metrics row (a block that shrank leaves none inside the layout: the grid above is written in full)
        batch(sid, [{"updateCells": {"range": {"sheetId": ids["Metrics"], "startRowIndex": len(mrows), "endRowIndex": manifest["end"] + 10}, "fields": "userEnteredValue"}}])
    log("Metrics written")
    # serial formats on Metrics date columns: week columns and as-of cells
    for nm in ("m_throughput", "m_throughput_chart", "m_created_done", "m_code_week", "m_code_week_chart", "m_merged_group"):
        r0, c0, r1, c1 = G.names[nm]
        mfmt.append({"repeatCell": {"range": {"sheetId": ids["Metrics"], "startRowIndex": r0 + 1, "endRowIndex": r1 + 1, "startColumnIndex": 0, "endColumnIndex": 1},
                                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": TB.FMT_DATE}}}, "fields": "userEnteredFormat.numberFormat"}})
    for nm in ("m_cfd", "m_cfd_chart"):
        r0, c0, r1, c1 = G.names[nm]
        mfmt.append({"repeatCell": {"range": {"sheetId": ids["Metrics"], "startRowIndex": r0 + 1, "endRowIndex": r1 + 1, "startColumnIndex": 0, "endColumnIndex": 1},
                                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": TB.FMT_DATE}}}, "fields": "userEnteredFormat.numberFormat"}})
    for nm in ("m_throughput_chart", "m_code_week_chart", "m_cfd_chart"):
        r0, c0, r1, c1 = G.names[nm]
        mfmt.append({"repeatCell": {"range": {"sheetId": ids["Metrics"], "startRowIndex": r0 + 1, "endRowIndex": r1 + 1, "startColumnIndex": 0, "endColumnIndex": 1},
                                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "mmm d"}}}, "fields": "userEnteredFormat.numberFormat"}})
    for nm in ("d_bugs612", "d_workmix612", "m_612_periods"):      # N1: period_start shown as an ISO date like the weeks everywhere else
        r0, c0, r1, c1 = G.names[nm]
        mfmt.append({"repeatCell": {"range": {"sheetId": ids["Metrics"], "startRowIndex": r0 + 1, "endRowIndex": r1 + 1, "startColumnIndex": c0 + 2, "endColumnIndex": c0 + 3},
                                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": TB.FMT_DATE}}}, "fields": "userEnteredFormat.numberFormat"}})
    for nm in ("asof", "window_start"):
        r0, c0, _, _ = G.names[nm]
        mfmt.append({"repeatCell": {"range": {"sheetId": ids["Metrics"], "startRowIndex": r0, "endRowIndex": r0 + 1, "startColumnIndex": 1, "endColumnIndex": 2},
                                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE_TIME", "pattern": TB.FMT_DT}}}, "fields": "userEnteredFormat.numberFormat"}})
    for nm in ("wk_last", "wk_first"):
        r0, c0, _, _ = G.names[nm]
        mfmt.append({"repeatCell": {"range": {"sheetId": ids["Metrics"], "startRowIndex": r0, "endRowIndex": r0 + 1, "startColumnIndex": 1, "endColumnIndex": 2},
                                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": TB.FMT_DATE}}}, "fields": "userEnteredFormat.numberFormat"}})
    # percent formats on rate columns of the level block
    for name in G.lv["names"]:
        if name.endswith("rate") or name.endswith("share_of_open") or name == "t_throughput_drop":
            cj = G.lv["ci"][name]
            mfmt.append({"repeatCell": {"range": {"sheetId": ids["Metrics"], "startRowIndex": G.lv["r0"] + 1, "endRowIndex": G.lv["r0"] + 1 + len(G.meta_lv), "startColumnIndex": cj, "endColumnIndex": cj + 1},
                                        "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}}, "fields": "userEnteredFormat.numberFormat"}})
    for rr, fmt in G.answer_cells:
        if fmt != "@":
            mfmt.append({"repeatCell": {"range": {"sheetId": ids["Metrics"], "startRowIndex": rr, "endRowIndex": rr + 1, "startColumnIndex": 1, "endColumnIndex": 2},
                                        "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT" if "%" in fmt else "NUMBER", "pattern": fmt}}}, "fields": "userEnteredFormat.numberFormat"}})
    batch(sid, mfmt)
    small("Prompt_Library", prm)
    small("canvas_source", can)
    small("Failing_Lists", fail)
    log("formulas written; giving Sheets time to calculate")
    time.sleep(8)

    notes = []
    for j, (cn, d) in enumerate(PN.IND_COLS):
        notes.append({"updateCells": {"rows": [{"values": [{"note": d + " (definitions: Definitions, About)"}]}], "fields": "note",
                                      "range": {"sheetId": ids["Individual"], "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": j, "endColumnIndex": j + 1}}})
    if _ig:          # A74: a note on each Other and untagged count says which filter lists the rows, and that it is not narrowed per person
        import itemfilters as _IFx
        _icn = [c[0] for c in PN.IND_COLS]
        for cn_, key_ in (("wi_other", "W:other:kind_is:other::sbu"), ("wi_untagged", "W:untagged:kind_is:untagged::sbu"), ("ch_other", "C:other:kind_is:other::sbu"), ("ch_untagged", "C:untagged:kind_is:untagged::sbu")):
            j_ = _icn.index(cn_)
            nt_ = f"Opens the top of the {_IFx.TABNAME[key_.split(chr(58), 1)[0]]} tab. The link cannot narrow to this person: the item tabs carry no owner column (A74). The filter below lists all our people's rows of this kind together: at least this number (this number is one person's part of them). " + _IFx.describe(key_) + "."
            notes.append({"updateCells": {"rows": [{"values": [{"note": nt_}]} for _ in range(len(ind) - 1)], "fields": "note",
                                          "range": {"sheetId": ids["Individual"], "startRowIndex": 1, "endRowIndex": len(ind), "startColumnIndex": j_, "endColumnIndex": j_ + 1}}})
    for name in G.lv["names"]:
        cj = G.lv["ci"][name]
        k = name.split("_")[0]
        d = PN.METRIC_DEFS.get(name) or (f"{k} ({PN.CHECK_DEFS[k]}): {name[len(k)+1:].replace('_', ' ')}" if k in PN.CHECK_DEFS else name.replace("_", " "))
        notes.append({"updateCells": {"rows": [{"values": [{"note": d + " (Definitions has the full definition)"}]}], "fields": "note",
                                      "range": {"sheetId": ids["Metrics"], "startRowIndex": G.lv["r0"], "endRowIndex": G.lv["r0"] + 1, "startColumnIndex": cj, "endColumnIndex": cj + 1}}})
        if "_days" in name or "_hours" in name or name in ("weeks_of_backlog", "reviews_per_week_12w"):
            notes.append({"repeatCell": {"range": {"sheetId": ids["Metrics"], "startRowIndex": G.lv["r0"] + 1, "endRowIndex": G.lv["r0"] + 1 + len(G.meta_lv), "startColumnIndex": cj, "endColumnIndex": cj + 1},
                                         "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.0"}}}, "fields": "userEnteredFormat.numberFormat"}})
    for k in range(0, len(notes), 100):
        batch(sid, notes[k:k + 100])
    # ---------------------------------------------------------------- Dashboard text and charts
    ad_rows, ad_starts = PN.alert_details_rows(G, cfg, PN.ALERT_CAPS, meta)
    jh = cfg.get("jira", {}).get("host", "")
    for row in dash_head:
        for j, v in enumerate(row):
            if isinstance(v, str) and v.startswith("{ALERT_LINK_"):
                k = int(v[len("{ALERT_LINK_"):-1])
                target = f'"#gid={ids["Alert details"]}&range={col_letter(ad_starts[k - 1])}1"'      # D76: every count links to its block on Alert details
                row[j] = pf(f'=HYPERLINK({target},alert{k})')
    if not data_only:
        write_grid(sid, "Dashboard", dash_head)
    # data-only refresh: the Dashboard is not written at all (v1.26: Alerts block columns are fixed by their widths, so no link moves)
    (write_diff(sid, "Coverage", PN.scrub_grid([[pf(v) for v in r] for r in cov]), "USER_ENTERED", log) if daily else write_grid(sid, "Coverage", PN.scrub_grid([[pf(v) for v in r] for r in cov])))
    (write_diff(sid, "Alert details", [[pf(v) for v in r] for r in ad_rows], "USER_ENTERED", log) if daily else write_grid(sid, "Alert details", [[pf(v) for v in r] for r in ad_rows]))
    batch(sid, [{"updateCells": {"rows": [{"values": [{"note": nt}]}], "fields": "note",          # a note on every linked number of Alerts blocks 7 and 8 (AC69)
                                 "range": {"sheetId": ids["Alert details"], "startRowIndex": r_, "endRowIndex": r_ + 1, "startColumnIndex": c_, "endColumnIndex": c_ + 1}}}
                for r_, c_, nt in PN.alert_link_notes(ad_starts, cfg, meta)])
    chart_row0 = len(dash_head)
    if data_only and a.layout:
        reqs, extras = [], {"dash": {}}          # the layout build leaves the charts alone: dashboard_build.py redraws every chart on the new anchors right after
    elif data_only:
        # The Dashboard's existing charts read Metrics by cell position. A refresh can move Metrics blocks, so every chart source range is re-pointed
        # to the same named range's new position (rows only; columns do not move). A chart range that matches no named range stops the build.
        reqs, extras = [], {"dash": {}}
        dsh = [x for x in sheets("get", params={"spreadsheetId": sid, "fields": "sheets(properties(sheetId,title),charts)"}).get("sheets", []) if x["properties"]["title"] == "Dashboard"]
        mid = ids["Metrics"]
        for ch in (dsh[0].get("charts", []) if dsh else []):
            spec = ch["spec"]
            def fix(src):
                if src.get("sheetId") != mid:
                    return
                r0, r1 = src.get("startRowIndex", 0), src.get("endRowIndex", 0)
                best = None
                for nm_, rg in old_named.items():
                    if rg.get("sheetId") == mid and rg.get("startRowIndex", 0) <= r0 and r1 <= rg.get("endRowIndex", 0) and nm_ in G.names:
                        size = rg["endRowIndex"] - rg["startRowIndex"]
                        if best is None or size < best[0]:
                            best = (size, nm_, rg)
                if best is None:
                    sys.exit(f"stop: a Dashboard chart range (Metrics rows {r0}-{r1}) matches no named range; the data-only refresh cannot re-point it")
                shift = G.names[best[1]][0] - best[2]["startRowIndex"]
                import daily_ranges as DR_
                src["startRowIndex"], src["endRowIndex"] = r0 + shift, DR_.chart_end(r1, best[2]["endRowIndex"], G.names[best[1]][2] + 1, shift)          # D414: a chart that read to the end of its block follows the block's new end
            def walk(o):
                if isinstance(o, dict):
                    for k_, v_ in o.items():
                        if k_ == "sources":
                            for src in v_:
                                fix(src)
                        else:
                            walk(v_)
                elif isinstance(o, list):
                    for v_ in o:
                        walk(v_)
            walk(spec)
            reqs.append({"updateChartSpec": {"chartId": ch["chartId"], "spec": spec}})
    else:
        reqs, extras = CH.chart_requests(G, ids, meta, cfg, chart_row0, v4_cap(G, sid), win612(G, sid))
    batch(sid, reqs)
    # v1.22: eight charts on the Dashboard, each with an answer card (formula over dk_* cells, AC44a) directly under it, the same width; tables and stat strips below
    fmt_reqs = []
    thin = {"style": "SOLID", "color": {"red": 0.6, "green": 0.7, "blue": 0.85}}
    DS = ids["Dashboard"]
    for key, e in extras["dash"].items():
        row, col, span, crow = e["row"], e["col"], e["span"], e["card_rows"]
        ans_ = PN.DASH_ANSWERS[key]
        write_grid(sid, "Dashboard", [[pf('="Answer: "&' + ans_[1:])]], start_row=row, start_col=col)
        rng_ = {"sheetId": DS, "startRowIndex": row, "endRowIndex": row + crow, "startColumnIndex": col, "endColumnIndex": col + span}
        fmt_reqs.append({"mergeCells": {"range": rng_, "mergeType": "MERGE_ALL"}})
        fmt_reqs.append({"repeatCell": {"range": rng_, "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "MIDDLE",
                                        "backgroundColor": {"red": 0.92, "green": 0.95, "blue": 0.99}, "textFormat": {"bold": True}}},
                                        "fields": "userEnteredFormat(wrapStrategy,verticalAlignment,backgroundColor,textFormat)"}})
        fmt_reqs.append({"updateBorders": {"range": rng_, "top": thin, "bottom": thin, "left": thin, "right": thin}})
        if key == "I2":          # plain-word table from d_incopen: plain headers, whole-day ages, no Blocker or Not Set row when its count is 0
            r_ = e["chart_row"]
            hdr_ = ["Incidents", "Priority", "Open now", "Median age (days)", "85th percentile age (days)", "Open more than 30 days"]
            body_ = ("=LET(f,FILTER(INDEX(d_incopen,2,1):INDEX(d_incopen,ROWS(d_incopen),6),"
                     "1-(((INDEX(d_incopen,2,2):INDEX(d_incopen,ROWS(d_incopen),2)=\"Blocker\")+(INDEX(d_incopen,2,2):INDEX(d_incopen,ROWS(d_incopen),2)=\"Not Set\")>0)"
                     "*(INDEX(d_incopen,2,3):INDEX(d_incopen,ROWS(d_incopen),3)=0))),"
                     "HSTACK(IF(INDEX(f,0,1)=\"customer\",\"Customer incidents\",\"Internal incidents\"),INDEX(f,0,2),INDEX(f,0,3),INDEX(f,0,4),INDEX(f,0,5),INDEX(f,0,6)))")
            write_grid(sid, "Dashboard", [hdr_], start_row=r_, start_col=0)
            write_grid(sid, "Dashboard", [[pf(body_)]], start_row=r_ + 1, start_col=0)
            fmt_reqs.append({"repeatCell": {"range": {"sheetId": DS, "startRowIndex": r_, "endRowIndex": r_ + 1, "startColumnIndex": 0, "endColumnIndex": 6},
                                            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "wrapStrategy": "WRAP", "verticalAlignment": "TOP"}}, "fields": "userEnteredFormat(textFormat,wrapStrategy,verticalAlignment)"}})
            fmt_reqs.append({"repeatCell": {"range": {"sheetId": DS, "startRowIndex": r_ + 1, "endRowIndex": r_ + 14, "startColumnIndex": 2, "endColumnIndex": 6},
                                            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0"}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}})
            fmt_reqs.append({"updateDimensionProperties": {"range": {"sheetId": DS, "dimension": "ROWS", "startIndex": r_, "endIndex": r_ + 1}, "properties": {"pixelSize": 42}, "fields": "pixelSize"}})
        strips_ = PN.DASH_STRIPS.get(key)
        if strips_:          # stat strips (AC44b): one label row and one value row per strip, cells A to H; label rows are tall enough for wrapped labels
            r_ = e["strip_row"]
            for label_, cells_ in strips_:
                if label_:
                    write_grid(sid, "Dashboard", [[label_]], start_row=r_, start_col=0)
                    fmt_reqs.append({"repeatCell": {"range": {"sheetId": DS, "startRowIndex": r_, "endRowIndex": r_ + 1, "startColumnIndex": 0, "endColumnIndex": 1},
                                                    "cell": {"userEnteredFormat": {"textFormat": {"italic": True}}}, "fields": "userEnteredFormat.textFormat"}})
                    r_ += 1
                write_grid(sid, "Dashboard", [[l for l, _, _ in cells_], [pf("=" + nm) for _, nm, _ in cells_]], start_row=r_, start_col=0)
                fmt_reqs.append({"repeatCell": {"range": {"sheetId": DS, "startRowIndex": r_, "endRowIndex": r_ + 1, "startColumnIndex": 0, "endColumnIndex": len(cells_)},
                                                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "wrapStrategy": "WRAP", "verticalAlignment": "TOP", "horizontalAlignment": "CENTER"}},
                                                "fields": "userEnteredFormat(textFormat,wrapStrategy,verticalAlignment,horizontalAlignment)"}})
                fmt_reqs.append({"updateDimensionProperties": {"range": {"sheetId": DS, "dimension": "ROWS", "startIndex": r_, "endIndex": r_ + 1}, "properties": {"pixelSize": 63}, "fields": "pixelSize"}})
                for j_, (_, _, nf_) in enumerate(cells_):
                    fmt_reqs.append({"repeatCell": {"range": {"sheetId": DS, "startRowIndex": r_ + 1, "endRowIndex": r_ + 2, "startColumnIndex": j_, "endColumnIndex": j_ + 1},
                                                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": nf_}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}})
                r_ += 2
    # alert table header bold (row 4)
    if not data_only:
        fmt_reqs.append({"repeatCell": {"range": {"sheetId": ids["Dashboard"], "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 5},
                                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat.textFormat"}})
    batch(sid, fmt_reqs)
    # column widths (the Dashboard's are left alone in a data-only refresh)
    batch(sid, [w_ for w_ in [{"updateDimensionProperties": {"range": {"sheetId": ids["Dashboard"], "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                                               "properties": {"pixelSize": 460}, "fields": "pixelSize"}},
                {"updateDimensionProperties": {"range": {"sheetId": ids["Dashboard"], "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                                               "properties": {"pixelSize": 170}, "fields": "pixelSize"}},
                {"updateDimensionProperties": {"range": {"sheetId": ids["Dashboard"], "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4},
                                               "properties": {"pixelSize": 230}, "fields": "pixelSize"}},
                {"updateDimensionProperties": {"range": {"sheetId": ids["Dashboard"], "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5},
                                               "properties": {"pixelSize": 500}, "fields": "pixelSize"}},
                {"updateDimensionProperties": {"range": {"sheetId": ids["Dashboard"], "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3},
                                               "properties": {"pixelSize": 140}, "fields": "pixelSize"}},
                {"updateDimensionProperties": {"range": {"sheetId": ids["Dashboard"], "dimension": "COLUMNS", "startIndex": 5, "endIndex": 8},
                                               "properties": {"pixelSize": 150}, "fields": "pixelSize"}},
                {"updateDimensionProperties": {"range": {"sheetId": ids["Coverage"], "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                                               "properties": {"pixelSize": 300}, "fields": "pixelSize"}},
                {"updateDimensionProperties": {"range": {"sheetId": ids["Coverage"], "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                                               "properties": {"pixelSize": 900}, "fields": "pixelSize"}},
                {"updateDimensionProperties": {"range": {"sheetId": ids["README"], "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                                               "properties": {"pixelSize": 900}, "fields": "pixelSize"}},
                {"updateCells": {"range": {"sheetId": ids["README"], "startRowIndex": 0, "endRowIndex": len(readme) + 2, "startColumnIndex": 0, "endColumnIndex": 1},
                                 "rows": [], "fields": "userEnteredFormat.wrapStrategy"}} if False else {"repeatCell": {
                    "range": {"sheetId": ids["README"], "startRowIndex": 0, "endRowIndex": len(readme) + 2, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat.wrapStrategy"}}] if not daily and not (data_only and w_.get("updateDimensionProperties", {}).get("range", {}).get("sheetId") == ids.get("Dashboard"))])          # the daily path leaves every width and format as the layout and tabs steps set them
    log("charts created")

    # ---------------------------------------------------------------- protection (warning only) and order
    has_prot = {s_["properties"]["title"] for s_ in sheets("get", params={"spreadsheetId": sid, "fields": "sheets(properties(title),protectedRanges(protectedRangeId))"}).get("sheets", [])
                if s_.get("protectedRanges")}
    prot = [{"addProtectedRange": {"protectedRange": {"range": {"sheetId": ids[t]}, "warningOnly": True,
                                                       "description": "Script-written. Edits are overwritten on refresh."}}}
            for t in ["Metrics"] + DATA_TABS + ["canvas_source"] if t not in has_prot]
    if prot and not daily:
        batch(sid, prot)
    m = get_meta(sid)
    cur = {s_["properties"]["title"]: s_["properties"]["sheetId"] for s_ in m["sheets"]}
    if "Insights" not in cur:
        batch(sid, [{"addSheet": {"properties": {"title": "Insights"}}}])
        write_grid(sid, "Insights", [["AI-written summary (pending). Numbers here are verbatim copies of cited Metrics cells; no individual is named."]], option="RAW")
        m = get_meta(sid)
        cur = {s_["properties"]["title"]: s_["properties"]["sheetId"] for s_ in m["sheets"]}
    # tab renames from data/config.json (tab_renames: old title -> new title): title only, the sheetId is kept; a no-op when the old tab is absent or the new title is taken
    ren = [(o_, n_) for o_, n_ in cfg.get("tab_renames", {}).items() if o_ in cur and n_ not in cur]
    if ren:
        batch(sid, [{"updateSheetProperties": {"properties": {"sheetId": cur[o_], "title": n_}, "fields": "title"}} for o_, n_ in ren])
        for o_, n_ in ren:
            cur[n_] = cur.pop(o_)
            log(f"renamed tab {o_!r} to {n_!r} (same sheetId)")
    # tab order and hidden machinery tabs come from data/config.json (tab_order, hidden_tabs): a rebuild recreates tabs visible, so this runs every time
    hidden = [t for t in cfg.get("hidden_tabs", []) if t in cur]
    in_order = [t for t in cfg.get("tab_order", ORDER) if t in cur]         # a hidden tab that is listed in tab_order (the Explore canvas) keeps its place there
    rest = [t for t in cur if t not in in_order and t not in hidden]
    final = in_order + rest + [t for t in hidden if t not in in_order]
    props = [{"updateSheetProperties": {"properties": {"sheetId": cur[t], "index": i, "hidden": t in hidden}, "fields": "index,hidden"}}
             for i, t in enumerate(final)]
    # tab colour by purpose (config tab_purposes and tab_colors), applied on every build
    color_of = {}
    for purpose, tabs_ in cfg.get("tab_purposes", {}).items():
        hx = cfg.get("tab_colors", {}).get(purpose)
        for t_ in tabs_:
            if hx:
                color_of[t_] = hx
    for t_ in final:
        hx = color_of.get(t_)
        rgbc = ({"red": int(hx[0:2], 16) / 255, "green": int(hx[2:4], 16) / 255, "blue": int(hx[4:6], 16) / 255} if hx else None)
        props.append({"updateSheetProperties": {"properties": {"sheetId": cur[t_], "tabColorStyle": ({"rgbColor": rgbc} if rgbc else {})}, "fields": "tabColorStyle"}})
    if not daily:          # order, hidden state and colours belong to the layout build; the daily path leaves them as they are
        batch(sid, props)
    log(f"tab order and colours applied; hidden: {hidden}" if not daily else "tab order, hidden state and colours left as they are (daily path)")
    if not daily and not a.skip_items_hook and os.path.exists("data/items_layout.json"):
        # v1.41: this build deleted and re-added the named ranges, and Sheets does NOT re-bind formulas to a re-created name (every item-tab formula turns to #REF!): rebuild both item tabs now, then run the error gate
        log("named ranges were re-created: rebuilding the item tabs (items_build --build), then the error gate")
        import items_build as _IB2, error_gate as _EG
        _IB2.main(["--target", sid, "--config", a.config, "--build"])
        _bad = _EG.run(sid, list(_EG.ITEM_TABS))
        if _bad:
            sys.exit("ERROR GATE: " + "; ".join(f"{t}: {len(h)} error cells" for t, h in _bad.items()))
        log("error gate passed on the item tabs (run error_gate.py --target <id> after the Teams and Dashboard builds for the tabs that read them)")
    json.dump({"sheet_id": sid, "ids": ids, "meta": {k: v for k, v in meta.items() if k not in ("statuses", "open_statuses", "open_types")},
               "built_at": D.iso(dt.datetime.now(dt.timezone.utc)), "stats": STATS},
              open(os.path.join(cfg["paths"]["derived"], "last_build.json"), "w"), indent=1, default=str)
    log(f"done. api stats {STATS}")


if __name__ == "__main__":
    main()
