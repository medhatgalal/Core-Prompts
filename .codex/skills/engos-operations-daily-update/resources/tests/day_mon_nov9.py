"""Test day Mon Nov 9, 2026: the modes that had never run, plus refusals.

  python3 day_mon_nov9.py DOC_ID

Then run sweep.py, overview.py and verify.py for 2026-11-09 (see README). Each step prints the review the
person would see, then writes as if they said "publish". Evidence links are made up (example.test).
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "../scripts"))
import datetime as dt
import sys

import dudoc as du
import modes as m

DOC = sys.argv[1]
DAY = dt.date(2026, 11, 9)
L = lambda path: f"https://example.test/{path}"


def tab(title):
    return next(t["tabProperties"]["tabId"] for t, _ in du.all_tabs(du.read_doc(DOC)) if t["tabProperties"]["title"] == title)


def step(who, what):
    print(f"\n== {who}: {what}")


# 1. Refusals: a leader may not change the fixed structure or another owner's area tab.
rev = du.read_doc(DOC)["revisionId"]
step("Kyle", '"add an area called Composer Labs"')
print("Review: only the doc owner adds areas. Draft for Scott (not sent): "
      '"Can we add a Composer Labs area under Automation? Owner: Kyle."')
step("Kyle", '"change the Agents headline to say the pilot slipped"')
print("Review: the Agents area tab belongs to Sahil, so nothing written. Offer: a note to Sahil (drafted, not sent).")
step("Kyle", '"add an initiative called Evals"')
print(f"Review: similar tab exists: {m.similar(du.read_doc(DOC), 'Evals')}. Add another anyway? Kyle: no. Nothing written.")
assert du.read_doc(DOC)["revisionId"] == rev, "a refusal wrote to the doc"
print("Doc revision unchanged after all three refusals.")

# 2. Add an initiative owned by someone else.
step("Kyle", '"add Composer Telemetry, owner Joo, dashboard live Fri Nov 20"')
print(f"Similar tabs: {m.similar(du.read_doc(DOC), 'Composer Telemetry') or 'none'}. Publish? yes")
lines = m.section_lines(DAY, "🟢", "Telemetry dashboard live, Fri Nov 20",
                        "Joo opened the telemetry epic and the first metric is in review (Jira COM-1001).",
                        ["Added by Kyle for Joo."])
tel = m.add_initiative(DOC, tab("Composer (Kyle)"), "Composer Telemetry", "Joo", "Kyle", "Composer", lines,
                       [(3, "Jira COM-1001", L("jira/COM-1001"))])
m.set_row(DOC, tab("Composer (Kyle)"), "Composer Telemetry",
          ["Composer Telemetry", "Joo", "🟢 On track", "Telemetry dashboard live, Fri Nov 20"])

# 3. Change owner.
step("Kyle", '"Chandra now owns Composer UX"')
ux = tab("Composer UX (AlexD)")
m.retitle(DOC, ux, "Composer UX (Chandra)")
m.replace_in_para(DOC, ux, "Owner: AlexD ·", "Owner: Chandra ·", startswith="Owner:")
m.write_section(DOC, ux, m.section_lines(DAY, "🟡", "Product release sign-off, Fri Nov 13",
                                         "Owner changed from AlexD to Chandra on Mon Nov 9 (chat).",
                                         ["Green when: Product starts sign-off."]),
                [(3, "chat", L("chat/composer/m/5120"))])
m.set_row(DOC, tab("Composer (Kyle)"), "Composer UX", ["Composer UX", "Chandra", "🟡 At risk", "Product release sign-off, Fri Nov 13"])

# 4. Set updaters (doc owner).
step("Scott", '"Sahil updates Composer Resiliency"')
print("Composer Resiliency (Joo): Updater Kyle -> Sahil. Publish? yes")
m.replace_in_para(DOC, tab("Composer Resiliency (Joo)"), "Updater: Kyle ·", "Updater: Sahil ·", startswith="Owner:")

# 5. Finish an initiative.
step("Kui", '"Team Restructure is done"')
tr = tab("Team Restructure (Kui)")
m.write_section(DOC, tr, m.section_lines(DAY, "🟢", "Comms plan to the two teams, done Mon Nov 9.",
                                         "Done Mon Nov 9: both teams now work in the new structure (chat)."),
                [(3, "chat", L("chat/ea/m/880"))])
m.replace_in_para(DOC, tab("Enterprise Automation (Kui)"), "No initiatives finished yet.",
                  "Team Restructure: done Mon Nov 9, both teams now work in the new structure.")
import build
build.set_headline(DOC, "Enterprise Automation (Kui)",
                   "🟢 On track · Team Restructure is done; the GenAI upgrade holds for Wed Nov 11. (Mon Nov 9)")
m.set_row(DOC, tab("Enterprise Automation (Kui)"), "Team Restructure",
          ["Team Restructure", "Kui", "🟢 On track", "Done Mon Nov 9"])

# 5b. Stop an initiative.
step("Akhilesh", '"/engos-operations-daily-update stop EBC Support"')
print("   Agent: what's the reason? Akhilesh: Support moved the briefing to the field team. Publish? yes")
ebc = tab("EBC Support (Akhilesh)")
m.write_section(DOC, ebc, m.section_lines(DAY, "⚪", "None, stopped Mon Nov 9",
                                          "Stopped Mon Nov 9: Support moved the briefing to the field team (email).",
                                          ["Green when: Not planned."]),
                [(3, "email", L("mail/ebc/40"))])
m.replace_in_para(DOC, tab("AI Platform (Kui)"), "No initiatives finished yet.",
                  "EBC Support: stopped Mon Nov 9, Support moved the briefing to the field team.")
m.set_row(DOC, tab("AI Platform (Kui)"), "EBC Support", ["EBC Support", "Akhilesh", "⚪ Paused", "None, stopped Mon Nov 9"])

# 6. Change the structure (doc owner): rename an area, move one initiative.
step("Scott", '"rename Automation-wide to Cross-cutting, and move Claude Code Pilot under Enterprise Automation"')
print("Before: Automation-wide (Scott) > AI Engineering Hiring, Chennai Team Onboarding, Claude Code Pilot\n"
      "After:  Cross-cutting (Scott) > AI Engineering Hiring, Chennai Team Onboarding; "
      "Enterprise Automation (Kui) > ..., Claude Code Pilot. Publish? yes")
aw = tab("Automation-wide (Scott)")
m.retitle(DOC, aw, "Cross-cutting (Scott)")
m.replace_in_para(DOC, "t.0", "Automation-wide", "Cross-cutting")              # Area health row name
for title in ("AI Engineering Hiring (Scott)", "Chennai Team Onboarding (Chandra)", "Claude Code Pilot (Scott)"):
    m.replace_in_para(DOC, tab(title), "Area: Automation-wide ·", "Area: Cross-cutting ·", startswith="Owner:")
ccp = tab("Claude Code Pilot (Scott)")
ea = tab("Enterprise Automation (Kui)")
n_ea = len(m.find_tab(du.read_doc(DOC), ea).get("childTabs", []))
m.move_tab(DOC, ccp, ea, n_ea)
m.replace_in_para(DOC, ccp, "Area: Cross-cutting ·", "Area: Enterprise Automation ·", startswith="Owner:")
src = next(i for i in du.model(du.read_doc(DOC))[2] if i.tab_id == ccp)
if src.sections[0].date == DAY:
    m.insert_line_before(DOC, ccp, "Unconfirmed:", "Moved from Cross-cutting to Enterprise Automation on Mon Nov 9.")
else:  # skill: add a section dated today that carries status, milestone and Green when
    st, ms, gw = src.newest("status").status, src.newest("milestone").milestone, src.newest().line("Green when:")
    m.write_section(DOC, ccp, m.section_lines(DAY, st, ms, "Moved from Cross-cutting to Enterprise Automation on Mon Nov 9.",
                                              [gw] if gw and st != "🟢" else []))
src = next(i for i in du.model(du.read_doc(DOC))[2] if i.tab_id == ccp)
row = next(r for a in du.model(du.read_doc(DOC))[1].values() for r in a.rows() if r[0] == "Claude Code Pilot")
m.delete_row(DOC, aw, "Claude Code Pilot")
m.set_row(DOC, ea, "Claude Code Pilot", row)

fixed = du.repair_headings(DOC)
print(f"\nHeadings restored after writes: {fixed or 'none needed'}")
