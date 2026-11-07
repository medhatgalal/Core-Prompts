"""Doc edits for the skill's less common modes, used by test-day scenarios. Writes only to E2E TEST docs.

Each function does what SKILL.md tells the agent to do for that mode, after the person said "publish".
"""
import re

import dudoc as du


def _paras(tab_id, at, lines, styles, links=()):
    """Insert lines at index `at` as paragraphs with the given named styles; links = [(line_no, word, url)]."""
    text = "\n".join(lines) + "\n"
    reqs = [{"insertText": {"location": {"index": at, "tabId": tab_id}, "text": text}}]
    pos = at
    starts = []
    for ln, st in zip(lines, styles):
        n = du.utf16(ln) + 1
        starts.append(pos)
        reqs.append({"updateParagraphStyle": {"range": {"startIndex": pos, "endIndex": pos + n, "tabId": tab_id},
                                              "paragraphStyle": {"namedStyleType": st}, "fields": "namedStyleType"}})
        reqs.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos + n, "tabId": tab_id},
                                         "textStyle": {}, "fields": "bold,italic,link"}})
        p = next((x for x in du.BOLD_PREFIXES if ln.startswith(x)), None)
        if p:
            reqs.append({"updateTextStyle": {"range": {"startIndex": pos, "endIndex": pos + du.utf16(p), "tabId": tab_id},
                                             "textStyle": {"bold": True}, "fields": "bold"}})
        pos += n
    for k, word, url in links:
        ln = lines[k]
        at = ln.index(f"({word})") + 1 if f"({word})" in ln else ln.rindex(word)  # link the cited word
        s = starts[k] + du.utf16(ln[:at])
        reqs.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + du.utf16(word), "tabId": tab_id},
                                         "textStyle": {"link": {"url": url}}, "fields": "link"}})
    return reqs


def section_lines(day, status, milestone, progress, extra=()):
    return [du.label(day, True), du.STATUSES[status], f"Next milestone: {milestone}", f"Progress: {progress}", *extra]


def relink(old_lines, new_lines, links):
    """Links are (line_no, word, url) against old_lines; re-point them at the same line in new_lines."""
    return [(new_lines.index(old_lines[k]), w, u) for k, w, u in links if old_lines[k] in new_lines]


def write_section(doc_id, tab_id, lines, links=(), between=None):
    """Daily step 6: insert at the top (under the header), or replace a section with the same date.
    `between` (tests only) runs after the read and before the write, to simulate another leader's edit."""
    doc = du.read_doc(doc_id)
    if between:
        between()
    init = next(i for i in du.model(doc)[2] if i.tab_id == tab_id)
    norm = du.normalize(lines, carry=init.sections[0] if init.sections else None)
    links, lines = relink(lines, norm, links), norm
    reqs = []
    same = next((s for s in init.sections if du.label(s.date, True) == lines[0]), None)
    if same:
        idx = init.sections.index(same)
        end = init.sections[idx + 1].heading_el["startIndex"] if idx + 1 < len(init.sections) else init.body[-1]["endIndex"] - 1
        start = same.heading_el["startIndex"]
        reqs.append({"deleteContentRange": {"range": {"startIndex": start, "endIndex": end, "tabId": tab_id}}})
        at = start
    else:
        at = init.first_heading_index()
    reqs += _paras(tab_id, at, lines + [""], ["HEADING_2"] + ["NORMAL_TEXT"] * len(lines),
                   [(k, w, u) for k, w, u in links])
    du.batch(doc_id, reqs, doc)
    # A rewrite that still carries the starting line (the doc owner correcting a starting section) keeps it.
    tidy(doc_id, tab_id, keep_first=any(x.startswith("Starting section drafted by") for x in lines))


def tidy(doc_id, tab_id, cap=10, keep_first=False):
    """After a confirmed publish: drop 'Starting section drafted by' lines, keep at most `cap` sections.
    keep_first leaves the newest section's starting line in place."""
    doc = du.read_doc(doc_id)
    init = next(i for i in du.model(doc)[2] if i.tab_id == tab_id)
    ranges = [(el["startIndex"], el["endIndex"]) for k, s in enumerate(init.sections) for t, el in s.lines
              if t.startswith("Starting section drafted by") and not (keep_first and k == 0)]
    if len(init.sections) > cap:
        ranges.append((init.sections[cap].heading_el["startIndex"], init.body[-1]["endIndex"] - 1))
    reqs = [{"deleteContentRange": {"range": {"startIndex": a, "endIndex": b, "tabId": tab_id}}}
            for a, b in sorted(ranges, reverse=True)]
    du.batch(doc_id, reqs, doc)


