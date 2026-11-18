"""Send step: draft the reader summary from the overview and stop at the gate. Never sends.

  python3 send.py DOC_ID '[{"name":"Medhat","email":"medhat.test@example.invalid","channel":"email"}]'
      [--html OUT.html] [--last-sent last_sent.json]
  python3 send.py snapshot DOC_ID        # the JSON to save as `last_sent` in config.json after a successful send

Chat readers get the plain text. Email readers get the HTML page (`--html`), built only from the overview and the
initiative tabs, plus an author-only checklist written next to it (OUT.checklist.md), never part of the email.
"""
import datetime as dt
import html as _h
import json
import re
import sys

import dudoc as du

R, A, G, P = "#b91c1c", "#d97706", "#166534", "#9ca3af"
NAME = {"🔴": "Red", "🟡": "At risk", "🟢": "On track", "⚪": "Paused"}
EMOJI = {v: k for k, v in NAME.items()}
PILL = {"Red": ("#fdecea", R), "At risk": ("#fef3c7", "#92400e"), "On track": ("#e6f4ea", G), "Paused": ("#f3f4f6", "#4b5563")}
RANK = {"Red": 0, "At risk": 1, "On track": 2, "Paused": 3}
BAR = (("🔴", R), ("🟡", A), ("🟢", "#1a7f4b"), ("⚪", P))
HEAD = 'padding:14px 20px 4px;font-size:13px;font-weight:bold;letter-spacing:.5px;color:#374151'
e = lambda s: _h.escape(str(s), quote=True)


def facts(doc_id):
    """Everything the page says, read from the doc. Nothing is invented here."""
    doc = du.read_doc(doc_id)
    ov, tabs, inits = du.model(doc)
    body = ov["documentTab"]["body"]["content"]
    paras = [x for x in body if "paragraph" in x]
    title = du.para_text(paras[0]["paragraph"]).strip()
    asof = next(du.para_text(x["paragraph"]) for x in paras if "As of" in du.para_text(x["paragraph"]))
    today = du.dates_in(asof)[0][1]
    when = re.search(r"\d{1,2}:\d{2}\s*[AP]M(?:\s*ET)?", asof)
    tables = {du.cell_text(x["table"]["tableRows"][0]["tableCells"][0]): [[du.cell_text(c) for c in r["tableCells"]]
                                                                         for r in x["table"]["tableRows"][1:]]
              for x in body if "table" in x}
    by_name = {a.name: a for a in tabs.values()}
    areas = []
    for r in tables.get("Area", []):
        counts = {k: int(n) for k, n in re.findall(r"(🔴|🟡|🟢|⚪)\s*(\d+)", r[2])}
        live = [NAME[k] for k in ("🔴", "🟡", "🟢") if counts.get(k)]
        a = by_name.get(r[0])
        areas.append({"name": r[0], "tab": a.tab_id if a else None, "counts": counts,
                      "status": live[0] if live else "Paused", "headline": r[3], "updated": r[4]})
    def finished(i):  # done or stopped: waiting for Archive, so never "unconfirmed" (the sweep skips these too)
        return bool(i.sections) and (i.sections[0].line("Progress:") or "").startswith(("Progress: Done ", "Progress: Stopped "))
    open_ = [i.name for i in inits if not finished(i) and (not i.sections or i.sections[0].date < today
             or i.sections[0].unconfirmed
             or any(t.startswith("Starting section drafted by") for t, _ in i.sections[0].lines))]
    # Coming up and past due come from the overview's own Next 2 weeks table, so the email says what the doc says.
    owner = {c: i for d, c, i, st in du.next_two_weeks(inits, today)}
    nxt = []
    for r in tables.get("Date", []):
        found = du.dates_in(r[0])
        if found and found[0][1]:
            c = re.split(r",?\s*no date set yet", r[1], flags=re.I)[0].strip(" ,") or r[1]
            nxt.append((found[0][1], c, owner.get(r[1]), r[2][:1]))
    return {"doc_id": doc_id, "title": title, "asof": asof, "today": today, "time": when.group(0) if when else "",
            "areas": areas, "decisions": tables.get(du.DECISIONS_COL, []), "inits": inits, "open": open_,
            "next": nxt, "missing": du.missing_plan(inits, today)}


def snapshot(f):
    return {"date": f["today"].isoformat(), "areas": {a["name"]: a["status"] for a in f["areas"]},
            "unconfirmed": len(f["open"]), "missing": len(f["missing"])}


