#!/usr/bin/env python3
"""v1.36 links (A66): every Dashboard and Teams number links to the top of the derived 'Work items' or 'Code changes' tab; its cell note says how to filter to get the number
(itemfilters.describe). The flag columns repeat the count rule, so the rows left after that filter are the rows counted (selfcheck). Counts only, no names, no usernames in any link.
View key: '<tab>:<kind>:<measure>:<type>:<priority>:<scope>' (tab W work items | C code changes; scope sbu | g=<Group> | t=<Team> | gonly | sonly)."""
import json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
CFG = json.load(open(os.path.join(ROOT, "data", "config.json")))
GROUPS = list(CFG["groups"])
LAYOUT = os.path.join(ROOT, "data", "items_layout.json")
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemfilters as F


def _gid(tab):
    return json.load(open(LAYOUT))["gid"][F.TABNAME[tab]]


class V(str):
    """a view key"""


def _scope(scope):
    if scope == "sbu":
        return "sbu"
    if scope in ("gonly", "sonly", "rem"):
        return scope
    if isinstance(scope, tuple) and scope[0] == "group":
        return "g=" + scope[1]
    if isinstance(scope, tuple) and scope[0] == "team":
        return "t=" + scope[1]
    return None


def _key(tab, kind, measure, scope, typ="", prio=""):
    sc = _scope(scope)
    return None if sc is None else V(f"{tab}:{kind}:{measure}:{typ}:{prio}:{sc}")


def link(u, value):
    """HYPERLINK to the top of the item tab (A66: no saved views), value kept; u None = no link for this number"""
    if u is None:
        return value
    fv = F.view_id(str(u))          # v1.41 3d: a link opens its saved view when one exists, else the top of the tab
    return f'HYPERLINK("#gid={_gid(str(u).split(":", 1)[0])}&' + (f'fvid={fv}' if fv else 'range=A1') + f'",{value})'


def note(u, is_list=False):
    """the cell note of a linked number: where the link goes and how to filter to get the number"""
    return F.howto(str(u), is_list)


def work_period(kind, per, scope, issuetype=None, tech_debt=False):
    typ = "Bug" if issuetype == "Bug" else ("Technical Debt" if tech_debt else "")
    return _key("W", "work", ("fin_" if kind == "fin" else "add_") + per, scope, typ)


def work_open(kind, scope, unassigned=False):
    return _key("W", "work", "stuck" if kind == "wip" else ("blocked_long" if kind == "blocked_long" else "blocked"), scope)


def inc_period(project, kind, per, scope):
    return _key("W", "customer" if project == "EA" else "internal", ("fin_" if kind == "fin" else "add_") + per, scope)


def inc_open(project, scope, priority=None, over30=False, order=False):
    return _key("W", "customer" if project == "EA" else "internal", "over_limit" if over30 else "open", scope, "", "" if priority in (None, "All") else priority)


def work_mix(col, scope):
    """G2 (D408): the list behind a work-mix number: col fin | cust | int | ops | sup | none | feat, scope sbu or ('group', name)"""
    return _key("W", "work", "wm_" + col, scope)


def gl_merged(per, scope):
    return _key("C", "code", "merged_" + per, scope)


def gl_open(scope):
    return None


NOTE_EXACT = "Link to the item tab; the filter is in the note."
NOTE_TEAMFIELD = NOTE_EXACT
NOTE_LIST = "List link: the rows a median, age or share is worked out over."
NOTE_REMAINDER = NOTE_EXACT
NOTE_CODE = "No link can show this number."
NOTE_NONE = "No link: this row is a remainder (the total minus the other rows), so it has no rows of its own."
NOTE_GITLAB = NOTE_EXACT
NOTE_GITLAB_LIST = NOTE_LIST
