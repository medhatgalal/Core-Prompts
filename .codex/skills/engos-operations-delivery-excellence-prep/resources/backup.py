"""Back up settings.json to the person's own Google Drive, and restore it.

Local file stays primary. The Drive copy lives in the person's own My Drive and is never shared:

    My Drive/.engos/README.md                      what the folder is; please don't delete it
    My Drive/.engos/delivery-excellence/settings.json

  python3 backup.py sync      newer side wins; same content does nothing
  python3 backup.py restore   put the Drive copy back on a new machine (refuses to overwrite a local file)

If Drive cannot be reached, sync says the backup was skipped and exits 0.
Test overrides: DELIVERY_EXCELLENCE_HOME (local folder), DE_BACKUP_ROOT (top Drive folder name), GWS_BIN.
"""
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

import settings

ROOT = os.environ.get("DE_BACKUP_ROOT") or ".engos"
SUB = "delivery-excellence"
NAME = "settings.json"
FOLDER = "application/vnd.google-apps.folder"
README = """# .engos: files for EngOS AI skills

Please don't delete, move or share this folder.

Your AI agent keeps backups here for the EngOS skills you use, such as Delivery Excellence Prep.
It writes them as you work and restores from them if your laptop's copy is lost.

- Each subfolder belongs to one skill.
- Deleting the folder means setting those skills up again from scratch.
- It's private to you because the files name your own colleagues and documents. Sharing it would expose them.

If this file goes missing, the next run puts it back.
"""


class Offline(Exception):
    pass


def _gws(*args, body=None, upload=None, out=None, ctype=None):
    # gws only reads or writes files inside its working folder, so run it from the file's own folder.
    cmd, cwd = [os.environ.get("GWS_BIN", "gws"), *args], None
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    if upload:
        cwd = os.path.dirname(os.path.abspath(upload))
        cmd += ["--upload", os.path.basename(upload), "--upload-content-type", ctype or "text/plain"]
    if out:
        cwd = os.path.dirname(os.path.abspath(out))
        cmd += ["-o", os.path.basename(out)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Offline(str(e))
    if p.returncode != 0:
        raise Offline((p.stderr or p.stdout or "gws failed").strip()[-400:])
    try:
        return json.loads(p.stdout.strip()) if p.stdout.strip() and not out else {}
    except ValueError:
        return {}


def _list(parent, name, folder):
    q = f"'{parent}' in parents and trashed = false and 'me' in owners and name = '{name}'"
    q += f" and mimeType {'=' if folder else '!='} '{FOLDER}'"
    r = _gws("drive", "files", "list", "--params", json.dumps(
        {"q": q, "fields": "files(id,name,md5Checksum,modifiedTime)", "pageSize": 10}))
    return r.get("files", [])


def _folder(parent, name):
    hit = _list(parent, name, True)
    if hit:
        return hit[0]["id"]
    return _gws("drive", "files", "create", "--params", json.dumps({"fields": "id"}),
                body={"name": name, "mimeType": FOLDER, "parents": [parent]})["id"]


def _rfc(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _ts(rfc):
    return dt.datetime.strptime(rfc[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp()


def _md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _upload(parent, name, path, existing=None):
    meta = {"modifiedTime": _rfc(os.path.getmtime(path))}
    if existing:
        _gws("drive", "files", "update", "--params", json.dumps({"fileId": existing["id"], "fields": "id"}), body=meta, upload=path)
    else:
        _gws("drive", "files", "create", "--params", json.dumps({"fields": "id"}),
             body={**meta, "name": name, "parents": [parent], "mimeType": "text/plain"}, upload=path)


def _folders():
    root = _folder("root", ROOT)
    return root, _folder(root, SUB)


def sync():
    local = settings.PATH
    try:
        root, sub = _folders()
        if not _list(root, "README.md", False):
            tmp = os.path.join(settings.HOME, ".README.md")
            open(tmp, "w").write(README)
            _upload(root, "README.md", tmp)
            os.remove(tmp)
        hit = _list(sub, NAME, False)
        remote = hit[0] if hit else None
        if os.path.isfile(local) and (not remote or _md5(local) != remote.get("md5Checksum")):
            if not remote or os.path.getmtime(local) >= _ts(remote["modifiedTime"]):
                _upload(sub, NAME, local, remote)
                return "uploaded settings.json to Drive"
        if remote and not os.path.isfile(local):
            return restore()
        if remote and os.path.isfile(local) and _md5(local) != remote.get("md5Checksum"):
            return "Drive copy is newer; run: python3 backup.py restore --force"
        return "settings.json already matches the Drive copy" if remote else "nothing to back up yet"
    except Offline as e:
        return f"Drive backup skipped: {e}"


def restore(force=False):
    if os.path.isfile(settings.PATH) and not force:
        return "settings.json already exists locally; use --force to overwrite it from Drive"
    try:
        _, sub = _folders()
        hit = _list(sub, NAME, False)
        if not hit:
            return "no settings.json in Drive yet; run the onboarding"
        os.makedirs(settings.HOME, exist_ok=True)
        tmp = settings.PATH + ".restore"
        _gws("drive", "files", "get", "--params", json.dumps({"fileId": hit[0]["id"], "alt": "media"}), out=tmp)
        json.load(open(tmp))  # refuse to install a file that is not JSON
        os.replace(tmp, settings.PATH)
        os.utime(settings.PATH, (_ts(hit[0]["modifiedTime"]),) * 2)
        return "restored settings.json from Drive"
    except (Offline, ValueError, OSError) as e:
        return f"restore failed, nothing changed: {e}"


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    print(sync() if cmd == "sync" else restore("--force" in sys.argv) if cmd == "restore" else "usage: backup.py sync|restore [--force]")
