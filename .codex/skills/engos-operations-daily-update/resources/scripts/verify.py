"""Read an E2E TEST doc back and check it against the skill's rules. Read only.

  python3 verify.py DOC_ID 2026-11-06 --since 2026-11-03 --started 2026-11-01T19:20:00Z

--since   per-section rules (status, milestone, weekday, links, raw URLs, agent notes) are checked on
          sections dated on or after this day. Older sections are history written under older rules.
--started isolation: the protected docs must not have been modified after this time.
Exit code 0 only if every check passes.
"""
import argparse
import os
import datetime as dt
import json
import re
import sys

import dudoc as du

# Test isolation: the only address a test doc may be shared with or tag. DU_TEST_EMAIL, else the signed-in gws user.
def _tester():
    if os.environ.get("DU_TEST_EMAIL"):
        return os.environ["DU_TEST_EMAIL"]
    try:
        return du.gws("gmail", "users", "getProfile", "--params", json.dumps({"userId": "me"})).get("emailAddress", "")
    except Exception:
        return ""
results = []
# Column shares from SKILL.md "Docs API notes", keyed by the header row.
SHARES = {("Area", "Owner", "Status", "Headline", "Updated"): [21, 11, 15, 38, 15],
          ("Initiative", "Owner", "Status", "Next milestone and date"): [30, 15, 17, 38],
          ("Decision", "Why now", "Recommend", "By", "Owner"): [24, 22, 24, 14, 16],
          ("Initiative", "Area", "Updater", "Last confirmed"): [34, 26, 18, 22]}


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


# Rule 6: link only what anyone in the company can open. A line from private sources ends with one of these labels.
PRIVATE_LABEL = r"\((?:email|chat|meeting notes)\)\.?$"
DRIVE_ID = re.compile(r"(?:docs\.google\.com/(?:document|spreadsheets|presentation|forms)/d/|drive\.google\.com/"
                      r"(?:file/d/|open\?id=|drive/folders/))([\w-]{20,})")
_sharing = {}


def links_in(content):
    """(word, url) for every linked run in these body elements, tables included."""
    for e in content:
        if "paragraph" in e:
            for r in e["paragraph"]["elements"]:
                url = r.get("textRun", {}).get("textStyle", {}).get("link", {}).get("url")
                if url:
                    yield r["textRun"]["content"].strip(), url
        for row in e.get("table", {}).get("tableRows", []):
            for c in row["tableCells"]:
                yield from links_in(c["content"])


def link_problem(url, own_id):
    """Why this link is not one anyone in the company can open, or None. Reads Drive sharing only."""
    if re.search(r"//(?:mail|chat)\.google\.com/", url):
        return "points to Gmail or Chat"
    m = DRIVE_ID.search(url)
    if not m or m.group(1) == own_id:  # not a Drive file, or a tab of the status doc itself
        return None
    fid = m.group(1)
    if fid not in _sharing:
        q = {"fileId": fid, "fields": "name,permissions(type,role)", "supportsAllDrives": True}
        try:
            f = du.gws("drive", "files", "get", "--params", json.dumps(q))
            perms = f.get("permissions")
            if perms is None:  # Drive leaves this out for shared-drive files; ask the permissions list instead
                q["fields"] = "permissions(type,role)"
                perms = du.gws("drive", "permissions", "list", "--params", json.dumps(q)).get("permissions", [])
            if "Notes by Gemini" in f.get("name", ""):
                _sharing[fid] = "is Gemini meeting notes"
            elif any(p.get("type") in ("domain", "anyone") for p in perms):
                _sharing[fid] = None
            else:
                _sharing[fid] = "Drive file not shared to the domain or anyone with the link"
        except RuntimeError:
            _sharing[fid] = "Drive sharing could not be read"
    return _sharing[fid]


