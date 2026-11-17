#!/usr/bin/env python3
"""AC70 (inbox 127): the text tabs the daily path appends to (Definitions and the other small tabs) get their grid size from the LAYOUT build, with at least 50 percent spare rows; the daily path never resizes a tab
and refuses, before any write, when its text would overflow the reserved grid. Pure functions, no Sheet call (offline selftest: crew/agents/sheet/tabsize_selftest.py)."""
import math

TEXT_TABS = ("Data_Dictionary", "Individual", "README", "Thresholds", "Roster", "Roster_History", "Prompt_Library", "Run_Log", "Coverage", "Identity", "canvas_source")
SPARE = 1.5


# v1.41: canvas_source is a hidden machine tab (41 columns, about 5,500 rows) that changes only with a layout build: no 50% spare, which would cost 113,693 cells (copy 3 went over the 9.0M stop line)
NO_SPARE = ("canvas_source",)


def reserve(sizes):
    """layout build: sizes {tab: (rows used + 2, cols)} -> {tab: [rows with at least 50 percent spare, cols]} for the text tabs"""
    out = {}
    for t in TEXT_TABS:
        if t in sizes:
            r, c = sizes[t]
            used = max(r - 2, 0)
            out[t] = [r, c] if t in NO_SPARE else [max(r, math.ceil(used * SPARE) + 2), c]
    return out


def apply_daily(sizes, reserved):
    """daily path: returns (sizes with the reserved grid for every text tab, [overflow messages]); a tab whose rows or columns would not fit is reported and the caller refuses before any write"""
    msgs, out = [], dict(sizes)
    for t in TEXT_TABS:
        if t in sizes and t in reserved:
            r, c = sizes[t]; rr, rc = reserved[t]
            if r - 2 > rr - 2 or c > rc:
                msgs.append(f"{t}: needs {r - 2} rows and {c} columns, the reserved grid is {rr - 2} rows and {rc} columns: run the layout build (no write was made)")
            out[t] = (rr, rc)
    return out, msgs


def no_shrink(sizes, actual):
    """D415 rule: the daily path NEVER shrinks a tab (rows or columns); a dimension may only stay or grow. sizes: {tab: (rows, cols)} the build computed; actual: {tab: (rows, cols)} the Sheet has.
    -> (sizes with every dimension at least the actual one, [notes for each tab where the computed size was below the actual one])"""
    out, notes = dict(sizes), []
    for t, (r, c) in sizes.items():
        if t in actual:
            ar, ac = actual[t]
            if r < ar or c < ac:
                notes.append(f"{t}: computed {r} rows x {c} columns is below the actual {ar} x {ac}; the actual size is kept")
            out[t] = (max(r, ar), max(c, ac))
    return out, notes


CELL_STOP = 9_500_000          # v1.43 (user ruling 14 Nov): the Sheet may not pass 9,500,000 cells; Google's own cap is 10,000,000


def cell_guard(live_dims, new_sizes, stop=CELL_STOP):
    """B4: pure, no Sheet call. live_dims {tab: (rows, cols)} = the grids now; new_sizes {tab: (rows, cols)} = the grids this write would leave (a tab not listed keeps its grid; a tab not in live_dims is new).
    -> (projected total cells, [refusal messages]). Refuses when the projected total is over the stop line (a total equal to the stop passes) and names the tab that grows most."""
    live = sum(r * c for r, c in live_dims.values())
    grow = {t: r * c - (live_dims[t][0] * live_dims[t][1] if t in live_dims else 0) for t, (r, c) in new_sizes.items()}
    total = live + sum(grow.values())
    if total <= stop:
        return total, []
    worst = max(grow, key=lambda t: grow[t]) if grow else "no tab"
    return total, [f"CELLS: this write would take the Sheet to {total:,} cells ({live:,} now, {total - live:+,} from the grids it resizes; biggest change: {worst} {grow.get(worst, 0):+,}), over the {stop:,} stop line (Google's cap is 10,000,000): no write was made"]


def _selftest():
    out, notes = no_shrink({"Alert details": (2318, 52), "Metrics": (100, 20), "Roster": (50, 6)}, {"Alert details": (2318, 58), "Metrics": (90, 25), "Roster": (50, 6), "Other": (9, 9)})
    ok = out == {"Alert details": (2318, 58), "Metrics": (100, 25), "Roster": (50, 6)} and len(notes) == 2 and "Alert details" in notes[0] and "Metrics" in notes[1]          # Alerts 52 vs 58 is the case that would have deleted BA:BF
    ok &= all(out[t][0] >= a[0] and out[t][1] >= a[1] for t, a in {"Alert details": (2318, 58), "Metrics": (90, 25), "Roster": (50, 6)}.items())
    ok &= no_shrink({"X": (5, 5)}, {"X": (5, 5)}) == ({"X": (5, 5)}, [])
    print("tabsize no_shrink selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest() if "--selftest" in sys.argv else 2)
