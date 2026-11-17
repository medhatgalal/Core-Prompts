"""Derive Team and Group for each roster person from the parsed department page.
Usage: derive.py <dept_json> <roster_in> <roster_out> <report_md> [--write-ledger]
Rules (see report): tier1 Team/Developers/Quality; tier2 Lead; tier3 Delivery Manager. Backup contact / technical
advisor / product roles never assign a team. Seed blank group+team stays blank (the user-confirmed roster)."""
import sys, json, collections
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
def tier(sec):
    if sec == "Team" or "Developer" in sec or sec.startswith("Quality Lead"): return 1
    if sec == "Lead": return 2
    if sec == "Delivery Manager": return 3
    return None
def main():
    dept = json.load(open(sys.argv[1]))["rows"]; ros = read_csv(sys.argv[2])
    idx = {}
    for r in ros: idx[norm(r["chart_name"])] = r; idx[norm(r["name"])] = r
    mem = collections.defaultdict(list)
    for r in dept:
        p = idx.get(norm(r["name"]))
        if p: mem[p["name"]].append((r["group"], r["team"], r["section"]))
    out, report, changes = [], [], []
    for r in ros:
        r = dict(r); sg, st = r["group"], r["team"]
        if not sg and st in GROUPS: sg, st = st, ""          # seed put a group name in the team column
        seed_blank = not sg and not st
        m = mem.get(r["name"], [])
        ng, nt, why = sg, st, ""
        cands = None
        for t in (1, 2, 3):
            c = list(dict.fromkeys((g, tm) for g, tm, s in m if tier(s) == t))
            if c: cands = (t, c); break
        if seed_blank and r["group"] == "" and r["team"] == "":
            ng, nt = "", ""
            if cands: why = f"seed blank kept; page shows {sorted(cands[1])} (tier {cands[0]})"
        elif cands is None:
            why = "not on any team page; seed values kept (group-in-team-column fixed)"
        else:
            t, c = cands
            pool = list(dict.fromkeys((g, tm) for g, tm, sc in m if tier(sc)))
            spick = [x for x in pool if x[1] == st]
            if spick and len(c) > 1 or (spick and spick[0] not in c):
                ng, nt = spick[0]; why = f"kept seed team {st!r}; page roles: " + "; ".join(f"{tm} ({sc})" for g, tm, sc in m if tier(sc))
            elif len(c) == 1: ng, nt = c[0]
            else:
                if len({g for g, _ in c}) == 1: ng, nt = c[0][0], ""; why = f"on {len(c)} teams {sorted(x[1] for x in c)}, seed team not among them; team left blank"
                else: ng, nt = sg, ""; why = f"on teams in several groups {sorted(c)}; team blank, seed group kept"
        if nt == "(Not on a Team)": nt = ""
        if ng and ng not in GROUPS: why = (why + "; " if why else "") + f"seed group '{ng}' is not one of the four groups"
        if (r["group"], r["team"]) != (ng, nt):
            changes.append((r["name"], r["group"], r["team"], ng, nt))
        r["group"], r["team"] = ng, nt
        if why: report.append((r["name"], why))
        out.append(r)
    write_csv(sys.argv[3], out, ROSTER_COLS)
    with open(sys.argv[4], "w") as f:
        f.write(f"# Team/Group derivation, {now()}\n\nChanged vs seed: {len(changes)} of {len(ros)}\n\n")
        for c in changes: f.write(f"- {c[0]}: ({c[1]!r}, {c[2]!r}) -> ({c[3]!r}, {c[4]!r})\n")
        f.write(f"\n## Ambiguities ({len(report)})\n\n")
        for n, w in report: f.write(f"- {n}: {w}\n")
        multi = []
        for r in out:
            m = mem.get(r["name"], [])
            core = sorted({(g, tm) for g, tm, s in m if tier(s)})
            allt = sorted({(g, tm) for g, tm, s in m})
            if len(core) >= 2 or len(allt) >= 2: multi.append((r, m, core, allt))
        f.write(f"\n## Multiple team memberships on the page ({len(multi)} people; every one listed)\n\n")
        f.write("Roster team shown first; roles from the page (Team, Developers, Quality Lead, Lead, Delivery Manager assign a team; Backup Contact and Technical Advisor never do).\n\n")
        for r, m, core, allt in multi:
            f.write(f"- {r['name']}: roster = {r['group']} | {r['team'] or '(none)'}; page: " + "; ".join(f"{tm} [{s}]" for g, tm, s in m) + f" ({len(core)} assigning teams, {len(allt)} teams in all)\n")
    if "--write-ledger" in sys.argv:
        for n, bg, bt, ag, at in changes:
            ledger_append("roster seed", n, "group,team", f"{bg}|{bt}", f"{ag}|{at}", "recomputed from department page (expanded)")
    print("changed", len(changes), "ambiguities", len(report))
main()
