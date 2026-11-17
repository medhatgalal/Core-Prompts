"""v1.22: the eight Dashboard charts (D1, D3, D4, D5, B1, I1, I2, M1) built through the Sheets API from named ranges on Metrics. Deterministic; no Sheets AI.
I2 is a table (written by build.py). The Charts (detail) tab and its other charts are gone; their ranges stay on Metrics."""

PALETTE = ["1F77B4", "FF7F0E", "2CA02C", "9467BD", "8C564B", "E377C2", "17BECF", "BCBD22"]
GREY = {"sbu_main": "333333", "sbu_wont_do": "999999", "sbu_duplicate": "CCCCCC", "sbu_main_avg4": "000000"}


def rgb(hexs):
    return {"rgbColor": {"red": int(hexs[0:2], 16) / 255, "green": int(hexs[2:4], 16) / 255, "blue": int(hexs[4:6], 16) / 255}}


def chart_requests(G, ids, meta, cfg, row0, cap4=None, win=None, only=None):
    M = ids["Metrics"]
    D_ = ids["Dashboard"]
    groups_all = list(meta["groups"]) + [cfg["labels"]["other"], cfg["labels"]["unknown"]]
    gcolor = {g: PALETTE[i % len(PALETTE)] for i, g in enumerate(groups_all)}
    pcolor = {"gitlab": "FC6D26", "github": "24292E"}
    CLASS_COLORS = {"normal": "1F77B4", "bot": "FF7F0E", "revert": "D62728", "docs": "2CA02C", "backport": "9467BD", "release": "8C564B"}
    STATUS_COLORS = {"new": "8DA0CB", "created": "8DA0CB", "indeterminate": "FF7F0E", "done": "2CA02C"}   # one map for V2 and V3
    reqs = []

    def rng(name, c0=None, c1=None, skip_header=False):
        r0, a, r1, b = G.names[name]
        c0 = a if c0 is None else a + c0
        c1 = b if c1 is None else a + c1
        return {"sources": [{"sheetId": M, "startRowIndex": r0, "endRowIndex": r1 + 1, "startColumnIndex": c0, "endColumnIndex": c1 + 1}]}

    def shade(hexs, f):
        return "%02X%02X%02X" % tuple(int(int(hexs[i:i + 2], 16) * f) for i in (0, 2, 4))

    def col_color(header):
        h = header
        if h in STATUS_COLORS:
            return STATUS_COLORS[h]
        for plat, f in (("gitlab: ", 1.0), ("github: ", 0.55)):
            if h.startswith(plat):
                return shade(CLASS_COLORS[h[len(plat):]], f)
        for g, c in gcolor.items():
            if h == g or h.endswith(": " + g) or h.endswith(g):
                return c
        for k, c in GREY.items():
            if h == k:
                return c
        for p, c in pcolor.items():
            if h.startswith(p):
                return c
        return None

    KEYS = {}        # chart key -> [(label, colour hex)]: the cell key under a 6/12 chart (the Sheets API cannot merge legend entries: a series has no legend switch)
    placed = []      # (spec, w, h, key); spec None = a table placeholder (I2): rows are reserved, build.py writes the table
    extras = {"dash": {}}      # key -> dict(row (card row), col, span, card_rows, strip_row, chart_row)
    CARD_ROWS = {"D1": 4, "D3": 3, "K1": 3, "D4": 4, "D5": 4, "B1": 4, "I1C": 3, "I1": 3, "I2": 4, "M1": 4}

    def place(spec, w=850, h=378, key=None):
        placed.append((spec, w, h, key))

    def layout():
        """v1.26 Dashboard: columns A to F are 420, 130, 110, 190, 330 and 190 px. Every chart is 850 px wide (A to D), stacked, one per band; the detail table sits beside it in E to G.
        The answer card is right under the chart (A to D). The two incident charts are stacked; their one shared card is under the second. I2 is a table (A to F) with its card directly under it."""
        row = row0
        lst = placed if only is None else [p_ for p_ in placed if ("I1" if p_[3] == "I1I" else p_[3]) in only]
        for spec, w, h, key in lst:
            legend = KEYS.get(key)          # v1.30: a chart with a cell key has no native legend; the key takes the row right under the chart image
            img_h = h - (21 if legend else 0)
            # the first band row is 21 px (table title), the second 42 px (wrapped table header), the rest 21: rows the chart image really covers (a table beside it is on every slot but I2)
            covered = (2 + max(0, -(-(img_h - 63) // 21))) if spec is not None else -(-h // 21)
            hrows = covered + (1 if legend else 0)
            key_e = "I1C" if key == "I1C" else ("I1" if key == "I1I" else key)
            span = 6 if key_e == "I2" else 4          # the open-incident card has the width of its two tables (A to F); every chart card has its chart's width (A to D)
            crow = CARD_ROWS.get(key_e, 3)
            band = max(hrows, (meta.get("inc_table_rows") or {}).get(key_e, 0) + 2)
            # v1.30 spacing: chart (or table) band, ONE blank row, the answer card, ONE blank row, the next slot
            extras["dash"][key_e] = {"chart_row": row, "row": row + band + 1, "col": 0, "span": span, "card_rows": crow, "table_col": 4, "table_row": row, "band": band,
                                     "key_row": (row + covered) if legend else None, "legend": legend}
            if spec is not None:
                reqs.append({"addChart": {"chart": {"spec": spec, "position": {"overlayPosition": {
                    "anchorCell": {"sheetId": D_, "rowIndex": row, "columnIndex": 0}, "offsetXPixels": 0, "widthPixels": w, "heightPixels": img_h}}}}})
            row += band + 1 + crow + 1

    def basic(title, ctype, domain, series, xt, yt, stacked=None, legend=True, headers=None, combo_types=None, header_count=1, ranges_as_cols=True, subtitle=None):
        s = []
        for i, (src, hdr) in enumerate(series):
            e = {"series": {"sourceRange": src}, "targetAxis": "BOTTOM_AXIS" if ctype == "BAR" else "LEFT_AXIS"}
            c = col_color(hdr)
            if c:
                e["colorStyle"] = rgb(c)
            if combo_types:
                e["type"] = combo_types[i]
            s.append(e)
        b = {"chartType": ctype, "legendPosition": "BOTTOM_LEGEND",
             "axis": [{"position": "BOTTOM_AXIS", "title": xt}, {"position": "LEFT_AXIS", "title": yt}],
             "domains": [{"domain": {"sourceRange": domain}}], "series": s, "headerCount": header_count}
        if stacked:
            b["stackedType"] = stacked
        out = {"title": title, "basicChart": b}
        if subtitle:
            out["subtitle"] = subtitle
        return out

    def colsrc(name, j):
        return rng(name, j, j)

    ADDED, FINISHED, NET = STATUS_COLORS["created"], STATUS_COLORS["done"], "9467BD"      # the Dashboard palette: added blue, finished green, net purple

    def six12(title, name, measures, key, w, h, zero_col=None, subtitle="", wkey=None, single_axis=False, zero_name=None, left_title=None, right_title=None, names=None):
        """6/12 line chart (D84, D85, D86). measures: [(colour, weekly col, monthly col, weekly label col, monthly label col, label placement[, range name[, dash]])].
        One colour per measure for its weekly and monthly parts; weekly on the left axis, monthly on the right; the gap row is blank so the lines break;
        data labels come from the separate label columns (only last point, peak and low) as custom labels on the real series; a label column of None draws no label; legend at the bottom."""
        ser = []
        for m_ in measures:
            colour, cw, cm, lw, lm, place_ = m_[:6]
            nm = m_[6] if len(m_) > 6 else name
            dash = m_[7] if len(m_) > 7 else "SOLID"
            for c, axis, lc in ((cw, "LEFT_AXIS", lw), (cm, "RIGHT_AXIS", lm)):
                e = {"series": {"sourceRange": colsrc(nm, c)}, "targetAxis": axis, "type": "LINE", "colorStyle": rgb(colour),
                     "lineStyle": {"width": 2, "type": dash}, "pointStyle": {"shape": "CIRCLE", "size": 6}}
                if lc is not None:      # v1.26: the end labels sit on the real series (custom labels from the label columns), so the legend lists only real series
                    e["dataLabel"] = {"type": "CUSTOM", "customLabelData": {"sourceRange": colsrc(nm, lc)}, "placement": place_, "textFormat": {"fontSize": 9}}
                ser.append(e)
        if zero_col:
            ser.append({"series": {"sourceRange": colsrc(zero_name or name, zero_col)}, "targetAxis": "LEFT_AXIS", "type": "LINE", "colorStyle": rgb("444444"),
                        "lineStyle": {"width": 1, "type": "MEDIUM_DASHED"}, "pointStyle": {"shape": "CIRCLE", "size": 1}})
        left = {"position": "LEFT_AXIS", "title": "Left: per week. Right: per month."}          # A50: the API keeps no right-axis title, so the left axis title names both axes
        right = {"position": "RIGHT_AXIS"}
        if win and wkey in win:
            lo_w, hi_w, lo_m, hi_m = win[wkey]
            left["viewWindowOptions"] = {"viewWindowMin": lo_w, "viewWindowMax": hi_w}
            right["viewWindowOptions"] = {"viewWindowMin": lo_m, "viewWindowMax": hi_m}
        right["title"] = right_title or "Per month (right axis)"
        spec = {"title": title, "subtitle": subtitle,
                "basicChart": {"chartType": "LINE", "legendPosition": "NO_LEGEND", "headerCount": 1,
                               "axis": [{"position": "BOTTOM_AXIS", "title": "Last 6 weeks, then last 12 months"}, left] + ([right] if right else []),
                               "domains": [{"domain": {"sourceRange": colsrc(name, 0)}}], "series": ser}}
        KEYS[key] = [(names[i] if names else "", m_[0]) for i, m_ in enumerate(measures)] + ([("Zero line", "444444")] if zero_col else [])
        place(spec, w=w, h=h, key=key)

    KEY1 = "Blue added, green finished, purple net. Left axis per week, right per month."
    ADDED, FINISHED, NET = STATUS_COLORS["created"], STATUS_COLORS["done"], "9467BD"      # the Dashboard palette: added blue, finished green, net purple
    BUG_CREATED = "D62728"
    H = 336
    FULL = 940               # every chart is exactly as wide as columns A to D (360 + 230 + 220 + 130 px, set in dashboard_build.py), so the answer card (A to D) has the chart's edges
    PAGE = 1370              # A to F

    # ---------------- the eight Dashboard charts, in order (v1.22): D1, D3, D4, D5, B1, I1, I2, M1. Each has an answer card under it (build.py).
    six12("Are we finishing as much as we start? (work items added, finished and net: last 6 weeks, then last 12 months)", "d_flow612",
          [(ADDED, 1, 4, 8, 11, "ABOVE"), (FINISHED, 2, 5, 9, 12, "BELOW"), (NET, 3, 6, 10, 13, "ABOVE")], "D1", FULL, 378, zero_col=7, subtitle=KEY1, wkey="d_flow612", names=["Added", "Finished", "Net"])
    place(basic("Is anything stuck? (in-progress items older than normal for their Group, by Group)", "BAR", colsrc("d_stuck", 0),
                [(colsrc("d_stuck", 1), "count")], "Items older than their Group's P85", "Group"), w=FULL, h=H, key="D3")
    kr0, ka, kr1, kb = G.names["d_blocked"]          # K1: count by Group (the SBU total row is not a bar)
    ksrc = lambda j: {"sources": [{"sheetId": M, "startRowIndex": kr0, "endRowIndex": kr1, "startColumnIndex": ka + j, "endColumnIndex": ka + j + 1}]}
    place(basic("Is work blocked? (open items in a blocked status, by Group)", "BAR", ksrc(0), [(ksrc(1), "count")], "Blocked items", "Group"), w=FULL, h=H, key="K1")
    six12("Are we shipping code? (ordinary code changes merged: last 6 weeks, then last 12 months)", "d_code612",
          [(CLASS_COLORS["normal"], 1, 2, 3, 4, "ABOVE")], "D4", FULL, 378, names=["Changes merged"],
          subtitle="Ordinary changes only (no bots, docs, reverts or releases). Weeks left axis, months right; first month partial.")
    six12("Is code reviewed quickly? (median hours to first review: last 6 weeks, then last 12 months)", "d_review612",
          [(CLASS_COLORS["bot"], 1, 2, 3, 4, "ABOVE")], "D5", FULL, 378, names=["Median hours to first review"], subtitle="Median hours: weeks on the left axis, months on the right; the first month is partial.", wkey="d_review612",
          )
    six12("Are we fixing bugs as fast as they come in? (bugs created, fixed and net: last 6 weeks, then last 12 months)", "d_bugs612_chart",
          [(BUG_CREATED, 1, 4, 8, 11, "ABOVE"), (FINISHED, 2, 5, 9, 12, "BELOW"), (NET, 3, 6, 10, 13, "ABOVE")], "B1", FULL, 378, zero_col=7, names=["Created", "Fixed", "Net"],
          subtitle="Red created, green fixed, purple net (fixed minus created). Left axis per week, right per month; the first month is partial.", wkey="d_bugs612_chart")
    if meta.get("incidents_enabled", True):
        # I1: two charts stacked (customer, then internal), the shared answer card under the second
        for code, sp in (("C", "customer"), ("I", "internal")):
            six12(f"Are we keeping up with {sp} incidents? (created, resolved and net: last 6 weeks, then last 12 months)", f"d_inc612_chart_{sp}",
                  [(BUG_CREATED, 1, 4, 8, 11, "ABOVE"), (FINISHED, 2, 5, 9, 12, "BELOW"), (NET, 3, 6, 10, 13, "ABOVE")], f"I1{code}", FULL, 378, zero_col=7, names=["Created", "Resolved", "Net"],
                  subtitle="Red created, green resolved, purple net. Left axis per week, right per month.", wkey=f"d_inc612_chart_{sp}")
        place(None, w=PAGE, h=(meta.get("i2_rows") or 11) * 21, key="I2")
    # M1 (v1.43c AC76, replaces T1): work mix, share of finished tickets by Work Category, SBU, 6/12
    six12("What kind of work did we finish? (% of finished tickets by Work Category: last 6 weeks, then last 12 months)", "d_workmix612_chart",
          [("1F77B4", 1, 6, None, None, "ABOVE"), ("17BECF", 2, 7, None, None, "ABOVE"), ("FF7F0E", 3, 8, None, None, "ABOVE"), ("D62728", 4, 9, None, None, "ABOVE"), ("888888", 5, 10, None, None, "ABOVE", "d_workmix612_chart", "MEDIUM_DASHED")],
          "M1", FULL, 378, names=["Customer Feature", "Internal Feature", "Ops & Maintenance", "Support", "No category (share of all finished)"],
          subtitle="SBU. Share of finished tickets that have a category; the dashed line is the share with no category. History is the epic's value at the finish date, not change events. Group shares for 12 months are in the table beside the chart.")
    layout()
    return reqs, extras
