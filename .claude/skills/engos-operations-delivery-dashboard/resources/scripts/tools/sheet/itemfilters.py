#!/usr/bin/env python3
"""v1.36 (A66): no saved views. Every number links to the top of 'Work items' or 'Code changes'; its cell note says how to filter to get the number.
This module is the one definition of the columns and of the filter behind every link key (no imports, so links, builders and the selfcheck share it).
Link key: '<tab>:<kind>:<measure>:<type>:<priority>:<scope>' (tab W | C; scope sbu | g=<Group> | t=<Team> | gonly | sonly)."""

WI_IDS = ["key", "kind", "type", "priority", "level", "group", "team", "sbu", "group_at_creation", "team_at_creation", "status", "created", "finished", "tag_conflict",
          "fin_wk", "fin_mo", "add_wk", "add_mo", "stuck", "blocked", "open", "over_limit", "blocked_long", "work_category", "item_kind", "stalled", "all_done", "fin_yr"]
WI_DISP = ["Key", "Kind", "Type", "Priority", "Level", "Group", "Team", "SBU", "Group at creation", "Team at creation", "Status", "Created", "Finished", "Tag conflict",
           "Finished last week", "Finished last month", "Added last week", "Added last month", "Stuck now", "Blocked now", "Open now", "Open too long", "Blocked too long", "Work category", "Item kind", "Stalled now", "Children all done", "Finished last 12 months"]
CC_IDS = ["number", "host", "repo", "group", "team", "level", "class", "state", "counted", "merged", "merged_wk", "merged_mo", "kind", "key_state"]
CC_DISP = ["Number", "Host", "Repo", "Group", "Team", "Level", "Class", "State", "Counted", "Merged", "Merged last week", "Merged last month", "Kind", "Ticket link"]
DISP = {"W": dict(zip(WI_IDS, WI_DISP)), "C": dict(zip(CC_IDS, CC_DISP))}
TABNAME = {"W": "Work items", "C": "Code changes"}


WM_NAMES = ("Customer Feature", "Internal Feature", "Ops & Maintenance", "Support")
WM_CATS = {"wm_fin": "*", "wm_cust": "Customer Feature", "wm_int": "Internal Feature", "wm_ops": "Ops & Maintenance", "wm_sup": "Support", "wm_none": "", "wm_feat": ("Customer Feature", "Internal Feature")}
WM_LABEL = {"wm_fin": "All", "wm_cust": "Customer Feature", "wm_int": "Internal Feature", "wm_ops": "Ops & Maintenance", "wm_sup": "Support", "wm_none": "No category", "wm_feat": "Features (Customer and Internal)"}