def draft(doc_id):
    """The plain text, for a Chat reader."""
    f = facts(doc_id)
    lines = [f"{f['title']}, {du.label(f['today'])}", ""]
    lines += [f"{EMOJI[a['status']]} {a['name']}: {a['headline']}" for a in f["areas"]]
    if f["decisions"]:
        lines += ["", "Decisions or help needed:"] + [f"- {d[0]} (by {d[3]})" for d in f["decisions"]]
    o, m = f["open"], f["missing"]
    lines += ["", f"{len(o)} of {len(f['inits'])} initiatives not confirmed today: {', '.join(o)}."
              if o else "All initiatives confirmed today."]
    lines += [f"{len(m)} initiatives are missing a plan: {', '.join(i.name for i, _, _ in m)}."
              if m else "Every open initiative has a dated next milestone."]
    return lines + ["", f"Doc: https://docs.google.com/document/d/{doc_id}/edit"]


def overall(red, at, total):
    """RED when two or more initiatives, or a quarter of all work, are red; AMBER when anything is red or at risk."""
    if red >= 2 or (total and red * 4 >= total):
        return "RED"
    return "AMBER" if red or at else "GREEN"


def friday_after(today):
    d = today + dt.timedelta(days=1)
    while d.weekday() != 4:
        d += dt.timedelta(days=1)
    return d


def _num(n, color, bg, label, cap):
    return (f'<td width="25%" style="background:{bg};padding:10px 6px;text-align:center"><div style="font-size:28px;'
            f'font-weight:bold;color:{color};line-height:1.1">{n}</div><div style="font-size:12px;font-weight:bold;'
            f'padding-top:2px">{e(label)}</div><div style="font-size:11px;color:#555">{e(cap)}</div></td>')


def _chip(name, old, new):
    """Coloured by the NEW status. The arrow carries direction."""
    col, bg = PILL[new][1], PILL[new][0]
    arrow = "&#9650;" if RANK[new] > RANK[old] else "&#9660;"
    return (f'<td width="33%" style="background:{bg};padding:8px 8px;text-align:center;font-size:12px;vertical-align:top">'
            f'<b>{e(name)}</b><br><span style="color:{col};font-weight:bold">{arrow} {e(old)} to {e(new)}</span></td>')


def _card(color, area, chip, chipbg, chipfg, head, why, doing, doing_red, need):
    d = f'<b style="color:{R}">{e(doing)}</b>' if doing_red else e(doing)
    return (f'<tr><td style="border-left:4px solid {color};background:#fafafa;padding:10px 14px"><table width="100%" '
            f'cellpadding="0" cellspacing="0"><tr><td style="font-size:12px;color:#555">{e(area)}</td><td align="right">'
            f'<span style="background:{chipbg};color:{chipfg};font-size:11px;font-weight:bold;padding:2px 8px;'
            f'border-radius:10px">{e(chip)}</span></td></tr></table><div style="font-size:15px;font-weight:bold;'
            f'padding:4px 0">{e(head)}</div><div style="font-size:13px;line-height:1.55"><b style="color:#555">WHY</b> '
            f'{e(why)}<br><b style="color:#555">DOING</b> {d}<br><b style="color:#555">NEEDED</b> {e(need)}</div></td></tr>'
            f'<tr><td style="height:8px"></td></tr>')


def _why(f, area, new):
    """(initiative, reason) pairs: why an area changed colour, taken only from what the initiative tabs say today."""
    out = []
    for i in f["inits"]:
        if i.area_name != area or not i.sections:
            continue
        cur, prev = i.sections[0], (i.sections[1] if len(i.sections) > 1 else None)
        st = {"\U0001F534": "Red", "\U0001F7E1": "At risk", "\U0001F7E2": "On track", "\u26AA": "Paused"}.get(cur.status)
        moved = prev is not None and prev.status != cur.status
        if st != new and not moved:
            continue
        prog = (cur.line("Progress:") or "").replace("Progress:", "", 1).strip()
        blk = (cur.line("Blocked on:") or "").replace("Blocked on:", "", 1).strip()
        text = prog.split(". ")[0].rstrip(".") + "."
        if len(text) > 260:
            text = text[:257].rsplit(" ", 1)[0] + "..."
        if blk and blk.lower().rstrip(".") != "none":
            text += " Blocked on: " + (blk if len(blk) < 200 else blk[:197].rsplit(" ", 1)[0] + "...")
        out.append((i.name, text if prog else "No reason is recorded in the doc.", bool(moved)))
    if any(x[2] for x in out):  # something moved: say why it moved, not what stayed put
        out = [x for x in out if x[2]]
    return out[:3]