def find_tab(doc, tab_id):
    return next(t for t, _ in du.all_tabs(doc) if t["tabProperties"]["tabId"] == tab_id)


def similar(doc, name):
    """Add step 2: tabs whose name shares a significant word with the new one."""
    words = {w.lower() for w in re.findall(r"\w{4,}", name)} - {"composer", "agent", "agents"}
    return [t["tabProperties"]["title"] for t, _ in du.all_tabs(doc)
            if words & {w.lower() for w in re.findall(r"\w{4,}", t["tabProperties"]["title"])}]


def add_initiative(doc_id, area_tab_id, name, owner, updater, area_name, lines, links):
    doc = du.read_doc(doc_id)
    area_tab = find_tab(doc, area_tab_id)
    n_children = len(area_tab.get("childTabs", []))
    r = du.batch(doc_id, [{"addDocumentTab": {"tabProperties": {
        "title": f"{name} ({owner})", "parentTabId": area_tab_id, "index": n_children}}}], doc)
    tab_id = r["replies"][0]["addDocumentTab"]["tabProperties"]["tabId"]
    du.pageless(doc_id, [tab_id])
    norm = du.normalize(lines)
    links, lines = relink(lines, norm, links), norm
    otitle = du.overview_title(du.read_doc(doc_id))
    header = f"Owner: {owner} · Updater: {updater} · Area: {area_name} · Back to {otitle}"
    all_lines = [f"{name} ({owner})", header] + lines + [""]
    styles = ["HEADING_1", "NORMAL_TEXT", "HEADING_2"] + ["NORMAL_TEXT"] * (len(lines))
    lk = [(1, otitle, du.tab_url(doc_id, "t.0"))] + [(k + 2, w, u) for k, w, u in links]
    du.batch(doc_id, _paras(tab_id, 1, all_lines, styles, lk))
    return tab_id


def set_row(doc_id, area_tab_id, name, values, new_name=None):
    """Update one row of an area's Initiatives table (that row only); add it at the end if missing."""
    doc = du.read_doc(doc_id)
    area = next(a for a in du.model(doc)[1].values() if a.tab_id == area_tab_id)
    names = [r[0] for r in area.rows()]
    if name not in names:
        last = len(area.table["table"]["tableRows"]) - 1
        du.batch(doc_id, [{"insertTableRow": {"tableCellLocation": {
            "tableStartLocation": {"index": area.table["startIndex"], "tabId": area_tab_id},
            "rowIndex": last, "columnIndex": 0}, "insertBelow": True}}], doc)
        doc = du.read_doc(doc_id)
        area = next(a for a in du.model(doc)[1].values() if a.tab_id == area_tab_id)
        ri = len(area.table["table"]["tableRows"]) - 1
    else:
        ri = names.index(name) + 1
    row = area.table["table"]["tableRows"][ri]
    reqs = []
    for cell, val in reversed(list(zip(row["tableCells"], values))):
        s, e = cell["content"][0]["startIndex"], cell["content"][-1]["endIndex"] - 1
        if e > s:
            reqs.append({"deleteContentRange": {"range": {"startIndex": s, "endIndex": e, "tabId": area_tab_id}}})
        reqs.append({"insertText": {"location": {"index": s, "tabId": area_tab_id}, "text": val}})
        reqs.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + du.utf16(val), "tabId": area_tab_id},
                                         "textStyle": {}, "fields": "bold"}})
    du.batch(doc_id, reqs, doc)


def delete_row(doc_id, area_tab_id, name):
    doc = du.read_doc(doc_id)
    area = next(a for a in du.model(doc)[1].values() if a.tab_id == area_tab_id)
    ri = [r[0] for r in area.rows()].index(name) + 1
    du.batch(doc_id, [{"deleteTableRow": {"tableCellLocation": {
        "tableStartLocation": {"index": area.table["startIndex"], "tabId": area_tab_id},
        "rowIndex": ri, "columnIndex": 0}}}], doc)


