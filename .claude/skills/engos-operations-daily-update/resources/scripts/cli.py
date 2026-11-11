"""Noun-verb command line for the daily-update kit.

    du.py <noun> <verb> [args] [--doc ID] [--json] [--dry-run] [--for-owner]

Nouns are the things in the model (doc, area, initiative, person, reader, source, section) plus `day`, the
daily close-out cycle, and `doctor`, the one read-only health check (no verb). Verbs are the same everywhere: list, show, add, set-*, remove, plus the initiative
lifecycle (pause, resume, done, stop, reopen, archive).

This module owns four things and nothing else:
  1. the grammar (argparse; `du.py <noun> --help` lists the verbs),
  2. the lifecycle table and who may do what (pure functions, tested offline in tests/cli_test.py),
  3. reads (list, show), which never write,
  4. writes, which check the rules first, print a PLAN, and write nothing under --dry-run.

The Google Docs work itself stays in dudoc.py, modes.py and build.py.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

import dudoc as du
import modes as m

SOURCE_KINDS = ("jira", "gitlab", "github", "chat", "email", "meetings", "docs")
PRIVATE_KINDS = ("chat", "email", "meetings")  # read for drafting, never linked (skill rule 6)
CHANNELS = ("email", "chat")
STATES = ("open", "paused", "done", "stopped", "archived")

# verb -> (states it may start from, state it ends in). The single source of truth for the lifecycle.
TRANSITIONS = {
    "pause": ({"open"}, "paused"),
    "resume": ({"paused"}, "open"),
    "done": ({"open", "paused"}, "done"),
    "stop": ({"open", "paused"}, "stopped"),
    "reopen": ({"done", "stopped"}, "open"),
    "archive": ({"done", "stopped"}, "archived"),
}


class Refused(SystemExit):
    def __init__(self, why):
        super().__init__(f"REFUSED: {why} Nothing written.")


# ---------- pure rules (no doc, no network) ----------

def canon(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def same_person(a, b):
    """'Scott' matches 'Scott Parrish': first names compare, case-insensitive."""
    fa, fb = canon(a).split(" ")[0], canon(b).split(" ")[0]
    return bool(fa) and fa == fb


def state_of(init, archived=False):
    """open, paused, done, stopped or archived. Read from the newest section, the way Sweep and Overview do."""
    if archived:
        return "archived"
    if not init.sections:
        return "open"
    prog = init.sections[0].line("Progress:") or ""
    if prog.startswith("Progress: Done "):
        return "done"
    if prog.startswith("Progress: Stopped "):
        return "stopped"
    st = init.newest("status")
    return "paused" if st and st.status == "⚪" else "open"


def check_transition(verb, state, name):
    allowed, _ = TRANSITIONS[verb]
    if state not in allowed:
        raise Refused(f"cannot {verb} {name!r}: it is {state}; {verb} needs it to be {' or '.join(sorted(allowed))}.")


def match_one(items, ref, key_name, label):
    """Find one item by exact title or by name, ignoring case. Refuse when none or several match."""
    hits = [x for x in items if canon(x.title) == canon(ref) or canon(getattr(x, "name", "")) == canon(ref)]
    if len(hits) == 1:
        return hits[0]
    names = ", ".join(sorted(getattr(x, key_name) for x in items)) or "none"
    if not hits:
        raise Refused(f"no {label} named {ref!r}. Known: {names}.")
    raise Refused(f"{ref!r} matches several {label}s: {', '.join(x.title for x in hits)}. Use the full title.")


def check_reader(r):
    if not r.get("name", "").strip():
        raise Refused("a reader needs a name.")
    if r.get("channel") not in CHANNELS:
        raise Refused(f"a reader's channel is one of {', '.join(CHANNELS)}.")
    if "@" not in r.get("email", ""):
        raise Refused("a reader needs an email address.")


def source_valid(me, owner, updater, backups):
    """The one test for a saved source: you may keep sources on a tab if you are its updater, one of its
    backups, or the doc owner. Used by `source add` and by `doctor`, so they cannot disagree."""
    return any(same_person(me, p) for p in [updater, owner, *backups])


def check_add_backup(i, person, people):
    """add-backup rules: the person can be tagged (in the people list, with an email), is not already the
    updater, and is not already a backup. Anything else is a no-op, refused."""
    if not person.strip():
        raise Refused("a backup needs a person.")
    if canon(person) == canon(i.updater):
        raise Refused(f"{person!r} is already the updater of {i.name!r}; a backup is someone else.")
    if any(canon(b) == canon(person) for b in i.backups):
        raise Refused(f"{person!r} is already a backup of {i.name!r}.")
    have = {canon(k): v for k, v in people.items()}
    if canon(person) not in have:
        raise Refused(f"{person!r} is not in the people list, so they cannot be tagged or confirmed to have access. "
                      f"Run `person set-email {person} <email>` first.")
    if "@" not in have[canon(person)]:
        raise Refused(f"{person!r} has no email in the people list, so they cannot be tagged or confirmed to have access. "
                      f"Run `person set-email {person} <email>` first.")


def check_remove_backup(i, person):
    if not any(canon(b) == canon(person) for b in i.backups):
        raise Refused(f"{person!r} is not a backup of {i.name!r}. Backups: {', '.join(i.backups) or 'none'}.")


def backup_header_edit(header, backups, new):
    """(old, new) text for one replace in the header line, turning the backups list `backups` into `new`.
    The part sits right after `Updater:` (after `Owner:` when there is no updater part) and is dropped when empty."""
    if backups and new:
        return f"Backups: {', '.join(backups)}", f"Backups: {', '.join(new)}"
    if backups:
        return f" · Backups: {', '.join(backups)}", ""
    m = re.search(r"Updater: ([^·]+)", header) or re.search(r"Owner: ([^·]+)", header)
    anchor = m.group(0).rstrip()
    return anchor, f"{anchor} · Backups: {', '.join(new)}"


def backup_targets(inits, states, person):
    """For `add-backup --all`: (initiatives to change, [(initiative, why skipped)]). Open and paused only."""
    todo, skipped = [], []
    for i in inits:
        if states.get(i.title) not in ("open", "paused"):
            continue
        if canon(person) == canon(i.updater):
            skipped.append((i, "is the updater"))
        elif any(canon(b) == canon(person) for b in i.backups):
            skipped.append((i, "is already a backup"))
        else:
            todo.append(i)
    return todo, skipped


def check_source(kind, ref):
    if kind not in SOURCE_KINDS:
        raise Refused(f"source kind is one of {', '.join(SOURCE_KINDS)}.")
    if not ref.strip():
        raise Refused("a source needs a reference (a Jira key, a repo, a space, a search).")


# ---------- local config (sources live here, never on the doc) ----------

def config_path():
    return os.environ.get("DU_CONFIG") or os.path.expanduser("~/.daily-update/config.json")


def load_config():
    try:
        with open(config_path()) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_config(cfg):
    du.guard_write("saving the config")
    os.makedirs(os.path.dirname(config_path()), exist_ok=True)
    with open(config_path(), "w") as f:
        json.dump(cfg, f, indent=1, ensure_ascii=False)
    if not os.environ.get("DU_NO_SYNC"):
        import backup
        print(backup.report(backup.sync()), file=sys.stderr)


# ---------- the doc, read once per command ----------

class Ctx:
    def __init__(self, doc_id):
        self.id = doc_id
        self.cfg = load_config()
        self.me = self.cfg.get("me", "")
        self.doc = du.read_doc(doc_id)
        self.overview, self.areas, self.inits = du.model(self.doc)
        self.archive = next((t for t, p in du.all_tabs(self.doc)
                             if p is None and t["tabProperties"]["title"].startswith("Archive")), None)
        kids = [du.Initiative(c, self.archive) for c in (self.archive or {}).get("childTabs", [])]
        self.archived = [k for k in kids if "Area:" in (k.header or "")]
        self.archived_areas = [k for k in kids if "Area:" not in (k.header or "")]
        self._settings = None

    @property
    def settings(self):
        if self._settings is None:
            self._settings = du.settings_get(self.id)
        return self._settings

    @property
    def owner(self):
        return self.settings["owner"]

    def state(self, init):
        return state_of(init, archived=init in self.archived)

    def everyone(self):
        names = set(self.settings["people"])
        for i in self.inits + self.archived:
            names |= {i.owner, i.updater}
        for a in self.areas.values():
            names.add(a.owner)
        names |= {r["name"] for r in self.settings["readers"]}
        return {n for n in names if n}

    def area_of(self, init):
        return self.areas.get(init.area_title)

    def init(self, ref, archived=False):
        return match_one(self.inits + (self.archived if archived else []), ref, "name", "initiative")

    def area(self, ref):
        return match_one(list(self.areas.values()), ref, "name", "area")


def resolve_doc(ns):
    doc_id = ns.doc or load_config().get("doc_id")
    if not doc_id:
        raise SystemExit("No doc. Pass --doc ID, or run `du.py doc create`, or `/engos-operations-daily-update doc join <link>` in the chat, first.")
    m_ = re.search(r"/document/d/([\w-]+)", doc_id)
    return m_.group(1) if m_ else doc_id


# ---------- who may do what ----------

def need_owner(ctx, ns, what):
    """Doc-owner commands. Any editor may run them for the doc owner with --for-owner (the agent asks first)."""
    if getattr(ns, "for_owner", False) or same_person(ctx.me, ctx.owner):
        return
    raise Refused(f"{what} is the doc owner's ({ctx.owner}). Ask them, or run it for them with --for-owner "
                  f"once they have said so.")


def need_initiative_editor(ctx, ns, init, what):
    """The tab's updater, its area owner or the doc owner."""
    if getattr(ns, "for_owner", False):
        return
    allowed = [init.updater, init.area_owner, ctx.owner]
    if not any(same_person(ctx.me, a) for a in allowed):
        raise Refused(f"{what} on {init.title!r} is for {init.updater} (updater), {init.area_owner} (area owner) "
                      f"or {ctx.owner} (doc owner). You are {ctx.me or 'not set up'}. Draft a note to them instead.")


