#!/usr/bin/env python3
"""daily-update doc tool. The agent decides the words; this writes them in the skill's exact layout.

    du.py <noun> <verb> [args] [--doc ID] [--json] [--dry-run] [--for-owner]

Run `du.py --help`, or `du.py <noun> --help`, for the verbs. The grammar lives in cli.py; this file holds the
engine each verb calls. Every write re-reads the doc, sends the revision it read (a doc changed by someone else
is refused, then retried up to 3 times), restores date headings, and prints the re-read text. Writes take
--dry-run: they print the PLAN and write nothing, so the agent can show it and wait for "publish".
Nothing here messages anyone except `day send --confirmed`, run only after the person said "send".

  doc        create STRUCTURE.json | show | sync
  area       list | show | add | rename | set-owner | set-headline | merge | remove
  initiative list | show | add | rename | move | set-owner | set-updater | add-backup | remove-backup
             pause | resume | done | stop | reopen | archive
  person     list | show | set-email
  reader     list | add | remove | set-channel
  source     list | add | remove                    (yours, local, never on the doc)
  section    write TAB FILE | show TAB DATE | lint TAB FILE
  day        sweep | overview | decisions | send    (doc owner, 3pm close-out)
  discover   check FILE
  doctor     [--local | --only-doc]     (read only; names the fix for each problem)

Initiative lifecycle:  open -> paused -> open;  open|paused -> done|stopped;  done|stopped -> open (reopen)
or -> archived (terminal). Archive is normally proposed by `day overview`; the doc owner approves it.

SECTION.json: {"date": "YYYY-MM-DD", "status": "🟡", "milestone": "...",
  "progress": "... (Jira COM-994).", "blocked": "None.", "green_when": "...", "extra": [],
  "links": [["Jira COM-994", "https://..."]], "author": "Kyle", "cover_for": null}
  Links go on the Progress or Blocked on line that cites them. When "author" is not the tab's updater, set
  "cover_for" to the updater; the "Updated by <author> for <updater>." line is added for you.
  A line drawn only from email, chat or meeting notes ends "(email)", "(chat)" or "(meeting notes)" with no link.
INIT.json (initiative add): SECTION.json plus "name", "owner", optional "updater" (default the area owner).
STRUCTURE.json (doc create): {"org": "Automation", "owner": "Scott", "reader": "Medhat", "date": "YYYY-MM-DD",
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
    title = s.get("title") or f"{s['org']} Daily Updates"
    did = build.create(title, s["org"], s["owner"], s["reader"], structure, dt.date.fromisoformat(s["date"]))
    du.settings_set(did, owner=s["owner"], readers=s.get("readers", []), people=s.get("people", {}))
    from zoneinfo import ZoneInfo
    now = dt.datetime.now(ZoneInfo("America/New_York")).strftime("%-I:%M %p ET")
    subprocess.call([sys.executable, os.path.join(HERE, "overview.py"), did, s["date"], now, "--publish"],
                    stdout=subprocess.DEVNULL)
    print(did)


def _review(doc_id, title, spec):
    """Build the section and run the skill's checks against the tab's previous section (read only)."""
    import daily
    lines, links = section_lines(spec)
    tid = tab_of(doc_id, title)
    init = next(i for i in du.model(du.read_doc(doc_id))[2] if i.tab_id == tid)
    day = dt.date.fromisoformat(spec["date"])
    prev = next((x for x in init.sections if x.date < day), None)
    author, cover = spec.get("author"), spec.get("cover_for")
    if author and author != init.updater:
        if cover != init.updater:
            raise SystemExit(f"REFUSED: {author} is not the updater of {title} ({init.updater} is). "
                             f"Set \"cover_for\": \"{init.updater}\" only if they asked to cover it. Nothing written.")
        line = f"Updated by {author} for {init.updater}."
        if line not in lines:
            lines.append(line)
    body = lines[1:]
    _, areas, inits = du.model(du.read_doc(doc_id))
    people = {p for i in inits for p in (i.owner, i.updater) if p} | {a.owner for a in areas.values() if a.owner}
    probs = daily.checks(body, [(k - 1, w, u) for k, w, u in links], known_names=sorted(people), prev=prev)
    return tid, lines, links, probs


def cmd_lint(a):
    """The pre-publish check, read only: prints warnings (shown in the review) and problems that block."""
    doc_id, title, spec = a[0], a[1], load(a[2])
    _, lines, _, probs = _review(doc_id, title, spec)
    print("\n".join("  " + x for x in lines))
    for p in probs:
        print(("WARN  " + p[len("warn: "):]) if p.startswith("warn:") else ("BLOCK " + p))
    print("OK: nothing blocks publishing." if not [p for p in probs if not p.startswith("warn:")] else
          "NOT READY: fix the BLOCK lines before publishing.")


def cmd_section(a):
    doc_id, title, spec = a[0], a[1], load(a[2])
    day = dt.date.fromisoformat(spec["date"])
    tid, lines, links, probs = _review(doc_id, title, spec)
    hard = [p for p in probs if not p.startswith("warn:")]
    if hard:
        raise SystemExit("REFUSED: " + "; ".join(hard) + ". Nothing written.")
    for p in probs:
        print("WARN " + p[len("warn: "):])
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


def cmd_today(a):
    """Daily step 1 on a same-day re-run: today's published section, links included, as the starting draft."""
    doc_id, title, day = a[0], a[1], dt.date.fromisoformat(a[2])
    tid = tab_of(doc_id, title)
    init = next(i for i in du.model(du.read_doc(doc_id))[2] if i.tab_id == tid)
    s = next((x for x in init.sections if x.date == day), None)
    if s is None:
        print(json.dumps(None))
        return
    keys = {"Next milestone:": "milestone", "Progress:": "progress", "Blocked on:": "blocked", "Green when:": "green_when"}
    out = {"date": day.isoformat(), "status": s.status, "extra": [], "links": []}
    for t, el in s.lines:
        k = next((p for p in keys if t.startswith(p)), None)
        if k:
            out[keys[k]] = t[len(k):].strip()
            if k in ("Progress:", "Blocked on:"):
                out["links"] += [[r["textRun"]["content"], r["textRun"]["textStyle"]["link"]["url"]]
                                 for r in el["paragraph"]["elements"] if r.get("textRun", {}).get("textStyle", {}).get("link")]
        elif t[:1] not in du.STATUSES and not t.startswith("Confidence:"):
            out["extra"].append(t)
    print(json.dumps(out, ensure_ascii=False, indent=1))