def criteria(key):
    """-> [(column id, kind, value)] kind eq | num | hide"""
    tab, kind, measure, typ, prio, sc = key.split(":", 5)
    out = []
    if measure == "tile_level":          # attribution-health tiles (AC72)
        return [("kind", "eq", "work"), ("level", "eq", typ)]
    if measure == "kind_is":          # A74: the Other and untagged counts on the person rows link here: Kind = other (or untagged); not narrowed per person
        return [("kind", "eq", typ)]
    if measure == "sbu_only_inc":
        return [("kind", "hide", ["work", "container"]), ("level", "eq", "SBU")]          # D407: v1.43 added Kind = container rows; an incident is neither
    if measure in WM_CATS:          # G2 (D408): the work-mix numbers: finished work items of the last 12 complete months (main series), by Work category, SBU or one Group
        out = [("kind", "eq", "work"), ("fin_yr", "num", 1)]
        cat = WM_CATS[measure]
        if cat == "*":
            pass
        elif cat == "":
            out.append(("work_category", "hide", list(WM_NAMES)))          # No category = none of the four
        elif isinstance(cat, tuple):
            out.append(("work_category", "hide", [c for c in WM_NAMES if c not in cat]))          # features = Customer + Internal: hide the other two ...
            out.append(("work_category", "notblank", None))          # ... and require a value (a blank inside hiddenValues is undocumented in the API: q95 follow-up)
        else:
            out.append(("work_category", "eq", cat))
        if sc.startswith("g="):
            out.append(("group", "eq", sc[2:]))
        return out
    if measure == "tile_noticket":
        return [("counted", "eq", "1"), ("class", "eq", "normal"), ("state", "eq", "merged"), ("key_state", "eq", "no_key"), ("host", "eq", typ)]
    if tab == "C":
        out.append((measure, "num", 1))
        g, t = "group", "team"
    else:
        out.append(("kind", "eq", kind))
        if measure.startswith("c_"):          # v1.43c AC75: epics and initiatives (kind = container): open, stalled, children all done; typ = Epic or Initiative
            out.append(("type", "eq", typ)); out.append(("status", "hide", ["done"]))
            if measure == "c_stalled": out.append(("stalled", "num", 1))
            if measure == "c_alldone": out.append(("all_done", "num", 1))
            typ = ""
        else:
            out.append((measure, "num", 1))
        if typ:
            out.append(("type", "eq", typ))
        if prio:
            out.append(("priority", "eq", prio))
        c = measure.startswith("add_")
        g, t = ("group_at_creation", "team_at_creation") if c else ("group", "team")
    if sc.startswith("g="):
        out.append((g, "eq", sc[2:]))
    elif sc.startswith("t="):
        out.append((t, "eq", sc[2:]))
    elif sc == "gonly":
        out += ([("level", "eq", "Group")] if not (tab == "W" and measure.startswith("add_")) else []) + [(t, "eq", "No team"), (g, "hide", ["SBU only"])]          # created counts read the Group and Team at creation, so no level filter there
    elif sc == "sonly":
        out.append((g, "eq", "SBU only"))
    elif sc == "rem":          # v1.41 3c: the Teams remainder row (Not in an Automation Group): every Group that is not one of ours and not SBU only
        import json as _j, os as _o
        out.append((g, "hide", list(_j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "..", "data", "config.json")))["groups"]) + ["SBU only"]))
    return out


def describe(key):
    """the filter line in a cell note, readable and machine-parsable: 'Filter: Kind = work; Finished last week = 1; Group = EXAMPLE GROUP'"""
    tab = key.split(":", 1)[0]
    parts = []
    for c, kd, v in criteria(key):
        n = DISP[tab][c]
        if kd == "notblank":
            parts.append(f"{n} has a value"); continue
        parts.append(f"{n} = {v}" if kd in ("eq", "num") else (f"{n} is none of {', '.join(v)}" if len(v) > 1 else f"{n} is not {v[0]}"))
    return "Filter: " + "; ".join(parts)


def parse(tab, line):
    """inverse of describe(): the note's filter line -> [(column id, kind, value)]"""
    rev = {v: k for k, v in DISP[tab].items()}
    out = []
    for p in line.split("Filter:", 1)[1].strip().rstrip(".").split("; "):
        if p.endswith(" has a value"):
            out.append((rev[p[:-len(" has a value")]], "notblank", None))
        elif " is none of " in p:
            n, v = p.split(" is none of ", 1); out.append((rev[n], "hide", v.split(", ")))
        elif " is not " in p:
            n, v = p.split(" is not ", 1); out.append((rev[n], "hide", [v]))
        else:
            n, v = p.split(" = ", 1); out.append((rev[n], "num" if v == "1" and n not in ("Number",) and rev[n] in ("fin_wk", "fin_mo", "add_wk", "add_mo", "stuck", "blocked", "open", "over_limit", "blocked_long", "merged_wk", "merged_mo", "stalled", "all_done", "fin_yr") else "eq", v))
    return out


import json as _json, os as _os
VIEW_REG = _os.environ.get("VIEWS_REG") or _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "data", "views_v141.json")          # one registry per target sheet (VIEWS_REG, set by the run driver)
TEAM_GROUP = {}          # set by teams_build: Team -> Group (a Team link opens its Group's view; the note says to set Team too)
ED_NOTE = "Editors: use Data > Filter views > Create new temporary filter view, or reset the saved view after."          # nobody changes a saved view's filter
PERIOD_SFX = {"fin_wk": " last week", "fin_mo": " last month", "add_wk": " last week", "add_mo": " last month", "merged_wk": " last week", "merged_mo": " last month"}          # v1.43i: appended to the view family name
EXTRA_SCOPES = {"gonly": "Group level, no Team", "sonly": "Group SBU only", "rem": "Not in an Automation Group"}          # v1.43i: scopes that had no view; period views only
PERIOD = {"fin_wk": "Finished last week", "fin_mo": "Finished last month", "add_wk": "Added last week", "add_mo": "Added last month", "merged_wk": "Merged last week", "merged_mo": "Merged last month"}