def need_area_editor(ctx, ns, area, what):
    if getattr(ns, "for_owner", False) or any(same_person(ctx.me, a) for a in (area.owner, ctx.owner)):
        return
    raise Refused(f"{what} on {area.title!r} is for {area.owner} (area owner) or {ctx.owner} (doc owner).")


# ---------- output ----------

def table(ns, rows, cols):
    """rows: list of dicts. --json prints them as they are; otherwise an aligned plain-text table."""
    if getattr(ns, "json", False):
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    if not rows:
        print("(none)")
        return
    rows = [{k: ", ".join(v) if isinstance(v, list) else v for k, v in r.items()} for r in rows]
    w = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    print("  ".join(c.upper().ljust(w[c]) for c in cols))
    for r in rows:
        print("  ".join(str(r.get(c, "")).ljust(w[c]) for c in cols).rstrip())


def card(ns, data):
    if getattr(ns, "json", False):
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return
    for k, v in data.items():
        if isinstance(v, (list, dict)) and v:
            print(f"{k}:")
            for x in (v.items() if isinstance(v, dict) else v):
                print("  - " + (", ".join(f"{a}={b}" for a, b in x.items()) if isinstance(x, dict) else
                                 " = ".join(map(str, x)) if isinstance(x, tuple) else str(x)))
        else:
            print(f"{k}: {v if v not in ([], {}) else '(none)'}")


def apply(ns, plan, fn):
    """Show the plan; write only when this is not a dry run. The agent shows the plan, waits for "publish",
    then runs the same command without --dry-run."""
    print("PLAN:")
    for p in plan:
        print("  " + p)
    if ns.dry_run:
        print("Dry run: nothing written.")
        return False
    fn()
    print("DONE")
    return True


def today():
    return du.ref_date()


# ---------- shared write helpers ----------

def row_for(init, name=None, owner=None):
    ms = init.newest("milestone")
    st = init.newest("status")
    prog = init.sections[0].line("Progress:") if init.sections else ""
    return [name or init.name, owner or init.owner, du.status_text(st.status if st else "🟡", ms.milestone if ms else "", prog or ""),
            (ms.milestone if ms else "") or ""]


def note(ctx, init, line):
    """Record a change in a section that already exists for today: add the line there. With no section for today
    it writes nothing: a section dated today counts as a confirmed update (sweep skips the tab, the overview and
    doctor read it as fresh), and a change note is not one. The change is already in the title, header or table."""
    day = today()
    fresh = next(i for i in du.model(du.read_doc(ctx.id))[2] if i.tab_id == init.tab_id)
    if fresh.sections and fresh.sections[0].date == day:
        m.insert_line_before(ctx.id, init.tab_id, "Unconfirmed:", line)


def set_header(ctx, tab_id, old, new):
    m.replace_in_para(ctx.id, tab_id, old, new, startswith="Owner:")


def done_lines(ctx, area):
    """Paragraphs under the area tab's Done heading (read fresh)."""
    tab = m.find_tab(du.read_doc(ctx.id), area.tab_id)
    paras = [e for e in tab["documentTab"]["body"]["content"] if "paragraph" in e]
    k = next((n for n, e in enumerate(paras) if du.para_text(e["paragraph"]).strip() == "Done"), None)
    return [] if k is None else paras[k + 1:]


PLACEHOLDER = "No initiatives finished yet."


def add_done_line(ctx, area, line):
    paras = done_lines(ctx, area)
    if paras and du.para_text(paras[0]["paragraph"]).strip() == PLACEHOLDER:
        m.replace_in_para(ctx.id, area.tab_id, PLACEHOLDER, line)
        return
    tab = m.find_tab(du.read_doc(ctx.id), area.tab_id)
    at = tab["documentTab"]["body"]["content"][-1]["endIndex"] - 1
    du.batch(ctx.id, m._paras(area.tab_id, at, [line], ["NORMAL_TEXT"]))


def remove_done_line(ctx, area, name):
    paras = done_lines(ctx, area)
    hit = next((e for e in paras if du.para_text(e["paragraph"]).startswith(f"{name}:")), None)
    if hit is None:
        return
    others = [e for e in paras if e is not hit and du.para_text(e["paragraph"]).strip()]
    if others:
        du.batch(ctx.id, [{"deleteContentRange": {"range": {"startIndex": hit["startIndex"], "endIndex": hit["endIndex"],
                                                            "tabId": area.tab_id}}}])
    else:
        m.replace_in_para(ctx.id, area.tab_id, du.para_text(hit["paragraph"]).rstrip("\n"), PLACEHOLDER)


# ---------- doc ----------

def doc_create(ns):
    import du as dumain
    dumain.cmd_setup([ns.structure])


def doc_show(ns):
    ctx = Ctx(resolve_doc(ns))
    counts = {s: sum(1 for i in ctx.inits if ctx.state(i) == s) for s in STATES if s != "archived"}
    counts["archived"] = len(ctx.archived)
    card(ns, {"doc": ctx.id, "title": ctx.doc.get("title", ""), "owner": ctx.owner, "me": ctx.me,
              "role": "doc owner" if same_person(ctx.me, ctx.owner) else "leader",
              "areas": len(ctx.areas), "initiatives": counts, "readers": len(ctx.settings["readers"])})


def doc_sync(ns):
    import du as dumain
    dumain.cmd_sync([])


# ---------- area ----------

def area_rows(ctx):
    rows = []
    for a in ctx.areas.values():
        kids = [i for i in ctx.inits if i.area_title == a.title]
        by = {s: sum(1 for i in kids if ctx.state(i) == s) for s in STATES[:4]}
        sts = [i.newest("status").status for i in kids if i.newest("status") and ctx.state(i) in ("open", "paused")]
        rows.append({"area": a.name, "owner": a.owner, "open": by["open"], "paused": by["paused"],
                     "finished": by["done"] + by["stopped"], "status": du.status_counts(sts).replace("\n", " "),
                     "headline": a.headline or ""})
    return rows


def area_list(ns):
    table(ns, area_rows(Ctx(resolve_doc(ns))), ["area", "owner", "open", "paused", "finished", "status"])


def area_show(ns):
    ctx = Ctx(resolve_doc(ns))
    a = ctx.area(ns.name)
    kids = [i for i in ctx.inits if i.area_title == a.title]
    card(ns, {"area": a.name, "owner": a.owner, "headline": a.headline or "",
              "initiatives": [{"name": i.name, "owner": i.owner, "updater": i.updater, "state": ctx.state(i)} for i in kids]})


def area_add(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "adding an area")
    if not ns.owner.strip():
        raise Refused("an area needs an owner.")
    if any(canon(a.name) == canon(ns.name) for a in ctx.areas.values()):
        raise Refused(f"area {ns.name!r} already exists.")
    title = f"{ns.name} ({ns.owner})"

    def write():
        import build
        tops = ctx.doc["tabs"]
        at = next((k for k, t in enumerate(tops) if t["tabProperties"]["title"].startswith("Archive")), len(tops))
        r = du.batch(ctx.id, [{"addDocumentTab": {"tabProperties": {"title": title, "index": at}}}], ctx.doc)
        tid = r["replies"][0]["addDocumentTab"]["tabProperties"]["tabId"]
        du.pageless(ctx.id, [tid])
        otitle = du.overview_title(du.read_doc(ctx.id))
        lines = [title, f"Owner: {ns.owner} · Back to {otitle}", "Headline", f"No initiatives yet. ({du.label(today())})",
                 "Initiatives", "", "Done", PLACEHOLDER]
        st = ["HEADING_1", "NORMAL_TEXT", "HEADING_2", "NORMAL_TEXT", "HEADING_2", "NORMAL_TEXT", "HEADING_2", "NORMAL_TEXT"]
        du.batch(ctx.id, m._paras(tid, 1, lines, st, [(1, otitle, du.tab_url(ctx.id, "t.0"))]))
        build.add_table(ctx.id, tid, build.anchor_index(ctx.id, tid, "Initiatives"), [du.INIT_HEAD], build.INIT_SHARES)
        du.repair_headings(ctx.id)
    if apply(ns, [f"Add area tab {title!r} above Archive.", "The overview's Area health table refreshes at `day overview`."], write):
        print("ADDED " + title)