def section_lines(spec):
    """SECTION.json -> (lines starting with the date heading, links as (line_no, word, url)).
    Each link goes on the Progress or Blocked on line that cites its word, "(Jira COM-994)", else that names it."""
    day = dt.date.fromisoformat(spec["date"])
    lines = [du.label(day, True), du.STATUSES[spec["status"]], f"Next milestone: {spec['milestone']}"]
    if spec.get("progress"):
        lines.append(f"Progress: {spec['progress']}")
    lines.append(f"Blocked on: {spec.get('blocked') or 'None.'}")
    if spec["status"] != "🟢" and spec.get("green_when"):
        lines.append(f"Green when: {spec['green_when']}")
    lines += spec.get("extra", [])
    cand = [k for k, x in enumerate(lines) if x.startswith(("Progress:", "Blocked on:"))]
    links, used = [], set()
    for w, u in spec.get("links", []):
        k = next((k for k in cand if f"({w})" in lines[k] and (k, w) not in used), None)
        if k is None:
            k = next((k for k in cand if w in lines[k] and (k, w) not in used), None)
        if k is not None:
            used.add((k, w))
            links.append((k, w, u))
    return lines, links


def cmd_add(a):
    """Add steps 2-5: refuse a similar name unless --new, then the tab, its first section and the area row.
    INIT.json: SECTION.json plus "name", "owner", optional "updater" (default the area owner) and "author"."""
    doc_id, area_title, spec = a[0], a[1], load(a[2])
    doc = du.read_doc(doc_id)
    area = du.model(doc)[1].get(area_title)
    if area is None:
        raise SystemExit(f"REFUSED: no area tab {area_title!r}. A new area is the doc owner's call. Nothing written.")
    near = [t for t in m.similar(doc, spec["name"]) if t != area_title]
    if near and "--new" not in a:
        raise SystemExit(f"REFUSED: similar tabs exist: {near}. Ask the person; rerun with --new only if it is different.")
    spec["milestone"] = re.sub(r"(?i)no date set yet", "No date set yet", spec["milestone"])
    if spec.get("author") and spec["author"] != spec["owner"]:
        spec.setdefault("extra", []).append(f"Added by {spec['author']} for {spec['owner']}.")
    lines, links = section_lines(spec)
    tid = m.add_initiative(doc_id, area.tab_id, spec["name"], spec["owner"], spec.get("updater") or area.owner,
                           area.name, lines, links)
    m.set_row(doc_id, area.tab_id, spec["name"], [spec["name"], spec["owner"], du.STATUSES[spec["status"]], spec["milestone"]])
    du.repair_headings(doc_id)
    init = next(i for i in du.model(du.read_doc(doc_id))[2] if i.tab_id == tid)
    print(("ADDED " if init.sections else "DID NOT LAND ") + init.title)
    for t, _ in (init.sections[0].lines if init.sections else []):
        print("  " + t)


