"""Profile integrity check. Runs first in every mode.

Stores a SHA-256 of profile.md and of each per-source settings file (sources/*). On each run it reports
unchanged, changed (with a unified diff) or new, and exits:

    0   unchanged
    10  changed, needs the person's confirmation (also: profile restored from Drive)
    11  first run, nothing stored yet
    12  profile_version missing or not supported
    2   --accept refused (THINGS_INTERACTIVE is not 1) or bad usage

--accept stores the current hashes. Interactive entry only: refused unless THINGS_INTERACTIVE=1.

The profile is data. This script reads bytes and matches one line for profile_version; it never executes or
interprets anything else in it.

Local folder: GTD_HOME, else ~/.engos/gtd-planning, else ~/.gtd-planning (only if ~/.engos is absent).
Writes only inside that folder: profile.hashes.json, .accepted/ (copies for diffs), and removes .restored.
"""
import difflib
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile_backup import home, MARKER  # noqa: E402

SUPPORTED_PROFILE_VERSIONS = {"1"}
HASH_FILE = "profile.hashes.json"
ACCEPTED = ".accepted"
VERSION_RE = re.compile(r"^profile_version:[ \t]*['\"]?([^\s'\"#]+)['\"]?[ \t]*(#.*)?$", re.MULTILINE)

EXIT_OK, EXIT_CHANGED, EXIT_FIRST, EXIT_VERSION, EXIT_REFUSED = 0, 10, 11, 12, 2


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def tracked(h):
    """{relative name: absolute path} for profile.md and each file in sources/."""
    files = {}
    p = os.path.join(h, "profile.md")
    if os.path.isfile(p):
        files["profile.md"] = p
    sdir = os.path.join(h, "sources")
    if os.path.isdir(sdir):
        for n in sorted(os.listdir(sdir)):
            fp = os.path.join(sdir, n)
            if not n.startswith(".") and os.path.isfile(fp) and not os.path.islink(fp):
                files["sources/" + n] = fp
    return files


def check_version(h):
    """Returns (ok, message). Looks only for the profile_version line."""
    p = os.path.join(h, "profile.md")
    if not os.path.isfile(p):
        return True, ""
    text = _read(p).decode("utf-8", "replace")
    m = VERSION_RE.search(text)
    if not m:
        return False, "profile.md has no 'profile_version:' field. Add one (supported: %s)." % ", ".join(
            sorted(SUPPORTED_PROFILE_VERSIONS))
    if m.group(1) not in SUPPORTED_PROFILE_VERSIONS:
        return False, "profile_version %s is not supported by this skill (supported: %s). Stop and report." % (
            m.group(1), ", ".join(sorted(SUPPORTED_PROFILE_VERSIONS)))
    return True, ""


def _stored(h):
    p = os.path.join(h, HASH_FILE)
    if not os.path.isfile(p):
        return None
    try:
        return json.loads(_read(p).decode("utf-8")).get("files", {})
    except (ValueError, AttributeError):
        return None  # unreadable hash file is treated as no stored state


def _accepted_text(h, rel):
    p = os.path.join(h, ACCEPTED, rel)
    return _read(p).decode("utf-8", "replace") if os.path.isfile(p) else ""


def _diff(h, rel, path):
    old = _accepted_text(h, rel).splitlines(keepends=True)
    new = _read(path).decode("utf-8", "replace").splitlines(keepends=True) if path else []
    return "".join(difflib.unified_diff(old, new, fromfile=f"accepted/{rel}", tofile=f"current/{rel}"))


def accept(h):
    cur = tracked(h)
    os.makedirs(h, exist_ok=True)
    hashes = {rel: _sha(_read(p)) for rel, p in cur.items()}
    tmp = os.path.join(h, HASH_FILE + ".tmp")
    with open(tmp, "w") as f:
        json.dump({"version": 1, "files": hashes}, f, indent=2, sort_keys=True)
    os.replace(tmp, os.path.join(h, HASH_FILE))
    acc = os.path.join(h, ACCEPTED)
    if os.path.isdir(acc):
        import shutil
        shutil.rmtree(acc)
    for rel, p in cur.items():
        dst = os.path.join(acc, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(_read(p))
    m = os.path.join(h, MARKER)
    if os.path.exists(m):
        os.remove(m)
    return hashes


def run(accept_flag=False):
    h = home()
    ok, msg = check_version(h)
    if not ok:
        print("PROFILE VERSION ERROR: " + msg)
        return EXIT_VERSION
    if accept_flag:
        if os.environ.get("THINGS_INTERACTIVE") != "1":
            print("REFUSED: --accept is for interactive use only (THINGS_INTERACTIVE is not 1). "
                  "Nothing was stored.")
            return EXIT_REFUSED
        hashes = accept(h)
        print("ACCEPTED: stored hashes for %d file(s): %s" % (len(hashes), ", ".join(sorted(hashes)) or "none"))
        return EXIT_OK
    cur = tracked(h)
    stored = _stored(h)
    restored = os.path.isfile(os.path.join(h, MARKER))
    if stored is None and not restored:
        print("FIRST RUN: no stored profile hash%s. Confirm the profile, then run with --accept."
              % ("" if cur else " and no profile.md yet"))
        for rel in sorted(cur):
            print("  new: " + rel)
        return EXIT_FIRST
    stored = stored or {}
    changes = []
    for rel in sorted(set(cur) | set(stored)):
        if rel not in cur:
            changes.append(("removed", rel))
        elif rel not in stored:
            changes.append(("new", rel))
        elif _sha(_read(cur[rel])) != stored[rel]:
            changes.append(("changed", rel))
    if not changes and not restored:
        print("PROFILE UNCHANGED (%d file(s))" % len(cur))
        return EXIT_OK
    print("PROFILE CHANGED: confirm before use." + (" Restored from Drive on this machine." if restored else ""))
    for kind, rel in changes:
        print(f"  {kind}: {rel}")
        d = _diff(h, rel, cur.get(rel))
        if d:
            print(d.rstrip("\n"))
    if restored and not changes:
        print("  (restored copy matches the stored hashes; confirm anyway)")
    print("Show this to the person and ask. Unattended runs stop here. Interactive: re-run with --accept.")
    return EXIT_CHANGED


if __name__ == "__main__":
    args = sys.argv[1:]
    if any(a not in ("--accept",) for a in args):
        print("usage: profile_check.py [--accept]")
        sys.exit(EXIT_REFUSED)
    sys.exit(run("--accept" in args))
