"""Create mode and overview/area helpers for E2E TEST docs (test tooling, not part of the skill)."""
import json
import os

import dudoc as du
import modes as m

GREY = {"color": {"rgbColor": {"red": 0.45, "green": 0.45, "blue": 0.45}}}
GUIDE_LINE = "Template: see the Update guide tab."
# Overview table column shares, percent of the text width.
AREA_SHARES = [18, 9, 11, 50, 12]
DECISION_SHARES = [30, 18, 24, 16, 12]
NEXT_SHARES = [20, 66, 14]
MISSING_SHARES = [34, 14, 28, 24]
INIT_SHARES = [30, 15, 17, 38]
# Overview "How to update": one bullet per role. The text before ":" is bold; `backticked` words are monospace.
HOW_TO = [f"Leaders: by 3pm ET, run `{du.CMD}`, review, say \"publish\".",
          "Tab owners: your updater updates your tab.",
          "Doc owner: at 3pm ET, `close` the day, then `send` the summary.",
          "Changes: `add` or `discover` new initiatives; `done` or `stop` to end one. `help` lists all.",
          "Meetings: read this doc first; spend meeting time on \"decisions or help needed\".",
          GUIDE_LINE]


def text_width(tab):
    ds = tab["documentTab"]["documentStyle"]
    return ds["pageSize"]["width"]["magnitude"] - ds["marginLeft"]["magnitude"] - ds["marginRight"]["magnitude"]


def widths(tw, shares):
    w = [round(tw * s / 100) for s in shares]
    w[shares.index(max(shares))] += tw - sum(w)
    return w


def fit_tables(doc_id):
    """Skill rule: every table's columns add up to the tab's text width in the skill's split. Fixes any that drift."""
    import dudoc
    kinds = {("Area", "Owner", "Status", "Headline", "Updated"): AREA_SHARES, ("Date", "Commitment", "Status"): NEXT_SHARES,
             ("Initiative", "Owner", "Status", "Next milestone and date"): INIT_SHARES,
             ("Initiative", "Owner", "What's missing", "Since"): MISSING_SHARES,
             (dudoc.DECISIONS_COL, "Why now", "Recommend", "By", "Owner"): DECISION_SHARES}
    doc = du.read_doc(doc_id)
    fixed = []
    for tab, _ in du.all_tabs(doc):
        tid = tab["tabProperties"]["tabId"]
        reqs = []
        for e in tab["documentTab"]["body"]["content"]:
            if "table" not in e:
                continue
            kind = tuple(du.cell_text(c) for c in e["table"]["tableRows"][0]["tableCells"])
            shares = kinds.get(kind)
            if not shares:
                continue
            want = widths(text_width(tab), shares)
            have = [c.get("width", {}).get("magnitude", 0) for c in e["table"].get("tableStyle", {}).get("tableColumnProperties", [])]
            if len(have) == len(want) and all(abs(a - b) <= 1 for a, b in zip(have, want)):
                continue
            fixed.append(f"{tab['tabProperties']['title']}: {kind[0]} table {have} -> {want}")
            for i, w in enumerate(want):
                reqs.append({"updateTableColumnProperties": {"tableStartLocation": {"index": e["startIndex"], "tabId": tid},
                             "columnIndices": [i], "tableColumnProperties": {"widthType": "FIXED_WIDTH",
                             "width": {"magnitude": w, "unit": "PT"}}, "fields": "width,widthType"}})
        if reqs:
            du.batch(doc_id, reqs, doc)
            doc = du.read_doc(doc_id)
    return fixed


