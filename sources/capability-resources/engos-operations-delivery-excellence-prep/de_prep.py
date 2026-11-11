#!/usr/bin/env python3
"""Deterministic tab builder for the Delivery Excellence doc.

  python3 de_prep.py new-tab --date 2026-11-12 [--doc DOC_ID] [--dry]
  python3 de_prep.py check   --date 2026-11-12 [--doc DOC_ID]

new-tab adds a dated tab (outline only, no content) with owner name chips.
It refuses to run if a tab with that title already exists. It never posts
comments and never edits other tabs.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
import settings
CFG = settings.load()


def gws(*args, body=None):
    cmd = ["gws", *args]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"gws failed: {r.stderr[:400]}")
    return json.loads(r.stdout) if r.stdout.strip() else {}


def get_doc(doc_id):
    return gws("docs", "documents", "get", "--params",
               json.dumps({"documentId": doc_id, "includeTabsContent": True}))


def tab_titles(doc):
    return [t["tabProperties"]["title"] for t in doc.get("tabs", [])]


def u16(s):
    """Google Docs indexes count UTF-16 code units (emoji such as 🟢 count as 2)."""
    return len(s.encode("utf-16-le")) // 2


def build_lines(date):
    """Return list of (text, para_style, runs, people). runs: [(start,end,style)] in-line."""
    L = []
    def add(text="", style="NORMAL_TEXT", runs=None, people=None):
        L.append((text, style, runs or [], people or []))
    links = CFG["links"]
    readme = f"https://docs.google.com/document/d/{CFG['doc_id']}/edit?tab={CFG['readme_tab']}"
    add(f"{date} - {CFG['org_name']} Delivery Excellence", "TITLE")
    add("Agenda", runs=[(0, 6, {"link": readme})])
    add()
    add("How to fill this in", runs=[(0, 19, {"bold": True})])
    add(CFG["how_to"], runs=[(0, len(CFG["how_to"]), {"italic": True})])
    add("🟢 Going well (5★) - standout only, not business-as-usual.")
    add("🔴 Off track / at risk (1★) - what, next action, owner, by when, link.")
    add()
    for s in CFG["sections"]:
        add(s["heading"], "HEADING_2")
        if s.get("desc"):
            add(s["desc"], runs=[(0, len(s["desc"]), {"italic": True})])
        if s.get("views"):
            t, runs = "Views: ", []
            for i, v in enumerate(s["views"]):
                if i:
                    t += " and "
                runs.append((len(t), len(t) + len(v), {"link": links[v]}))
                t += v
            add(t + ".", runs=runs)
        if s.get("note"):
            add(s["note"])
        if s.get("link_line"):
            v = s["link_line"]
            add(v, runs=[(0, len(v), {"link": links[v]})])
        add()
        for g in s.get("groups", []):
            # "Label [" + chips + suffix + "]"; chips inserted at the marker offsets
            label = g["label"] + " ["
            people = []
            text = label
            for i, e in enumerate(g["owners"]):
                if i:
                    text += ", "
                people.append((len(text), e))
            text += g.get("suffix", "") + "]"
            add(text, runs=[(0, len(text), {"bold": True})], people=people)
            for ln in g.get("lines", ["🟢 Going well:", "🔴 Off track / at risk:"]):
                add(ln)
            add()
        if s.get("ops_groups"):
            for head in ("🟢 Going well", "🔴 Off track / at risk"):
                add(head)
                for g in s["ops_groups"]:
                    text = g["label"] + " ["
                    people = []
                    for i, e in enumerate(g["owners"]):
                        if i:
                            text += ", "
                        people.append((len(text), e))
                    text += "]"
                    add(text, runs=[(0, len(text), {"bold": True})], people=people)
                    add("")
            if s.get("subheading"):
                add(s["subheading"], "HEADING_3")
                add()
    return L


def new_tab(doc_id, date, dry):
    doc = get_doc(doc_id)
    if date in tab_titles(doc):
        sys.exit(f"Tab {date} already exists; nothing changed.")
    titles = tab_titles(doc)
    # put the new tab right before the newest dated tab
    idx = next((i for i, t in enumerate(titles) if t[:2] == "20"), len(titles))
    lines = build_lines(date)
    if dry:
        for t, st, runs, people in lines:
            chips = " ".join(f"@{e}" for _, e in people)
            print(f"[{st}] {t} {chips}".rstrip())
        return
    r = gws("docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id}),
            body={"requests": [{"addDocumentTab": {"tabProperties": {"title": date, "index": idx}}}]})
    tab_id = r["replies"][0]["addDocumentTab"]["tabProperties"]["tabId"]
    text = "".join(t + "\n" for t, *_ in lines)
    reqs = [{"insertText": {"location": {"index": 1, "tabId": tab_id}, "text": text}}]
    pos, chip_inserts = 1, []
    for t, st, runs, people in lines:
        end = pos + u16(t) + 1
        reqs.append({"updateParagraphStyle": {"range": {"startIndex": pos, "endIndex": end, "tabId": tab_id},
                     "paragraphStyle": {"namedStyleType": st}, "fields": "namedStyleType"}})
        for a, b, style in runs:
            a, b = u16(t[:a]), u16(t[:b])
            ts, fields = {}, []
            if "bold" in style: ts["bold"] = True; fields.append("bold")
            if "italic" in style: ts["italic"] = True; fields.append("italic")
            if "link" in style: ts["link"] = {"url": style["link"]}; fields.append("link")
            reqs.append({"updateTextStyle": {"range": {"startIndex": pos + a, "endIndex": pos + b, "tabId": tab_id},
                         "textStyle": ts, "fields": ",".join(fields)}})
        for off, email in people:
            chip_inserts.append((pos + u16(t[:off]), email))
        pos = end
    # chips last, from the end backwards so earlier indexes stay valid
    for at, email in sorted(chip_inserts, reverse=True):
        reqs.append({"insertPerson": {"location": {"index": at, "tabId": tab_id},
                     "personProperties": {"email": email}}})
    gws("docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id}), body={"requests": reqs})
    print(f"created tab {date} ({tab_id}) with {len(chip_inserts)} name chips")


def check(doc_id, date):
    doc = get_doc(doc_id)
    tab = next((t for t in doc["tabs"] if t["tabProperties"]["title"] == date), None)
    if not tab:
        sys.exit(f"FAIL: no tab {date}")
    want = build_lines(date)
    got, chips = [], []
    for c in tab["documentTab"]["body"]["content"]:
        p = c.get("paragraph")
        if not p:
            continue
        s = ""
        for e in p.get("elements", []):
            if "textRun" in e:
                s += e["textRun"]["content"]
            elif "person" in e:
                chips.append(e["person"]["personProperties"].get("email"))
        got.append((s.rstrip("\n"), p.get("paragraphStyle", {}).get("namedStyleType")))
    fails = 0
    for (t, st, _, people), (gt, gst) in zip(want, got):
        if t != gt or st != gst:
            fails += 1
            print(f"FAIL line: want [{st}] {t!r} got [{gst}] {gt!r}")
    want_chips = [e for *_, ppl in want for _, e in ppl]
    if sorted(want_chips) != sorted(chips):
        fails += 1
        print(f"FAIL chips: want {sorted(want_chips)} got {sorted(chips)}")
    print(f"{'PASS' if not fails else 'FAIL'}: {len(want)} lines, {len(chips)} chips, {fails} problems")
    sys.exit(1 if fails else 0)


def new_doc():
    """Create the Delivery Excellence doc when settings do not name one yet, and record it in settings."""
    if CFG["doc_id"]:
        sys.exit("settings already name a doc; nothing created.")
    doc = gws("docs", "documents", "create", body={"title": f"{CFG['org_name']} Delivery Excellence"})
    doc_id = doc["documentId"]
    tab = get_doc(doc_id)["tabs"][0]["tabProperties"]["tabId"]
    text = "How this doc works\n" + CFG["how_to"] + "\n"
    gws("docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": doc_id}), body={"requests": [
        {"insertText": {"location": {"index": 1, "tabId": tab}, "text": text}},
        {"updateParagraphStyle": {"range": {"startIndex": 1, "endIndex": 19, "tabId": tab},
                                  "paragraphStyle": {"namedStyleType": "HEADING_1"}, "fields": "namedStyleType"}},
        {"updateDocumentTabProperties": {"tabProperties": {"tabId": tab, "title": "README"}, "fields": "title"}}]})
    CFG.update({"doc_id": doc_id, "readme_tab": tab})
    settings.save(CFG)
    print(f"created doc {doc_id} (README tab {tab}); saved to {settings.PATH}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["new-tab", "check", "new-doc"])
    ap.add_argument("--date")
    ap.add_argument("--doc", default=CFG["doc_id"])
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if a.cmd == "new-doc":
        new_doc()
    elif not a.date:
        sys.exit(f"{a.cmd} needs --date YYYY-MM-DD")
    else:
        (new_tab(a.doc, a.date, a.dry) if a.cmd == "new-tab" else check(a.doc, a.date))
