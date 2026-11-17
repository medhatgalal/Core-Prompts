"""Insights tab: render, check (AC45), and write. No model call; computes no metric.

Numbers are never typed: each {CELL} placeholder in data/insights/items.json is replaced by code with that Metrics
cell's displayed (FORMATTED_VALUE) text. Checks: no digit outside a placeholder; every placeholder is
cited; comparatives confirmed from the cited cells; no roster name appears; 3 to 8 items.

Usage: python3 -I tools/insights/insights.py check|write|verify
  check  : render from live Metrics and run the checks (no write)
  write  : check, then rewrite the Insights tab (only tab touched)
  verify : read the Insights tab back and confirm every number equals its cited cell now
"""
import csv, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITEMS = ROOT / "data/insights/items.json"
CFG = json.loads((ROOT / "data/config.json").read_text())
SHEET = CFG["sheet_id"]
PH = re.compile(r"\{([A-Z]+[0-9]+)\}")


def gws(args, body=None):
    cmd = ["gws", "sheets", "spreadsheets", *args]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-500:])
    txt = out.stdout
    return json.loads(txt[txt.index("{"):]) if "{" in txt else {}


def read_tab(tab):
    p = {"spreadsheetId": SHEET, "range": tab, "valueRenderOption": "FORMATTED_VALUE"}
    return gws(["values", "get", "--params", json.dumps(p)]).get("values", [])


def a1(ref):
    m = re.fullmatch(r"([A-Z]+)([0-9]+)", ref)
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return int(m.group(2)) - 1, col - 1


def cell(grid, ref):
    r, c = a1(ref)
    return grid[r][c] if r < len(grid) and c < len(grid[r]) else ""


def cells(grid, rng):
    a, b = rng.split(":")
    (r1, c1), (r2, c2) = a1(a), a1(b)
    return [cell(grid, f"{chr(65 + c)}{r + 1}") for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


def num(s):
    return float(s.replace(",", "").rstrip("%"))


def names():
    out = set()
    with open(ROOT / "data/roster.csv") as f:
        for row in csv.DictReader(f):
            for k in ("name", "chart_name"):
                n = (row.get(k) or "").strip()
                if n:
                    out.add(n)
                    out.update(p for p in n.split() if len(p) > 3)
    return out


def render(spec, grid):
    rows, errors = [], []
    for it in spec["items"]:
        refs = PH.findall(it["text"])
        if re.search(r"[0-9]", PH.sub("", it["text"])):
            errors.append(f"{it['id']}: digit outside a placeholder")
        cited = set()
        for c in it["cites"]:
            if ":" in c:
                a, b = c.split(":")
                (r1, c1), (r2, c2) = a1(a), a1(b)
                cited.update(f"{chr(65 + cc)}{r + 1}" for r in range(r1, r2 + 1) for cc in range(c1, c2 + 1))
            else:
                cited.add(c)
        for r in refs:
            if r not in cited:
                errors.append(f"{it['id']}: {r} used but not cited")
            if cell(grid, r) == "":
                errors.append(f"{it['id']}: {r} is blank")
        for left, op, right in it["comparatives"]:
            lv = num(cell(grid, left))
            if op == ">":
                ok = lv > num(cell(grid, right))
            else:
                vals = [num(v) for v in cells(grid, right) if v != ""]
                others = list(vals)
                others.remove(lv)
                ok = all(lv > o for o in others) if op == "max_of" else all(lv < o for o in others)
            if not ok:
                errors.append(f"{it['id']}: comparative {left} {op} {right} not confirmed")
        text = PH.sub(lambda m: cell(grid, m.group(1)), it["text"])
        for n in names():
            if re.search(rf"\b{re.escape(n)}\b", text):
                errors.append(f"{it['id']}: roster name '{n}' appears")
        rows.append([it["id"], text, ", ".join("Metrics!" + c for c in it["cites"])])
    if not 3 <= len(rows) <= 8:
        errors.append(f"item count {len(rows)} not in 3..8")
    return rows, errors


def main(mode):
    spec = json.loads(ITEMS.read_text())
    grid = read_tab("Metrics")
    rows, errors = render(spec, grid)
    if mode == "verify":
        tab = read_tab("Insights")
        got = {r[0]: r[1] for r in tab[3:] if len(r) > 1}
        for rid, text, _ in rows:
            if got.get(rid) != text:
                errors.append(f"{rid}: Insights tab text differs from a fresh render of the cited cells")
        n = sum(len(PH.findall(it["text"])) for it in spec["items"])
        print(json.dumps({"items": len(rows), "numbers": n, "errors": errors}, indent=2))
        return 1 if errors else 0
    print(json.dumps({"rows": rows, "errors": errors}, indent=2))
    if errors:
        return 1
    if mode == "write":
        header = [[spec["label"]],
                  [f"Metrics as of {cell(grid, spec['as_of_cell'])} (Metrics!{spec['as_of_cell']}); last complete week starts {cell(grid, spec['last_week_cell'])} (Metrics!{spec['last_week_cell']})"],
                  [],
                  ["item", "insight", "cited Metrics cells"]]
        gws(["values", "clear", "--params", json.dumps({"spreadsheetId": SHEET, "range": "Insights"})], body={})
        gws(["values", "update", "--params", json.dumps({"spreadsheetId": SHEET, "range": "Insights!A1",
                                                          "valueInputOption": "RAW"})],
            body={"values": header + rows})
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "check"))
