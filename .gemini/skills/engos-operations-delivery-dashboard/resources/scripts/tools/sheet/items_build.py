#!/usr/bin/env python3
"""v1.35 stage (ii): the two derived, VISIBLE item tabs 'Work items' and 'Code changes' (A52, A53, AC70).
Every column is one spilled formula over the stored source tabs (named ranges ji_*, ii_*, cc_*), at fixed anchors (row 1 headers, row 2 formulas), with reserved capacity
(data/items_layout.json). No titles, no free text, no names: a ticket key or a change number and a link only. A repo in a personal namespace shows 'personal project'; the real URL sits only in the link (A61).
The flag columns repeat each Dashboard and Teams count rule exactly, so the filter in a cell note (flag = 1, Group or Team) leaves as many rows as the cell says (items_check.py).
Usage: items_build.py --target <spreadsheet id> --config <cfg> [--check] [--build]"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from sheetlib import sheets, batch, values_update, values_get, col_letter

import itemfilters as IF
HEAD_WI, HEAD_CC = IF.WI_IDS, IF.CC_IDS          # column ids (formulas); the header row shows IF.WI_DISP / IF.CC_DISP
WK = ('INDEX(INDEX(m_612_periods,0,3),7)', 'INDEX(INDEX(m_612_periods,0,4),7)')
MO = ('INDEX(INDEX(m_612_periods,0,3),19)', 'INDEX(INDEX(m_612_periods,0,4),19)')
YR = ('INDEX(INDEX(m_612_periods,0,3),8)', 'INDEX(INDEX(m_612_periods,0,4),19)')          # G2 (D408): the 12 complete months of the work-mix table (rows 8 to 19 of the 6/12 periods), the same window as d_workmix612
CAPACITY_FACTOR = 1.5
BUDGET = 9_500_000
LAY = os.environ.get("ITEMS_LAYOUT", "data/items_layout.json")          # the env override is for the offline capacity test only


def win(x, p):
    return f"ISNUMBER({x})*({x}>={p[0]})*({x}<{p[1]})"


def wi_formulas(cfg):
    host = cfg["jira"]["host"]
    J = lambda e: f'FILTER({e},ji_key<>"")'          # v1.43c AC74: epics and initiatives are rows too (Kind = Epic or Initiative); the Kind column 'kind' stays work only for tickets
    I = lambda e: f'FILTER({e},ii_split<>"")'
    zj = 'ARRAYFORMULA(IF(ji_key<>"",0,0))'
    zi = 'ARRAYFORMULA(IF(ii_split<>"",0,0))'
    bj = 'ARRAYFORMULA(IF(ji_key<>"","",""))'
    bi = 'ARRAYFORMULA(IF(ii_split<>"","",""))'
    O = lambda e: f'FILTER({e},oi_kind<>"")'
    zo = 'ARRAYFORMULA(IF(oi_kind<>"",0,0))'
    bo = 'ARRAYFORMULA(IF(oi_kind<>"","",""))'
    def V(a, b, o=None):
        return "=VSTACK(" + J(a) + "," + I(b) + "," + O(o if o is not None else bo) + ")"
    f = {}
    f["key"] = "=LET(k," + V("ji_key", "ii_key", "oi_key")[1:] + f',ARRAYFORMULA(IF(k="","",HYPERLINK("https://{host}/browse/"&k,k))))'          # v1.41 3a: the key is the link (the far-right Link column is dropped); v1.43f AC65: incident and other-item rows carry their real Jira key (ii_key, oi_key)
    f["kind"] = V('ARRAYFORMULA(IF(ji_key<>"",IF(ji_is_work_item=1,"work","container"),""))', "ii_split", "oi_kind")
    f["item_kind"] = V('ARRAYFORMULA(IF(ji_key<>"",IF(ji_is_work_item=1,"Ticket",IF(ji_type="Epic","Epic","Initiative")),""))', 'ARRAYFORMULA(IF(ii_split<>"","Ticket",""))', 'ARRAYFORMULA(IF(oi_kind<>"","Ticket",""))')          # v1.43c AC74: Ticket, Epic or Initiative
    f["type"] = V("ji_type", "ii_type", "oi_type")
    f["priority"] = V("ji_priority", "ii_priority")
    f["level"] = V("ji_level", "ii_level")
    f["group"] = V("ji_group", "ii_group")
    f["team"] = V("ji_team", "ii_team")
    f["sbu"] = V("ji_sbu", bi, "oi_owning")
    f["group_at_creation"] = V("ji_group_c", "ii_group_c")
    f["team_at_creation"] = V("ji_team_c", "ii_team_c")
    f["status"] = V("ji_status_category", 'ARRAYFORMULA(IF(ii_open_at_asof=1,"open","done"))', "oi_status_category")
    f["created"] = V("ji_created", "ii_created", "oi_created")
    f["finished"] = V("ji_final_done", "ii_final_done", "oi_final_done")
    f["tag_conflict"] = V("ji_tag_conflict", zi, zo)
    for nm, p in (("wk", WK), ("mo", MO)):
        f["fin_" + nm] = V(f'(ji_series="main")*{win("ji_final_done", p)}', win("ii_final_done", p), zo)
        f["add_" + nm] = V(f'(ji_is_work_item=1)*(ji_ours_c=1)*{win("ji_created", p)}', f"(ii_ours_c=1)*{win('ii_created', p)}", zo)
    f["stuck"] = V("(ji_wip=1)*ISNUMBER(ji_start_age_days)*(ji_start_age_days>t_stuck_days)", zi, zo)          # v1.41 3b: stuck = in progress longer than the Thresholds cell t_stuck_days (no second typed number)
    f["blocked"] = V("1*(ji_blocked=1)", zi, zo)
    f["open"] = V(zj, "1*(ii_open_at_asof=1)", zo)
    f["blocked_long"] = V("(ji_blocked=1)*ISNUMBER(ji_blocked_age_days)*(ji_blocked_age_days>t_blocked_days)", zi, zo)          # v1.41 3c: blocked longer than t_blocked_days (the scorecard tests this number)
    f["over_limit"] = V(zj, 'ISNUMBER(ii_age_days)*(ii_open_at_asof=1)*(ii_age_days>t_incident_open_days)', zo)
    f["stalled"] = V('(ji_type="Epic")*ISNUMBER(ji_stalled_days)*(ji_stalled_days>t_epic_stalled_days)+(ji_type="Initiative")*ISNUMBER(ji_stalled_days)*(ji_stalled_days>t_init_stalled_days)', zi, zo)          # v1.43c AC75: open epic or initiative with no update under it within its limit
    f["all_done"] = V("1*(ji_kids_done=1)", zi, zo)          # v1.43c AC75: open epic or initiative whose child tickets are all done
    f["fin_yr"] = V(f'(ji_series="main")*{win("ji_final_done", YR)}', zi, zo)          # G2 (D408): finished in the 12 complete months, main series: the numerator list behind every work-mix number
    f["work_category"] = V("ji_work_category", bi, bo)          # v1.43 B4(2): the epic's Work Category at the ticket's finish date (now if open), set by derive from the side files; incidents and other items stay blank
    return f


def cc_formulas(cfg, gid_cc=0):
    ns = cfg.get("items", {}).get("code_namespaces", ["appian", "docs"])
    nsre = "^(" + "|".join(ns) + ")/"
    F = lambda e: f'=FILTER({e},cc_change_id<>"")'
    f = {}
    gl = cfg["gitlab"]["host"]
    G = lambda e: f'FILTER({e},cc_change_id<>"")'
    # v1.41 3a: the number is the link, in column A; the target is built from the SAME row's host, repo and number (array arithmetic, no INDEX by row: the old fault pointed every link at one repo);
    # a personal-namespace change (AC65) links to the tab top so no personal path is exposed
    f["number"] = (f'=LET(h,{G("cc_platform")},p,{G("cc_project")},n,{G("cc_number")},ARRAYFORMULA(IF(n="","",HYPERLINK(IF(REGEXMATCH(p,"{nsre}"),'
                   f'IF(h="gitlab","https://{gl}/"&p&"/-/merge_requests/","https://github.com/"&p&"/pull/")&n,"#gid={gid_cc}&range=A1"),n))))')
    f["host"] = F("cc_platform")
    f["repo"] = F(f'ARRAYFORMULA(IF(REGEXMATCH(cc_project,"{nsre}"),cc_project,"personal project"))')
    f["group"] = F("cc_group")
    f["team"] = F("cc_team")
    f["level"] = F("cc_level")
    f["class"] = F("cc_class")
    f["state"] = F("cc_state")
    f["counted"] = F("cc_counted")
    f["merged"] = F("cc_merged_at")
    f["kind"] = F("cc_comp_kind")
    f["key_state"] = F("cc_key_state")
    for nm, p in (("wk", WK), ("mo", MO)):
        f["merged_" + nm] = F(f'(cc_counted=1)*(cc_state="merged")*(cc_class="normal")*{win("cc_merged_at", p)}')
    return f


def used_rows(sid):
    from sheetlib import values_get as vg
    k = vg(sid, "Jira_Issues!A2:A40000")
    wi = sum(1 for r in k if r and r[0])
    isw = vg(sid, "Jira_Issues!C2:C40000")
    wi = sum(1 for r in k if r and r[0])          # v1.43c: epics and initiatives are rows on Work items too
    inc = sum(1 for r in vg(sid, "Incident_Issues!A2:A2000") if r and r[0])
    cc = sum(1 for r in vg(sid, "Code_Changes!A2:A40000") if r and r[0])
    oth = sum(1 for r in vg(sid, "Other_Items!A2:A400") if r and r[0])
    return wi + inc + oth, cc


def cells_total(sid):
    m = sheets("get", params={"spreadsheetId": sid, "fields": "sheets(properties(title,gridProperties(rowCount,columnCount)))"})
    return sum(s["properties"]["gridProperties"]["rowCount"] * s["properties"]["gridProperties"]["columnCount"] for s in m["sheets"] if "gridProperties" in s["properties"])


def capacity_status(wi, cc, lay):
    """AC70 for the item tabs (no Sheet call). wi = work items + incidents the source tabs would fill, cc = code changes. -> (level, [messages]); level 'refuse' when a tab's spill would exceed its grid
    (the FILTER spill would fail), 'warn' at 80 percent of the grid, else 'ok'."""
    msgs, level = [], "ok"
    for name, used, cap in (("Work items", wi, lay["wi_rows"]), ("Code changes", cc, lay["cc_rows"])):
        if used > cap:
            level = "refuse"; msgs.append(f"{name}: {used:,} rows would exceed the grid of {cap:,} rows: run the layout build (no write was made)")
        elif used > 0.8 * cap and level != "refuse":
            level = "warn"; msgs.append(f"{name}: {used:,} rows is {100 * used / cap:.0f}% of the grid of {cap:,} rows (warning at 80%)")
    return level, msgs


def relayout_budget(base_cells, wi, cc, factor=CAPACITY_FACTOR):
    """cell total if the item tabs were re-laid-out at 'factor' for wi and cc rows; base_cells = the Sheet without the two item tabs"""
    wic, ccc = int(wi * factor / 100 + 1) * 100, int(cc * factor / 100 + 1) * 100
    return base_cells + (wic + 1) * len(HEAD_WI) + (ccc + 1) * len(HEAD_CC), wic, ccc


def edit_check(sid, cell="Insights!Z1"):
    """edit-acceptance check (A66): after the item tabs exist the Sheet must still accept a value write, a formatting write and a clear. Stops the build at the first refusal and prints the total cells."""
    try:
        values_update(sid, cell, [["probe"]], "RAW")
        sheets("values", "clear", params={"spreadsheetId": sid, "range": cell}, body={})
        m = sheets("get", params={"spreadsheetId": sid, "fields": "sheets(properties(sheetId,title))"})
        sid0 = next(s["properties"]["sheetId"] for s in m["sheets"] if s["properties"]["title"] == "Insights")
        batch(sid, [{"updateCells": {"range": {"sheetId": sid0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 25, "endColumnIndex": 26}, "fields": "userEnteredValue"}}])
    except (RuntimeError, SystemExit) as e:
        print("STOP: the Sheet refused an edit after the item tabs were built:", str(e)[:300]); raise SystemExit(2)
    print(f"edit-acceptance check passed; grid cells now {cells_total(sid):,}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="data/config.json"); ap.add_argument("--target", required=True)
    ap.add_argument("--check", action="store_true"); ap.add_argument("--probe", action="store_true"); ap.add_argument("--build", action="store_true")
    a = ap.parse_args(argv)
    cfg = json.load(open(a.config)); sid = a.target
    wi, cc = used_rows(sid)
    lay = json.load(open(LAY)) if os.path.exists(LAY) else {}
    print(f"rows used now: work items + incidents {wi}, code changes {cc}; capacity {lay.get('wi_rows')} / {lay.get('cc_rows')}")
    if a.probe:
        edit_check(sid); return
    if a.check:
        if wi > lay["wi_rows"] or cc > lay["cc_rows"]:
            raise SystemExit("LAYOUT: the item tabs have no room for the rows: run the layout build")
        print("capacity ok"); return
    if not a.build:
        return
    wi_cap = int(wi * CAPACITY_FACTOR / 100 + 1) * 100
    cc_cap = int(cc * CAPACITY_FACTOR / 100 + 1) * 100
    cur = cells_total(sid)
    m = sheets("get", params={"spreadsheetId": sid, "fields": "sheets(properties(sheetId,title,index,gridProperties(rowCount,columnCount)))"})
    tabs = {s["properties"]["title"]: s["properties"] for s in m["sheets"]}
    have = sum(t["gridProperties"]["rowCount"] * t["gridProperties"]["columnCount"] for n, t in tabs.items() if n in ("Work items", "Code changes"))
    add = (wi_cap + 1) * len(HEAD_WI) + (cc_cap + 1) * len(HEAD_CC)
    total = cur - have + add
    print(f"cell budget: now {cur:,}; the two tabs {add:,} (rows {wi_cap:,} x {len(HEAD_WI)} and {cc_cap:,} x {len(HEAD_CC)}); total {total:,} = {100 * total / 10_000_000:.1f}% of 10,000,000")
    if total > BUDGET:
        raise SystemExit(f"STOP: {total:,} cells is over {BUDGET:,}")
    reqs = []
    anchor = tabs.get("Teams", {"index": 3})["index"]
    for i, (name, head, cap) in enumerate((("Work items", HEAD_WI, wi_cap), ("Code changes", HEAD_CC, cc_cap))):
        gp = {"rowCount": cap + 1, "columnCount": len(head), "frozenRowCount": 1}
        col = {"tabColorStyle": {"rgbColor": {"red": 0xFA / 255, "green": 0x7B / 255, "blue": 0x17 / 255}}}          # act colour, like Teams and Alerts
        if name in tabs:
            reqs.append({"updateSheetProperties": {"properties": {"sheetId": tabs[name]["sheetId"], "gridProperties": gp, **col}, "fields": "gridProperties,tabColorStyle"}})
            reqs.append({"updateCells": {"range": {"sheetId": tabs[name]["sheetId"]}, "fields": "userEnteredValue"}})
        else:
            reqs.append({"addSheet": {"properties": {"title": name, "index": anchor + 1 + i, "gridProperties": gp, **col}}})
    batch(sid, reqs)
    m = sheets("get", params={"spreadsheetId": sid, "fields": "sheets(properties(sheetId,title))"})
    gid = {s["properties"]["title"]: s["properties"]["sheetId"] for s in m["sheets"]}
    for name, head, fm, cap in (("Work items", HEAD_WI, wi_formulas(cfg), wi_cap), ("Code changes", HEAD_CC, cc_formulas(cfg, gid["Code changes"]), cc_cap)):
        values_update(sid, f"'{name}'!A1", [IF.WI_DISP if name == "Work items" else IF.CC_DISP], "RAW")
        for j, h in enumerate(head):
            values_update(sid, f"'{name}'!{col_letter(j)}2", [[fm[h]]])
    fmt = []
    for name, head in (("Work items", HEAD_WI), ("Code changes", HEAD_CC)):
        s = gid[name]
        fmt.append({"repeatCell": {"range": {"sheetId": s, "startRowIndex": 0, "endRowIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat.textFormat"}})
        for j, h in enumerate(head):
            if h in ("created", "finished", "merged"):
                fmt.append({"repeatCell": {"range": {"sheetId": s, "startRowIndex": 1, "startColumnIndex": j, "endColumnIndex": j + 1},
                                           "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}}}, "fields": "userEnteredFormat.numberFormat"}})
        fmt.append({"updateDimensionProperties": {"range": {"sheetId": s, "dimension": "COLUMNS", "startIndex": 0, "endIndex": len(head)}, "properties": {"pixelSize": 120}, "fields": "pixelSize"}})
    HOWTO = {"Work items": "How to read this tab: one row per Jira work item or incident (no titles, no names). The columns 'Finished last week', 'Finished last month', 'Added last week', 'Added last month', 'Stuck now', 'Blocked now', 'Open now' and 'Open too long' hold 1 when the row is counted in that Dashboard or Teams number. To get a number, filter in a temporary filter view: Data > Filter views > Create new temporary filter view (readers with comment access use this; the shared filter buttons in row 1 are for the owner). The cell note of each linked number says which filter, for example Finished last week = 1 and Group = " + cfg["groups"][0] + ". Column A is the link: click a key to open the ticket in Jira. Saved views (Data > Filter views) hold the measure and the Group but never the period: add the period flag yourself. Editors: use Data > Filter views > Create new temporary filter view, or reset the saved view after. Filled by formula from the data tabs: do not type here.",
             "Code changes": "How to read this tab: one row per merge request or pull request (no titles, no names; a repo in a personal namespace shows as personal project). 'Merged last week' and 'Merged last month' hold 1 when the change is counted in that Dashboard or Teams number. To get a number, filter in a temporary filter view: Data > Filter views > Create new temporary filter view (readers with comment access use this; the shared filter buttons in row 1 are for the owner). The cell note of each linked number says which filter, for example Merged last week = 1 and Group = " + cfg["groups"][0] + ". Column A is the link: click a number to open the change in GitLab or GitHub (a change in a personal namespace links to the top of this tab). Saved views (Data > Filter views) hold the measure and the Group but never the period: add the period flag yourself. Editors: use Data > Filter views > Create new temporary filter view, or reset the saved view after. Filled by formula from the data tabs: do not type here."}
    for name, head, cap in (("Work items", HEAD_WI, wi_cap), ("Code changes", HEAD_CC, cc_cap)):
        s_ = gid[name]
        fmt.append({"setBasicFilter": {"filter": {"range": {"sheetId": s_, "startRowIndex": 0, "endRowIndex": cap + 1, "startColumnIndex": 0, "endColumnIndex": len(head)}}}})
        fmt.append({"updateCells": {"rows": [{"values": [{"note": HOWTO[name]}]}], "fields": "note", "range": {"sheetId": s_, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1}}})
    batch(sid, fmt)
    json.dump({"wi_rows": wi_cap, "cc_rows": cc_cap, "wi_head": HEAD_WI, "cc_head": HEAD_CC, "wi_disp": IF.WI_DISP, "cc_disp": IF.CC_DISP, "gid": {"Work items": gid["Work items"], "Code changes": gid["Code changes"]}, "total_cells": total}, open(LAY, "w"), indent=1)
    print("item tabs written", LAY)
    edit_check(sid)


if __name__ == "__main__":
    main()
