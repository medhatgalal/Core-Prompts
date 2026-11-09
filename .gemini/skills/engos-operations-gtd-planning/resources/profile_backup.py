"""Back up the GTD planning profile to the person's own Google Drive, and restore it.

Local files stay primary, in ~/.engos/gtd-planning/ (or ~/.gtd-planning/ only when ~/.engos does not exist):

    profile.md            the profile
    sources/*             one settings file per enabled source

The Drive copy lives in the person's own My Drive and is never shared (it holds personal ids):

    My Drive/.engos/README.md                shared note: please don't delete, move or share
    My Drive/.engos/gtd-planning/            profile.md
    My Drive/.engos/gtd-planning/sources/    per-source settings

Not backed up, on purpose: the stored hash file and its accepted copies. They are this laptop's record of what
the person approved. A restore drops a `.restored` marker so profile_check treats the restored profile as a
change and asks before it is used.

sync() compares each file by content. Same: nothing to do. Different: the newer side wins (local newer or Drive
missing: upload; Drive newer or local missing: download). Uploads carry the local modified time and downloads set
it, so an unchanged file never bounces. If Drive cannot be reached, sync() reports a skip and never fails a run.

Writes only inside its own local subfolder. Never reads or alters other tools' files in ~/.engos.

Test overrides: GTD_HOME (local folder), GTD_BACKUP_ROOT (top Drive folder name), GWS_BIN (the gws binary).
"""
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

SUB = "gtd-planning"
FOLDER = "application/vnd.google-apps.folder"
MARKER = ".restored"
THROTTLE = 600  # seconds between automatic syncs

README = """# .engos: files for EngOS AI skills

Please don't delete, move or share this folder.

Your AI agent keeps backups here for the EngOS skills you use, such as GTD planning. It writes them as you work
and restores from them if your laptop's copy is lost.

- Each subfolder belongs to one skill.
- Deleting the folder means setting those skills up again from scratch.
- It's private to you because the files point at your own accounts and ids. Sharing it would expose them.

If this file goes missing, the next run puts it back.
"""


def home():
    """Local folder. GTD_HOME wins; else ~/.engos/gtd-planning; else ~/.gtd-planning only if ~/.engos is absent."""
    env = os.environ.get("GTD_HOME")
    if env:
        return env
    engos = os.path.expanduser("~/.engos")
    if os.path.isdir(engos):
        return os.path.join(engos, SUB)
    return os.path.expanduser("~/.gtd-planning")


def root_name():
    return os.environ.get("GTD_BACKUP_ROOT") or ".engos"


class Offline(Exception):
    pass


