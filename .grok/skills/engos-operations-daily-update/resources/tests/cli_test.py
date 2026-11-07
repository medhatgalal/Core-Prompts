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
    sub = next(x for x in p._subparsers._group_actions)
    verbs[noun] = sorted(sub.choices)
check("nouns", sorted(verbs) == ["area", "day", "discover", "doc", "initiative", "person", "reader", "section", "source"], str(sorted(verbs)))
check("initiative verbs", verbs["initiative"] == sorted(
    ["list", "show", "add", "rename", "move", "set-owner", "set-updater", "pause", "resume", "done", "stop", "reopen", "archive"]))
check("area verbs", verbs["area"] == sorted(["list", "show", "add", "rename", "set-owner", "set-headline", "merge", "remove"]))
check("reader verbs", verbs["reader"] == sorted(["list", "add", "remove", "set-channel"]))
check("every noun with a collection has list and show or add/remove",
      all("list" in verbs[n] for n in ("area", "initiative", "person", "reader", "source")))
check("every verb has help text", all(p.description for n in verbs for p in
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
