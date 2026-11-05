#!/usr/bin/env python3
"""daily-update doc tool. The agent decides the words; this writes them in the skill's exact layout.

Every write re-reads the doc, sends the revision it read (a doc changed by someone else is refused, then
retried up to 3 times), restores date headings, makes Confidence a chip, and prints the re-read text.
Nothing here messages anyone except `send --confirmed`, which the agent runs only after the person said "send".

  du.py setup STRUCTURE.json                 create the doc; prints its id
  du.py section DOC TAB_TITLE SECTION.json   write today's section on one initiative tab
  du.py headline DOC AREA_TITLE "<status> · <sentences> (<Weekday Mon D>)"
  du.py row DOC AREA_TITLE ROW.json          set one Initiatives-table row (["name","owner","status","milestone"])
  du.py sweep DOC YYYY-MM-DD OWNER [--publish] [--decide "Name=red|done" ...]
  du.py overview DOC YYYY-MM-DD "4:00 PM ET" [--publish]
  du.py thirty DOC BULLETS.json              In 30 seconds: [["🟡","<Tab title>","rest"], ...]
  du.py decisions DOC READER ROWS.json [LINKS.json]
  du.py archive DOC TAB_TITLE "done Mon Nov 9"
  du.py send DOC [--confirmed]               draft the reader summary; --confirmed sends it
  du.py settings DOC [--owner NAME] [--readers JSON] [--people JSON]   show or set settings stored on the doc
  du.py check DOC YYYY-MM-DD                 rule and reader checks on the doc

SECTION.json: {"date": "YYYY-MM-DD", "status": "🟡", "milestone": "...", "confidence": "Slightly confident",
  "progress": "... (Jira COM-994).", "blocked": "None.", "green_when": "...", "extra": ["Updated by X for Y."],
  "links": [["Jira COM-994", "https://..."]], "author": "Kyle", "cover_for": null}
  A line drawn only from email, chat or meeting notes ends "(email)", "(chat)" or "(meeting notes)" with no link.
STRUCTURE.json: {"org": "Automation", "owner": "Scott", "reader": "Medhat", "date": "YYYY-MM-DD",
  "areas": [{"name": "Composer", "owner": "Kyle", "initiatives": [
    {"name": "Composer Evals", "owner": "Goldberg", "updater": "Kyle", "status": "🟡",
     "milestone": "...", "progress": "... (Jira COM-994).", "link": ["Jira COM-994", "https://..."],
     "extra": ["Green when: ..."]}]}]}
  For several links on one Progress line, use "links": [["word", "https://..."], ...] instead of "link".
  An initiative with no source leaves out "progress" and "link": its section gets no Progress line.
  Setup adds the "Starting section drafted by" line itself; do not put it in "extra".
  Status may be the bare emoji ("🟡"); the scripts write the full form ("🟡 At risk").
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dudoc as du  # noqa: E402
import modes as m  # noqa: E402


def load(arg):
    return json.load(sys.stdin) if arg == "-" else json.load(open(arg))


def run(script, *args):
    return subprocess.call([sys.executable, os.path.join(HERE, script), *args])


def tab_of(doc_id, title):
    doc = du.read_doc(doc_id)
    for t, _ in du.all_tabs(doc):
        if t["tabProperties"]["title"] == title:
            return t["tabProperties"]["tabId"]
    raise SystemExit(f"No tab titled {title!r}. Titles: {[t['tabProperties']['title'] for t, _ in du.all_tabs(doc)]}")


def cmd_setup(a):
    import build
    s = load(a[0])
    structure = [(ar["name"], ar["owner"],
                  [(i["name"], i["owner"], i.get("updater", ar["owner"]), i["status"],
                    re.sub(r"(?i)no date set yet", "No date set yet", i["milestone"]), i.get("progress"),
                    i.get("links") or ([i["link"]] if i.get("link") else []), None, i.get("extra", []))
                   for i in ar["initiatives"]])
                 for ar in s["areas"]]
    title = s.get("title") or f"{s['org']} daily update"
    did = build.create(title, s["org"], s["owner"], s["reader"], structure, dt.date.fromisoformat(s["date"]))
    du.settings_set(did, owner=s["owner"], readers=s.get("readers", []), people=s.get("people", {}))
    from zoneinfo import ZoneInfo
    now = dt.datetime.now(ZoneInfo("America/New_York")).strftime("%-I:%M %p ET")
    subprocess.call([sys.executable, os.path.join(HERE, "overview.py"), did, s["date"], now, "--publish"],
                    stdout=subprocess.DEVNULL)
    print(did)


def cmd_section(a):
    doc_id, title, spec = a[0], a[1], load(a[2])
    day = dt.date.fromisoformat(spec["date"])
    lines = [du.label(day, True), du.STATUSES[spec["status"]], f"Next milestone: {spec['milestone']}",
             f"Confidence: {spec.get('confidence', du.DEFAULT_CONF[spec['status']])}"]
    if spec.get("progress"):
        lines.append(f"Progress: {spec['progress']}")
    lines.append(f"Blocked on: {spec.get('blocked') or 'None.'}")
    if spec["status"] != "🟢" and spec.get("green_when"):
        lines.append(f"Green when: {spec['green_when']}")
    lines += spec.get("extra", [])
    prog_k = next((k for k, x in enumerate(lines) if x.startswith("Progress:")), None)
    links = [(prog_k, w, u) for w, u in spec.get("links", [])] if prog_k is not None else []
    tid = tab_of(doc_id, title)
    for attempt in range(3):
        try:
            m.write_section(doc_id, tid, lines, links)
            break
        except RuntimeError as e:
            if "revision" not in str(e).lower() or attempt == 2:
                raise
            print(f"doc changed since read; retrying ({attempt + 1})")
    du.repair_headings(doc_id)
    init = next(i for i in du.model(du.read_doc(doc_id))[2] if i.tab_id == tid)
    s = init.sections[0]
    print(("LANDED " if s.date == day else "DID NOT LAND ") + title)
    for t, _ in s.lines:
        print("  " + t)


def cmd_headline(a):
    import build
    build.set_headline(a[0], a[1], a[2])
    print("HEADLINE " + (du.model(du.read_doc(a[0]))[1][a[1]].headline or ""))


def cmd_row(a):
    doc_id, area_title, vals = a[0], a[1], load(a[2])
    vals[2] = du.STATUSES.get(vals[2].strip(), vals[2])  # a bare "🟡" becomes "🟡 At risk"
    vals[3] = re.sub(r"(?i)no date set yet", "No date set yet", vals[3])
    m.set_row(doc_id, tab_of(doc_id, area_title), vals[0], vals)
    print("ROW", du.model(du.read_doc(doc_id))[1][area_title].rows())


def cmd_thirty(a):
    import build
    build.set_thirty_seconds(a[0], load(a[1]))
    print("In 30 seconds written")


def cmd_decisions(a):
    import build
    build.set_decisions(a[0], a[1], load(a[2]), load(a[3]) if len(a) > 3 else ())
    print("Needs decision written")


def cmd_archive(a):
    m.archive(a[0], a[1], a[2])
    print("ARCHIVED " + a[1])


def cmd_send(a):
    import send
    doc_id = a[0]
    st = du.settings_get(doc_id)
    readers = st["readers"]
    if not readers:
        raise SystemExit("No readers set. Run: du.py settings DOC --readers '[{\"name\":..,\"email\":..,\"channel\":\"email\"}]'")
    text = send.draft(doc_id, readers)
    subject, body = text[0], "\n".join(text[2:])
    print("RECIPIENTS: " + ", ".join(f"{r['name']} <{r['email']}> by {r['channel']}" for r in readers))
    print("SUBJECT: " + subject)
    print("BODY:\n" + body)
    if "--confirmed" not in a:
        print("\nNot sent. Run again with --confirmed only after the person replies \"send\".")
        return
    me = du.gws("gmail", "users", "getProfile", "--params", json.dumps({"userId": "me"})).get("emailAddress", "")
    if st["owner"] and me and not me.lower().startswith(st["owner"].split()[0].lower()):
        body += f"\n\nSent by {me} for {st['owner']}."
    import base64
    from email.message import EmailMessage
    for r in readers:
        if r["channel"] != "email":
            print(f"SKIPPED {r['name']}: channel {r['channel']} not supported by this tool yet; send by hand.")
            continue
        msg = EmailMessage()
        msg["To"], msg["Subject"] = r["email"], subject
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        du.gws("gmail", "users", "messages", "send", "--params", json.dumps({"userId": "me"}), body={"raw": raw})
        print(f"SENT to {r['name']} <{r['email']}>")


def cmd_settings(a):
    doc_id = a[0]
    kw = {}
    rest = a[1:]
    for flag, key, parse in (("--owner", "owner", str), ("--readers", "readers", json.loads), ("--people", "people", json.loads)):
        if flag in rest:
            kw[key] = parse(rest[rest.index(flag) + 1])
    print(json.dumps(du.settings_set(doc_id, **kw) if kw else du.settings_get(doc_id), indent=1))


def cmd_check(a):
    doc_id, day = a[0], a[1]
    started = (dt.datetime.utcnow() - dt.timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r1 = run("verify.py", doc_id, day, "--since", day, "--started", started)
    r2 = run("usability.py", doc_id, day, "--since", day)
    sys.exit(1 if (r1 or r2) else 0)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd, a = sys.argv[1], sys.argv[2:]
    if a and a[0] in du.PROTECTED and cmd not in ("check", "settings"):
        raise SystemExit(f"REFUSED: {du.PROTECTED[a[0]]} is protected while the skill is in testing. Nothing written.")
    if cmd == "sweep":
        sys.exit(run("sweep.py", a[0], a[1], "--owner", *a[2:]))
    if cmd == "overview":
        sys.exit(run("overview.py", *a))
    fn = globals().get(f"cmd_{cmd}")
    if not fn:
        raise SystemExit(f"Unknown command {cmd!r}. Run du.py help.")
    fn(a)


if __name__ == "__main__":
    main()
