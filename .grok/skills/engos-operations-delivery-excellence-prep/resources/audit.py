#!/usr/bin/env python3
"""Read-only pre-checkpoint audit for the Delivery Checkpoint.

Checks Goals, Jira, the Delivery Excellence doc's open comments, the Upcoming
Features sheet and the checkpoint invite. Writes findings.json, findings.md and
drafts.md (one draft comment per owner) under out/<date>/. Posts nothing.

Feature cards are checked separately by the scheduled task through the
appian-home MCP, which this script cannot call.

  python3 audit.py --date 2026-11-12
"""
import argparse, base64, datetime as dt, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from http.client import HTTPException  # not "import http.client": the http() function below would shadow it

HERE = os.path.dirname(os.path.abspath(__file__))
import settings
CFG = settings.load()
SITE = CFG["jira_site"]
CONTAINER = CFG["goals_container"]
ROOT_GOAL = CFG["goals_root"]
JIRA_FILTER = CFG["jira_filter"]
FEATURES_SHEET = CFG["features_sheet"]
STALE_DAYS = 14
NOW = dt.datetime.now(dt.timezone.utc)
DONE_GOAL = {"Completed 🎉", "Cancelled", "Archived", "Done"}
GROUP_FIELD = CFG["group_field"]  # Jira "Group"
# Unassigned epics go to the group's Delivery Goals owner
GROUP_OWNER = CFG["group_owners"]  # in settings.json
CURRENT_RELEASE = tuple(CFG["current_release"])  # epics named for an earlier release are treated as shipped
CATEGORY_FIELD = CFG["category_field"]  # Jira "Work Category"
STANDING = set(CFG["standing_work_categories"])
STANDING_NAME = re.compile(CFG["standing_name_pattern"], re.I)  # generic words kept from the original rule
def standing(f):
    return ((f.get(CATEGORY_FIELD) or {}).get("value")) in STANDING or bool(STANDING_NAME.search(f["summary"]))  # epics in these categories never close; staleness says little
MAX_ITEMS = 5  # per draft comment; the rest are listed by key


def secrets():
    out = subprocess.run(["zsh", "-c", "source ~/.secrets.env >/dev/null 2>&1; print -rn -- $JIRA_EMAIL; print -rn -- '\t'; print -rn -- $JIRA_TOKEN"],
                         capture_output=True, text=True).stdout
    email, token = out.split("\t", 1)
    return "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()


AUTH = secrets()


def http(url, body=None, headers=None):
    h = {"Authorization": AUTH, "Accept": "application/json", "Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=h)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == 5:
                raise
            time.sleep(int(e.headers.get("Retry-After") or 0) or 2 ** (attempt + 1))
        except (urllib.error.URLError, ConnectionError, TimeoutError, HTTPException):
            # dropped connection or timeout: retry with backoff
            if attempt == 5:
                raise
            time.sleep(2 ** (attempt + 1))


def gws(*args):
    r = subprocess.run(["gws", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"gws {' '.join(args[:3])} failed: {r.stderr[-300:]}")
    return json.loads(r.stdout[r.stdout.index("{"):])


def age_days(iso):
    return (NOW - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))).days if iso else None


# ---------- Goals ----------
GOAL_Q = """query Goal($c: ID!, $k: String!) { goals_byKey(containerId: $c, goalKey: $k) @optIn(to: "Townsquare") {
  key name url state { label } owner { name } latestUpdateDate
  targetDate { dateRange { end } }
  subGoals(first: 50) { edges { node { key } } } } }"""


def goal(key):
    d = http(f"{SITE}/gateway/api/graphql", {"operationName": "Goal", "query": GOAL_Q, "variables": {"c": CONTAINER, "k": key}},
             {"X-ExperimentalApi": "Townsquare"})
    if d.get("errors"):
        raise RuntimeError(f"Goals API error on {key}: {d['errors'][0]['message'][:200]}")
    return d["data"]["goals_byKey"]


def fetch_goals(cache):
    """Walk the goal tree (about 12 minutes because of rate limits). Reuses cache if given and present."""
    if cache and os.path.exists(cache):
        return json.load(open(cache))
    raw, todo = [], [ROOT_GOAL]
    while todo:
        g = goal(todo.pop())
        raw.append(g)
        print(f"  goal {len(raw)}: {g['key']} ({len(todo)} queued)", file=sys.stderr, flush=True)
        todo += [e["node"]["key"] for e in g["subGoals"]["edges"]]
    if cache:
        json.dump(raw, open(cache, "w"))
    return raw


