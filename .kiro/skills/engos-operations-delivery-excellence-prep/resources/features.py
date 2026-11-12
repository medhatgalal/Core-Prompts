#!/usr/bin/env python3
"""Step 4 of the prep: flag feature cards and merge them into audit.py's findings.md and drafts.md.

The agent first fetches feature cards through the appian-home tools (they cannot be called from a script) and saves:
  <out>/<date>/feature_cards.json   one object per kept feature card: id, name, url, status, release, group,
                                    productOwnerId, initiativeJiraKey, updatedOn   (status/release as {"name"}/{"version"} or plain text)
  <out>/<date>/owners.json          {"<productOwnerId>": "<display name>"}
Then:  python3 features.py --date YYYY-MM-DD
Run it after audit.py (which rewrites drafts.md). It refuses to run twice on the same files.
Read-only toward Jira and Appian Home; writes only the two files above.
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, urllib.parse
import audit, settings

CFG = settings.load()
STALE_DAYS = 14
CAP = 5
MAP = {"Backlog": "To Do", "In Progress": "In Progress", "Merged": "Done", "Released": "Done"}


def name_of(v, key="name"):
    return v.get(key) or v.get("name") or v.get("version") if isinstance(v, dict) else v


def jira_status(keys):
    out = {}
    keys = sorted(set(keys))
    for i in range(0, len(keys), 40):
        chunk = keys[i:i + 40]
        try:
            for x in audit.jql(f'key in ({",".join(chunk)})'):
                out[x["key"]] = (x["fields"]["status"]["statusCategory"]["name"], x["fields"].get("updated"))
        except Exception:
            for k in chunk:  # one missing key fails the whole query; ask one at a time
                try:
                    for x in audit.jql(f"key = {k}"):
                        out[x["key"]] = (x["fields"]["status"]["statusCategory"]["name"], x["fields"].get("updated"))
                except Exception:
                    pass
    for k in keys:  # the API search cannot see some projects; acli can. Only after both fail is an item "not found".
        if k in out:
            continue
        p = subprocess.run(["acli", "jira", "workitem", "view", k, "--json", "--fields", "key,summary,status,updated"],
                           capture_output=True, text=True)
        try:
            f = json.loads(p.stdout)["fields"]
            out[k] = (f["status"]["statusCategory"]["name"], f.get("updated"))
        except Exception:
            pass
    return out


def flag(cards, owners):
    today = dt.datetime.now(dt.timezone.utc)
    jira = jira_status([c["initiativeJiraKey"] for c in cards if c.get("initiativeJiraKey")])
    group_owner = CFG["group_owners"]
    rows = []
    for c in cards:
        st = name_of(c.get("status")) or "Backlog"
        issues, actions = [], []
        k = c.get("initiativeJiraKey")
        if not k:
            issues.append("no Jira link"); actions.append("link the feature card to its Jira initiative")
        elif k not in jira:
            issues.append(f"linked Jira item {k} not found"); actions.append(f"make the feature card status and {k} agree")
        elif MAP.get(st) != jira[k][0]:
            issues.append(f"feature card says {st}, {k} is {jira[k][0]}"); actions.append(f"make the feature card status and {k} agree")
        age = (today - dt.datetime.fromisoformat(c["updatedOn"].replace("Z", "+00:00"))).days if c.get("updatedOn") else None
        # Stale checks do not apply to Released or Backlog feature cards (nothing to update yet or any more), nor to an
        # In Progress feature card whose linked Jira item is In Progress and was updated within the window: the work is
        # moving, and the feature card's own edit date says little.
        moving = False
        if k in jira and jira[k][0] == "In Progress" and jira[k][1]:
            moving = (today - dt.datetime.fromisoformat(jira[k][1].replace("Z", "+00:00"))).days < STALE_DAYS
        if age is not None and age >= STALE_DAYS and st not in ("Released", "Backlog") and not moving:
            issues.append(f"no update in {age} days"); actions.append("update the feature card")
        if not issues:
            continue
        o = owners.get(str(c.get("productOwnerId")))
        star = ""
        if not o:
            o, star = group_owner.get(c["group"].lower(), f"Unassigned ({c['group']})"), "*"
        rows.append({"owner": o + star, "base": o, "name": c["name"], "url": c["url"], "state": st, "issues": issues, "actions": actions})
    return rows


def short(t, n=70):
    return t if len(t) <= n else t[:n - 1].rstrip() + "…"


def bullet(r):
    return f"- [{short(r['name'])}]({r['url']}): {', '.join(r['issues'])}. Please {' and '.join(dict.fromkeys(r['actions']))}."


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date", required=True); a = ap.parse_args()
    d = os.path.join(settings.OUT, a.date)
    cards = json.load(open(os.path.join(d, "feature_cards.json")))
    owners = json.load(open(os.path.join(d, "owners.json")))
    fp, dp = os.path.join(d, "findings.md"), os.path.join(d, "drafts.md")
    f, dr = open(fp).read(), open(dp).read()
    if "## Feature cards" in f:
        sys.exit("findings.md already has a Feature cards section. Re-run audit.py first, then this.")
    rows = flag(cards, owners)
    counts = {}
    for c in cards:
        counts[c["group"]] = counts.get(c["group"], 0) + 1
    nolink = sum("no Jira link" in r["issues"] for r in rows)
    dis = sum(any("feature card says" in i or "not found" in i for i in r["issues"]) for r in rows)
    stale = sum(any("no update in" in i for i in r["issues"]) for r in rows)
    rel = ", ".join(CFG["feature_card_releases"])
    sec = [f"\n## Feature cards ({rel})", f"- feature cards checked: {len(cards)} (" + ", ".join(f"{g} {n}" for g, n in sorted(counts.items())) + ")",
           f"- no Jira link: {nolink}", f"- status disagrees with Jira: {dis}", f"- no update in {STALE_DAYS}+ days: {stale}", "",
           "| Area | Owner | Item | State | Issue |", "|---|---|---|---|---|"]
    for r in rows:
        for i in r["issues"]:
            sec.append(f"| Feature card | {r['owner']} | [{r['name']}]({r['url']}) | {r['state']} | {i} |")
    open(fp, "w").write(f.rstrip("\n") + "\n" + "\n".join(sec) + "\n")
    # drafts: group by owner, add to the owner's section or start a new one
    intro = re.search(r"^Ahead of .*?:$", dr, re.M)
    intro = intro.group(0) if intro else "Ahead of the Delivery Checkpoint, please take care of these:"
    by = {}
    for r in rows:
        by.setdefault(r["owner"], []).append(r)
    parts = re.split(r"(?m)^(?=## @)", dr)
    head, secs = parts[0], parts[1:]
    for o, rs in by.items():
        base = re.sub(r"\*$", "", o)
        idx = next((i for i, s in enumerate(secs) if re.match(r"## @" + re.escape(base) + r"( \(|\*? \()", s)), None)
        if idx is None:
            secs.append(f"## @{o} (0 items)\n\n{intro}\n\n"); idx = len(secs) - 1
        s = secs[idx]
        m = re.match(r"## @(.+?) \((\d+) items?\)", s)
        n = int(m.group(2)) + len(rs)
        lines = s.rstrip("\n").split("\n")
        body = [l for l in lines[1:] if l.startswith("- ")]
        room = max(0, CAP - len(body))
        add, over = rs[:room], rs[room:]
        pre = [l for l in lines[1:] if not l.startswith("- ")]
        new_b = body + [bullet(r) for r in add]
        if over:
            new_b.append(f"- {len(over)} more feature cards that need a Jira link, a status fix, or an update: " + ", ".join(r["name"] for r in over))
        secs[idx] = f"## @{m.group(1)} ({n} item{'s' if n != 1 else ''})\n" + "\n".join(pre).rstrip("\n") + "\n\n" + "\n".join(new_b) + "\n\n"
    open(dp, "w").write(head + "".join(secs))
    print(f"feature cards checked {len(cards)}; flagged {len(rows)} (no link {nolink}, disagree {dis}, stale {stale}); {len(by)} owners touched")


if __name__ == "__main__":
    main()
