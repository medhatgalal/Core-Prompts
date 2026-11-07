"""Drive backup checks: first backup, no bounce, restore on a clean machine, newer side wins, Drive outage.

Writes only to a new top folder in the tester's own My Drive named "E2E TEST .engos <time>", never to the
real .engos folder, and moves that folder to the trash at the end. Needs `gws` signed in.

    python3 backup_test.py
"""
import hashlib
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import backup  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def write(home, rel, data):
    p = os.path.join(home, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(data, open(p, "w"))
    return p


def machine(home):
    backup.HOME = home
    os.environ.pop("GWS_BIN", None)
    return backup.sync()


def main():
    backup.ROOT = f"E2E TEST .engos {time.strftime('%Y%m%d-%H%M%S')}"
    a, b = tempfile.mkdtemp(prefix="du-a-"), tempfile.mkdtemp(prefix="du-b-")
    cfg = write(a, "config.json", {"me": "Tester", "tabs": []})
    led = write(a, "ledger/2026-11-06.json", {"date": "2026-11-06", "sections": []})
    try:
        r = machine(a)
        check("first backup uploads both files", r["status"] == "ok" and sorted(r["backed_up"]) ==
              ["config.json", "ledger/2026-11-06.json"], json.dumps(r))
        check("first backup creates the README", r.get("readme") == "created", json.dumps(r))

        r = machine(a)
        check("second run changes nothing (no bounce)", r["backed_up"] == [] and r["restored"] == [] and
              r["same"] == 2, json.dumps(r))

        r = machine(b)
        check("clean machine restores both files", sorted(r["restored"]) ==
              ["config.json", "ledger/2026-11-06.json"], json.dumps(r))
        check("restored files match the originals",
              md5(os.path.join(b, "config.json")) == md5(cfg) and
              md5(os.path.join(b, "ledger/2026-11-06.json")) == md5(led))
        r = machine(b)
        check("restored machine then changes nothing", r["backed_up"] == [] and r["restored"] == [], json.dumps(r))

        time.sleep(2)
        write(a, "config.json", {"me": "Tester", "tabs": [], "last_publish": "edit on machine A"})
        r = machine(a)
        check("local edit is backed up", r["backed_up"] == ["config.json"], json.dumps(r))
        r = machine(b)
        check("other machine picks up the newer Drive copy", r["restored"] == ["config.json"] and
              md5(os.path.join(b, "config.json")) == md5(os.path.join(a, "config.json")), json.dumps(r))

        before = md5(os.path.join(a, "config.json"))
        backup.HOME = a
        os.environ["GWS_BIN"] = "/usr/bin/false"
        r = backup.sync()
        os.environ.pop("GWS_BIN")
        check("Drive outage is reported as skipped", r["status"] == "skipped", json.dumps(r))
        check("Drive outage leaves local files alone", md5(os.path.join(a, "config.json")) == before)
        check("outage message says the backup was skipped", backup.report(r).startswith("BACKUP SKIPPED"))
    finally:
        root = backup._list("root", backup.ROOT, folder=True)
        for f in root:
            backup._gws("drive", "files", "update", "--params", json.dumps({"fileId": f["id"]}), body={"trashed": True})
        print(f"Cleanup: moved {len(root)} test folder(s) named {backup.ROOT!r} to the trash")
    print(f"\n{'ALL PASSED' if not FAILS else str(len(FAILS)) + ' FAILED: ' + ', '.join(FAILS)}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