def add_table(doc_id, tab_id, at, rows, shares):
    """Insert a table at index `at`, fill it, bold the header row, left-align every cell, set widths from the tab's page."""
    du.batch(doc_id, [{"insertTable": {"rows": len(rows), "columns": len(rows[0]),
                                       "location": {"index": at, "tabId": tab_id}}}])
    doc = du.read_doc(doc_id)
    tab = m.find_tab(doc, tab_id)
    tbl = min((e for e in tab["documentTab"]["body"]["content"] if "table" in e and e["startIndex"] >= at - 1),
              key=lambda e: e["startIndex"])
    cells = [(c["content"][0]["startIndex"], v) for r, vals in zip(tbl["table"]["tableRows"], rows)
             for c, v in zip(r["tableCells"], vals)]
    du.batch(doc_id, [{"insertText": {"location": {"index": s, "tabId": tab_id}, "text": v}}
                      for s, v in sorted(cells, reverse=True) if v], doc)
    doc = du.read_doc(doc_id)
    tab = m.find_tab(doc, tab_id)
    tbl = min((e for e in tab["documentTab"]["body"]["content"] if "table" in e and e["startIndex"] >= at - 1),
              key=lambda e: e["startIndex"])
    reqs = [{"updateTextStyle": {"range": {"startIndex": c["startIndex"], "endIndex": c["endIndex"] - 1, "tabId": tab_id},
                                 "textStyle": {"bold": True}, "fields": "bold"}}
            for c in tbl["table"]["tableRows"][0]["tableCells"] if c["endIndex"] - 1 > c["startIndex"]]
    reqs += [{"updateParagraphStyle": {"range": {"startIndex": c["startIndex"], "endIndex": c["endIndex"] - 1, "tabId": tab_id},
                                       "paragraphStyle": {"alignment": "START"}, "fields": "alignment"}}
             for r in tbl["table"]["tableRows"] for c in r["tableCells"]]
    for i, w in enumerate(widths(text_width(tab), shares)):
        reqs.append({"updateTableColumnProperties": {"tableStartLocation": {"index": tbl["startIndex"], "tabId": tab_id},
                     "columnIndices": [i], "tableColumnProperties": {"widthType": "FIXED_WIDTH",
                     "width": {"magnitude": w, "unit": "PT"}}, "fields": "width,widthType"}})
    du.batch(doc_id, reqs, doc)


def anchor_index(doc_id, tab_id, after_heading):
    """Start index of the empty paragraph right after a heading (where a table goes)."""
    tab = m.find_tab(du.read_doc(doc_id), tab_id)
    paras = [e for e in tab["documentTab"]["body"]["content"] if "paragraph" in e]
    i = next(k for k, e in enumerate(paras) if du.para_text(e["paragraph"]).strip() == after_heading)
    return paras[i + 1]["startIndex"]