def use_registry_for(sid, env=None, base=None):
    """D417: the saved-view registry of THIS Sheet = data/views_<first 6 characters of the Sheet id>.json. VIEWS_REG (set by the run driver) wins. A Sheet with no registry file STOPS the build before any write:
    the old default views_v141.json holds the ids of another Sheet's views, and every Alerts link built from it opened a view that does not exist (verify-d #95). Sets and returns VIEW_REG."""
    global VIEW_REG
    env = _os.environ if env is None else env
    if env.get("VIEWS_REG"):
        VIEW_REG = env["VIEWS_REG"]; return VIEW_REG
    base = base or _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "data")
    p = _os.path.join(base, f"views_{sid[:6]}.json")
    if not _os.path.exists(p):
        raise SystemExit(f"stop: no saved-view registry for this Sheet ({_os.path.basename(p)} is missing); links would open another Sheet's views. No write was made.")
    VIEW_REG = p; return p


def views():
    """{title: filterViewId} of the saved views (v1.41 3d), or {} when the registry does not exist (links then stay plain, A66)"""
    try:
        return _json.load(open(VIEW_REG))["views"]
    except Exception:
        return {}


def view_title(key):
    """the saved view that shows this link key's rows (a view holds the measure and the scope, never the period), or None when no view exists for it"""
    tab, kind, measure, typ, prio, sc = key.split(":", 5)
    pd = PERIOD_SFX.get(measure, "")          # v1.43i (AC73a): a period number opens a view that holds its period (the flag column = 1), so the title says which
    if sc == "sbu":
        lab = "SBU"
    elif sc.startswith("g="):
        lab = "Group " + sc[2:]
    elif sc.startswith("t=") and sc[2:] in TEAM_GROUP:
        lab = "Group " + TEAM_GROUP[sc[2:]]
    elif pd and sc in EXTRA_SCOPES:          # period numbers only: the Teams rows 'Group level, no Team', 'Group SBU only' and the remainder row each get their own exact view
        lab = EXTRA_SCOPES[sc]
    else:
        return None
    if tab == "C":
        if measure in ("merged_wk", "merged_mo"):
            return f"Code changes | Merged ordinary changes{pd} | {lab}"
        if measure == "tile_noticket":
            return f"Code changes | No linked ticket | {typ.capitalize()}"
        return None
    name = "Work items | "
    if kind == "container" and measure in ("c_open", "c_stalled", "c_alldone"):          # v1.43c AC75
        w = {"Epic": "Epics", "Initiative": "Initiatives"}.get(typ)
        return (name + w + " " + {"c_open": "open", "c_stalled": "stalled", "c_alldone": "all children done"}[measure] + " | " + lab) if w and not (typ == "Initiative" and measure == "c_alldone") else None
    if kind == "work" and measure in WM_CATS:          # G2 (D408)
        return f"{name}Work mix finished 12 months, {WM_LABEL[measure]} | {lab}"
    if kind == "work":
        m = {"stuck": "Stuck now", "blocked": "Blocked now", "blocked_long": "Blocked too long", "tag_conflict": "Tag conflict"}.get(measure)
        if measure == "tile_level":
            return name + {"Team": "Level Team", "Group": "Level Group", "SBU": "Level SBU only"}.get(typ, "?") + " | SBU"
        if m:
            return name + m + " | " + lab
        per = measure[:3]
        if per == "fin":
            return name + {"": "Work finished", "Bug": "Bugs fixed"}.get(typ, "?") + pd + " | " + lab
        if per == "add":
            return name + {"": "Work added", "Bug": "Bugs created"}.get(typ, "?") + pd + " | " + lab
        return None
    if kind in ("customer", "internal"):
        kd = kind.capitalize()
        if measure == "sbu_only_inc":
            return name + "Incidents at SBU level only | SBU"
        if measure in ("open", "over_limit"):
            w = "open now" if measure == "open" else "open too long"
            return name + f"{kd} incidents {w}" + (f" | priority {prio}" if prio else "") + " | " + lab
        if measure[:3] == "fin":
            return name + f"{kd} incidents resolved{pd} | {lab}"
        if measure[:3] == "add":
            return name + f"{kd} incidents created{pd} | {lab}"
    return None


