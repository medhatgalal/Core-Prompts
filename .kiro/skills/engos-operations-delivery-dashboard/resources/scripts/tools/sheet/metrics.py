"""Metrics tab generator: Sheet formulas over named data ranges. Every number is a formula; thresholds are named cells.
Layout is a list of blocks stacked vertically. Each block registers named ranges (m_*) and named single cells (h_*)."""
from sheetlib import a1, col_letter
from tabs import date_serial


MANIFEST = None          # set by build.py from data/layout.json for the daily path and the layout run


class LayoutError(Exception):
    pass


class Grid:
    def __init__(self):
        self.cells = {}
        self.names = {}      # name -> (r0, c0, r1, c1) inclusive, 0-based, on Metrics
        self.row = 0
        self.refs = {}       # logical key -> A1 on Metrics (for citations)
        self.blocks = []     # (block key, start row) in order of title()
        self.manifest = MANIFEST

    def put(self, r, c, v):
        self.cells[(r, c)] = v

    def name_range(self, name, r0, c0, r1, c1):
        self.names[name] = (r0, c0, r1, c1)

    def name_cell(self, name, r, c):
        self.names[name] = (r, c, r, c)
        self.refs[name] = f"Metrics!{a1(r, c)}"

    def title(self, text):
        # v1.26 fixed layout (AC70): every block starts at an anchor from data/layout.json (written once by the layout build, with at least 50% spare rows per block).
        # Without a manifest the blocks are packed as before and recorded; with one, a block that would pass its anchor stops the build before any write.
        key = text.split(":")[0].split(" (")[0][:40]
        n = len(self.blocks)
        if self.manifest is not None:
            blk = self.manifest["blocks"]
            if n >= len(blk) or blk[n][0] != key:
                raise LayoutError(f"block {n} is '{key}' but the layout has '{blk[n][0] if n < len(blk) else 'nothing'}': the layout changed, run the layout build")
            if self.row > blk[n][1]:
                raise LayoutError(f"block '{blk[n - 1][0] if n else ''}' needs rows up to {self.row} but block '{key}' is anchored at row {blk[n][1]}: over capacity, run the layout build (no write was made)")
            self.row = blk[n][1]
        self.blocks.append((key, self.row))
        self.put(self.row, 0, text)
        self.row += 1

    def table(self, header, rows):
        r0 = self.row
        for j, h in enumerate(header):
            self.put(r0, j, h)
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                if v is not None:
                    self.put(r0 + 1 + i, j, v)
        self.row = r0 + 1 + len(rows) + 1
        return r0

    def to_rows(self):
        maxr = max(r for r, _ in self.cells) + 1
        maxc = max(c for _, c in self.cells) + 1
        out = [["" for _ in range(maxc)] for _ in range(maxr)]
        for (r, c), v in self.cells.items():
            out[r][c] = v
        return out


def level_rows(groups, roster_rows, L):
    """[(level, group, team)]: SBU, each Group, then Teams per Group (+ No team, Ownerless, Unmapped)."""
    rows = [("SBU", "*", "*")]
    allg = list(groups) + [L["other"], L["unknown"]]
    for g in allg:
        rows.append(("Group", g, "*"))
    teams_by_g = {}
    for r in roster_rows:
        g = r["group"] or L["other"]
        if r["team"]:
            teams_by_g.setdefault(g, set()).add(r["team"])
    for g in allg:
        ts = sorted(teams_by_g.get(g, []))
        extra = [] if g == L["unknown"] else [L["no_team"]]
        for t in ts + extra + [L["ownerless"], L["unmapped"]]:
            rows.append(("Team", g, t))
    return rows



def neg_run(rng, col):
    """Number of weeks, counting back from the last complete week, in which net was below zero (0 to 6). rng has a header row, then the 6 weeks (rows 2 to 7)."""
    c = lambda i: f"INDEX(INDEX({rng},0,{col}),{i})"
    return "=IF(" + c(7) + ">=0,0,IF(" + c(6) + ">=0,1,IF(" + c(5) + ">=0,2,IF(" + c(4) + ">=0,3,IF(" + c(3) + ">=0,4,IF(" + c(2) + ">=0,5,6))))))"

