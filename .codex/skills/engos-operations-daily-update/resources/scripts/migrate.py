"""One-time move of an existing doc to the v1.19.10 rules (doc owner only).

  python3 migrate.py DOC_ID              # review: prints every change, writes nothing
  python3 migrate.py DOC_ID --publish    # apply, then re-read and report
  python3 migrate.py DOC_ID --set "Federated Agent Studio (Nima)=🟡"   # the doc owner's call for a newest section
  python3 migrate.py DOC_ID --set "Composer UX (AlexD)@2026-11-05=🟡"   # ... or for one dated section

Every dated section on every initiative tab (Archive included) is recoloured by the new rule, its Confidence
line (chip) is removed, and its Green when line kept only when the section is not green. Area table Status
cells follow the newest sections, and each area headline loses its colour (the area's colour comes from its
initiatives). The Update guide tab is
rewritten to the new template. The overview is rebuilt separately with overview.py (the doc owner's close).

New colour, from what the section already says:
  🔴 and ⚪ are unchanged.
  🟡 or 🟢 with Confidence "Not confident", or waiting on someone ("Blocked on" is not "None.") -> 🟡
  otherwise 🟡 with any other Confidence -> 🟢; 🟡 with no Confidence line stays 🟡 (nothing says it will land).
Text that may now contradict its colour (a Progress line that opens "At risk", "Green", "Red", "Now dated",
and so on, or a headline sentence about risk) is listed for the doc owner and never rewritten here.
"""
import argparse
import re

import build
import dudoc as du
import guide
import modes as m

REASON = re.compile(r"^Progress: (At risk|Red\b|Green\b|Now green|Now dated|Now red|Now yellow|Yellow|Paused)", re.I)


def new_status(old, conf, blocked):
    if old in ("🔴", "⚪"):
        return old
    waiting = bool(blocked) and not re.match(r"Blocked on: None\.?$", blocked.strip())
    if conf == "Not confident" or waiting:
        return "🟡"
    if old == "🟡" and conf is None:
        return "🟡"
    return "🟢"


def plan_tab(tab_id, init, overrides=None):
    """(requests, report lines, newest new status) for one initiative tab. `overrides` maps a tab title to the
    colour the doc owner chose for its newest section."""
    reqs, report, newest = [], [], None
    for k, s in enumerate(init.sections):
        old = s.status
        conf_line = s.line("Confidence:")
        conf = conf_line[len("Confidence:"):].strip() if conf_line else None
        blocked = s.line("Blocked on:")
        new = new_status(old, conf, blocked)
        if overrides:
            dated = f"{init.title}@{s.date.isoformat()}"
            if dated in overrides:
                new = overrides[dated]
            elif k == 0 and init.title in overrides:
                new = overrides[init.title]
        if newest is None:
            newest = new
        changes = []
        els = {t: el for t, el in s.lines}
        st_line = next((t for t, _ in s.lines if t[:1] in du.STATUSES), None)
        if new != old and st_line:
            el = els[st_line]
            reqs.append(("replace", el["startIndex"], el["endIndex"] - 1, du.STATUSES[new]))
            changes.append(f"{old} -> {new}")
        if conf_line:
            el = els[conf_line]
            reqs.append(("delete", el["startIndex"], el["endIndex"], None))
            changes.append(f"remove Confidence ({conf})")
        gw = s.line("Green when:")
        if new == "🟢" and gw:
            el = els[gw]
            reqs.append(("delete", el["startIndex"], el["endIndex"], None))
            changes.append("remove Green when (now green)")
        if new != "🟢" and not gw and blocked:
            el = els[blocked]
            reqs.append(("insert_after", el["endIndex"] - 1, None, f"Green when: {init.updater} sets this when they confirm."))
            changes.append("add placeholder Green when (now not green)")
        prog = s.line("Progress:")
        flags = []
        if new != old and prog and REASON.match(prog):
            flags.append(f"Progress opens '{REASON.match(prog).group(1)}' but the colour is now {new}")
        if new != old and prog and re.search(r"\bat risk\b", prog, re.I) and new == "🟢":
            flags.append("Progress says 'at risk' but the section is now green")
        if changes or flags:
            report.append(f"  {du.label(s.date)}: " + "; ".join(changes + [f"CHECK: {f}" for f in flags]))
    return reqs, report, newest


