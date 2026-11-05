"""Run the skill's Overview steps on an E2E TEST doc, for the parts a script can decide.

  python3 overview.py DOC_ID 2026-11-06 "4:00 PM ET"            # review only
  python3 overview.py DOC_ID 2026-11-06 "4:00 PM ET" --publish

Rewrites the "As of" line and everything below "In 30 seconds": Area health, Not updated today, the
decisions table (rows kept as they are), Next 2 weeks, How to update, Status key and the grey line. That also
moves an older overview to this layout. Leaves "In 30 seconds" alone: that is a judgement call the agent makes.
"""
import argparse
import datetime as dt
import re

import build
import dudoc as du
import modes as m

KEY = ["🔴 Red: a committed date passed and it is not done, or blocked with no owned fix and date.",
       "🟡 At risk: next milestone has no date, or something owed or undecided could slip the date.",
       "🟢 On track: none of the above.",
       "⚪ Paused: paused or not started."]
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
    sentence = re.sub(r"^[🔴🟡🟢⚪] [^·]*· ", "", hl)
    sentence = re.sub(r"\s*\((Mon|Tue|Wed|Thu|Fri|Sat|Sun) \w{3} \d{1,2}\)$", "", sentence)
    hl_status = hl[:1] if hl[:1] in du.STATUSES else None
    reasons = []
    if hl_date and updated and hl_date < updated:
        reasons.append(f"headline {du.label(hl_date)} older than newest update {du.label(updated)}")
    if hl_status and hl_status != status:
        reasons.append(f"headline says {hl_status}, tabs say {status}")
    if reasons:
        cell = f"{sentence} (headline from {du.label(hl_date) if hl_date else 'unknown date'}; out of date with its tabs)"
    elif hl_date and hl_date < today:
        cell = f"{sentence} (headline from {du.label(hl_date)}; not updated today)"
    else:
        cell = sentence  # the Updated column carries the date
    stale = [i for i in mine if not i.sections or i.sections[0].date < today or i.sections[0].unconfirmed]
    return {"area": area, "status": status, "counts": du.status_counts(statuses), "cell": cell, "updated": updated,
            "reasons": reasons, "stale": stale}


def link_col(doc_id, tid, first_cell, col, urls):
    """Link column `col` of the table whose header starts with `first_cell`, one url per body row."""
    doc = du.read_doc(doc_id)
    tbl = next(e for e in du.model(doc)[0]["documentTab"]["body"]["content"]
               if "table" in e and du.cell_text(e["table"]["tableRows"][0]["tableCells"][0]) == first_cell)
    reqs = []
    for r, url in zip(tbl["table"]["tableRows"][1:], urls):
        c = r["tableCells"][col]
        reqs.append({"updateTextStyle": {"range": {"startIndex": c["startIndex"] + 1, "endIndex": c["endIndex"] - 1, "tabId": tid},
                                         "textStyle": {"link": {"url": url}}, "fields": "link"}})
    du.batch(doc_id, reqs, doc)


def rebuild(doc_id, today, time):
    doc = du.read_doc(doc_id)
    ov, areas, inits = du.model(doc)
    tid = ov["tabProperties"]["tabId"]
    views = [area_view(ar, inits, today) for ar in areas.values()]
    body = ov["documentTab"]["body"]["content"]

    # Keep the decisions rows (old "Decision" or new header) and each row's link.
    dec = next((e for e in body if "table" in e and du.cell_text(e["table"]["tableRows"][0]["tableCells"][0])
                in ("Decision", du.DECISIONS_COL)), None)
    decisions, dec_links = [], []
    for r in (dec["table"]["tableRows"][1:] if dec else []):
        decisions.append([du.cell_text(c) for c in r["tableCells"]])
        dec_links.append(next((x["textRun"]["textStyle"]["link"]["url"] for p in r["tableCells"][0]["content"] if "paragraph" in p
                               for x in p["paragraph"]["elements"] if x.get("textRun", {}).get("textStyle", {}).get("link", {}).get("url")), None))

    # Delete everything from the first heading after "In 30 seconds" to the end; update the "As of" line.
    paras = [e for e in body if "paragraph" in e]
    i30 = next(k for k, e in enumerate(paras) if du.para_text(e["paragraph"]).strip() == "In 30 seconds")
    first = next((e for e in paras[i30 + 1:] if e["paragraph"]["paragraphStyle"].get("namedStyleType") == "HEADING_2"), None)
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
    stale = [(i, v) for v in views for i in v["stale"]]
    count = f"{sum(1 for v in views if v['stale'])} of {len(views)} areas not fully updated today."
    nxt = du.next_two_weeks(inits, today)
    lines = (["Area health", "", "Not updated today", count] + ([""] if stale else []) +
             [du.NEXT_HEAD, "" if nxt else "No dated commitments in the next 2 weeks.", "How to update"] +
             [x.replace("`", "") for x in build.HOW_TO] + ["Status key"] + KEY + [GREY_LINE])
    heads = {"Area health", "Not updated today", du.NEXT_HEAD, "How to update", "Status key"}
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
                     for v in views], [22, 10, 11, 43, 14])
    if stale:
        def last_confirmed(i):
            s = next((x for x in i.sections if not x.unconfirmed), None)
            return du.label(s.date) if s else "None yet"
        build.add_table(doc_id, tid, build.anchor_index(doc_id, tid, count), [["Initiative", "Area", "Updater", "Last confirmed"]] +
                        [[i.name, v["area"].name, i.updater, last_confirmed(i)] for i, v in stale], [34, 26, 18, 22])
        link_col(doc_id, tid, "Initiative", 0, [du.tab_url(doc_id, i.tab_id) for i, _ in stale])
    if nxt:
        build.add_table(doc_id, tid, build.anchor_index(doc_id, tid, du.NEXT_HEAD), [["Date", "Commitment", "Initiative", "Status"]] +
                        [[du.label(d), c, i.name, du.STATUSES[st]] for d, c, i, st in nxt], [16, 44, 26, 14])
        link_col(doc_id, tid, "Date", 2, [du.tab_url(doc_id, i.tab_id) for _, _, i, _ in nxt])
    if decisions:
        build.set_decisions(doc_id, None, decisions, dec_links)

    build.style_how_to(doc_id, tid)
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
    n_stale = sum(1 for v in views if v["stale"])

    print(f"OVERVIEW REVIEW {du.label(today, True)}")
    for v in views:
        print(f"  {v['area'].name}: {v['counts'].replace(chr(10), ' ')} | {v['cell']}")
        if v["reasons"]:
            print(f"     FLAG: {'; '.join(v['reasons'])}. Offer a note to {v['area'].owner} (drafted, not sent).")
    print(f"  Not updated today: {n_stale} of {len(views)} areas")
    for d, c, i, st in du.next_two_weeks(inits, today):
        print(f"  Next 2 weeks: {du.label(d)} | {c} | {i.name} | {du.STATUSES[st]}")
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
