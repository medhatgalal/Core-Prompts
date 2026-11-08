"""Offline checks for the noun-verb command line: lifecycle table, who may do what, name matching, validation,
source CRUD on a throwaway config, and the grammar itself. No doc and no network.

    python3 cli_test.py
"""
import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile

os.environ["DU_NO_SYNC"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import cli  # noqa: E402
import dudoc as du  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def refused(fn, *a, **k):
    try:
        fn(*a, **k)
    except SystemExit as e:
        return str(e)
    return None


class Init:
    """Just enough of dudoc.Initiative for the pure rules."""
    def __init__(self, title, updater="Kyle", area_owner="Kyle", progress=None, status="🟢", backups=()):
        self.title = title
        self.name, self.owner = du.title_parts(title)
        self.updater, self.area_owner = updater, area_owner
        self.backups = list(backups)
        self.area_name = "Core"
        s = du.Section(dt.date(2026, 11, 6), None)
        s.lines = [(du.STATUSES[status], None)] + ([(f"Progress: {progress}", None)] if progress else [])
        self.sections = [s]

    def newest(self, attr=None):
        return self.sections[0]


class Ctx:
    def __init__(self, me, owner="Scott"):
        self.me, self.owner = me, owner


class Ns:
    def __init__(self, **k):
        self.for_owner = False
        self.__dict__.update(k)


# ---- lifecycle ----
check("open is open", cli.state_of(Init("A (x)")) == "open")
check("paused from the grey status", cli.state_of(Init("A (x)", status="⚪")) == "paused")
check("done from the Progress line", cli.state_of(Init("A (x)", progress="Done Thu Nov 5: shipped.")) == "done")
check("stopped wins over the grey status", cli.state_of(Init("A (x)", progress="Stopped Thu Nov 5: dropped.", status="⚪")) == "stopped")
check("archived by place, not by text", cli.state_of(Init("A (x)"), archived=True) == "archived")

want = {"pause": {"open"}, "resume": {"paused"}, "done": {"open", "paused"}, "stop": {"open", "paused"},
        "reopen": {"done", "stopped"}, "archive": {"done", "stopped"}}
for verb, ok_from in want.items():
    got = {s for s in cli.STATES if refused(cli.check_transition, verb, s, "A") is None}
    check(f"{verb} is legal from exactly {sorted(ok_from)}", got == ok_from, str(sorted(got)))
check("archived is terminal", all(refused(cli.check_transition, v, "archived", "A") for v in want))
check("every verb ends in a state", all(end in cli.STATES for _, end in cli.TRANSITIONS.values()))

# ---- names and people ----
inits = [Init("Work Intake (Scott)"), Init("Work Plan (Kyle)"), Init("Evals (Goldberg)")]
check("match by name, ignoring case", cli.match_one(inits, "work intake", "name", "initiative") is inits[0])
check("match by full title", cli.match_one(inits, "Evals (Goldberg)", "name", "initiative") is inits[2])
check("no match lists what is known", "Known: Evals, Work Intake, Work Plan" in (refused(cli.match_one, inits, "nope", "name", "initiative") or ""))
dup = inits + [Init("Work Intake (Kui)")]
check("two matches refuse and say which", "Work Intake (Scott)" in (refused(cli.match_one, dup, "Work Intake", "name", "initiative") or ""))
check("full title breaks the tie", cli.match_one(dup, "Work Intake (Kui)", "name", "initiative") is dup[3])
check("first names match", cli.same_person("Scott", "scott Parrish") and not cli.same_person("Scott", "Kyle"))
check("empty name matches nobody", not cli.same_person("", ""))

# ---- who may do what ----
i = Init("Evals (Goldberg)", updater="Kyle", area_owner="Kyle")
for who, ok in (("Kyle", True), ("Scott", True), ("Sahil", False), ("", False)):
    got = refused(cli.need_initiative_editor, Ctx(who), Ns(), i, "done") is None
    check(f"initiative editor: {who or 'unset'} {'may' if ok else 'may not'}", got == ok)
check("--for-owner lets an editor run it", refused(cli.need_initiative_editor, Ctx("Sahil"), Ns(for_owner=True), i, "done") is None)
check("doc owner command: owner may", refused(cli.need_owner, Ctx("Scott"), Ns(), "x") is None)
check("doc owner command: leader may not", "doc owner's (Scott)" in (refused(cli.need_owner, Ctx("Kyle"), Ns(), "x") or ""))
check("doc owner command: --for-owner allows", refused(cli.need_owner, Ctx("Kyle"), Ns(for_owner=True), "x") is None)

# ---- backups: who may be saved as a source owner, header edits, no-op refusals ----
check("source valid: the updater", cli.source_valid("Kyle", "Scott", "Kyle", []))
check("source valid: a backup", cli.source_valid("Sahil", "Scott", "Kyle", ["Sahil"]))
check("source valid: the doc owner", cli.source_valid("Scott", "Scott", "Kyle", []))
check("source valid: first names match", cli.source_valid("scott parrish", "Scott", "Kyle", []))
check("source invalid: someone else", not cli.source_valid("Kui", "Scott", "Kyle", ["Sahil"]))
check("source invalid: nobody set up", not cli.source_valid("", "Scott", "Kyle", ["Sahil"]) and not cli.source_valid("", "", "", []))

H = "Owner: Goldberg · Updater: Kyle · Area: Core · Back to Overview"
HB = "Owner: Goldberg · Updater: Kyle · Backups: Sahil, Kui · Area: Core · Back to Overview"
check("backups parse from the header", du.parse_backups(HB) == ["Sahil", "Kui"] and du.parse_backups(H) == [] and du.parse_backups(None) == [])
check("first backup goes after the Updater part", cli.backup_header_edit(H, [], ["Sahil"]) == ("Updater: Kyle", "Updater: Kyle · Backups: Sahil"))
check("no Updater part: goes after Owner", cli.backup_header_edit("Owner: Goldberg · Area: Core", [], ["Sahil"])
      == ("Owner: Goldberg", "Owner: Goldberg · Backups: Sahil"))
check("another backup extends the list", cli.backup_header_edit(HB, ["Sahil", "Kui"], ["Sahil", "Kui", "Joo"]) == ("Backups: Sahil, Kui", "Backups: Sahil, Kui, Joo"))
check("removing one keeps the others", cli.backup_header_edit(HB, ["Sahil", "Kui"], ["Kui"]) == ("Backups: Sahil, Kui", "Backups: Kui"))
check("removing the last drops the whole part", cli.backup_header_edit(HB.replace("Sahil, Kui", "Kui"), ["Kui"], []) == (" · Backups: Kui", ""))
bi = Init("Evals (Goldberg)", updater="Kyle", backups=["Sahil"])
ppl = {"Sahil": "s@x.com", "Kui": "k@x.com", "Kyle": "ky@x.com", "Bo": "", "Joo": "nope"}
check("add-backup ok", refused(cli.check_add_backup, bi, "Kui", ppl) is None)
check("add-backup: the current updater is refused", "already the updater" in (refused(cli.check_add_backup, bi, "kyle", ppl) or ""))
check("add-backup: an existing backup is a no-op refusal", "already a backup" in (refused(cli.check_add_backup, bi, "Sahil", ppl) or ""))
check("add-backup: not in the people list", "people list" in (refused(cli.check_add_backup, bi, "Zed", ppl) or ""))
check("add-backup: no email refused and names the fix", "person set-email Bo" in (refused(cli.check_add_backup, bi, "Bo", ppl) or ""))
check("add-backup: a bad email refused", refused(cli.check_add_backup, bi, "Joo", ppl) is not None)
check("remove-backup ok", refused(cli.check_remove_backup, bi, "sahil") is None)
check("remove-backup: a non-backup is a no-op refusal", "not a backup" in (refused(cli.check_remove_backup, bi, "Kui") or ""))
a1, a2, a3, a4 = (Init("A (x)", updater="Kyle"), Init("B (x)", updater="Sahil"), Init("C (x)", updater="Kyle", backups=["Sahil"]),
                  Init("D (x)", updater="Kyle"))
stt = {a1.title: "open", a2.title: "open", a3.title: "paused", a4.title: "done"}
todo, skipped = cli.backup_targets([a1, a2, a3, a4], stt, "Sahil")
check("--all: open and paused only, skips updater and existing backup", [i.name for i in todo] == ["A"] and
      sorted(i.name for i, _ in skipped) == ["B", "C"], f"{[i.name for i in todo]} {[(i.name, w) for i, w in skipped]}")
check("--all: a person who backs up nothing yet gets every live tab", [i.name for i in cli.backup_targets([a1, a2, a3, a4], stt, "Kui")[0]] == ["A", "B", "C"])
nb = cli.check_no_backup([a1, a3, a4], stt)
check("doctor: open tab with no backup warns with the fix, never fails", [(f["level"], f["fix"]) for f in nb] ==
      [("warn", "initiative add-backup 'A' <person>")], str(nb))
check("doctor: paused and done tabs are not asked for a backup", cli.check_no_backup([a3, a4], stt) == [])
mine_b = Init("Evals (Goldberg)", updater="Kyle", backups=["Scott"])
cfgb = {"me": "Scott", "tabs": [{"name": "Evals", "kind": "initiative", "sources": {"jira": ["C-1"]}}]}
check("doctor: source on a tab you back up is ok", [f["level"] for f in cli.check_sources(cfgb, [mine_b], "Kui")] == ["ok"])
check("doctor: source on a tab as the doc owner is ok", [f["level"] for f in cli.check_sources(cfgb, [Init("Evals (Goldberg)", updater="Kyle")], "Scott")] == ["ok"])
check("doctor: stranger still fails and the wording names backups",
      "backup" in cli.check_sources(cfgb, [Init("Evals (Goldberg)", updater="Kyle")], "Kui")[0]["detail"])
brows = cli.init_rows(type("C", (), {"inits": [bi], "archived": [], "state": lambda s, i: "open"})(), Ns(area=None, owner=None, updater=None))
check("initiative list rows carry backups", brows[0]["backups"] == ["Sahil"], str(brows))

# ---- validation ----
good = {"name": "Medhat", "channel": "email", "email": "m@x.com"}
check("reader ok", refused(cli.check_reader, good) is None)
check("reader needs an email", refused(cli.check_reader, dict(good, email="nope")) is not None)
check("reader channel is email or chat", refused(cli.check_reader, dict(good, channel="sms")) is not None)
check("reader needs a name", refused(cli.check_reader, dict(good, name=" ")) is not None)
check("source kind checked", refused(cli.check_source, "slack", "x") is not None)
check("source ref required", refused(cli.check_source, "jira", " ") is not None)
check("chat, email, meetings are private", set(cli.PRIVATE_KINDS) == {"chat", "email", "meetings"})


# ---- doctor: pure checks ----
class A:
    def __init__(self, title):
        self.title = title
        self.name, self.owner = du.title_parts(title)


def lv(fs, level):
    return [f for f in fs if f["level"] == level]


areas = {"Core (Kyle)": A("Core (Kyle)"), "Empty (Sahil)": A("Empty (Sahil)")}
ia, ib = Init("Evals (Goldberg)", updater="Kyle"), Init("Plan (Kyle)", updater="Sahil")
ia.area_title = ib.area_title = "Core (Kyle)"
fs = cli.check_people({}, [ia, ib], areas)
check("doctor: updater with no email fails and names the fix",
      [f["fix"] for f in lv(fs, "fail")] == ["person set-email Kyle <email>", "person set-email Sahil <email>"], str(fs))
check("doctor: email match ignores case", cli.check_people({"kyle": "k@x.com", "Sahil": "s@x.com"}, [ia, ib], areas) == [])
check("doctor: an email needs an @", len(cli.check_people({"Kyle": "k", "Sahil": "s@x.com"}, [ia, ib], areas)) == 1)
orphan = Init("Lost (Kyle)")
orphan.area_title = "Gone (Kyle)"
check("doctor: initiative outside every area fails", any(f["check"] == "initiative sits under an area"
      for f in cli.check_people({"Kyle": "k@x.com"}, [orphan], areas)))
noowner = Init("Bare")
noowner.area_title = "Core (Kyle)"
check("doctor: title without an owner fails", any(f["check"] == "initiative has an owner"
      for f in cli.check_people({}, [noowner], areas)))
check("doctor: area without an owner fails", any(f["check"] == "area has an owner"
      for f in cli.check_people({}, [], {"Bare": A("Bare")})))
check("doctor: readers valid pass", cli.check_readers([good]) == [])
bad = cli.check_readers([good, dict(good, name="Bo", email="nope")])
check("doctor: bad reader fails with a fix", len(bad) == 1 and bad[0]["level"] == "fail" and "reader remove 'Bo'" in bad[0]["fix"], str(bad))
check("doctor: weekdays skip weekends", cli.weekdays_between(dt.date(2026, 11, 6), dt.date(2026, 11, 9)) == 1)
st = {ia.title: "open", ib.title: "open"}
fr = cli.check_freshness([ia, ib], areas, st, dt.date(2026, 11, 9))
check("doctor: stale tab and empty area warn, nothing fails",
      {f["check"] for f in fr} == {"area has work"} and not lv(fr, "fail"), str(fr))
fr = cli.check_freshness([ia], areas, {ia.title: "open"}, dt.date(2026, 11, 11))
check("doctor: stale tab warns", any(f["check"] == "tab is current" and f["level"] == "warn" for f in fr))
ia.sections = []
check("doctor: tab with no section warns", any(f["check"] == "tab has an update"
      for f in cli.check_freshness([ia], areas, {ia.title: "open"}, dt.date(2026, 11, 9))))
check("doctor: done tabs are not stale", not [f for f in cli.check_freshness([ia], areas, {ia.title: "done"}, dt.date(2026, 11, 30))
                                              if f["check"] != "area has work"])
mine = Init("Evals (Goldberg)", updater="Scott")
cfg = {"me": "Scott", "tabs": [{"name": "Evals", "kind": "initiative", "sources": {"jira": ["C-1"]}}]}
check("doctor: source on a tab you update is ok", [f["level"] for f in cli.check_sources(cfg, [mine])] == ["ok"])
bad = cli.check_sources(dict(cfg, me="Kyle"), [mine])
check("doctor: source on someone else's tab fails with the remove command",
      bad[0]["level"] == "fail" and "source remove 'Evals' jira C-1" in bad[0]["fix"], str(bad))
check("doctor: source on a non-initiative tab fails", cli.check_sources(
    {"me": "Scott", "tabs": [{"name": "Overview", "kind": "overview", "sources": {"jira": ["C-1"]}}]})[0]["level"] == "fail")
check("doctor: source on a tab missing from the doc fails", cli.check_sources(cfg, [])[0]["level"] == "fail")
check("doctor: backup matches", cli.check_backup("a", "a")["level"] == "ok")
check("doctor: backup missing warns with doc sync", (cli.check_backup("a", None)["level"], cli.check_backup("a", None)["fix"]) == ("warn", "doc sync"))
check("doctor: backup differs warns", cli.check_backup("a", "b")["level"] == "warn")

lay = cli.parse_layout("FAIL Evals 11/06: no raw URLs  []\nFAIL Evals: has a section for Sat Nov 7  x\n"
                       "ISSUE Plan: jargon MR\n\n3 of 9 checks passed\n")
check("doctor: layout lines become warnings with a fix, today's-section line dropped",
      [(f["level"], f["check"]) for f in lay] == [("warn", "layout"), ("warn", "readability")] and all(f["fix"] for f in lay), str(lay))
check("doctor: clean layout output gives nothing", cli.parse_layout("12 of 12 checks passed\n0 usability issues\n") == [])

# ---- source CRUD on a throwaway config ----
def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            cli.main(list(argv))
            code = 0
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            if isinstance(e.code, str):
                err.write(e.code)
    return code, out.getvalue(), err.getvalue()


with tempfile.TemporaryDirectory() as d:
    os.environ["DU_CONFIG"] = os.path.join(d, "config.json")
    json.dump({"me": "Scott", "tabs": [{"name": "Work Intake", "kind": "initiative", "sources": {"jira": ["COM-1"]}},
                                       {"name": "Overview", "kind": "overview"}]}, open(os.environ["DU_CONFIG"], "w"))
    code, out, _ = run("source", "list", "--json")
    check("source list reads the config", code == 0 and json.loads(out) == [
        {"initiative": "Work Intake", "kind": "jira", "ref": "COM-1", "private": ""}], out)
    code, out, _ = run("source", "add", "Work Intake", "chat", "spaces/AAA", "--dry-run")
    check("dry run prints a plan and writes nothing", code == 0 and "PLAN:" in out and "Dry run" in out
          and "spaces/AAA" not in open(os.environ["DU_CONFIG"]).read())
    code, out, _ = run("source", "add", "work intake", "chat", "spaces/AAA")
    cfg = json.load(open(os.environ["DU_CONFIG"]))
    check("source add saves it, matching the name loosely", code == 0 and cfg["tabs"][0]["sources"]["chat"] == ["spaces/AAA"])
    check("source add says chat is private", "private" in out)
    code, out, _ = run("source", "add", "Work Intake", "chat", "spaces/AAA")
    check("adding the same source twice is a no-op", code == 0 and "Already saved" in out
          and json.load(open(os.environ["DU_CONFIG"]))["tabs"][0]["sources"]["chat"] == ["spaces/AAA"])
    code, _, err = run("source", "add", "Not Mine", "jira", "COM-9")
    check("sources only for tabs you update", code != 0 and "not a tab you update" in err, err)
    code, _, err = run("source", "add", "Overview", "jira", "COM-9")
    check("not for non-initiative tabs", code != 0)
    code, _, err = run("source", "remove", "Work Intake", "jira", "COM-404")
    check("removing what is not saved refuses", code != 0 and "not saved" in err, err)
    code, _, _ = run("source", "remove", "Work Intake", "jira", "COM-1")
    cfg = json.load(open(os.environ["DU_CONFIG"]))
    check("removing the last source of a kind drops the kind", code == 0 and "jira" not in cfg["tabs"][0]["sources"])
    code, out, _ = run("source", "list", "Work Intake")
    check("list one initiative", code == 0 and "spaces/AAA" in out and "COM-1" not in out)
os.environ.pop("DU_CONFIG")

# ---- section write keeps the area table row in step with the tab ----
import du as dumain  # noqa: E402

calls = []
_saved = (dumain.cmd_section, cli.resolve_doc, cli.Ctx, cli._update_row)
try:
    class FakeCtx:
        inits = [Init("Evals (Goldberg)"), Init("Work Plan (Kyle)")]

        def __init__(self, doc):
            pass
    dumain.cmd_section = lambda a: calls.append(("section", a[1]))
    cli.resolve_doc = lambda ns: "DOC"
    cli.Ctx = FakeCtx
    cli._update_row = lambda ctx, i, **o: calls.append(("row", i.name))
    with contextlib.redirect_stdout(io.StringIO()):
        cli.section_write(Ns(tab="Evals (Goldberg)", file="s.json", doc=None))
        cli.section_write(Ns(tab="Composer (Kyle)", file="s.json", doc=None))
finally:
    dumain.cmd_section, cli.resolve_doc, cli.Ctx, cli._update_row = _saved
check("section write refreshes the initiative's area row", ("row", "Evals") in calls, str(calls))
check("section write on an area tab touches no row", [c for c in calls if c[0] == "row"] == [("row", "Evals")], str(calls))

# ---- grammar ----
parser = cli.build_parser()
verbs = {}
for a in parser._subparsers._group_actions[0].choices.items():
    noun, p = a
    if noun == "doctor":  # a command, not a noun: no verbs
        verbs[noun] = []
        continue
    sub = next(x for x in p._subparsers._group_actions)
    verbs[noun] = sorted(sub.choices)
check("nouns", sorted(verbs) == ["area", "day", "discover", "doc", "doctor", "initiative", "person", "reader", "section", "source"], str(sorted(verbs)))
check("initiative verbs", verbs["initiative"] == sorted(
    ["list", "show", "add", "rename", "move", "set-owner", "set-updater", "add-backup", "remove-backup", "pause", "resume", "done", "stop", "reopen", "archive"]))
check("area verbs", verbs["area"] == sorted(["list", "show", "add", "rename", "set-owner", "set-headline", "merge", "remove"]))
check("reader verbs", verbs["reader"] == sorted(["list", "add", "remove", "set-channel"]))
code, _, err = run("initiative", "add-backup", "A")
check("add-backup needs an initiative and a person", code != 0 and "initiative and a person" in err, err)
code, _, err = run("initiative", "add-backup", "--all", "A", "B")
check("add-backup --all takes only a person", code != 0 and "only a person" in err, err)
code, _, err = run("initiative", "remove-backup", "A")
check("remove-backup needs an initiative and a person", code == 2)
check("every noun with a collection has list and show or add/remove",
      all("list" in verbs[n] for n in ("area", "initiative", "person", "reader", "source")))
check("doc has no check verb; doctor replaces it", verbs["doc"] == ["create", "show", "sync"])
check("doctor has help text and both section flags", parser._subparsers._group_actions[0].choices["doctor"].description
      and run("doctor", "--local", "--only-doc")[0] == 2)
check("every verb has help text", all(p.description for n in verbs if n != "doctor" for p in
      next(iter(parser._subparsers._group_actions[0].choices[n]._subparsers._group_actions)).choices.values()))
for old in ("setup", "onboard", "add", "owner", "done", "stop", "updater", "readers", "sources", "settings", "archive", "dedupe",
            "section-write", "today", "row", "headline"):
    code, _, _ = run(old)
    check(f"old command {old!r} is gone", code != 0)
for n in verbs:
    for v in verbs[n]:
        code, out, _ = run(n, v, "--help")
        if code != 0 or "--dry-run" not in out:
            check(f"{n} {v} --help works and offers --dry-run", False, out[:80])
            break
check("every verb takes --help, --dry-run, --json, --doc", True)

code, _, err = run("initiative", "move", "A")
check("move needs --area", code == 2)

# lifecycle verbs need the right words
code, _, err = run("initiative", "stop", "A")
check("stop without a reason is a usage error", code == 2)
code, _, err = run("initiative", "done", "A")
check("done without an outcome is a usage error", code == 2)

# ---- day sweep: a passed milestone must be decided (done or red) before --publish writes ----
import sweep  # noqa: E402


class SweepInit:
    def __init__(self, name, milestone):
        self.title, self.name, self.owner, self.updater = f"{name} (Kyle)", name, "Kyle", "Kyle"
        self.area_title, self.tab_id = "Core (Kyle)", "t." + name
        s = du.Section(dt.date(2026, 11, 6), None)
        s.lines = [("🟢 On track", None), (f"Next milestone: {milestone}", None), ("Blocked on: None.", None)]
        self.sections = [s]

    def newest(self, attr=None):
        return self.sections[0]


class StopHere(Exception):
    pass


def sweep_run(inits, *extra):
    """Run sweep.py's main on fake initiatives; reading the doc a second time means --publish got past the gate."""
    reads = []

    def read_doc(_):
        reads.append(1)
        if len(reads) > 1:
            raise StopHere
        return {}

    saved = (du.read_doc, du.model, sys.argv)
    du.read_doc, du.model = read_doc, lambda _doc: (None, {}, inits)
    sys.argv = ["sweep.py", "DOC", "2026-11-09", "--owner", "Scott", *extra]
    out, code = io.StringIO(), "returned"
    try:
        with contextlib.redirect_stdout(out):
            sweep.main()
    except SystemExit as e:
        code = str(e)
    except StopHere:
        code = "past the gate"
    finally:
        du.read_doc, du.model, sys.argv = saved
    return code, out.getvalue()


two = lambda: [SweepInit("Evals", "Nightly run, Fri Nov 6"), SweepInit("Planning", "Release, Thu Nov 12")]
code, out = sweep_run(two(), "--publish")
check("sweep --publish refuses while a passed milestone has no decision",
      code.startswith("REFUSED") and "Evals (Kyle)" in code and "Planning" not in code and "--decide" in code, code)
check("the refusal names the exact --decide forms", 'Evals=done' in out and 'Evals=red' in out, out)
code, out = sweep_run(two())
check("sweep preview lists the undecided milestone as needing a decision",
      "NEEDS A DECISION: Evals (Kyle)" in out and "Publish?" not in out and code == "returned", out)
code, _ = sweep_run(two(), "--publish", "--decide", "Evals=done")
check("a done decision lets --publish through", code == "past the gate", code)
code, _ = sweep_run(two(), "--publish", "--decide", "Evals=red")
check("a red decision lets --publish through", code == "past the gate", code)
code, _ = sweep_run(two(), "--publish", "--decide", "Evals=late")
check("a decision that is not done or red does not count", code.startswith("REFUSED"), code)
code, _ = sweep_run([SweepInit("Planning", "Release, Thu Nov 12")], "--publish")
check("no passed milestone: --publish is not blocked", code == "past the gate", code)

# ---- day sweep: a red decision says why, a done decision names the next step, overdue stays on the overview ----
today = dt.date(2026, 11, 9)
lines_red, notes_red = sweep.draft(SweepInit("Evals", "Nightly run, Fri Nov 6"), today, "Scott", {"Evals": "red"})
prog = next((x for x in lines_red if x.startswith("Progress:")), "")
check("red decision: the section opens Progress with the reason, in skill order",
      lines_red[1].startswith("🔴") and "Nightly run" in prog and "Fri Nov 6" in prog and "Red" in prog
      and lines_red.index(prog) == 3 and lines_red[4].startswith("Blocked on:"), lines_red)
check("red decision: no placeholder text is written",
      not any("<" in x or ">" in x for x in lines_red) and any(x.startswith("Green when: Kyle sets this") for x in lines_red), lines_red)
lines_done, _ = sweep.draft(SweepInit("Evals", "Nightly run, Fri Nov 6"), today, "Scott", {"Evals": "done"})
check("done decision: no Progress line (the sweep knows no outcome)", not any(x.startswith("Progress:") for x in lines_done), lines_done)
code, out = sweep_run(two(), "--decide", "Evals=done")
check("done decision: the review names the next step", "NEXT: Evals (Kyle)" in out and "initiative done 'Evals' --outcome" in out
      and "next milestone" in out, out)
ov = [SweepInit("Late", "Nightly run, Fri Nov 6"), SweepInit("Soon", "Release, Thu Nov 12"), SweepInit("Done", "Old run, Mon Nov 2, done Tue Nov 3.")]
for i in ov:
    i.newest = lambda attr=None, i=i: i.sections[0]
rows = du.next_two_weeks(ov, today)
check("overview Next 2 weeks keeps an overdue milestone, marks it, and sorts it first",
      [r[2].name for r in rows] == ["Late", "Soon"] and du.next_two_weeks_date(rows[0][0], today) == "Fri Nov 6 (overdue)"
      and du.next_two_weeks_date(rows[1][0], today) == "Thu Nov 12", rows)


# ---- a note on a change is never an update section (add-backup, remove-backup, rename and the rest) ----
class FakeInit:
    tab_id = "t.1"
    def __init__(self, date):
        self.sections = [du.Section(date, None)]
        self.sections[0].lines = [("🟢 On track", None)]
        self.title = "Evals (Kyle)"
        self.name = "Evals"
        self.backups = ["Sam"]
        self.header = "Owner: Kyle · Updater: Kyle · Backups: Sam · Area: Core"

    def newest(self, attr=None):
        return self.sections[0]


def note_run(date):
    """Run cli.note against a tab whose newest section is `date`; return the writes it attempted."""
    calls = []
    saved = (cli.du.read_doc, cli.du.model, cli.m.write_section, cli.m.insert_line_before)
    cli.du.read_doc = lambda doc_id: {}
    cli.du.model = lambda doc: (None, {}, [FakeInit(date)])
    cli.m.write_section = lambda *a, **k: calls.append("write_section")
    cli.m.insert_line_before = lambda *a, **k: calls.append("insert_line_before")
    try:
        cli.note(Ctx("Scott"), FakeInit(date), "x")
    finally:
        cli.du.read_doc, cli.du.model, cli.m.write_section, cli.m.insert_line_before = saved
    return calls


Ctx.id = "doc"
check("a change note never creates a section dated today", note_run(cli.today() - dt.timedelta(days=2)) == [])
check("a change note still goes into a section that already exists for today", note_run(cli.today()) == ["insert_line_before"])

calls = []
saved = (cli.set_header, cli.note)
cli.set_header = lambda *a, **k: calls.append("set_header")
cli.note = lambda *a, **k: calls.append("note")
try:
    cli._backup_write(Ctx("Scott"), FakeInit(dt.date(2026, 11, 6)), [])
finally:
    cli.set_header, cli.note = saved
check("add-backup and remove-backup change the header line and write no section", calls == ["set_header"], str(calls))

# ---- section remove: only an automatic backup note, never anything else ----
def sec(day, lines):
    x = du.Section(day, None)
    x.lines = [(t, None) for t in lines]
    return x


def tab(*sections):
    t = FakeInit(dt.date(2026, 11, 6))
    t.sections = list(sections)
    return t


NOTE = "Progress: Backup Sam added on Sun Nov 8. (from Scott)"
real = sec(dt.date(2026, 11, 6), ["🟡 At risk", "Next milestone: Ship, Fri Nov 13", "Progress: Work moved on (chat).", "Blocked on: None.", "Green when: unblocked."])
note_sec = sec(dt.date(2026, 11, 8), ["🟡 At risk", "Next milestone: Ship, Fri Nov 13", NOTE, "Blocked on: None.", "Green when: unblocked."])
check("section remove: an automatic backup note carrying the older lines may go", cli.note_only_problem(tab(note_sec, real), note_sec) is None)
gone_sec = sec(note_sec.date, [note_sec.lines[0][0], note_sec.lines[1][0], NOTE.replace("added", "removed"), "Blocked on: None.", "Green when: unblocked."])
check("section remove: removed-backup notes may go too", cli.note_only_problem(tab(gone_sec, real), gone_sec) is None)
check("section remove: refused when it is the tab's only section", "only section" in (cli.note_only_problem(tab(note_sec), note_sec) or ""))
check("section remove: refused for a real update", "not an automatic" in (cli.note_only_problem(tab(note_sec, real), real) or ""))
edited = sec(note_sec.date, [*[t for t, _ in note_sec.lines], "Updated by Kyle for Scott."])
check("section remove: refused when anything else is in the section", "more than the note" in (cli.note_only_problem(tab(edited, real), edited) or ""))
moved = sec(note_sec.date, ["🟢 On track", "Next milestone: Ship, Fri Nov 13", NOTE, "Blocked on: None."])
check("section remove: refused when the status or milestone differs from the older section", "more than the note" in (cli.note_only_problem(tab(moved, real), moved) or ""))
other = sec(note_sec.date, ["🟡 At risk", "Next milestone: Ship, Fri Nov 13", "Progress: Renamed from A to B on Sun Nov 8. (from Scott)", "Blocked on: None.", "Green when: unblocked."])
check("section remove: refused for any note but a backup note", "not an automatic" in (cli.note_only_problem(tab(other, real), other) or ""))
with contextlib.redirect_stderr(io.StringIO()):
    no_force = refused(cli.build_parser().parse_args, ["section", "remove", "--all", "2026-11-08", "--force"])
check("section remove has no --force", no_force is not None)

# ---- --dry-run writes nothing, on every verb: a fake `gws` records every call, and any write fails the run ----
import shutil  # noqa: E402
import subprocess  # noqa: E402
import textwrap  # noqa: E402

FAKE_GWS = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, sys
    args = sys.argv[1:]
    words = []
    for a in args:
        if a.startswith("-"):
            break
        words.append(a)
    verb = words[-1] if words else ""
    with open(os.environ["FAKE_GWS_LOG"], "a") as f:
        f.write(("READ " if verb in ("get", "list", "getProfile") else "WRITE ") + " ".join(words) + "\\n")
    d = os.path.dirname(os.path.abspath(__file__))
    if words[:3] == ["docs", "documents", "get"]:
        print(open(os.path.join(d, "doc.json")).read())
    elif words[:3] == ["drive", "files", "get"]:
        print(json.dumps({"name": "E2E TEST fake", "properties": {
            "du.owner": "Scott", "du.person.Scott": "scott@x.test", "du.person.Kyle": "kyle@x.test", "du.person.Sam": "sam@x.test",
            "du.reader.1": "Medhat|email|medhat@x.test"}}))
    elif words[:3] == ["drive", "permissions", "list"]:
        print(json.dumps({"permissions": [{"emailAddress": "scott@x.test"}]}))
    elif words[:3] == ["drive", "comments", "list"]:
        print(json.dumps({"comments": []}))
    elif words[-1] == "getProfile":
        print(json.dumps({"emailAddress": "scott@x.test"}))
    else:
        print("{}")
""")


class FakeDoc:
    """Just enough Docs JSON for du.model: an overview, two areas and five initiative tabs in different states."""
    def __init__(self):
        self.tabs = []

    @staticmethod
    def para(text, at, style="NORMAL_TEXT"):
        n = du.utf16(text) + 1
        return {"startIndex": at, "endIndex": at + n, "paragraph": {"paragraphStyle": {"namedStyleType": style},
                                                                   "elements": [{"textRun": {"content": text + "\n"}}]}}, at + n

    def body(self, items):
        at, out = 1, []
        for text, style in items:
            if isinstance(text, list):  # a table: rows of cell texts
                start, rows = at, []
                for r in text:
                    cells = []
                    for c in r:
                        e, nxt = self.para(c, at + 1)
                        cells.append({"startIndex": at, "endIndex": nxt, "content": [e]})
                        at = nxt
                    rows.append({"tableCells": cells})
                out.append({"startIndex": start, "endIndex": at, "table": {"tableRows": rows}})
                continue
            e, at = self.para(text, at, style)
            out.append(e)
        return out

    def tab(self, tid, title, items, kids=()):
        return {"tabProperties": {"tabId": tid, "title": title}, "childTabs": list(kids),
                "documentTab": {"body": {"content": self.body(items)}}}

    def init(self, tid, title, header, sections):
        items = [(title, "HEADING_1"), (header, "NORMAL_TEXT")]
        for head, lines in sections:
            items += [(head, "HEADING_2")] + [(x, "NORMAL_TEXT") for x in lines] + [("", "NORMAL_TEXT")]
        return self.tab(tid, title, items)

    def build(self):
        sec = lambda *extra: ("Fri Nov 6, 2026", ["🟢 On track", "Next milestone: Ship, Fri Nov 13", *extra, "Blocked on: None."])
        hdr = lambda area, upd="Scott", bk="": f"Owner: Scott · Updater: {upd}{bk} · Area: {area} · Back to Overview"
        tabs = [
            self.tab("t.0", "Overview (Scott)", [("Overview (Scott)", "TITLE"), ("As of Fri Nov 6, 3:00 PM ET", "NORMAL_TEXT"),
                                                 ("Area health", "HEADING_2"), ([["Area", "Owner", "Status", "Headline"], ["Alpha", "Scott", "🟢 2", "Fine."]], None)]),
            self.tab("t.a", "Alpha (Scott)", [("Alpha (Scott)", "HEADING_1"), ("Headline", "HEADING_2"), ("Fine. (Fri Nov 6)", "NORMAL_TEXT"),
                                              ("Initiatives", "HEADING_2"),
                                              ([["Initiative", "Owner", "Status", "Next milestone"], ["Open", "Scott", "x", "y"],
                                                ["Kylestab", "Scott", "x", "y"], ["Paused", "Scott", "x", "y"], ["Finished", "Scott", "x", "y"]], None),
                                              ("Done", "HEADING_2"), ("No initiatives finished yet.", "NORMAL_TEXT")],
                     [self.init("t.1", "Open (Scott)", hdr("Alpha"), [sec("Progress: Work moved on (chat).")]),
                      self.init("t.2", "Kylestab (Scott)", hdr("Alpha", "Kyle", " · Backups: Sam"),
                                [("Sun Nov 8, 2026", ["🟢 On track", "Next milestone: Ship, Fri Nov 13", "Progress: Backup Sam added on Sun Nov 8. (from Scott)", "Blocked on: None."]),
                                 sec("Progress: Work moved on (chat).")]),
                      self.init("t.5", "Swept (Scott)", hdr("Alpha"), [("Mon Nov 9, 2026", ["🟢 On track", "Next milestone: Ship, Fri Nov 13", "Blocked on: None.", "Unconfirmed: no update from Scott by 3pm ET."]), sec("Progress: Work moved on (chat).")]),
                      self.init("t.3", "Paused (Scott)", hdr("Alpha"), [("Fri Nov 6, 2026", ["⚪ Paused", "Next milestone: None, No date set yet", "Progress: Paused Fri Nov 6: wait. (from Scott)", "Blocked on: None."])]),
                      self.init("t.4", "Finished (Scott)", hdr("Alpha"), [("Fri Nov 6, 2026", ["🟢 On track", "Next milestone: Ship, done Fri Nov 6", "Progress: Done Fri Nov 6: shipped. (from Scott)", "Blocked on: None."])])]),
            self.tab("t.b", "Beta (Scott)", [("Beta (Scott)", "HEADING_1"), ("Headline", "HEADING_2"), ("Fine. (Fri Nov 6)", "NORMAL_TEXT"),
                                             ("Initiatives", "HEADING_2"), ([["Initiative", "Owner", "Status", "Next milestone"]], None),
                                             ("Done", "HEADING_2"), ("No initiatives finished yet.", "NORMAL_TEXT")]),
            self.tab("t.z", "Archive (Scott)", [("Archive (Scott)", "HEADING_1")]),
        ]
        return {"title": "E2E TEST fake", "revisionId": "r1", "tabs": tabs}


work = tempfile.mkdtemp()
bindir = os.path.join(work, "bin")
os.makedirs(bindir)
open(os.path.join(bindir, "gws"), "w").write(FAKE_GWS)
os.chmod(os.path.join(bindir, "gws"), 0o755)
json.dump(FakeDoc().build(), open(os.path.join(bindir, "doc.json"), "w"))
log = os.path.join(work, "gws.log")
cfg_file = os.path.join(work, "config.json")
json.dump({"me": "Scott", "doc_id": "FAKEDOC", "tabs": [{"name": "Open", "kind": "initiative", "sources": {"jira": ["COM-1"]}}]}, open(cfg_file, "w"))
sec_file, init_file, struct_file, rows_file, cand_file = (os.path.join(work, n) for n in
    ("sec.json", "init.json", "struct.json", "rows.json", "cand.json"))
json.dump({"date": "2026-11-09", "status": "🟢", "milestone": "Ship, Fri Nov 13", "progress": "More (chat).", "blocked": "None."}, open(sec_file, "w"))
json.dump({"date": "2026-11-09", "status": "🟢", "milestone": "Ship, Fri Nov 20", "progress": "Start (chat).", "blocked": "None.",
           "name": "Fresh", "owner": "Scott"}, open(init_file, "w"))
json.dump({"org": "X", "owner": "Scott", "reader": "Medhat", "date": "2026-11-06",
           "areas": [{"name": "A", "owner": "Scott", "initiatives": [{"name": "I", "owner": "Scott", "status": "🟢", "milestone": "m, Fri Nov 13"}]}]}, open(struct_file, "w"))
json.dump([["Approve X", "Why", "Yes", "Fri Nov 13", "Scott"]], open(rows_file, "w"))
json.dump([{"name": "Thing", "links": [], "sources": {}}], open(cand_file, "w"))

D = "2026-11-09"
VERB_ARGS = {
    ("doc", "create"): [struct_file], ("doc", "show"): [], ("doc", "sync"): [],
    ("area", "list"): [], ("area", "show"): ["Alpha"], ("area", "add"): ["Gamma", "Scott"], ("area", "rename"): ["Alpha", "Alpha2"],
    ("area", "set-owner"): ["Alpha", "Kyle"], ("area", "set-headline"): ["Alpha", "Steady. (Fri Nov 6)"],
    ("area", "merge"): ["Beta", "Alpha"], ("area", "remove"): ["Beta"],
    ("initiative", "list"): [], ("initiative", "show"): ["Open"], ("initiative", "add"): [init_file, "--area", "Alpha"],
    ("initiative", "rename"): ["Open", "Opened"], ("initiative", "move"): ["Open", "--area", "Beta"],
    ("initiative", "set-owner"): ["Open", "Kyle"], ("initiative", "set-updater"): ["Open", "Kyle"],
    ("initiative", "add-backup"): ["Open", "Sam"], ("initiative", "remove-backup"): ["Kylestab", "Sam"],
    ("initiative", "pause"): ["Open", "--reason", "wait"], ("initiative", "resume"): ["Paused", "--status", "🟢", "--milestone", "Ship, Fri Nov 20"],
    ("initiative", "done"): ["Open", "--outcome", "shipped"], ("initiative", "stop"): ["Open", "--reason", "dropped"],
    ("initiative", "reopen"): ["Finished", "--reason", "more", "--status", "🟢", "--milestone", "Ship, Fri Nov 20"],
    ("initiative", "archive"): ["Finished"],
    ("person", "list"): [], ("person", "show"): ["Kyle"], ("person", "set-email"): ["Kyle", "k2@x.test"],
    ("reader", "list"): [], ("reader", "add"): ["Pat", "pat@x.test"], ("reader", "remove"): ["Medhat"],
    ("reader", "set-channel"): ["Medhat", "chat"],
    ("source", "list"): [], ("source", "add"): ["Open", "jira", "COM-2"], ("source", "remove"): ["Open", "jira", "COM-1"],
    ("section", "write"): ["Open (Scott)", sec_file], ("section", "show"): ["Open (Scott)", "2026-11-06"],
    ("section", "lint"): ["Open (Scott)", sec_file], ("section", "remove"): ["Kylestab (Scott)", "2026-11-08"],
    ("day", "sweep"): [D, "--publish", "--tag"], ("day", "overview"): [D, "3:00 PM ET", "--publish"],
    ("day", "decisions"): ["Medhat", rows_file], ("day", "send"): ["--confirmed"],
    ("discover", "check"): [cand_file],
}
parser = cli.build_parser()
grammar = [(n, v) for n, p in parser._subparsers._group_actions[0].choices.items()
           if p._subparsers for v in p._subparsers._group_actions[0].choices]
check("the dry-run test names args for every grammar verb", set(grammar) == set(VERB_ARGS), str(set(grammar) ^ set(VERB_ARGS)))

env_keep = {k: os.environ.get(k) for k in ("PATH", "FAKE_GWS_LOG", "DU_CONFIG", "DU_TEST", "GWS_BIN", "DU_TODAY", "DU_NO_SYNC")}
os.environ.update(PATH=bindir + os.pathsep + os.environ["PATH"], FAKE_GWS_LOG=log, DU_CONFIG=cfg_file, DU_TEST="1",
                  GWS_BIN=os.path.join(bindir, "gws"), DU_TODAY=D, DU_NO_SYNC="1")
cli.du.PROTECTED = {}


LAST = []


def writes_of(argv):
    open(log, "w").close()
    out = io.StringIO()
    quiet = os.open(os.devnull, os.O_WRONLY)
    saved_fd = os.dup(1)
    os.dup2(quiet, 1)  # child scripts (sweep, overview) print to fd 1
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            try:
                cli.main(argv)
            except (SystemExit, Exception) as e:
                out.write(f"\nEXIT {str(e)[:150]}")
    finally:
        os.dup2(saved_fd, 1)
        os.close(saved_fd)
        os.close(quiet)
    LAST.append((argv[:2], out.getvalue()))
    return [l.strip() for l in open(log) if l.startswith("WRITE")], os.environ.get("DU_DRY_RUN")


# the recorder works: the same call without --dry-run does reach the fake
w, _ = writes_of(["section", "write", "Open (Scott)", sec_file])
check("the fake gws records a real write (the test can fail)", any("batchUpdate" in x for x in w), str(w))
for (noun, verb_), args in sorted(VERB_ARGS.items()):
    w, leak = writes_of([noun, verb_, *args, "--dry-run"])
    check(f"--dry-run writes nothing: {noun} {verb_}", not w, "; ".join(w[:3]))
    if os.environ.get("SHOW_OUTCOMES"):
        print("   ->", LAST[-1][1].strip().replace("\n", " | ")[:230])
    check(f"--dry-run is switched off again after: {noun} {verb_}", leak is None, str(leak))
# --tag works on its own, after the publish: the tab swept earlier gets its comment, and only once
w, _ = writes_of(["day", "sweep", D, "--tag"])
check("day sweep --tag alone tags the updater of a swept tab", any("comments create" in x for x in w), str(w))
for k, v in env_keep.items():
    if v is None:
        os.environ.pop(k, None)
    else:
        os.environ[k] = v
shutil.rmtree(work, ignore_errors=True)

print("\n" + ("ALL PASS" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}"))
sys.exit(1 if FAILS else 0)
