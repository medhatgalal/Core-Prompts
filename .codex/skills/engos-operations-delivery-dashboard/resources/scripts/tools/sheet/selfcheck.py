#!/usr/bin/env python3
"""Builder's own spot check (NOT the independent verification): recompute metrics in Python from the derived rows and compare with the
Sheet's Metrics cells. Same code base as the Sheet, so it only catches formula mistakes, not definition mistakes.
Usage: selfcheck.py [--config data/config.json] [--target real|scratch] [--out file]"""
import argparse, collections, json, os, re, sys, statistics
import datetime as dt_
sys.path.insert(0, os.path.dirname(__file__))
import derive as D
from sheetlib import values_get, get_meta, col_letter
import metrics as MT



def _tabname(sid, reader_title):
    """a check names tabs by their reader titles (Alerts, About, ...); a Sheet that still carries the old titles (the real Sheet) is read under them: the inverse of sheetlib's RENAMED shim"""
    import sheetlib as _SL
    inv = {v: k for k, v in _SL.RENAMED.items()}
    return reader_title if _SL._use_new(sid) else inv.get(reader_title, reader_title)

def pct(v, p):
    return D.pct_inc(v, p)


def _stuck_days():
    """v1.41: the stuck limit is the t_stuck_days row of data/thresholds.csv (a fixed number of days, no longer the Group P85)"""
    import csv
    return float(next(r["value"] for r in csv.DictReader(open("data/thresholds.csv")) if r["name"] == "t_stuck_days"))


def incident_outside(body, li, oc):
    """rows the ladder does not place: level not Team, Group or SBU. G4: a created-only row (ours when created, retagged later: level blank, ours_c 1) is allowed; it counts as created and nowhere else."""
    ok_levels = ("Team", "Group", "SBU")
    return [r for r in body if li is None or li >= len(r) or (r[li] not in ok_levels and not (r[li] == "" and oc is not None and oc < len(r) and r[oc] in (1, "1")))]


def scorecard_row(col_a):
    """0-based index of the 'Scorecard' title in Dashboard column A, or -1. v1.43c AC79 put five blocks above it (row 10 now; row 4 before), so the scorecard rows are found, not fixed."""
    return next((i for i, v in enumerate(col_a) if str(v).strip() == "Scorecard"), -1)