def to_requests(tab_id, plan):
    out = []
    for kind, start, end, text in sorted(plan, key=lambda r: r[1], reverse=True):
        if kind == "replace":
            out += [{"deleteContentRange": {"range": {"startIndex": start, "endIndex": end, "tabId": tab_id}}},
                    {"insertText": {"location": {"index": start, "tabId": tab_id}, "text": text}}]
        elif kind == "delete":
            out.append({"deleteContentRange": {"range": {"startIndex": start, "endIndex": end, "tabId": tab_id}}})
        elif kind == "insert_after":
            n = du.utf16("\n" + text)
            out += [{"insertText": {"location": {"index": start, "tabId": tab_id}, "text": "\n" + text}},
                    {"updateTextStyle": {"range": {"startIndex": start + 1, "endIndex": start + n, "tabId": tab_id},
                                         "textStyle": {}, "fields": "bold,italic,link"}},
                    {"updateTextStyle": {"range": {"startIndex": start + 1, "endIndex": start + 1 + du.utf16("Green when:"),
                                                   "tabId": tab_id}, "textStyle": {"bold": True}, "fields": "bold"}}]
    return out


def split_table(doc_id, area):
    """Give an old 4-column Initiatives table its own Date column: 'Next milestone and date' becomes
    'Next milestone' and 'Date', and each row's milestone is split. Returns True when it changed the table."""
    if not area.table or area.split:
        return False
    tid = area.tab_id
    du.batch(doc_id, [{"insertTableColumn": {"tableCellLocation": {
        "tableStartLocation": {"index": area.table["startIndex"], "tabId": tid}, "rowIndex": 0, "columnIndex": 3},
        "insertRight": True}}])
    doc = du.read_doc(doc_id)
    ar = next(a for a in du.model(doc)[1].values() if a.tab_id == tid)
    reqs = []
    for k, r in enumerate(ar.table["table"]["tableRows"]):
        c3, c4 = r["tableCells"][3], r["tableCells"][4]
        old = du.cell_text(c3)
        vals = ("Next milestone", "Date") if k == 0 else du.split_milestone(old)
        for cell, val in ((c4, vals[1]), (c3, vals[0])):  # highest index first
            s0, e0 = cell["content"][0]["startIndex"], cell["content"][-1]["endIndex"] - 1
            if e0 > s0:
                reqs.append({"deleteContentRange": {"range": {"startIndex": s0, "endIndex": e0, "tabId": tid}}})
            reqs.append({"insertText": {"location": {"index": s0, "tabId": tid}, "text": val}})
            reqs.append({"updateTextStyle": {"range": {"startIndex": s0, "endIndex": s0 + du.utf16(val), "tabId": tid},
                                             "textStyle": {"bold": k == 0}, "fields": "bold"}})
            reqs.append({"updateParagraphStyle": {"range": {"startIndex": s0, "endIndex": s0 + du.utf16(val) + 1, "tabId": tid},
                                                  "paragraphStyle": {"alignment": "START"}, "fields": "alignment"}})
    reqs.sort(key=lambda q: next(iter(q.values())).get("range", next(iter(q.values())).get("location", {})).get("startIndex",
              next(iter(q.values())).get("location", {}).get("index", 0)), reverse=True)
    du.batch(doc_id, _ordered(reqs), doc)
    return True


def _ordered(reqs):
    """Requests grouped per cell are already highest-first; keep each cell's delete/insert/style together."""
    return reqs


def all_initiatives(doc):
    """Initiative tabs under areas and under Archive."""
    out = []
    for t, parent in du.all_tabs(doc):
        if parent is not None and not parent["tabProperties"]["title"].startswith(du.GUIDE):
            out.append(du.Initiative(t, parent))
    return out


