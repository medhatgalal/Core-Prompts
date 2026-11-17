#!/usr/bin/env python3
"""D414 (option B): the daily path's range check, pure functions. A Metrics block may grow or shrink between pulls (a new week, items entering or leaving scope).
START row, columns and tab must still match the layout (a moved range is a stop); only the END row may differ, and only inside the block's reserved space
(up to the next layout block's start). The build then updates that named range's end in place (updateNamedRange: nothing created or deleted) and extends the chart sources that ended at the old end.
Selftest: python3 tools/sheet/daily_ranges.py --selftest"""
import sys


def classify(defs, old_named, ids_pre, blocks):
    """defs: [(name, tab, r0, c0, r1, c1)] as this run computes them (inclusive r1). old_named: {name: range dict}. ids_pre: {tab: sheetId}. blocks: layout [[name, start_row], ...] sorted by start.
    -> (hard [names], resized [(name, new_end_exclusive, old_end_exclusive)], overflow [(name, new_end, limit)])"""
    starts = sorted(b[1] for b in blocks)
    hard, resized, over = [], [], []
    for (nm, tab, r0, c0, r1, c1) in defs:
        o = old_named.get(nm)
        want = {"sheetId": ids_pre.get(tab), "startRowIndex": r0, "startColumnIndex": c0, "endColumnIndex": c1 + 1}
        if not o or any(o.get(k, 0) != v for k, v in want.items()):
            hard.append(nm); continue
        new_end = r1 + 1
        if o.get("endRowIndex", 0) != new_end:
            nxt = min([s for s in starts if s > r0] or [10 ** 9])
            (over if new_end > nxt else resized).append((nm, new_end, o.get("endRowIndex", 0)) if new_end <= nxt else (nm, new_end, nxt))
    return hard, resized, over


def chart_end(r1, old_end, new_end, shift=0):
    """a chart source row end: it followed the named range's end -> the new end; else shifted as before"""
    return new_end if r1 == old_end else r1 + shift


def selftest():
    ids = {"Metrics": 7}
    old = {"a": {"sheetId": 7, "startRowIndex": 10, "endRowIndex": 20, "startColumnIndex": 0, "endColumnIndex": 3},
           "b": {"sheetId": 7, "startRowIndex": 30, "endRowIndex": 40, "startColumnIndex": 0, "endColumnIndex": 3}}
    blocks = [["Metrics", 0], ["a", 10], ["b", 30], ["(end)", 100]]
    same = [("a", "Metrics", 10, 0, 19, 2), ("b", "Metrics", 30, 0, 39, 2)]
    ok = classify(same, old, ids, blocks) == ([], [], [])
    h, r, o = classify([("a", "Metrics", 10, 0, 22, 2), ("b", "Metrics", 30, 0, 37, 2)], old, ids, blocks)
    ok &= h == [] and o == [] and r == [("a", 23, 20), ("b", 38, 40)]                       # grow and shrink inside the block
    h, r, o = classify([("a", "Metrics", 10, 0, 30, 2)], old, ids, blocks); ok &= o and o[0][0] == "a" and r == []   # grows into the next block: stop
    ok &= classify([("a", "Metrics", 11, 0, 19, 2)], old, ids, blocks)[0] == ["a"]           # start moved
    ok &= classify([("a", "Metrics", 10, 0, 19, 3)], old, ids, blocks)[0] == ["a"]           # columns changed
    ok &= classify([("zz", "Metrics", 10, 0, 19, 2)], old, ids, blocks)[0] == ["zz"]         # a range the Sheet does not have
    ok &= classify([("a", "Other", 10, 0, 19, 2)], old, ids, blocks)[0] == ["a"]             # another tab
    ok &= chart_end(20, 20, 23) == 23 and chart_end(15, 20, 23) == 15 and chart_end(15, 20, 23, shift=2) == 17
    print("daily_ranges selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 2)
