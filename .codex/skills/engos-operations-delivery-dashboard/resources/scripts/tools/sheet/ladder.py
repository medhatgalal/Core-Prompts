#!/usr/bin/env python3
"""v1.34 attribution ladder (A53) with tags at the event date and the org-events table (AC71, A54, A55, A57, A58, A60).
A Jira ticket is ours at the first level that applies: (1) its Team is an Automation Team, at Team level; (2) else its Group is an Automation Group, at Group level;
(3) else its SBU is Automation, at SBU level (SBU row only); (4) else not ours. Tags are read at the event date, rebuilt from the changelog (jira_tag_history.csv)
and adjusted by data/org_events.csv: a 'restate' bulk retag (A to B) means history follows B for every date; a 'freeze' keeps the tag at the time; lineage rows rename
(a former Group name is one current Group at every date) or end a Group (a Group that counts in Automation through a last date, inclusive).
Counts only: nothing here stores a person, a title or free text."""
import csv, datetime as dt, collections, os

UTC = dt.timezone.utc


def pt(x):
    return dt.datetime.fromisoformat(x.replace("Z", "+00:00")).astimezone(UTC) if x else None


class Ladder:
    def __init__(self, cfg, jira_dir, roster_rows, org_path="data/org_events.csv", lineage_path="data/team_lineage.csv", team_groups_path="data/team_groups.csv"):
        self.groups = list(cfg["groups"])
        self.placeholders = set(cfg.get("placeholder_teams", ["Pending Assignment"]))          # A72, A75: a placeholder Team value is blank: no Team, never a conflict
        self.alias = dict(cfg.get("jira", {}).get("team_aliases", {}))           # Jira Team name -> roster Team name (A45)
        self.GROUP_ALIASES = dict(cfg["jira"]["group_aliases"])          # D402: former Group names that are one current Group at every date (config jira.group_aliases); by NAME on purpose (A78)
        self.group_col = cfg["jira"]["group_field_column"]               # the derived column that holds the Jira Group field value
        # the roster Teams under the 4 Groups, and each Team's Group
        self.team_group = {}
        for r in roster_rows:
            if r.get("team") and r.get("group") in self.groups:
                self.team_group.setdefault(r["team"], r["group"])
        self.events = list(csv.DictReader(open(org_path))) if os.path.exists(org_path) else []
        self.rename = {e["from_value"]: e["to_value"] for e in self.events if e["kind"] == "lineage" and e["field"] == "group" and e["to_value"] and e["mode"] == "restate"}
        self.ended = {e["from_value"]: pt(e["valid_to"] + "T23:59:59Z") for e in self.events if e["kind"] == "lineage" and e["field"] == "group" and not e["to_value"] and e["valid_to"]}
        self.restates = [e for e in self.events if e["kind"] == "bulk_retag" and e["mode"] == "restate"]
        # team lineage (A58: teams are renamed often; history follows the current name): from_team, to_team, valid_from, valid_to (blank = all dates); a data file, empty until the user maps names
        self.team_lineage = []
        if os.path.exists(lineage_path):
            for r in csv.DictReader(open(lineage_path)):
                if r.get("from_team") and r.get("to_team"):
                    self.team_lineage.append((r["from_team"], r["to_team"], pt(r["valid_from"] + "T00:00:00Z") if r.get("valid_from") else None, pt(r["valid_to"] + "T23:59:59Z") if r.get("valid_to") else None))
        # A64: a Team that is off the roster still counts at Team level under the Group data/team_groups.csv gives it (team, group, valid_from, valid_to)
        self.former = {}
        if os.path.exists(team_groups_path):
            for r in csv.DictReader(open(team_groups_path)):
                if r.get("team") and r.get("group") in self.groups:
                    self.former.setdefault(r["team"], (r["group"], pt(r["valid_from"] + "T00:00:00Z") if r.get("valid_from") else None, pt(r["valid_to"] + "T23:59:59Z") if r.get("valid_to") else None))
        self.hist = collections.defaultdict(list)
        p = os.path.join(jira_dir, "jira_tag_history.csv")
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                self.hist[(r["key"], r["field"])].append((pt(r["changed_at"]), r["from_value"], r["to_value"], r.get("from_id", ""), r.get("to_id", "")))
            for v in self.hist.values():
                v.sort(key=lambda x: x[0])
        # a change belongs to a restate event when field, from and to match and it falls in the event's window
        self._win = []
        for e in self.restates:
            st = pt(e["event_date"])
            self._win.append((e["field"], e["from_value"], e["to_value"], st - dt.timedelta(minutes=1), st + dt.timedelta(hours=float(e["span_hours"] or 0) + 1)))

    def _is_restated(self, field, ch):
        t, a, b = ch[0], ch[1], ch[2]
        return any(f == field and a == fa and b == tb and lo <= t <= hi for f, fa, tb, lo, hi in self._win)

    def value_at(self, key, field, when, current):
        """the tag value of the ticket at 'when': the changelog gives the value then; a restated bulk retag after 'when' replaces the old value with the corrected one.
        Matching is by NAME (A78): option ids are recorded but not used."""
        chg = self.hist.get((key, field), [])
        if not chg:
            v, vid = current, ""
        else:
            before = [c for c in chg if c[0] <= when]
            v, vid = (before[-1][2], before[-1][4]) if before else (chg[0][1], chg[0][3])
            for c in chg:
                if c[0] > when and self._is_restated(field, c) and (v == c[1] or (os.environ.get("LADDER_ID_MATCH") and vid and vid == c[3])):   # A65, A78 (the env toggle exists only to measure the id reading for crew/agents/sheet/option-15769.md; never set in a build): restates match by NAME; Jira option ids are NOT used (Groups that share a history are still distinct Groups)
                    v, vid = c[2], c[4]
        return v or ""

    def at_creation(self, issue, asof):
        """A71: the tag at creation is the SETTLED value at the end of the 24 h window after creation (initial tagging often takes several edits), with restates applied; an issue younger than 24 h at the as-of uses the as-of"""
        cr = pt(issue["created"])
        return self.at(issue, min(cr + dt.timedelta(hours=24), asof))

    # D402 (user): some former Group names are one current Group at every date; the names come from config jira.group_aliases (set per instance in __init__).
    # By NAME on purpose (A78 keeps name matching): the changelog names the old options 1:1, and a ticket that never changed Group has no option id in the
    # history, only today's name.

    def canon_group(self, g):
        g = self.rename.get(g, g)
        return self.GROUP_ALIASES.get(g, g)

    def at(self, issue, when):
        """-> dict(level, group, team, ours, conflict, untagged, sbu) for the ticket at 'when'"""
        key = issue["key"]
        team = self.value_at(key, "team", when, issue.get("team_name", ""))
        team = self.alias.get(team, team)
        if team in self.placeholders:
            team = ""
        for fr, to, lo, hi in self.team_lineage:
            if team == fr and (lo is None or when >= lo) and (hi is None or when <= hi):
                team = to
                break
        grp = self.canon_group(self.value_at(key, "group", when, issue.get(self.group_col, "")))
        sbu = self.value_at(key, "sbu", when, issue.get("sbu", ""))
        g_ours = grp in self.groups or (grp in self.ended and when <= self.ended[grp])
        tg_ = self.team_group.get(team)
        if tg_ is None and team in self.former:
            g_, lo_, hi_ = self.former[team]
            if (lo_ is None or when >= lo_) and (hi_ is None or when <= hi_):
                tg_ = g_
        t_ours = tg_ is not None
        s_ours = sbu == "Automation"
        level = "Team" if t_ours else ("Group" if g_ours else ("SBU" if s_ours else ""))
        ours = bool(level)
        group = ""
        if level == "Team":
            group = tg_
        elif level == "Group":
            group = grp
        non_ours = [x for x, ok in ((team, t_ours), (grp, g_ours), (sbu, s_ours)) if x and not ok]
        conflict = ours and (bool(non_ours) or (t_ours and g_ours and tg_ != grp))
        untagged = not (team or grp or sbu)
        return {"level": level, "group": group, "team": team if t_ours else "", "ours": ours, "conflict": conflict, "untagged": untagged, "sbu": sbu, "grp_tag": grp, "team_tag": team}
