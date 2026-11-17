#!/usr/bin/env python3
"""AC47: hash every value and formula on Metrics, every data tab, and canvas_source. Usage: hashes.py snapshot|verify [--target real|scratch] [--file data/hashes.json]"""
import argparse, hashlib, json, os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
from sheetlib import sheets, get_meta

TABS = ["Metrics", "canvas_source", "Jira_Issues", "Jira_Transitions", "Daily_Status_Counts", "Code_Changes", "Code_Jira_Links", "Code_Reviews", "State_History", "Incident_Issues"]


def tab_hash(sid, title, rows_hint):
    h = hashlib.sha256()
    n = 0
    step = 4000
    r = 1
    while True:
        out = []
        for render in ("FORMULA", "UNFORMATTED_VALUE"):
            v = sheets("values", "get", params={"spreadsheetId": sid, "range": f"'{title}'!A{r}:ZZ{r + step - 1}", "valueRenderOption": render}).get("values", [])
            out.append(v)
        if not out[0]:
            break
        h.update(json.dumps(out, sort_keys=True, separators=(",", ":")).encode())
        n += len(out[0])
        if len(out[0]) < step:
            break
        r += step
    return h.hexdigest(), n


def snapshot(sid):
    m = get_meta(sid)
    have = {s["properties"]["title"] for s in m["sheets"]}
    res = {}
    for t in TABS:
        if t in have:
            hx, n = tab_hash(sid, t, None)
            res[t] = {"sha256": hx, "rows": n}
    return {"taken_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sheet_id": sid, "tabs": res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snapshot", "verify"])
    ap.add_argument("--config", default="data/config.json")
    ap.add_argument("--target", default="real")
    ap.add_argument("--file", default="")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    sid = {"real": cfg["sheet_id"], "scratch": cfg["scratch_sheet_id"]}.get(a.target, a.target)
    real = a.target == "real" or a.target == cfg.get("sheet_id")
    if not a.file:
        a.file = "data/hashes.json" if real else "data/hashes-scratch.json"
    if not real and os.path.abspath(a.file) == os.path.abspath("data/hashes.json") and a.cmd == "snapshot":
        sys.exit("refusing to overwrite the real Sheet's hash baseline (data/hashes.json) for a non-real target")
    if a.cmd == "snapshot":
        s = snapshot(sid)
        json.dump(s, open(a.file, "w"), indent=1)
        print("snapshot", {k: v["rows"] for k, v in s["tabs"].items()})
    else:
        base = json.load(open(a.file))
        now = snapshot(sid)
        bad = [t for t, v in base["tabs"].items() if now["tabs"].get(t, {}).get("sha256") != v["sha256"]]
        print("hash check:", "OK, no change" if not bad else f"CHANGED: {bad}")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
