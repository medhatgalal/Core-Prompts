"""Doc read/write helpers for the daily-update skill. The agent writes the words; these write the layout.

Safety: every write goes through `batch()`. It refuses the docs in PROTECTED, read from the person's own
`~/.daily-update/protected.json` ({"<doc id>": "<label>"}; no file means none), and with DU_TEST=1 it also
refuses any doc whose title does not start with "E2E TEST". Every write carries the revision it was based on,
so a doc changed by someone else is never overwritten. Reads are always allowed.
"""
import datetime as dt
import json
import os
import re
import subprocess


def _protected():
    path = os.path.expanduser("~/.daily-update/protected.json")
    try:
        with open(path) as f:
            return {str(k): str(v) for k, v in json.load(f).items()}
    except FileNotFoundError:
        return {}


PROTECTED = _protected()


def _skill_name():
    """The installed skill's folder name, so doc text shows the command people actually type.
    Layouts: <skill>/scripts/ (this repo) and <skill>/resources/scripts/ (Core-Prompts bundles)."""
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.basename(parent) == "resources":
        parent = os.path.dirname(parent)
    return os.path.basename(parent)


SKILL_NAME = _skill_name()
CMD = "/" + SKILL_NAME
TEST_TITLE_PREFIX = "E2E TEST"
STATUSES = {"🔴": "🔴 Red", "🟡": "🟡 At risk", "🟢": "🟢 On track", "⚪": "⚪ Paused"}
RANK = {"🔴": 0, "🟡": 1, "🟢": 2, "⚪": 3}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DATE_RE = re.compile(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b")
HEADING_RE = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\w{3}) (\d{1,2}), (\d{4})$")


# ---------- gws ----------

READ_VERBS = ("get", "list", "getProfile")


def dry_run():
    """True under --dry-run (cli.main sets DU_DRY_RUN, and child scripts inherit it)."""
    return os.environ.get("DU_DRY_RUN") == "1"


def guard_write(what):
    """The one place a dry run is enforced. Every write path (Docs, Drive, Gmail, config file) calls this or goes
    through gws(). A handler should print its PLAN and return before it gets here; reaching here is a bug."""
    if dry_run():
        raise SystemExit(f"REFUSED (dry run): {what} would write. Nothing written.")


def is_read(args):
    """A gws call reads when its method (the words before the first --flag) is get, list or getProfile."""
    words = []
    for a in args:
        if a.startswith("-"):
            break
        words.append(a)
    return bool(words) and words[-1] in READ_VERBS


def gws(*args, body=None):
    if not is_read(args):
        guard_write("gws " + " ".join(args[:4]))
    cmd = ["gws", *args]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        raise RuntimeError(f"gws failed: {' '.join(args[:4])}\n{p.stderr[-2000:]}")
    out = p.stdout.strip()
    return json.loads(out) if out else {}


def read_doc(doc_id):
    return gws("docs", "documents", "get", "--params",
               json.dumps({"documentId": doc_id, "includeTabsContent": True}))