def area_rename(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "renaming an area")
    a = ctx.area(ns.name)
    if any(canon(x.name) == canon(ns.new_name) for x in ctx.areas.values()):
        raise Refused(f"area {ns.new_name!r} already exists.")
    kids = [i for i in ctx.inits if i.area_title == a.title]

    def write():
        m.retitle(ctx.id, a.tab_id, f"{ns.new_name} ({a.owner})")
        for k in kids:
            set_header(ctx, k.tab_id, f"Area: {a.name}", f"Area: {ns.new_name}")
            if k.sections:
                note(ctx, k, f"Area renamed from {a.name} to {ns.new_name} on {du.label(today())}.")
    apply(ns, [f"Rename area {a.name!r} to {ns.new_name!r}.", f"Update the Area line on {len(kids)} initiative tab(s) "
               "and note it in today's section on each tab that already has one."], write)


def area_set_owner(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "changing an area's owner")
    a = ctx.area(ns.name)
    if canon(ns.person) == canon(a.owner):
        raise Refused(f"area {a.name!r} is already owned by {a.owner}.")

    def write():
        m.retitle(ctx.id, a.tab_id, f"{a.name} ({ns.person})")
        set_header(ctx, a.tab_id, f"Owner: {a.owner}", f"Owner: {ns.person}")
    apply(ns, [f"Area {a.name!r}: owner {a.owner} -> {ns.person}.",
               "Initiative updaters do not change; use `initiative set-updater` for those."], write)


def area_set_headline(ns):
    ctx = Ctx(resolve_doc(ns))
    a = ctx.area(ns.name)
    need_area_editor(ctx, ns, a, "the headline")
    if not re.search(r"\((Mon|Tue|Wed|Thu|Fri|Sat|Sun) \w{3} \d{1,2}\)$", ns.text.strip()):
        raise Refused("a headline ends with its date in brackets, like (Fri Nov 6).")

    def write():
        import build
        build.set_headline(ctx.id, a.title, ns.text)
    apply(ns, [f"Headline of {a.name!r}: {ns.text}"], write)


def archive_area(ctx, a):
    """Move an empty area under Archive and list it there, so the Archive tab accounts for every tab under it."""
    arch = ctx.archive
    aid = arch["tabProperties"]["tabId"]
    m.move_tab(ctx.id, a.tab_id, aid, len(arch.get("childTabs", [])))
    m.list_on_archive(ctx.id, aid, a.tab_id, a.title, f"removed {du.label(today())}")


def area_remove(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "removing an area")
    a = ctx.area(ns.name)
    kids = [i for i in ctx.inits if i.area_title == a.title]
    if kids:
        raise Refused(f"area {a.name!r} still has {len(kids)} initiative(s): {', '.join(k.name for k in kids)}. "
                      "Archive them or move them (`area merge`) first. An area is never deleted; this moves it under Archive.")

    def write():
        archive_area(ctx, a)
    apply(ns, [f"Move area tab {a.title!r} under Archive and list it there. Its history stays."], write)


def area_merge(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "merging areas")
    src, dst = ctx.area(ns.name), ctx.area(ns.into)
    if src.tab_id == dst.tab_id:
        raise Refused("an area cannot merge into itself.")
    kids = [i for i in ctx.inits if i.area_title == src.title]

    def write():
        for k in kids:
            initiative_move_now(Ctx(ctx.id), ns, k.name, dst.name)
        c2 = Ctx(ctx.id)
        archive_area(c2, c2.area(src.name))
    apply(ns, [f"Move {len(kids)} initiative(s) from {src.name!r} to {dst.name!r}: {', '.join(k.name for k in kids) or 'none'}.",
               f"Move the empty area tab {src.title!r} under Archive."], write)


# ---------- initiative ----------

def init_rows(ctx, ns):
    pool = ctx.inits + (ctx.archived if (getattr(ns, "state", None) == "archived" or getattr(ns, "all", False)) else [])
    rows = []
    for i in pool:
        st = ctx.state(i)
        if getattr(ns, "state", None) and st != ns.state:
            continue
        if ns.area and canon(i.area_name) != canon(ns.area):
            continue
        if ns.owner and not same_person(i.owner, ns.owner):
            continue
        if ns.updater and not same_person(i.updater, ns.updater):
            continue
        s, ms = i.newest("status"), i.newest("milestone")
        what, when = du.split_milestone(ms.milestone) if ms else ("None", "No date set yet")
        rows.append({"name": i.name, "area": i.area_name if i not in ctx.archived else "(archived)", "owner": i.owner,
                     "updater": i.updater, "backups": list(i.backups), "state": st, "status": du.status_text(s.status, ms.milestone if ms else "", i.sections[0].line("Progress:") or "") if s else "", "milestone": what,
                     "date": when})
    return rows


def initiative_list(ns):
    table(ns, init_rows(Ctx(resolve_doc(ns)), ns), ["name", "area", "owner", "updater", "backups", "state", "status", "milestone", "date"])


def initiative_show(ns):
    ctx = Ctx(resolve_doc(ns))
    i = ctx.init(ns.name, archived=True)
    s = i.sections[0] if i.sections else None
    card(ns, {"initiative": i.name, "area": i.area_name, "owner": i.owner, "updater": i.updater, "backups": list(i.backups),
              "state": ctx.state(i), "newest": du.label(s.date, True) if s else None, "lines": [t for t, _ in s.lines] if s else [],
              "sources": next((t.get("sources", {}) for t in ctx.cfg.get("tabs", []) if canon(t.get("name")) == canon(i.name)), {})})


def initiative_add(ns):
    import du as dumain
    ctx = Ctx(resolve_doc(ns))
    area = ctx.area(ns.area)
    if not any(same_person(ctx.me, a) for a in (area.owner, ctx.owner)) and not ns.for_owner:
        print(f"NOTE: {area.name} belongs to {area.owner}; they should confirm this initiative.", file=sys.stderr)
    args = [ctx.id, area.title, ns.file] + (["--new"] if ns.new else [])
    if ns.dry_run:
        spec = json.load(open(ns.file))
        print("PLAN:")
        print(f"  Add initiative {spec['name']!r} (owner {spec['owner']}, updater {spec.get('updater') or area.owner}) under {area.name!r},")
        print("  with its first section and its row in the area table.")
        near = [t for t in m.similar(ctx.doc, spec["name"]) if t != area.title]
        print("  Similar tabs: " + (", ".join(near) if near else "none"))
        print("Dry run: nothing written.")
        return
    dumain.cmd_add(args)


def _update_row(ctx, i, **over):
    fresh = next(x for x in du.model(du.read_doc(ctx.id))[2] if x.tab_id == i.tab_id)
    area = next(a for a in du.model(du.read_doc(ctx.id))[1].values() if a.title == fresh.area_title)
    m.set_row(ctx.id, area.tab_id, i.name, row_for(fresh, **over))


def initiative_rename(ns):
    ctx = Ctx(resolve_doc(ns))
    i = ctx.init(ns.name)
    need_initiative_editor(ctx, ns, i, "renaming")
    if any(canon(x.name) == canon(ns.new_name) for x in ctx.inits + ctx.archived):
        raise Refused(f"an initiative named {ns.new_name!r} already exists.")

    def write():
        m.retitle(ctx.id, i.tab_id, f"{ns.new_name} ({i.owner})")
        _update_row_named(ctx, i, i.name, ns.new_name)
        if i.sections:
            note(ctx, i, f"Renamed from {i.name} to {ns.new_name} on {du.label(today())}.")
    apply(ns, [f"Rename {i.name!r} to {ns.new_name!r}: tab title, area table row, and a note in today's section if it has one."], write)


def _update_row_named(ctx, i, old_name, new_name):
    doc = du.read_doc(ctx.id)
    fresh = next(x for x in du.model(doc)[2] if x.tab_id == i.tab_id)
    area = next(a for a in du.model(doc)[1].values() if a.title == fresh.area_title)
    m.set_row(ctx.id, area.tab_id, old_name, row_for(fresh, name=new_name))


