"""Run the skill's Sweep steps 1-3 on an E2E TEST doc, the way the doc owner's agent would.

  python3 sweep.py DOC_ID 2026-11-06 --owner Scott            # review only (step 3), writes nothing
  python3 sweep.py DOC_ID 2026-11-06 --owner Scott --publish \
      --decide "Composer Evals=red" --decide "Team Restructure=done"

Step 4 (tag comments) runs only with --tag, and tags only people who already have access to the doc.
"""
import argparse
import datetime as dt
import json

import dudoc as du


def draft(init, today, owner, decisions):
    """Return (lines, note) for an Unconfirmed section, or None if today already has a section."""
    same = next((s for s in init.sections if s.date == today), None)
    if same and not any(t.startswith("Starting section drafted by") for t, _ in same.lines):
        return None
    prog = (init.sections[0].line("Progress:") or "") if init.sections else ""
    if prog.startswith(("Progress: Done ", "Progress: Stopped ")):
        return None  # finished or stopped: waiting for Archive
    st_sec, ms_sec = init.newest("status"), init.newest("milestone")
    notes = []
    if st_sec is None:
        status, ms = "🟡", "No date set yet"
        notes.append("no earlier section: 🟡, No date set yet")
    else:
        status = st_sec.status
        ms = ms_sec.milestone if ms_sec else "No date set yet"
        ms = ms.replace("Not set yet", "No date set yet")
        if not du.milestone_dated(ms):
            ms += ", No date set yet"
            notes.append("carried milestone had no date")
        due = du.milestone_date(ms)
        if due and due < today and ", done " not in ms:
            choice = decisions.get(init.name)
            choice = choice if choice in ("red", "done") else None
            notes.append(f"PASSED: milestone due {du.label(due)}; doc owner chose {choice or 'NOTHING YET'}")
            if choice == "red":
                status = "🔴"
            elif choice == "done":
                ms = f"{ms}, done {du.label(today)}."
    ms_line = f"Next milestone: {ms}"
    find = lambda p: next((t for s in init.sections for t, _ in s.lines if t.startswith(p)), None)
    lines = [du.label(today, year=True), du.STATUSES[status], ms_line,
             find("Blocked on:") or "Blocked on: None."]
    if status != "🟢":
        lines.append(find("Green when:") or f"Green when: {init.updater} sets this when they confirm.")
    lines.append(f"Unconfirmed: no update from {init.updater} by 3pm ET.")
    return lines, notes


def section_requests(init, lines):
    import modes
    at = init.first_heading_index()
    return modes._paras(init.tab_id, at, lines + [""], ["HEADING_2"] + ["NORMAL_TEXT"] * len(lines))


def row_values(init, lines):
    ms = lines[2][len("Next milestone: "):]
    return [init.name, init.owner, lines[1], ms]