def audit_goals(cache):
    raw = fetch_goals(cache)
    findings = []
    for g in raw:
        state = g["state"]["label"]
        # Pending = not started yet; missing dates/updates are expected there
        if state in DONE_GOAL or state == "Pending":
            continue
        owner = (g.get("owner") or {}).get("name") or "No owner"
        base = {"area": "Goals", "owner": owner, "item": f"{g['key']} {g['name']}", "link": g["url"], "state": state}
        age = age_days(g.get("latestUpdateDate"))
        if age is None:
            findings.append({**base, "age": 999, "issue": "no status update ever posted", "action": "post a status update"})
        elif age > STALE_DAYS:
            findings.append({**base, "age": age, "issue": f"last update {age} days ago", "action": "post a status update"})
        if state in ("Off track", "At risk"):
            findings.append({**base, "age": age or 0, "issue": f"marked {state}", "action": "add the recovery plan to the update"})
        end = ((g.get("targetDate") or {}).get("dateRange") or {}).get("end")
        if not end:
            findings.append({**base, "age": age or 0, "issue": "no target date", "action": "add a target date"})
        elif age_days(end) > 0:
            findings.append({**base, "age": age or 0, "issue": f"target date {end[:10]} has passed",
                             "action": "move the target date or mark it complete"})
        if owner == "No owner":
            findings.append({**base, "age": age or 0, "issue": "no owner", "action": "assign an owner"})
    return findings, len(raw)


# ---------- Jira ----------
def jql(q):
    issues, token = [], None
    while True:
        body = {"jql": q, "fields": ["summary", "status", "assignee", "updated", "issuetype", GROUP_FIELD, CATEGORY_FIELD], "maxResults": 100}
        if token:
            body["nextPageToken"] = token
        d = http(f"{SITE}/rest/api/3/search/jql", body)
        issues += d.get("issues", [])
        token = d.get("nextPageToken")
        if not token:
            return issues


def old_release(summary):
    """Release named in the summary (26.1, 25.4, 26C3) if it is before the current release."""
    m = re.search(r"\b(2\d)[.C](\d{1,2})\b", summary)
    if m and (int(m[1]), int(m[2])) < CURRENT_RELEASE:
        return f"{m[1]}.{m[2]}"
    return None


def area_owner(fields):
    group = ((fields.get(GROUP_FIELD) or {}).get("value") or "").strip().lower()
    return GROUP_OWNER.get(group, f"Unassigned (group: {group or 'none'})")


def audit_jira():
    findings, counts = [], {}
    q_parent = f"filter = {JIRA_FILTER} AND issuetype = Epic AND statusCategory = \"In Progress\" AND parent is EMPTY"
    q_stale = f"filter = {JIRA_FILTER} AND issuetype = Epic AND statusCategory = \"In Progress\" AND updated < -{STALE_DAYS}d"
    rows = {"parent": jql(q_parent), "stale": jql(q_stale)}
    counts["in-progress epics with no initiative"] = len(rows["parent"])
    skipped = 0
    for kind, issues in rows.items():
        for i in issues:
            f = i["fields"]
            assignee = (f.get("assignee") or {}).get("displayName")
            base = {"area": "Jira", "owner": assignee or area_owner(f), "unassigned": not assignee,
                    "item": f"{i['key']} {f['summary']}", "link": f"{SITE}/browse/{i['key']}",
                    "state": f["status"]["name"], "age": age_days(f["updated"])}
            if kind == "parent":
                if standing(f):
                    skipped += 1  # standing buckets have no initiative by design
                    continue
                findings.append({**base, "issue": "no parent initiative", "action": "link it to its initiative"})
                continue
            rel = old_release(f["summary"])
            if rel:
                findings.append({**base, "issue": f"named for release {rel}, which has shipped",
                                 "action": "close it if the work is done"})
            elif standing(f):
                skipped += 1  # standing support/bug/maintenance buckets never close; staleness says little
            else:
                findings.append({**base, "issue": f"no update in {base['age']} days",
                                 "action": "update the status, or close it if the work is done"})
    counts["stale epics (excluding standing buckets)"] = sum(1 for x in findings if "no update" in x["issue"])
    counts["old release epics still open"] = sum(1 for x in findings if "has shipped" in x["issue"])
    counts["standing bucket epics skipped"] = skipped
    return findings, counts