def initiative_set_owner(ns):
    ctx = Ctx(resolve_doc(ns))
    i = ctx.init(ns.name)
    need_initiative_editor(ctx, ns, i, "changing the owner")
    if not ns.person.strip():
        raise Refused("an initiative needs an owner.")
    if canon(ns.person) == canon(i.owner):
        raise Refused(f"{i.name!r} is already owned by {i.owner}.")
    warn = [] if ns.person in ctx.everyone() else [f"WARN: {ns.person!r} appears nowhere else in the doc. Check the spelling."]

    def write():
        m.retitle(ctx.id, i.tab_id, f"{i.name} ({ns.person})")
        set_header(ctx, i.tab_id, f"Owner: {i.owner}", f"Owner: {ns.person}")
        _update_row(ctx, i, owner=ns.person)
        if i.sections:
            note(ctx, i, f"Owner changed from {i.owner} to {ns.person} on {du.label(today())}.")
    apply(ns, [f"{i.name}: owner {i.owner} -> {ns.person}.", "Tab title, header, area table row, and a note in today's section if it has one."] + warn, write)


def initiative_set_updater(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "setting an updater")
    i = ctx.init(ns.name)
    if canon(ns.person) == canon(i.updater):
        raise Refused(f"{i.name!r} is already updated by {i.updater}.")
    people = {canon(k): v for k, v in ctx.settings["people"].items()}
    if canon(ns.person) not in people:
        raise Refused(f"{ns.person!r} is not in the people list, so they cannot be tagged or confirmed to have access. "
                      f"Run `person set-email {ns.person} <email>` first.")

    def write():
        set_header(ctx, i.tab_id, f"Updater: {i.updater}", f"Updater: {ns.person}")
    apply(ns, [f"{i.name}: updater {i.updater} -> {ns.person}.",
               "Reminder: the new updater needs edit access to the doc (check its sharing list)."], write)


def _backup_write(ctx, i, new):
    old, new_txt = backup_header_edit(i.header, i.backups, new)
    set_header(ctx, i.tab_id, old, new_txt)  # the header line is the record; a backup change is never an update section


def initiative_add_backup(ns):
    if ns.all and len(ns.target) != 1:
        raise Refused("add-backup --all takes only a person: add-backup --all <person>.")
    if not ns.all and len(ns.target) != 2:
        raise Refused("add-backup needs an initiative and a person: add-backup <initiative> <person>, or add-backup --all <person>.")
    ctx = Ctx(resolve_doc(ns))
    if ns.all:
        person = ns.target[0]
        states = {i.title: ctx.state(i) for i in ctx.inits}
        todo, skipped = backup_targets(ctx.inits, states, person)
        if not todo:
            raise Refused(f"nothing to do: {person!r} is already the updater or a backup of every open or paused initiative.")
        for i in todo:
            check_add_backup(i, person, ctx.settings["people"])
            need_initiative_editor(ctx, ns, i, "adding a backup")
        plan = [f"Add {person} as a backup on {len(todo)} initiative(s): {', '.join(i.name for i in todo)}."]
        if skipped:
            plan.append("Skipped: " + ", ".join(f"{i.name} ({why})" for i, why in skipped) + ".")
        plan.append("Header line on each. Each backup needs edit access to the doc.")

        def write_all():
            for i in todo:
                _backup_write(ctx, i, i.backups + [person])
        apply(ns, plan, write_all)
        return
    i, person = ctx.init(ns.target[0]), ns.target[1]
    need_initiative_editor(ctx, ns, i, "adding a backup")
    check_add_backup(i, person, ctx.settings["people"])
    apply(ns, [f"{i.name}: backups {', '.join(i.backups) or '(none)'} -> {', '.join(i.backups + [person])}.",
               "Header line only; no section is written.",
               "Reminder: the backup needs edit access to the doc (check its sharing list)."],
          lambda: _backup_write(ctx, i, i.backups + [person]))


def initiative_remove_backup(ns):
    ctx = Ctx(resolve_doc(ns))
    i, person = ctx.init(ns.initiative), ns.person
    need_initiative_editor(ctx, ns, i, "removing a backup")
    check_remove_backup(i, person)
    keep = [b for b in i.backups if canon(b) != canon(person)]
    apply(ns, [f"{i.name}: backups {', '.join(i.backups)} -> {', '.join(keep) or '(none)'}.", "Header line only; no section is written."],
          lambda: _backup_write(ctx, i, keep))


def initiative_move_now(ctx, ns, name, area_name):
    i, dst = ctx.init(name), ctx.area(area_name)
    if i.area_title == dst.title:
        raise Refused(f"{i.name!r} is already in {dst.name!r}.")
    src = ctx.area_of(i)
    m.move_tab(ctx.id, i.tab_id, dst.tab_id, len(m.find_tab(ctx.doc, dst.tab_id).get("childTabs", [])))
    set_header(ctx, i.tab_id, f"Area: {i.area_name}", f"Area: {dst.name}")
    if src and i.name in [r[0] for r in src.rows()]:
        m.delete_row(ctx.id, src.tab_id, i.name)
    m.set_row(ctx.id, dst.tab_id, i.name, row_for(i))
    if i.sections:
        note(ctx, i, f"Moved from {i.area_name} to {dst.name} on {du.label(today())}.")


def initiative_move(ns):
    ctx = Ctx(resolve_doc(ns))
    i, dst = ctx.init(ns.name), ctx.area(ns.area)
    need_initiative_editor(ctx, ns, i, "moving")
    if i.area_title == dst.title:
        raise Refused(f"{i.name!r} is already in {dst.name!r}.")
    apply(ns, [f"Move {i.name!r} from {i.area_name!r} to {dst.name!r}: tab, Area line, both area tables, and a note in today's section if it has one."],
          lambda: initiative_move_now(ctx, ns, ns.name, ns.area))


def _lifecycle_spec(ctx, i, verb, ns):
    """The section a lifecycle verb writes. Words come from the person (reason, outcome); the layout is the skill's."""
    day = today()
    lab = du.label(day)
    me = ctx.me or ctx.owner
    ms_sec, st_sec = i.newest("milestone"), i.newest("status")
    ms = ms_sec.milestone if ms_sec else "No date set yet"
    spec = {"date": day.isoformat(), "blocked": "None.", "links": [], "extra": [], "author": me,
            "cover_for": None if same_person(me, i.updater) else i.updater}
    if verb == "pause":
        spec.update(status="⚪", milestone=ms, progress=f"Paused {lab}: {ns.reason}.",
                    green_when=f"{i.updater} sets this when work resumes.")
    elif verb == "done":
        spec.update(status="🟢", milestone=f"{du.commitment(ms)}, done {lab}", progress=f"Done {lab}: {ns.outcome}.")
    elif verb == "stop":
        spec.update(status="⚪", milestone=f"None, stopped {lab}", progress=f"Stopped {lab}: {ns.reason}.",
                    green_when="Not planned.")
    else:  # resume, reopen: the person gives the colour and the next milestone
        if not ns.status or not ns.milestone:
            raise Refused(f"{verb} needs --status (🟢, 🟡 or 🔴) and --milestone (with its date, or 'No date set yet').")
        why = f"Reopened {lab}: {ns.reason}." if verb == "reopen" else f"Resumed {lab}."
        spec.update(status=ns.status, milestone=ns.milestone, progress=why)
        if ns.status != "🟢" and ns.green_when:
            spec["green_when"] = ns.green_when
    return spec


def initiative_lifecycle(ns):
    import tempfile
    import du as dumain
    verb = ns.verb
    ctx = Ctx(resolve_doc(ns))
    i = ctx.init(ns.name, archived=(verb == "archive"))
    need_initiative_editor(ctx, ns, i, verb) if verb != "archive" else need_owner(ctx, ns, "archiving")
    check_transition(verb, ctx.state(i), i.name)
    if verb == "archive":
        s = i.sections[0]
        text = f"{'done' if ctx.state(i) == 'done' else 'stopped'} {du.label(s.date)}"
        apply(ns, [f"Move {i.title!r} under Archive, remove its area table row, list it on the Archive tab as {text!r}."],
              lambda: dumain.cmd_archive([ctx.id, i.title, text]))
        return
    spec = _lifecycle_spec(ctx, i, verb, ns)
    plan = [f"{i.name}: {ctx.state(i)} -> {TRANSITIONS[verb][1]}.", f"New section: {spec['status']} {spec['progress']}",
            f"Next milestone: {spec['milestone']}"]
    if verb in ("done", "stop"):
        plan.append("Add a line to the area tab's Done list.")
    if verb == "done":
        plan.append("Colour is set to 🟢 for a finished initiative (my inference; change it if wrong).")

    def write():
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(spec, f, ensure_ascii=False)
        try:
            dumain.cmd_section([ctx.id, i.title, f.name])
        finally:
            os.unlink(f.name)
        c2 = Ctx(ctx.id)
        _update_row(c2, i)
        area = c2.area_of(next(x for x in c2.inits if x.tab_id == i.tab_id))
        lab = du.label(today())
        if verb == "done":
            add_done_line(c2, area, f"{i.name}: done {lab}, {ns.outcome}.")
        elif verb == "stop":
            add_done_line(c2, area, f"{i.name}: stopped {lab}, {ns.reason}.")
        elif verb == "reopen":
            remove_done_line(c2, area, i.name)
    apply(ns, plan, write)


