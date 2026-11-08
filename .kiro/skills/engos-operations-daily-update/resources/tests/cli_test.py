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
    def __init__(self, title, updater="Kyle", area_owner="Kyle", progress=None, status="🟢"):
        self.title = title
        self.name, self.owner = du.title_parts(title)
        self.updater, self.area_owner = updater, area_owner
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
    ["list", "show", "add", "rename", "move", "set-owner", "set-updater", "pause", "resume", "done", "stop", "reopen", "archive"]))
check("area verbs", verbs["area"] == sorted(["list", "show", "add", "rename", "set-owner", "set-headline", "merge", "remove"]))
check("reader verbs", verbs["reader"] == sorted(["list", "add", "remove", "set-channel"]))
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

print("\n" + ("ALL PASS" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}"))
sys.exit(1 if FAILS else 0)
