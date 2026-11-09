"""Offline tests for profile_check.py and profile_backup.py. No network, no real Drive: gws is a local stub.

    python3 tests/gtd/test_gtd_profile_tools.py
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sources", "capability-resources",
                    "engos-operations-gtd-planning")
HERE = os.path.normpath(HERE)
sys.path.insert(0, HERE)
import profile_backup as pb  # noqa: E402

CHECK = os.path.join(HERE, "profile_check.py")
FAILS = []

STUB = r'''#!/usr/bin/env python3
"""Fake gws. State in $STUB_STATE/files.json. Supports drive files list/create/update/get."""
import base64, hashlib, json, os, re, sys, time, datetime as dt
state = os.path.join(os.environ["STUB_STATE"], "files.json")
db = json.load(open(state)) if os.path.exists(state) else {"n": 0, "files": {}}
a = sys.argv[1:]
def opt(flag):
    return a[a.index(flag) + 1] if flag in a else None
params = json.loads(opt("--params") or "{}")
body = json.loads(opt("--json") or "{}")
up, out = opt("--upload"), opt("-o")
def save(): json.dump(db, open(state, "w"))
def now(): return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
def view(f):
    d = {k: f[k] for k in ("id", "name", "mimeType", "modifiedTime")}
    if f.get("content") is not None:
        d["md5Checksum"] = hashlib.md5(base64.b64decode(f["content"])).hexdigest()
    return d
if a[:3] == ["drive", "files", "list"]:
    q = params["q"]
    parent = re.search(r"'([^']+)' in parents", q).group(1)
    nm = re.search(r"name = '((?:[^'\\]|\\.)*)'", q)
    res = []
    for f in db["files"].values():
        if parent not in f["parents"]: continue
        if nm and f["name"] != nm.group(1).replace("\\'", "'").replace("\\\\", "\\"): continue
        isf = f["mimeType"] == "application/vnd.google-apps.folder"
        if "mimeType = '" in q and not isf: continue
        if "mimeType != '" in q and isf: continue
        res.append(view(f))
    print(json.dumps({"files": res}))
elif a[:3] == ["drive", "files", "create"]:
    db["n"] += 1
    fid = "id%d" % db["n"]
    f = {"id": fid, "name": body["name"], "parents": body["parents"], "mimeType": body.get("mimeType", "text/plain"),
         "modifiedTime": body.get("modifiedTime", now()), "content": None}
    if up: f["content"] = base64.b64encode(open(up, "rb").read()).decode()
    db["files"][fid] = f; save(); print(json.dumps({"id": fid}))
elif a[:3] == ["drive", "files", "update"]:
    f = db["files"][params["fileId"]]
    if "modifiedTime" in body: f["modifiedTime"] = body["modifiedTime"]
    if up: f["content"] = base64.b64encode(open(up, "rb").read()).decode()
    save(); print(json.dumps({"id": f["id"]}))
elif a[:3] == ["drive", "files", "get"]:
    f = db["files"][params["fileId"]]
    open(out, "wb").write(base64.b64decode(f["content"]))
else:
    sys.exit(2)
'''
OFFLINE = "#!/bin/sh\necho 'network unreachable' >&2\nexit 1\n"


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    return path


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def tree(root, skip=None):
    out = {}
    for d, dirs, files in os.walk(root):
        if skip and os.path.abspath(d) == os.path.abspath(skip):
            dirs[:] = []
            continue
        for n in files:
            p = os.path.join(d, n)
            out[os.path.relpath(p, root)] = sha(p)
    return out


def run_check(home, *args, interactive=False, extra=None):
    env = dict(os.environ, GTD_HOME=home)
    env.pop("THINGS_INTERACTIVE", None)
    if interactive:
        env["THINGS_INTERACTIVE"] = "1"
    env.update(extra or {})
    p = subprocess.run([sys.executable, CHECK, *args], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def use(home, gws, state=None, root="test-engos"):
    os.environ["GTD_HOME"] = home
    os.environ["GWS_BIN"] = gws
    os.environ["GTD_BACKUP_ROOT"] = root
    if state:
        os.environ["STUB_STATE"] = state


PROFILE = "profile_version: 1\ntimezone: UTC\nareas: [Work, Home]\n"


def main():
    tmp = tempfile.mkdtemp(prefix="gtd-test-")
    stub = write(os.path.join(tmp, "gws_stub.py"), STUB)
    off = write(os.path.join(tmp, "gws_off.sh"), OFFLINE)
    os.chmod(stub, 0o755)
    os.chmod(off, 0o755)
    state = os.path.join(tmp, "drive")
    os.makedirs(state)

    # --- profile_check ---
    h = os.path.join(tmp, "a")
    prof = write(os.path.join(h, "profile.md"), PROFILE)
    src = write(os.path.join(h, "sources", "jira.md"), "jql: assignee = currentUser()\n")
    code, out = run_check(h)
    check("first run exits 11", code == 11, f"{code} {out}")
    code, out = run_check(h, "--accept")
    check("accept refused without THINGS_INTERACTIVE (exit 2)", code == 2, f"{code} {out}")
    check("refused accept stores nothing", not os.path.exists(os.path.join(h, "profile.hashes.json")))
    code, out = run_check(h, "--accept", interactive=True)
    check("accept with THINGS_INTERACTIVE=1 stores hashes", code == 0 and
          set(json.load(open(os.path.join(h, "profile.hashes.json")))["files"]) == {"profile.md", "sources/jira.md"},
          f"{code} {out}")
    code, out = run_check(h)
    check("unchanged exits 0", code == 0, f"{code} {out}")
    write(prof, PROFILE + "timezone: Europe/Paris\n")
    code, out = run_check(h)
    check("changed exits 10 and prints a unified diff", code == 10 and "+timezone: Europe/Paris" in out and
          "--- accepted/profile.md" in out, f"{code} {out}")
    code, out = run_check(h, extra={"THINGS_INTERACTIVE": ""})
    check("unattended run on a change still exits 10", code == 10)
    write(src, "jql: assignee = currentUser() and updated > -7d\n")
    code, out = run_check(h)
    check("a changed source file is reported", code == 10 and "changed: sources/jira.md" in out, out)
    write(os.path.join(h, "sources", "gitlab.md"), "projects: []\n")
    code, out = run_check(h)
    check("a new source file is reported as new", "new: sources/gitlab.md" in out and code == 10, out)
    code, out = run_check(h, "--accept", interactive=True)
    code, out = run_check(h)
    check("accept after review returns to unchanged", code == 0, f"{code} {out}")

    # version
    write(prof, "profile_version: 99\n")
    code, out = run_check(h)
    check("version mismatch exits 12 with clear message", code == 12 and "not supported" in out, f"{code} {out}")
    code, out = run_check(h, "--accept", interactive=True)
    check("accept also refuses a bad version", code == 12)
    write(prof, "timezone: UTC\n")
    code, out = run_check(h)
    check("missing profile_version exits 12", code == 12 and "no 'profile_version:'" in out, f"{code} {out}")
    # data only: embedded commands are not run
    canary = os.path.join(tmp, "canary")
    write(prof, f"profile_version: 1\nnote: $(touch {canary}); `touch {canary}`\n")
    run_check(h)
    check("profile contents are never executed", not os.path.exists(canary))

    # --- backup ---
    write(prof, PROFILE)
    use(h, stub, state)
    r = pb.sync()
    check("first backup uploads profile and source files", r["status"] == "ok" and
          sorted(r["backed_up"]) == ["profile.md", "sources/gitlab.md", "sources/jira.md"], json.dumps(r))
    check("first backup creates the README", r.get("readme") == "created", json.dumps(r))
    db = json.load(open(os.path.join(state, "files.json")))["files"]
    names = {f["name"] for f in db.values()}
    check("hash file and accepted copies are not uploaded", "profile.hashes.json" not in names and
          not any(n.startswith(".") for n in names), str(names))
    check("no file or folder is shared", all("permissions" not in f for f in db.values()))
    mt = [f for f in db.values() if f["name"] == "profile.md"][0]["modifiedTime"]
    check("upload carries local mtime", mt == pb._rfc(os.path.getmtime(prof)), mt)
    r = pb.sync()
    check("second run changes nothing (no bounce)", r["backed_up"] == [] and r["restored"] == [] and r["same"] == 3,
          json.dumps(r))

    # restore onto a fresh home
    b = os.path.join(tmp, "b")
    use(b, stub, state)
    r = pb.sync()
    check("fresh home restores everything", sorted(r["restored"]) == ["profile.md", "sources/gitlab.md",
          "sources/jira.md"], json.dumps(r))
    check("restored files match the originals", sha(os.path.join(b, "profile.md")) == sha(prof) and
          sha(os.path.join(b, "sources", "jira.md")) == sha(src))
    check("restored home then changes nothing", pb.sync()["restored"] == [])
    code, out = run_check(b)
    check("restored profile counts as changed: exit 10 unattended", code == 10 and "Restored from Drive" in out,
          f"{code} {out}")
    code, out = run_check(b, "--accept", interactive=True)
    code, out = run_check(b)
    check("accepting the restore returns to unchanged", code == 0, f"{code} {out}")

    # newer side wins
    time.sleep(1.1)
    write(prof, PROFILE + "extra: edited on A\n")
    use(h, stub, state)
    r = pb.sync()
    check("local edit is backed up", r["backed_up"] == ["profile.md"], json.dumps(r))
    use(b, stub, state)
    r = pb.sync()
    check("other machine picks up the newer Drive copy and keeps the old one", r["restored"] == ["profile.md"] and
          os.path.isdir(os.path.join(b, ".before-restore")), json.dumps(r))
    code, out = run_check(b)
    check("a restore over an accepted profile exits 10", code == 10 and "+extra: edited on A" in out, f"{code} {out}")

    # broken local file never overwrites Drive
    time.sleep(1.1)
    write(os.path.join(b, "profile.md"), "")
    r = pb.sync()
    check("an empty local file is not uploaded", r["invalid"] == ["profile.md"] and r["backed_up"] == [], json.dumps(r))

    # symlinks are never read, uploaded or overwritten
    c = os.path.join(tmp, "c")
    secret = write(os.path.join(tmp, "secret.txt"), "private\n")
    write(os.path.join(c, "profile.md"), PROFILE)
    os.makedirs(os.path.join(c, "sources"))
    os.symlink(secret, os.path.join(c, "sources", "jira.md"))
    os.symlink(secret, os.path.join(c, "sources", "linkonly.md"))
    use(c, stub, state)
    db0 = json.load(open(os.path.join(state, "files.json")))["files"]
    jira0 = [f for f in db0.values() if f["name"] == "jira.md"][0]
    r = pb.sync()
    db1 = json.load(open(os.path.join(state, "files.json")))["files"]
    jira1 = [f for f in db1.values() if f["name"] == "jira.md"][0]
    check("symlinked source is skipped, even when Drive has the same name",
          "sources/jira.md" not in r["backed_up"] + r["restored"] and "sources/linkonly.md" not in r["backed_up"],
          json.dumps(r))
    check("symlink target never uploaded", jira1.get("md5Checksum") == jira0.get("md5Checksum") and
          jira1["modifiedTime"] == jira0["modifiedTime"] and "linkonly.md" not in {f["name"] for f in db1.values()})
    check("symlink and its target are left untouched", os.path.islink(os.path.join(c, "sources", "jira.md")) and
          open(secret).read() == "private\n")

    # offline
    use(h, off)
    before = tree(h)
    r = pb.sync()
    check("offline sync is skipped, not failed", r["status"] == "skipped" and
          pb.report(r).startswith("BACKUP SKIPPED"), json.dumps(r))
    check("offline leaves local files alone", tree(h) == before)
    p = subprocess.run([sys.executable, os.path.join(HERE, "profile_backup.py"), "--now"], capture_output=True,
                       text=True, env=dict(os.environ, GTD_HOME=h, GWS_BIN=off))
    check("offline CLI exits 0", p.returncode == 0 and "BACKUP SKIPPED" in p.stdout, p.stdout + p.stderr)

    # nothing outside the gtd-planning subfolder; default location resolution
    fake = os.path.join(tmp, "fakehome")
    other = os.path.join(fake, ".engos", "other-tool")
    write(os.path.join(other, "config.json"), '{"x": 1}')
    write(os.path.join(fake, ".engos", "notes.txt"), "not ours")
    os.makedirs(os.path.join(fake, "unrelated"))
    write(os.path.join(fake, "unrelated", "f"), "z")
    snap = tree(fake)
    env = dict(os.environ, HOME=fake, GWS_BIN=stub, STUB_STATE=state, GTD_BACKUP_ROOT="test-engos")
    env.pop("GTD_HOME", None)
    env.pop("THINGS_INTERACTIVE", None)
    py = ("import sys; sys.path.insert(0, %r); import profile_backup as pb; r = pb.sync(); "
          "print(r['status'], sorted(r['restored']))" % HERE)
    p = subprocess.run([sys.executable, "-c", py], capture_output=True, text=True, env=env)
    gtd = os.path.join(fake, ".engos", "gtd-planning")
    check("default home is ~/.engos/gtd-planning and restores there", p.returncode == 0 and
          os.path.isfile(os.path.join(gtd, "profile.md")), p.stdout + p.stderr)
    subprocess.run([sys.executable, CHECK], capture_output=True, text=True, env=env)
    subprocess.run([sys.executable, CHECK, "--accept"], capture_output=True, text=True,
                   env=dict(env, THINGS_INTERACTIVE="1"))
    after_outside = tree(fake, skip=gtd)
    check("nothing written outside the gtd-planning subfolder", after_outside == {k: v for k, v in snap.items()},
          str(set(after_outside) ^ set(snap)))
    check("other tools' files untouched", sha(os.path.join(other, "config.json")) ==
          snap[os.path.join(".engos", "other-tool", "config.json")])

    fake2 = os.path.join(tmp, "fakehome2")
    os.makedirs(fake2)
    env2 = dict(env, HOME=fake2)
    subprocess.run([sys.executable, "-c", py], capture_output=True, text=True, env=env2)
    check("falls back to ~/.gtd-planning only when ~/.engos is absent", os.path.isfile(
        os.path.join(fake2, ".gtd-planning", "profile.md")) and not os.path.exists(os.path.join(fake2, ".engos")))

    print(f"\n{'ALL PASSED' if not FAILS else str(len(FAILS)) + ' FAILED: ' + ', '.join(FAILS)}")
    sys.exit(1 if FAILS else 0)


def test_profile_tools():
    try:
        main()
    except SystemExit as exit_:
        assert exit_.code == 0, FAILS


if __name__ == "__main__":
    main()