# ---------- person ----------

def person_rows(ctx):
    rows = []
    for n in sorted(ctx.everyone(), key=canon):
        owns = [a.name for a in ctx.areas.values() if same_person(a.owner, n)]
        own_i = [i.name for i in ctx.inits if same_person(i.owner, n)]
        upd = [i.name for i in ctx.inits if same_person(i.updater, n)]
        rd = any(same_person(r["name"], n) for r in ctx.settings["readers"])
        rows.append({"person": n, "email": ctx.settings["people"].get(n, ""), "areas": len(owns), "owns": len(own_i),
                     "updates": len(upd), "reader": "yes" if rd else "", "_owns": own_i, "_updates": upd, "_areas": owns})
    return rows


def person_list(ns):
    rows = person_rows(Ctx(resolve_doc(ns)))
    table(ns, [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
          ["person", "email", "areas", "owns", "updates", "reader"])


def person_show(ns):
    ctx = Ctx(resolve_doc(ns))
    r = next((x for x in person_rows(ctx) if canon(x["person"]) == canon(ns.name)), None)
    if r is None:
        raise Refused(f"nobody named {ns.name!r} in the doc. Known: {', '.join(sorted(ctx.everyone()))}.")
    card(ns, {"person": r["person"], "email": r["email"] or "(none; person set-email)", "owns areas": r["_areas"],
              "owns initiatives": r["_owns"], "updates initiatives": r["_updates"], "reader": bool(r["reader"])})


def person_set_email(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "the people list")
    if "@" not in ns.email:
        raise Refused("that is not an email address.")
    people = dict(ctx.settings["people"])
    people[ns.name] = ns.email
    apply(ns, [f"{ns.name}: email {ctx.settings['people'].get(ns.name) or '(none)'} -> {ns.email}"],
          lambda: du.settings_set(ctx.id, people=people))


# ---------- reader ----------

def reader_list(ns):
    ctx = Ctx(resolve_doc(ns))
    table(ns, ctx.settings["readers"], ["name", "channel", "email"])


def reader_add(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "the readers")
    r = {"name": ns.name, "channel": ns.channel, "email": ns.email}
    check_reader(r)
    cur = ctx.settings["readers"]
    if any(canon(x["name"]) == canon(ns.name) for x in cur):
        raise Refused(f"{ns.name!r} is already a reader. Use `reader set-channel`.")
    apply(ns, [f"Readers: {[x['name'] for x in cur]} -> {[x['name'] for x in cur + [r]]}"],
          lambda: du.settings_set(ctx.id, readers=cur + [r]))


def reader_remove(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "the readers")
    cur = ctx.settings["readers"]
    keep = [x for x in cur if canon(x["name"]) != canon(ns.name)]
    if len(keep) == len(cur):
        raise Refused(f"{ns.name!r} is not a reader. Readers: {', '.join(x['name'] for x in cur) or 'none'}.")
    apply(ns, [f"Readers: {[x['name'] for x in cur]} -> {[x['name'] for x in keep]}"],
          lambda: du.settings_set(ctx.id, readers=keep))


def reader_set_channel(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "the readers")
    cur = ctx.settings["readers"]
    hit = next((x for x in cur if canon(x["name"]) == canon(ns.name)), None)
    if hit is None:
        raise Refused(f"{ns.name!r} is not a reader.")
    new = [dict(x, channel=ns.channel) if x is hit else x for x in cur]
    check_reader(next(x for x in new if x["name"] == hit["name"]))
    apply(ns, [f"{hit['name']}: channel {hit['channel']} -> {ns.channel}"], lambda: du.settings_set(ctx.id, readers=new))


# ---------- source (local to this person; backed up to their own Drive, never on the doc) ----------

def _my_tab(cfg, name, ctx=None, create=False):
    """The saved-sources entry for a tab you may keep sources on (updater, backup or doc owner; see source_valid).
    With the doc (ctx) the rule is checked against it; without a doc, being in your config is the evidence."""
    tabs = cfg.get("tabs", [])
    hit = [t for t in tabs if canon(t.get("name")) == canon(name) and t.get("kind") == "initiative"]
    if ctx is not None:
        i = ctx.init(name)
        if not source_valid(cfg.get("me", ""), ctx.owner, i.updater, i.backups):
            raise Refused(f"you are not the updater, a backup or the doc owner of {i.name!r} (updater {i.updater}"
                          f"{', backups ' + ', '.join(i.backups) if i.backups else ''}). Sources are saved only for those tabs.")
        if not hit and create:
            hit = [{"tab_id": i.tab_id, "kind": "initiative", "name": i.name, "area": i.area_name, "owner": i.owner, "sources": {}}]
            tabs.append(hit[0])
            cfg["tabs"] = tabs
    if not hit:
        mine = ", ".join(t["name"] for t in tabs if t.get("kind") == "initiative") or "none"
        raise Refused(f"{name!r} is not a tab you update or back up. Yours: {mine}. Sources are saved only for your own tabs.")
    return hit[0]


def source_list(ns):
    cfg = load_config()
    rows = [{"initiative": t["name"], "kind": k, "ref": r, "private": "yes" if k in PRIVATE_KINDS else ""}
            for t in cfg.get("tabs", []) if t.get("kind") == "initiative" and (not ns.name or canon(t["name"]) == canon(ns.name))
            for k, refs in t.get("sources", {}).items() for r in refs]
    table(ns, rows, ["initiative", "kind", "ref", "private"])


def source_add(ns):
    cfg = load_config()
    check_source(ns.kind, ns.ref)
    doc_id = ns.doc or cfg.get("doc_id")
    t = _my_tab(cfg, ns.name, Ctx(resolve_doc(ns)) if doc_id else None, create=True)
    if ns.ref in t.setdefault("sources", {}).get(ns.kind, []):
        print(f"Already saved: {ns.kind} {ns.ref} on {t['name']}.")
        return
    apply(ns, [f"{t['name']}: add {ns.kind} {ns.ref}" + (" (private: read for drafting, never linked)" if ns.kind in PRIVATE_KINDS else "")],
          lambda: (t["sources"].setdefault(ns.kind, []).append(ns.ref), save_config(cfg)))


def source_remove(ns):
    cfg = load_config()
    t = _my_tab(cfg, ns.name)
    if ns.ref not in t.get("sources", {}).get(ns.kind, []):
        raise Refused(f"{ns.kind} {ns.ref!r} is not saved on {t['name']}.")

    def write():
        t["sources"][ns.kind].remove(ns.ref)
        if not t["sources"][ns.kind]:
            del t["sources"][ns.kind]
        save_config(cfg)
    apply(ns, [f"{t['name']}: remove {ns.kind} {ns.ref}"], write)


# ---------- section (the daily write; the agent supplies the words) ----------

def section_write(ns):
    """Write the section, then refresh that initiative's row in its area table so the table never lags the tab."""
    import du as dumain
    doc = resolve_doc(ns)
    if dumain.cmd_section([doc, ns.tab, ns.file]) is False:
        return  # dry run: the PLAN is printed, nothing written
    ctx = Ctx(doc)
    i = next((x for x in ctx.inits if ns.tab in (x.title, x.name)), None)
    if i is not None:
        _update_row(ctx, i)
        print(f"Area table row refreshed for {i.name}.")


def section_show(ns):
    import du as dumain
    dumain.cmd_today([resolve_doc(ns), ns.tab, ns.date])


def section_lint(ns):
    import du as dumain
    dumain.cmd_lint([resolve_doc(ns), ns.tab, ns.file])


# Only what the old add-backup / remove-backup wrote: a section whose whole content is that one automatic note.
BACKUP_NOTE = re.compile(r"^Progress: Backup .+ (added|removed) on [A-Z][a-z]{2} [A-Z][a-z]{2} \d{1,2}\. \(from [^()]+\)$")
CARRIED = ("Next milestone:", "Blocked on:", "Green when:")


def note_only_problem(init, sec):
    """Why `sec` may not be removed, or None when it is nothing but an automatic backup note carrying its older
    section's status, milestone, Blocked on and Green when."""
    if len(init.sections) < 2:
        return "it is the only section on the tab"
    texts = [t for t, _ in sec.lines]
    notes = [t for t in texts if t.startswith("Progress:")]
    if len(notes) != 1 or not BACKUP_NOTE.match(notes[0]):
        return "its content is not an automatic backup note"
    k = init.sections.index(sec)
    older = [t for t, _ in init.sections[k + 1].lines] if k + 1 < len(init.sections) else None
    for t in texts:
        if t in notes:
            continue
        if not (t in older if older is not None else (t[:1] in du.STATUSES or t.startswith(CARRIED))):
            return f"it holds more than the note ({t[:40]!r})"
    return None


def section_remove(ns):
    """Remove a section that is only an automatic change note, never anything else. No --force."""
    ctx = Ctx(resolve_doc(ns))
    if ns.all:
        if len(ns.target) != 1:
            raise Refused("remove --all takes only a date: section remove --all <date>.")
        day_s, tabs = ns.target[0], ctx.inits
    else:
        if len(ns.target) != 2:
            raise Refused("section remove needs a tab and a date: section remove <tab> <date>, or --all <date>.")
        day_s, tabs = ns.target[1], [ctx.init(ns.target[0])]
    try:
        day = dt.date.fromisoformat(day_s)
    except ValueError:
        raise Refused(f"{day_s!r} is not a date (YYYY-MM-DD).")
    todo, skipped = [], []
    for i in tabs:
        sec = next((x for x in i.sections if x.date == day), None)
        if sec is None:
            if not ns.all:
                raise Refused(f"{i.name!r} has no section for {du.label(day)}.")
            continue
        why = note_only_problem(i, sec)
        if why:
            if not ns.all:
                raise Refused(f"will not remove {du.label(day)} on {i.name!r}: {why}.")
            skipped.append(f"{i.name} ({why})")
        else:
            need_initiative_editor(ctx, ns, i, "removing a section")
            todo.append((i, sec))
    if not todo:
        raise Refused(f"no section for {du.label(day)} is only an automatic backup note." + (" Left alone: " + "; ".join(skipped) + "." if skipped else ""))

    def write():
        for i, sec in todo:
            fresh = next(x for x in du.model(du.read_doc(ctx.id))[2] if x.tab_id == i.tab_id)
            s2 = next(x for x in fresh.sections if x.date == day)
            if note_only_problem(fresh, s2):  # re-check against the doc as it is now
                print(f"SKIPPED {i.name}: changed since the review.")
                continue
            k = fresh.sections.index(s2)
            end = fresh.sections[k + 1].heading_el["startIndex"] if k + 1 < len(fresh.sections) else fresh.body[-1]["endIndex"] - 1
            du.batch(ctx.id, [{"deleteContentRange": {"range": {"startIndex": s2.heading_el["startIndex"], "endIndex": end,
                                                                "tabId": fresh.tab_id}}}])
            gone = next(x for x in du.model(du.read_doc(ctx.id))[2] if x.tab_id == i.tab_id)
            print(("REMOVED " if not any(x.date == day for x in gone.sections) else "DID NOT REMOVE ") + i.title)
    plan = [f"Remove the {du.label(day)} section from {len(todo)} tab(s), each only an automatic backup note: " + ", ".join(i.name for i, _ in todo) + "."]
    if skipped:
        plan.append("Left alone: " + "; ".join(skipped) + ".")
    apply(ns, plan, write)


# ---------- day (the close-out cycle, doc owner) ----------

def _day_owner(ns):
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "closing out the day")
    return ctx.id


