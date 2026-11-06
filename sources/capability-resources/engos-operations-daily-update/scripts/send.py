"""Send step test: draft the reader summary from the overview and stop at the gate. Never sends.

  python3 send.py DOC_ID '[{"name":"Medhat","email":"medhat.test@example.invalid","channel":"email"}]'
"""
import json
import sys

import dudoc as du


def draft(doc_id, readers):
    doc = du.read_doc(doc_id)
    ov = du.model(doc)[0]
    body = ov["documentTab"]["body"]["content"]
    paras = [e for e in body if "paragraph" in e]
    title = du.para_text(paras[0]["paragraph"]).strip()
    asof = next(du.para_text(e["paragraph"]) for e in paras if "As of" in du.para_text(e["paragraph"]))
    day = du.label(du.dates_in(asof)[0][1])
    tables = {du.cell_text(e["table"]["tableRows"][0]["tableCells"][0]): [[du.cell_text(c) for c in r["tableCells"]]
                                                                         for r in e["table"]["tableRows"][1:]]
              for e in body if "table" in e}
    # One line per Area health row: the area's colour (the top of its Status cell), name and headline.
    bullets = [f"{r[2][:1]} {r[0]}: {r[3]}" for r in tables.get("Area", [])]
    decisions = tables.get(du.DECISIONS_COL, [])
    lines = [f"{title}, {day}", ""] + bullets
    if decisions:
        lines += ["", "Decisions or help needed:"] + [f"- {d[0]} (by {d[3]})" for d in decisions]
    inits = du.model(doc)[2]
    today = du.dates_in(asof)[0][1]
    open_ = [i.name for i in inits if not i.sections or i.sections[0].date < today or i.sections[0].unconfirmed
             or any(t.startswith("Starting section drafted by") for t, _ in i.sections[0].lines)]
    lines += ["", f"{len(open_)} of {len(inits)} initiatives not confirmed today: {', '.join(open_)}."
              if open_ else "All initiatives confirmed today."]
    lines += ["", f"Doc: https://docs.google.com/document/d/{doc_id}/edit"]
    return lines


if __name__ == "__main__":
    readers = json.loads(sys.argv[2])
    text = draft(sys.argv[1], readers)
    print("RECIPIENTS: " + ", ".join(f"{r['name']} <{r['email']}> by {r['channel']}" for r in readers))
    print("TEXT:\n" + "\n".join(text))
    print(f"\nSend to {', '.join(r['name'] for r in readers)}?  (test answers no; nothing sent)")