def build(meta, roster_rows, cfg, nrows, ind_n):
    """meta: derive meta; nrows: tab -> data row count; returns Grid"""
    L = cfg["labels"]
    G = Grid()
    weeks = meta["weeks"]
    W = [date_serial(w) for w in weeks]
    LV = level_rows(meta["groups"], roster_rows, L)
    groups_all = list(meta["groups"]) + [L["other"], L["unknown"]]

    # ---------------------------------------------------------------- header cells
    G.title("Metrics: every number here is a formula over the data tabs (named ranges ji_, jt_, ds_, cc_, cl_, cr_, ind_) and the Thresholds tab (t_). Blocks are stacked; each has a named range.")
    G.row += 1
    r = G.row
    G.put(r, 0, "as_of_utc"); G.put(r, 1, date_serial(meta["as_of"]) + 0)  # filled with exact serial below
    G.name_cell("asof", r, 1)
    from tabs import serial
    import datetime as dt
    G.cells[(r, 1)] = serial(dt.datetime.fromisoformat(meta["as_of"].replace("Z", "+00:00")))
    G.put(r + 1, 0, "window_start_utc"); G.cells[(r + 1, 1)] = serial(dt.datetime.fromisoformat(meta["window_start"].replace("Z", "+00:00")))
    G.name_cell("window_start", r + 1, 1)
    G.put(r + 2, 0, "last_complete_week_start"); G.put(r + 2, 1, W[-1]); G.name_cell("wk_last", r + 2, 1)
    G.put(r + 3, 0, "first_week_start"); G.put(r + 3, 1, W[0]); G.name_cell("wk_first", r + 3, 1)
    G.put(r + 4, 0, "weeks_in_review_window"); G.put(r + 4, 1, 12); G.name_cell("review_weeks", r + 4, 1)
    G.put(r + 5, 0, "age_hours_per_day"); G.put(r + 5, 1, 24); G.name_cell("hpd", r + 5, 1)
    G.put(r + 6, 0, "item_tab_guard"); G.put(r + 6, 1, meta.get("item_guard", "")); G.name_cell("item_guard", r + 6, 1)          # A69: empty when the item tabs have room; a warning or refusal text otherwise (shown in the Dashboard freshness line)
    G.put(r + 7, 0, "health_untagged_people"); G.put(r + 7, 1, meta.get("health_untagged", 0)); G.name_cell("health_untagged", r + 7, 1); G.put(r + 8, 0, "health_people_tickets"); G.put(r + 8, 1, meta.get("health_people_tickets", 0)); G.name_cell("health_people_tickets", r + 8, 1)          # AC72: untagged tickets assigned to our people (from the Jira pull, summed over the Individual rows)
    G.row = r + 9          # r + 8 (health_people_tickets) is the spare row that was there: the block keeps its size and the layout does not move

    # ---------------------------------------------------------------- weekly blocks
    n_w = len(W)
    # Spec ranges are long form; the Sheets chart API cannot pivot, so V1, V3, V9, V11, V12 read formula-built wide `<name>_chart` ranges
    # (AC v1.14 exception) that pivot the spec range cell for cell.
    series_defs = [("sbu_main", 'ji_series,"main"'), ("sbu_wont_do", 'ji_series,"wont_do"'), ("sbu_duplicate", 'ji_series,"duplicate"')]
    series_defs += [(f"main: {g}", f'ji_series,"main",ji_group,"{g}"') for g in groups_all]
    G.title("m_throughput (V1): Jira throughput per ISO week (UTC), complete weeks only, long form: week, series, count, rolling_avg (this week and the 3 before; blank until 4 weeks exist).")
    r0 = G.row
    G.put(r0, 0, "week"); G.put(r0, 1, "series"); G.put(r0, 2, "count"); G.put(r0, 3, "rolling_avg")
    for si, (sname, crit) in enumerate(series_defs):
        for i, w in enumerate(W):
            rr = r0 + 1 + si * n_w + i
            G.put(rr, 0, w); G.put(rr, 1, sname)
            G.put(rr, 2, f"=COUNTIFS({crit},ji_done_week,$A{rr+1})")
            if i >= 3:
                G.put(rr, 3, f"=AVERAGE(C{rr-2}:C{rr+1})")
    n_long = len(series_defs) * n_w
    G.name_range("m_throughput", r0, 0, r0 + n_long, 3)
    G.row = r0 + n_long + 2
    thr_r0 = r0
    G.title("m_throughput_chart (V1): wide pivot of m_throughput, one column per series, plus the SBU main rolling average.")
    c0 = G.row
    G.put(c0, 0, "week")
    for j, (sname, _) in enumerate(series_defs):
        G.put(c0, 1 + j, sname)
    G.put(c0, 1 + len(series_defs), "sbu_main_avg4")
    for i in range(n_w):
        rr = c0 + 1 + i
        G.put(rr, 0, f"=INDEX(INDEX(m_throughput,0,1),{i+2})")
        for j in range(len(series_defs)):
            cl = col_letter(1 + j)
            G.put(rr, 1 + j, f"=SUMIFS(INDEX(m_throughput,0,3),INDEX(m_throughput,0,1),$A{rr+1},INDEX(m_throughput,0,2),{cl}${c0+1})")
        if i >= 3:
            G.put(rr, 1 + len(series_defs), f'=SUMIFS(INDEX(m_throughput,0,4),INDEX(m_throughput,0,1),$A{rr+1},INDEX(m_throughput,0,2),"sbu_main")')
    G.name_range("m_throughput_chart", c0, 0, c0 + n_w, 1 + len(series_defs))
    G.row = c0 + n_w + 2

    G.title("m_created_done (V2): Jira work items created and finished per complete week (finished = final Done, all series).")
    r0 = G.row
    rows = []
    for i, w in enumerate(W):
        rr = r0 + 1 + i
        rows.append([w, f'=COUNTIFS(ji_is_work_item,1,ji_ours_c,1,ji_created_week,$A{rr+1})',
                     f'=COUNTIFS(ji_is_work_item,1,ji_done_week,$A{rr+1})'])
    G.table(["week", "created", "done"], rows)
    G.name_range("m_created_done", r0, 0, r0 + n_w, 2)

    cats = ["new", "indeterminate", "done"]
    G.title("m_cfd (V3): cumulative flow, long form: week end date, status category, work items at the end of that day (from Daily_Status_Counts).")
    r0 = G.row
    G.put(r0, 0, "date"); G.put(r0, 1, "category"); G.put(r0, 2, "count")
    for ci_, cat in enumerate(cats):
        for i, w in enumerate(W):
            rr = r0 + 1 + ci_ * n_w + i
            G.put(rr, 0, w + 6); G.put(rr, 1, cat)
            G.put(rr, 2, f"=SUMIFS(ds_count,ds_date,$A{rr+1},ds_status_category,$B{rr+1})")
    G.name_range("m_cfd", r0, 0, r0 + 3 * n_w, 2)
    G.row = r0 + 3 * n_w + 2
    G.title("m_cfd_chart (V3): wide pivot of m_cfd, one column per category.")
    c0 = G.row
    G.put(c0, 0, "date")
    for j, cat in enumerate(cats):
        G.put(c0, 1 + j, cat)
    for i in range(n_w):
        rr = c0 + 1 + i
        G.put(rr, 0, f"=INDEX(INDEX(m_cfd,0,1),{i+2})")
        for j in range(3):
            G.put(rr, 1 + j, f"=SUMIFS(INDEX(m_cfd,0,3),INDEX(m_cfd,0,1),$A{rr+1},INDEX(m_cfd,0,2),{col_letter(1+j)}${c0+1})")
    G.name_range("m_cfd_chart", c0, 0, c0 + n_w, 3)
    G.row = c0 + n_w + 2

    classes = ["normal", "bot", "revert", "docs", "backport", "release"]
    combos = [(p, c) for p in ("gitlab", "github") for c in classes]
    G.title("m_code_week (V9): changes merged per complete week, long form: week, platform, class, merged (counted once), median hours to first review for that platform and class.")
    r0 = G.row
    for j, h in enumerate(["week", "platform", "class", "merged", "median_first_review_hours"]):
        G.put(r0, j, h)
    for k, (p_, c_) in enumerate(combos):
        for i, w in enumerate(W):
            rr = r0 + 1 + k * n_w + i
            G.put(rr, 0, w); G.put(rr, 1, p_); G.put(rr, 2, c_)
            G.put(rr, 3, f'=COUNTIFS(cc_counted,1,cc_state,"merged",cc_merged_week,$A{rr+1},cc_platform,$B{rr+1},cc_class,$C{rr+1})')
            G.put(rr, 4, f'=IFERROR(MEDIAN(FILTER(cc_hours_to_first_review,cc_counted=1,cc_state="merged",cc_merged_week=$A{rr+1},cc_platform=$B{rr+1},cc_class=$C{rr+1},cc_hours_to_first_review<>"")),"")')
    G.name_range("m_code_week", r0, 0, r0 + len(combos) * n_w, 4)
    G.row = r0 + len(combos) * n_w + 2
    G.title("m_code_week_chart (V9): wide pivot of m_code_week: merged per platform and class, and median first-review hours of normal changes per platform.")
    c0 = G.row
    G.put(c0, 0, "week")
    for j, (p_, c_) in enumerate(combos):
        G.put(c0, 1 + j, f"{p_}: {c_}")
    G.put(c0, 13, "median_first_review_hours: gitlab (normal)"); G.put(c0, 14, "median_first_review_hours: github (normal)")
    for i in range(n_w):
        rr = c0 + 1 + i
        G.put(rr, 0, f"=INDEX(INDEX(m_code_week,0,1),{i+2})")
        for j, (p_, c_) in enumerate(combos):
            G.put(rr, 1 + j, f'=SUMIFS(INDEX(m_code_week,0,4),INDEX(m_code_week,0,1),$A{rr+1},INDEX(m_code_week,0,2),"{p_}",INDEX(m_code_week,0,3),"{c_}")')
        for j, p_ in enumerate(("gitlab", "github")):
            G.put(rr, 13 + j, f'=IFERROR(1/(1/SUMIFS(INDEX(m_code_week,0,5),INDEX(m_code_week,0,1),$A{rr+1},INDEX(m_code_week,0,2),"{p_}",INDEX(m_code_week,0,3),"normal")),"")')
    G.name_range("m_code_week_chart", c0, 0, c0 + n_w, 14)
    G.row = c0 + n_w + 2

    # merged per week by group (all classes), for the drop alert
    G.title("m_merged_group: merged changes per complete week (counted once, all classes) for the SBU and each Group.")
    hdr = ["week", "sbu"] + groups_all
    r0 = G.row
    rows = []
    for i, w in enumerate(W):
        rr = r0 + 1 + i
        row = [w, f'=COUNTIFS(cc_counted,1,cc_state,"merged",cc_merged_week,$A{rr+1})']
        for g in groups_all:
            row.append(f'=COUNTIFS(cc_counted,1,cc_state,"merged",cc_merged_week,$A{rr+1},cc_group,"{g}")')
        rows.append(row)
    G.table(hdr, rows)
    G.name_range("m_merged_group", r0, 0, r0 + n_w, len(hdr) - 1)
    mg_r0 = r0

    # ---------------------------------------------------------------- level table and blocks
    G.title("m_levels: one row per SBU, Group, and Team (with No team, Ownerless, Unmapped). Columns B and C are the criteria used by the formulas on the row ('*' = all).")
    lv_hdr = ["level", "group", "team"]
    cols = []   # (name, formula_fn(rr))   rr = 1-based sheet row

    def add(name, fn):
        cols.append((name, fn))

    def K(rr):  # criteria pair for Jira side and code side (same text)
        return f"$B{rr}", f"$C{rr}"

    def jc(rr, extra):  # COUNTIFS on Jira with level criteria
        g, t = K(rr)
        return f"COUNTIFS(ji_group,{g},ji_team,{t},{extra})"

    def jcc(rr, extra):  # COUNTIFS on Jira by the Group and Team at the CREATION date (v1.34: created counts read the tag at the event date); SBU rows need ours at creation
        g, t = K(rr)
        return f"COUNTIFS(ji_group_c,{g},ji_team_c,{t},ji_ours_c,1,{extra})"

    def cc_(rr, extra):
        g, t = K(rr)
        return f"COUNTIFS(cc_group,{g},cc_team,{t},{extra})"

    def jf(rr, rng, extra):  # FILTER on Jira by level
        g, t = K(rr)
        return f'FILTER({rng},(({g}="*")+(ji_group={g})>0)*(({t}="*")+(ji_team={t})>0)>0,{extra})'

    def cf(rr, rng, extra):
        g, t = K(rr)
        return f'FILTER({rng},(({g}="*")+(cc_group={g})>0)*(({t}="*")+(cc_team={t})>0)>0,{extra})'

    def FR(rr):   # distinct (change, reviewer) pairs with a review event in the last 12 complete weeks at this level
        g, t = K(rr)
        return (f'FILTER(cr_change_id&"|"&cr_reviewer,(({g}="*")+(cr_reviewer_group={g})>0)*(({t}="*")+(cr_reviewer_team={t})>0)>0,'
                f'cr_review_week>=wk_last-7*(review_weeks-1),cr_review_week<=wk_last)')

    # --- Jira backlog and flow
    add("open_work_items", lambda r: "=" + jc(r, 'ji_population,"open",ji_is_work_item,1'))
    add("open_containers", lambda r: "=" + jc(r, 'ji_population,"open",ji_is_work_item,0'))
    add("wip", lambda r: "=" + jc(r, "ji_wip,1"))
    add("open_not_started", lambda r: "=" + jc(r, 'ji_population,"open",ji_is_work_item,1,ji_status_category,"new"'))
    add("ownerless_open_work_items", lambda r: "=" + jc(r, 'ji_population,"open",ji_is_work_item,1,ji_owner_kind,"ownerless"'))
    add("ownerless_share_of_open", lambda r: f'=IFERROR(INDEX(L{r}:L{r},1)/INDEX(F{r}:F{r},1),"")')  # placeholder fixed below
    add("stale_open_work_items", lambda r: "=" + jc(r, 'ji_population,"open",ji_is_work_item,1,ji_days_since_update,">"&t_jira_stale_days'))
    add("stale_share_of_open", lambda r: "")
    add("aging_wip_over_p85", lambda r: "=" + jc(r, 'ji_wip,1,ji_start_age_days,">"&t_stuck_days'))          # v1.41: stuck = in progress longer than t_stuck_days (a fixed limit on the Thresholds tab), no longer the Group P85
    add("in_progress_no_owner", lambda r: "=" + jc(r, 'ji_wip,1,ji_owner_kind,"ownerless"'))
    add("oldest_no_owner_age_days", lambda r: f'=IFERROR(MAXIFS(ji_start_age_days,ji_group,$B{r},ji_team,$C{r},ji_wip,1,ji_owner_kind,"ownerless"),"")'.replace("MAXIFS(ji_start_age_days,ji_group,$B%d,ji_team,$C%d," % (r, r), "MAXIFS(ji_start_age_days,ji_group,$B%d,ji_team,$C%d," % (r, r)))
    for i, (lab, lo, hi) in enumerate([("0_30", None, "ba_hi1"), ("31_90", "ba_hi1", "ba_hi2"), ("91_365", "ba_hi2", "ba_hi3"), ("over_365", "ba_hi3", None)]):
        crit = 'ji_population,"open",ji_is_work_item,1'
        if lo:
            crit += f',ji_age_whole_days,">"&{lo}'
        if hi:
            crit += f',ji_age_whole_days,"<="&{hi}'
        add(f"backlog_age_{lab}", (lambda c: (lambda r: "=" + jc(r, c)))(crit))
    add("done_last_week_main", lambda r: "=" + jc(r, 'ji_series,"main",ji_done_week,wk_last'))
    add("done_prior4_avg_main", lambda r: "=" + jc(r, 'ji_series,"main",ji_done_week,">="&(wk_last-28),ji_done_week,"<="&(wk_last-7)') + "/4")
    add("done_last4_avg_main", lambda r: "=" + jc(r, 'ji_series,"main",ji_done_week,">="&(wk_last-21),ji_done_week,"<="&wk_last') + "/4")
    add("weeks_of_backlog", lambda r: "")
    add("created_last_week", lambda r: "=" + jcc(r, "ji_is_work_item,1,ji_created_week,wk_last"))
    add("throughput_drop_alert", lambda r: "")
    add("cycle_n", lambda r: "=" + jc(r, "ji_in_cycle_pop,1"))
    add("cycle_median_days", lambda r: f'=IFERROR(MEDIAN({jf(r, "ji_cycle_days", "ji_in_cycle_pop=1")}),"")')
    add("cycle_p85_days", lambda r: f'=IFERROR(PERCENTILE.INC({jf(r, "ji_cycle_days", "ji_in_cycle_pop=1")},0.85),"")')
    add("lead_median_days", lambda r: f'=IFERROR(MEDIAN({jf(r, "ji_lead_days", "ji_series=" + chr(34) + "main" + chr(34) + ",ji_lead_days<>" + chr(34) + chr(34))}),"")')
    add("lead_p85_days", lambda r: f'=IFERROR(PERCENTILE.INC({jf(r, "ji_lead_days", "ji_series=" + chr(34) + "main" + chr(34) + ",ji_lead_days<>" + chr(34) + chr(34))},0.85),"")')
    # --- code delivery
    add("merged_12m", lambda r: "=" + cc_(r, 'cc_counted,1,cc_state,"merged"'))
    add("merged_normal_12m", lambda r: "=" + cc_(r, 'cc_counted,1,cc_state,"merged",cc_class,"normal"'))
    add("merged_last_week", lambda r: "=" + cc_(r, 'cc_counted,1,cc_state,"merged",cc_class,"normal",cc_merged_week,wk_last'))          # v1.41 3c: ORDINARY changes, the basis of the Dashboard shipping-code row (designer)
    add("merged_prior4_avg", lambda r: "=" + cc_(r, 'cc_counted,1,cc_state,"merged",cc_class,"normal",cc_merged_week,">="&(wk_last-28),cc_merged_week,"<="&(wk_last-7)') + "/4")
    add("merge_drop_alert", lambda r: "")
    add("open_to_merge_median_days", lambda r: f'=IFERROR(MEDIAN({cf(r, "cc_open_to_merge_days", "cc_counted=1,cc_state=" + chr(34) + "merged" + chr(34))}),"")')
    add("open_to_merge_p85_days", lambda r: f'=IFERROR(PERCENTILE.INC({cf(r, "cc_open_to_merge_days", "cc_counted=1,cc_state=" + chr(34) + "merged" + chr(34))},0.85),"")')
    add("first_review_median_hours", lambda r: f'=IFERROR(MEDIAN({cf(r, "cc_hours_to_first_review", "cc_counted=1,cc_state=" + chr(34) + "merged" + chr(34) + ",cc_hours_to_first_review<>" + chr(34) + chr(34))}),"")')
    add("merged_normal_no_review", lambda r: "=" + cc_(r, 'cc_counted,1,cc_state,"merged",cc_class,"normal",cc_first_review_at,""'))
    add("open_changes", lambda r: "=" + cc_(r, 'cc_counted,1,cc_state,"open"'))
    add("open_normal_changes", lambda r: "=" + cc_(r, 'cc_counted,1,cc_state,"open",cc_class,"normal"'))
    add("open_age_median_days", lambda r: f'=IFERROR(MEDIAN({cf(r, "cc_open_age_days", "cc_counted=1,cc_state=" + chr(34) + "open" + chr(34))}),"")')
    add("open_age_p85_days", lambda r: f'=IFERROR(PERCENTILE.INC({cf(r, "cc_open_age_days", "cc_counted=1,cc_state=" + chr(34) + "open" + chr(34))},0.85),"")')
    add("open_age_max_days", lambda r: f'=IFERROR(MAXIFS(cc_open_age_days,cc_group,$B{r},cc_team,$C{r},cc_counted,1,cc_state,"open"),"")')
    add("reviews_per_week_12w", lambda r: f'=COUNTIFS(cr_reviewer_group,$B{r},cr_reviewer_team,$C{r},cr_review_week,">="&(wk_last-7*(review_weeks-1)),cr_review_week,"<="&wk_last)/review_weeks')
    add("changes_reviewed_per_week_12w", lambda r: f'=IFERROR(ROWS(UNIQUE({FR(r)}))/review_weeks,0)')
    add("open_no_review_over_limit", lambda r: "=" + cc_(r, 'cc_counted,1,cc_state,"open",cc_class,"normal",cc_first_review_at,"",cc_open_age_days,">"&t_first_review_days'))
    # --- hygiene C1..C8 (normal counted changes, merged or open) : pass, applicable, rate, fail
    ncl = 'cc_counted,1,cc_class,"normal",cc_state,"<>closed"'
    hyg = {}
    hyg["C1"] = (lambda r: "=" + cc_(r, ncl + ",cc_c1_pass,1"), lambda r: "=" + cc_(r, ncl + ",cc_c1_pass,\">=0\""))
    hyg["C2"] = (lambda r: "=" + cc_(r, ncl + ",cc_c2_pass,1"), lambda r: "=" + cc_(r, ncl + ",cc_c2_pass,\">=0\""))
    hyg["C3"] = (lambda r: "=" + cc_(r, ncl + ",cc_c3_pass,1"), lambda r: "=" + cc_(r, ncl + ",cc_c3_pass,\">=0\""))
    hyg["C4"] = (lambda r: "=" + cc_(r, ncl + ",cc_c4_pass,1"), lambda r: "=" + cc_(r, ncl + ",cc_c4_pass,\">=0\""))
    hyg["C5"] = (lambda r: "=" + cc_(r, ncl + ',cc_lines_for_c5,"<="&t_mr_size_lines'), lambda r: "=" + cc_(r, ncl + ',cc_lines_for_c5,">=0"'))
    hyg["C6"] = (lambda r: "=" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_state,"<>closed",cc_hours_to_first_review,"<="&(t_first_review_days*hpd)'),
                 lambda r: "=" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_state,"merged"') + "+" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_state,"open",cc_hours_to_first_review,">=-1E9"')
                 + "+" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_state,"open",cc_first_review_at,"",cc_open_age_days,">"&t_first_review_days'))
    c7b = 'cc_counted,1,cc_class,"normal",cc_state,"open"'
    hyg["C7"] = (lambda r: "=" + cc_(r, c7b + ',cc_days_since_activity,"<="&t_open_stale_days') + "-(1-t_c7_include_drafts)*" + cc_(r, c7b + ',cc_draft,1,cc_days_since_activity,"<="&t_open_stale_days'),
                 lambda r: "=" + cc_(r, c7b) + "-(1-t_c7_include_drafts)*" + cc_(r, c7b + ',cc_draft,1'))
    hyg["C8"] = (lambda r: "=" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_state,"open",cc_draft,1,cc_open_age_days,"<="&t_open_stale_days'),
                 lambda r: "=" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_state,"open",cc_draft,1'))
    hyg["J1"] = (lambda r: "=" + jc(r, "ji_j1_pass,1"), lambda r: "=" + jc(r, 'ji_j1_pass,">=0"'))
    hyg["J2"] = (lambda r: "=" + jc(r, "ji_wip,1,ji_days_since_update,\"<=\"&t_ip_stale_days"), lambda r: "=" + jc(r, "ji_wip,1"))
    hyg["J3"] = (lambda r: "=" + jc(r, "ji_j3_pass,1"), lambda r: "=" + jc(r, 'ji_j3_pass,">=0"'))
    hyg["J4"] = (lambda r: "=" + jc(r, "ji_j4_pass,1"), lambda r: "=" + jc(r, 'ji_j4_pass,">=0"'))
    hyg["J5"] = (lambda r: "=" + jc(r, "ji_j5_pass,1"), lambda r: "=" + jc(r, 'ji_j5_pass,">=0"'))
    hyg["J6"] = (lambda r: "=" + jc(r, "ji_j6_pass,1"), lambda r: "=" + jc(r, 'ji_j6_pass,">=0"'))
    for k, (pf, af) in hyg.items():
        add(f"{k}_pass", pf)
        add(f"{k}_applicable", af)
        add(f"{k}_fail", (lambda kk: (lambda r: f"={{{kk}_A}}-{{{kk}_P}}"))(k))  # resolved below
        add(f"{k}_pass_rate", (lambda kk: (lambda r: ""))(k))
    # exempt counts: changes not 'normal' (code) / containers (Jira)
    add("code_exempt_non_normal", lambda r: "=" + cc_(r, 'cc_counted,1,cc_class,"<>normal",cc_state,"<>closed"'))
    add("jira_exempt_containers_open", lambda r: "=" + jc(r, 'ji_population,"open",ji_is_work_item,0'))
    # --- alignment A1..A5
    add("A1_linked", lambda r: "=" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_key_state,"linked",cc_opened,">="&window_start'))
    add("A1_denominator", lambda r: "=" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_opened,">="&window_start'))
    add("A1_rate", lambda r: "")
    add("A2_count", lambda r: "=" + jc(r, "ji_wip,1,ji_is_code_type,1,ji_days_since_linked_activity,\">\"&t_ip_stale_days") + "+" + jc(r, 'ji_wip,1,ji_is_code_type,1,ji_days_since_linked_activity,""'))
    add("A2_denominator", lambda r: "=" + jc(r, "ji_wip,1,ji_is_code_type,1"))
    add("A2_rate", lambda r: "")
    add("A3_count", lambda r: "=" + jc(r, "ji_a3_status_lag,1"))
    add("A3_denominator", lambda r: "=" + jc(r, 'ji_a3_status_lag,">=0"'))
    add("A3_rate", lambda r: "")
    add("A4_count", lambda r: "=" + jc(r, "ji_a4_no_code,1"))
    add("A4_denominator", lambda r: "=" + jc(r, 'ji_a4_no_code,">=0"'))
    add("A4_rate", lambda r: "")
    add("A5_count", lambda r: "=" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_state,"merged",cc_key_state,"no_key"'))
    add("A5_denominator", lambda r: "=" + cc_(r, 'cc_counted,1,cc_class,"normal",cc_state,"merged"'))
    add("A5_rate", lambda r: "")
    add("people_over_wip_limit", lambda r: f'=COUNTIFS(ind_group,$B{r},ind_team,$C{r},ind_wip,">"&t_wip_per_person)')          # the tested form: COUNTIFS reads '*' on the SBU row as a wildcard; the person rows show exact WIP (A76)
    add("alert_people_over_wip_limit_group_total", lambda r: "")

    names = [c[0] for c in cols]
    ci = {n_: 3 + i for i, n_ in enumerate(names)}   # column index in Metrics

    def L_(name, rr):  # A1 ref of metric in the same row
        return f"{col_letter(ci[name])}{rr}"

    r0 = G.row
    G.title("m_levels (see title above): level, group, team, then metric columns")
    r0 = G.row
    hdr = lv_hdr + names
    rows = []
    for i, (lv, g, t) in enumerate(LV):
        rr = r0 + 1 + i + 1   # 1-based sheet row
        row = [lv, g, t]
        for name, fn in cols:
            f = fn(rr)
            # patches that reference other columns of the row
            if name == "ownerless_share_of_open":
                f = f'=IFERROR({L_("ownerless_open_work_items", rr)}/{L_("open_work_items", rr)},"")'
            elif name == "stale_share_of_open":
                f = f'=IFERROR({L_("stale_open_work_items", rr)}/{L_("open_work_items", rr)},"")'
            elif name == "weeks_of_backlog":
                f = f'=IFERROR({L_("open_work_items", rr)}/{L_("done_last4_avg_main", rr)},"")'
            elif name == "throughput_drop_alert":
                f = f'=IF({L_("done_prior4_avg_main", rr)}>0,IF({L_("done_last_week_main", rr)}<t_throughput_drop*{L_("done_prior4_avg_main", rr)},1,0),0)'
            elif name == "merge_drop_alert":
                f = f'=IF({L_("merged_prior4_avg", rr)}>0,IF({L_("merged_last_week", rr)}<t_throughput_drop*{L_("merged_prior4_avg", rr)},1,0),0)'
            elif name.endswith("_fail") and name[:-5] in hyg:
                k = name[:-5]
                f = f"={L_(k + '_applicable', rr)}-{L_(k + '_pass', rr)}"
            elif name.endswith("_pass_rate") and name[:-10] in hyg:
                k = name[:-10]
                f = f'=IFERROR({L_(k + "_pass", rr)}/{L_(k + "_applicable", rr)},"")'
            elif name in ("A1_rate", "A2_rate", "A3_rate", "A4_rate", "A5_rate"):
                k = name[:2]
                num = {"A1": "A1_linked"}.get(k, f"{k}_count")
                f = f'=IFERROR({L_(num, rr)}/{L_(k + "_denominator", rr)},"")'
            elif name == "alert_people_over_wip_limit_group_total":
                f = ""
            row.append(f)
        rows.append(row)
    G.table(hdr, rows)
    lv_r0 = r0
    lv_n = len(LV)
    G.name_range("m_levels", r0, 0, r0 + lv_n, len(hdr) - 1)
    for k in ("level", "group", "team"):
        pass
    G.name_range("lv_group", r0 + 1, 1, r0 + lv_n, 1)
    G.name_range("lv_team", r0 + 1, 2, r0 + lv_n, 2)
    G.name_range("lv_level", r0 + 1, 0, r0 + lv_n, 0)
    for name in names:
        G.name_range("lv_" + name, r0 + 1, ci[name], r0 + lv_n, ci[name])
    G.lv = {"rows": LV, "r0": r0, "ci": ci, "names": names}
    # backlog-age bucket edges (definition cells): referenced by the age buckets above
    G.title("m_backlog_age: open work items by age since created (SBU). Edges are the bucket upper bounds in days.")
    br0 = G.row
    G.put(br0, 0, "bucket"); G.put(br0, 1, "count"); G.put(br0, 2, "upper_bound_days")
    labs = ["0_30", "31_90", "91_365", "over_365"]
    sbu_r = lv_r0 + 2  # 1-based row of SBU level
    for i, lab in enumerate(labs):
        G.put(br0 + 1 + i, 0, lab)
        G.put(br0 + 1 + i, 1, f"={L_('backlog_age_' + lab, sbu_r)}".replace(col_letter(ci['backlog_age_' + lab]), "Metrics!" + col_letter(ci['backlog_age_' + lab])) if False else f"={col_letter(ci['backlog_age_' + lab])}{sbu_r}")
    for i, v in enumerate([30, 90, 365]):
        G.put(br0 + 1 + i, 2, v)
        G.name_cell(f"ba_hi{i + 1}", br0 + 1 + i, 2)
    G.name_range("m_backlog_age", br0, 0, br0 + 4, 1)
    G.row = br0 + 6

    # ---------------------------------------------------------------- headline
    def lvref(name, row_key=("SBU", "*", "*")):
        i = LV.index(row_key)
        return f"{col_letter(ci[name])}{lv_r0 + 2 + i}"

    G.title("m_headline: headline metrics with week-over-week change (change = value minus previous_week, precomputed)")
    hr0 = G.row
    G.put(hr0, 0, "metric"); G.put(hr0, 1, "value"); G.put(hr0, 2, "previous_week"); G.put(hr0, 3, "change"); G.put(hr0, 4, "unit"); G.put(hr0, 5, "definition")
    asof7 = "asof-7"
    H = [
        ("in_progress_no_owner", f"={lvref('in_progress_no_owner')}", "=COUNTIFS(ji_no_owner_wip_prev_week,1)", "items", "Work items in an In Progress category with no assignee (headline problem); previous = the same one week before the as-of"),
        ("wip", f"={lvref('wip')}", "=COUNTIFS(ji_wip_prev_week,1)", "items", "Work items in an In Progress category now; previous = one week before the as-of"),
        ("open_backlog_work_items", f"={lvref('open_work_items')}", '=SUMIFS(ds_count,ds_date,INT(asof-7),ds_status_category,"new")+SUMIFS(ds_count,ds_date,INT(asof-7),ds_status_category,"indeterminate")', "items", "Open work items (new plus in progress categories); previous from the daily snapshot a week earlier"),
        ("jira_done_last_week", f"={lvref('done_last_week_main')}", '=COUNTIFS(ji_series,"main",ji_done_week,wk_last-7)', "items", "Main-series work items finished in the last complete week"),
        ("jira_created_last_week", f"={lvref('created_last_week')}", "=COUNTIFS(ji_is_work_item,1,ji_created_week,wk_last-7)", "items", "Work items created in the last complete week"),
        ("changes_merged_last_week", f"={lvref('merged_last_week')}", '=COUNTIFS(cc_counted,1,cc_state,"merged",cc_merged_week,wk_last-7)', "changes", "Changes merged in the last complete week (counted once)"),
        ("cycle_median_days", f"={lvref('cycle_median_days')}", '=IFERROR(MEDIAN(FILTER(ji_cycle_days,ji_in_cycle_pop=1,ji_final_done<=asof-7)),"")', "days", "Median first start to final Done, 12-month finished main-series work items; previous = items finished by one week before the as-of"),
        ("cycle_p85_days", f"={lvref('cycle_p85_days')}", '=IFERROR(PERCENTILE.INC(FILTER(ji_cycle_days,ji_in_cycle_pop=1,ji_final_done<=asof-7),0.85),"")', "days", "P85 of the same"),
        ("weeks_of_backlog", f"={lvref('weeks_of_backlog')}", '=IFERROR((SUMIFS(ds_count,ds_date,INT(asof-7),ds_status_category,"new")+SUMIFS(ds_count,ds_date,INT(asof-7),ds_status_category,"indeterminate"))/(COUNTIFS(ji_series,"main",ji_done_week,">="&(wk_last-28),ji_done_week,"<="&(wk_last-7))/4),"")', "weeks", "Open work items divided by the 4-week trailing average of main-series throughput; previous = a week earlier, weeks shifted back one"),
        ("weeks_of_backlog_basis", '=TEXT(wk_last-21,"yyyy-mm-dd")&" to "&TEXT(wk_last,"yyyy-mm-dd")', "", "weeks", "The four ISO weeks (Monday dates, first to last) averaged for weeks_of_backlog"),
        ("open_to_merge_median_days", f"={lvref('open_to_merge_median_days')}", '=IFERROR(MEDIAN(FILTER(cc_open_to_merge_days,cc_counted=1,cc_state="merged",cc_merged_at<=asof-7)),"")', "days", "Median opened to merged, changes merged in the window; previous = merged by one week before the as-of"),
        ("first_review_median_hours", f"={lvref('first_review_median_hours')}", '=IFERROR(MEDIAN(FILTER(cc_hours_to_first_review,cc_counted=1,cc_state="merged",cc_merged_at<=asof-7,cc_hours_to_first_review<>"")),"")', "hours", "Median opened to first review; previous as above"),
        ("a1_link_rate", f"={lvref('A1_rate')}", '=IFERROR(COUNTIFS(cc_counted,1,cc_class,"normal",cc_key_state,"linked",cc_opened,"<="&(asof-7))/COUNTIFS(cc_counted,1,cc_class,"normal",cc_opened,"<="&(asof-7)),"")', "fraction", "Share of normal changes carrying a linked Jira key; previous = changes opened by one week before the as-of"),
    ]
    for i, (nm, v, pv, unit, d) in enumerate(H):
        rr = hr0 + 1 + i
        G.put(rr, 0, nm); G.put(rr, 1, v)
        if pv:
            G.put(rr, 2, pv)
            G.put(rr, 3, f'=IFERROR(B{rr+1}-C{rr+1},"")')
        G.put(rr, 4, unit); G.put(rr, 5, d)
        G.name_cell("h_" + nm, rr, 1)
    G.name_range("m_headline", hr0, 0, hr0 + len(H), 5)
    G.row = hr0 + len(H) + 2

    # ---------------------------------------------------------------- SBU single-purpose blocks
    # V4 cycle bins
    G.title("m_cycle_bins (V4): cycle time distribution, 20 bins from 0 to the P95 (last bin open-ended); median and p85 repeat on each row.")
    cb0 = G.row
    for j, h in enumerate(["bin_low", "bin_high", "count", "median", "p85"]):
        G.put(cb0, j, h)
    sbu = lv_r0 + 2
    G.put(cb0, 9, "bin_width_days"); G.put(cb0 + 1, 9, '=ROUNDUP(PERCENTILE.INC(ji_cycle_days,0.95)/19,1)')
    G.name_cell("cycle_bin_width", cb0 + 1, 9)
    for i in range(20):
        rr = cb0 + 1 + i
        sr = rr + 1
        G.put(rr, 0, f"={i}*cycle_bin_width")
        G.put(rr, 1, f"=A{sr}+cycle_bin_width" if i < 19 else "")
        G.put(rr, 2, f'=COUNTIFS(ji_in_cycle_pop,1,ji_cycle_days,">="&A{sr},ji_cycle_days,"<"&B{sr})' if i < 19 else f'=COUNTIFS(ji_in_cycle_pop,1,ji_cycle_days,">="&A{sr})')
        G.put(rr, 3, f"={col_letter(ci['cycle_median_days'])}{sbu}")
        G.put(rr, 4, f"={col_letter(ci['cycle_p85_days'])}{sbu}")
    G.name_range("m_cycle_bins", cb0, 0, cb0 + 20, 4)
    G.row = cb0 + 22

    # time in status (SBU)
    G.title("m_time_in_status: median days in each status before leaving it, finished main-series work items; time after the strict final Done is not counted (statuses listed from the data).")
    ts0 = G.row
    G.put(ts0, 0, "status"); G.put(ts0, 1, "median_days"); G.put(ts0, 2, "transitions")
    for i, s in enumerate(meta["statuses"]):
        rr = ts0 + 1 + i
        G.put(rr, 0, s)
        G.put(rr, 1, f'=IFERROR(MEDIAN(FILTER(jt_days_in_from_status,jt_from_status=A{rr+1},jt_in_cycle_pop=1,jt_days_in_from_status<>"")),"")')
        G.put(rr, 2, f'=COUNTIFS(jt_from_status,A{rr+1},jt_in_cycle_pop,1,jt_days_in_from_status,">=0")')
    G.name_range("m_time_in_status", ts0, 0, ts0 + len(meta["statuses"]), 2)
    G.row = ts0 + len(meta["statuses"]) + 2

    # backlog by status and by type (SBU)
    G.title("m_backlog_status: open items by status; m_backlog_type: open items by type (work items and containers).")
    bs0 = G.row
    G.put(bs0, 0, "status"); G.put(bs0, 1, "open_work_items")
    for i, s in enumerate(meta["open_statuses"]):
        G.put(bs0 + 1 + i, 0, s)
        G.put(bs0 + 1 + i, 1, f'=COUNTIFS(ji_population,"open",ji_is_work_item,1,ji_status,A{bs0+2+i})')
    G.name_range("m_backlog_status", bs0, 0, bs0 + len(meta["open_statuses"]), 1)
    bt0 = bs0
    G.put(bt0, 3, "type"); G.put(bt0, 4, "open_items")
    for i, s in enumerate(meta["open_types"]):
        G.put(bt0 + 1 + i, 3, s)
        G.put(bt0 + 1 + i, 4, f'=COUNTIFS(ji_population,"open",ji_type,D{bt0+2+i})')
    G.name_range("m_backlog_type", bt0, 3, bt0 + len(meta["open_types"]), 4)
    G.row = bs0 + max(len(meta["open_statuses"]), len(meta["open_types"])) + 3

    # ---- V5 aging WIP list
    n_wip = meta["n_wip"]
    G.title("m_aging_wip: in-progress work items with age since start and the P85 of their Group (list = all in-progress work items at the as-of time).")
    aw0 = G.row
    for j, h in enumerate(["key", "group", "age_days", "group_p85"]):
        G.put(aw0, j, h)
    for i in range(n_wip):
        rr = aw0 + 1 + i
        G.put(rr, 0, f'=IFERROR(INDEX(FILTER(ji_key,ji_wip=1),{i+1}),"")')
        G.put(rr, 1, f'=IFERROR(INDEX(ji_group,MATCH(A{rr+1},ji_key,0)),"")')
        G.put(rr, 2, f'=IFERROR(INDEX(ji_start_age_days,MATCH(A{rr+1},ji_key,0)),"")')
        G.put(rr, 3, f'=IFERROR(INDEX(ji_group_p85_cycle_days,MATCH(A{rr+1},ji_key,0)),"")')
    G.name_range("m_aging_wip", aw0, 0, aw0 + n_wip, 3)
    G.row = aw0 + n_wip + 2

    # ---- V6 wip by group and team
    G.title("m_wip (V6): in-progress work items by Group and Team (group, team, wip; label is an extra column for the chart axis).")
    wp0 = G.row
    G.put(wp0, 0, "group"); G.put(wp0, 1, "team"); G.put(wp0, 2, "wip"); G.put(wp0, 3, "label")
    team_rows = [x for x in LV if x[0] == "Team"]
    for i, (_, g, t) in enumerate(team_rows):
        rr = wp0 + 1 + i
        G.put(rr, 0, g); G.put(rr, 1, t); G.put(rr, 2, f"=COUNTIFS(ji_group,A{rr+1},ji_team,B{rr+1},ji_wip,1)")
        G.put(rr, 3, (f'=B{rr+1}&" ("&A{rr+1}&")"' if t in (L["ownerless"], L["unmapped"], L["no_team"]) else f"=B{rr+1}"))
    G.name_range("m_wip", wp0, 0, wp0 + len(team_rows), 3)
    G.row = wp0 + len(team_rows) + 2

    # ---- V8 in progress no owner by group + list
    G.title("m_noowner_ip: in progress with no owner by Group (count, oldest age since start).")
    no0 = G.row
    G.put(no0, 0, "group"); G.put(no0, 1, "count"); G.put(no0, 2, "oldest_age_days")
    for i, g in enumerate(groups_all):
        rr = no0 + 1 + i
        G.put(rr, 0, g)
        G.put(rr, 1, f'=COUNTIFS(ji_group,A{rr+1},ji_wip,1,ji_owner_kind,"ownerless")')
        G.put(rr, 2, f'=IFERROR(MAXIFS(ji_start_age_days,ji_group,A{rr+1},ji_wip,1,ji_owner_kind,"ownerless"),"")')
    G.name_range("m_noowner_ip", no0, 0, no0 + len(groups_all), 2)
    G.row = no0 + len(groups_all) + 2
    G.title("m_noowner_list (V8): each in-progress work item with no owner: key, group, age_days, status (status is an extra column).")
    nl0 = G.row
    nn = meta["n_noowner"]
    for j, h in enumerate(["key", "group", "age_days", "status"]):
        G.put(nl0, j, h)
    for i in range(max(nn, 1)):
        rr = nl0 + 1 + i
        G.put(rr, 0, f'=IFERROR(INDEX(FILTER(ji_key,ji_wip=1,ji_owner_kind="ownerless"),{i+1}),"")')
        G.put(rr, 1, f'=IFERROR(INDEX(ji_group,MATCH(A{rr+1},ji_key,0)),"")')
        G.put(rr, 2, f'=IFERROR(INDEX(ji_start_age_days,MATCH(A{rr+1},ji_key,0)),"")')
        G.put(rr, 3, f'=IFERROR(INDEX(ji_status,MATCH(A{rr+1},ji_key,0)),"")')
    G.name_range("m_noowner_list", nl0, 0, nl0 + max(nn, 1), 3)
    G.row = nl0 + max(nn, 1) + 3

    # ---- V10 review load by team
    G.title("m_review_team: reviews given per week by reviewer Team, average of the last 12 complete weeks.")
    rt0 = G.row
    G.put(rt0, 0, "team"); G.put(rt0, 1, "reviews_per_week")
    rt_teams = sorted({t for (_, g, t) in team_rows if t not in (L["ownerless"], L["unmapped"])})
    for i, t in enumerate(rt_teams):
        rr = rt0 + 1 + i
        G.put(rr, 0, t)
        G.put(rr, 1, f'=COUNTIFS(cr_reviewer_team,A{rr+1},cr_review_week,">="&(wk_last-7*(review_weeks-1)),cr_review_week,"<="&wk_last)/review_weeks')
    G.name_range("m_review_team", rt0, 0, rt0 + len(rt_teams), 1)
    G.row = rt0 + len(rt_teams) + 2

    # ---- V11 hygiene: long spec range m_hygiene and wide m_hygiene_chart
    scopes = [("SBU", "*", "*")] + [("Group", g, "*") for g in groups_all]
    checks = list(hyg.keys())
    G.title("m_hygiene (V11): pass rate, failing count, and exempt count by check and Group (long form; SBU rows first within each check).")
    hc0 = G.row
    for j, h in enumerate(["system", "check", "group", "pass_rate", "failing_count", "exempt_count"]):
        G.put(hc0, j, h)
    rr = hc0 + 1
    for k in checks:
        for sc in scopes:
            lr = lv_r0 + 2 + LV.index(sc)
            G.put(rr, 0, "code" if k[0] == "C" else "jira"); G.put(rr, 1, k)
            G.put(rr, 2, "SBU" if sc[1] == "*" else sc[1])
            G.put(rr, 3, f"={col_letter(ci[k + '_pass_rate'])}{lr}")
            G.put(rr, 4, f"={col_letter(ci[k + '_fail'])}{lr}")
            G.put(rr, 5, f"={col_letter(ci['code_exempt_non_normal'] if k[0] == 'C' else ci['jira_exempt_containers_open'])}{lr}")
            rr += 1
    G.name_range("m_hygiene", hc0, 0, rr - 1, 5)
    G.row = rr + 1
    G.title("m_hygiene_chart (V11): wide pivot of m_hygiene: pass rate by check (rows) and Group (columns).")
    hy0 = G.row
    G.put(hy0, 0, "check")
    for j, (_, g, _) in enumerate(scopes):
        G.put(hy0, 1 + j, "SBU" if g == "*" else g)
    for i, k in enumerate(checks):
        r_ = hy0 + 1 + i
        G.put(r_, 0, k)
        for j in range(len(scopes)):
            G.put(r_, 1 + j, f'=IF(COUNTIFS(INDEX(m_hygiene,0,2),$A{r_+1},INDEX(m_hygiene,0,3),{col_letter(1+j)}${hy0+1},INDEX(m_hygiene,0,4),">=0")=0,"",SUMIFS(INDEX(m_hygiene,0,4),INDEX(m_hygiene,0,2),$A{r_+1},INDEX(m_hygiene,0,3),{col_letter(1+j)}${hy0+1}))')
    G.name_range("m_hygiene_chart", hy0, 0, hy0 + len(checks), len(scopes))
    G.row = hy0 + len(checks) + 2

    # ---- V12 alignment long and wide
    G.title("m_align (V12): alignment measures A1 to A5 by level (SBU, Group, Team), long form: measure, level, name, count, rate.")
    al0 = G.row
    for j, h in enumerate(["measure", "level", "name", "count", "rate"]):
        G.put(al0, j, h)
    rr = al0 + 1
    for k in ("A1", "A2", "A3", "A4", "A5"):
        for i, (lv, g, t) in enumerate(LV):
            lr = lv_r0 + 2 + i
            nm = "SBU" if lv == "SBU" else (g if lv == "Group" else f"{g} / {t}")
            cnt = "A1_linked" if k == "A1" else f"{k}_count"
            G.put(rr, 0, k); G.put(rr, 1, lv); G.put(rr, 2, nm)
            G.put(rr, 3, f"={col_letter(ci[cnt])}{lr}")
            G.put(rr, 4, f"={col_letter(ci[k + '_rate'])}{lr}")
            rr += 1
    G.name_range("m_align", al0, 0, rr - 1, 4)
    G.row = rr + 1
    G.title("m_align_chart (V12): wide pivot of m_align: rate by measure (rows) and Group (columns).")
    aw1 = G.row
    G.put(aw1, 0, "measure")
    for j, (_, g, _) in enumerate(scopes):
        G.put(aw1, 1 + j, "SBU" if g == "*" else g)
    for i, k in enumerate(("A1", "A2", "A3", "A4", "A5")):
        G.put(aw1 + 1 + i, 0, k)
        for j in range(len(scopes)):
            G.put(aw1 + 1 + i, 1 + j, f'=IF(COUNTIFS(INDEX(m_align,0,1),$A{aw1+2+i},INDEX(m_align,0,3),{col_letter(1+j)}${aw1+1},INDEX(m_align,0,5),">=0")=0,"",SUMIFS(INDEX(m_align,0,5),INDEX(m_align,0,1),$A{aw1+2+i},INDEX(m_align,0,3),{col_letter(1+j)}${aw1+1}))')
    G.name_range("m_align_chart", aw1, 0, aw1 + 5, len(scopes))
    G.row = aw1 + 7

    # ---- V13 open changes
    n_open = meta["n_open_normal"]
    G.title("m_open_changes: open normal changes (counted once): age, size, and the two thresholds.")
    oc0 = G.row
    for j, h in enumerate(["id", "group", "age_days", "lines", "size_threshold", "stale_threshold"]):
        G.put(oc0, j, h)
    for i in range(n_open):
        rr = oc0 + 1 + i
        G.put(rr, 0, f'=IFERROR(INDEX(FILTER(cc_change_id,cc_counted=1,cc_state="open",cc_class="normal"),{i+1}),"")')
        G.put(rr, 1, f'=IFERROR(INDEX(cc_group,MATCH(A{rr+1},cc_change_id,0)),"")')
        G.put(rr, 2, f'=IFERROR(INDEX(cc_open_age_days,MATCH(A{rr+1},cc_change_id,0)),"")')
        G.put(rr, 3, f'=IFERROR(INDEX(cc_lines_excl,MATCH(A{rr+1},cc_change_id,0)),"")')
        G.put(rr, 4, "=t_mr_size_lines")
        G.put(rr, 5, "=t_open_stale_days")
    G.name_range("m_open_changes", oc0, 0, oc0 + n_open, 5)
    G.row = oc0 + n_open + 3

    # ---------------------------------------------------------------- Dashboard ranges d_* (v1.16): formula-built from the m_ ranges
    G.title("d_created_done (D1): last 13 complete weeks, SBU: week, created (from m_created_done), done = the main throughput series (Won't Do and Duplicate excluded, from m_throughput), net = done minus created, and a zero column for the break-even line.")
    d0 = G.row
    for j, h in enumerate(["week", "created", "done", "net", "Zero (break-even)"]):
        G.put(d0, j, h)
    for k in range(13):
        rr = d0 + 1 + k
        for j in range(2):
            G.put(rr, j, f"=INDEX(INDEX(m_created_done,0,{j+1}),ROWS(m_created_done)-13+{k+1})")
        G.put(rr, 2, f'=SUMIFS(INDEX(m_throughput,0,3),INDEX(m_throughput,0,1),$A{rr+1},INDEX(m_throughput,0,2),"sbu_main")')
        G.put(rr, 3, f"=C{rr+1}-B{rr+1}")
        G.put(rr, 4, 0)
    G.name_range("d_created_done", d0, 0, d0 + 13, 4)
    G.row = d0 + 15
    G.title("d_noowner (D2): in progress with no owner by Group: group, count (from m_noowner_ip).")
    d0 = G.row
    G.put(d0, 0, "group"); G.put(d0, 1, "count")
    for k in range(len(groups_all)):
        G.put(d0 + 1 + k, 0, f"=INDEX(INDEX(m_noowner_ip,0,1),{k+2})")
        G.put(d0 + 1 + k, 1, f"=INDEX(INDEX(m_noowner_ip,0,2),{k+2})")
    G.name_range("d_noowner", d0, 0, d0 + len(groups_all), 1)
    G.row = d0 + len(groups_all) + 2
    G.title("d_stuck (D3): in-progress items older than t_stuck_days by Group: group, count, oldest_age_days (from m_aging_wip).")
    d0 = G.row
    for j, h in enumerate(["group", "count", "oldest_age_days"]):
        G.put(d0, j, h)
    for k in range(len(groups_all)):
        rr = d0 + 1 + k
        G.put(rr, 0, f"=INDEX(INDEX(m_noowner_ip,0,1),{k+2})")
        G.put(rr, 1, f"=SUMPRODUCT((INDEX(m_aging_wip,0,2)=$A{rr+1})*(INDEX(m_aging_wip,0,3)>t_stuck_days))")
        G.put(rr, 2, f"=ARRAYFORMULA(MAX(IF((INDEX(m_aging_wip,0,2)=$A{rr+1})*(INDEX(m_aging_wip,0,3)>t_stuck_days),INDEX(m_aging_wip,0,3),0)))")
    G.name_range("d_stuck", d0, 0, d0 + len(groups_all), 2)
    G.row = d0 + len(groups_all) + 2
    G.title("d_merged (D4): merged normal changes per week, both platforms, last 13 complete weeks (from m_code_week).")
    d0 = G.row
    G.put(d0, 0, "week"); G.put(d0, 1, "merged")
    for k in range(13):
        rr = d0 + 1 + k
        G.put(rr, 0, f"=INDEX(INDEX(m_created_done,0,1),ROWS(m_created_done)-13+{k+1})")
        G.put(rr, 1, f'=SUMIFS(INDEX(m_code_week,0,4),INDEX(m_code_week,0,1),$A{rr+1},INDEX(m_code_week,0,3),"normal")')
    G.name_range("d_merged", d0, 0, d0 + 13, 1)
    G.row = d0 + 15
    G.title("d_first_review (D5): median hours to first review of merged normal changes, both platforms, last 13 complete weeks. A combined median cannot be built from the per-platform medians in m_code_week, so it is computed from the merged changes with the same filters.")
    d0 = G.row
    G.put(d0, 0, "week"); G.put(d0, 1, "median_first_review_hours")
    for k in range(13):
        rr = d0 + 1 + k
        G.put(rr, 0, f"=INDEX(INDEX(m_created_done,0,1),ROWS(m_created_done)-13+{k+1})")
        G.put(rr, 1, f'=IFERROR(MEDIAN(FILTER(cc_hours_to_first_review,cc_counted=1,cc_state="merged",cc_class="normal",cc_merged_week=$A{rr+1},cc_hours_to_first_review<>"")),"")')
    G.name_range("d_first_review", d0, 0, d0 + 13, 1)
    G.row = d0 + 15
    G.title("d_align (D6): A1 link rate and A4 Done-with-no-code count by Group: group, a1_rate, a4_count (from m_align).")
    d0 = G.row
    for j, h in enumerate(["group", "a1_rate", "a4_count"]):
        G.put(d0, j, h)
    for k in range(len(groups_all)):
        rr = d0 + 1 + k
        G.put(rr, 0, f"=INDEX(INDEX(m_noowner_ip,0,1),{k+2})")
        G.put(rr, 1, f'=IF(COUNTIFS(INDEX(m_align,0,1),"A1",INDEX(m_align,0,3),$A{rr+1},INDEX(m_align,0,5),">=0")=0,"",SUMIFS(INDEX(m_align,0,5),INDEX(m_align,0,1),"A1",INDEX(m_align,0,3),$A{rr+1}))')
        G.put(rr, 2, f'=SUMIFS(INDEX(m_align,0,4),INDEX(m_align,0,1),"A4",INDEX(m_align,0,3),$A{rr+1})')
    G.name_range("d_align", d0, 0, d0 + len(groups_all), 2)
    G.row = d0 + len(groups_all) + 2

    # ---------------------------------------------------------------- 6/12 blocks (D77, D80, D85): 6 weekly points, a gap row, 12 monthly points
    def six12(rng, title, measures, zero=False, rnd=None):
        """measures: [(header, week_formula(k) -> str, month_formula(st, rr) -> str)]. Columns: label, then per measure weekly and monthly value, an optional
        zero line, then per measure two label columns holding the value only at the points that get a data label (last point of each segment,
        the peak and the low), so labels never crowd each other. Weekly cells are blank in the month rows and the other way round; the gap row is blank."""
        G.title(title)
        f0 = G.row
        n = len(measures)
        cols = ["label"] + [f"{m[0]} per week" for m in measures] + [f"{m[0]} per month" for m in measures] + (["Zero (break-even)"] if zero else [])
        lbl0 = len(cols)
        cols += [f"{m[0]} weekly label" for m in measures] + [f"{m[0]} monthly label" for m in measures]
        for j, h in enumerate(cols):
            G.put(f0, j, h)
        for k in range(6):
            rr = f0 + 1 + k
            G.put(rr, 0, f'="Wk "&TEXT(INDEX(INDEX(d_created_done,0,1),ROWS(d_created_done)-6+{k+1}),"mmm d")')
            for i, m in enumerate(measures):
                G.put(rr, 1 + i, m[1](k))
        for k in range(12):
            rr = f0 + 8 + k
            st = f"EDATE(DATE(YEAR(asof),MONTH(asof),1),{k-12})" if k else "(EDATE(asof,-12)+MOD(asof,1))"       # W1: the first month starts at the window start
            G.put(rr, 0, f'=TEXT({st},"mmm yyyy")' if k else f'=TEXT({st},"mmm yyyy")&" (from "&TEXT({st},"d mmm")&")"')
            for i, m in enumerate(measures):
                G.put(rr, 1 + n + i, m[2](st, rr))
        if zero:
            for rr in range(f0 + 1, f0 + 20):
                G.put(rr, 1 + 2 * n, 0)
        for i in range(n):
            for seg, (r_a, r_b, c) in (("w", (f0 + 1, f0 + 6, 1 + i)), ("m", (f0 + 8, f0 + 19, 1 + n + i))):
                L = col_letter(c)
                rngA = f"${L}${r_a + 1}:${L}${r_b + 1}"
                for rr in range(r_a, r_b + 1):
                    cell = f"{L}{rr + 1}"
                    val = f"ROUND({cell},{rnd})" if rnd is not None else cell
                    fmt_ = ("0." + "0" * rnd) if rnd else "0"
                    # the label is TEXT: custom chart labels read text cells (numeric label cells made the chart request fail with an internal error)
                    G.put(rr, lbl0 + (i if seg == "w" else n + i), f'=IF(OR(ROW()={r_b + 1},{cell}=MAX({rngA}),{cell}=MIN({rngA})),TEXT({val},"{fmt_}"),"")')
        G.name_range(rng, f0, 0, f0 + 19, len(cols) - 1)
        G.row = f0 + 22
        return f0

    mon_added = lambda st, rr: f'=COUNTIFS(ji_is_work_item,1,ji_ours_c,1,ji_created,">="&{st},ji_created,"<"&EDATE(DATE(YEAR({st}),MONTH({st}),1),1))'
    mon_fin = lambda st, rr: f'=COUNTIFS(ji_series,"main",ji_final_done,">="&{st},ji_final_done,"<"&EDATE(DATE(YEAR({st}),MONTH({st}),1),1))'
    six12("d_flow612", "d_flow612 (6/12, D1): work items added, finished and net (finished minus added), the last 6 complete weeks then the last 12 complete months. finished = main throughput series (Won't Do and Duplicate excluded). Weekly and monthly values are separate columns (they sit on different axes); the gap row is blank; the first month starts before the data window, so it is partial. The label columns hold a value only at the points that get a data label.",
          [("Added", lambda k: f"=INDEX(INDEX(d_created_done,0,2),ROWS(d_created_done)-6+{k+1})", mon_added),
           ("Finished", lambda k: f"=INDEX(INDEX(d_created_done,0,3),ROWS(d_created_done)-6+{k+1})", mon_fin),
           ("Net", lambda k: f"=INDEX(INDEX(d_created_done,0,4),ROWS(d_created_done)-6+{k+1})", lambda st, rr: f"=F{rr+1}-E{rr+1}")], zero=True)
    six12("d_code612", "d_code612 (6/12, D4): ordinary code changes merged (GitLab and GitHub together; bots, docs, reverts, backports and releases excluded), the last 6 complete weeks then the last 12 complete months; the first month is partial.",
          [("Merged", lambda k: f"=INDEX(INDEX(d_merged,0,2),ROWS(d_merged)-6+{k+1})",
            lambda st, rr: f'=COUNTIFS(cc_counted,1,cc_state,"merged",cc_class,"normal",cc_merged_at,">="&{st},cc_merged_at,"<"&EDATE(DATE(YEAR({st}),MONTH({st}),1),1))')])
    six12("d_review612", "d_review612 (6/12, D5): median hours to first review of merged ordinary changes, the last 6 complete weeks then the last 12 complete months; the first month is partial.",
          [("Median hours", lambda k: f"=INDEX(INDEX(d_first_review,0,2),ROWS(d_first_review)-6+{k+1})",
            lambda st, rr: f'=IFERROR(MEDIAN(FILTER(cc_hours_to_first_review,cc_counted=1,cc_state="merged",cc_class="normal",cc_merged_at>={st},cc_merged_at<EDATE(DATE(YEAR({st}),MONTH({st}),1),1),cc_hours_to_first_review<>"")),"")')], rnd=1)
    G.title("d_state612 (prototype): SBU work items in progress with no owner, measured at the end of each of the last 6 complete weeks and 12 complete months (from State_History, which replays the changelog). The as-of value must equal the Dashboard alert 1.")
    s0 = G.row
    for j, h in enumerate(["label", "No owner, end of week", "No owner, end of month"]):
        G.put(s0, j, h)
    for k in range(6):
        rr = s0 + 1 + k
        G.put(rr, 0, f'="Week of "&TEXT(INDEX(INDEX(d_created_done,0,1),ROWS(d_created_done)-6+{k+1}),"mmm d")')
        G.put(rr, 1, f'=SUMIFS(sh_in_progress_no_owner,sh_level,"SBU",sh_kind,"week",sh_snapshot_at,INDEX(INDEX(d_created_done,0,1),ROWS(d_created_done)-6+{k+1})+7)')
    for k in range(12):
        rr = s0 + 8 + k
        st = f"EDATE(DATE(YEAR(asof),MONTH(asof),1),{k-12})"
        G.put(rr, 0, f'=TEXT({st},"mmm yyyy")')
        G.put(rr, 2, f'=SUMIFS(sh_in_progress_no_owner,sh_level,"SBU",sh_kind,"month",sh_snapshot_at,EDATE(DATE(YEAR({st}),MONTH({st}),1),1))')
    G.name_range("d_state612", s0, 0, s0 + 19, 2)
    G.row = s0 + 22

    # ---------------------------------------------------------------- 6/12 long block for canvas_source (D90): SBU, Group, Team x 7 metrics x 6 weeks and 12 months. No person rows.
    M612 = ["created", "finished", "merged", "median_first_review_hours", "in_progress_no_owner", "stuck", "wip"]
    G.title("m_612_periods: the 18 periods of the 6/12 views: the last 6 complete weeks, then the last 12 complete months (end is exclusive; the first month is partial because the data window starts mid-month).")
    p0 = G.row
    for j, h in enumerate(["period_type", "period_label", "period_start", "period_end"]):
        G.put(p0, j, h)
    for k in range(6):
        rr = p0 + 1 + k
        G.put(rr, 0, "week")
        G.put(rr, 2, f"=INDEX(INDEX(d_created_done,0,1),ROWS(d_created_done)-6+{k+1})")
        G.put(rr, 1, f'="Week of "&TEXT(C{rr+1},"mmm d")')
        G.put(rr, 3, f"=C{rr+1}+7")
    for k in range(12):
        rr = p0 + 7 + k
        G.put(rr, 0, "month")
        if k == 0:      # W1: the first month starts at the window start (as-of minus 12 months, time of day kept), so it is partial and says so
            G.put(rr, 2, "=EDATE(asof,-12)+MOD(asof,1)")
            G.put(rr, 1, f'=TEXT(C{rr+1},"mmm yyyy")&" (from "&TEXT(C{rr+1},"d mmm")&")"')
            G.put(rr, 3, f"=DATE(YEAR(C{rr+1}),MONTH(C{rr+1})+1,1)")
        else:
            G.put(rr, 2, f"=EDATE(DATE(YEAR(asof),MONTH(asof),1),{k-12})")
            G.put(rr, 1, f'=TEXT(C{rr+1},"mmm yyyy")')
            G.put(rr, 3, f"=EDATE(C{rr+1},1)")
    G.name_range("m_612_periods", p0, 0, p0 + 18, 3)
    G.row = p0 + 21
    G.title("m_612_long: long form for the Explore canvas. One row per level entry (SBU, Group, Team), metric and period: level, group, team, name, metric, period_type, period_label, period_start, period_end (exclusive), value. created = work items created; finished = main series; merged = ordinary changes merged; median_first_review_hours = of those merged in the period; in_progress_no_owner, stuck (older than the Group's 85th-percentile cycle time) and wip are the state at the END of the period (State_History). Each item is attributed to the Group and Team its owner had at the end of the period (dated roster history).")
    l0 = G.row
    for j, h in enumerate(["level", "group", "team", "name", "metric", "period_type", "period_label", "period_start", "period_end", "value"]):
        G.put(l0, j, h)
    sh_col = {"in_progress_no_owner": "sh_in_progress_no_owner", "stuck": "sh_in_progress_stuck", "wip": "sh_in_progress"}
    base_row = {}
    rr = l0 + 1
    for (lv_, g_, t_) in LV:
        for m_ in M612:
            base_row[(lv_, g_, t_, m_)] = rr + 1
            for pi in range(18):
                prow = p0 + 2 + pi
                G.put(rr, 0, lv_); G.put(rr, 1, g_); G.put(rr, 2, t_)
                G.put(rr, 3, "SBU" if lv_ == "SBU" else (g_ if lv_ == "Group" else t_))
                G.put(rr, 4, m_)
                G.put(rr, 5, f"=$A${prow}"); G.put(rr, 6, f"=$B${prow}"); G.put(rr, 7, f"=$C${prow}"); G.put(rr, 8, f"=$D${prow}")
                g, t, st_, en_, R_ = f"$B{rr+1}", f"$C{rr+1}", f"$H{rr+1}", f"$I{rr+1}", rr + 1
                if m_ == "created":
                    f = f'=COUNTIFS(ji_group_c,{g},ji_team_c,{t},ji_ours_c,1,ji_is_work_item,1,ji_created,">="&{st_},ji_created,"<"&{en_})'
                elif m_ == "finished":
                    f = f'=COUNTIFS(ji_group,{g},ji_team,{t},ji_series,"main",ji_final_done,">="&{st_},ji_final_done,"<"&{en_})'
                elif m_ == "merged":
                    f = f'=COUNTIFS(cc_group,{g},cc_team,{t},cc_counted,1,cc_state,"merged",cc_class,"normal",cc_merged_at,">="&{st_},cc_merged_at,"<"&{en_})'
                elif m_ == "median_first_review_hours":
                    f = (f'=IFERROR(MEDIAN(FILTER(cc_hours_to_first_review,(({g}="*")+(cc_group={g})>0)*(({t}="*")+(cc_team={t})>0)>0,cc_counted=1,cc_state="merged",'
                         f'cc_class="normal",cc_merged_at>={st_},cc_merged_at<{en_},cc_hours_to_first_review<>"")),"")')
                else:
                    f = f"=SUMIFS({sh_col[m_]},sh_level,$A{R_},sh_group,{g},sh_team,{t},sh_snapshot_at,{en_})"
                G.put(rr, 9, f)
                rr += 1
    G.name_range("m_612_long", l0, 0, rr - 1, 9)
    G.row = rr + 2
    G.title("m_612_stats: one row per level entry and metric for the stat strip: last week, week over week (percent), average of the 4 weeks before last week, last month, month over month (percent), and the 12-month figure (sum for counts; average of the 12 month-ends for in_progress_no_owner, stuck and wip; median of all merged ordinary changes in the 12 months for median_first_review_hours). Each cell is a formula over m_612_long.")
    s0 = G.row
    for j, h in enumerate(["level", "group", "team", "name", "metric", "last_week", "wow_pct", "avg_4w_before", "last_month", "mom_pct", "total_12m", "total_12m_basis"]):
        G.put(s0, j, h)
    rr = s0 + 1
    for (lv_, g_, t_) in LV:
        for m_ in M612:
            b = base_row[(lv_, g_, t_, m_)]
            G.put(rr, 0, lv_); G.put(rr, 1, g_); G.put(rr, 2, t_); G.put(rr, 3, f"=D{b}"); G.put(rr, 4, m_)
            G.put(rr, 5, f"=J{b+5}")
            G.put(rr, 6, f'=IF(AND(ISNUMBER(J{b+5}),ISNUMBER(J{b+4})),IFERROR(ROUND(100*(J{b+5}/J{b+4}-1),1),""),"")')
            if m_ == "median_first_review_hours":     # D91: the 4-week figure is the median over the individual changes, not the average of weekly medians
                g4, t4 = f"$B{rr+1}", f"$C{rr+1}"
                G.put(rr, 7, (f'=IFERROR(MEDIAN(FILTER(cc_hours_to_first_review,(({g4}="*")+(cc_group={g4})>0)*(({t4}="*")+(cc_team={t4})>0)>0,cc_counted=1,cc_state="merged",cc_class="normal",'
                              f'cc_merged_at>=$C${p0+3},cc_merged_at<$D${p0+6},cc_hours_to_first_review<>"")),"")'))
            else:
                G.put(rr, 7, f"=IFERROR(AVERAGE(J{b+1}:J{b+4}),\"\")")
            G.put(rr, 8, f"=J{b+17}")
            G.put(rr, 9, f'=IF(AND(ISNUMBER(J{b+17}),ISNUMBER(J{b+16})),IFERROR(ROUND(100*(J{b+17}/J{b+16}-1),1),""),"")')
            if m_ in ("created", "finished", "merged"):
                G.put(rr, 10, f"=SUM(J{b+6}:J{b+17})"); G.put(rr, 11, "sum of the 12 months")
            elif m_ == "median_first_review_hours":
                g, t = f"$B{rr+1}", f"$C{rr+1}"
                G.put(rr, 10, (f'=IFERROR(MEDIAN(FILTER(cc_hours_to_first_review,(({g}="*")+(cc_group={g})>0)*(({t}="*")+(cc_team={t})>0)>0,cc_counted=1,cc_state="merged",cc_class="normal",'
                               f'cc_merged_at>=$C${p0+8},cc_merged_at<$D${p0+19},cc_hours_to_first_review<>"")),"")'))
                G.put(rr, 11, "median over all merged ordinary changes in the 12 months; avg_4w_before is also the median over the changes of the 4 weeks before last week; wow_pct and mom_pct are blank when a period has no reviews")
            else:
                G.put(rr, 10, f"=IFERROR(AVERAGE(J{b+6}:J{b+17}),\"\")"); G.put(rr, 11, "average of the 12 month-ends")
            rr += 1
    G.name_range("m_612_stats", s0, 0, rr - 1, 11)
    G.row = rr + 2

    # ---------------------------------------------------------------- B1, B2, T1 (v1.20, AC58 to AC60): bugs, open bug age, tech-debt share
    G.title("d_bugs612 (B1): Bugs (Jira type Bug) created and fixed per period, SBU: the last 6 complete weeks then the last 12 complete months. created = Bugs created in the period; fixed = Bugs whose final Done falls in the period, main series only (Won't Do and Duplicate excluded, as D1); net = fixed minus created. Periods come from m_612_periods; the first month is partial.")
    b0 = G.row
    for j, h in enumerate(["period_type", "period_label", "period_start", "created", "fixed", "net"]):
        G.put(b0, j, h)
    for i in range(18):
        rr = b0 + 1 + i
        prow = p0 + 2 + i
        G.put(rr, 0, f"=$A${prow}"); G.put(rr, 1, f"=$B${prow}"); G.put(rr, 2, f"=$C${prow}")
        G.put(rr, 3, f'=COUNTIFS(ji_type,"Bug",ji_ours_c,1,ji_created,">="&$C{rr+1},ji_created,"<"&$D${prow})')
        G.put(rr, 4, f'=COUNTIFS(ji_type,"Bug",ji_series,"main",ji_final_done,">="&$C{rr+1},ji_final_done,"<"&$D${prow})')
        G.put(rr, 5, f"=E{rr+1}-D{rr+1}")
    G.name_range("d_bugs612", b0, 0, b0 + 18, 5)
    G.row = b0 + 21
    bidx = lambda col, mexpr: f"=INDEX(INDEX(d_bugs612,0,{col}),{mexpr})"
    six12("d_bugs612_chart", "d_bugs612_chart (B1 chart range): the same values as d_bugs612 laid out for the 6/12 line chart (weekly columns, a blank gap row, monthly columns, a zero line, and label columns for the thinned data labels).",
          [("Created", lambda k: bidx(4, k + 2), lambda st, rr: bidx(4, f"MATCH({st},INDEX(d_bugs612,0,3),0)")),
           ("Fixed", lambda k: bidx(5, k + 2), lambda st, rr: bidx(5, f"MATCH({st},INDEX(d_bugs612,0,3),0)")),
           ("Net", lambda k: bidx(6, k + 2), lambda st, rr: bidx(6, f"MATCH({st},INDEX(d_bugs612,0,3),0)"))], zero=True)
    # B2: open bug age by level, and by priority
    G.title("d_bugage (B2): open Bugs at the as-of (status category not done) by level: SBU, each Group, each Team. age = as-of minus created, in days. Team rows with fewer than t_min_n open Bugs show counts only ('n under 10'). Columns G and H hold the level criteria used by the formulas on the row.")
    a0b = G.row
    for j, h in enumerate(["level", "name", "open", "median_age_days", "p85_age_days", "over_90", "group", "team"]):
        G.put(a0b, j, h)
    for i, (lv_, g_, t_) in enumerate(LV):
        rr = a0b + 1 + i
        R_ = rr + 1
        G.put(rr, 0, lv_); G.put(rr, 1, "SBU" if lv_ == "SBU" else (g_ if lv_ == "Group" else t_)); G.put(rr, 6, g_); G.put(rr, 7, t_)
        g, t = f"$G{R_}", f"$H{R_}"
        crit = f'(({g}="*")+(ji_group={g})>0)*(({t}="*")+(ji_team={t})>0)>0,ji_type="Bug",ji_status_category<>"done"'
        G.put(rr, 2, f'=COUNTIFS(ji_group,{g},ji_team,{t},ji_type,"Bug",ji_status_category,"<>done")')
        small = f'AND($A{R_}="Team",$C{R_}<t_min_n)'
        G.put(rr, 3, f'=IF({small},"n under "&t_min_n,IFERROR(MEDIAN(FILTER(ji_age_days,{crit})),""))')
        G.put(rr, 4, f'=IF({small},"n under "&t_min_n,IFERROR(PERCENTILE.INC(FILTER(ji_age_days,{crit}),0.85),""))')
        G.put(rr, 5, f'=COUNTIFS(ji_group,{g},ji_team,{t},ji_type,"Bug",ji_status_category,"<>done",ji_age_days,">90")')
    G.name_range("d_bugage", a0b, 0, a0b + len(LV), 5)
    G.row = a0b + len(LV) + 3
    G.title("d_bugage_prio (B2): open Bugs at the as-of by Jira priority (SBU): priority, open, median_age_days, over_90.")
    q0 = G.row
    for j, h in enumerate(["priority", "open", "median_age_days", "over_90"]):
        G.put(q0, j, h)
    prios = meta.get("bug_priorities", [])
    for i, pr in enumerate(prios):
        rr = q0 + 1 + i
        G.put(rr, 0, pr)
        G.put(rr, 1, f'=COUNTIFS(ji_type,"Bug",ji_status_category,"<>done",ji_priority,$A{rr+1})')
        G.put(rr, 2, f'=IFERROR(MEDIAN(FILTER(ji_age_days,ji_type="Bug",ji_status_category<>"done",ji_priority=$A{rr+1})),"")')
        G.put(rr, 3, f'=COUNTIFS(ji_type,"Bug",ji_status_category,"<>done",ji_priority,$A{rr+1},ji_age_days,">90")')
    G.name_range("d_bugage_prio", q0, 0, q0 + len(prios), 3)
    G.row = q0 + len(prios) + 3
    ents = [(lv_, g_, t_) for (lv_, g_, t_) in LV if lv_ in ("SBU", "Group")]          # SBU and each Group (the M1 and stalled blocks)
    ne = len(ents)
    # v1.43c AC76 (M1, replaces T1): work mix by Work Category, SBU and each Group, last 6 complete weeks then 12 complete months (same 18-row shape as the other 6/12 blocks)
    G.title("d_workmix612 (M1 work mix): tickets finished in the period (main series) by Work Category (the epic's value at the finish date), SBU and each Group, last 6 complete weeks then 12 complete months. finished = all finished tickets; customer, internal, ops, support = per category; none = No category; *_pct = the category's share of (finished minus none), one decimal, blank when no finished ticket has a category; none_pct = none / finished; features_pct = customer + internal. Limits: t_cat_support_max, t_cat_ops_max, t_cat_features_min.")
    w0 = G.row
    WMH = ["period_type", "period_label", "period_start", "level", "name", "finished", "customer", "internal", "ops", "support", "none", "customer_pct", "internal_pct", "ops_pct", "support_pct", "features_pct", "none_pct", "group", "team"]
    for j, h in enumerate(WMH):
        G.put(w0, j, h)
    for ei, (lv_, g_, t_) in enumerate(ents):
        for i in range(18):
            rr = w0 + 1 + ei * 18 + i
            R_ = rr + 1
            prow = p0 + 2 + i
            G.put(rr, 0, f"=$A${prow}"); G.put(rr, 1, f"=$B${prow}"); G.put(rr, 2, f"=$C${prow}")
            G.put(rr, 3, lv_); G.put(rr, 4, "SBU" if lv_ == "SBU" else g_); G.put(rr, 17, g_); G.put(rr, 18, t_)
            base = f'ji_group,$R{R_},ji_team,$S{R_},ji_series,"main",ji_final_done,">="&$C{R_},ji_final_done,"<"&$D${prow}'
            G.put(rr, 5, f"=COUNTIFS({base})")
            for k_, cat in enumerate(("Customer Feature", "Internal Feature", "Ops & Maintenance", "Support")):
                G.put(rr, 6 + k_, f'=COUNTIFS(ji_work_category,"{cat}",{base})')
            G.put(rr, 10, f"=F{R_}-G{R_}-H{R_}-I{R_}-J{R_}")
            den = f"(G{R_}+H{R_}+I{R_}+J{R_})"
            for k_, c_ in enumerate("GHIJ"):
                G.put(rr, 11 + k_, f'=IF({den}=0,"",ROUND(100*{c_}{R_}/{den},1))')
            G.put(rr, 15, f'=IF({den}=0,"",ROUND(100*(G{R_}+H{R_})/{den},1))')
            G.put(rr, 16, f'=IF(F{R_}=0,"",ROUND(100*K{R_}/F{R_},1))')
    G.name_range("d_workmix612", w0, 0, w0 + 18 * ne, len(WMH) - 1)
    G.row = w0 + 18 * ne + 3
    G.title("d_workmix_yr (M1 12-month shares and Status): per row (SBU and each Group): finished tickets over the last 12 complete months, each category's share of the categorised ones, No category / finished, and Status = Needs attention when Support is above t_cat_support_max, Ops & Maintenance above t_cat_ops_max or features below t_cat_features_min.")
    y0 = G.row
    for j, h in enumerate(["level", "name", "finished", "customer", "internal", "ops", "support", "none", "customer_pct", "internal_pct", "ops_pct", "support_pct", "features_pct", "none_pct", "status"]):
        G.put(y0, j, h)
    for ei, (lv_, g_, t_) in enumerate(ents):
        rr = y0 + 1 + ei
        R_ = rr + 1
        G.put(rr, 0, lv_); G.put(rr, 1, "SBU" if lv_ == "SBU" else g_)
        lo, hi = w0 + 1 + ei * 18 + 6 + 1, w0 + 1 + ei * 18 + 17 + 1          # sheet rows of this entity's 12 monthly rows
        for k_, col in enumerate("FGHIJK"):
            G.put(rr, 2 + k_, f"=SUM({col}{lo}:{col}{hi})")
        den = f"(D{R_}+E{R_}+F{R_}+G{R_})"
        for k_, c_ in enumerate("DEFG"):
            G.put(rr, 8 + k_, f'=IF({den}=0,"",ROUND(100*{c_}{R_}/{den},1))')
        G.put(rr, 12, f'=IF({den}=0,"",ROUND(100*(D{R_}+E{R_})/{den},1))')
        G.put(rr, 13, f'=IF(C{R_}=0,"",ROUND(100*H{R_}/C{R_},1))')
        G.put(rr, 14, f'=IF(M{R_}="","n/a",IF(OR(L{R_}>t_cat_support_max,K{R_}>t_cat_ops_max,M{R_}<t_cat_features_min),"Needs attention","OK"))')
    G.name_range("d_workmix_yr", y0, 0, y0 + ne, 14)
    G.row = y0 + ne + 3
    G.title("d_workmix612_chart (M1 chart range): SBU share (percent) of Customer Feature, Internal Feature, Ops & Maintenance, Support and the No category line for the 6/12 line chart: label, five weekly columns, five monthly columns (blank gap row between the weeks and the months).")
    c0 = G.row
    cats = ["Customer Feature", "Internal Feature", "Ops & Maintenance", "Support", "No category"]
    for j, h in enumerate(["label"] + [f"{c} per week" for c in cats] + [f"{c} per month" for c in cats]):
        G.put(c0, j, h)
    for k in range(18):
        rr = c0 + 1 + (k if k < 6 else k + 1)
        src = w0 + 2 + k
        G.put(rr, 0, f'="Wk "&TEXT(C{src},"mmm d")' if k < 6 else f"=B{src}")
        for ci_, sc in enumerate(["L", "M", "N", "O", "Q"]):          # customer_pct, internal_pct, ops_pct, support_pct, none_pct of the SBU rows (the first 18)
            G.put(rr, (1 + ci_) if k < 6 else (6 + ci_), f"={sc}{src}")
    G.name_range("d_workmix612_chart", c0, 0, c0 + 19, 10)
    G.row = c0 + 22

    # v1.43: stalled epics and initiatives (open ones with no update under them for t_epic_stalled_days / t_init_stalled_days); epics and initiatives are never lumped
    G.title("d_stalled (epics and initiatives): SBU and each Group. open_epics; stalled_epics (open epics with no update, in Jira updated, under their open child tickets for more than t_epic_stalled_days; with no child tickets, open longer than that); epics_all_done (open epics whose child tickets are all done); open_initiatives; stalled_initiatives (t_init_stalled_days, tickets under any child epic). Counted from ji_stalled_days and ji_kids_done (blank for anything that is not an open epic or initiative). Epics and initiatives are never counted together.")
    s0 = G.row
    for j, h in enumerate(["level", "name", "open_epics", "stalled_epics", "epics_all_done", "open_initiatives", "stalled_initiatives", "group", "team"]):
        G.put(s0, j, h)
    for ei, (lv_, g_, t_) in enumerate(ents):
        rr = s0 + 1 + ei
        R_ = rr + 1
        G.put(rr, 0, lv_); G.put(rr, 1, "SBU" if lv_ == "SBU" else g_); G.put(rr, 7, g_); G.put(rr, 8, t_)
        base = f'ji_group,$H{R_},ji_team,$I{R_}'
        G.put(rr, 2, f'=COUNTIFS(ji_type,"Epic",ji_stalled_days,">=0",{base})+COUNTIFS(ji_type,"Epic",ji_kids_done,1,{base})')
        G.put(rr, 3, f'=COUNTIFS(ji_type,"Epic",ji_stalled_days,">"&t_epic_stalled_days,{base})')
        G.put(rr, 4, f'=COUNTIFS(ji_type,"Epic",ji_kids_done,1,{base})')
        G.put(rr, 5, f'=COUNTIFS(ji_type,"Initiative",ji_stalled_days,">=0",{base})+COUNTIFS(ji_type,"Initiative",ji_kids_done,1,{base})')
        G.put(rr, 6, f'=COUNTIFS(ji_type,"Initiative",ji_stalled_days,">"&t_init_stalled_days,{base})')
    G.name_range("d_stalled", s0, 0, s0 + ne, 8)
    G.row = s0 + ne + 3
    wm_dk = []
    for nm_c, col, lab in (("customer", 9, "Customer Feature"), ("internal", 10, "Internal Feature"), ("ops", 11, "Ops & Maintenance"), ("support", 12, "Support"), ("feature", 13, "features"), ("none", 14, "No category")):
        wm_dk.append((f"dk_m1_{nm_c}_yr", f"=INDEX(INDEX(d_workmix_yr,0,{col}),2)", "0.0", f"M1 work mix: SBU share of finished tickets (with a category) that are {lab}, last 12 complete months (percent)" if nm_c != "none" else "M1 work mix: SBU share of finished tickets with No category, last 12 complete months (percent of all finished)"))
    wm_dk += [("dk_m1_support_wk", "=INDEX(INDEX(d_workmix612,0,15),7)", "0.0", "M1: SBU Support share in the last complete week (percent)"), ("dk_m1_ops_wk", "=INDEX(INDEX(d_workmix612,0,14),7)", "0.0", "M1: SBU Ops & Maintenance share in the last complete week (percent)"),
              ("dk_m1_feature_wk", "=INDEX(INDEX(d_workmix612,0,16),7)", "0.0", "M1: SBU features share in the last complete week (percent)"), ("dk_m1_finished_yr", "=INDEX(INDEX(d_workmix_yr,0,3),2)", "#,##0", "M1: finished tickets over the last 12 complete months, SBU"),
              ("dk_m1_break", '=IF(INDEX(INDEX(d_workmix_yr,0,15),2)="Needs attention",1,0)', "0", "M1: 1 when the SBU row breaks a work-mix limit (12 months)")]
    wm_dk += [("dk_stalled_epics", "=INDEX(INDEX(d_stalled,0,4),2)", "#,##0", "Stalled epics: open epics with no update under them for more than t_epic_stalled_days, SBU"),
              ("dk_epics_all_done", "=INDEX(INDEX(d_stalled,0,5),2)", "#,##0", "Open epics whose child tickets are all done, SBU"),
              ("dk_open_epics", "=INDEX(INDEX(d_stalled,0,3),2)", "#,##0", "Open epics, SBU (the base of the stalled-epic count)"),
              ("dk_stalled_inits", "=INDEX(INDEX(d_stalled,0,7),2)", "#,##0", "Stalled initiatives: open initiatives with no update under them for more than t_init_stalled_days, SBU"),
              ("dk_open_inits", "=INDEX(INDEX(d_stalled,0,6),2)", "#,##0", "Open initiatives, SBU (the base of the stalled-initiative count)")]

    inc_dk = []
    if meta.get("incidents_enabled", True):        # config incidents=false leaves the incident ranges out (Part 1 of the real apply)
        # ---------------------------------------------------------------- I1 to I4 (v1.21, AC61 to AC65): incidents, counts only
        splits = ["customer", "internal"]
        G.title("d_inc612 (I1): incidents (Jira projects EA = customer, IA = internal; any issue type) per period and split: the last 6 complete weeks then the last 12 complete months (18 rows per split). created = incidents created in the period; resolved = incidents whose final Done falls in the period, any resolution; resolved_wontdo_dup = of those, resolution Won't Do or Duplicate (shown, not dropped); net = resolved minus created. Source: Incident_Issues (counts only), measured at the Sheet's as-of; the first month is partial.")
        i0 = G.row
        for j, h in enumerate(["period_type", "period_label", "period_start", "split", "created", "resolved", "resolved_wontdo_dup", "net"]):
            G.put(i0, j, h)
        for si, sp in enumerate(splits):
            for i in range(18):
                rr = i0 + 1 + si * 18 + i
                R_, prow = rr + 1, p0 + 2 + i
                G.put(rr, 0, f"=$A${prow}"); G.put(rr, 1, f"=$B${prow}"); G.put(rr, 2, f"=$C${prow}"); G.put(rr, 3, sp)
                G.put(rr, 4, f'=COUNTIFS(ii_split,$D{R_},ii_ours_c,1,ii_created,">="&$C{R_},ii_created,"<"&$D${prow})')
                G.put(rr, 5, f'=COUNTIFS(ii_split,$D{R_},ii_final_done,">="&$C{R_},ii_final_done,"<"&$D${prow})')
                G.put(rr, 6, f'=COUNTIFS(ii_split,$D{R_},ii_final_done,">="&$C{R_},ii_final_done,"<"&$D${prow},ii_wontdo_dup,1)')
                G.put(rr, 7, f"=F{R_}-E{R_}")
        G.name_range("d_inc612", i0, 0, i0 + 36, 7)
        G.row = i0 + 39

        def inc_idx(col, off, expr):
            return f"=INDEX(INDEX(d_inc612,0,{col}),{expr})"

        for si, sp in enumerate(splits):
            off = 2 + si * 18
            mon = lambda col, off=off: (lambda st, rr: f"=INDEX(INDEX(d_inc612,0,{col}),MATCH({st},INDEX(INDEX(d_inc612,0,3),{off}):INDEX(INDEX(d_inc612,0,3),{off + 17}),0)+{off - 1})")
            wk = lambda col, off=off: (lambda k: f"=INDEX(INDEX(d_inc612,0,{col}),{off + k})")
            six12(f"d_inc612_chart_{sp}", f"d_inc612_chart_{sp} (I1 chart range, {sp}): the same values as d_inc612 for the 6/12 line chart (weekly columns, a blank gap row, monthly columns, a zero line, label columns).",
                  [("Created", wk(5), mon(5)), ("Resolved", wk(6), mon(6)), ("Net", wk(8), mon(8))], zero=True)
        # I2: open incidents at the as-of by split and priority (SBU level)
        iprios = meta.get("inc_priorities", [])
        G.title("d_incopen (I2): incidents open at the as-of (not resolved) by split and priority, SBU level (EA and IA are projects, no Group split): open, median_age_days, p85_age_days, over_30 (older than 30 days); age = as-of minus created. 'All' is the split total. Column G holds the priority criterion used by the formulas on the row.")
        o0 = G.row
        for j, h in enumerate(["split", "priority", "open", "median_age_days", "p85_age_days", "over_30", "priority_criterion"]):
            G.put(o0, j, h)
        rr = o0 + 1
        open_row = {}
        for sp in splits:
            for pr in ["All"] + iprios:
                R_ = rr + 1
                open_row[(sp, pr)] = R_ - o0
                G.put(rr, 0, sp); G.put(rr, 1, pr); G.put(rr, 6, "*" if pr == "All" else pr)
                crit = f'ii_split=$A{R_},(($G{R_}="*")+(ii_priority=$G{R_})>0),ii_open_at_asof=1'
                G.put(rr, 2, f'=COUNTIFS(ii_split,$A{R_},ii_priority,$G{R_},ii_open_at_asof,1)')
                G.put(rr, 3, f'=IFERROR(MEDIAN(FILTER(ii_age_days,{crit})),"")')
                G.put(rr, 4, f'=IFERROR(PERCENTILE.INC(FILTER(ii_age_days,{crit}),0.85),"")')
                G.put(rr, 5, f'=COUNTIFS(ii_split,$A{R_},ii_priority,$G{R_},ii_open_at_asof,1,ii_age_days,">"&t_incident_open_days)')
                rr += 1
        G.name_range("d_incopen", o0, 0, rr - 1, 5)
        G.row = rr + 3
        # I3: time to resolve per month
        G.title("d_incttr (I3): time to resolve (final Done minus created, in days) for incidents resolved in each of the last 12 complete months, per split: month, split, resolved, median_days, p85_days; blank when no incident was resolved that month.")
        r0t = G.row
        for j, h in enumerate(["month", "split", "resolved", "median_days", "p85_days"]):
            G.put(r0t, j, h)
        for si, sp in enumerate(splits):
            for m in range(12):
                rr = r0t + 1 + si * 12 + m
                R_, prow = rr + 1, p0 + 8 + m
                G.put(rr, 0, f"=$B${prow}"); G.put(rr, 1, sp)
                rng_ = f'ii_split,$B{R_},ii_final_done,">="&$C${prow},ii_final_done,"<"&$D${prow}'
                G.put(rr, 2, f"=COUNTIFS({rng_})")
                G.put(rr, 3, f'=IFERROR(MEDIAN(FILTER(ii_ttr_days,ii_split=$B{R_},ii_final_done>=$C${prow},ii_final_done<$D${prow})),"")')
                G.put(rr, 4, f'=IFERROR(PERCENTILE.INC(FILTER(ii_ttr_days,ii_split=$B{R_},ii_final_done>=$C${prow},ii_final_done<$D${prow}),0.85),"")')
        G.name_range("d_incttr", r0t, 0, r0t + 24, 4)
        G.row = r0t + 27
        G.title("d_incttr_chart (I3 chart range): the same values as d_incttr for the line chart: month, then median and P85 days for customer and internal incidents.")
        c0t = G.row
        for j, h in enumerate(["month", "Customer median days", "Customer P85 days", "Internal median days", "Internal P85 days"]):
            G.put(c0t, j, h)
        for m in range(12):
            rr = c0t + 1 + m
            G.put(rr, 0, f"=INDEX(INDEX(d_incttr,0,1),{2 + m})")
            for j, (si, col) in enumerate(((0, 4), (0, 5), (1, 4), (1, 5))):
                G.put(rr, 1 + j, f'=INDEX(INDEX(d_incttr,0,{col}),{2 + si * 12 + m})')
        G.name_range("d_incttr_chart", c0t, 0, c0t + 12, 4)
        G.row = c0t + 15
        # I4: incident types
        G.title("d_inctype (I4): incidents by split and Jira issue type: created_12m and resolved_12m over the last 12 complete months (first month partial) and open_now at the as-of. The types listed are exactly the types present in the incident extract. Counts only.")
        y0 = G.row
        for j, h in enumerate(["split", "type", "created_12m", "resolved_12m", "open_now"]):
            G.put(y0, j, h)
        itypes = meta.get("inc_types", [])
        for i, (sp, ty) in enumerate(itypes):
            rr = y0 + 1 + i
            R_ = rr + 1
            G.put(rr, 0, sp); G.put(rr, 1, ty)
            G.put(rr, 2, f'=COUNTIFS(ii_split,$A{R_},ii_type,$B{R_},ii_ours_c,1,ii_created,">="&$C${p0+8},ii_created,"<"&$D${p0+19})')
            G.put(rr, 3, f'=COUNTIFS(ii_split,$A{R_},ii_type,$B{R_},ii_final_done,">="&$C${p0+8},ii_final_done,"<"&$D${p0+19})')
            G.put(rr, 4, f'=COUNTIFS(ii_split,$A{R_},ii_type,$B{R_},ii_open_at_asof,1)')
        G.name_range("d_inctype", y0, 0, y0 + len(itypes), 4)
        G.row = y0 + len(itypes) + 3

        # answer cells for I1 to I4 (built from the ranges above; each a formula over d_ ranges)
        inc_dk = []
        ixn = lambda n, c, i: f"INDEX(INDEX({n},0,{c}),{i})"
        rgn = lambda n, c, i, j: f"{ixn(n, c, i)}:{ixn(n, c, j)}"
        for code, sp in (("c", "customer"), ("i", "internal")):
            F, pf_, lab = f"d_inc612_chart_{sp}", f"dk_i1{code}", f"I1 {sp}"
            inc_dk += [
                (f"{pf_}_wk_res", "=" + ixn(F, 3, 7), "0", f"{lab}: incidents resolved in the last complete week"),
                (f"{pf_}_wk_created", "=" + ixn(F, 2, 7), "0", f"{lab}: incidents created in the last complete week"),
                (f"{pf_}_wk_net", "=" + ixn(F, 4, 7), "+0;-0;0", f"{lab}: net (resolved minus created) for the last complete week"),
                (f"{pf_}_wk_wow", "=" + ixn(F, 3, 7) + "-" + ixn(F, 3, 6), "+0;-0;0", f"{lab}: resolved, change on the week before"),
                (f"{pf_}_wk_avg4", "=AVERAGE(" + rgn(F, 3, 3, 6) + ")", "0.0", f"{lab}: resolved, average of the 4 complete weeks before last week (last week excluded)"),
                (f"{pf_}_wk_dir", f'=IF({pf_}_wk_net>=0,"catching up","falling behind")', "@", f"{lab}: last week, resolved at least as many as created"),
                (f"{pf_}_neg_run", neg_run(F, 4), "0", f"{lab}: weeks in a row, counting back from last week, with net (resolved minus created) below zero"),
                (f"{pf_}_mo_res", "=" + ixn(F, 6, 20), "0", f"{lab}: incidents resolved in the last complete month"),
                (f"{pf_}_mo_created", "=" + ixn(F, 5, 20), "0", f"{lab}: incidents created in the last complete month"),
                (f"{pf_}_mo_net", "=" + ixn(F, 7, 20), "+0;-0;0", f"{lab}: net for the last complete month"),
                (f"{pf_}_mo_mom", "=" + ixn(F, 6, 20) + "-" + ixn(F, 6, 19), "+0;-0;0", f"{lab}: resolved, change on the month before"),
                (f"{pf_}_mo_dir", f'=IF({pf_}_mo_net>=0,"catching up","falling behind")', "@", f"{lab}: last month, resolved at least as many as created"),
                (f"{pf_}_yr_res", "=SUM(" + rgn(F, 6, 9, 20) + ")", "#,##0", f"{lab}: incidents resolved over the 12 months (first month partial)"),
                (f"{pf_}_yr_created", "=SUM(" + rgn(F, 5, 9, 20) + ")", "#,##0", f"{lab}: incidents created over the 12 months (first month partial)"),
                (f"{pf_}_yr_wd", f'=SUMIFS(INDEX(d_inc612,0,7),INDEX(d_inc612,0,4),"{sp}",INDEX(d_inc612,0,1),"month")', "#,##0", f"{lab}: of those resolved over the 12 months, Won't Do or Duplicate"),
            ]
            ar = open_row[(sp, "All")]                           # row index of the split total inside d_incopen (header is row 1)
            inc_dk += [
                (f"dk_i2{code}_open", "=" + ixn("d_incopen", 3, ar), "#,##0", f"I2 {sp}: incidents open at the as-of"),
                (f"dk_i2{code}_median", "=" + ixn("d_incopen", 4, ar), "0", f"I2 {sp}: median age in days of the open incidents"),
                (f"dk_i2{code}_p85", "=" + ixn("d_incopen", 5, ar), "0", f"I2 {sp}: 85th-percentile age in days of the open incidents"),
                (f"dk_i2{code}_over30", "=" + ixn("d_incopen", 6, ar), "#,##0", f"I2 {sp}: open incidents older than 30 days"),
                (f"dk_i2{code}_over_limit", f'=COUNTIFS(ii_split,"{sp}",ii_open_at_asof,1,ii_age_days,">"&t_incident_open_days)', "#,##0", f"I2 {sp}: open incidents older than the limit (t_incident_open_days on the Thresholds tab)"),
            ]
            last = 2 + (12 if sp == "customer" else 24) - 1
            inc_dk += [
                (f"dk_i3{code}_res", "=" + ixn("d_incttr", 3, last), "0", f"I3 {sp}: incidents resolved in the last complete month"),
                (f"dk_i3{code}_median", "=" + ixn("d_incttr", 4, last), "0.0", f"I3 {sp}: median days to resolve, last complete month"),
                (f"dk_i3{code}_p85", "=" + ixn("d_incttr", 5, last), "0.0", f"I3 {sp}: 85th-percentile days to resolve, last complete month"),
                (f"dk_i4{code}_created", f'=SUMIFS(INDEX(d_inctype,0,3),INDEX(d_inctype,0,1),"{sp}")', "#,##0", f"I4 {sp}: incidents created over the 12 months"),
                (f"dk_i4{code}_resolved", f'=SUMIFS(INDEX(d_inctype,0,4),INDEX(d_inctype,0,1),"{sp}")', "#,##0", f"I4 {sp}: incidents resolved over the 12 months"),
                (f"dk_i4{code}_open", f'=SUMIFS(INDEX(d_inctype,0,5),INDEX(d_inctype,0,1),"{sp}")', "#,##0", f"I4 {sp}: incidents open now"),
                (f"dk_i4{code}_types", f'=COUNTIFS(INDEX(d_inctype,0,1),"{sp}")', "0", f"I4 {sp}: number of issue types present"),
            ]


    G.title("d_blocked (K1): open work items whose current status is in the blocked status list (Blocked) at the as-of, by Group, then an SBU total row: group, blocked (count), median_blocked_age_days (as-of minus the time the item last entered a blocked status), unassigned (blocked items with no assignee). Counts and ages only; from Jira_Issues (ji_blocked, ji_blocked_age_days).")
    d0 = G.row
    for j, h in enumerate(["group", "blocked", "median_blocked_age_days", "unassigned"]):
        G.put(d0, j, h)
    for k in range(len(groups_all) + 1):
        rr = d0 + 1 + k
        R_ = rr + 1
        if k < len(groups_all):
            G.put(rr, 0, f"=INDEX(INDEX(m_noowner_ip,0,1),{k+2})")
            gc = f",ji_group,$A{R_}"
            G.put(rr, 1, f"=COUNTIFS(ji_blocked,1{gc})")
            G.put(rr, 2, f'=IFERROR(MEDIAN(FILTER(ji_blocked_age_days,ji_blocked=1,ji_group=$A{R_})),"")')
            G.put(rr, 3, f'=COUNTIFS(ji_blocked,1{gc},ji_owner_kind,"ownerless")')
        else:
            G.put(rr, 0, "SBU")
            G.put(rr, 1, "=COUNTIFS(ji_blocked,1)")
            G.put(rr, 2, '=IFERROR(MEDIAN(FILTER(ji_blocked_age_days,ji_blocked=1)),"")')
            G.put(rr, 3, '=COUNTIFS(ji_blocked,1,ji_owner_kind,"ownerless")')
    G.name_range("d_blocked", d0, 0, d0 + len(groups_all) + 1, 3)
    G.row = d0 + len(groups_all) + 3

    # ---------------------------------------------------------------- answer cells: every number an Answer sentence uses is a cell here (AC44a)
    G.title("m_answers: the cells the Answer sentences on the Dashboard cite (and the answer cells of charts that are not drawn). Each is a formula over d_ ranges, m_ ranges, or Metrics cells; the sentences only join them with text.")
    ans = [
        ("dk_added_last", "=INDEX(INDEX(d_created_done,0,2),ROWS(d_created_done))", "0", "Work items added (created) in the last complete week"),
        ("dk_finished_last", "=INDEX(INDEX(d_created_done,0,3),ROWS(d_created_done))", "0", "Work items finished in the last complete week (main series)"),
        ("dk_keeping_up", '=IF(dk_finished_last>=dk_added_last,"keeping up","falling behind")', "@", "Finished at least as many as added"),
        ("dk_noowner_total", "=SUM(INDEX(d_noowner,0,2))", "0", "In-progress items with no owner, all Groups"),
        ("dk_noowner_max", "=MAX(INDEX(d_noowner,0,2))", "0", "Largest Group count of in-progress items with no owner"),
        ("dk_noowner_max_group", "=INDEX(INDEX(d_noowner,0,1),MATCH(dk_noowner_max,INDEX(d_noowner,0,2),0))", "@", "The Group with that count"),
        ("dk_stuck_total", '=COUNTIFS(ji_wip,1,ji_start_age_days,">"&t_stuck_days)', "0", "In-progress items older than t_stuck_days (SBU row: includes SBU-only items)"),
        ("dk_stuck_oldest", '=IFERROR(MAXIFS(ji_start_age_days,ji_wip,1,ji_start_age_days,">"&t_stuck_days),"")', "0", "Age in days of the oldest of them"),
        ("dk_k1_total", "=INDEX(INDEX(d_blocked,0,2),ROWS(d_blocked))", "0", "K1: open work items in a blocked status at the as-of (SBU)"),
        ("dk_k1_median", "=INDEX(INDEX(d_blocked,0,3),ROWS(d_blocked))", "0", "K1: median days since those items entered the blocked status"),
        ("dk_k1_unassigned", "=INDEX(INDEX(d_blocked,0,4),ROWS(d_blocked))", "0", "K1: blocked items with no assignee"),
        ("dk_k1_top", "=MAX(INDEX(INDEX(d_blocked,0,2),2):INDEX(INDEX(d_blocked,0,2),ROWS(d_blocked)-1))", "0", "K1: largest Group count of blocked items"),
        ("dk_k1_top_group", "=INDEX(INDEX(d_blocked,0,1),MATCH(dk_k1_top,INDEX(INDEX(d_blocked,0,2),2):INDEX(INDEX(d_blocked,0,2),ROWS(d_blocked)-1),0)+1)", "@", "K1: the Group with that count"),
        ("dk_k1_over", '=COUNTIFS(ji_blocked,1,ji_blocked_age_days,">"&t_blocked_days)', "0", "K1: blocked items that have been blocked longer than the limit (t_blocked_days)"),
        ("dk_merged_last", "=INDEX(INDEX(d_merged,0,2),ROWS(d_merged))", "0", "Normal changes merged in the last complete week"),
        ("dk_merged_avg4", "=AVERAGE(INDEX(INDEX(d_merged,0,2),ROWS(d_merged)-4):INDEX(INDEX(d_merged,0,2),ROWS(d_merged)-1))", "0", "Average per week of the 4 weeks before"),
        ("dk_merged_change", "=ABS(dk_merged_last/dk_merged_avg4-1)", "0%", "Size of the difference from that average"),
        ("dk_merged_dir", '=IF(dk_merged_last>=dk_merged_avg4,"above","below")', "@", "Above or below that average"),
        ("dk_review_last", "=INDEX(INDEX(d_first_review,0,2),ROWS(d_first_review))", "0.0", "Median hours to first review, last complete week"),
        ("dk_review_limit", "=t_first_review_days*hpd", "0", "First-review limit in hours (threshold in days times 24)"),
        ("dk_a1_sbu", "=INDEX(lv_A1_rate,1)", "0%", "Share of normal changes that name a linked Jira issue, SBU"),
        ("dk_a1_low", "=MIN(INDEX(d_align,0,2))", "0%", "Lowest Group share"),
        ("dk_a1_low_group", "=INDEX(INDEX(d_align,0,1),MATCH(dk_a1_low,INDEX(d_align,0,2),0))", "@", "The Group with the lowest share"),
        ("dk_a4_total", "=SUM(INDEX(d_align,0,3))", "0", "Done code-type items with no merged code, all Groups"),
        ("dk_a4_max", "=MAX(INDEX(d_align,0,3))", "0", "Largest Group count"),
        ("dk_a4_max_group", "=INDEX(INDEX(d_align,0,1),MATCH(dk_a4_max,INDEX(d_align,0,3),0))", "@", "The Group with that count"),
        ("dk_v1_total", "=INDEX(INDEX(m_throughput_chart,0,2),ROWS(m_throughput_chart))", "0", "V1: main-series items finished last week"),
        ("dk_v1_avg4", "=INDEX(INDEX(m_throughput_chart,0,11),ROWS(m_throughput_chart))", "0", "V1: 4-week average"),
        ("dk_v2_created", "=INDEX(INDEX(m_created_done,0,2),ROWS(m_created_done))", "0", "V2: created last week"),
        ("dk_v2_done", "=INDEX(INDEX(m_created_done,0,3),ROWS(m_created_done))", "0", "V2: finished last week (all resolutions)"),
        ("dk_v3_inprog", "=INDEX(INDEX(m_cfd_chart,0,3),ROWS(m_cfd_chart))", "0", "V3: in progress at the last week end"),
        ("dk_v3_open", "=INDEX(INDEX(m_cfd_chart,0,2),ROWS(m_cfd_chart))+dk_v3_inprog", "0", "V3: open work items at the last week end"),
        ("dk_v3_done", "=INDEX(INDEX(m_cfd_chart,0,4),ROWS(m_cfd_chart))", "0", "V3: Done so far in the window"),
        ("dk_v4_median", "=INDEX(INDEX(m_cycle_bins,0,4),2)", "0.0", "V4: median cycle days"),
        ("dk_v4_p85", "=INDEX(INDEX(m_cycle_bins,0,5),2)", "0.0", "V4: P85 cycle days"),
        ("dk_v4_first", "=INDEX(INDEX(m_cycle_bins,0,3),2)", "0", "V4: items in the first bin"),
        ("dk_v5_old", "=INDEX(lv_aging_wip_over_p85,1)", "0", "V5: in-progress items older than their Group's P85"),
        ("dk_v5_wip", "=INDEX(lv_wip,1)", "0", "V5: in-progress items"),
        ("dk_v6_max", "=MAX(INDEX(m_wip,0,3))", "0", "V6: largest in-progress count of one Team row"),
        ("dk_v6_label", "=INDEX(INDEX(m_wip,0,4),MATCH(dk_v6_max,INDEX(m_wip,0,3),0))", "@", "V6: that Team"),
        ("dk_v6_total", "=SUM(INDEX(m_wip,0,3))", "0", "V6: in-progress items in total"),
        ("dk_v7_old", "=INDEX(INDEX(m_backlog_age,0,2),5)", "0", "V7: open items more than a year old"),
        ("dk_v7_total", "=SUM(INDEX(m_backlog_age,0,2))", "0", "V7: open work items"),
        ("dk_v7_share", "=dk_v7_old/dk_v7_total", "0%", "V7: share more than a year old"),
        ("dk_v8_total", "=SUM(INDEX(m_noowner_ip,0,2))", "0", "V8: in progress with no owner"),
        ("dk_v8_oldest", "=MAX(INDEX(m_noowner_ip,0,3))", "0", "V8: longest wait in days"),
        ("dk_v9a_last", "=SUMIFS(INDEX(m_code_week,0,4),INDEX(m_code_week,0,1),wk_last)", "0", "V9a: changes merged last week, all kinds"),
        ("dk_v9b_gitlab", "=INDEX(INDEX(m_code_week_chart,0,14),ROWS(m_code_week_chart))", "0.0", "V9b: GitLab median hours to first review, last week"),
        ("dk_v9b_github", "=INDEX(INDEX(m_code_week_chart,0,15),ROWS(m_code_week_chart))", "0.0", "V9b: GitHub median hours to first review, last week"),
        ("dk_v10_total", "=SUM(INDEX(m_review_team,0,2))", "0", "V10: reviews per week, all Teams"),
        ("dk_v10_max", "=MAX(INDEX(m_review_team,0,2))", "0", "V10: largest Team"),
        ("dk_v10_team", "=INDEX(INDEX(m_review_team,0,1),MATCH(dk_v10_max,INDEX(m_review_team,0,2),0))", "@", "V10: that Team"),
        ("dk_v11_c1", "=INDEX(lv_C1_pass_rate,1)", "0%", "V11: share of normal changes naming a Jira issue (C1)"),
        ("dk_v11_j1", "=INDEX(lv_J1_pass_rate,1)", "0%", "V11: share of in-progress items with an owner (J1)"),
        ("dk_v12_a1", "=INDEX(lv_A1_rate,1)", "0%", "V12: A1 share"),
        ("dk_v12_a4", "=INDEX(lv_A4_count,1)", "0", "V12: A4 count"),
        ("dk_v13_open", "=INDEX(lv_open_normal_changes,1)", "0", "V13: open normal changes"),
        ("dk_v13_oldest", "=INDEX(lv_open_age_max_days,1)", "0", "V13: oldest open change in days"),
        ("dk_net_last", '=INDEX(INDEX(d_created_done,0,4),ROWS(d_created_done))', "+0;-0;0", 'Net for the last complete week: finished minus added'),
        ("dk_p1_wk_fin", '=INDEX(INDEX(d_flow612,0,3),7)', "0", '6/12: finished in the last complete week'),
        ("dk_p1_wk_added", '=INDEX(INDEX(d_flow612,0,2),7)', "0", '6/12: added in the last complete week'),
        ("dk_p1_wk_net", '=INDEX(INDEX(d_flow612,0,4),7)', "+0;-0;0", '6/12: net (finished minus added) for the last complete week'),
        ("dk_p1_wk_wow", '=INDEX(INDEX(d_flow612,0,3),7)-INDEX(INDEX(d_flow612,0,3),6)', "+0;-0;0", '6/12: finished, change on the week before'),
        ("dk_p1_wk_avg4", '=AVERAGE(INDEX(INDEX(d_flow612,0,3),3):INDEX(INDEX(d_flow612,0,3),6))', "0", '6/12: finished, average of the 4 complete weeks before last week (last week excluded)'),
        ("dk_p1_wk_dir", '=IF(dk_p1_wk_net>=0,"keeping up","falling behind")', "@", '6/12: last week, finished at least as many as added'),
        ("dk_p1_mo_fin", '=INDEX(INDEX(d_flow612,0,6),20)', "0", '6/12: finished in the last complete month'),
        ("dk_p1_mo_added", '=INDEX(INDEX(d_flow612,0,5),20)', "0", '6/12: added in the last complete month'),
        ("dk_p1_mo_net", '=INDEX(INDEX(d_flow612,0,7),20)', "+0;-0;0", '6/12: net for the last complete month'),
        ("dk_p1_mo_mom", '=INDEX(INDEX(d_flow612,0,6),20)-INDEX(INDEX(d_flow612,0,6),19)', "+0;-0;0", '6/12: finished, change on the month before'),
        ("dk_p1_mo_dir", '=IF(dk_p1_mo_net>=0,"keeping up","falling behind")', "@", '6/12: last month, finished at least as many as added'),
        ("dk_p1_yr_fin", '=SUM(INDEX(INDEX(d_flow612,0,6),9):INDEX(INDEX(d_flow612,0,6),20))', "#,##0", '6/12: finished over the 12 months (the first month is partial)'),
        ("dk_p1_yr_added", '=SUM(INDEX(INDEX(d_flow612,0,5),9):INDEX(INDEX(d_flow612,0,5),20))', "#,##0", '6/12: added over the 12 months (the first month is partial)'),
        ("dk_p4_wk", '=INDEX(INDEX(d_code612,0,2),7)', "0", '6/12: ordinary code changes merged, last complete week'),
        ("dk_p4_wow", '=INDEX(INDEX(d_code612,0,2),7)-INDEX(INDEX(d_code612,0,2),6)', "+0;-0;0", '6/12: ordinary code changes merged, change on the week before'),
        ("dk_p4_avg4", '=AVERAGE(INDEX(INDEX(d_code612,0,2),3):INDEX(INDEX(d_code612,0,2),6))', "0", '6/12: ordinary code changes merged, average of the 4 complete weeks before last week (last week excluded)'),
        ("dk_p4_mo", '=INDEX(INDEX(d_code612,0,3),20)', "0", '6/12: ordinary code changes merged, last complete month'),
        ("dk_p4_mom", '=INDEX(INDEX(d_code612,0,3),20)-INDEX(INDEX(d_code612,0,3),19)', "+0;-0;0", '6/12: ordinary code changes merged, change on the month before'),
        ("dk_p4_yr", '=SUM(INDEX(INDEX(d_code612,0,3),9):INDEX(INDEX(d_code612,0,3),20))', "#,##0", '6/12: ordinary code changes merged over the 12 months (the first month is partial)'),
        ("dk_p5_wk", '=INDEX(INDEX(d_review612,0,2),7)', "0.0", '6/12: median hours to first review, last complete week'),
        ("dk_p5_wow", '=INDEX(INDEX(d_review612,0,2),7)-INDEX(INDEX(d_review612,0,2),6)', "+0.0;-0.0;0.0", '6/12: median hours to first review, change on the week before'),
        ("dk_p5_avg4", '=MEDIAN(FILTER(cc_hours_to_first_review,cc_counted=1,cc_state="merged",cc_class="normal",cc_merged_at>=INDEX(INDEX(m_612_periods,0,3),3),cc_merged_at<INDEX(INDEX(m_612_periods,0,4),6),cc_hours_to_first_review<>""))', "0.0", '6/12: median hours to first review over all ordinary changes merged in the 4 complete weeks before last week (last week excluded); a median over individual changes, not an average of weekly medians'),
        ("dk_p5_mo", '=INDEX(INDEX(d_review612,0,3),20)', "0.0", '6/12: median hours to first review, last complete month'),
        ("dk_p5_mom", '=INDEX(INDEX(d_review612,0,3),20)-INDEX(INDEX(d_review612,0,3),19)', "+0.0;-0.0;0.0", '6/12: median hours to first review, change on the month before'),
        ("dk_p5_yr", '=MEDIAN(FILTER(cc_hours_to_first_review,cc_counted=1,cc_state="merged",cc_class="normal",cc_merged_at>=(EDATE(asof,-12)+MOD(asof,1)),cc_merged_at<DATE(YEAR(asof),MONTH(asof),1),cc_hours_to_first_review<>""))', "0.0", '6/12: median hours to first review over the 12 months (the first month is partial)'),
        ("dk_p2_asof", '=SUMIFS(sh_in_progress_no_owner,sh_level,"SBU",sh_kind,"asof")', "0", "State history: in progress with no owner at the as-of"),
        ("dk_p2_last_wk", "=INDEX(INDEX(d_state612,0,2),7)", "0", "State history: at the end of the last complete week"),
        ("dk_p2_max", "=MAX(INDEX(d_state612,0,2),INDEX(d_state612,0,3))", "0", "State history: highest point in the 6 weeks and 12 months"),
        ('dk_b1_wk_fixed', '=INDEX(INDEX(d_bugs612_chart,0,3),7)', '0', 'B1: Bugs fixed in the last complete week'),
        ('dk_b1_wk_created', '=INDEX(INDEX(d_bugs612_chart,0,2),7)', '0', 'B1: Bugs created in the last complete week'),
        ('dk_b1_wk_net', '=INDEX(INDEX(d_bugs612_chart,0,4),7)', '+0;-0;0', 'B1: net (fixed minus created) for the last complete week'),
        ('dk_b1_wk_wow', '=INDEX(INDEX(d_bugs612_chart,0,3),7)-INDEX(INDEX(d_bugs612_chart,0,3),6)', '+0;-0;0', 'B1: fixed, change on the week before'),
        ('dk_b1_wk_avg4', '=AVERAGE(INDEX(INDEX(d_bugs612_chart,0,3),3):INDEX(INDEX(d_bugs612_chart,0,3),6))', '0', 'B1: fixed, average of the 4 complete weeks before last week (last week excluded)'),
        ('dk_b1_wk_dir', '=IF(dk_b1_wk_net>=0,"catching up","falling behind")', '@', 'B1: last week, fixed at least as many as created'),
        ('dk_b1_neg_run', neg_run("d_bugs612_chart", 4), '0', 'B1: weeks in a row, counting back from last week, with net (fixed minus created) below zero'),
        ('dk_b1_mo_fixed', '=INDEX(INDEX(d_bugs612_chart,0,6),20)', '0', 'B1: Bugs fixed in the last complete month'),
        ('dk_b1_mo_created', '=INDEX(INDEX(d_bugs612_chart,0,5),20)', '0', 'B1: Bugs created in the last complete month'),
        ('dk_b1_mo_net', '=INDEX(INDEX(d_bugs612_chart,0,7),20)', '+0;-0;0', 'B1: net for the last complete month'),
        ('dk_b1_mo_mom', '=INDEX(INDEX(d_bugs612_chart,0,6),20)-INDEX(INDEX(d_bugs612_chart,0,6),19)', '+0;-0;0', 'B1: fixed, change on the month before'),
        ('dk_b1_mo_dir', '=IF(dk_b1_mo_net>=0,"catching up","falling behind")', '@', 'B1: last month, fixed at least as many as created'),
        ('dk_b1_yr_fixed', '=SUM(INDEX(INDEX(d_bugs612_chart,0,6),9):INDEX(INDEX(d_bugs612_chart,0,6),20))', '#,##0', 'B1: Bugs fixed over the 12 months (the first month is partial)'),
        ('dk_b1_yr_created', '=SUM(INDEX(INDEX(d_bugs612_chart,0,5),9):INDEX(INDEX(d_bugs612_chart,0,5),20))', '#,##0', 'B1: Bugs created over the 12 months (the first month is partial)'),
        ('dk_b2_open', '=INDEX(INDEX(d_bugage,0,3),2)', '#,##0', 'B2: open Bugs at the as-of, SBU'),
        ('dk_b2_median', '=INDEX(INDEX(d_bugage,0,4),2)', '0', 'B2: median age in days of open Bugs, SBU'),
        ('dk_b2_p85', '=INDEX(INDEX(d_bugage,0,5),2)', '0', 'B2: 85th-percentile age in days of open Bugs, SBU'),
        ('dk_b2_over90', '=INDEX(INDEX(d_bugage,0,6),2)', '#,##0', 'B2: open Bugs older than 90 days, SBU'),
        ('dk_b2_over90_share', '=IFERROR(dk_b2_over90/dk_b2_open,"")', '0%', 'B2: share of open Bugs older than 90 days'),
        ('dk_b2_top_over90', '=MAX(INDEX(INDEX(d_bugage,0,6),3):INDEX(INDEX(d_bugage,0,6),8))', '#,##0', 'B2: largest Group count of open Bugs older than 90 days'),
        ('dk_b2_top_group', '=INDEX(INDEX(INDEX(d_bugage,0,2),3):INDEX(INDEX(d_bugage,0,2),8),MATCH(dk_b2_top_over90,INDEX(INDEX(d_bugage,0,6),3):INDEX(INDEX(d_bugage,0,6),8),0))', '@', 'B2: the Group with that count'),
    ]
    ans += inc_dk
    ans += wm_dk
    a0 = G.row
    G.put(a0, 0, "name"); G.put(a0, 1, "value"); G.put(a0, 2, "meaning")
    G.answer_cells = []
    G.answer_defs = []
    for i, (nm, f, fmt, d) in enumerate(ans):
        rr = a0 + 1 + i
        G.put(rr, 0, nm); G.put(rr, 1, f); G.put(rr, 2, d)
        G.name_cell(nm, rr, 1)
        G.answer_cells.append((rr, fmt))
        G.answer_defs.append((nm, d))
    G.name_range("m_answers", a0, 0, a0 + len(ans), 2)
    G.row = a0 + len(ans) + 3

    # ---------------------------------------------------------------- alerts
    G.title("m_alerts: proactive alerts in priority order. count = what the alert counts; detail = where to look. Ownerless backlog never alerts.")
    am0 = G.row
    for j, h in enumerate(["priority", "alert", "count", "unit", "detail"]):
        G.put(am0, j, h)
    sb = lv_r0 + 2
    teams_idx = [i for i, x in enumerate(LV) if x[0] == "Team"]
    grp_idx = [i for i, x in enumerate(LV) if x[0] == "Group"]
    def colrng(name, idxs):
        return f"{col_letter(ci[name])}{lv_r0 + 2 + idxs[0]}:{col_letter(ci[name])}{lv_r0 + 2 + idxs[-1]}"
    A = [
        (1, "Jira item in progress with no owner", f"={lvref('in_progress_no_owner')}", "items", "m_noowner_list has the keys; m_noowner_ip by Group"),
        (2, "Jira item in progress for longer than the stuck limit (t_stuck_days)", f"={lvref('aging_wip_over_p85')}", "items", "m_aging_wip: points above the diagonal"),
        (3, "People over the WIP limit (names only on the Individual tab)", f"={lvref('people_over_wip_limit')}", "people", "m_levels column people_over_wip_limit by Team"),
        (4, "Groups where last week's Jira throughput or merged changes fell below the drop threshold", f"=SUM({colrng('throughput_drop_alert', grp_idx)})+SUM({colrng('merge_drop_alert', grp_idx)})+{lvref('throughput_drop_alert')}+{lvref('merge_drop_alert')}", "flags", "m_levels columns throughput_drop_alert and merge_drop_alert (SBU and Group rows)"),
        (5, "Open change past the review threshold with no first review", f"={lvref('open_no_review_over_limit')}", "changes", "m_open_changes; m_levels column open_no_review_over_limit"),
        (6, "In-progress code-type issue with no linked change activity (A2)", f"={lvref('A2_count')}", "items", "m_levels column A2_count by Team"),
    ]
    for i, (p, nm, f, unit, det) in enumerate(A):
        G.put(am0 + 1 + i, 0, p); G.put(am0 + 1 + i, 1, nm); G.put(am0 + 1 + i, 2, f); G.put(am0 + 1 + i, 3, unit); G.put(am0 + 1 + i, 4, det)
        G.name_cell(f"alert{p}", am0 + 1 + i, 2)
    G.name_range("m_alerts", am0, 0, am0 + len(A), 4)
    G.row = am0 + len(A) + 2

    G.meta_ci = ci
    G.meta_lv = LV
    G.lv_r0 = lv_r0
    G.thr_r0 = thr_r0
    G.mg_r0 = mg_r0
    G.rt_teams = rt_teams
    return G