def day_sweep(ns):
    """Preview by default (nothing written); --publish writes the Unconfirmed sections. --tag posts the comment
    that tags the updaters, only after the doc owner said yes to the exact list."""
    import du as dumain
    ctx = Ctx(resolve_doc(ns))
    need_owner(ctx, ns, "closing out the day")
    args = [ctx.id, ns.date, "--owner", ctx.owner]
    for d in ns.decide or []:
        args += ["--decide", d]
    if ns.publish:
        args.append("--publish")
    if ns.tag:
        args += ["--tag", "--people", json.dumps(ctx.settings["people"])]
    sys.exit(dumain.run("sweep.py", *args))


def day_overview(ns):
    import du as dumain
    doc_id = _day_owner(ns)
    sys.exit(dumain.run("overview.py", doc_id, ns.date, ns.time, *(["--publish"] if ns.publish else [])))


def day_decisions(ns):
    import du as dumain
    dumain.cmd_decisions([_day_owner(ns), ns.reader, ns.rows] + ([ns.links] if ns.links else []))


def day_send(ns):
    import du as dumain
    doc_id = _day_owner(ns)
    dumain.cmd_send([doc_id] + (["--confirmed"] if ns.confirmed else []))


def discover(ns):
    import du as dumain
    dumain.cmd_dedupe([resolve_doc(ns), ns.file])


# ---------- doctor (read only: finds problems, names the command that fixes each, never fixes) ----------

def finding(level, check, detail, fix=""):
    return {"level": level, "check": check, "detail": detail, "fix": fix}


def has_email(people, name):
    return any(canon(k) == canon(name) and "@" in v for k, v in people.items())


def check_people(people, inits, areas):
    """Rules 1 and 2 of the SSOT: owners exist, the updater is in the people list with an email, titles read
    `<Name> (<owner>)`, each initiative sits under an area. Emails come first: nothing else can be tagged without them."""
    out = []
    for n in sorted({i.updater for i in inits if i.updater}, key=canon):
        if not has_email(people, n):
            out.append(finding("fail", "updater has an email", f"{n} updates a tab but has no email in the people list.",
                               f"person set-email {n} <email>"))
    for i in inits:
        if not i.owner:
            out.append(finding("fail", "initiative has an owner", f"tab {i.title!r} should read '<Name> (<owner>)' but has no owner.",
                               f"initiative set-owner {i.name!r} <person>"))
        if not i.updater:
            out.append(finding("fail", "initiative has an updater", f"{i.title!r} names no updater.",
                               f"initiative set-updater {i.name!r} <person>"))
        if i.area_title not in areas:
            out.append(finding("fail", "initiative sits under an area", f"{i.title!r} is not under an area tab.",
                               f"initiative move {i.name!r} --area <area>"))
    for a in areas.values():
        if not a.owner:
            out.append(finding("fail", "area has an owner", f"area {a.title!r} has no owner in its title.",
                               f"area set-owner {a.name!r} <person>"))
    return out


def check_readers(readers):
    out = []
    for r in readers:
        try:
            check_reader(r)
        except Refused as e:
            out.append(finding("fail", "reader is valid", f"reader {r.get('name') or '(no name)'!s}: {str(e).removeprefix('REFUSED: ').removesuffix(' Nothing written.')}",
                               f"reader remove {r.get('name', '')!r}, then reader add <name> <email> --channel email"))
    return out


def weekdays_between(a, b):
    """Weekdays after a, up to and including b."""
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        n += d.weekday() < 5
    return n


def check_freshness(inits, areas, states, today, stale_after=2):
    """Warnings only: a live tab with no update for `stale_after` weekdays, or none ever; an area with no live tab."""
    out = []
    for i in inits:
        if states.get(i.title) != "open":
            continue
        if not i.sections:
            out.append(finding("warn", "tab has an update", f"{i.title!r} has no daily section yet.",
                               f"section write {i.name!r} SECTION.json"))
            continue
        gap = weekdays_between(i.sections[0].date, today)
        if gap >= stale_after:
            out.append(finding("warn", "tab is current", f"{i.title!r} last updated {du.label(i.sections[0].date)} ({gap} weekdays ago).",
                               f"section write {i.name!r} SECTION.json, or initiative pause {i.name!r} --reason <why>"))
    for a in areas.values():
        if not any(i.area_title == a.title and states.get(i.title) in ("open", "paused") for i in inits):
            out.append(finding("warn", "area has work", f"area {a.title!r} has no open or paused initiative.",
                               f"initiative add INIT.json --area {a.name!r}, or area remove {a.name!r}"))
    return out


def check_sources(cfg, inits=None, owner=""):
    """Every saved source sits on a tab you update or back up, or any tab if you are the doc owner (source_valid)."""
    out, me = [], cfg.get("me", "")
    tabs = [t for t in cfg.get("tabs", []) if t.get("sources")]
    for t in tabs:
        refs = [(k, r) for k, rs in t["sources"].items() for r in rs]
        fix = "; ".join(f"source remove {t.get('name', '')!r} {k} {r}" for k, r in refs[:2]) + (" ..." if len(refs) > 2 else "")
        if t.get("kind") != "initiative":
            out.append(finding("fail", "source on a tab you update", f"sources saved on {t.get('name')!r}, which is not an initiative tab.", fix))
        elif inits is not None:
            hit = [i for i in inits if canon(i.name) == canon(t.get("name"))]
            if not hit:
                out.append(finding("fail", "source on a tab you update", f"sources saved on {t.get('name')!r}, which is not a tab in the doc.", fix))
            elif not source_valid(me, owner, hit[0].updater, hit[0].backups):
                out.append(finding("fail", "source on a tab you update",
                                   f"sources saved on {t.get('name')!r}, whose updater is {hit[0].updater} (backups: "
                                   f"{', '.join(hit[0].backups) or 'none'}); {me or 'you'} are neither, nor the doc owner.", fix))
    if tabs and not any(f["check"] == "source on a tab you update" for f in out):
        out.append(finding("ok", "source on a tab you update", f"{len(tabs)} tab(s) with saved sources" +
                           ("" if inits is not None else " (updater not checked without the doc)")))
    return out


