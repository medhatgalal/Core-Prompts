#!/usr/bin/env python3
"""AC41a tab ORDER only (inbox 117): Alerts, Teams, Work items, Code changes and Individual sit together in that order, right after Dashboard and Explore; every other tab keeps its relative place.
Changes sheet indexes only (updateSheetProperties index); no name, colour, content or protection is touched. Idempotent. --dry-run prints the plan.
Usage: tab_order.py --target <id> [--config data/config.json] [--dry-run]"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from sheetlib import sheets, batch
ap = argparse.ArgumentParser(); ap.add_argument("--target", required=True); ap.add_argument("--config", default="data/config.json"); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
cfg = json.load(open(a.config))
m = sheets("get", params={"spreadsheetId": a.target, "fields": "sheets(properties(sheetId,title,index))"})
cur = sorted((s["properties"] for s in m["sheets"]), key=lambda p: p["index"])
names = [p["title"] for p in cur]                      # the shim returns canonical names (Alert details)
want = [t for t in cfg["tab_order"] if t in names]      # the configured visible order first
rest = [t for t in names if t not in want]              # machinery and other tabs keep their relative order after it
order = want + rest
ids = {p["title"]: p["sheetId"] for p in cur}
moves = [(t, i) for i, t in enumerate(order) if names[i] != t]
print("current :", names); print("target  :", order); print(f"{len(moves)} tabs change index")
if moves and not a.dry_run:
    batch(a.target, [{"updateSheetProperties": {"properties": {"sheetId": ids[t], "index": i}, "fields": "index"}} for i, t in enumerate(order)])
    print("tab order written (index only)")