def batch(doc_id, requests, doc=None):
    if doc_id in PROTECTED:
        raise SystemExit(f"REFUSED: {PROTECTED[doc_id]} is protected while the skill is in testing.")
    doc = doc or read_doc(doc_id)
    if os.environ.get("DU_TEST") and not doc.get("title", "").startswith(TEST_TITLE_PREFIX):
        raise SystemExit(f"REFUSED (DU_TEST): doc title {doc.get('title')!r} does not start with {TEST_TITLE_PREFIX!r}.")
    if not requests:
        return {}
    # Skill rule: refuse the write if anyone changed the doc since this read.
    body = {"requests": requests, "writeControl": {"requiredRevisionId": doc["revisionId"]}}
    return gws("docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id}), body=body)


def pageless(doc_id, tab_ids):
    """Skill rule: every tab is pageless."""
    batch(doc_id, [{"updateDocumentStyle": {"tabId": t, "documentStyle": {"documentFormat": {"documentMode": "PAGELESS"}},
                                            "fields": "documentFormat"}} for t in tab_ids])


GUIDE = "Update guide"
DECISIONS_HEAD = "Exec leadership: decisions or help needed"
DECISIONS_COL = "Decision or help needed"
NEXT_HEAD = "Next 2 weeks"
CONF_DEF = "kix.confidence"  # legacy Confidence chips; migrate.py removes them


PREFIXES = ("Next milestone:", "Progress:", "Blocked on:", "Green when:", "Unconfirmed:", "Confidence:")
BOLD_PREFIXES = PREFIXES + ("Updated by", "Added by")  # line starts written bold
CONFIDENCE = ("Very confident", "Slightly confident", "Not confident")  # legacy sections only (see migrate.py)


def normalize(lines, carry=None):
    """Skill section format. `lines` starts with the date heading or the status line.
    Order: status, Next milestone, Progress, Blocked on, Green when (only when not green), then the closing
    lines (Updated by, Added by, Moved from, Unconfirmed). `carry` is a Section to take missing lines from.
    Confidence is no longer part of a section: any Confidence line is dropped."""
    head = [lines[0]] if HEADING_RE.match(lines[0]) else []
    body = [l for l in lines[len(head):] if not l.startswith("Confidence:")]
    raw_status = next(l for l in body if l[:1] in STATUSES)
    status = STATUSES.get(raw_status.strip(), raw_status)  # a bare "🟡" becomes "🟡 At risk"
    get = lambda p: next((l for l in body if l.startswith(p)), None) or (carry and carry.line(p))
    ms, prog = get("Next milestone:"), next((l for l in body if l.startswith("Progress:")), None)
    if ms:
        ms = re.sub(r"(?i)no date set yet", "No date set yet", ms)
    blk, gw = get("Blocked on:"), get("Green when:")
    tail = [l for l in body if l != raw_status and not l.startswith(PREFIXES)] + \
           [l for l in body if l.startswith("Unconfirmed:")]
    tail = list(dict.fromkeys(tail))  # a closing line written twice appears once
    out = [status, ms]
    if prog:
        out.append(prog)
    out.append(blk or "Blocked on: None.")
    if status[:1] != "🟢":
        out.append(gw or "Green when: the updater sets this when they confirm.")
    return head + [x for x in out if x] + tail


def repair_headings(doc_id):
    """Skill rule: after a write, every date line must still be a HEADING_2. Restores any that are not."""
    doc = read_doc(doc_id)
    reqs, fixed = [], []
    for t, _ in all_tabs(doc):
        for e in t["documentTab"]["body"]["content"]:
            if "paragraph" in e and HEADING_RE.match(para_text(e["paragraph"]).strip()) \
                    and e["paragraph"]["paragraphStyle"].get("namedStyleType") != "HEADING_2":
                reqs.append({"updateParagraphStyle": {
                    "range": {"startIndex": e["startIndex"], "endIndex": e["endIndex"], "tabId": t["tabProperties"]["tabId"]},
                    "paragraphStyle": {"namedStyleType": "HEADING_2"}, "fields": "namedStyleType"}})
                fixed.append(f"{t['tabProperties']['title']}: {para_text(e['paragraph']).strip()}")
    batch(doc_id, reqs, doc)
    return fixed


# ---------- dates ----------

def ref_date():
    """The day yearless dates are read against: DU_TODAY (YYYY-MM-DD, tests) or today in US Eastern time."""
    if os.environ.get("DU_TODAY"):
        return dt.date.fromisoformat(os.environ["DU_TODAY"])
    from zoneinfo import ZoneInfo
    return dt.datetime.now(ZoneInfo("America/New_York")).date()


def parse_date(wd, mon, day, year=None):
    """A section heading carries its year. A 'Fri Jan 8' style date does not: it is the nearest such date
    to ref_date(), so in December "Fri Jan 8" means next January. The weekday is not used to pick the year,
    so a wrong weekday still shows up as one."""
    if mon not in MONTHS:
        return None
    if year:
        try:
            return dt.date(int(year), MONTHS[mon], int(day))
        except ValueError:
            return None
    ref = ref_date()
    cands = []
    for y in (ref.year - 1, ref.year, ref.year + 1):
        try:
            cands.append(dt.date(y, MONTHS[mon], int(day)))
        except ValueError:  # Feb 29 in a non-leap year
            pass
    return min(cands, key=lambda c: abs((c - ref).days)) if cands else None  # no such date (Apr 31): None


def label(d, year=False):
    s = f"{WD[d.weekday()]} {d.strftime('%b')} {d.day}"
    return f"{s}, {d.year}" if year else s


def dates_in(text):
    """All 'Fri Nov 6' style dates in text: list of (matched text, date, weekday_ok)."""
    out = []
    for m in DATE_RE.finditer(text):
        d = parse_date(*m.groups())
        # A date that does not exist (Sun Apr 31) is reported like a wrong weekday instead of crashing.
        out.append((m.group(0), d, d is not None and WD[d.weekday()] == m.group(1)))
    return out


# ---------- doc model ----------

def utf16(s):
    return len(s.encode("utf-16-le")) // 2


def para_text(p):
    """Paragraph text; a dropdown chip reads as its selected value."""
    return "".join(r.get("textRun", {}).get("content", "") or
                   r.get("dropdown", {}).get("dropdownProperties", {}).get("displayValue", "") for r in p["elements"])


def cell_text(c):
    return "".join(para_text(x["paragraph"]) for x in c["content"] if "paragraph" in x).strip()


def all_tabs(doc):
    def walk(ts, parent=None):
        for t in ts:
            yield t, parent
            yield from walk(t.get("childTabs", []), t)
    return list(walk(doc["tabs"]))


def title_parts(title):
    m = re.match(r"^(.*) \((.*)\)$", title)
    return (m.group(1), m.group(2)) if m else (title, None)


def parse_backups(header):
    """The `Backups: A, B` part of an initiative's header line; empty when there is none."""
    m = re.search(r"Backups: ([^·]+)", header or "")
    return [b.strip() for b in m.group(1).split(",") if b.strip()] if m else []


class Section:
    def __init__(self, date, heading_el):
        self.date, self.heading_el, self.lines = date, heading_el, []

    def line(self, prefix):
        return next((t for t, _ in self.lines if t.startswith(prefix)), None)

    @property
    def status(self):
        return next((t[0] for t, _ in self.lines if t[:1] in STATUSES), None)

    @property
    def milestone(self):
        m = self.line("Next milestone:")
        return m[len("Next milestone:"):].strip() if m else None

    @property
    def unconfirmed(self):
        return any(t.startswith("Unconfirmed:") for t, _ in self.lines)

    @property
    def no_change(self):
        return any(t.startswith("No change since") for t, _ in self.lines)


class Initiative:
    def __init__(self, tab, parent):
        p = tab["tabProperties"]
        self.tab_id, self.title = p["tabId"], p["title"]
        self.name, self.owner = title_parts(self.title)
        self.area_title = parent["tabProperties"]["title"]
        self.area_name, self.area_owner = title_parts(self.area_title)
        self.body = tab["documentTab"]["body"]["content"]
        self.header, self.sections = None, []
        cur = None
        for e in self.body:
            if "paragraph" not in e:
                continue
            txt = para_text(e["paragraph"]).rstrip("\n")
            style = e["paragraph"]["paragraphStyle"].get("namedStyleType")
            m = HEADING_RE.match(txt)
            if style == "HEADING_2" and m and parse_date(*m.groups()):
                cur = Section(parse_date(*m.groups()), e)
                self.sections.append(cur)
            elif cur is not None:
                if txt.strip():
                    cur.lines.append((txt, e))
            elif txt.startswith("Owner:"):
                self.header = txt
        self.updater = self.owner
        if self.header:
            m = re.search(r"Updater: ([^·]+)", self.header)
            if m:
                self.updater = m.group(1).strip()
        self.backups = parse_backups(self.header)

    def newest(self, attr=None):
        for s in self.sections:
            if attr is None or getattr(s, attr):
                return s
        return None

    def first_heading_index(self):
        return self.sections[0].heading_el["startIndex"] if self.sections else self.body[-1]["endIndex"] - 1


class Area:
    def __init__(self, tab):
        p = tab["tabProperties"]
        self.tab_id, self.title = p["tabId"], p["title"]
        self.name, self.owner = title_parts(self.title)
        self.body = tab["documentTab"]["body"]["content"]
        self.headline = None
        after = False
        for e in self.body:
            if "paragraph" in e:
                txt = para_text(e["paragraph"]).strip()
                if txt == "Headline":
                    after = True
                elif after and txt:
                    self.headline = txt
                    after = False
        self.table = next((e for e in self.body if "table" in e
                           and cell_text(e["table"]["tableRows"][0]["tableCells"][0]) == "Initiative"), None)

    def rows(self):
        if not self.table:
            return []
        return [[cell_text(c) for c in r["tableCells"]] for r in self.table["table"]["tableRows"][1:]]

    @property
    def split(self):
        """True when the Initiatives table has separate Next milestone and Date columns (v1.19.10 and later)."""
        return bool(self.table) and len(self.table["table"]["tableRows"][0]["tableCells"]) == 5

    @staticmethod
    def row_milestone(r):
        """A row's milestone with its date, whichever table layout it comes from."""
        return f"{r[3]}, {r[4]}" if len(r) >= 5 and r[4] else r[3]


def model(doc):
    inits, areas, overview, archive = [], {}, None, None
    for t, parent in all_tabs(doc):
        title = t["tabProperties"]["title"]
        if parent is None:
            if overview is None:
                overview = t
            elif title.startswith(GUIDE):
                continue
            elif title.startswith("Archive"):
                archive = t
            else:
                areas[title] = Area(t)
        elif not parent["tabProperties"]["title"].startswith(("Archive", GUIDE)):
            inits.append(Initiative(t, parent))
    return overview, areas, inits


def tab_url(doc_id, tab_id):
    return f"https://docs.google.com/document/d/{doc_id}/edit?tab={tab_id}"


INIT_HEAD = ["Initiative", "Owner", "Status", "Next milestone", "Date"]
INIT_HEAD_OLD = ["Initiative", "Owner", "Status", "Next milestone and date"]


def split_milestone(ms):
    """'Pilot live, Fri Nov 13' -> ('Pilot live', 'Fri Nov 13'); undated -> (what, 'No date set yet');
    'Ship, Mon Nov 2, done Thu Nov 5.' -> ('Ship', 'Mon Nov 2, done Thu Nov 5')."""
    ms = (ms or "").strip().rstrip(".")
    if not ms or re.fullmatch(r"(?i)no date set yet", ms):
        return ("None", "No date set yet")
    m = re.search(r",?\s*no date set yet\b(.*)$", ms, re.I)
    if m:
        return (ms[:m.start()].strip(" ,"), "No date set yet" + m.group(1))
    found = list(DATE_RE.finditer(ms))
    if not found:
        return (ms, "No date set yet")
    first = found[0]
    head = ms[:first.start()].rstrip(" ,;:")
    when = ms[first.start():].strip()
    m = re.search(r",?\s*(done|stopped)$", head)
    if m:
        head, when = head[:m.start()].rstrip(" ,"), f"{m.group(1)} " + when
    head = re.sub(r"\s+(by|on|due)$", "", head)
    return (head or ms, when)


def row_cells(values, ncols):
    """Initiatives-table cells from [name, owner, status, milestone with date], for a 4- or 5-column table."""
    if ncols == 5 and len(values) == 4:
        what, when = split_milestone(values[3])
        return [values[0], values[1], values[2], what, when]
    return list(values)


def milestone_dated(ms):
    return ms is not None and (bool(DATE_RE.search(ms)) or "No date set yet" in ms)


def milestone_date(ms):
    """The milestone's own due date (ignores a trailing 'done <date>')."""
    if not ms:
        return None
    core = re.split(r", done ", ms)[0]
    found = dates_in(core)
    return found[-1][1] if found else None


def worst(statuses):
    s = [x for x in statuses if x]
    return min(s, key=lambda x: RANK[x]) if s else None


def status_counts(statuses):
    """Area health Status cell: one line per colour, worst first, zero counts left out ("🟡 1\\n🟢 4")."""
    s = [x for x in statuses if x]
    return "\n".join(f"{c} {s.count(c)}" for c in RANK if s.count(c))


LONG_MILESTONE = 60  # characters, without the date: longer gets a WARN asking for a shorter wording


def commitment(ms):
    """A milestone without its date, exactly as written: 'Pilot live, Fri Nov 13' -> 'Pilot live'.
    Never shortened here: a long milestone is reworded in its section (the pre-publish check warns)."""
    core = re.split(r", done ", ms)[0]
    found = list(DATE_RE.finditer(core))
    if found:
        f = found[-1]
        core = core[:f.start()].rstrip(" ,;:") + core[f.end():]
    return re.sub(r"\s+(by|on|due)$", "", core.strip(" ,;:."))


def next_two_weeks(inits, today):
    """Overview 'Next 2 weeks': (date, commitment, initiative, status) for each open initiative whose newest
    Next milestone falls from today through today + 14 days, or whose date has already passed and is not done
    (overdue items stay visible until they are done); by date, then worst first."""
    rows = []
    for i in inits:
        s = i.newest("milestone")
        prog = (i.sections[0].line("Progress:") or "") if i.sections else ""
        if not s or ", done " in s.milestone or prog.startswith(("Progress: Done ", "Progress: Stopped ")):
            continue
        d = milestone_date(s.milestone)
        if d and d <= today + dt.timedelta(days=14):
            st = i.newest("status")
            rows.append((d, commitment(s.milestone), i, st.status if st else "🟡"))
    return sorted(rows, key=lambda r: (r[0], RANK[r[3]]))


def next_two_weeks_date(d, today):
    """The Date cell of a Next 2 weeks row: an overdue milestone is marked."""
    return label(d) + (" (overdue)" if d < today else "")


def missing_plan(inits, today):
    """Overview 'Missing a plan': (initiative, what is missing, since) for each open initiative whose newest
    section has no next milestone, or one with no date. Done, stopped and paused (⚪) initiatives are left out.
    `since` is the oldest date of the unbroken run of newest sections that lack a dated milestone."""
    rows = []
    for i in inits:
        if not i.sections:
            rows.append((i, "No section yet", None))
            continue
        prog = i.sections[0].line("Progress:") or ""
        st = i.newest("status")
        if prog.startswith(("Progress: Done ", "Progress: Stopped ")) or (st and st.status == "⚪"):
            continue
        ms_sec = i.newest("milestone")
        ms = ms_sec.milestone if ms_sec else None
        if ms and (milestone_date(ms) or ", done " in ms):
            continue
        what = "Milestone has no date" if ms and not re.match(r"(?i)(none|no date set yet)\b", ms) else "No next milestone"
        since = None
        for s in i.sections:
            if s.milestone is None and not s.no_change:
                continue
            if s.milestone and (milestone_date(s.milestone) or ", done " in s.milestone):
                break
            since = s.date
        rows.append((i, what, since or i.sections[-1].date))
    return sorted(rows, key=lambda r: (r[2] or today, r[0].name))


# ---------- overview title, used for every "Back to <overview>" link ----------

def overview_title(doc):
    first = next(e for e in doc["tabs"][0]["documentTab"]["body"]["content"] if "paragraph" in e)
    return para_text(first["paragraph"]).strip() or doc.get("title", "")


# ---------- shared settings: stored on the doc itself (Drive file properties) ----------
# Anyone with edit access reads and writes the same values, so whoever runs close/send on the doc owner's
# behalf has the readers and people without the doc owner's laptop.

def settings_get(doc_id):
    props = gws("drive", "files", "get", "--params",
                json.dumps({"fileId": doc_id, "fields": "properties", "supportsAllDrives": True})).get("properties", {})
    readers, people = [], {}
    for k in sorted(props):
        if k.startswith("du.reader."):
            name, channel, email = (props[k].split("|") + ["", ""])[:3]
            readers.append({"name": name, "channel": channel, "email": email})
        elif k.startswith("du.person."):
            people[k[len("du.person."):]] = props[k]
    return {"owner": props.get("du.owner", ""), "readers": readers, "people": people}


def settings_set(doc_id, owner=None, readers=None, people=None):
    """Replace the given parts. Drive keeps each key+value under 124 bytes, so values stay short."""
    cur = gws("drive", "files", "get", "--params",
              json.dumps({"fileId": doc_id, "fields": "properties", "supportsAllDrives": True})).get("properties", {})
    props = {}
    if owner is not None:
        props["du.owner"] = owner
    if readers is not None:
        props.update({k: None for k in cur if k.startswith("du.reader.")})
        for n, r in enumerate(readers, 1):
            props[f"du.reader.{n}"] = f"{r['name']}|{r.get('channel', 'email')}|{r['email']}"
    if people is not None:
        props.update({k: None for k in cur if k.startswith("du.person.")})
        for name, email in people.items():
            props[f"du.person.{name}"] = email
    if os.environ.get("DU_TEST"):
        title = gws("drive", "files", "get", "--params", json.dumps({"fileId": doc_id, "fields": "name"})).get("name", "")
        if not title.startswith(TEST_TITLE_PREFIX):
            raise SystemExit("REFUSED (DU_TEST): settings write to a non-test doc.")
    if doc_id in PROTECTED:
        raise SystemExit(f"REFUSED: {PROTECTED[doc_id]} is protected while the skill is in testing.")
    gws("drive", "files", "update", "--params", json.dumps({"fileId": doc_id, "fields": "properties",
                                                            "supportsAllDrives": True}), body={"properties": props})
    return settings_get(doc_id)