def check_no_backup(inits, states):
    """Warnings only: an open initiative nobody backs up."""
    return [finding("warn", "initiative has a backup", f"{i.title!r} has no backup if {i.updater} is out.",
                    f"initiative add-backup '{i.name}' <person>")
            for i in inits if states.get(i.title) == "open" and not i.backups]


def check_backup(local_md5, remote):
    """remote: None (no Drive copy) or the Drive file's md5."""
    if local_md5 is None:
        return finding("warn", "Drive backup of config", "no local config to back up.", "doc join")
    if remote is None:
        return finding("warn", "Drive backup of config", "no copy of the config on your Drive.", "doc sync")
    if remote != local_md5:
        return finding("warn", "Drive backup of config", "the Drive copy differs from the local config.", "doc sync")
    return finding("ok", "Drive backup of config", "the Drive copy matches.")


def machine_findings():
    out = []
    try:
        du.gws("drive", "about", "get", "--params", json.dumps({"fields": "user"}))
        out.append(finding("ok", "Google sign-in", "gws reaches Drive."))
        online = True
    except (RuntimeError, OSError, ValueError) as e:
        out.append(finding("fail", "Google sign-in", f"gws cannot reach Drive ({str(e).splitlines()[-1][:120] if str(e) else 'no detail'}).", "gws auth login"))
        online = False
    path = config_path()
    cfg = None
    try:
        cfg = json.load(open(path))
        out.append(finding("ok", "config readable", path))
    except FileNotFoundError:
        out.append(finding("fail", "config readable", f"no config at {path}.", "doc join"))
    except (ValueError, OSError) as e:
        out.append(finding("fail", "config readable", f"{path} cannot be read ({e}).", f"fix the JSON in {path}, or restore it with doc sync"))
    if cfg is not None:
        if not cfg.get("me"):
            out.append(finding("fail", "config names you", "'me' is not set.", "doc join"))
        out.append(("sources", cfg))
    remote, local = None, None
    if os.path.isfile(path):
        import backup
        local = backup._md5(path)
        if online:
            try:
                root = backup._list("root", backup.ROOT, folder=True)
                kit = root and backup._list(root[0]["id"], backup.SUB, folder=True)
                hit = kit and backup._list(kit[0]["id"], "config.json", folder=False)
                remote = hit[0].get("md5Checksum") if hit else None
            except Exception as e:  # Drive unreachable is its own finding above
                out.append(finding("warn", "Drive backup of config", f"could not look ({str(e)[:100]}).", "doc sync"))
                return out
    if online or local is None:
        out.append(check_backup(local, remote))
    out.append(finding("skip", "installed version vs latest", "skipped: the kit records no version it can compare offline."))
    return out


LAYOUT_FIX = "section show '<tab>' <date>, correct it, then section write '<tab>' SECTION.json"


def parse_layout(out):
    """verify.py prints 'FAIL <check>  <detail>' and usability.py 'ISSUE <text>'. Each becomes a warning.
    'has a section for <today>' is dropped: the stale-update check already says it, and kindly on weekends."""
    out_f = []
    for line in out.splitlines():
        m = re.match(r"(FAIL|ISSUE) (.+)", line)
        if m and ": has a section for " not in m.group(2):
            out_f.append(finding("warn", "layout" if m.group(1) == "FAIL" else "readability", m.group(2).strip()[:200], LAYOUT_FIX))
    return out_f


def layout_findings(doc_id, day):
    out = []
    since = ["--since", day]
    for script, extra in (("verify.py", ["--started", "1970-01-01T00:00:00Z"]), ("usability.py", [])):
        p = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), script), doc_id, day, *since, *extra],
                           capture_output=True, text=True, timeout=600, env={k: v for k, v in os.environ.items() if k != "DU_TEST"})
        found = parse_layout(p.stdout)
        if p.returncode and not re.search(r"checks passed|usability issues", p.stdout):
            out.append(finding("warn", f"{script} ran", f"{script} stopped: {(p.stderr.strip().splitlines() or ['no output'])[-1][:150]}", "doctor --only-doc"))
        out += found
    return out


def doc_findings(ns):
    try:
        ctx = Ctx(resolve_doc(ns))
    except (SystemExit, RuntimeError) as e:
        return [finding("fail", "doc opens", str(e).splitlines()[-1][:160] if str(e) else "cannot read the doc",
                        "pass --doc <link>, or doc create STRUCTURE.json")], None
    states = {i.title: ctx.state(i) for i in ctx.inits}
    out = check_people(ctx.settings["people"], ctx.inits, ctx.areas) + check_readers(ctx.settings["readers"]) \
        + check_freshness(ctx.inits, ctx.areas, states, today()) + check_no_backup(ctx.inits, states) + layout_findings(ctx.id, today().isoformat())
    if not any(f["level"] == "fail" for f in out):
        out.insert(0, finding("ok", "doc rules", f"{len(ctx.areas)} area(s), {len(ctx.inits)} initiative(s), people and readers valid."))
    return out, ctx


def doctor(ns):
    result = {}
    if not ns.only_doc:
        mach = machine_findings()
        cfg = next((x[1] for x in mach if isinstance(x, tuple)), None)
        mach = [x for x in mach if not isinstance(x, tuple)]
        result["machine"] = mach
    if not ns.local:
        doc, ctx = doc_findings(ns)
        result["doc"] = doc
        if not ns.only_doc and cfg is not None:
            result["machine"] += check_sources(cfg, ctx.inits if ctx else None, ctx.owner if ctx else "")
    elif not ns.only_doc and cfg is not None:
        result["machine"] += check_sources(cfg)
    fails = sum(f["level"] == "fail" for v in result.values() for f in v)
    warns = sum(f["level"] == "warn" for v in result.values() for f in v)
    if ns.json:
        print(json.dumps({**result, "fail": fails, "warn": warns}, ensure_ascii=False, indent=1))
    else:
        titles = {"machine": "This machine", "doc": "The doc"}
        for sec, items in result.items():
            print(titles[sec])
            for f in sorted(items, key=lambda f: ("fail", "warn", "ok", "skip").index(f["level"])):
                print(f"  {f['level'].upper():<4}  {f['check']}: {f['detail']}")
                if f["fix"]:
                    print(f"        fix: {f['fix']}")
            print()
        print(f"{fails} fail, {warns} warn. Nothing was changed.")
    sys.exit(1 if fails else 0)


# ---------- feedback ----------

def feedback_add(ns):
    """Add one dated, named entry to the Feedback tab (newest first). Never blocks or undoes a publish."""
    import feedback as fb
    doc = resolve_doc(ns)
    ctx = Ctx(doc)
    if not ctx.me:
        raise Refused("no name in ~/.daily-update/config.json (me); run `doc join` first.")
    bad = fb.lint(ns.text)
    if bad:
        raise Refused("; ".join(bad))
    label = du.label(today())
    line = fb.entry(label, ctx.me, ns.text)
    try:
        status, _ = fb.add(doc, label, ctx.me, ns.text, dry=True)
    except LookupError as e:
        raise Refused(f"{e} Ask the doc owner to add it; nothing else is affected.")
    except ValueError as e:
        raise Refused(str(e))
    if status == "duplicate":
        print(f"Already on the Feedback tab, not added again: {line}")
        return
    if apply(ns, [f"Add to the top of 'Feedback so far' on the Feedback tab: {line}"],
             lambda: print("Re-read:", fb.add(doc, label, ctx.me, ns.text)[1])):
        return


def feedback_list(ns):
    import feedback as fb
    tab, _ = fb.find_tab(du.read_doc(resolve_doc(ns)))
    if tab is None:
        raise Refused("this doc has no Feedback tab under the Update guide tab.")
    rows = fb.list_entries(tab) or []
    if ns.json:
        print(json.dumps(rows, indent=2))
    else:
        print("\n".join(rows) if rows else "No feedback yet.")


def feedback_lint(ns):
    import feedback as fb
    bad = fb.lint(ns.text)
    print("OK" if not bad else "BLOCK: " + "; ".join(bad))
    if bad:
        sys.exit(1)


# ---------- grammar ----------