def render(f, last=None):
    """(subject, html, checklist) for an email reader. `last` is the saved `last_sent`, or None."""
    doc, today = f"https://docs.google.com/document/d/{f['doc_id']}/edit", f["today"]
    areas = f["areas"]
    total_n = sum(sum(a["counts"].values()) for a in areas)
    cnt = lambda k: sum(a["counts"].get(k, 0) for a in areas)
    red, at, green = cnt("🔴"), cnt("🟡"), cnt("🟢")
    colour = overall(red, at, total_n)
    cbg, cfg = {"RED": PILL["Red"], "AMBER": PILL["At risk"], "GREEN": PILL["On track"]}[colour]
    asks = len(f["decisions"])
    prev_day = dt.date.fromisoformat(last["date"]) if last else None
    prev_wd = prev_day.strftime("%A") if last else ""
    checklist = []

    # the four numbers
    red_inits = [i for d, c, i, s in f["next"] if s == "🔴" and i]
    red_names = [i.name if i else c for d, c, i, s in f["next"] if s == "🔴"]
    overdue = [d for d, c, i, s in f["next"] if s == "🔴" and d < today]
    red_cap = "none"
    if red_names:
        red_cap = red_names[0] + (f", {(today - overdue[0]).days} days late" if overdue else "") + (f" and {len(red_names) - 1} more" if len(red_names) > 1 else "")
    end = friday_after(today)
    week = [(d, c, s) for d, c, i, s in f["next"] if today < d <= end]
    miss = f["missing"]
    miss_cap = f"was {last['missing']} on {prev_wd}" if last else "open initiatives"
    nums = (_num(red, R, PILL["Red"][0], "Red", red_cap)
            + _num(at, "#92400e", PILL["At risk"][0], "At risk", f"across {sum(1 for a in areas if a['counts'].get('🟡'))} areas")
            + _num(len(week), "#374151", "#f3f4f6", "Due this week", f"{du.label(today + dt.timedelta(days=1))} to {du.label(end)}")
            + _num(len(miss), "#92400e" if miss else G, PILL["At risk"][0] if miss else PILL["On track"][0], "No dated plan", miss_cap))

    # the two bold lines
    line1 = f"{green} of {total_n} initiatives are on track: {red} red, {at} at risk." + (f" {asks} decision{'s' if asks != 1 else ''} or help needed." if asks else "")
    push = [f"{n} (past due)" for n in red_names] + [d[0] for d in f["decisions"]]
    line2 = ("Needs a push: " + "; ".join(push) + ".") if push else "Nothing needs a push today."

    # changed since the last send
    changed = ""
    if last:
        moved = [(a["name"], last["areas"][a["name"]], a["status"]) for a in areas
                 if a["name"] in last["areas"] and last["areas"][a["name"]] != a["status"]]
        inner = ('<tr><td style="padding:6px 20px 8px"><table width="100%" cellpadding="0" cellspacing="6" style="border-collapse:separate"><tr>'
                 + "".join(_chip(*m) for m in moved) + "</tr></table></td></tr>"
                 + "".join(f'<tr><td style="padding:2px 20px 6px;font-size:12px;line-height:1.5"><b>{e(m[0])}, why:</b> '
                           + " ".join(f'{e(n)}: {e(t)}' for n, t, _ in _why(f, m[0], m[2]))
                           + "</td></tr>" for m in moved)) if moved else \
            f'<tr><td style="padding:6px 20px 8px;font-size:13px">No area changed colour since {e(du.label(prev_day))}.</td></tr>'
        changed = f'<tr><td style="{HEAD}">CHANGED SINCE {e(prev_wd.upper())}</td></tr>' + inner

    # decision cards
    cards = ""
    for d in f["decisions"]:
        init = next((i for i in f["inits"] if i.name.lower() in d[0].lower()), None)
        prog = (init.sections[0].line("Progress:") if init and init.sections else None) or ""
        prog = prog[len("Progress:"):].strip()
        is_red = bool(init and init in red_inits)
        col, bg = (R, PILL["Red"][0]) if is_red else (A, PILL["At risk"][0])
        if not prog:
            checklist.append(f'Decision "{d[0]}" has no recorded action, so the card says so in red. Confirm that is true.')
        cards += _card(col, f"{init.area_name} · {init.name}" if init else "Exec leadership", f"By {d[3]}", bg,
                       R if is_red else "#92400e", d[0], d[1], prog or "No action is recorded in the doc.", not prog,
                       f"{d[2]} ({d[4]} decides)" if d[4] else d[2])
    decisions = (f'<tr><td style="{HEAD}">NEEDS A DECISION OR OWNER</td></tr><tr><td style="padding:6px 20px 8px">'
                 f'<table width="100%" cellpadding="0" cellspacing="0">{cards}</table></td></tr>') if cards else ""

    # area health
    prev_by = (last or {}).get("areas", {})
    rows = ""
    for a in areas:
        bg, fg = PILL[a["status"]]
        p = prev_by.get(a["name"])
        if not p:
            mark, was = "&nbsp;", ""
        elif RANK[a["status"]] > RANK[p]:
            mark, was = f'<span style="color:{G};font-weight:bold">&#9650; Better</span>', f"(was {p.lower()})"
        elif RANK[a["status"]] < RANK[p]:
            mark, was = f'<span style="color:{R};font-weight:bold">&#9660; Worse</span>', f"(was {p.lower()})"
        else:
            mark, was = '<span style="color:#555">No change</span>', ""
        tot = sum(a["counts"].values()) or 1
        bar = "".join(f'<td width="{round(a["counts"][k] * 100 / tot)}%" style="background:{c};height:10px;font-size:1px;line-height:10px">&nbsp;</td>'
                      for k, c in BAR if a["counts"].get(k))
        words = ", ".join(f"{a['counts'][k]} {NAME[k].lower()}" for k, _ in BAR if a["counts"].get(k))
        link = f'{doc}?tab={a["tab"]}' if a["tab"] else doc
        rows += (f'<tr><td style="padding:10px 10px;border-top:1px solid #e5e7eb;vertical-align:top;width:150px"><a href="{e(link)}" '
                 f'style="color:#1a56db;text-decoration:none;font-weight:bold;font-size:14px">{e(a["name"])}</a><br>'
                 f'<span style="display:inline-block;margin-top:4px;background:{bg};color:{fg};font-size:11px;font-weight:bold;'
                 f'padding:2px 8px;border-radius:10px">{e(a["status"])}</span><br><span style="font-size:11px">{mark} {e(was)}</span></td>'
                 f'<td style="padding:10px 10px;border-top:1px solid #e5e7eb;vertical-align:top;font-size:13px;line-height:1.45">'
                 f'<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse"><tr>{bar}</tr></table>'
                 f'<div style="font-size:11px;color:#555;padding:3px 0 5px">{e(words)}</div>{e(a["headline"])}</td></tr>')
        if "headline from" in a["headline"]:
            checklist.append(f"{a['name']}: the headline is flagged old or out of date with its tabs. The email repeats it as written.")

    # coming up and no dated plan
    past = [(d, c) for d, c, i, s in f["next"] if d < today]
    by_day = {}
    for d, c, s in week:
        by_day.setdefault(d, []).append(c + {"🔴": " (red)", "🟡": " (at risk)"}.get(s, ""))
    lines = [f'<b>Past due:</b> {e("; ".join(f"{c} (was {du.label(d)})" for d, c in past))}'] if past else []
    lines += [f'<b>{e(du.label(d))}:</b> {e(". ".join(v))}.' for d, v in sorted(by_day.items())]
    coming = (f'<tr><td style="{HEAD}">COMING UP</td></tr><tr><td style="padding:6px 20px 8px;font-size:13px;line-height:1.7">'
              + "<br>".join(lines) + "</td></tr>") if lines else ""
    plan = (f'<tr><td style="{HEAD}">NO DATED PLAN</td></tr><tr><td style="padding:6px 20px 8px;font-size:13px;line-height:1.5">'
            f'<b>{len(miss)} initiative{"s have" if len(miss) != 1 else " has"} no dated next milestone:</b> '
            f'{e(", ".join(i.name for i, _, _ in miss))}.</td></tr>') if miss else ""

    # footer and checklist
    n_open = len(f["open"])
    foot = f"{n_open} of {len(f['inits'])} initiatives are unconfirmed today" if n_open else "All initiatives are confirmed today"
    if last:
        foot += f" ({last['unconfirmed']} on {prev_wd})"
    foot += (f'. Statuses come from each leader\'s update in the <a href="{e(doc)}" style="color:#1a56db">daily update doc</a>, '
             f"as of {e(du.label(today))}{', ' + e(f['time']) if f['time'] else ''}."
             + (f" {e(prev_wd)}'s statuses are from the summary sent {e(du.label(prev_day))}." if last else "")
             + " Green: on track. Amber: at risk or waiting on another team. Red: a committed date has passed.")
    if total_n != len(f["inits"]):
        checklist.append(f"The overview counts {total_n} initiatives and the doc has {len(f['inits'])} tabs. The bars use the overview counts.")
    if f["open"]:
        checklist.append("Unconfirmed today: " + ", ".join(f["open"]) + ".")
    if not last:
        checklist.append("No `last_sent` saved, so Changed since, the better and worse marks and the 'was N' figures are left out.")
    checklist.append(f"Overall colour is {colour}: RED when two or more initiatives, or a quarter of all work, are red; AMBER when anything is red or at risk.")

    pre = f"{colour}. {red} red, {at} at risk." + (f" {asks} decision{'s' if asks != 1 else ''} or help needed." if asks else "")
    day = today.strftime("%A, %b ") + str(today.day) + today.strftime(", %Y")
    sub = f"{f['title']}, {du.label(today)}: {colour}, {red} red, {asks} ask{'s' if asks != 1 else ''}"
    vs = f"vs {e(du.label(prev_day))} · " if last else ""
    asof = f"as of {e(f['time'])} · " if f["time"] else ""
    page = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>@media (max-width:480px){{.sc td{{display:inline-block !important;width:46% !important;box-sizing:border-box}}}}</style></head>