# ---------- Doc, sheet, invite ----------
def audit_doc():
    comments, token = [], None
    while True:  # page through all comments; one page holds at most 100
        p = {"fileId": CFG["doc_id"], "pageSize": 100,
             "fields": "nextPageToken,comments(id,author/displayName,createdTime,resolved,deleted,content)"}
        if token:
            p["pageToken"] = token
        d = gws("drive", "comments", "list", "--params", json.dumps(p))
        comments += d.get("comments", [])
        token = d.get("nextPageToken")
        if not token:
            break
    open_ = [c for c in comments if not c.get("resolved") and not c.get("deleted")]
    old = [c for c in open_ if age_days(c["createdTime"]) > STALE_DAYS]
    return [{"area": "Doc", "owner": c["author"]["displayName"], "item": c["content"][:120].replace("\n", " "),
             "link": f"https://docs.google.com/document/d/{CFG['doc_id']}/edit?disco={c['id']}",
             "state": "open", "issue": f"open comment, {age_days(c['createdTime'])} days old"} for c in old], len(open_)


def audit_sheet():
    d = gws("drive", "files", "get", "--params", json.dumps({"fileId": FEATURES_SHEET, "fields": "name,modifiedTime,lastModifyingUser/displayName", "supportsAllDrives": True}))
    age = age_days(d["modifiedTime"])
    f = []
    if age > STALE_DAYS:
        f.append({"area": "Upcoming Features", "owner": "What's Next owners", "item": d["name"],
                  "link": f"https://docs.google.com/spreadsheets/d/{FEATURES_SHEET}/edit", "state": "",
                  "issue": f"sheet not edited in {age} days"})
    return f, {"modified": d["modifiedTime"], "by": (d.get("lastModifyingUser") or {}).get("displayName")}


def owners():
    out = set()
    for s in CFG["sections"]:
        for g in s.get("groups", []) + [g for g in s.get("ops_groups", []) if isinstance(g, dict)]:
            out.update(g["owners"])
    return out


def audit_invite(date):
    start = f"{date}T00:00:00-05:00"
    end = (dt.date.fromisoformat(date) + dt.timedelta(days=1)).isoformat() + "T00:00:00-05:00"
    d = gws("calendar", "events", "list", "--params", json.dumps({
        "calendarId": "primary", "timeMin": start, "timeMax": end, "singleEvents": True, "q": CFG["checkpoint_title"]}))
    ev = next((e for e in d.get("items", []) if CFG["checkpoint_title"] in e.get("summary", "")), None)
    if not ev:
        return None, []
    invited = {a["email"].lower() for a in ev.get("attendees", [])}
    missing = sorted(owners() - invited)
    return ev, [{"area": "Invite", "owner": CFG["leader_name"], "item": m, "link": ev.get("htmlLink", ""), "state": "",
                 "issue": "section owner is not on the checkpoint invite"} for m in missing]


# ---------- Output ----------
def short(text, n=70):
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