def replace_in_para(doc_id, tab_id, old, new, startswith=None):
    """Replace text inside the first paragraph of a tab containing `old` (optionally starting with `startswith`)."""
    doc = du.read_doc(doc_id)
    t = find_tab(doc, tab_id)
    def walk(content):
        for e in content:
            if "paragraph" in e:
                yield e
            elif "table" in e:
                for r in e["table"]["tableRows"]:
                    for c in r["tableCells"]:
                        yield from walk(c["content"])
    for e in walk(t["documentTab"]["body"]["content"]):
        txt = du.para_text(e["paragraph"])
        if old in txt and (startswith is None or txt.startswith(startswith)):
            s = e["startIndex"] + du.utf16(txt[:txt.index(old)])
            du.batch(doc_id, [
                {"deleteContentRange": {"range": {"startIndex": s, "endIndex": s + du.utf16(old), "tabId": tab_id}}},
                {"insertText": {"location": {"index": s, "tabId": tab_id}, "text": new}}], doc)
            return True
    raise LookupError(f"{old!r} not found in tab {tab_id}")


def retitle(doc_id, tab_id, title):
    """Rename a tab and its HEADING_1 title line, if it has one."""
    doc = du.read_doc(doc_id)
    t = find_tab(doc, tab_id)
    old = t["tabProperties"]["title"]
    du.batch(doc_id, [{"updateDocumentTabProperties": {"tabProperties": {"tabId": tab_id, "title": title},
                                                       "fields": "title"}}], doc)
    first = next((e for e in t["documentTab"]["body"]["content"] if "paragraph" in e), None)
    if first and first["paragraph"]["paragraphStyle"].get("namedStyleType") == "HEADING_1" \
            and du.para_text(first["paragraph"]).strip() == old:
        replace_in_para(doc_id, tab_id, old, title)


def move_tab(doc_id, tab_id, parent_id, index):
    du.batch(doc_id, [{"updateDocumentTabProperties": {"tabProperties": {
        "tabId": tab_id, "parentTabId": parent_id, "index": index}, "fields": "parentTabId,index"}}])


def insert_line_before(doc_id, tab_id, before_prefix, line, in_newest=True):
    """Add one NORMAL_TEXT line in the newest section, just above its line starting with before_prefix
    (or at the end of the section if none)."""
    doc = du.read_doc(doc_id)
    init = next(i for i in du.model(doc)[2] if i.tab_id == tab_id)
    s = init.sections[0]
    target = next((el for t, el in s.lines if t.startswith(before_prefix)), None)
    at = target["startIndex"] if target else s.lines[-1][1]["endIndex"]
    du.batch(doc_id, _paras(tab_id, at, [line], ["NORMAL_TEXT"]), doc)


def archive(doc_id, title, done_text):
    """Overview step 2: move a finished tab under Archive, delete its area-table row, list it on Archive."""
    doc = du.read_doc(doc_id)
    tabs = {t["tabProperties"]["title"]: (t, p) for t, p in du.all_tabs(doc)}
    t, parent = tabs[title]
    arch = next(x for k, (x, _) in tabs.items() if k.startswith("Archive"))
    arch_id, tid = arch["tabProperties"]["tabId"], t["tabProperties"]["tabId"]
    delete_row(doc_id, parent["tabProperties"]["tabId"], du.title_parts(title)[0])
    move_tab(doc_id, tid, arch_id, len(arch.get("childTabs", [])))
    line = f"{title}, {done_text}."
    try:
        replace_in_para(doc_id, arch_id, "None yet.", line)
    except LookupError:
        at = find_tab(du.read_doc(doc_id), arch_id)["documentTab"]["body"]["content"][-1]["endIndex"] - 1
        du.batch(doc_id, _paras(arch_id, at, [line], ["NORMAL_TEXT"]))
    doc = du.read_doc(doc_id)
    p = next(e for e in find_tab(doc, arch_id)["documentTab"]["body"]["content"]
             if "paragraph" in e and du.para_text(e["paragraph"]).startswith(line))
    du.batch(doc_id, [{"updateTextStyle": {"range": {"startIndex": p["startIndex"],
                                                     "endIndex": p["startIndex"] + du.utf16(title), "tabId": arch_id},
                                           "textStyle": {"link": {"url": du.tab_url(doc_id, tid)}}, "fields": "link"}}], doc)
