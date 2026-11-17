"""Parse the saved department page text into (group, team, section, name, code) rows.
Usage: dept_parse.py <page_txt> <out_json>   Also prints the printed count lines exactly (AC3)."""
import sys, re, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import GROUPS
import os
DEPT_HEADER = os.environ.get("DASHBOARD_DEPT_HEADER", "")  # page header text to skip; set for your org
SECTION = re.compile(r"^(Product Owners?|User Experience|Documentation|Delivery Manager|Backup Contact|Quality Leads?|Lead|Team|Technical Advisors?|Technical Lead|\d+ Developers?)$")
CODE = re.compile(r"^[A-Z]{2,5}\d?$")
def split_code(s):
    s = s.strip(); t = s.split()
    if len(t) >= 3 and CODE.match(t[-1]): return " ".join(t[:-1]), t[-1]
    if len(t) == 2 and CODE.match(t[-1]) and len(t[-1]) >= 3 and t[-1] not in ("H",): return t[0], t[-1]  # single-token name + code
    return s, ""
def parse(txt):
    L = [l.rstrip() for l in txt.split("\n")]
    rows, counts = [], []
    group = team = section = None
    for i, raw in enumerate(L):
        l = raw.strip()
        if not l: continue
        if l in GROUPS and any(x.strip() == "Click on this icon to open the team page" for x in L[max(0,i-3):i]):
            group, team, section = l, None, None; continue
        m = re.match(r"^(\d+) teams\s+●\s+(\d+) full-time staff\s+●\s+(\d+) loaned\s+●\s+(\d+) borrowed", l)
        if m and group: counts.append({"group": group, "line": re.sub(r"\s+", " ", l)}); continue
        if group and i + 2 < len(L) and L[i+2].strip() == "Edit Team" and not L[i+1].strip():
            team, section = l, None; continue
        if l == "Not on a Team" and group: team, section = "(Not on a Team)", "Team"; continue
        if (DEPT_HEADER and l.startswith(DEPT_HEADER)) or l.startswith("Click on this") or l.startswith("Button Collapse"): team = None; continue
        if not team: continue
        if SECTION.match(l): section = l; continue
        if l in ("Edit Group", "Add Team", "Team Chat", "Jira Board") or re.match(r"^\d+ engineers", l): 
            if l in ("Edit Group", "Add Team"): team = None
            continue
        if section is None: continue   # team description line
        if l == "Unspecified": continue
        name, code = split_code(l)
        name = re.sub(r"\s*\([^)]*\)", "", name).strip()   # drop nicknames in parentheses
        rows.append({"group": group, "team": team, "section": section, "name": name, "code": code})
    return rows, counts
if __name__ == "__main__":
    rows, counts = parse(open(sys.argv[1]).read())
    json.dump({"rows": rows, "printed_counts": counts}, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
    import collections
    for c in counts: print(c["group"], "|", c["line"])
    for k, v in collections.Counter((r["group"], r["team"]) for r in rows).items(): print(k, v)