def check_links(tag, content, own_id):
    for word, url in links_in(content):
        why = link_problem(url, own_id)
        check(f"{tag}: link '{word[:30]}' opens for anyone in the company", why is None, why)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc_id")
    ap.add_argument("date")
    ap.add_argument("--since", required=True)
    ap.add_argument("--started", required=True)
    a = ap.parse_args()
    today, since = dt.date.fromisoformat(a.date), dt.date.fromisoformat(a.since)

    doc = du.read_doc(a.doc_id)
    ov, areas, inits = du.model(doc)

    # ---- initiative tabs ----
    for i in inits:
        dates = [s.date for s in i.sections]
        check(f"{i.name}: one section per date", len(dates) == len(set(dates)), dates)
        check(f"{i.name}: newest first", dates == sorted(dates, reverse=True))
        check(f"{i.name}: has a section for {du.label(today)}", dates and dates[0] == today)
        for s in i.sections:
            if s.date < since:
                continue  # sections written before the rules under test are history, not checked
            tag = f"{i.name} {du.label(s.date)}"
            check(f"{tag}: status line", s.status is not None)
            texts = [t for t, _ in s.lines]
            if not s.no_change:
                ms = s.milestone
                check(f"{tag}: milestone dated or 'No date set yet'", du.milestone_dated(ms), ms)
                if ms and "No date set yet" in ms:
                    check(f"{tag}: no date -> not green", s.status != "🟢", s.status)
            for t in texts:
                for m, d, ok in du.dates_in(t):
                    check(f"{tag}: weekday matches '{m}'", ok)
            check(f"{tag}: no raw URLs", not any(re.search(r"https?://", t) for t in texts))
            check(f"{tag}: no agent notes", not any(re.match(r"Note \(agent", t) for t in texts))
            check(f"{tag}: at most one 'Starting section drafted by' line",
                  sum(t.startswith("Starting section drafted by") for t in texts) <= 1)
            for t, el in s.lines:
                if t.startswith(("Progress:", "Blocked on:")) and not re.search(r"No update from|No change since|Blocked on: None\.|Moved from .+ on |\(from [A-Z][\w .'-]*\)\.?$", t):
                    has = any(r.get("textRun", {}).get("textStyle", {}).get("link") for r in el["paragraph"]["elements"])
                    check(f"{tag}: '{t[:30]}...' has a link or a private-source label", has or re.search(PRIVATE_LABEL, t))
            check_links(tag, [el for _, el in s.lines], a.doc_id)
            if s.unconfirmed:
                check(f"{tag}: Unconfirmed line is last", texts[-1].startswith("Unconfirmed:"))
            conf_el = next((el for t, el in s.lines if t.startswith("Confidence:")), None)
            check(f"{tag}: Confidence is a dropdown chip",
                  conf_el and any(r.get("dropdown", {}).get("dropdownProperties", {}).get("dropdownDefinitionId") == du.CONF_DEF
                                  for r in conf_el["paragraph"]["elements"]))
            conf = s.line("Confidence:")
            check(f"{tag}: Confidence line", conf and conf[len("Confidence: "):] in du.CONFIDENCE, conf)
            check(f"{tag}: Blocked on line", s.line("Blocked on:"))
            check(f"{tag}: Green when only when not green", bool(s.line("Green when:")) == (s.status != "🟢"))
            order = [p for p in du.PREFIXES[:5] if s.line(p)]
            seen = [p for t, _ in s.lines for p in du.PREFIXES[:5] if t.startswith(p)]
            check(f"{tag}: lines in skill order", seen == order, seen)
            for t, el in s.lines:
                p = next((x for x in du.PREFIXES if t.startswith(x)), None)
                if p:
                    first = el["paragraph"]["elements"][0]
                    tr = first.get("textRun", {})
                    ok = tr.get("textStyle", {}).get("bold") and tr.get("content", "").startswith(p) \
                        and len(tr["content"].rstrip("\n")) <= du.utf16(p) + 1
                    check(f"{tag}: '{p}' prefix is bold (and only the prefix)", ok, tr.get("content", "")[:40])

    # ---- headers match the tree (owner from title, area from parent, an updater named) ----
    for i in inits:
        h = i.header or ""
        check(f"{i.title}: header Owner matches title", h.startswith(f"Owner: {i.owner} ·"), h[:60])
        check(f"{i.title}: header names an Updater", "Updater: " in h)
        check(f"{i.title}: header Area matches parent tab", f"Area: {i.area_name} ·" in h, h)
        for s in i.sections[:1]:
            for t, _ in s.lines:
                m = re.match(r"Added by (.+) for (.+)\.$", t)
                if m:
                    check(f"{i.title}: 'Added by' names the owner", m.group(2) == i.owner, t)
    for ar in areas.values():
        first = next((du.para_text(e["paragraph"]).strip() for e in ar.body if "paragraph" in e), "")
        check(f"{ar.title}: title line matches tab name", first == ar.title, first)
        check(f"{ar.title}: header Owner matches", any(du.para_text(e["paragraph"]).startswith(f"Owner: {ar.owner} ·")
                                                     for e in ar.body if "paragraph" in e))
        mine = {i.name for i in inits if i.area_title == ar.title}
        for r in ar.rows():
            check(f"{ar.name} table: row '{r[0]}' has a tab in this area", r[0] in mine)
    archived = [c["tabProperties"]["title"] for t, _ in du.all_tabs(doc) if t["tabProperties"]["title"].startswith("Archive")
                for c in t.get("childTabs", [])]
    for title in archived:
        name = du.title_parts(title)[0]
        check(f"Archive: {title} not still listed in an area table", all(name not in [r[0] for r in a.rows()] for a in areas.values()))

    archive = next((t for t, p in du.all_tabs(doc) if p is None and t["tabProperties"]["title"].startswith("Archive")), None)
    archived = [du.Initiative(c, archive) for c in archive.get("childTabs", [])] if archive else []
    for i in inits + archived:
        first = next((e for e in i.body if "paragraph" in e), None)
        check(f"{i.title}: HEADING_1 title matches tab name",
              first and first["paragraph"]["paragraphStyle"].get("namedStyleType") == "HEADING_1"
              and du.para_text(first["paragraph"]).strip() == i.title)
        for s in i.sections:
            if s.date >= since and s.status in ("🟡", "🔴"):
                check(f"{i.name} {du.label(s.date)}: not green has a Green when line", s.line("Green when:"))
        check(f"{i.title}: at most 10 sections", len(i.sections) <= 10, len(i.sections))

    # ---- every date line is a real heading (a plain-text date silently merges two days) ----
    for t, _ in du.all_tabs(doc):
        for e in t["documentTab"]["body"]["content"]:
            if "paragraph" in e:
                txt = du.para_text(e["paragraph"]).strip()
                if du.HEADING_RE.match(txt):
                    check(f"{t['tabProperties']['title']}: '{txt}' is a HEADING_2",
                          e["paragraph"]["paragraphStyle"].get("namedStyleType") == "HEADING_2")

    # ---- area tables: every initiative has a row that matches its newest section ----
    for ar in areas.values():
        mine = [i for i in inits if i.area_title == ar.title]
        rows = {r[0]: r for r in ar.rows()}
        for i in mine:
            r = rows.get(i.name)
            check(f"{ar.name} table: row for {i.name}", r is not None)
            if r:
                st, ms_sec = i.newest("status"), i.newest("milestone")
                check(f"{ar.name} table: {i.name} status matches tab", r[2][:1] == (st.status if st else None), (r[2], st and st.status))
                if ms_sec:
                    want = du.milestone_date(ms_sec.milestone)
                    got = du.milestone_date(r[3])
                    check(f"{ar.name} table: {i.name} milestone date matches tab",
                          want == got or ("No date set yet" in r[3] and "No date set yet" in ms_sec.milestone), (r[3], ms_sec.milestone))
                if len(r) == 4:
                    check(f"{ar.name} table: {i.name} owner", r[1] == i.owner, r[1])
        for _, r in rows.items():
            for m, d, ok in du.dates_in(" ".join(r)):
                check(f"{ar.name} table: weekday matches '{m}'", ok)

    # ---- overview: Area health and Not updated today ----
    body = ov["documentTab"]["body"]["content"]
    check_links("overview", body, a.doc_id)
    for ar in areas.values():
        check_links(ar.title, ar.body, a.doc_id)
    table = next(e for e in body if "table" in e and du.cell_text(e["table"]["tableRows"][0]["tableCells"][0]) == "Area")
    health = {du.cell_text(r["tableCells"][0]): [du.cell_text(c) for c in r["tableCells"]] for r in table["table"]["tableRows"][1:]}
    full = "\n".join(du.para_text(e["paragraph"]) for e in body if "paragraph" in e)
    full += "\n".join(" ".join(v) for v in health.values())
    check("overview: no 'tabs updated since' wording", "tabs updated since" not in full)
    check(f"overview: As of {du.label(today)}", f"As of {du.label(today, True)}" in full)
    stale_areas = 0
    nut_tbl = next((e for e in body if "table" in e and tuple(du.cell_text(c) for c in e["table"]["tableRows"][0]["tableCells"])
                    == ("Initiative", "Area", "Updater", "Last confirmed")), None)
    nut = {du.cell_text(r["tableCells"][0]): [du.cell_text(c) for c in r["tableCells"]]
           for r in nut_tbl["table"]["tableRows"][1:]} if nut_tbl else {}
    for r in (nut_tbl["table"]["tableRows"][1:] if nut_tbl else []):
        has = any(x.get("textRun", {}).get("textStyle", {}).get("link")
                  for p in r["tableCells"][0]["content"] if "paragraph" in p for x in p["paragraph"]["elements"])
        check(f"overview: Not updated '{du.cell_text(r['tableCells'][0])}' links to its tab", has)
    for ar in areas.values():
        mine = [i for i in inits if i.area_title == ar.title]
        row = health.get(ar.name)
        check(f"overview: Area health row for {ar.name}", row is not None)
        if not row:
            continue
        want = du.worst(i.newest("status").status for i in mine if i.newest("status"))
        check(f"overview: {ar.name} status from its tabs", row[2][:1] == want, (row[2], want))
        hl_dates = du.dates_in(ar.headline or "")
        hl_date = hl_dates[-1][1] if hl_dates else None
        confirmed = [s.date for i in mine for s in i.sections if not s.unconfirmed]
        newest = max(confirmed + ([hl_date] if hl_date else []), default=None)
        hl_status = (ar.headline or "")[:1]
        flagged = (hl_date and newest and hl_date < newest) or (hl_status in du.STATUSES and hl_status != want)
        if flagged:
            check(f"overview: {ar.name} flagged headline wording",
                  row[3].endswith(f"(headline from {du.label(hl_date)}; out of date with its tabs)"), row[3][-70:])
        elif hl_date and hl_date < today:
            check(f"overview: {ar.name} headline marked not updated today",
                  row[3].endswith(f"(headline from {du.label(hl_date)}; not updated today)"), row[3][-70:])
        else:
            # The agent may also flag a headline whose text contradicts its tabs (a stopped milestone it still
            # names); dates and colour cannot show that, so the flagged wording is accepted here too.
            check(f"overview: {ar.name} unflagged headline ends with its date",
                  hl_date is None or row[3].endswith(f"({du.label(hl_date)})")
                  or row[3].endswith(f"(headline from {du.label(hl_date)}; out of date with its tabs)"), row[3][-40:])
        for m, d, ok in du.dates_in(" ".join(row)):
            check(f"overview: weekday matches '{m}' ({ar.name})", ok)
        if any(not i.sections or i.sections[0].date < today or i.sections[0].unconfirmed for i in mine):
            stale_areas += 1
            for i in mine:
                if not i.sections or i.sections[0].date < today or i.sections[0].unconfirmed:
                    check(f"overview: Not updated today lists {i.name}", i.name in nut, sorted(nut))
                    if i.name in nut:
                        lc = next((s for s in i.sections if not s.unconfirmed), None)
                        check(f"overview: {i.name} last confirmed", nut[i.name][3] == (du.label(lc.date) if lc else "None yet"), nut[i.name])
                        check(f"overview: {i.name} updater", nut[i.name][2] == i.updater, nut[i.name])
    tab_by_id = {t["tabProperties"]["tabId"]: du.title_parts(t["tabProperties"]["title"])[0] for t, _ in du.all_tabs(doc)}
    for e in body:
        if "paragraph" not in e:
            continue
        for r in e["paragraph"]["elements"]:
            tr = r.get("textRun", {})
            url = tr.get("textStyle", {}).get("link", {}).get("url", "")
            if "?tab=" in url:
                want = tab_by_id.get(url.split("?tab=")[1])
                check(f"overview: link on '{tr['content'].strip()}' points to that tab", tr["content"].strip() == want,
                      f"points to {want}")
    check("overview: stale count", f"{stale_areas} of {len(areas)} areas not fully updated today" in full)
    paras = [du.para_text(e["paragraph"]).strip() for e in body if "paragraph" in e]
    heads = [p for p in paras if p in ("Area health", "Not updated today", "How to update", "Status key")]
    styles = {du.para_text(e["paragraph"]).strip(): e["paragraph"]["paragraphStyle"].get("namedStyleType") for e in body if "paragraph" in e}
    for hname in ("In 30 seconds", "Area health", "Not updated today", "How to update", "Status key"):
        check(f"overview: '{hname}' is a heading", styles.get(hname) == "HEADING_2", styles.get(hname))
    check("overview: order Area health, Not updated today, How to update, Status key",
          heads == ["Area health", "Not updated today", "How to update", "Status key"], heads)

    for t, _ in du.all_tabs(doc):
        mode = t["documentTab"].get("documentStyle", {}).get("documentFormat", {}).get("documentMode")
        check(f"{t['tabProperties']['title']}: pageless", mode == "PAGELESS", mode)

    guide = [t for t, p in du.all_tabs(doc) if p is None and t["tabProperties"]["title"].startswith(du.GUIDE)]
    check("Update guide tab exists at the top level", len(guide) == 1)
    if guide:
        gtext = "\n".join(du.para_text(e["paragraph"]) for e in guide[0]["documentTab"]["body"]["content"] if "paragraph" in e)
        for must in ("Template", "Next milestone:", "Confidence:", "Progress:", "Blocked on:", "Green when:",
                     "Best practices", "Sources"):
            check(f"Update guide has '{must}'", must in gtext)
        ov_txt = "\n".join(du.para_text(e["paragraph"]) for e in ov["documentTab"]["body"]["content"] if "paragraph" in e)
        check("overview How to update points to the Update guide", "Update guide" in ov_txt)

    # ---- tables fit the page ----
    for t, _ in du.all_tabs(doc):
        ds = t["documentTab"].get("documentStyle", {})
        text_w = ds["pageSize"]["width"]["magnitude"] - ds["marginLeft"]["magnitude"] - ds["marginRight"]["magnitude"]
        for e in t["documentTab"]["body"]["content"]:
            if "table" in e:
                cols = [c.get("width", {}).get("magnitude", 0) for c in e["table"].get("tableStyle", {}).get("tableColumnProperties", [])]
                kind = tuple(du.cell_text(c) for c in e["table"]["tableRows"][0]["tableCells"])
                shares = SHARES.get(kind)
                if shares and len(cols) == len(shares):
                    want = [round(text_w * x / 100) for x in shares]
                    want[shares.index(max(shares))] += text_w - sum(want)
                    check(f"{t['tabProperties']['title']}: {kind} table widths {cols} match skill split {want}",
                          all(abs(a - b) <= 1 for a, b in zip(cols, want)))
                else:
                    check(f"{t['tabProperties']['title']}: {kind} table has the expected column count", False, cols)

    # ---- isolation (test runs only) ----
    if not os.environ.get("DU_TEST"):
        return finish()
    for did, name in du.PROTECTED.items():
        f = du.gws("drive", "files", "get", "--params", json.dumps({"fileId": did, "fields": "modifiedTime", "supportsAllDrives": True}))
        check(f"isolation: {name} not modified since start", f["modifiedTime"] < a.started, f["modifiedTime"])
    perms = du.gws("drive", "permissions", "list", "--params", json.dumps({"fileId": a.doc_id, "fields": "permissions(emailAddress,role,type)", "supportsAllDrives": True}))
    tester = _tester()
    check("isolation: tester address known (DU_TEST_EMAIL or gws profile)", bool(tester))
    others = [p for p in perms.get("permissions", []) if p.get("emailAddress") != tester]
    check("isolation: test doc shared with the tester only", not others, others)
    com = du.gws("drive", "comments", "list", "--params", json.dumps({"fileId": a.doc_id, "fields": "comments(content,createdTime)", "pageSize": 100}))
    tagged = {m for c in com.get("comments", []) for m in re.findall(r"\+([\w.]+@[\w.]+)", c.get("content", ""))}
    check("isolation: comments tag only the tester", tagged <= {tester}, tagged)

    return finish()


def finish():
    fails = [r for r in results if not r[1]]
    for n, ok, d in results:
        if not ok:
            print(f"FAIL {n}  {d}")
    print(f"\n{len(results) - len(fails)} of {len(results)} checks passed")
    print("(One set of checks runs per tab and per section written since --since, so the total grows as the doc does.)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