def cmd_dedupe(a):
    """Discover step 2, read only. CANDIDATES.json: [{"name", "links": [urls], "sources": {"jira": [...], ...}}]."""
    import verify
    doc_id, cands = a[0], load(a[1])
    cfg_path = a[2] if len(a) > 2 else os.path.expanduser("~/.daily-update/config.json")
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
    doc = du.read_doc(doc_id)
    _, _, inits = du.model(doc)
    archive = next((t for t, p in du.all_tabs(doc) if p is None and t["tabProperties"]["title"].startswith("Archive")), None)
    archived = [du.Initiative(c, archive) for c in archive.get("childTabs", [])] if archive else []

    def tab_links(i):
        return {u for _, u in verify.links_in(i.body)}

    def norm(v):
        return str(v).strip().lower()
    saved = {t.get("name"): {norm(v) for vs in t.get("sources", {}).values() for v in vs} for t in cfg.get("tabs", [])}
    for c in cands:
        want = {norm(v) for vs in c.get("sources", {}).values() for v in vs}
        links = set(c.get("links", []))
        words = {w.lower() for w in re.findall(r"\w{4,}", c["name"])} - {"composer", "agent", "agents"}

        def same(i):
            return words & {w.lower() for w in re.findall(r"\w{4,}", i.name)}
        hit = next((i for i in inits if want & saved.get(i.name, set())), None)
        if hit:
            verdict = f"already covered: a saved source of {hit.title}"
        else:
            hit = next((i for i in inits if same(i) or links & tab_links(i)), None)
            arch = next((i for i in archived if same(i) or links & tab_links(i)), None)
            verdict = (f"add as a source to {hit.title}" if hit else
                       f"drop: in Archive ({arch.title})" if arch else "new")
        print(json.dumps({"name": c["name"], "verdict": verdict}, ensure_ascii=False))


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


def cmd_decisions(a):
    import build
    build.set_decisions(a[0], a[1], load(a[2]), load(a[3]) if len(a) > 3 else ())
    print("Decisions table written")


def cmd_archive(a):
    m.archive(a[0], a[1], a[2])
    print("ARCHIVED " + a[1])


def cmd_send(a):
    import send
    doc_id = a[0]
    st = du.settings_get(doc_id)
    readers = st["readers"]
    if not readers:
        raise SystemExit("No readers set. Run: du.py reader add NAME EMAIL --channel email")
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


def cmd_sync(a):
    import backup
    print(backup.report(backup.sync()))


def main():
    import cli
    cli.main()


if __name__ == "__main__":
    main()