def view_id(key):
    t = view_title(key)
    return views().get(t) if t else None


LIST_MARKS = ("worked out over", "rows this number is computed", "net or a share", "List link")          # every list-link note carries one of these; the reader (period_inventory) and the check in items_check go by them


def note_is_list(note):
    """v1.43i (verify-c q121): a note says its link is a list link (the number is a median, share, net or average, not a count of the rows). One definition for the writer and the readers."""
    return any(m in (note or "") for m in LIST_MARKS)


def howto_avg4(key, extra=""):
    """v1.43i (verify-c q121): the Alerts 'average of the 4 weeks before' cells open last week's view. The note says so: the view is context, the number is not worked out over its rows."""
    vt = view_title(key)
    if vt and vt in views():
        return (f'Opens the saved view "{vt}" on the {TABNAME[key.split(":", 1)[0]]} tab, which shows LAST week\'s rows for context. This number is the average per week of the 4 weeks before last week: '
                f'it is worked out over those earlier weeks, not over the rows of this view, so the view\'s row count is not this number.{extra} ' + describe(key) + ".")
    return howto(key, True) + extra


def howto(key, is_list=False):
    """the cell note of a link. v1.43i (AC73a): a period number's view already holds its period, so no note tells the reader to add it. Team numbers open their Group's view: the note says to set Team (this row's Team, no name)."""
    tab = key.split(":", 1)[0]
    vt = view_title(key)
    if vt and vt in views():
        meas = key.split(":", 5)[2]
        sc = key.split(":", 5)[5]
        per = " The period is already applied." if meas in PERIOD else ""
        if is_list:
            extra = " Its rows are the rows this number is worked out over (a median, age or share is worked out over them)." + per
        elif sc.startswith("t="):
            extra = " It shows the whole Group" + (" for the period" if meas in PERIOD else "") + " (not only this row's Team): also set Team = this row's Team to get this number. The rows of the Team are not a saved view."
        else:
            extra = " Its rows are the rows counted." + per
        return f'Opens the saved view "{vt}" on the {TABNAME[tab]} tab.' + extra + " " + describe(key) + "."
    lead = ("Opens the top of the " + TABNAME[tab] + " tab. Use its filter buttons (row 1) to get " + ("the rows this number is computed from (a median, age or share is worked out over them). " if is_list else "this number: the rows left are the rows counted. "))
    return lead + describe(key) + "."


def _selftest():
    import tempfile
    t = tempfile.mkdtemp()
    for n, v in (("views_v141.json", 1), ("views_ABCDEF.json", 2)):
        _json.dump({"views": {"T": v}}, open(_os.path.join(t, n), "w"))
    ok = True
    global VIEW_REG
    keep = VIEW_REG
    try:
        use_registry_for("ABCDEF123", env={}, base=t); ok &= views() == {"T": 2}                       # this Sheet's registry, not v141
        try:
            use_registry_for("ZZZZZZ999", env={}, base=t); ok = False                                    # no registry: stop, never v141
        except SystemExit as e:
            ok &= "no saved-view registry" in str(e)
        use_registry_for("ZZZZZZ999", env={"VIEWS_REG": _os.path.join(t, "views_v141.json")}, base=t); ok &= views() == {"T": 1}          # the run driver's VIEWS_REG wins
        real = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "data")
        _st = _json.load(open(_os.path.join(real, "config.json")))["selftest_ids"]
        use_registry_for(_st["real_sheet_id"], env={}, base=real)
        ok &= views().get("Work items | Stuck now | SBU") == _st["stuck_view_real"]                       # the real Sheet's id (v141 says stuck_view_v141)
    finally:
        VIEW_REG = keep
    print("itemfilters registry selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_selftest() if "--selftest" in _sys.argv else 2)
