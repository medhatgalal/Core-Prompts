"""Daily mode helpers: the skill's checks, permission rule, review and publish (test tooling).

The persona's agent drafts the section text; this module enforces what SKILL.md says must hold before
the review, and does step 6 on "publish".
"""
import datetime as dt
import json
import os
import re
from zoneinfo import ZoneInfo

import dudoc as du
import modes as m

ET = ZoneInfo("America/New_York")
LEDGER = os.path.join(os.environ.get("KIROCREW_SCRATCH", "/tmp"), "du-ledger")
SENSITIVE = re.compile(r"\b(interview\w*|candidate\w*|offer\w*|hire[ds]?|salary|comp|PTO|leave|sick|performance|promotion|PIP)\b", re.I)
VAGUE = re.compile(r"\b(this week|next week|soon|TBD|EOW|end of week|shortly|later this month)\b", re.I)
NAME = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")


def et_date(local_dt):
    """Skill: 'today' is the calendar date in US Eastern time, wherever the person is."""
    return local_dt.astimezone(ET).date()


MOVED = re.compile(r"\b(mov(e|ed|es|ing)|postpon\w*|push(ed)? (back|out|to)|delay\w*|slip\w*|reschedul\w*|now due)\b", re.I)


NOT_SENSITIVE = re.compile(r"\brelease candidates?\b|\bcandidate (cut|build|branch|list)\b|\boffers? (the|a|an|to)\b", re.I)
DATEISH = re.compile(r"\b(release|date|deadline|milestone|launch|ship\w*|freeze|cut|go-live)\b", re.I)


def _about_a_date(text, mv, milestone_day):
    """A 'moved' word is about timing when a later date or a timing word sits within 60 characters of it."""
    window = text[max(0, mv.start() - 60):mv.end() + 60]
    later = [d for _, d, ok in du.dates_in(window) if ok and d and milestone_day and d > milestone_day]
    return bool(later or DATEISH.search(window))


def checks(lines, links, known_names=(), prev=None):
    """The skill's 'Checks before any review' for one drafted section.
    Returns problems. A problem starting "warn:" is shown in the review before "Publish?" and does not block;
    every other problem blocks the write. `prev` is the tab's previous Section, for the stale-date check."""
    probs = []
    status = next((l[:1] for l in lines if l[:1] in du.STATUSES), None)
    ms = next((l for l in lines if l.startswith("Next milestone:")), None)
    ms_text = ms[len("Next milestone:"):].strip() if ms else None
    prog = next((l for l in lines if l.startswith("Progress:")), "")
    body = " ".join(lines)
    for l in lines:
        for sent in re.split(r"(?<=[.;])\s+", l):
            plain = NOT_SENSITIVE.sub("", sent)
            if not SENSITIVE.search(plain):
                continue
            if any(re.search(rf"\b{re.escape(n)}\b", plain) for n in known_names):
                probs.append(f"people-sensitive: '{sent}'")  # a person in the doc next to a sensitive word
            elif NAME.search(plain):
                probs.append(f"warn: check for people-sensitive detail: '{sent[:90]}'")
    if VAGUE.search(body):
        probs.append(f"vague date: '{VAGUE.search(body).group(0)}'")
    for mtxt, d, ok in du.dates_in(body):
        if not ok:
            probs.append(f"weekday wrong: '{mtxt}' is a {du.WD[d.weekday()] if d else 'not a real date'}")
    if any(l.startswith("Confidence:") for l in lines):
        probs.append("Confidence line: sections no longer carry Confidence")
    if not ms or not ms_text or re.match(r"(?i)none\b", ms_text) and "stopped" not in ms_text.lower():
        probs.append("warn: no next milestone; it will be listed under Missing a plan")
    elif not du.milestone_date(ms_text) and ", done " not in ms_text:
        probs.append("warn: next milestone has no date; it will be listed under Missing a plan")
    if prev is not None and ms_text and prev.milestone:
        d_now, d_prev = du.milestone_date(ms_text), du.milestone_date(prev.milestone)
        later = [d for _, d, ok in du.dates_in(prog) if ok and d and d_now and d > d_now]
        hit = next((mv for mv in MOVED.finditer(prog) if _about_a_date(prog, mv, d_now)), None)
        if d_now and d_now == d_prev and hit:
            probs.append(f"warn: milestone date {du.label(d_now)} is carried from {du.label(prev.date)}, but Progress "
                         f"says something moved ('{hit.group(0)}'); confirm the date")
        elif d_now and d_now == d_prev and later:
            probs.append(f"warn: milestone date {du.label(d_now)} is carried from {du.label(prev.date)}, but Progress "
                         f"names a later date ({du.label(later[0])}); confirm the date")
    if status != "🟢" and not any(l.startswith("Green when:") for l in lines):
        probs.append("not green but no Green when line")
    if any("sets this when they confirm" in l for l in lines):
        probs.append("warn: placeholder Green when: write what would make it green")
    if status == "🟢" and any(l.startswith("Green when:") for l in lines):
        probs.append("green section has a Green when line")
    if not any(l.startswith("Blocked on:") for l in lines):
        probs.append("no Blocked on line")
    short = next((m for m in re.finditer(r"\b(MR|QE|SDK|reqs?)\b|Kata(?! container)", body)
                  if f"({m.group(0)})" not in body), None)
    if short:
        probs.append(f"warn: unexplained shorthand: '{short.group(0)}'")
    if re.search(r"https?://", body):
        probs.append("raw URL in text")
    if re.search(r"Note \(agent", body):
        probs.append("agent note in doc")
    for k, l in enumerate(lines):
        if l.startswith(("Progress:", "Blocked on:")) and not re.search(
                r"No (change since|update from)|Blocked on: None\.|Moved from .+ on |\((email|chat|meeting notes)\)\.?$|\(from [A-Z][\w .'-]*\)\.?$", l):
            if not any(i == k for i, _, _ in links):
                probs.append(f"no link or source label on line: '{l[:40]}'")
        if l.startswith("Progress:") and len(re.findall(r"[.!?](\s|$)", l)) > 3:
            probs.append("Progress over 3 sentences")
    return probs