def create(title, org, owner, reader, structure, day):
    """Create mode step 4. structure: [(area, area_owner, [(name, owner, updater, status, milestone, progress, word, url, extra)])]"""
    # Check every link before anything is created, so a bad link refuses cleanly and leaves no half-built doc.
    missing = []
    for _, _, items in structure:
        for n, o, u, s, ms, prog, word, url, extra in items:
            pairs = [(word, url)] if url else [tuple(p) for p in (word or [])]
            for w, _u in pairs:
                if not prog or w not in prog:
                    missing.append(f"{n}: link word {w!r} is not in its Progress text")
    if missing:
        raise SystemExit("REFUSED: nothing created. Put each link word in its Progress line, for example "
                         "\"(Jira COM-1168)\", then run setup again:\n  " + "\n  ".join(missing))
    if os.environ.get("DU_TEST") and not title.startswith(du.TEST_TITLE_PREFIX):
        raise SystemExit(f"REFUSED (DU_TEST): title {title!r} does not start with {du.TEST_TITLE_PREFIX!r}. Nothing created.")
    doc = du.gws("docs", "documents", "create", body={"title": title})
    did = doc["documentId"]
    ov = "t.0"
    reqs = [{"updateDocumentTabProperties": {"tabProperties": {"tabId": ov, "title": f"{org} ({owner})"}, "fields": "title"}}]
    for k, (area, aown, _) in enumerate(structure):
        reqs.append({"addDocumentTab": {"tabProperties": {"title": f"{area} ({aown})", "index": k + 1}}})
    reqs.append({"addDocumentTab": {"tabProperties": {"title": f"Archive ({owner})", "index": len(structure) + 1}}})
    r = du.batch(did, reqs)
    ids = [x["addDocumentTab"]["tabProperties"]["tabId"] for x in r["replies"] if "addDocumentTab" in x]
    area_ids, archive_id = ids[:-1], ids[-1]
    otitle = f"{org} Daily Updates"
    back = (1, otitle, du.tab_url(did, ov))
    inits = {}
    for (area, aown, items), aid in zip(structure, area_ids):
        r = du.batch(did, [{"addDocumentTab": {"tabProperties": {"title": f"{n} ({o})", "parentTabId": aid, "index": k}}}
                           for k, (n, o, *_) in enumerate(items)])
        for (n, *_), x in zip(items, r["replies"]):
            inits[n] = x["addDocumentTab"]["tabProperties"]["tabId"]
        # area tab
        worst = du.worst(it[3] for it in items)
        nxt = "; ".join(f"{n}: {ms}" for n, o, u, s, ms, *_ in items[:2])
        hl = f"{du.STATUSES[worst]} · Next up: {nxt}. ({du.label(day)})"
        lines = [f"{area} ({aown})", f"Owner: {aown} · Back to {otitle}", "Headline", hl,
                 "Initiatives", "", "Done", "No initiatives finished yet."]
        st = ["HEADING_1", "NORMAL_TEXT", "HEADING_2", "NORMAL_TEXT", "HEADING_2", "NORMAL_TEXT", "HEADING_2", "NORMAL_TEXT"]
        du.batch(did, m._paras(aid, 1, lines, st, [back]))
        add_table(did, aid, anchor_index(did, aid, "Initiatives"),
                  [["Initiative", "Owner", "Status", "Next milestone and date"]] +
                  [[n, o, du.STATUSES[s], ms] for n, o, u, s, ms, *_ in items], [30, 15, 17, 38])
        # initiative tabs
        for n, o, u, s, ms, prog, word, url, extra in items:
            extra = [x for x in extra if not x.startswith("Starting section drafted by")]  # added once, below
            sec = m.section_lines(day, s, ms, prog, list(extra) +
                                  [f"Starting section drafted by {owner}'s agent. {u} confirms or corrects it on their first update."])
            if not prog:  # no source: no Progress line
                sec = [x for x in sec if not x.startswith("Progress:")]
            sec = du.normalize(sec)
            lines = [f"{n} ({o})", f"Owner: {o} · Updater: {u} · Area: {area} · Back to {otitle}"] + sec + [""]
            st = ["HEADING_1", "NORMAL_TEXT", "HEADING_2"] + ["NORMAL_TEXT"] * (len(sec))
            links = [(1, otitle, du.tab_url(did, ov))]
            # `word` is either one link word (with `url`) or a list of [word, url] pairs (url None)
            pairs = [(word, url)] if url else [tuple(p) for p in (word or [])]
            if prog:
                pk = next(k for k, x in enumerate(lines) if x.startswith("Progress:"))
                links += [(pk, w, u) for w, u in pairs]
            du.batch(did, m._paras(inits[n], 1, lines, st, links))
    # archive
    du.batch(did, m._paras(archive_id, 1, [f"Archive ({owner})", f"Owner: {owner} · Back to {otitle}",
                                           "Finished initiatives move here.", "None yet."],
                           ["HEADING_1", "NORMAL_TEXT", "NORMAL_TEXT", "NORMAL_TEXT"], [back]))
    # overview: title and owner line here; overview.rebuild writes everything below them
    lines = [f"{org} Daily Updates", f"Owner: {owner} · Readers: {reader} and all leaders · As of {du.label(day, True)}, 4:00 PM ET"]
    du.batch(did, m._paras(ov, 1, lines, ["TITLE", "NORMAL_TEXT"]))
    du.pageless(did, [t["tabProperties"]["tabId"] for t, _ in du.all_tabs(du.read_doc(did))])
    import guide
    import overview
    guide.add_guide(did, owner)
    overview.rebuild(did, day, "4:00 PM ET")
    du.repair_headings(did)
    return did


def set_headline(doc_id, area_title, text):
    """Replace the area tab's headline paragraph (area owner only)."""
    import re
    # Format: "<status> · <sentences> (<date>)". Fix a "." or "," written where the "·" belongs.
    text = re.sub(r"^((?:🔴 Red|🟡 At risk|🟢 On track|⚪ Paused))\s*[.,:;]?\s+(?!·)", r"\1 · ", text)
    doc = du.read_doc(doc_id)
    area = du.model(doc)[1][area_title]
    paras = [e for e in area.body if "paragraph" in e]
    i = next(k for k, e in enumerate(paras) if du.para_text(e["paragraph"]).strip() == "Headline")
    p = paras[i + 1]
    du.batch(doc_id, [{"deleteContentRange": {"range": {"startIndex": p["startIndex"], "endIndex": p["endIndex"] - 1, "tabId": area.tab_id}}},
                      {"insertText": {"location": {"index": p["startIndex"], "tabId": area.tab_id}, "text": text}}], doc)