def write(date, findings, meta):
    out = os.path.join(settings.OUT, date)
    os.makedirs(out, exist_ok=True)
    json.dump({"meta": meta, "findings": findings}, open(os.path.join(out, "findings.json"), "w"), indent=1)
    md = [f"# Delivery Checkpoint audit for {date}", "", f"Run {NOW:%Y-%m-%d %H:%M} UTC. Read-only.", ""]
    for k, v in meta.items():
        md.append(f"- {k}: {v}")
    md += ["", "| Area | Owner | Item | State | Issue |", "|---|---|---|---|---|"]
    for f in findings:
        md.append(f"| {f['area']} | {f['owner']} | [{f['item'][:80]}]({f['link']}) | {f['state']} | {f['issue']} |")
    open(os.path.join(out, "findings.md"), "w").write("\n".join(md) + "\n")
    # one entry per item per owner, combining every issue and action on it
    by = {}
    for f in findings:
        if f["area"] not in ("Goals", "Jira"):
            continue
        items = by.setdefault(f["owner"], {})
        e = items.setdefault(f["item"], {**f, "issues": [], "actions": []})
        e["age"] = max(e.get("age") or 0, f.get("age") or 0)
        if f["issue"] not in e["issues"]:
            e["issues"].append(f["issue"])
        if f["action"] not in e["actions"]:
            e["actions"].append(f["action"])
    deadline = (dt.date.fromisoformat(date) - dt.timedelta(days=1)).strftime("%A %b %-d")
    dr = [f"# Draft comments for {date} (NOT POSTED - {CFG["leader_name"]} approves each one)", ""]
    for who, items in sorted(by.items(), key=lambda kv: (kv[0].startswith("Unassigned"), kv[0])):
        rows = sorted(items.values(), key=lambda e: -(e["age"] or 0))
        dr += [f"## @{who} ({len(rows)} item{'s' if len(rows) != 1 else ''})", "",
               f"Ahead of Thursday's Delivery Checkpoint, please take care of these by COB {deadline}:", ""]
        for e in rows[:MAX_ITEMS]:
            star = "*" if e.get("unassigned") else ""
            act = " and ".join(e["actions"])
            dr.append(f"- [{short(e['item'])}]({e['link']}){star}: {', '.join(e['issues'])}. Please {act}.")
        rest = rows[MAX_ITEMS:]
        if rest:
            jira = [e["item"].split()[0] for e in rest if e["area"] == "Jira"]
            goals = [e["item"].split()[0] for e in rest if e["area"] == "Goals"]
            if goals:
                dr.append(f"- {len(goals)} more goal{'s' if len(goals) != 1 else ''} that need{'s' if len(goals) == 1 else ''} a status update or a new target date: {', '.join(goals)}")
            if jira:
                url = f"{SITE}/issues/?jql=" + urllib.parse.quote(f"key in ({','.join(jira)}) ORDER BY updated ASC")
                dr.append(f"- [{len(jira)} more epics]({url}) that need a status update, an initiative link, or closing")
        if any(e.get("unassigned") for e in rows):
            dr += ["", "* No assignee, so it came to you as the group owner."]
        dr.append("")
    open(os.path.join(out, "drafts.md"), "w").write("\n".join(dr) + "\n")
    return out


def drop_closed(findings):
    """Re-read each flagged Jira epic just before writing and drop any whose finding no longer holds:
    closed since the first read, or (for "no parent initiative") a parent has since been set."""
    jira = [x for x in findings if x["area"] == "Jira"]
    if not jira:
        return findings, 0
    key = lambda x: x["item"].split()[0]
    live = {i["key"] for i in jql(f'key in ({",".join(sorted({key(x) for x in jira}))}) AND statusCategory != Done')}
    pk = sorted({key(x) for x in jira if x["issue"] == "no parent initiative"})
    still_orphan = {i["key"] for i in jql(f'key in ({",".join(pk)}) AND parent is EMPTY')} if pk else set()
    ok = lambda x: key(x) in live and (x["issue"] != "no parent initiative" or key(x) in still_orphan)
    kept = [x for x in findings if x["area"] != "Jira" or ok(x)]
    return kept, len(findings) - len(kept)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="checkpoint date YYYY-MM-DD")
    ap.add_argument("--reuse-goals", action="store_true", help="reuse this date's cached goal tree instead of re-reading it")
    a = ap.parse_args()
    findings, meta = [], {}
    os.makedirs(os.path.join(settings.OUT, a.date), exist_ok=True)
    cache = os.path.join(settings.OUT, a.date, "goals_raw.json")
    if not a.reuse_goals and os.path.exists(cache):
        os.remove(cache)
    ev, inv = audit_invite(a.date)
    if not ev:
        sys.exit(f"No {CFG['checkpoint_title']} on {a.date}; nothing to audit.")
    meta["checkpoint"] = ev.get("summary")
    g, n = audit_goals(cache); findings += g; meta["goals checked"] = n
    j, c = audit_jira(); findings += j; meta.update({f"jira: {k}": v for k, v in c.items()})
    d, n = audit_doc(); findings += d; meta["open doc comments"] = n
    s, m = audit_sheet(); findings += s; meta["upcoming features sheet last edit"] = f"{m['modified'][:10]} by {m['by']}"
    findings += inv
    findings, closed = drop_closed(findings); meta["jira: closed since first read, dropped"] = closed
    out = write(a.date, findings, meta)
    print(f"{len(findings)} findings -> {out}")
    for k, v in meta.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