def blocking(probs):
    return [p for p in probs if not p.startswith(("warn:", "review:"))]


def updater_tabs(doc, person):
    return [i for i in du.model(doc)[2] if i.updater == person]


def is_engineer(doc, person):
    inits = du.model(doc)[2]
    return any(i.owner == person for i in inits) and not any(i.updater == person for i in inits) \
        and not any(a.owner == person for a in du.model(doc)[1].values())


def author_of(section, updater):
    for t, _ in section.lines:
        mm = re.match(r"Updated by (.+) for (.+)\.$", t)
        if mm:
            return mm.group(1)
        if t.startswith(("Unconfirmed:", "Starting section drafted")):
            return None  # replaceable by the updater
    return updater


def ledger_path(person, day):
    return os.path.join(LEDGER, person, f"{day.isoformat()}.json")


def load_ledger(person, day):
    try:
        return json.load(open(ledger_path(person, day)))
    except FileNotFoundError:
        return {}


def hand_edits(doc_id, person, tab_title, day):
    """Daily step 6: lines a person changed in the doc since this person's agent published today's section."""
    init = next(i for i in du.model(du.read_doc(doc_id))[2] if i.title == tab_title)
    sec = next((s for s in init.sections if s.date == day), None)
    led = load_ledger(person, day).get(tab_title)
    if not sec or not led:
        return []
    return [t for t, _ in sec.lines if t not in led["lines"]]


def publish(doc_id, person, tab_title, lines, links, day, cover_for=None, replace_other=False, between=None,
            confirm_mismatch=False):
    """Daily step 6 for one initiative tab. Raises on a permission or check failure (nothing written)."""
    doc = du.read_doc(doc_id)
    init = next(i for i in du.model(doc)[2] if i.title == tab_title)
    if person != init.updater:
        if cover_for != init.updater:
            raise PermissionError(f"{person} is not the updater of {tab_title} ({init.updater} is); nothing written")
        lines = lines + [f"Updated by {person} for {init.updater}."]
    norm = du.normalize(lines, carry=init.sections[0] if init.sections else None)
    links, lines = m.relink(lines, norm, links), norm
    probs = blocking(checks(lines, links, known_names=["Priya"], prev=init.sections[0] if init.sections else None))
    if probs:
        raise ValueError(probs)
    same = next((s for s in init.sections if s.date == day), None)
    if same:
        who = author_of(same, init.updater)
        if who not in (None, person) and not replace_other:
            return f"ASK: today's section on {tab_title} was written by {who}. Replace it or merge into it?"
    sec_lines = [du.label(day, True)] + lines
    sec_links = [(k + 1, w, u) for k, w, u in links]
    for attempt in range(3):
        try:
            m.write_section(doc_id, init.tab_id, sec_lines, sec_links, between=between if attempt == 0 else None)
            break
        except RuntimeError as e:
            if "revision" not in str(e).lower() or attempt == 2:
                raise
            print(f"   write refused (doc changed since read); re-read and retry {attempt + 1}")
    ms = next(l for l in lines if l.startswith("Next milestone:"))[len("Next milestone: "):]
    area_tab = du.model(du.read_doc(doc_id))[1][init.area_title].tab_id
    m.set_row(doc_id, area_tab, init.name, [init.name, init.owner, lines[0], ms])
    fixed = du.repair_headings(doc_id)
    led = load_ledger(person, day)
    led[tab_title] = {"lines": lines, "links": [u for _, _, u in links]}
    os.makedirs(os.path.dirname(ledger_path(person, day)), exist_ok=True)
    json.dump(led, open(ledger_path(person, day), "w"), indent=1)
    got = next(i for i in du.model(du.read_doc(doc_id))[2] if i.title == tab_title).sections[0]
    quoted = " / ".join(t for t, _ in got.lines)
    ok = got.date == day and all(l in [t for t, _ in got.lines] for l in lines)
    return f"{'LANDED' if ok else 'DID NOT LAND'} {tab_title}: {quoted}" + (f" [headings restored: {fixed}]" if fixed else "")
