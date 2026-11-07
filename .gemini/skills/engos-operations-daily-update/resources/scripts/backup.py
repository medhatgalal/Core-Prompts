"""Back up the kit's local files to the person's own Google Drive, and restore them.

Local files (~/.daily-update) stay primary. The Drive copy lives in the person's own My Drive:

    My Drive/.engos/README.md                         what the folder is; please don't delete it
    My Drive/.engos/automation-daily-updates/         config.json, protected.json
    My Drive/.engos/automation-daily-updates/ledger/  YYYY-MM-DD.json

The folders are created private and are never shared: the files point at the person's own email and chats.

sync() compares each file by content. Same content: nothing to do. Different: the newer side wins (local
newer or Drive missing: upload; Drive newer or local missing: download). Uploads carry the local modified time,
and downloads set it, so an unchanged file never bounces back and forth.
If Drive cannot be reached, sync() reports that the backup was skipped and never fails the run.

Test overrides: DU_HOME (local folder), DU_BACKUP_ROOT (top Drive folder name), GWS_BIN (the gws binary).
"""
import datetime as dt
import glob
import hashlib
import json
import os
import subprocess
import time

HOME = os.environ.get("DU_HOME") or os.path.expanduser("~/.daily-update")
ROOT = os.environ.get("DU_BACKUP_ROOT") or ".engos"
SUB = "automation-daily-updates"
FOLDER = "application/vnd.google-apps.folder"

README = """# .engos: files for EngOS AI skills

Please don't delete, move or share this folder.

Your AI agent keeps backups here for the EngOS skills you use, such as Automation Daily Updates
(`/engos-operations-daily-update`). It writes them as you work and restores from them if your laptop's copy
is lost.

- Each subfolder belongs to one skill.
- Deleting the folder means setting those skills up again from scratch.
- It's private to you because the files point at your own email and chats. Sharing it would expose them.

If this file goes missing, the next run puts it back.
"""


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
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _rfc(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _ts(rfc):
    return dt.datetime.strptime(rfc[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp()


def _upload(parent, name, path, existing=None):
    # Stored as plain text: gws prints a JSON download instead of saving it, which would reformat the file.
    meta = {"modifiedTime": _rfc(os.path.getmtime(path))}
    if existing:
        _gws("drive", "files", "update", "--params", json.dumps({"fileId": existing["id"], "fields": "id"}),
             body=meta, upload=path, ctype="text/plain")
    else:
        _gws("drive", "files", "create", "--params", json.dumps({"fields": "id"}),
             body={**meta, "name": name, "parents": [parent], "mimeType": "text/plain"}, upload=path, ctype="text/plain")


def _download(remote, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".restore"
    _gws("drive", "files", "get", "--params", json.dumps({"fileId": remote["id"], "alt": "media"}), out=tmp)
    if not os.path.isfile(tmp):
        raise Offline(f"download of {remote['name']} saved nothing")
    os.replace(tmp, path)
    t = _ts(remote["modifiedTime"])
    os.utime(path, (t, t))


def _local_files():
    files = {}
    for name in ("config.json", "protected.json"):
        p = os.path.join(HOME, name)
        if os.path.isfile(p):
            files[("", name)] = p
    for p in sorted(glob.glob(os.path.join(HOME, "ledger", "*.json"))):
        files[("ledger", os.path.basename(p))] = p
    return files


def _sync_dir(folder_id, sub, local, result):
    remote = {f["name"]: f for f in _list(folder_id, folder=False)}
    names = {n for (s, n) in local if s == sub} | set(remote)
    for name in sorted(names):
        path = local.get((sub, name)) or os.path.join(HOME, sub, name)
        r = remote.get(name)
        label = f"{sub}/{name}" if sub else name
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
    """Back up and restore. Returns {"status": "ok"|"skipped", "backed_up", "restored", "same", "error"}."""
    result = {"status": "ok", "backed_up": [], "restored": [], "same": 0, "error": ""}
    try:
        root = _folder("root", ROOT)
        readme = _list(root, "README.md", folder=False)
        if not readme:
            tmp = os.path.join(HOME, ".engos-README.md")
            os.makedirs(HOME, exist_ok=True)
            open(tmp, "w").write(README)
            _gws("drive", "files", "create", "--params", json.dumps({"fields": "id"}),
                 body={"name": "README.md", "parents": [root], "mimeType": "text/markdown"}, upload=tmp,
                 ctype="text/markdown")
            os.remove(tmp)
            result["readme"] = "created"
        kit = _folder(root, SUB)
        ledger = _folder(kit, "ledger")
        local = _local_files()
        _sync_dir(kit, "", local, result)
        _sync_dir(ledger, "ledger", local, result)
    except Offline as e:
        result.update(status="skipped", error=str(e))
    return result


THROTTLE = 600  # seconds between automatic syncs


def auto(now=None):
    """Run sync() at most once every THROTTLE seconds. Returns the result, or None when it was not due.
    Every du.py command calls this first, so a new laptop restores its files without the agent remembering."""
    if os.environ.get("DU_TEST") or os.environ.get("DU_NO_SYNC"):
        return None
    stamp = os.path.join(HOME, ".last-sync")
    now = now or time.time()
    try:
        if now - os.path.getmtime(stamp) < THROTTLE:
            return None
    except OSError:
        pass
    r = sync()
    if r["status"] == "ok":
        os.makedirs(HOME, exist_ok=True)
        open(stamp, "w").close()
        os.utime(stamp, (now, now))
    return r


def report(r):
    if r["status"] == "skipped":
        return f"BACKUP SKIPPED: Drive not reachable ({r['error'][:200]}). Local files are unchanged."
    parts = [f"backed up {len(r['backed_up'])}", f"restored {len(r['restored'])}", f"unchanged {r['same']}"]
    lines = [f"BACKUP OK ({', '.join(parts)}) in My Drive/{ROOT}/{SUB}"]
    lines += [f"  backed up: {x}" for x in r["backed_up"]] + [f"  restored: {x}" for x in r["restored"]]
    if r.get("readme"):
        lines.append(f"  README.md created in My Drive/{ROOT}")
    return "\n".join(lines)