def set_decisions(doc_id, reader, rows, links=()):
    """Overview 'Exec leadership: decisions or help needed' table, added above Next 2 weeks when there are any.
    `reader` is kept for the command line; the heading no longer names a reader."""
    doc = du.read_doc(doc_id)
    ov = du.model(doc)[0]
    head = du.DECISIONS_HEAD
    paras = [e for e in ov["documentTab"]["body"]["content"] if "paragraph" in e]
    if not any(du.para_text(e["paragraph"]).strip() == head for e in paras):
        nx = next(e for e in paras if du.para_text(e["paragraph"]).strip() in (du.NEXT_HEAD, "How to update"))
        du.batch(doc_id, m._paras("t.0", nx["startIndex"], [head, ""], ["HEADING_2", "NORMAL_TEXT"]), doc)
        add_table(doc_id, "t.0", anchor_index(doc_id, "t.0", head),
                  [[du.DECISIONS_COL, "Why now", "Recommend", "By", "Owner"]] + rows, DECISION_SHARES)
    # Link each Decision cell to the thing being decided.
    doc = du.read_doc(doc_id)
    ov = du.model(doc)[0]
    tbl = next(e for e in ov["documentTab"]["body"]["content"]
               if "table" in e and du.cell_text(e["table"]["tableRows"][0]["tableCells"][0]) == du.DECISIONS_COL)
    reqs = []
    for r, url in zip(tbl["table"]["tableRows"][1:], links):
        if not url:
            continue
        c = r["tableCells"][0]
        reqs.append({"updateTextStyle": {"range": {"startIndex": c["startIndex"] + 1, "endIndex": c["endIndex"] - 1,
                                                   "tabId": "t.0"},
                                         "textStyle": {"link": {"url": url}}, "fields": "link"}})
    du.batch(doc_id, reqs, doc)


def style_how_to(doc_id, tab_id):
    """Make the How to update lines bullets, bold each label, and set each command in a monospace font."""
    doc = du.read_doc(doc_id)
    paras = {du.para_text(e["paragraph"]).strip(): e for e in m.find_tab(doc, tab_id)["documentTab"]["body"]["content"]
             if "paragraph" in e}
    found = [(paras[x.replace("`", "")], x) for x in HOW_TO]
    reqs = [{"createParagraphBullets": {"range": {"startIndex": found[0][0]["startIndex"],
                                                  "endIndex": found[-1][0]["endIndex"] - 1, "tabId": tab_id},
                                        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}}]
    for p, marked in found:
        pos = p["startIndex"]
        reqs.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos + du.utf16(marked[:marked.index(":") + 1]),
                                                   "tabId": tab_id}, "textStyle": {"bold": True}, "fields": "bold"}})
        for k, part in enumerate(marked.split("`")):
            if k % 2:  # inside backticks
                reqs.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos + du.utf16(part), "tabId": tab_id},
                                                 "textStyle": {"weightedFontFamily": {"fontFamily": "Roboto Mono"}},
                                                 "fields": "weightedFontFamily"}})
            pos += du.utf16(part)
    du.batch(doc_id, reqs, doc)


def link_guide_line(doc_id, guide_tab_id):
    """Put the 'Template' line under How to update (add it if missing) and link 'Update guide'."""
    doc = du.read_doc(doc_id)
    ov = du.model(doc)[0]
    paras = [e for e in ov["documentTab"]["body"]["content"] if "paragraph" in e]
    line = GUIDE_LINE
    p = next((e for e in paras if du.para_text(e["paragraph"]).strip() == line), None)
    if p is None:
        sk = next(e for e in paras if du.para_text(e["paragraph"]).strip() == "Status key")
        du.batch(doc_id, m._paras("t.0", sk["startIndex"], [line], ["NORMAL_TEXT"]), doc)
        doc = du.read_doc(doc_id)
        paras = [e for e in du.model(doc)[0]["documentTab"]["body"]["content"] if "paragraph" in e]
        p = next(e for e in paras if du.para_text(e["paragraph"]).strip() == line)
    s = p["startIndex"] + du.utf16(line[:line.index("Update guide")])
    du.batch(doc_id, [{"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + du.utf16("Update guide"), "tabId": "t.0"},
                                           "textStyle": {"link": {"url": du.tab_url(doc_id, guide_tab_id)}}, "fields": "link"}}], doc)