def set_cells(area, row_idx, values):
    """Requests replacing each cell's text in one table row, highest index first."""
    row = area.table["table"]["tableRows"][row_idx]
    values = du.row_cells(values, len(row["tableCells"]))
    reqs = []
    for cell, val in reversed(list(zip(row["tableCells"], values))):
        start = cell["content"][0]["startIndex"]
        end = cell["content"][-1]["endIndex"] - 1
        if end > start:
            reqs.append({"deleteContentRange": {"range": {"startIndex": start, "endIndex": end, "tabId": area.tab_id}}})
        reqs.append({"insertText": {"location": {"index": start, "tabId": area.tab_id}, "text": val}})
    return reqs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc_id")
    ap.add_argument("date")
    ap.add_argument("--owner", default="Scott")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--tag", action="store_true", help="the doc owner said yes to tagging")
    ap.add_argument("--people", default=None, help='JSON {"<name in doc>": "<email>"}')
    ap.add_argument("--decide", action="append", default=[], help="'<initiative>=red|done'")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.date)
    decisions = dict(x.split("=", 1) for x in a.decide)

    doc = du.read_doc(a.doc_id)
    _, areas, inits = du.model(doc)
    # Step 0: publish first. The doc owner's own tabs with nothing today.
    own = [i.name for i in inits if i.updater == a.owner and not any(x.date == today for x in i.sections)]
    if own:
        tabs = ", ".join(own)
        note = " (owner said no; they get Unconfirmed sections)" if a.publish else ""
        print(f"STEP 0: \"You haven't published {tabs} today. Do your update first?\"{note}")
    drafts = {}
    for init in inits:
        r = draft(init, today, a.owner, decisions)
        if r:
            drafts[init.title] = (init, *r)

    # Step 3 review
    by_updater = {}
    for init, lines, notes in drafts.values():
        by_updater.setdefault(init.updater, []).append((init, lines, notes))
    print(f"SWEEP REVIEW {du.label(today, True)}: {len(drafts)} tabs with no section today")
    for upd, items in by_updater.items():
        print(f"\n{upd}:")
        for init, lines, notes in items:
            print(f"  {init.title}: {lines[1]} | {lines[2]}" + (f"   [{'; '.join(notes)}]" if notes else ""))
    passed = [i.title for i, _, n in drafts.values() if any(x.startswith("PASSED") for x in n)]
    print(f"\nMilestones already passed (doc owner decides done or red): {passed or 'none'}")
    # A passed milestone is never published silently: the doc owner decides done or red first.
    undecided = [(init, n) for init, _, n in drafts.values()
                 if any(x.startswith("PASSED") and x.endswith("NOTHING YET") for x in n)]
    for init, _ in undecided:
        print(f"NEEDS A DECISION: {init.title}: milestone passed. Pass --decide \"{init.name}=done\" or --decide \"{init.name}=red\".")
    if a.publish and undecided:
        raise SystemExit("REFUSED: " + str(len(undecided)) + " passed milestone(s) have no decision: "
                         + "; ".join(i.title for i, _ in undecided)
                         + ". Re-run with --decide \"<initiative>=done\" or \"<initiative>=red\" for each. Nothing written.")
    if not a.publish:
        if undecided:
            print("\nNot ready to publish: decide the milestones above first.")
            return
        print("\nPublish? (re-run with --publish)")
        return

    # Step 3 publish: sections, re-reading each tab right before its write.
    for title, (init, lines, _) in drafts.items():
        doc = du.read_doc(a.doc_id)
        fresh = next(i for i in du.model(doc)[2] if i.tab_id == init.tab_id)
        same = next((s for s in fresh.sections if s.date == today), None)
        if same and not any(t.startswith("Starting section drafted by") for t, _ in same.lines):
            print(f"skip {title}: a section for today appeared since the review")
            continue
        if same:  # Create starting section: swap its closing line for the Unconfirmed line
            el = next(el for t, el in same.lines if t.startswith("Starting section drafted by"))
            line = lines[-1]
            # Skill step 2: an Unconfirmed section has no Progress line unless the doc owner's sources showed
            # something new. The starting section's Progress line is the morning's, so it goes (deleted last-first).
            prog = next((el2 for t, el2 in same.lines if t.startswith("Progress:")), None)
            reqs = [{"deleteContentRange": {"range": {"startIndex": el["startIndex"], "endIndex": el["endIndex"] - 1,
                                                      "tabId": fresh.tab_id}}},
                    {"insertText": {"location": {"index": el["startIndex"], "tabId": fresh.tab_id}, "text": line}},
                    {"updateTextStyle": {"range": {"startIndex": el["startIndex"], "endIndex": el["startIndex"] + du.utf16("Unconfirmed:"),
                                                   "tabId": fresh.tab_id}, "textStyle": {"bold": True}, "fields": "bold"}}]
            if prog is not None:  # Progress sits above the closing line, so delete it after the edits below it
                reqs.append({"deleteContentRange": {"range": {"startIndex": prog["startIndex"], "endIndex": prog["endIndex"],
                                                              "tabId": fresh.tab_id}}})
            du.batch(a.doc_id, reqs, doc)
            continue
        du.batch(a.doc_id, section_requests(fresh, lines), doc)

    # Area table rows: update the swept row only; add it if missing.
    for title, (init, lines, _) in drafts.items():
        doc = du.read_doc(a.doc_id)
        area = du.model(doc)[1][init.area_title]
        if area.table is None:
            print(f"WARN {init.area_title} has no Initiatives table")
            continue
        names = [r[0] for r in area.rows()]
        vals = row_values(init, lines)
        if init.name in names:
            du.batch(a.doc_id, set_cells(area, names.index(init.name) + 1, vals), doc)
        else:
            last = len(area.table["table"]["tableRows"]) - 1
            du.batch(a.doc_id, [{"insertTableRow": {"tableCellLocation": {
                "tableStartLocation": {"index": area.table["startIndex"], "tabId": area.tab_id},
                "rowIndex": last, "columnIndex": 0}, "insertBelow": True}}], doc)
            doc = du.read_doc(a.doc_id)
            area = du.model(doc)[1][init.area_title]
            reqs = set_cells(area, len(area.table["table"]["tableRows"]) - 1, vals)
            # a new row copies the style of the row above; make sure it is not bold
            du.batch(a.doc_id, reqs, doc)
            print(f"added row for {init.name} to {init.area_title}")

    # Step 4: tag updaters, only on --tag (the doc owner's yes), only emails that already have access.
    if a.tag:
        people = json.loads(a.people) if a.people else du.settings_get(a.doc_id)["people"]
        perms = du.gws("drive", "permissions", "list", "--params", json.dumps(
            {"fileId": a.doc_id, "fields": "permissions(emailAddress)", "supportsAllDrives": True}))
        access = {p.get("emailAddress") for p in perms.get("permissions", [])}
        for upd, items in by_updater.items():
            email = people.get(upd)
            tabs = ", ".join(i.name for i, _, _ in items)
            if not email or email not in access:
                if not email:
                    print(f"NOT TAGGED {upd}: no email in people. Ask {a.owner} for {upd}'s email.")
                else:
                    print(f"NOT TAGGED {upd}: no access to the doc. Draft note for {a.owner} (not sent): "
                          f"\"{upd} needs access to the daily update doc to confirm: {tabs}.\"")
                continue
            if a.doc_id not in du.PROTECTED:  # --tag is the doc owner's yes; access was checked above
                du.gws("drive", "comments", "create", "--params", json.dumps({"fileId": a.doc_id, "fields": "id,content"}),
                       body={"content": f"+{email} Unconfirmed today: {tabs}. Please confirm or correct by running \"do my daily update\"."})
                print(f"TAGGED {upd} <{email}>: {tabs}")
            else:
                print(f"NOT TAGGED {upd}: this doc is protected. Nothing posted.")

    # Re-read and quote (Daily step 6 rule).
    doc = du.read_doc(a.doc_id)
    for init in du.model(doc)[2]:
        if init.title in drafts:
            s = init.sections[0]
            ok = s.date == today and s.unconfirmed  # in-place or new
            print(f"{'LANDED' if ok else 'DID NOT LAND'} {init.title}: " + " / ".join(t for t, _ in s.lines))


if __name__ == "__main__":
    main()
