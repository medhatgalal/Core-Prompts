"""Run the skill's Overview steps on an E2E TEST doc, for the parts a script can decide.

  python3 overview.py DOC_ID 2026-11-06 "4:00 PM ET"            # review only
  python3 overview.py DOC_ID 2026-11-06 "4:00 PM ET" --publish

Rewrites the "As of" line and everything below it: Area health, the decisions table (rows and their links kept
as they are), Next 2 weeks, How to update, Status key and the grey line. That also moves an older overview to
this layout (its "In 30 seconds" and "Not updated today" sections go). Area health headline links are kept
where their phrase is still in the headline; any initiative name in a headline links to its tab. A Next 2 weeks
row is the milestone without its date, exactly as its section words it (never shortened here).
"""
import argparse
import datetime as dt
import re

import build
import dudoc as du
import modes as m

KEY = ["🔴 Red: a committed date passed and it is not done, or it is blocked and nobody owns the fix.",
       "🟡 At risk: the updater does not expect the next milestone to land on its date, or it waits on another team.",
       "🟢 On track: the updater expects the next milestone to land on its date.",
       "⚪ Paused: paused or not started.",
       "A missing date is not a colour: Missing a plan lists every open initiative without a dated next milestone."]
MISSING_HEAD = "Missing a plan"
MISSING_NONE = "Every open initiative has a dated next milestone."
GREY_LINE = "Drafted by AI agents from each leader's sources. Sections an owner has not confirmed yet say so."


def area_view(area, inits, today):
    mine = [i for i in inits if i.area_title == area.title]
    statuses = [i.newest("status").status if i.newest("status") else "🟡" for i in mine]
    status = du.worst(statuses) or "⚪"
    confirmed = [s.date for i in mine for s in i.sections if not s.unconfirmed]
    hl = area.headline or ""
    hl_dates = du.dates_in(hl)
    hl_date = hl_dates[-1][1] if hl_dates else None
    updated = max(confirmed + ([hl_date] if hl_date else []), default=None)
    sentence = build.strip_colour(hl)
    sentence = re.sub(r"\s*\((Mon|Tue|Wed|Thu|Fri|Sat|Sun) \w{3} \d{1,2}\)$", "", sentence)
    reasons = []
    if hl_date and updated and hl_date < updated:
        reasons.append(f"headline {du.label(hl_date)} older than newest update {du.label(updated)}")
    if reasons:
        cell = f"{sentence} (headline from {du.label(hl_date) if hl_date else 'unknown date'}; out of date with its tabs)"
    elif hl_date and hl_date < today:
        cell = f"{sentence} (headline from {du.label(hl_date)}; not updated today)"
    else:
        cell = sentence  # the Updated column carries the date
    return {"area": area, "status": status, "counts": du.status_counts(statuses), "cell": cell, "updated": updated,
            "reasons": reasons}


def missing_header():
    return ["Initiative", "Owner", "What's missing", "Since"]


def missing_cells(i, what, since, today):
    """'Since' carries how long it has gone unfixed; over two weeks is marked."""
    if since is None:
        return [i.name, i.owner, what, "Not yet"]
    old = (today - since).days > 14
    return [i.name, i.owner, what, du.label(since) + (" (over 2 weeks)" if old else "")]


def cell_links(cell):
    """(phrase, url) for each linked run in a table cell."""
    return [(x["textRun"]["content"].strip(), x["textRun"]["textStyle"]["link"]["url"])
            for p in cell["content"] if "paragraph" in p for x in p["paragraph"]["elements"]
            if x.get("textRun", {}).get("textStyle", {}).get("link", {}).get("url")]


def link_phrase(tid, cell, phrase, url, reqs):
    """Link the first `phrase` in a table cell to `url`. False when the phrase is not there."""
    for p in cell["content"] if phrase else []:
        for x in p.get("paragraph", {}).get("elements", []):
            t = x.get("textRun", {}).get("content", "")
            k = t.find(phrase)
            if k >= 0:
                s = x["startIndex"] + du.utf16(t[:k])
                reqs.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + du.utf16(phrase), "tabId": tid},
                                                 "textStyle": {"link": {"url": url}}, "fields": "link"}})
                return True
    return False


def tables_by_head(tab):
    return {du.cell_text(e["table"]["tableRows"][0]["tableCells"][0]): e for e in tab["documentTab"]["body"]["content"] if "table" in e}


