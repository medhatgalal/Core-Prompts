"""Run the skill's Overview steps on an E2E TEST doc, for the parts a script can decide.

  python3 overview.py DOC_ID 2026-11-06 "4:00 PM ET"            # review only
  python3 overview.py DOC_ID 2026-11-06 "4:00 PM ET" --publish

Rewrites: the "As of" line, the Area health table (Status, Headline, Updated) and "Not updated today".
Leaves "In 30 seconds" and "Needs decision" alone: those are judgement calls the agent makes in a real run.
"""
import argparse
import datetime as dt
import re

import build
import dudoc as du


def area_view(area, inits, today):
    mine = [i for i in inits if i.area_title == area.title]
    status = du.worst(i.newest("status").status if i.newest("status") else "🟡" for i in mine) or "⚪"
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
        cell = f"{sentence} ({du.label(hl_date)})" if hl_date else sentence
    stale = [i for i in mine if not i.sections or i.sections[0].date < today or i.sections[0].unconfirmed]
    return {"area": area, "status": status, "cell": cell, "updated": updated, "reasons": reasons, "stale": stale}


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
        print(f"  {v['area'].name}: {du.STATUSES[v['status']]} | {v['cell']}")
        if v["reasons"]:
            print(f"     FLAG: {'; '.join(v['reasons'])}. Offer a note to {v['area'].owner} (drafted, not sent).")
    print(f"  Not updated today: {n_stale} of {len(views)} areas")
    if not a.publish:
        print("\nPublish? (re-run with --publish)")
        return

    body = ov["documentTab"]["body"]["content"]
    tid = ov["tabProperties"]["tabId"]
    reqs = []

    # Area health table rows, keyed by area name in column 0.
    table = next(e for e in body if "table" in e and du.cell_text(e["table"]["tableRows"][0]["tableCells"][0]) == "Area")
    rows = table["table"]["tableRows"]
    by_name = {v["area"].name: v for v in views}
    cell_edits = []
    for r in rows[1:]:
        v = by_name.get(du.cell_text(r["tableCells"][0]))
        if not v:
            continue
        vals = {2: du.STATUSES[v["status"]], 3: v["cell"], 4: du.label(v["updated"]) if v["updated"] else "Not yet"}
        for ci, val in vals.items():
            c = r["tableCells"][ci]
            cell_edits.append((c["content"][0]["startIndex"], c["content"][-1]["endIndex"] - 1, val))

    paras = [e for e in body if "paragraph" in e]

    # "As of" line.
    asof = next(e for e in paras if "As of" in du.para_text(e["paragraph"]))
    asof_txt = du.para_text(asof["paragraph"]).rstrip("\n")
    new_asof = re.sub(r"As of .*$", f"As of {du.label(today, True)}, {a.time}", asof_txt)
    asof_start = asof["startIndex"] + du.utf16(asof_txt.split("As of")[0])

    # Area health cells and the As-of line, from the highest index down.
    edits = sorted([(s, e, t) for s, e, t in cell_edits] +
                   [(asof_start, asof["endIndex"] - 1, new_asof[len(asof_txt.split("As of")[0]):])], key=lambda x: -x[0])
    for s, e, t in edits:
        if e > s:
            reqs.append({"deleteContentRange": {"range": {"startIndex": s, "endIndex": e, "tabId": tid}}})
        reqs.append({"insertText": {"location": {"index": s, "tabId": tid}, "text": t}})
    du.batch(a.doc_id, reqs, doc)

    # "Not updated today": a count line, then a table (Initiative, Area, Updater, Last confirmed).
    doc = du.read_doc(a.doc_id)
    paras = [e for e in du.model(doc)[0]["documentTab"]["body"]["content"] if "paragraph" in e]
    h = next(i for i, e in enumerate(paras) if du.para_text(e["paragraph"]).strip() == "Not updated today")
    nxt = next(e for e in paras[h + 1:] if e["paragraph"]["paragraphStyle"].get("namedStyleType") == "HEADING_2")
    start, end = paras[h]["endIndex"], nxt["startIndex"]
    count = f"{n_stale} of {len(views)} areas not fully updated today."
    stale = [(i, v) for v in views for i in v["stale"]]
    text = count + ("\n\n" if stale else "\n")
    reqs = [{"deleteContentRange": {"range": {"startIndex": start, "endIndex": end, "tabId": tid}}},
            {"insertText": {"location": {"index": start, "tabId": tid}, "text": text}},
            {"updateParagraphStyle": {"range": {"startIndex": start, "endIndex": start + du.utf16(text), "tabId": tid},
                                      "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"}, "fields": "namedStyleType"}},
            {"updateTextStyle": {"range": {"startIndex": start, "endIndex": start + du.utf16(text), "tabId": tid},
                                 "textStyle": {}, "fields": "link,bold"}},
            {"updateParagraphStyle": {"range": {"startIndex": paras[h]["startIndex"], "endIndex": paras[h]["endIndex"], "tabId": tid},
                                      "paragraphStyle": {"namedStyleType": "HEADING_2"}, "fields": "namedStyleType"}}]
    du.batch(a.doc_id, reqs, doc)
    if stale:
        def last_confirmed(i):
            s = next((x for x in i.sections if not x.unconfirmed), None)
            return du.label(s.date) if s else "None yet"
        rows = [["Initiative", "Area", "Updater", "Last confirmed"]] + \
               [[i.name, v["area"].name, i.updater, last_confirmed(i)] for i, v in stale]
        build.add_table(a.doc_id, tid, build.anchor_index(a.doc_id, tid, count), rows, [34, 26, 18, 22])
        doc = du.read_doc(a.doc_id)
        tbl = next(e for e in du.model(doc)[0]["documentTab"]["body"]["content"]
                   if "table" in e and du.cell_text(e["table"]["tableRows"][0]["tableCells"][0]) == "Initiative")
        reqs = []
        for r, (i, _) in zip(tbl["table"]["tableRows"][1:], stale):
            c = r["tableCells"][0]
            reqs.append({"updateTextStyle": {"range": {"startIndex": c["startIndex"] + 1, "endIndex": c["endIndex"] - 1,
                                                       "tabId": tid},
                                             "textStyle": {"link": {"url": du.tab_url(a.doc_id, i.tab_id)}}, "fields": "link"}})
        du.batch(a.doc_id, reqs, doc)

    # Re-read and quote.
    doc = du.read_doc(a.doc_id)
    ov = du.model(doc)[0]
    out = []
    for e in ov["documentTab"]["body"]["content"]:
        if "paragraph" in e:
            out.append(du.para_text(e["paragraph"]).rstrip("\n"))
        elif "table" in e:
            for r in e["table"]["tableRows"]:
                out.append(" | ".join(du.cell_text(c) for c in r["tableCells"]))
    print("RE-READ OVERVIEW:\n" + "\n".join(x for x in out if x))


if __name__ == "__main__":
    main()