def rewrite_guide(doc_id):
    doc = du.read_doc(doc_id)
    g = next((t for t, p in du.all_tabs(doc) if p is None and t["tabProperties"]["title"].startswith(du.GUIDE)), None)
    if not g:
        return False
    tid = g["tabProperties"]["tabId"]
    owner = du.title_parts(g["tabProperties"]["title"])[1] or ""
    body = g["documentTab"]["body"]["content"]
    end = body[-1]["endIndex"] - 1
    if end > 1:
        du.batch(doc_id, [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end, "tabId": tid}}}], doc)
    lines, styles, links = guide.content(owner, du.tab_url(doc_id, "t.0"), du.overview_title(du.read_doc(doc_id)))
    reqs = m._paras(tid, 1, lines, styles, links)
    k = next(i for i, x in enumerate(lines) if x.startswith("Status: "))
    at = 1 + sum(du.utf16(x) + 1 for x in lines[:k])
    reqs.append({"updateTextStyle": {"range": {"startIndex": at, "endIndex": at + 7, "tabId": tid},
                                     "textStyle": {"bold": True}, "fields": "bold"}})
    du.batch(doc_id, reqs)
    # Drop the empty paragraph the old body leaves behind after the new text.
    tab = m.find_tab(du.read_doc(doc_id), tid)
    last = [e for e in tab["documentTab"]["body"]["content"] if "paragraph" in e]
    if len(last) > 1 and not du.para_text(last[-1]["paragraph"]).strip() and not du.para_text(last[-2]["paragraph"]).strip():
        du.batch(doc_id, [{"deleteContentRange": {"range": {"startIndex": last[-2]["startIndex"],
                                                            "endIndex": last[-2]["endIndex"], "tabId": tid}}}])
    return True


def run(doc_id, publish=False, overrides=None):
    doc = du.read_doc(doc_id)
    _, areas, _ = du.model(doc)
    inits = all_initiatives(doc)
    newest = {}
    print(f"MIGRATION {'APPLY' if publish else 'REVIEW'}: {du.overview_title(doc)}")
    for i in inits:
        plan, report, nst = plan_tab(i.tab_id, i, overrides)
        newest[i.title] = nst
        if report:
            print(f"{i.title}")
            print("\n".join(report))
        if publish and plan:
            fresh = du.read_doc(doc_id)
            ii = next(x for x in all_initiatives(fresh) if x.tab_id == i.tab_id)
            plan2, _, _ = plan_tab(ii.tab_id, ii, overrides)
            du.batch(doc_id, to_requests(ii.tab_id, plan2), fresh)
    for ar in areas.values():
        if ar.table and not ar.split:
            print(f"{ar.title} table: split 'Next milestone and date' into 'Next milestone' and 'Date'")
            if publish:
                split_table(doc_id, ar)
    if publish:
        _, areas, _ = du.model(du.read_doc(doc_id))
    for ar in areas.values():
        mine = [i for i in inits if i.area_title == ar.title]
        rows = {r[0]: r for r in ar.rows()}
        for i in mine:
            r = rows.get(i.name)
            want = newest.get(i.title)
            if r and want and r[2][:1] != want:
                print(f"{ar.title} table: {i.name} {r[2][:1]} -> {want}")
                if publish:
                    m.set_row(doc_id, ar.tab_id, i.name, [r[0], r[1], du.STATUSES[want], du.Area.row_milestone(r)])
        hl = ar.headline or ""
        if hl[:1] in du.STATUSES:
            print(f"{ar.title} headline: remove its colour ({hl[:1]}); the area's colour comes from its initiatives")
            if publish:
                build.set_headline(doc_id, ar.title, build.strip_colour(hl))
    print("Update guide: rewrite to the new template" + (" (done)" if publish and rewrite_guide(doc_id) else ""))
    if publish:
        du.repair_headings(doc_id)
        for f in build.fit_tables(doc_id):
            print("Table widths fixed: " + f)
        left = [(i.title, du.label(s.date)) for i in all_initiatives(du.read_doc(doc_id)) for s in i.sections
                if s.line("Confidence:")]
        print("RE-READ: Confidence lines left:", left or "none")
    else:
        print("\nPublish? (re-run with --publish)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc_id")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--set", action="append", default=[], metavar='"<Tab title>=🟡"',
                    help="the doc owner's colour for a tab's newest section, overriding the mapping")
    a = ap.parse_args()
    run(a.doc_id, a.publish, dict(x.rsplit("=", 1) for x in a.set))


if __name__ == "__main__":
    main()