def _gws(*args, body=None, upload=None, out=None, ctype=None):
    # gws only reads or writes files inside its working folder, so run it from the file's own folder.
    cmd = [os.environ.get("GWS_BIN", "gws"), *args]
    cwd = None
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    if upload:
        cwd = os.path.dirname(os.path.abspath(upload))
        cmd += ["--upload", os.path.basename(upload)]
        if ctype:
            cmd += ["--upload-content-type", ctype]
    if out:
        cwd = os.path.dirname(os.path.abspath(out))
        cmd += ["-o", os.path.basename(out)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Offline(str(e))
    if p.returncode != 0:
        raise Offline((p.stderr or p.stdout or "gws failed").strip()[-400:])
    s = p.stdout.strip()
    try:
        return json.loads(s) if s and not out else {}
    except ValueError:
        return {}


def _q(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _list(parent, name=None, folder=None):
    q = [f"'{parent}' in parents", "trashed = false", "'me' in owners"]
    if name is not None:
        q.append(f"name = '{_q(name)}'")
    if folder is True:
        q.append(f"mimeType = '{FOLDER}'")
    elif folder is False:
        q.append(f"mimeType != '{FOLDER}'")
    r = _gws("drive", "files", "list", "--params", json.dumps(
        {"q": " and ".join(q), "fields": "files(id,name,mimeType,md5Checksum,modifiedTime)", "pageSize": 1000}))
    return r.get("files", [])


def _folder(parent, name):
    hit = _list(parent, name, folder=True)
    if hit:
        return hit[0]["id"]
    return _gws("drive", "files", "create", "--params", json.dumps({"fields": "id"}),
                body={"name": name, "mimeType": FOLDER, "parents": [parent]})["id"]


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _rfc(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _ts(rfc):
    return dt.datetime.strptime(rfc[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp()


def _upload(parent, name, path, existing=None):
    # Stored as plain text so Drive never reformats the file.
    meta = {"modifiedTime": _rfc(os.path.getmtime(path))}
    if existing:
        _gws("drive", "files", "update", "--params", json.dumps({"fileId": existing["id"], "fields": "id"}),
             body=meta, upload=path, ctype="text/plain")
    else:
        _gws("drive", "files", "create", "--params", json.dumps({"fields": "id"}),
             body={**meta, "name": name, "parents": [parent], "mimeType": "text/plain"}, upload=path, ctype="text/plain")


def _valid(path):
    """A usable text file: readable UTF-8 and not empty."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        data.decode("utf-8")
        return len(data.strip()) > 0
    except (UnicodeDecodeError, OSError):
        return False


def _download(remote, path):
    h = home()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".restore"
    _gws("drive", "files", "get", "--params", json.dumps({"fileId": remote["id"], "alt": "media"}), out=tmp)
    if not os.path.isfile(tmp):
        raise Offline(f"download of {remote['name']} saved nothing")
    if not _valid(tmp):
        os.remove(tmp)
        raise Offline(f"Drive copy of {remote['name']} is empty or not text; kept the local file")
    if os.path.isfile(path):
        # Never lose the laptop's copy: keep it before the restore replaces it.
        keep = os.path.join(h, ".before-restore", time.strftime("%Y%m%d-%H%M%S"), os.path.relpath(path, h))
        os.makedirs(os.path.dirname(keep), exist_ok=True)
        shutil.copy2(path, keep)
    os.replace(tmp, path)
    t = _ts(remote["modifiedTime"])
    os.utime(path, (t, t))


def _safe_name(name):
    return bool(name) and "/" not in name and "\\" not in name and not name.startswith(".") and name != ".."


def _local_files():
    h = home()
    files = {}
    p = os.path.join(h, "profile.md")
    if os.path.isfile(p) and not os.path.islink(p):
        files[("", "profile.md")] = p
    sdir = os.path.join(h, "sources")
    if os.path.isdir(sdir):
        for n in sorted(os.listdir(sdir)):
            fp = os.path.join(sdir, n)
            if _safe_name(n) and os.path.isfile(fp) and not os.path.islink(fp):
                files[("sources", n)] = fp
    return files


def _sync_dir(folder_id, sub, local, result):
    h = home()
    remote = {f["name"]: f for f in _list(folder_id, folder=False)}
    # Only the files this tool owns are synced: profile.md at the top, anything safe-named under sources/.
    if sub == "":
        remote = {n: f for n, f in remote.items() if n == "profile.md"}
    else:
        remote = {n: f for n, f in remote.items() if _safe_name(n)}
    names = {n for (s, n) in local if s == sub} | set(remote)
    for name in sorted(names):
        path = local.get((sub, name)) or os.path.join(h, sub, name)
        r = remote.get(name)
        label = f"{sub}/{name}" if sub else name
        if os.path.islink(path):
            # Symlinks are never read, uploaded or overwritten, whether or not Drive has a file of that name.
            result["invalid"].append(label)
            continue
        if os.path.isfile(path) and not _valid(path):
            # A broken or empty local file never overwrites the Drive copy; left for the person to look at.
            result["invalid"].append(label)
            continue
        if not os.path.isfile(path):
            _download(r, path)
            result["restored"].append(label)
        elif r is None:
            _upload(folder_id, name, path)
            result["backed_up"].append(label)
        elif r.get("md5Checksum") == _md5(path):
            result["same"] += 1
        elif os.path.getmtime(path) >= _ts(r["modifiedTime"]):
            _upload(folder_id, name, path, existing=r)
            result["backed_up"].append(label)
        else:
            _download(r, path)
            result["restored"].append(label)


def sync():
    """Back up and restore. Returns {"status": "ok"|"skipped", "backed_up", "restored", "same", "invalid", "error"}."""
    h = home()
    result = {"status": "ok", "backed_up": [], "restored": [], "same": 0, "invalid": [], "error": ""}
    try:
        root = _folder("root", root_name())
        if not _list(root, "README.md", folder=False):
            tmp = os.path.join(h, ".engos-README.md")
            os.makedirs(h, exist_ok=True)
            with open(tmp, "w") as f:
                f.write(README)
            try:
                _gws("drive", "files", "create", "--params", json.dumps({"fields": "id"}),
                     body={"name": "README.md", "parents": [root], "mimeType": "text/markdown"}, upload=tmp,
                     ctype="text/markdown")
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
            result["readme"] = "created"
        kit = _folder(root, SUB)
        sources = _folder(kit, "sources")
        local = _local_files()
        _sync_dir(kit, "", local, result)
        _sync_dir(sources, "sources", local, result)
    except Offline as e:
        result.update(status="skipped", error=str(e))
    if result["restored"]:
        # Tell profile_check: this profile came from Drive, so ask before using it.
        with open(os.path.join(h, MARKER), "w") as f:
            f.write("\n".join(result["restored"]) + "\n")
    return result


def auto(now=None):
    """Run sync() at most once every THROTTLE seconds. Returns the result, or None when it was not due."""
    if os.environ.get("GTD_NO_SYNC"):
        return None
    h = home()
    stamp = os.path.join(h, ".last-sync")
    now = now or time.time()
    try:
        if now - os.path.getmtime(stamp) < THROTTLE:
            return None
    except OSError:
        pass
    r = sync()
    if r["status"] == "ok":
        os.makedirs(h, exist_ok=True)
        open(stamp, "w").close()
        os.utime(stamp, (now, now))
    return r


def report(r):
    if r["status"] == "skipped":
        return f"BACKUP SKIPPED: Drive not reachable ({r['error'][:200]}). Local files are unchanged."
    parts = [f"backed up {len(r['backed_up'])}", f"restored {len(r['restored'])}", f"unchanged {r['same']}"]
    lines = [f"BACKUP OK ({', '.join(parts)}) in My Drive/{root_name()}/{SUB}"]
    lines += [f"  backed up: {x}" for x in r["backed_up"]] + [f"  restored: {x}" for x in r["restored"]]
    lines += [f"  NOT backed up (empty or not text, fix it locally): {x}" for x in r.get("invalid", [])]
    if r["restored"]:
        lines.append(f"  replaced local copies kept in {os.path.join(home(), '.before-restore')}")
        lines.append("  restored profile needs your confirmation (run profile_check.py)")
    if r.get("readme"):
        lines.append(f"  README.md created in My Drive/{root_name()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report(auto() or sync()) if "--now" not in sys.argv else report(sync()))
    sys.exit(0)  # a backup problem never fails the run