<body style="margin:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;color:#111">
<div style="display:none;max-height:0;overflow:hidden;font-size:1px;color:#f3f4f6">{e(pre)}</div>
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:12px 8px">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;background:#fff;border:1px solid #e5e7eb">
<tr><td style="background:#1f2937;color:#fff;padding:14px 20px"><div style="font-size:12px;color:#9ca3af">{e(f['title'])}</div>
<div style="font-size:18px;font-weight:bold">{e(day)} <span style="font-weight:normal;font-size:12px;color:#9ca3af">{vs}{asof}<a href="{e(doc)}" style="color:#93c5fd">Daily update doc</a></span></div></td></tr>
<tr><td style="padding:14px 20px 4px"><table class="sc" width="100%" cellpadding="0" cellspacing="6" style="border-collapse:separate"><tr>{nums}</tr></table></td></tr>
<tr><td style="padding:8px 20px 16px;border-bottom:1px solid #e5e7eb"><table width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="96" style="vertical-align:top"><div style="background:{cbg};color:{cfg};font-weight:bold;font-size:15px;text-align:center;padding:10px 4px;border-radius:6px">{colour}</div></td>
<td style="padding-left:12px;font-size:14px;line-height:1.55"><b>{e(line1)}</b><br><b>{e(line2)}</b></td></tr></table></td></tr>
{changed}{decisions}
<tr><td style="{HEAD}">AREA HEALTH <span style="font-weight:normal;color:#555;letter-spacing:0">(bar = each area's initiatives: <span style="color:{R}">red</span>, <span style="color:{A}">at risk</span>, <span style="color:#1a7f4b">on track</span>, <span style="color:#6b7280">paused</span>)</span></td></tr>
<tr><td style="padding:6px 20px 8px"><table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border-bottom:1px solid #e5e7eb">{rows}</table></td></tr>
{coming}{plan}
<tr><td style="padding:10px 20px 16px;font-size:12px;color:#555;border-top:1px solid #e5e7eb;line-height:1.5">{foot}</td></tr>
</table></td></tr></table></body></html>'''
    page = page.replace("—", ",")  # no em dashes, even from text in the doc
    return sub, page, "# Author checklist (not part of the email)\n\n" + "\n".join(f"{n}. {c}" for n, c in enumerate(checklist, 1)) + "\n"


if __name__ == "__main__":
    if sys.argv[1] == "snapshot":
        print(json.dumps(snapshot(facts(sys.argv[2]))))
        sys.exit(0)
    args = sys.argv[1:]
    opt = {k: args[args.index(k) + 1] for k in ("--html", "--last-sent") if k in args}
    readers = json.loads(args[1])
    text = draft(args[0])
    print("RECIPIENTS: " + ", ".join(f"{r['name']} <{r['email']}> by {r['channel']}" for r in readers))
    if "--html" in opt:
        last = json.load(open(opt["--last-sent"])) if "--last-sent" in opt else None
        sub, page, check = render(facts(args[0]), last)
        out = opt["--html"]
        open(out, "w").write(page)
        open(out.rsplit(".", 1)[0] + ".checklist.md", "w").write(check)
        print(f"SUBJECT: {sub}\nHTML: {out}\nCHECKLIST: {out.rsplit('.', 1)[0]}.checklist.md")
    print("TEXT:\n" + "\n".join(text))
    print(f"\nSend to {', '.join(r['name'] for r in readers)}?  (test answers no; nothing sent)")