def selftest():
    old = ["Automation Engineering Dashboard", "Last data refresh", "", "Scorecard", "Question"]
    new = ["Automation Engineering Dashboard", "Last data refresh", "Group and Team views", "Flow (tickets)", "Epics and initiatives", "Work mix", "Quality", "Incidents", "", "Scorecard", "Question"]
    ok = scorecard_row(old) == 3 and scorecard_row(new) == 9 and scorecard_row(["x"]) == -1 and scorecard_row([]) == -1
    ok &= scorecard_row(new) != 3          # the old fixed row 3 reads the AC79 Dashboard one block off: the copy-7 selfcheck failure (76 differences)
    li, oc = 2, 3
    ok &= incident_outside([["x", "y", "Team", 1], ["x", "y", "", 1]], li, oc) == []          # IA-1822: blank level, ours at creation
    ok &= len(incident_outside([["x", "y", "", 0]], li, oc)) == 1 and len(incident_outside([["x", "y", "Other", 1]], li, oc)) == 1          # not placed and not ours at creation
    ok &= 3 + 12 == 15          # the scorecard stray-cell range keeps its old size (rows to the end of the ten slots)
    print("selfcheck selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="data/config.json")
    ap.add_argument("--target", default="scratch")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    sid = {"real": cfg["sheet_id"], "scratch": cfg["scratch_sheet_id"]}.get(a.target, a.target)
    R, T, meta, asof = D.derive(cfg, cfg["paths"]["derived"])
    J, C = T["Jira_Issues"], T["Code_Changes"]
    LV = MT.level_rows(meta["groups"], R.rows, cfg["labels"])
    last = json.load(open(os.path.join(cfg["paths"]["derived"], "last_build.json"))) if os.path.exists(os.path.join(cfg["paths"]["derived"], "last_build.json")) else {}
    # locate the m_levels header row in the Sheet
    v = values_get(sid, "Metrics!A1:DZ%d" % (5000), "UNFORMATTED_VALUE")
    hdr_i = next(i for i, r in enumerate(v) if r and r[0] == "level" and len(r) > 10)
    hdr = v[hdr_i]
    rows = {(r[0], r[1], r[2]): r for r in v[hdr_i + 1: hdr_i + 1 + len(LV)]}

    def cell(key, name):
        r = rows[key]
        x = r[hdr.index(name)] if hdr.index(name) < len(r) else ""
        return x

    def num(x):
        try:
            return float(str(x).replace("%", "")) / (100 if "%" in str(x) else 1)
        except Exception:
            return None

    def inlevel(rec, lv, g, t, gk="group", tk="team"):
        return (g == "*" or rec[gk] == g) and (t == "*" or rec[tk] == t)

    res = []
    checks = 0

    def cmp(label, sheet, py, tol=1e-3):
        nonlocal checks
        checks += 1
        s = num(sheet)
        ok = (s is not None and py is not None and abs(s - py) <= max(tol, abs(py) * 1e-4)) or (py is None and sheet in ("", None))
        res.append((label, sheet, py, "OK" if ok else "DIFF"))

    sample = [LV[0], LV[1], LV[2], next(x for x in LV if x[0] == "Team" and x[2] not in ("Ownerless", "Unmapped"))]
    for key in sample:
        lv, g, t = key
        tag = f"{lv}:{g}/{t}"
        Jl = [j for j in J if inlevel(j, lv, g, t)]
        Cl = [c for c in C if inlevel(c, lv, g, t) and c["counted"]]
        openwi = [j for j in Jl if j["population"] == "open" and j["is_work_item"]]
        cmp(f"{tag} open_work_items", cell(key, "open_work_items"), len(openwi))
        cmp(f"{tag} wip", cell(key, "wip"), sum(j["wip"] for j in Jl))
        cmp(f"{tag} in_progress_no_owner", cell(key, "in_progress_no_owner"), sum(1 for j in Jl if j["wip"] and j["owner_kind"] == "ownerless"))
        cmp(f"{tag} aging_wip_over_p85", cell(key, "aging_wip_over_p85"), sum(1 for j in Jl if j["wip"] and j["start_age_days"] is not None and j["start_age_days"] > _stuck_days()))
        cyc = [j["cycle_days"] for j in Jl if j["in_cycle_pop"]]
        cmp(f"{tag} cycle_n", cell(key, "cycle_n"), len(cyc))
        cmp(f"{tag} cycle_median", cell(key, "cycle_median_days"), statistics.median(cyc) if cyc else None)
        cmp(f"{tag} cycle_p85", cell(key, "cycle_p85_days"), pct(cyc, 0.85) if cyc else None)
        lead = [j["lead_days"] for j in Jl if j["series"] == "main" and j["lead_days"] is not None]
        cmp(f"{tag} lead_median", cell(key, "lead_median_days"), statistics.median(lead) if lead else None)
        cmp(f"{tag} merged_12m", cell(key, "merged_12m"), sum(1 for c in Cl if c["state"] == "merged"))
        otm = [c["open_to_merge_days"] for c in Cl if c["state"] == "merged" and c["open_to_merge_days"] is not None]
        cmp(f"{tag} open_to_merge_median", cell(key, "open_to_merge_median_days"), statistics.median(otm) if otm else None)
        cmp(f"{tag} open_to_merge_p85", cell(key, "open_to_merge_p85_days"), pct(otm, 0.85) if otm else None)
        fr = [c["hours_to_first_review"] for c in Cl if c["state"] == "merged" and c["hours_to_first_review"] is not None]
        cmp(f"{tag} first_review_median", cell(key, "first_review_median_hours"), statistics.median(fr) if fr else None)
        nrm = [c for c in Cl if c["class"] == "normal"]
        wst = D.pt(meta["window_start"])
        n1 = [c for c in nrm if c["opened"] and c["opened"] >= wst]     # G2: A1 counts changes opened on or after the window start
        cmp(f"{tag} A1_denominator", cell(key, "A1_denominator"), len(n1))
        cmp(f"{tag} A1_linked", cell(key, "A1_linked"), sum(1 for c in n1 if c["key_state"] == "linked"))
        cmp(f"{tag} A5_count", cell(key, "A5_count"), sum(1 for c in nrm if c["state"] == "merged" and c["key_state"] == "no_key"))
        cmp(f"{tag} J4_fail", cell(key, "J4_fail"), sum(1 for j in Jl if j["j4_pass"] == 0))
        cmp(f"{tag} J6_fail", cell(key, "J6_fail"), sum(1 for j in Jl if j["j6_pass"] == 0))
        cmp(f"{tag} C2_pass", cell(key, "C2_pass"), sum(1 for c in nrm if c["state"] != "closed" and c["c2_pass"] == 1))
        cmp(f"{tag} C3_fail", cell(key, "C3_fail"), sum(1 for c in nrm if c["state"] != "closed" and c["c3_pass"] == 0))
        cmp(f"{tag} open_changes", cell(key, "open_changes"), sum(1 for c in Cl if c["state"] == "open"))
        cmp(f"{tag} A3_count", cell(key, "A3_count"), sum(1 for j in Jl if j["a3_status_lag"] == 1))
        cmp(f"{tag} A4_count", cell(key, "A4_count"), sum(1 for j in Jl if j["a4_no_code"] == 1))
    # level roll-up: Teams of a Group sum to the Group (AC23) for open work items, merged
    for g in ([] if cfg.get("ladder") else meta["groups"]):          # v1.34: the Teams of a Group no longer sum to the Group (former Teams, Group only); the Teams tab checks add up with those rows
        for name in ("open_work_items", "wip", "merged_12m", "in_progress_no_owner"):
            s = sum(num(cell(k, name)) or 0 for k in rows if k[0] == "Team" and k[1] == g)
            cmp(f"rollup {g} {name}", cell(("Group", g, "*"), name), s)
    ladder_ = bool(cfg.get("ladder"))
    _TF = "cf[" + cfg["jira"]["fields"]["team"].split("_")[-1] + "]"          # the Jira Team field as JQL writes it, from config jira.fields.team
    xg_ = {cfg["labels"].get("sbu_only", "SBU only")} | set(cfg["jira"]["sbu_only_groups"])          # v1.34: SBU-only tickets (A59) and the Groups in config jira.sbu_only_groups (an ended Group) count in the SBU row and in no Group row
    for name in ("open_work_items", "wip", "merged_12m"):
        s = sum(num(cell(k, name)) or 0 for k in rows if k[0] == "Group")
        if ladder_ and name == "merged_12m":
            continue          # code attribution is by ticket or author: the Group rows plus the rest are checked on the Teams tab and per level above
        if ladder_:
            if name == "open_work_items":
                s += sum(1 for j in J if j["group"] in xg_ and j["is_work_item"] and j["status_category"] != "done")
            elif name == "wip":
                s += sum(1 for j in J if j["group"] in xg_ and j["wip"])
            elif False:
                s += sum(1 for c in C if c["group"] in xg_ and c["state"] == "merged" and c["class"] == "normal" and c["counted"] and c["merged_at"] and c["merged_at"] >= asof - dt_.timedelta(days=cfg["window_days"]))
        cmp(f"rollup SBU {name}" + (" (Group rows + " + " and ".join(["SBU-only"] + cfg["jira"]["sbu_only_groups"]) + ", from the derived rows)" if ladder_ else ""), cell(("SBU", "*", "*"), name), s)
    # AC29: per-person counts add up to the Team totals (Ownerless and Unmapped are separate rows)
    iv = values_get(sid, "Individual!A1:AB200", "UNFORMATTED_VALUE")
    import panels as _PNh
    _inv = {v: k for k, v in _PNh.IND_HEADERS.items()}
    ih = [_inv.get(h, h) for h in iv[0]]
    ppl = [dict(zip(ih, r)) for r in iv[1:] if r]
    for key in [x for x in LV if x[0] == "Team" and x[2] not in ("Ownerless", "Unmapped") and not ladder_]:          # v1.34: the person view is the owner view, no longer the team numbers (AC29 person rows are checked separately)
        lv, g, t = key
        mem = [p for p in ppl if p["group"] == g and p["team"] == t]
        cmp(f"AC29 {g}/{t} sum of person wip vs team wip", cell(key, "wip"), sum(num(p["wip"]) or 0 for p in mem))
        cmp(f"AC29 {g}/{t} sum of person open_changes vs team open_changes", cell(key, "open_changes"), sum(num(p["open_changes"]) or 0 for p in mem))
    # AC29 (A76): person rows show exact counts and shares and sort by name (no ranking); the grouped Other breakdown keeps '<5'
    def ceq(label, got, want):
        nonlocal checks
        checks += 1
        res.append((label, got, want, "OK" if got == want else "DIFF"))
    try:
        _hdr = iv[0]; _ix = {h: i for i, h in enumerate(_hdr)}
        _names = [r[0] for r in iv[1:] if r and r[0]]
        ceq("AC29 person rows sort by name (no ranking)", _names == sorted(_names, key=lambda x: x), True)
        _txt = [(r[0], k_) for r in iv[1:] if r and r[0] for k_ in ("Work in progress", "Blocked items", "Tickets: ours", "Tickets: Other", "Tickets: untagged", "Changes: ours", "Changes: Other", "Changes: untagged") if len(r) > _ix[k_] and isinstance(r[_ix[k_]], str) and r[_ix[k_]] != ""]
        ceq("AC29 no person-row count is text (no '<5' on person rows, A76) (person, column)", _txt[:3], [])
        ceq("AC29 every person row says its history basis", sum(1 for r in iv[1:] if r and r[0] and str(r[_ix["History basis"]]).startswith(("approximate", "exact"))), sum(1 for r in iv[1:] if r and r[0]))
    except Exception as e_ind:
        ceq("AC29 person-row checks could run", str(e_ind)[:120], "")
    # Alerts M2 (alert 3, people over the WIP limit) equals a recompute from the derived tickets: people with more in-progress items than t_wip_per_person (SBU row of the Metrics column, Alerts block 3 count)
    try:
        _thr = {r[0]: r[1] for r in values_get(sid, "Thresholds!A1:B30", "UNFORMATTED_VALUE") if len(r) > 1}
        _lim = float(_thr["t_wip_per_person"])
        _wipc = collections.Counter(j["owner"] for j in T["Jira_Issues"] if j.get("wip") == 1 and j.get("owner_kind") == "person")
        _want = sum(1 for _o, _n in _wipc.items() if _n > _lim)
        _m2 = values_get(sid, "Alert details!M2", "FORMATTED_VALUE")
        _got = int(re.match(r"\s*(\d+)", _m2[0][0]).group(1)) if _m2 and _m2[0] else None
        checks += 1
        res.append(("Alerts M2 (people over the WIP limit) equals a recompute from the derived tickets", _got, _want, "OK" if _got == _want else "DIFF"))
    except Exception as e_m2:
        checks += 1
        res.append(("Alerts M2 recompute could run", str(e_m2)[:120], "", "DIFF"))
    # v1.26: the Dashboard tab itself (the 157 Metrics checks never read it: that is how a data-path write into Dashboard B5:B9 went unnoticed)
    try:
        import dashboard_build as DBd
        from sheetlib import sheets
        mm = sheets("get", params={"spreadsheetId": sid, "fields": "namedRanges"})
        nr = {n["name"]: n["range"] for n in mm["namedRanges"]}
        dfm = values_get(sid, "Dashboard!A1:Z40", "FORMULA")
        dvl = values_get(sid, "Dashboard!A1:Z40", "UNFORMATTED_VALUE")
        g = lambda rows_, r, c: (rows_[r][c] if r < len(rows_) and c < len(rows_[r]) else "")
        sc = scorecard_row([r_[0] if r_ else "" for r_ in dfm])          # AC79: the five blocks sit above the scorecard, so its rows are found, not fixed

        def eq(label, got, want):
            nonlocal checks
            checks += 1
            res.append((label, got, want, "OK" if str(got) == str(want) else "DIFF"))
        eq("Dashboard A1 title", g(dfm, 0, 0), "Automation Engineering Dashboard")
        eq("Dashboard A2 begins 'Last data refresh: '", str(g(dvl, 1, 0))[:19], "Last data refresh: ")
        eq("Dashboard has the Scorecard title in column A", sc >= 0, True)
        sc = max(sc, 3)
        for c, w in enumerate(["Question", "Now", "Limit", "Threshold", "Status", "Chart", "Items"]):
            eq(f"Dashboard header {col_letter(c)}{sc + 2}", g(dfm, sc + 1, c), w)
        for k, (key, q, dk, nf, limit, status, items) in enumerate(DBd.SLOTS):
            r = sc + 2 + k
            eq(f"Dashboard row {k + 1} question", (str(g(dfm, r, 0)) == DBd.question_cell(k, key, q)) if key in DBd.QUESTION_F else str(g(dfm, r, 0)).startswith(f"{k + 1}. {q}"), True)
            eq(f"Dashboard row {k + 1} Now formula (the number the status tests, v1.41)", g(dfm, r, 1), DBd.now_formula(key, dk))
            eq(f"Dashboard row {k + 1} Limit formula (v1.41 numeric limit)", g(dfm, r, 2), "=" + DBd.LIMIT_NUM[key])
            eq(f"Dashboard row {k + 1} Threshold formula", g(dfm, r, 3), limit)
            eq(f"Dashboard row {k + 1} Status formula", g(dfm, r, 4), status)
            eq(f"Dashboard row {k + 1} Chart link", str(g(dfm, r, 5)).startswith('=HYPERLINK("#gid='), True)
            dk = DBd.now_cell(key, dk)
            nrg = nr[dk]
            cellv = values_get(sid, f"Metrics!{col_letter(nrg['startColumnIndex'])}{nrg['startRowIndex'] + 1}", "UNFORMATTED_VALUE")
            eq(f"Dashboard row {k + 1} Now value equals {dk}", g(dvl, r, 1), cellv[0][0] if cellv and cellv[0] else "")
        stray = [(i + 1, c) for i in range(0, sc + 12) for c in range(7, 26) if g(dfm, i, c) != ""]
        eq("Dashboard: no stray cells right of column G in rows 1 to 15", stray, [])
        names_ = set(json.load(open("data/config.json"))["groups"]) | {"SBU", "Other", "Unknown"}
        dd = values_get(sid, "Dashboard!E1:G320", "UNFORMATTED_VALUE")
        blank_ = [(i + 1, r_[0]) for i, r_ in enumerate(dd) if r_ and r_[0] in names_ and (len(r_) < 3 or r_[1] == "" or r_[2] == "")]
        eq("Dashboard detail tables: no blank number cell on an SBU, Group, Other or Unknown row", blank_[:3], [])
        i2_ = values_get(sid, "Dashboard!A150:F300", "UNFORMATTED_VALUE")
        blank_i2 = [(i + 150, r_[0]) for i, r_ in enumerate(i2_) if r_ and str(r_[0]).startswith(("Customer incidents", "Internal incidents")) and (len(r_) < 6 or any(r_[c] == "" for c in range(2, 6)))]
        eq("Dashboard incident open table: no blank number cell (0 for a count, n/a for a median or P85 with no items)", blank_i2[:3], [])
        zero_med, cur_, d4w = [], None, {}
        for i, r_ in enumerate(dd):         # no 0 or 0.0 Oldest or median where the item count is 0 (Dashboard detail tables: D3 stuck, K1 blocked, D5 review hours against D4 merged)
            if len(r_) >= 3 and r_[0] == "Group":
                cur_ = r_[1]
                continue
            if not r_ or r_[0] not in names_ or cur_ is None or len(r_) < 3:
                continue
            if cur_ in ("Stuck now", "Blocked now") and r_[1] == 0 and r_[2] == 0:
                zero_med.append((i + 1, cur_, r_[0]))
            if cur_ == "Last week: changes merged":
                d4w[r_[0]] = (r_[1], r_[2])
            if cur_ == "Last week: median hours" and r_[0] in d4w:
                for k_ in (0, 1):
                    if d4w[r_[0]][k_] == 0 and r_[1 + k_] == 0:
                        zero_med.append((i + 1, "D5", r_[0]))
        eq("Dashboard detail tables: no 0 median or Oldest where the item count is 0 (n/a instead)", zero_med[:3], [])
        # v1.30 spacing: exactly one blank row at every seam (chart or table to its answer card, card to the next slot); the cell key sits inside its chart's band
        ds_ = sheets("get", params={"spreadsheetId": sid, "ranges": ["Dashboard!A1:G320"], "includeGridData": True,
                                    "fields": "sheets(properties(title,sheetId),merges,charts(position,spec(basicChart(chartType))),data(rowMetadata(pixelSize),rowData(values(formattedValue))))"})
        sh_ = next(x for x in ds_["sheets"] if x["properties"]["title"] == "Dashboard")
        grid_ = [[(v.get("formattedValue", "") or "") for v in r_.get("values", [])] for r_ in sh_["data"][0].get("rowData", [])]
        filled_ = lambda i: i < len(grid_) and any(x != "" for x in grid_[i])
        rh_ = [(m_.get("pixelSize") or 21) for m_ in sh_["data"][0].get("rowMetadata", [])]
        def bottom_row(anchor, px):          # the last row the chart image really covers, from the actual row heights
            acc, i = 0, anchor
            while i < len(rh_) and acc + rh_[i] < px:
                acc += rh_[i]; i += 1
            return i
        cards_ = sorted((m_["startRowIndex"], m_["endRowIndex"]) for m_ in sh_.get("merges", []) if m_["startColumnIndex"] == 0 and m_["endColumnIndex"] in (4, 6) and m_["endRowIndex"] - m_["startRowIndex"] >= 3)
        charts_ = sorted((c_["position"]["overlayPosition"]["anchorCell"]["rowIndex"], c_["position"]["overlayPosition"]["heightPixels"]) for c_ in sh_.get("charts", []))
        i2_ = next((i for i in range(len(grid_)) if grid_[i] and grid_[i][0] == "Open incidents now, by priority"), None)
        starts_ = sorted([c_[0] for c_ in charts_] + ([i2_] if i2_ is not None else []))
        bad_seams, seam_by_chart = [], {}
        for n_, (c0, c1) in enumerate(cards_):
            prev_starts = [x for x in starts_ if x < c0]
            if not prev_starts:
                continue
            st = prev_starts[-1]
            last_used = st
            for i in range(st, c0):
                if filled_(i):
                    last_used = i
            for cr_, hp_ in charts_:
                if cr_ == st:
                    last_used = max(last_used, bottom_row(cr_, hp_))
            blank_before = c0 - last_used - 1
            nxt = [x for x in starts_ if x >= c1]
            blank_after = (nxt[0] - c1) if nxt else 1
            seam_by_chart[st] = (blank_before, blank_after)
            if blank_before != 1 or blank_after != 1:
                bad_seams.append((c0 + 1, blank_before, blank_after))
        gh_ = next((i for i in range(len(grid_)) if len(grid_[i]) > 1 and grid_[i][0] == "Incidents" and grid_[i][1] == "Group or Team"), None)
        gap_i2 = None
        if gh_ is not None:
            k_ = gh_ - 1
            while k_ >= 0 and not filled_(k_):
                k_ -= 1
            gap_i2 = gh_ - k_ - 1
        eq("Dashboard spacing: exactly one blank row between the two tables of the open-incident slot (blank rows)", gap_i2, 1)
        eq("Dashboard spacing: exactly one blank row before and after every answer card, measured from the chart's real bottom row (row, blank before, blank after)", bad_seams[:5], [])
        bars_ = [c_["position"]["overlayPosition"]["anchorCell"]["rowIndex"] for c_ in sh_.get("charts", []) if c_["spec"].get("basicChart", {}).get("chartType") == "BAR"]
        eq("Dashboard spacing: the two bar charts (stuck, blocked) have exactly one blank row between chart and card (chart row, blank before, blank after)",
           ([(b_ + 1, seam_by_chart.get(b_)) for b_ in bars_ if seam_by_chart.get(b_, (0, 0))[0] != 1], len(bars_)), ([], 2))
        # a chart with a cell key: the key is in the row directly under the chart image (no blank row between)
        key_gap = []
        for n_, (cr_, hp_) in enumerate(charts_):
            b_ = bottom_row(cr_, hp_)
            nxt_ = charts_[n_ + 1][0] if n_ + 1 < len(charts_) else len(grid_)
            krow_ = next((i for i in range(cr_, min(nxt_, len(grid_))) if grid_[i] and "\u2501" in grid_[i][0]), None)
            if krow_ is not None and krow_ != b_ + 1:
                key_gap.append((cr_ + 1, krow_ + 1, b_ + 2))
        eq("Dashboard keys: the key sits in the row directly under its chart image (chart row, key row, expected row)", key_gap[:5], [])
        # the cell key under a 6/12 chart uses exactly the series colours of that chart
        kd_ = sheets("get", params={"spreadsheetId": sid, "ranges": ["Dashboard!A1:A320"], "includeGridData": True,
                                    "fields": "sheets(properties(title),charts(position,spec(basicChart(axis(position,title),series(colorStyle,targetAxis)))),data(rowData(values(textFormatRuns))))"})
        ks_ = next(x for x in kd_["sheets"] if x["properties"]["title"] == "Dashboard")
        rd_ = ks_["data"][0].get("rowData", [])
        col_of = lambda c: tuple(round(c.get(k, 0), 2) for k in ("red", "green", "blue"))
        key_bad = []
        for ch_ in ks_.get("charts", []):
            ser_ = ch_["spec"].get("basicChart", {}).get("series", [])
            if not ser_ or len(ser_) < 2 and False:
                continue
            anc_ = ch_["position"]["overlayPosition"]["anchorCell"]["rowIndex"]
            kr_ = bottom_row(anc_, ch_["position"]["overlayPosition"]["heightPixels"]) + 1          # the key row: right under the chart image's real bottom row
            runs_ = (rd_[kr_]["values"][0].get("textFormatRuns", []) if kr_ < len(rd_) and rd_[kr_].get("values") else [])
            keyc_ = {col_of(r_["format"]["foregroundColor"]) for r_ in runs_ if r_.get("format", {}).get("bold")}
            serc_ = {col_of(x_["colorStyle"]["rgbColor"]) for x_ in ser_ if x_.get("colorStyle", {}).get("rgbColor")}
            if keyc_ and keyc_ != serc_:
                key_bad.append((anc_ + 1, sorted(keyc_), sorted(serc_)))
            if not keyc_ and len(ser_) > 1 and any(x_.get("targetAxis") == "RIGHT_AXIS" for x_ in ser_):
                key_bad.append((anc_ + 1, "no key", ""))
        eq("Dashboard keys: every 6/12 chart has a key and its colours equal the chart's series colours (chart row, key colours, series colours)", key_bad[:3], [])
        axis_bad = [(ch_["position"]["overlayPosition"]["anchorCell"]["rowIndex"] + 1, next((a_.get("title") for a_ in ch_["spec"]["basicChart"].get("axis", []) if a_["position"] == "LEFT_AXIS"), None))
                    for ch_ in ks_.get("charts", [])
                    if any(x_.get("targetAxis") == "RIGHT_AXIS" for x_ in ch_["spec"].get("basicChart", {}).get("series", []))
                    and next((a_.get("title") for a_ in ch_["spec"]["basicChart"].get("axis", []) if a_["position"] == "LEFT_AXIS"), None) != "Left: per week. Right: per month."]
        eq("Dashboard: the left-axis title of every chart with a right-axis series reads 'Left: per week. Right: per month.' (A50, read back from the API)", axis_bad[:5], [])
        tt_ = sheets("get", params={"spreadsheetId": sid, "fields": "sheets(properties(title),charts(spec(title)))"})
        titles_ = [c_["spec"].get("title", "") for s_ in tt_["sheets"] if s_["properties"]["title"] == "Dashboard" for c_ in s_.get("charts", [])]
        unit_bad = [w_ for w_, t_ in (("%", next((x for x in titles_ if "Work Category" in x), "")), ("hours", next((x for x in titles_ if "reviewed quickly" in x), ""))) if w_ not in t_]
        eq("Dashboard chart titles carry their unit: the work-mix title has '%', the review title says hours (units missing)", unit_bad, [])
        cw_ = sheets("get", params={"spreadsheetId": sid, "ranges": ["Dashboard!A1:D1"], "includeGridData": True, "fields": "sheets(data(columnMetadata(pixelSize)))"})["sheets"][0]["data"][0]["columnMetadata"]
        w_ad = sum(c_.get("pixelSize", 100) for c_ in cw_[:4])
        chart_w = [(c_["position"]["overlayPosition"]["anchorCell"]["rowIndex"] + 1, c_["position"]["overlayPosition"]["widthPixels"], c_["position"]["overlayPosition"].get("offsetXPixels", 0), c_["position"]["overlayPosition"]["anchorCell"].get("columnIndex", 0))
                   for c_ in ks_.get("charts", [])]
        wrong_w = [x for x in chart_w if x[1] != w_ad or x[2] != 0 or x[3] != 0]
        eq("Dashboard: every chart is exactly as wide as the answer cards (columns A to D) and starts at column A (chart row, width, offset, column)", (wrong_w[:3], w_ad, len(chart_w)), ([], w_ad, 9))
        i2t_ = next((i for i in range(len(grid_)) if grid_[i] and grid_[i][0] == "Open incidents now, by priority"), 10 ** 6)
        card_cols = {(m_["startRowIndex"], m_["endColumnIndex"]) for m_ in sh_.get("merges", []) if m_["startColumnIndex"] == 0 and m_["endColumnIndex"] in (4, 6) and m_["endRowIndex"] - m_["startRowIndex"] >= 3}
        i2_card = min((r0 for r0, _ in card_cols if r0 > i2t_), default=None)
        wrong_cards = [(r0 + 1, c1) for r0, c1 in sorted(card_cols) if c1 != (6 if r0 == i2_card else 4)]
        eq("Dashboard: every chart answer card spans A to D (the chart's width); the open-incident card spans A to F (its tables' width) (card row, end column)", (wrong_cards[:3], i2_card is not None), ([], True))
        # the same number reads the same on every tab: Alerts block 7 against the Dashboard's blocked table, Teams I2 'All' against the Dashboard's open-incident table
        fv = lambda rng: values_get(sid, rng, "FORMATTED_VALUE")
        dsh = fv("Dashboard!A1:K260")
        al7 = fv(f"{_tabname(sid, 'Alerts')}!AK1:AN14")
        tms = fv("Teams!A1:G260")
        hdr_k1 = next((i for i, r_ in enumerate(dsh) if len(r_) > 6 and r_[4:7] == ["Group", "Blocked now", "Median days blocked"]), None)
        mism = []
        if hdr_k1 is not None:
            d_sbu = dsh[hdr_k1 + 1][5:7]
            a_sbu = next((r_[1:3] for r_ in al7 if r_ and r_[0] == "SBU"), None)
            if a_sbu is not None and [x for x in d_sbu] != [x for x in a_sbu]:
                mism.append(("blocked SBU row", d_sbu, a_sbu))
        t_i2 = next((i for i, r_ in enumerate(tms) if r_ and r_[:2] == ["Team", "Group"] and len(r_) > 2 and str(r_[2]).startswith("Customer: open now")), None)
        if t_i2 is not None:
            trow = next((r_ for r_ in tms[t_i2 + 1:t_i2 + 30] if r_ and str(r_[0]).startswith("All")), None)
            for sp_, (c_open, c_med) in (("Customer incidents", (2, 3)), ("Internal incidents", (4, 5))):
                drow = next((r_ for r_ in dsh if len(r_) > 3 and r_[0] == sp_ and r_[1] == "All"), None)
                if trow and drow and [trow[c_open], trow[c_med]] != [drow[2], drow[3]]:
                    mism.append((sp_, [trow[c_open], trow[c_med]], drow[2:4]))
        eq("the same number reads the same on every tab (Alerts block 7 vs Dashboard blocked table, Teams I2 'All' vs Dashboard open incidents)", mism[:3], [])
        eq("Dashboard has ten answer cards and ten scorecard rows", (len(cards_), len(DBd.SLOTS)), (10, 10))
        right = [(i + 1, c) for i in range(0, sc + 12) for c in range(7, 26) if g(dfm, i, c) != ""]          # v1.41: the scorecard now runs A to G (Limit column)
        eq("Dashboard: nothing right of column G in the scorecard rows (rows 1 to 15)", right, [])
    except Exception as e_:
        checks += 1
        res.append(("Dashboard checks could not run", str(e_)[:120], "", "DIFF"))
    # v1.28: an incident outside the roster (no roster Group and no roster Team) must not reach any tab
    try:
        ros_g = set(R.groups)
        ros_t = {x["team"] for x in R.rows if x.get("team") and x.get("group") in ros_g}
        iv_ = values_get(sid, "Incident_Issues!A1:Z8000", "UNFORMATTED_VALUE")
        ih_ = iv_[0]
        gi, ti = ih_.index("group"), ih_.index("team")
        body_ = [r_ for r_ in iv_[1:] if r_ and r_[0] != ""]
        if cfg.get("ladder"):          # v1.34: an incident is ours by the ladder (Team, Group or SBU); only a row the ladder does not attribute may not reach the tab
            li = ih_.index("level") if "level" in ih_ else None
            oc = ih_.index("ours_c") if "ours_c" in ih_ else None
            outside = incident_outside(body_, li, oc)
        else:
            outside = [r_ for r_ in body_ if (r_[gi] if gi < len(r_) else "") not in ros_g and (r_[ti] if ti < len(r_) else "") not in ros_t]
        checks += 1
        res.append(("incident rows the attribution does not place (no Team, Group or SBU level) on the Incident_Issues tab", len(outside), 0, "OK" if not outside else "DIFF"))
        checks += 1
        res.append(("incident rows on the tab equal the derived rows", len(body_), len(T["Incident_Issues"]), "OK" if len(body_) == len(T["Incident_Issues"]) else "DIFF"))
        ki_ = ih_.index("key") if "key" in ih_ else None          # v1.43f (AC65): every incident row carries its real Jira key
        nokey = [r_ for r_ in body_ if ki_ is None or ki_ >= len(r_) or not str(r_[ki_]).strip()]
        checks += 1
        res.append(("incident rows with no Jira key on the Incident_Issues tab (v1.43f)", len(nokey), 0, "OK" if not nokey else "DIFF"))
        # and no Unspecified bucket anywhere on the Dashboard
        dtxt = values_get(sid, "Dashboard!A1:Z300", "FORMATTED_VALUE")
        unspec = [(i + 1, c) for i, row in enumerate(dtxt) for c, x in enumerate(row) if "Unspecified" in str(x)]
        checks += 1
        res.append(("no 'Unspecified' on the Dashboard", unspec[:3], [], "OK" if not unspec else "DIFF"))
    except Exception as e_:
        checks += 1
        res.append(("incident scope checks could not run", str(e_)[:120], "", "DIFF"))
    # v1.28/inbox 90: slot codes are not shown to readers; the incident tables beside the charts read the label on their own row and add up; I2 by Group and Team adds up
    try:
        import re as _re
        import panels as _PN
        pat = _re.compile(r"\b(?:" + _PN._CODE + "|" + _PN._REF + r")\b")
        for tab_ in ("About", "Definitions", "Alerts", "Dashboard", "Sources", "Log", "Thresholds"):
            real_ = {"About": "README", "Definitions": "Data_Dictionary", "Alerts": "Alert details", "Sources": "Coverage", "Log": "Run_Log"}.get(tab_, tab_)
            vv = values_get(sid, f"'{real_}'", "FORMATTED_VALUE")
            hits = [(i + 1, str(x)[:50]) for i, r_ in enumerate(vv) for x in r_ if isinstance(x, str) and pat.search(x) and not x.startswith("=")]
            checks += 1
            res.append((f"no slot codes on the {tab_} tab", hits[:3], [], "OK" if not hits else "DIFF"))
        # inbox 97: no old tab names and no version tags anywhere a reader looks (cell values and the notes in the first rows, every visible tab)
        old_names = _re.compile(r"README|Coverage|Data_Dictionary|Run_Log|Alert details")
        ver_tag = _re.compile(r"\bv1\.\d{1,2}\b")
        from sheetlib import sheets as _sh
        bad_names, bad_vers, bad_links, links_seen, bad_users = [], [], [], {}, []
        cells_, hdr_vals, na_bad, float_bad, wrap_bad = {}, {}, [], [], []
        import datetime as _dt, derive as _D
        _R = _D.Roster(json.load(open("data/config.json")))
        usernames_ = {u for u in list(_R.by_gl) + list(_R.by_gh) if len(u) >= 5}
        tok_ = _re.compile(r"[A-Za-z0-9._-]+")
        sheet_ids_ = {x_["properties"]["sheetId"] for x_ in _sh("get", params={"spreadsheetId": sid, "fields": "sheets(properties(sheetId))"})["sheets"]}
        for tab_ in ("Dashboard", "Alerts", "Teams", "Individual", "Insights", "About", "Sources", "Definitions", "Thresholds", "Log"):
            gd_ = _sh("get", params={"spreadsheetId": sid, "ranges": [f"'{_tabname(sid, tab_)}'!A1:AD1300"], "includeGridData": True, "fields": "sheets(data(rowData(values(formattedValue,note,hyperlink,userEnteredValue,userEnteredFormat(horizontalAlignment,wrapStrategy)))))"})
            for i_, r_ in enumerate(gd_["sheets"][0]["data"][0].get("rowData", [])):
                hdr_vals.setdefault(tab_, {})[i_] = [(x_.get("formattedValue", "") or "") for x_ in r_.get("values", [])] if (i_ in (0, 2, 3, 4) or (r_.get("values") and r_["values"][0].get("formattedValue") in ("Team", "Group"))) else None
                for j_, v_ in enumerate(r_.get("values", [])):
                    ft_ = v_.get("formattedValue", "") or ""
                    if _re.fullmatch(r"-?\d+\.\d{3,}%?", ft_):
                        float_bad.append((tab_, i_ + 1, j_ + 1, ft_))
                    if ft_ and ((tab_ == "Alerts" and i_ == 2) or (tab_ in ("Individual", "Log", "Sources", "Definitions") and i_ == 0)) and v_.get("userEnteredFormat", {}).get("wrapStrategy") != "WRAP":
                        wrap_bad.append((tab_, i_ + 1, j_ + 1, ft_[:20]))
                    if tab_ in ("Dashboard", "Teams", "Alerts") and v_.get("formattedValue") == "n/a" and v_.get("userEnteredFormat", {}).get("horizontalAlignment") not in ("RIGHT", "CENTER"):
                        na_bad.append((tab_, i_ + 1, j_ + 1))
                    fv_ = v_.get("userEnteredValue", {}).get("formulaValue", "")
                    if fv_.startswith("=HYPERLINK(") and tab_ in ("Dashboard", "Teams", "Alerts"):
                        cells_.setdefault(tab_, {})[(i_, j_)] = (v_.get("formattedValue", ""), v_.get("note", ""), v_.get("hyperlink", ""))
                    if fv_.startswith("=HYPERLINK("):
                        links_seen[tab_] = links_seen.get(tab_, 0) + (1 if v_.get("hyperlink") else 0)
                        hl_ = v_.get("hyperlink", "")
                        if not hl_:
                            bad_links.append((tab_, i_ + 1, j_ + 1, "no resolved hyperlink"))
                        elif hl_.startswith("#gid="):
                            gid_, _, rg_ = hl_[5:].partition("&range=")
                            if "&fvid=" in gid_:
                                gid_, _, fv_id = gid_.partition("&fvid=")
                                if not gid_.isdigit() or int(gid_) not in sheet_ids_ or not fv_id.isdigit():
                                    bad_links.append((tab_, i_ + 1, j_ + 1, hl_[:40]))
                            elif not gid_.isdigit() or int(gid_) not in sheet_ids_ or not _re.fullmatch(r"[A-Z]{1,2}\d{1,5}", rg_ or "A1"):
                                bad_links.append((tab_, i_ + 1, j_ + 1, hl_[:40]))
                        else:
                            from urllib.parse import urlparse as _up
                            u_ = _up(hl_)
                            if u_.scheme != "https" or not u_.netloc or (u_.netloc.startswith(json.load(open("data/config.json"))["jira"]["host"].split(".")[0]) and "jql=" not in u_.query):
                                bad_links.append((tab_, i_ + 1, j_ + 1, hl_[:40]))
                    for txt_ in (v_.get("formattedValue", ""), v_.get("note", "")):
                        if tab_ not in ("Individual", "Identity") and txt_ and any(t_.lower() in usernames_ for t_ in tok_.findall(txt_)):
                            bad_users.append((tab_, i_ + 1, j_ + 1, txt_[:40]))
                        if txt_ and old_names.search(txt_):
                            bad_names.append((tab_, i_ + 1, j_ + 1, txt_[:40]))
                        if txt_ and ver_tag.search(txt_):
                            bad_vers.append((tab_, i_ + 1, j_ + 1, txt_[:40]))
        import teams_build as _TB
        exp_teams = sum(1 for r_ in _TB.build_rows([(g_, t_, False) for g_, t_ in _TB.roster_teams(json.load(open("data/config.json")))] + [(g_, t_, True) for g_, t_ in _TB.former_teams(json.load(open("data/config.json")))])[0] for x_ in r_ if isinstance(x_, str) and x_.startswith("=HYPERLINK("))
        import links_jql_old as _LK
        import urllib.parse as _up2
        isnum_ = lambda x: x == "n/a" or bool(_re.fullmatch(r"-?[0-9.,]+%?", x or ""))
        no_note, short_note = [], []
        for tab_, cs_ in cells_.items():
            for (i_, j_), (fv_, nt_, hl_) in cs_.items():
                if isnum_(fv_) and (hl_.startswith("https://") or "&range=A1" in hl_):
                    if not nt_:
                        no_note.append((tab_, i_ + 1, j_ + 1))
                    elif len(nt_) < 40:
                        short_note.append((tab_, i_ + 1, j_ + 1, nt_))
        # link row = value row: the search behind a number names the Group or Team of its OWN row
        misrow = []
        gid_of = lambda name: _LK.T2ID.get(name)
        trows = values_get(sid, "Teams!A1:A300", "FORMATTED_VALUE")
        for (i_, j_), (fv_, nt_, hl_) in cells_.get("Teams", {}).items():
            lab_ = trows[i_][0] if i_ < len(trows) and trows[i_] else ""
            q_ = _up2.unquote(hl_.split("jql=", 1)[1]) if "jql=" in hl_ else ""
            if lab_ in _LK.T2ID and q_ and _LK.T2ID[lab_] not in q_:
                misrow.append(("Teams", i_ + 1, lab_))
            if lab_ in ("All (Dashboard total)",) and q_ and _TF + " = " in q_:
                misrow.append(("Teams", i_ + 1, lab_))
        drows = values_get(sid, "Dashboard!E1:E300", "FORMATTED_VALUE")
        for (i_, j_), (fv_, nt_, hl_) in cells_.get("Dashboard", {}).items():
            lab_ = drows[i_][0] if i_ < len(drows) and drows[i_] else ""
            q_ = _up2.unquote(hl_.split("jql=", 1)[1]) if "jql=" in hl_ else ""
            if j_ >= 5 and lab_ in _LK.GROUP_IDS and q_ and "filter" in q_ and not all(i2 in q_ for i2 in _LK.GROUP_IDS[lab_][:1]):
                misrow.append(("Dashboard", i_ + 1, lab_))
        arows = values_get(sid, f"{_tabname(sid, 'Alerts')}!AK1:AK40", "FORMATTED_VALUE")
        for (i_, j_), (fv_, nt_, hl_) in cells_.get("Alerts", {}).items():
            if j_ in (37, 38, 39) and i_ >= 3:
                lab_ = arows[i_][0] if i_ < len(arows) and arows[i_] else ""
                q_ = _up2.unquote(hl_.split("jql=", 1)[1]) if "jql=" in hl_ else ""
                if lab_ in _LK.GROUP_IDS and _LK.GROUP_IDS[lab_][0] not in q_:
                    misrow.append(("Alerts block 7", i_ + 1, lab_))
                if lab_ == "SBU" and _TF in q_:
                    misrow.append(("Alerts block 7", i_ + 1, lab_))
        snake_ = _re.compile(r"[A-Za-z0-9]_[A-Za-z0-9]")
        hdr_bad = []
        for tab_, rows_h in hdr_vals.items():
            for i_, hv_ in rows_h.items():
                if hv_ and tab_ in ("Dashboard", "Teams", "Alerts", "Individual", "Definitions", "Sources", "Log", "Thresholds", "About", "Insights"):
                    is_hdr = (tab_ == "Alerts" and i_ == 2) or (tab_ in ("Individual", "Definitions", "Sources", "Log", "Thresholds") and i_ == 0) or (tab_ == "Teams" and hv_ and hv_[0] == "Team") or (tab_ == "Dashboard" and hv_ and hv_[0] in ("Group", "Question"))
                    if is_hdr:
                        hdr_bad += [(tab_, i_ + 1, x_) for x_ in hv_ if snake_.search(x_)]
        checks += 4
        res.append(("no number with more than 2 decimals shows in any visible cell (tab, row, column, value)", float_bad[:5], [], "OK" if not float_bad else "DIFF"))
        res.append(("every header row (Alerts, Individual, Log, Sources, Definitions) wraps its text (tab, row, column)", wrap_bad[:5], [], "OK" if not wrap_bad else "DIFF"))
        res.append(("no underscore or snake_case word in any visible header row (Alerts, Individual, Definitions, Sources, Log, Thresholds, Teams, Dashboard tables)", hdr_bad[:5], [], "OK" if not hdr_bad else "DIFF"))
        res.append(("every 'n/a' cell on the Dashboard, Teams and Alerts is right-aligned like the numbers (or centred in the centred tables)", na_bad[:5], [], "OK" if not na_bad else "DIFF"))
        checks += 3
        res.append(("every linked number has a note of at least 40 characters (tab, row, column)", (no_note[:3], short_note[:3]), ([], []), "OK" if not no_note and not short_note else "DIFF"))
        res.append(("link row = value row: the search behind a number names the Group or Team of its own row (Teams, Dashboard tables, Alerts block 7)", misrow[:5], [], "OK" if not misrow else "DIFF"))
        res.append(("Alerts block 7 has exactly one header row and an SBU row", [(arows[3][0] if len(arows) > 3 and arows[3] else "") == "Group" and len(arows) > 4 and arows[4][0] == "Group", any(r_ and r_[0] == "SBU" for r_ in arows[4:14])], [False, True], "OK" if not ((arows[3][0] if len(arows) > 3 and arows[3] else "") == "Group" and len(arows) > 4 and arows[4][0] == "Group") and any(r_ and r_[0] == "SBU" for r_ in arows[4:14]) else "DIFF"))
        checks += 6
        res.append(("no roster username in the text or notes of any visible tab except Individual (links may hold them)", bad_users[:3], [], "OK" if not bad_users else "DIFF"))
        res.append(("every HYPERLINK cell on every visible tab has a resolved link (tab, row, column, reason)", bad_links[:5], [], "OK" if not bad_links else "DIFF"))
        res.append(("the Teams tab holds exactly the links the build intends (resolved links, intended)", links_seen.get("Teams", 0), exp_teams, "OK" if links_seen.get("Teams", 0) == exp_teams else "DIFF"))
        res.append(("the Dashboard holds at least 250 link cells in its tables, scorecard and Teams links", links_seen.get("Dashboard", 0) >= 250, True, "OK" if links_seen.get("Dashboard", 0) >= 250 else "DIFF"))
        if os.path.exists("data/items_layout.json"):
            import items_check as _VC
            _exp = {"W_other": sum(1 for x_ in T["Other_Items"] if x_["kind"] == "other"), "W_untagged": sum(1 for x_ in T["Other_Items"] if x_["kind"] == "untagged"),
                    "C_other": sum(1 for c_ in T["Code_Changes"] if c_.get("comp_kind") == "other"), "C_untagged": sum(1 for c_ in T["Code_Changes"] if c_.get("comp_kind") == "untagged")}
            _vr, _vn = _VC.run(sid, cfg, cells_, _exp)
            res += _vr; checks += _vn
        res.append(("no old tab names (README, Coverage, Data_Dictionary, Run_Log, Alert details) in values or notes on any visible tab", bad_names[:3], [], "OK" if not bad_names else "DIFF"))
        res.append(("no version tags (v1.xx) in values or notes on any visible tab", bad_vers[:3], [], "OK" if not bad_vers else "DIFF"))
        dv = values_get(sid, "Dashboard!A1:G320", "FORMATTED_VALUE")
        def block(title_prefix):
            out_ = []
            for i, r_ in enumerate(dv):
                if len(r_) > 4 and r_[4] == "Detail by Group and Team" and (title_prefix is None or True):
                    out_.append(i)
            return out_
        starts_ = block(None)
        itab = {}
        for rr in T["Incident_Issues"]:
            pass
        wk = values_get(sid, "Metrics!A1:D40", "UNFORMATTED_VALUE")
        nrp = nr["m_612_periods"]
        mp = values_get(sid, f"Metrics!A{nrp['startRowIndex'] + 2}:D{nrp['endRowIndex']}", "UNFORMATTED_VALUE")
        from tabs import serial as _ser
        w_st, w_en, m_st, m_en = mp[5][2], mp[5][3], mp[17][2], mp[17][3]
        def cnt(sp, key, val, st, en, field):
            n = 0
            for rr in T["Incident_Issues"]:
                if rr["split"] != sp: continue
                if key and rr[key] != val: continue
                d_ = rr[field]
                if d_ is not None and st <= _ser(d_) < en:
                    n += 1
            return n
        for si, (sp, st0) in enumerate(zip(("customer", "internal"), starts_[:2])):
            rows_ = dv[st0 + 2: st0 + 2 + 40]
            tot = None
            sums = [0, 0, 0, 0]
            for r_ in rows_:
                if not r_ or len(r_) < 7 or r_[4] == "Team":
                    if r_ and len(r_) > 4 and r_[4] == "Team":
                        break
                    continue
                lab = r_[4]
                try:
                    a_w, b_w = [int(x) for x in str(r_[5]).split(" / ")]
                    a_m, b_m = [int(x) for x in str(r_[6]).split(" / ")]
                except Exception:
                    continue
                if lab.startswith("All"):
                    tot = (a_w, b_w, a_m, b_m)
                else:
                    sums = [sums[0] + a_w, sums[1] + b_w, sums[2] + a_m, sums[3] + b_m]
                    key = "group"
                    checks += 1
                    want = (cnt(sp, key, lab, w_st, w_en, "final_done"), cnt(sp, key, lab, w_st, w_en, "created"), cnt(sp, key, lab, m_st, m_en, "final_done"), cnt(sp, key, lab, m_st, m_en, "created"))
                    res.append((f"incident table {sp}: row '{lab}' equals a recompute by its own label", (a_w, b_w, a_m, b_m), want, "OK" if (a_w, b_w, a_m, b_m) == want else "DIFF"))
            checks += 1
            res.append((f"incident table {sp}: Group rows (with Other Group) add up to the total", tuple(sums), tot, "OK" if tot is not None and tuple(sums) == tot else "DIFF"))
        # Teams tab (v1.29): the Team rows plus 'Tied by Group only' add up to the 'All' row of every block; the rows of the count blocks equal a recompute by Team
        tv = values_get(sid, "Teams!A1:J1400", "UNFORMATTED_VALUE")
        blk = [i for i, r_ in enumerate(tv) if r_ and r_[0] and i + 1 < len(tv) and tv[i + 1] and tv[i + 1][0] == "Team"]
        for bi in blk:
            hdr_ = tv[bi + 1]
            rows_ = []
            j = bi + 2
            while j < len(tv) and tv[j] and tv[j][0] != "":
                rows_.append(tv[j]); j += 1
            SPECIAL = ("Group only", "SBU only", "Not in an Automation Group", "All")
            teamrows = [r_ for r_ in rows_ if not str(r_[0]).startswith(SPECIAL)]
            rem = None
            specials = [r_ for r_ in rows_ if str(r_[0]).startswith(SPECIAL[:3])]
            tot = next((r_ for r_ in rows_ if str(r_[0]).startswith("All")), None)
            if hdr_[2:4] in (["Stuck now", "Oldest (days)"], ["Blocked now", "Median days blocked"]):
                zt = [r_[0] for r_ in rows_ if len(r_) > 3 and r_[2] == 0 and r_[3] == 0]
                checks += 1
                res.append((f"Teams block '{str(tv[bi][0])[:40]}': no 0 Oldest or median where the count is 0 (n/a instead)", zt[:3], [], "OK" if not zt else "DIFF"))
            if hdr_[2:4] == ["Last week: median hours", "Last month: median hours"]:
                zt = [r_[0] for r_ in rows_ if len(r_) > 3 and (r_[2] == 0 or r_[3] == 0)]
                checks += 1
                res.append((f"Teams block '{str(tv[bi][0])[:40]}': no 0 median hours (n/a instead)", zt[:3], [], "OK" if not zt else "DIFF"))
            blanks = [(r_[0], hdr_[c_]) for r_ in rows_ for c_ in range(2, len(hdr_)) if c_ >= len(r_) or r_[c_] == ""]
            checks += 1
            res.append((f"Teams block '{str(tv[bi][0])[:40]}': no blank number cell (0 or n/a instead)", blanks[:3], [], "OK" if not blanks else "DIFF"))
            for c_ in range(2, len(hdr_)):
                if tot is not None and len(tot) > c_ and isinstance(tot[c_], (int, float)) and hdr_[c_] and "median" not in str(hdr_[c_]).lower() and "Oldest" not in str(hdr_[c_]) and "hours" not in str(hdr_[c_]):
                    got = sum((r_[c_] if len(r_) > c_ and isinstance(r_[c_], (int, float)) else 0) for r_ in teamrows + specials)
                    checks += 1
                    res.append((f"Teams block '{str(tv[bi][0])[:40]}' column '{hdr_[c_]}': Team rows, former Teams, Group only, SBU only and the rest add up to All", got, tot[c_], "OK" if abs(got - tot[c_]) < 1e-9 else "DIFF"))
            # the 'Not in an Automation Group' row is 0 on the Jira blocks (every ticket in a population is ours); code and incident blocks may hold unmapped authors
            nia = next((r_ for r_ in specials if str(r_[0]).startswith("Not in")), None)
            if nia is not None and str(tv[bi][0]).startswith(("Are we finishing", "Is anything stuck", "Is work blocked", "Are we fixing bugs", "How much of our finished")):
                nz = [x for x in nia[2:] if isinstance(x, (int, float)) and x != 0]
                checks += 1
                res.append((f"Teams block '{str(tv[bi][0])[:40]}': the 'Not in an Automation Group' row is 0 on a Jira block", nz[:3], [], "OK" if not nz else "DIFF"))
        # recompute by Team for the finished/created/merged/bug/incident count columns
        from tabs import serial as _ser2
        def inwin(d_, st, en):
            return d_ is not None and st <= _ser2(d_) < en
        wkw, wkm = (w_st, w_en), (m_st, m_en)
        ji = T["Jira_Issues"]; cc = T["Code_Changes"]; ii = T["Incident_Issues"]
        def tblock(title_start):
            for bi in blk:
                if str(tv[bi][0]).startswith(title_start):
                    out_ = []
                    j = bi + 2
                    while j < len(tv) and tv[j] and tv[j][0] != "":
                        out_.append(tv[j]); j += 1
                    return out_
            return []
        def chk(label, got, want):
            nonlocal checks
            checks += 1
            res.append((label, got, want, "OK" if got == want else "DIFF"))
        for r_ in tblock("Are we finishing as much as we start"):
            if str(r_[0]).startswith(("Group only", "SBU only", "Not in an Automation Group", "All")): continue
            t_ = r_[0]
            want = [sum(1 for x in ji if x["team"] == t_ and x["series"] == "main" and inwin(x["final_done"], *wkw)),
                    sum(1 for x in ji if x.get("team_c", x["team"]) == t_ and x["is_work_item"] == 1 and inwin(x["created"], *wkw)),
                    sum(1 for x in ji if x["team"] == t_ and x["series"] == "main" and inwin(x["final_done"], *wkm)),
                    sum(1 for x in ji if x.get("team_c", x["team"]) == t_ and x["is_work_item"] == 1 and inwin(x["created"], *wkm))]
            chk(f"Teams finished/added '{t_}' equals a recompute", [r_[2], r_[3], r_[4], r_[5]], want)
        for r_ in tblock("Are we shipping code"):
            if str(r_[0]).startswith(("Group only", "SBU only", "Not in an Automation Group", "All")): continue
            t_ = r_[0]
            want = [sum(1 for x in cc if x["team"] == t_ and x["counted"] == 1 and x["state"] == "merged" and x["class"] == "normal" and inwin(x["merged_at"], *w_)) for w_ in (wkw, wkm)]
            chk(f"Teams merged '{t_}' equals a recompute", [r_[2], r_[3]], want)
        for key_, sp_ in (("Are we keeping up with customer incidents", "customer"), ("Are we keeping up with internal incidents", "internal")):
            for r_ in tblock(key_):
                if str(r_[0]).startswith(("Group only", "SBU only", "Not in an Automation Group", "All")): continue
                t_ = r_[0]
                want = [sum(1 for x in ii if x["split"] == sp_ and (x["team"] if f_ == "final_done" else x["team_c"]) == t_ and inwin(x[f_], *w_)) for w_ in (wkw, wkm) for f_ in ("final_done", "created")]          # A67(b): created reads the Team at creation
                chk(f"Teams {sp_} incidents '{t_}' equals a recompute", [r_[2], r_[3], r_[4], r_[5]], want)
    except Exception as e_:
        import traceback; traceback.print_exc()
        checks += 1
        res.append(("slot-code, incident-table and Teams checks could not run", str(e_)[:160], "", "DIFF"))
    bad = [r for r in res if r[3] != "OK"]
    out = {"checks": checks, "differences": len(bad), "detail": res}
    text = json.dumps(out, indent=1, default=str)
    if a.out:
        open(a.out, "w").write(text)
    print(f"selfcheck: {checks} checks, {len(bad)} differences")
    for r in bad[:20]:
        print(r)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