def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--doc", help="doc id or link (default: doc_id in ~/.daily-update/config.json)")
    common.add_argument("--json", action="store_true", help="print JSON (reads)")
    common.add_argument("--dry-run", action="store_true", help="show the PLAN and write nothing (writes)")
    common.add_argument("--for-owner", action="store_true", help="run a doc-owner command for the doc owner, who said so")
    root = argparse.ArgumentParser(prog="du.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    nouns = root.add_subparsers(dest="noun", metavar="<noun>", required=True)

    def group(name, help_):
        sub = nouns.add_parser(name, help=help_).add_subparsers(dest="verb", metavar="<verb>", required=True)
        return sub

    def verb(sub, name, fn, help_, *args, **opts):
        p = sub.add_parser(name, help=help_, description=help_, parents=[common])
        for a in args:
            if isinstance(a, tuple):
                p.add_argument(a[0], **a[1])
            else:
                p.add_argument(a)
        for flag, kw in opts.items():
            p.add_argument("--" + flag.replace("_", "-"), **kw)
        p.set_defaults(fn=fn)
        return p

    g = group("doc", "the status doc")
    verb(g, "create", doc_create, "create a doc from STRUCTURE.json; you become the doc owner", "structure")
    verb(g, "show", doc_show, "owner, you, areas, initiatives by state, readers")
    verb(g, "sync", doc_sync, "back up ~/.daily-update to your Drive, restoring older local files")

    g = group("area", "areas: groups of initiatives, each with an owner")
    verb(g, "list", area_list, "every area with counts and colour")
    verb(g, "show", area_show, "one area and its initiatives", "name")
    verb(g, "add", area_add, "add an area (doc owner)", "name", "owner")
    verb(g, "rename", area_rename, "rename an area (doc owner)", "name", "new_name")
    verb(g, "set-owner", area_set_owner, "change an area's owner (doc owner)", "name", "person")
    verb(g, "set-headline", area_set_headline, "replace the area headline: '<sentences> (Fri Nov 6)'", "name", "text")
    verb(g, "merge", area_merge, "move every initiative of one area into another, then archive it (doc owner)", "name",
         ("into", {"metavar": "INTO"}))
    verb(g, "remove", area_remove, "move an empty area under Archive (doc owner; never deletes)", "name")

    g = group("initiative", "initiatives: the tabs people update")
    verb(g, "list", initiative_list, "list initiatives; filter by area, owner, updater, state", **{
        "area": {"help": "area name"}, "owner": {}, "updater": {},
        "state": {"choices": STATES}, "all": {"action": "store_true", "help": "include archived"}})
    verb(g, "show", initiative_show, "one initiative: owner, updater, backups, state, newest section, your sources", ("name", {}))
    verb(g, "add", initiative_add, "add an initiative from INIT.json under an area", "file",
         area={"required": True}, new={"action": "store_true", "help": "add even if a similar tab exists (after the person confirms)"})
    verb(g, "rename", initiative_rename, "rename an initiative", "name", "new_name")
    verb(g, "move", initiative_move, "move an initiative to another area", "name", area={"required": True})
    verb(g, "set-owner", initiative_set_owner, "change who is accountable for the work", "name", "person")
    verb(g, "set-updater", initiative_set_updater, "change who writes the daily update (doc owner)", "name", "person")
    verb(g, "add-backup", initiative_add_backup, "add a backup for the updater; `--all <person>` does every open or paused initiative",
         ("target", {"nargs": "+", "metavar": "ARG", "help": "<initiative> <person>, or just <person> with --all"}),
         all={"action": "store_true", "help": "every open or paused initiative (skips ones where the person is already updater or backup)"})
    verb(g, "remove-backup", initiative_remove_backup, "remove a backup", "initiative", "person")
    verb(g, "pause", initiative_lifecycle, "open -> paused (⚪)", "name", reason={"required": True})
    verb(g, "resume", initiative_lifecycle, "paused -> open; you give the colour and next milestone", "name",
         status={"choices": ["🟢", "🟡", "🔴"]}, milestone={}, green_when={})
    verb(g, "done", initiative_lifecycle, "open or paused -> done", "name", outcome={"required": True})
    verb(g, "stop", initiative_lifecycle, "open or paused -> stopped, with a reason", "name", reason={"required": True})
    verb(g, "reopen", initiative_lifecycle, "done or stopped -> open; you give the colour and next milestone", "name",
         reason={"required": True}, status={"choices": ["🟢", "🟡", "🔴"]}, milestone={}, green_when={})
    verb(g, "archive", initiative_lifecycle, "done or stopped -> archived: tab moves under Archive (doc owner)", "name")

    g = group("person", "people named in the doc, with emails")
    verb(g, "list", person_list, "everyone named as owner, updater or reader")
    verb(g, "show", person_show, "what one person owns, updates and reads", "name")
    verb(g, "set-email", person_set_email, "record a person's email (doc owner)", "name", "email")

    g = group("reader", "who gets the daily summary, and how")
    verb(g, "list", reader_list, "readers")
    verb(g, "add", reader_add, "add a reader (doc owner)", "name", "email", channel={"default": "email", "choices": list(CHANNELS)})
    verb(g, "remove", reader_remove, "remove a reader (doc owner)", "name")
    verb(g, "set-channel", reader_set_channel, "change how a reader gets it (doc owner)", "name", ("channel", {"choices": list(CHANNELS)}))

    g = group("source", "where your agent reads from, per initiative you update (local, private)")
    verb(g, "list", source_list, "your saved sources", ("name", {"nargs": "?"}))
    verb(g, "add", source_add, "save a source", "name", ("kind", {"choices": list(SOURCE_KINDS)}), "ref")
    verb(g, "remove", source_remove, "forget a source", "name", ("kind", {"choices": list(SOURCE_KINDS)}), "ref")

    g = group("section", "one day's section on an initiative tab")
    verb(g, "write", section_write, "write today's section from SECTION.json (checked first)", "tab", "file")
    verb(g, "show", section_show, "print a day's section as SECTION.json, to re-summarize", "tab", "date")
    verb(g, "lint", section_lint, "the pre-publish check, read only", "tab", "file")
    verb(g, "remove", section_remove, "remove a section that is only an automatic backup note; `--all <date>` does every tab",
         ("target", {"nargs": "+", "metavar": "ARG", "help": "<tab> <date>, or just <date> with --all"}),
         all={"action": "store_true", "help": "every tab with such a section on that date"})

    g = group("feedback", "feedback on the daily update itself (template, drafts, overview, summary)")
    verb(g, "add", feedback_add, "add one dated entry with your name, newest first; shown in the review, written after publish", "text")
    verb(g, "list", feedback_list, "entries on the Feedback tab, newest first")
    verb(g, "lint", feedback_lint, "check a line before it is added (read only)", "text")

    g = group("day", "the 3pm close-out (doc owner)")
    verb(g, "sweep", day_sweep, "preview, or with --publish write, Unconfirmed sections for tabs nobody updated today", "date",
         publish={"action": "store_true"}, tag={"action": "store_true", "help": "tag updaters in a doc comment (doc owner said yes)"},
         decide={"action": "append", "help": "'<initiative>=red|done' for a carried date that has passed"})
    verb(g, "overview", day_overview, "preview, or with --publish rebuild, the overview below its As of line", "date", "time",
         publish={"action": "store_true"})
    verb(g, "decisions", day_decisions, "write the decisions-or-help-needed table", "reader", "rows",
         ("links", {"nargs": "?"}))
    verb(g, "send", day_send, "draft the reader summary; --confirmed sends it", confirmed={"action": "store_true"})

    d = nouns.add_parser("doctor", help="read-only health check of this machine and the doc; names the fix for each problem",
                         description="Read-only health check. Prints fail, warn or ok per finding, the exact command that fixes it, "
                                     "and exits non-zero on any fail. Never fixes anything.")
    d.add_argument("--doc", help="doc id or link (default: doc_id in ~/.daily-update/config.json)")
    d.add_argument("--json", action="store_true", help="print JSON")
    one = d.add_mutually_exclusive_group()
    one.add_argument("--local", action="store_true", help="only 'This machine'")
    one.add_argument("--only-doc", action="store_true", help="only 'The doc'")
    d.set_defaults(fn=doctor)

    verb(nouns.add_parser("discover", help="find recurring work no tab covers").add_subparsers(dest="verb", metavar="<verb>", required=True),
         "check", discover, "compare CANDIDATES.json with tabs, saved sources and links (read only)", "file")
    return root


def main(argv=None):
    args = build_parser().parse_args(argv)
    before = os.environ.get("DU_DRY_RUN")
    if getattr(args, "dry_run", False):
        os.environ["DU_DRY_RUN"] = "1"  # the one switch: dudoc.gws, backup and save_config refuse to write while it is set
    try:
        if not (args.noun == "doctor" or (args.noun == "doc" and args.verb == "sync")):
            import backup
            r = None if os.environ.get("DU_NO_SYNC") else backup.auto()
            if r and (r["status"] == "skipped" or r["restored"] or r["backed_up"]):
                print(backup.report(r), file=sys.stderr)
        args.fn(args)
    finally:
        if before is None:
            os.environ.pop("DU_DRY_RUN", None)
        else:
            os.environ["DU_DRY_RUN"] = before


if __name__ == "__main__":
    main()
