#!/usr/bin/env python3
"""Restore Chat sidebar sections from a snapshot. Dry run by default.
Usage: restore_sidebar.py SNAPSHOT.json [--apply]
Only moves spaces between sections. Never deletes sections or leaves spaces."""
import json, subprocess, sys

def gws(*a, params=None, body=None):
    c = ["gws", "chat", "users", "sections", *a]
    if params: c += ["--params", json.dumps(params)]
    if body: c += ["--json", json.dumps(body)]
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"FAILED {' '.join(c[:7])}: {r.stderr.strip()[:300]}")
    return json.loads(r.stdout or "{}")

def paged(args, params, key):
    got, tok = [], None
    while True:
        p = dict(params, pageSize=100)
        if tok: p["pageToken"] = tok
        r = gws(*args, params=p)
        got += r.get(key, [])
        tok = r.get("nextPageToken")
        if not tok: return got

def current():
    out = {}
    secs = paged(["list"], {"parent": "users/me"}, "sections")
    for s in secs:
        items = paged(["items", "list"], {"parent": s["name"]}, "sectionItems")
        out[s["name"]] = {"displayName": s.get("displayName") or s.get("type", ""),
                          "items": {i["name"]: i.get("space") or i.get("name") for i in items}}
    return out

if sys.argv[1] == "--snapshot":   # --snapshot OUT.json : save the live sidebar in snapshot format
    live = current()
    json.dump({k: {"displayName": v["displayName"], "type": "", "items": [{"name": n, "space": sp} for n, sp in v["items"].items()]} for k, v in live.items()}, open(sys.argv[2], "w"), indent=1)
    print("saved", sys.argv[2]); sys.exit(0)
snap = json.load(open(sys.argv[1]))
apply = "--apply" in sys.argv
cur = current()
where = {sp: sec for sec, v in cur.items() for sp in v["items"].values()}   # space -> current section
moves = []
for sec, v in snap.items():
    for it in v["items"]:
        sp = it["space"]
        if sp in where and where[sp] != sec and sec in cur:
            moves.append((sp, where[sp], sec, v["displayName"] or v["type"]))
missing_secs = [(v["displayName"] or v["type"]) for k, v in snap.items() if k not in cur]
print(f"{len(moves)} space(s) differ from the snapshot")
for sp, frm, to, nm in moves:
    print(f"  {sp}: {cur[frm]['displayName']} -> {nm}")
if missing_secs: print("Sections in snapshot but gone now (not recreated):", missing_secs)
if not apply:
    print("Dry run. Re-run with --apply to move them."); sys.exit(0)
for sp, frm, to, nm in moves:
    item = next(n for n, s in cur[frm]["items"].items() if s == sp)
    gws("items", "move", params={"name": item}, body={"targetSection": to})
    print("moved", sp, "->", nm)
after = current()
bad = [sp for sp, _, to, _ in moves if sp not in after[to]["items"].values()]
print("Verified." if not bad else f"NOT verified: {bad}")
