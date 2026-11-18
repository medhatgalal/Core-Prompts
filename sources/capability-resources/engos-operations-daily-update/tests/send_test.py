"""Offline checks for the email summary page. No doc and no network.

    python3 send_test.py
"""
import datetime as dt
import os
import sys

os.environ.setdefault("DU_TODAY", "2026-11-17")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import send  # noqa: E402

FAILS = []
D = dt.date


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


class Sec:
    status = "🟢"

    def __init__(self, prog):
        self.prog = prog
        self.date = D(2026, 11, 17)

    def line(self, p):
        return f"Progress: {self.prog}" if self.prog and p == "Progress:" else None


class Init:
    def __init__(self, name, prog=""):
        self.name, self.area_name = name, "Automation-wide"
        self.sections = [Sec(prog)]

    def newest(self, a):
        return self.sections[0]


def area(name, counts, status, head="Headline."):
    return {"name": name, "tab": "t.x", "counts": counts, "status": status, "headline": head, "updated": "Tue Nov 17"}


iso, gen = Init("ISO 42001", ""), Init("GenAI Skills", "Toggle waits on approval.")
f = {"doc_id": "D", "title": "Automation Daily Updates", "asof": "", "today": D(2026, 11, 17), "time": "7:00 PM ET",
     "areas": [area("Composer", {"🟢": 4}, "On track"), area("Automation-wide", {"🟡": 2, "🟢": 1}, "At risk"),
               area("Enterprise Automation", {"🔴": 1, "🟢": 1}, "Red")],
     "decisions": [["ISO 42001 approvals", "Half cannot finish.", "Approve three.", "Wed Nov 18", "Medhat"],
                   ["GenAI Skills release", "Customers wait.", "Confirm the date.", "Wed Nov 18", "Kui"]],
     "inits": [iso, gen], "open": ["Evals"], "missing": [(Init("Evals"), "No date", None)],
     "next": [(D(2026, 11, 13), "GenAI Skills on", gen, "🔴"), (D(2026, 11, 18), "ISO done", iso, "🟡")]}
last = {"date": "2026-11-16", "areas": {"Composer": "At risk", "Automation-wide": "Red", "Enterprise Automation": "On track"},
        "unconfirmed": 4, "missing": 2}
sub, page, check_md = send.render(f, last)

check("subject leads with colour and asks", sub == "Automation Daily Updates, Tue Nov 17: AMBER, 1 red, 2 asks", sub)
check("chip colour follows the new status", "background:#fef3c7" in page.split("CHANGED SINCE")[1].split("NEEDS A DECISION")[0]
      and "Red to At risk" in page)
check("improvement arrow points up", "&#9650; Red to At risk" in page and "&#9660; On track to Red" in page)
check("no recorded action says so in red", f'<b style="color:{send.R}">No action is recorded in the doc.</b>' in page)
check("recorded action is quoted", "Toggle waits on approval." in page)
check("days late counted from the as-of date", "4 days late" in page)
check("area name links to its tab", "edit?tab=t.x" in page)
check("bars have words beside them", "1 red, 1 on track" in page)
check("preheader present", 'display:none' in page and "AMBER. 1 red, 2 at risk." in page)
check("no em dash", "—" not in page)
check("footer says unconfirmed against last send", "1 of 2 initiatives are unconfirmed today (4 on Monday)" in page)
check("checklist is not in the page", "Author checklist" not in page and "Author checklist" in check_md)
_, p2, c2 = send.render(f, None)
check("no last_sent drops Changed since", "CHANGED SINCE" not in p2 and "No `last_sent`" in c2)
_, p3, _ = send.render(f, {"date": "2026-11-16", "areas": {"Composer": "Red", "Enterprise Automation": "On track"}, "unconfirmed": 0, "missing": 0})
check("area health says Worse when status fell (on track to red)", "&#9660; Worse</span> (was on track)" in p3)
check("area health says Better when status rose (red to at risk)", "&#9650; Better</span> (was red)" in p3)
check("changed since gives a why for each moved area", "Composer, why:" in p3 or "Enterprise Automation, why:" in p3)
check("overall rule", send.overall(1, 5, 26) == "AMBER" and send.overall(2, 0, 26) == "RED" and send.overall(0, 0, 26) == "GREEN")
print("\n%d failure(s)" % len(FAILS))
sys.exit(1 if FAILS else 0)
