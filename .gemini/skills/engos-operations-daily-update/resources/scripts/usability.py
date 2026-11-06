"""Read-only usability scan: what a reader (Medhat) or an editing leader would trip over.

  python3 usability.py DOC_ID 2026-11-09 --since 2026-11-05

Complements verify.py (rule checks). Exit 0 only with zero issues.
"""
import argparse
import datetime as dt
import re
import sys

import dudoc as du

PROCESS = re.compile(r"\b(agent|starting view|drafted by|placeholder|TODO|lorem)\b", re.I)
# Shorthand a leader outside the team would not know, and the expansion that must appear on the same tab.
JARGON = [(r"\bMR\b", "merge request (MR)"), (r"\bQE\b", "quality engineering (QE)"),
          (r"\bSDK\b", "software development kit (SDK)"), (r"\breqs?\b", None),
          (r"\bKata\b(?! container)", None), (r"\bEBC\b", "Executive Briefing Center (EBC)")]


def tab_text(tab):
    out = []

    def walk(content):
        for e in content:
            if "paragraph" in e:
                out.append(du.para_text(e["paragraph"]))
            elif "table" in e:
                for r in e["table"]["tableRows"]:
                    for c in r["tableCells"]:
                        walk(c["content"])
    walk(tab["documentTab"]["body"]["content"])
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc_id")
    ap.add_argument("date")
    ap.add_argument("--since", required=True)
    a = ap.parse_args()
    since = dt.date.fromisoformat(a.since)
    doc = du.read_doc(a.doc_id)
    ov, areas, inits = du.model(doc)
    issues = []
    names = sorted({du.title_parts(t["tabProperties"]["title"])[0] for t, _ in du.all_tabs(doc)}, key=len, reverse=True)

    def strip_names(text):
        for n in names:
            text = text.replace(n, "")
        return text

    def process(text):
        return PROCESS.search(strip_names(text))

    archive = next((t for t, p in du.all_tabs(doc) if p is None and t["tabProperties"]["title"].startswith("Archive")), None)
    archived = [du.Initiative(c, archive) for c in archive.get("childTabs", [])] if archive else []

    # ---- initiative tabs (active and archived) ----
    for i in inits + archived:
        secs = [s for s in i.sections if s.date >= since]
        for s in secs:
            tag = f"{i.name} {du.label(s.date)}"
            if s.status != "🟢" and not s.line("Green when:"):
                issues.append(f"{tag}: not green but no 'Green when' line (reader can't tell what fixes it)")
            if not s.unconfirmed and "sets this when they confirm" in (s.line("Green when:") or ""):
                issues.append(f"{tag}: placeholder 'Green when' on a confirmed section")
            if s.status == "🟢" and s.line("Green when:"):
                issues.append(f"{tag}: green section carries a 'Green when' line")
            for t, _ in s.lines:
                mm = re.match(r"Moved from .+ on (\w{3} \w{3} \d{1,2})\.", t)
                if mm and mm.group(1) != du.label(s.date):
                    issues.append(f"{tag}: '{t}' sits in another day's section")
            k = i.sections.index(s)
            prev = next((p for p in i.sections[k + 1:] if p.milestone), None)
            if prev and s.milestone and "No date set yet" in s.milestone and du.milestone_date(prev.milestone):
                if not re.search(r"date|milestone|slip|moved|done", s.line("Progress:") or "", re.I):
                    issues.append(f"{tag}: dated milestone '{prev.milestone}' dropped to 'No date set yet' with no reason")
            before = i.sections[k + 1] if k + 1 < len(i.sections) else None
            if before and before.status and s.status and s.status != before.status and not s.unconfirmed:
                prog = s.line("Progress:") or ""
                if not prog or prog.startswith("Progress: No change since"):
                    issues.append(f"{tag}: colour changed {before.status} -> {s.status} with no reason in Progress")
        for k, s in enumerate(i.sections):
            if any(t.startswith("Starting section drafted by") for t, _ in s.lines) \
                    and any(not x.unconfirmed for x in i.sections[:k]):
                issues.append(f"{i.name}: 'Starting section drafted by' line kept after a confirmed update")
        if i.sections and i.sections[0].no_change and not i.sections[0].status:
            issues.append(f"{i.name}: 'No change' section has no status")

    # ---- jargon, per tab ----
    for t, _ in du.all_tabs(doc):
        text = strip_names(tab_text(t))
        for pat, expansion in JARGON:
            m = re.search(pat, text)
            if m and (expansion is None or expansion not in text):
                issues.append(f"{t['tabProperties']['title']}: unexplained shorthand '{m.group(0)}'")

    # ---- links never point at private or person-specific things (A1) ----
    for t, _ in du.all_tabs(doc):
        def walk(content):
            for e in content:
                if "paragraph" in e:
                    for r in e["paragraph"]["elements"]:
                        u = r.get("textRun", {}).get("textStyle", {}).get("link", {}).get("url", "")
                        if re.search(r"mail\.google\.com|chat\.google\.com/.*/dm/|greenhouse|scorecard", u, re.I):
                            issues.append(f"{t['tabProperties']['title']}: link to a private or person-specific page: {u[:60]}")
                elif "table" in e:
                    for row in e["table"]["tableRows"]:
                        for c in row["tableCells"]:
                            walk(c["content"])
        walk(t["documentTab"]["body"]["content"])

    # ---- one name form for every person (A4) ----
    owners = {}
    for t, _ in du.all_tabs(doc):
        n = du.title_parts(t["tabProperties"]["title"])[1]
        if n:
            owners.setdefault(n.split()[0], set()).add(n)
    for first, forms in owners.items():
        if len(forms) > 1:
            issues.append(f"one person written {len(forms)} ways in tab titles: {sorted(forms)}")

    # ---- area headlines ----
    for ar in areas.values():
        if ar.headline and not re.search(r"\((Mon|Tue|Wed|Thu|Fri|Sat|Sun) \w{3} \d{1,2}\)$", ar.headline):
            issues.append(f"{ar.name} headline does not end with its date: '{ar.headline[-50:]}'")
        if process(ar.headline or ""):
            issues.append(f"{ar.name} headline has process text: '{ar.headline[:70]}'")

    # ---- overview ----
    body = ov["documentTab"]["body"]["content"]
    asof = next(du.para_text(e["paragraph"]) for e in body if "paragraph" in e and "As of" in du.para_text(e["paragraph"]))
    today = du.dates_in(asof)[0][1]
    for e in body:
        if "table" not in e:
            continue
        rows = e["table"]["tableRows"]
        head = [du.cell_text(c) for c in rows[0]["tableCells"]]
        for r in rows[1:]:
            vals = [du.cell_text(c) for c in r["tableCells"]]
            row = " | ".join(vals)
            if process(row):
                issues.append(f"overview table has process text: '{row[:80]}'")
            if head[0] == "Area":
                hl = vals[3]
                if re.search(r"\((Mon|Tue|Wed|Thu|Fri|Sat|Sun) \w{3} \d{1,2}\)$", hl):
                    issues.append(f"Area health: {vals[0]} headline repeats its date; the Updated column carries it: '{hl[-40:]}'")
                if vals[4] != du.label(today) and "(headline from " not in hl:
                    issues.append(f"Area health: {vals[0]} is not updated today and its headline is not flagged: '{hl[-40:]}'")
            if head[0] == du.DECISIONS_COL:
                if not any(x.get("textRun", {}).get("textStyle", {}).get("link")
                           for p in r["tableCells"][0]["content"] if "paragraph" in p for x in p["paragraph"]["elements"]):
                    issues.append(f"Decision '{vals[0]}' has no link to what is being decided")
    # ---- archive: one linked line per finished initiative ----
    if archive:
        aparas = [e for e in archive["documentTab"]["body"]["content"] if "paragraph" in e]
        for c in archive.get("childTabs", []):
            tid, title = c["tabProperties"]["tabId"], c["tabProperties"]["title"]
            line = next((e for e in aparas if du.para_text(e["paragraph"]).startswith(f"{title}, ")), None)
            linked = line and any(r.get("textRun", {}).get("textStyle", {}).get("link", {}).get("url", "").endswith(f"tab={tid}")
                                  for r in line["paragraph"]["elements"])
            if not linked:
                issues.append(f"Archive: '{title}' has no line of its own linked to its tab")

    for x in issues:
        print("ISSUE", x)
    print(f"\n{len(issues)} usability issues")
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
