"""The Feedback tab: dated entries about the daily update itself (template, drafts, overview, summary), newest first.

Written only through `du.py feedback add`. It inserts one paragraph at the top of "Feedback so far" and touches
nothing else on the tab, so comments and other people's edits survive. Entry: "Wed Nov 11, Scott: <text>" with the
date and name in bold.
"""
import re

import dudoc as du

TAB = "Feedback"
LIST_HEAD = "Feedback so far"
EMPTY = "None yet."
MAX_CHARS = 400
LINK = re.compile(r"https?://|www\.|\S+@\S+\.\w+", re.I)
SENSITIVE = re.compile(r"\b(candidates?|offers?|offered|salary|compensation|PTO|promotions?|performance reviews?)\b", re.I)


def lint(text):
    """Why this text may not go in the shared doc (empty list = fine). Same people-sensitive and link rules as the doc."""
    t = (text or "").strip()
    out = []
    if not t:
        out.append("the feedback is empty.")
    if "\n" in t:
        out.append("one line only; split it into separate entries.")
    if len(t) > MAX_CHARS:
        out.append(f"{len(t)} characters; keep it under {MAX_CHARS}.")
    if LINK.search(t):
        out.append("no links or email addresses; say what you saw in words.")
    m = SENSITIVE.search(t)
    if m:
        out.append(f"'{m.group(0)}' is people-sensitive and this doc is read by every leader; reword without it.")
    return out


def entry(label, name, text):
    return f"{label}, {name}: {' '.join(text.split())}"


def find_tab(doc):
    """(tab, tab_id) of the Feedback tab under the Update guide tab, or (None, None)."""
    for t, p in du.all_tabs(doc):
        if (p is not None and p["tabProperties"]["title"].startswith(du.GUIDE)
                and t["tabProperties"]["title"].startswith(TAB)):
            return t, t["tabProperties"]["tabId"]
    return None, None


def _paras(tab):
    return [e for e in tab["documentTab"]["body"]["content"] if "paragraph" in e]


def list_entries(tab):
    """Entry lines under 'Feedback so far', newest first (as written)."""
    paras = _paras(tab)
    k = next((i for i, e in enumerate(paras) if du.para_text(e["paragraph"]).strip() == LIST_HEAD), None)
    if k is None:
        return None
    lines = [du.para_text(e["paragraph"]).strip() for e in paras[k + 1:]]
    return [l for l in lines if l and l != EMPTY]


def plan_add(tab, tab_id, line):
    """Requests that put `line` at the top of the list, or None when that exact line is already there.
    Raises ValueError when the tab has no 'Feedback so far' heading (someone restructured it)."""
    paras = _paras(tab)
    k = next((i for i, e in enumerate(paras) if du.para_text(e["paragraph"]).strip() == LIST_HEAD), None)
    if k is None:
        raise ValueError(f"the Feedback tab has no '{LIST_HEAD}' heading.")
    if line in (list_entries(tab) or []):
        return None
    after = paras[k + 1:]
    first = after[0] if after else None
    ftxt = du.para_text(first["paragraph"]).strip() if first else ""
    n = du.utf16(line)
    reqs = []
    if first is None:
        raise ValueError(f"the Feedback tab has nothing under '{LIST_HEAD}' to anchor on.")
    at = first["startIndex"]
    if ftxt in ("", EMPTY):  # first entry: replace the placeholder text in place, keep its paragraph
        if first["endIndex"] - 1 > at:
            reqs.append({"deleteContentRange": {"range": {"startIndex": at, "endIndex": first["endIndex"] - 1, "tabId": tab_id}}})
        reqs.append({"insertText": {"location": {"index": at, "tabId": tab_id}, "text": line}})
        end = at + n + 1
    else:  # later entries: a new paragraph above the newest one
        reqs.append({"insertText": {"location": {"index": at, "tabId": tab_id}, "text": line + "\n"}})
        end = at + n + 1
    rng = {"startIndex": at, "endIndex": end, "tabId": tab_id}
    reqs.append({"updateParagraphStyle": {"range": rng, "paragraphStyle": {"namedStyleType": "NORMAL_TEXT",
                                          "spaceBelow": {"magnitude": 6, "unit": "PT"}}, "fields": "namedStyleType,spaceBelow"}})
    reqs.append({"updateTextStyle": {"range": rng, "textStyle": {}, "fields": "bold,italic,link"}})
    prefix = line.index(":") + 1
    reqs.append({"updateTextStyle": {"range": {"startIndex": at, "endIndex": at + du.utf16(line[:prefix]), "tabId": tab_id},
                                     "textStyle": {"bold": True}, "fields": "bold"}})
    return reqs


def add(doc_id, label, name, text, dry=False):
    """Write one entry. Returns ('written'|'duplicate'|'dry', line). Retries when the doc changed under us."""
    bad = lint(text)
    if bad:
        raise ValueError("; ".join(bad))
    line = entry(label, name, text)
    for attempt in range(3):
        doc = du.read_doc(doc_id)
        tab, tid = find_tab(doc)
        if tab is None:
            raise LookupError("this doc has no Feedback tab under the Update guide tab.")
        reqs = plan_add(tab, tid, line)
        if reqs is None:
            return "duplicate", line
        if dry:
            return "dry", line
        try:
            du.batch(doc_id, reqs, doc)
            break
        except RuntimeError as e:  # revision moved under us: re-read and try again, as every other write does
            if "revision" not in str(e).lower() or attempt == 2:
                raise
    tab, _ = find_tab(du.read_doc(doc_id))
    got = list_entries(tab) or []
    if line not in got:
        raise RuntimeError("the entry did not land; re-read the tab and tell the person.")
    return "written", line