def rebuild(doc_id, today, time):
    doc = du.read_doc(doc_id)
    ov, areas, inits = du.model(doc)
    tid = ov["tabProperties"]["tabId"]
    views = [area_view(ar, inits, today) for ar in areas.values()]
    body = ov["documentTab"]["body"]["content"]

    # Keep the decisions rows (old "Decision" or new header) with their links, and the Area health headline links.
    old = tables_by_head(ov)
    dec = old.get(du.DECISIONS_COL) or old.get("Decision")
    rows = dec["table"]["tableRows"][1:] if dec else []
    decisions = [[du.cell_text(c) for c in r["tableCells"]] for r in rows]
    dec_links = [cell_links(r["tableCells"][0]) for r in rows]
    hl_links = {du.cell_text(r["tableCells"][0]): cell_links(r["tableCells"][3])
                for r in (old["Area"]["table"]["tableRows"][1:] if "Area" in old else [])}
    # Delete everything from the first heading to the end; update the "As of" line.
    paras = [e for e in body if "paragraph" in e]
    first = next((e for e in paras if e["paragraph"]["paragraphStyle"].get("namedStyleType") == "HEADING_2"), None)
    start, end = (first["startIndex"] if first else body[-1]["endIndex"] - 1), body[-1]["endIndex"] - 1
    asof = next(e for e in paras if "As of" in du.para_text(e["paragraph"]))
    asof_txt = du.para_text(asof["paragraph"]).rstrip("\n")
    lead = asof_txt.split("As of")[0]
    reqs = [{"deleteContentRange": {"range": {"startIndex": start, "endIndex": end, "tabId": tid}}}] if end > start else []
    reqs += [{"deleteContentRange": {"range": {"startIndex": asof["startIndex"] + du.utf16(lead), "endIndex": asof["endIndex"] - 1, "tabId": tid}}},
             {"insertText": {"location": {"index": asof["startIndex"] + du.utf16(lead), "tabId": tid},
                             "text": f"As of {du.label(today, True)}, {time}"}}]
    du.batch(doc_id, reqs, doc)

    # Write the sections, then the tables into their empty paragraphs.
    # Each row is the milestone as its section words it; reword it there, not here.
    nxt = [(d, c, [(c, du.tab_url(doc_id, i.tab_id))], st) for d, c, i, st in du.next_two_weeks(inits, today)]
    missing = du.missing_plan(inits, today)
    lines = (["Area health", "", MISSING_HEAD, "" if missing else MISSING_NONE] + ([du.DECISIONS_HEAD, ""] if decisions else []) +
             [du.NEXT_HEAD, "" if nxt else "No dated commitments in the next 2 weeks.", "How to update"] +
             [x.replace("`", "") for x in build.HOW_TO] + ["Status key"] + KEY + [GREY_LINE])
    heads = {"Area health", MISSING_HEAD, du.DECISIONS_HEAD, du.NEXT_HEAD, "How to update", "Status key"}
    doc = du.read_doc(doc_id)
    at = m.find_tab(doc, tid)["documentTab"]["body"]["content"][-1]["startIndex"]
    reqs = m._paras(tid, at, lines, ["HEADING_2" if x in heads else "NORMAL_TEXT" for x in lines])
    n = du.utf16("\n".join(lines) + "\n")
    reqs += [{"deleteParagraphBullets": {"range": {"startIndex": at, "endIndex": at + n, "tabId": tid}}},
             {"updateTextStyle": {"range": {"startIndex": at, "endIndex": at + n, "tabId": tid}, "textStyle": {},
                                  "fields": "foregroundColor,fontSize,weightedFontFamily"}}]
    du.batch(doc_id, reqs, doc)

    build.add_table(doc_id, tid, build.anchor_index(doc_id, tid, "Area health"),
                    [["Area", "Owner", "Status", "Headline", "Updated"]] +
                    [[v["area"].name, v["area"].owner, v["counts"], v["cell"], du.label(v["updated"]) if v["updated"] else "Not yet"]
                     for v in views], build.AREA_SHARES)
    if missing:
        build.add_table(doc_id, tid, build.anchor_index(doc_id, tid, MISSING_HEAD), [missing_header()] +
                        [missing_cells(i, what, since, today) for i, what, since in missing], build.MISSING_SHARES)
    if decisions:
        build.add_table(doc_id, tid, build.anchor_index(doc_id, tid, du.DECISIONS_HEAD),
                        [[du.DECISIONS_COL, "Why now", "Recommend", "By", "Owner"]] + decisions, build.DECISION_SHARES)
    if nxt:
        build.add_table(doc_id, tid, build.anchor_index(doc_id, tid, du.NEXT_HEAD), [["Date", "Commitment", "Status"]] +
                        [[du.next_two_weeks_date(d, today), c, st] for d, c, _, st in nxt], build.NEXT_SHARES)

    build.style_how_to(doc_id, tid)
    build.fit_tables(doc_id)
    doc = du.read_doc(doc_id)
    gid = next((t["tabProperties"]["tabId"] for t, p in du.all_tabs(doc) if p is None and t["tabProperties"]["title"].startswith(du.GUIDE)), None)
    if gid:
        build.link_guide_line(doc_id, gid)
        doc = du.read_doc(doc_id)
    grey = next(e for e in m.find_tab(doc, tid)["documentTab"]["body"]["content"]
                if "paragraph" in e and du.para_text(e["paragraph"]).strip() == GREY_LINE)
    du.batch(doc_id, [{"updateTextStyle": {"range": {"startIndex": grey["startIndex"], "endIndex": grey["endIndex"] - 1, "tabId": tid},
                                           "textStyle": {"foregroundColor": build.GREY, "fontSize": {"magnitude": 9, "unit": "PT"}},
                                           "fields": "foregroundColor,fontSize"}}], doc)

    # Links: each area name and headline phrase, decision and commitment to its tab.
    doc = du.read_doc(doc_id)
    new = tables_by_head(m.find_tab(doc, tid))
    reqs = []
    for r, v in zip(new["Area"]["table"]["tableRows"][1:], views):
        ar = v["area"]
        link_phrase(tid, r["tableCells"][0], ar.name, du.tab_url(doc_id, ar.tab_id), reqs)
        names = [(i.name, du.tab_url(doc_id, i.tab_id)) for i in inits if i.area_title == ar.title]
        done = set()
        for phrase, url in hl_links.get(ar.name, []) + names:
            if phrase not in done and link_phrase(tid, r["tableCells"][3], phrase, url, reqs):
                done.add(phrase)
    for r, (i, _, _) in zip(new["Initiative"]["table"]["tableRows"][1:] if missing else [], missing):
        link_phrase(tid, r["tableCells"][0], i.name, du.tab_url(doc_id, i.tab_id), reqs)
    for r, links in zip(new[du.DECISIONS_COL]["table"]["tableRows"][1:] if decisions else [], dec_links):
        for phrase, url in links:
            link_phrase(tid, r["tableCells"][0], phrase, url, reqs)
    for r, (_, _, links, _) in zip(new["Date"]["table"]["tableRows"][1:] if nxt else [], nxt):
        for phrase, url in links:
            link_phrase(tid, r["tableCells"][1], phrase, url, reqs)
    du.batch(doc_id, reqs, doc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc_id")
    ap.add_argument("date")
    ap.add_argument("time")
    ap.add_argument("--publish", action="store_true")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.date)

    doc = du.read_doc(a.doc_id)
    ov, areas, inits = du.model(doc)
    views = [area_view(ar, inits, today) for ar in areas.values()]

    print(f"OVERVIEW REVIEW {du.label(today, True)}")
    for v in views:
        print(f"  {v['area'].name}: {v['counts'].replace(chr(10), ' ')} | {v['cell']}")
        if v["reasons"]:
            print(f"     FLAG: {'; '.join(v['reasons'])}. Offer a note to {v['area'].owner} (drafted, not sent).")
    for i, what, since in du.missing_plan(inits, today):
        print(f"  Missing a plan: {' | '.join(missing_cells(i, what, since, today))}")
    for d, c, i, st in du.next_two_weeks(inits, today):
        print(f"  Next 2 weeks: {du.next_two_weeks_date(d, today)} | {c} ({i.name}) | {st}")
    if not a.publish:
        print("\nPublish? (re-run with --publish)")
        return

    rebuild(a.doc_id, today, a.time)

    # Re-read and quote.
    ov = du.model(du.read_doc(a.doc_id))[0]
    out = []
    for e in ov["documentTab"]["body"]["content"]:
        if "paragraph" in e:
            out.append(du.para_text(e["paragraph"]).rstrip("\n"))
        elif "table" in e:
            for r in e["table"]["tableRows"]:
                out.append(" | ".join(du.cell_text(c).replace("\n", " / ") for c in r["tableCells"]))
    print("RE-READ OVERVIEW:\n" + "\n".join(x for x in out if x))


if __name__ == "__main__":
    main()
