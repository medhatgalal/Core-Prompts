"""Full exploratory run on a brand-new temp doc: Create, then two days across every persona.

  python3 exploratory.py create            # prints the new doc id
  python3 exploratory.py day1 DOC_ID       # Fri Nov 6: leaders, covering, refusals, traps, concurrency
  python3 exploratory.py day2 DOC_ID       # Mon Nov 9: hand edit, no-change day, then day_mon_nov9.py modes

Sweep, overview and verify run separately (see README). Evidence is made up (example.test links).
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "../scripts"))
import datetime as dt
import sys
from zoneinfo import ZoneInfo

import build
import daily as d
import dudoc as du
import modes as m

FRI, MON = dt.date(2026, 11, 6), dt.date(2026, 11, 9)
L = lambda p: f"https://example.test/{p}"
GW = lambda: "Green when: "


def S(n, o, u, s, ms, prog, word, path, extra=()):
    return (n, o, u, s, ms, prog, word, L(path), extra)


STRUCTURE = [
    ("Composer", "Kyle", [
        S("Composer Evals", "Goldberg", "Kyle", "🟢", "First full nightly eval run, Mon Nov 9", "Navigator is now where every eval run starts (chat).", "chat", "chat/evals/1"),
        S("Composer Planning APIs", "Chandra", "Kyle", "🟢", "Internal release, Tue Nov 10", "Quality engineering called Part 1 stable after the bug bash (Jira COM-901).", "Jira COM-901", "jira/COM-901"),
        S("Composer UX", "AlexD", "Kyle", "🟡", "Product release sign-off, Fri Nov 13", "Engineering is ready; Product has not started sign-off (chat).", "chat", "chat/ux/2",
          ["Green when: Product starts sign-off."]),
        S("Composer Resiliency", "Joo", "Kyle", "🟡", "Shared cache design approved, Wed Nov 11", "The second cache merge request is up; the design needs Scott and Medhat's approval (merge request !212).", "merge request !212", "mr/212",
          ["Green when: the cache design is approved."]),
        S("Fast Harness Default", "John Irby", "Kyle", "🟢", "Fast becomes the default, Tue Nov 10", "Slices 1 and 2 are closed and slice 3 is in review (Jira COM-965).", "Jira COM-965", "jira/COM-965"),
    ]),
    ("Agents", "Sahil", [
        S("AI Control Plane", "Sahil", "Sahil", "🟢", "Policy engine for the pilot, Fri Nov 13", "The policy engine build started (chat).", "chat", "chat/acp/3"),
        S("Federated Agent Studio", "Nima", "Sahil", "🟢", "Federation smoke tests pass, Fri Nov 6", "3 of 5 smoke tests pass (merge request !121).", "merge request !121", "mr/121"),
        S("Agent Studio Quality", "Mahima", "Sahil", "🟢", "Flaky test count under 5, Fri Nov 13", "Flaky tests are down from 14 to 8 (Jira AP-4301).", "Jira AP-4301", "jira/AP-4301"),
    ]),
    ("Enterprise Automation", "Kui", [
        S("Team Restructure", "Kui", "Kui", "🟡", "Comms plan to the two teams, No date set yet", "The comms plan is drafted but not agreed (doc).", "doc", "doc/restructure",
          ["Green when: the comms plan has an agreed date."]),
        S("GenAI Skills Model Upgrades", "Chema", "Kui", "🟢", "Production rollout, Wed Nov 11", "The upgrade passed staging (chat).", "chat", "chat/genai/4"),
    ]),
    ("AI Platform", "Kui", [
        S("Deep Agents", "Akhilesh", "Akhilesh", "🟡", "Kata container sandboxes in production, Fri Nov 13", "Production needs Kata container sandboxes, and that date moved to Fri Nov 13 (chat).", "chat", "chat/deep/5",
          ["Green when: Kata container sandboxes have a committed date."]),
        S("Dev MCP / Tools", "Akhilesh", "Akhilesh", "🟢", "Port finished, Fri Nov 6", "224 of 226 Dev MCP APIs run on the new software development kit (merge request !340).", "merge request !340", "mr/340"),
        S("API Desk", "Akhilesh", "Akhilesh", "⚪", "Restart after Dev MCP, Mon Nov 30", "Paused behind Dev MCP / Tools work (chat).", "chat", "chat/apidesk/6",
          ["Green when: Dev MCP / Tools frees up the team to restart."]),
        S("EBC Support", "Akhilesh", "Akhilesh", "🟡", "Briefing pack ready, Wed Nov 18", "Support asked for an Executive Briefing Center (EBC) visit on Wed Nov 18 (email).", "email", "mail/ebc/7",
          ["Green when: the briefing pack has an owner."]),
    ]),
    ("Automation-wide", "Scott", [
        S("AI Engineering Hiring", "Scott", "Scott", "🟢", "Close the two open roles, Fri Nov 20", "Two candidates are in the final round (email).", "email", "mail/hiring/8"),
        S("Chennai Team Onboarding", "Chandra", "Scott", "🟡", "All eight engineers set up, Wed Nov 11", "Six of eight engineers have VPN tokens (chat).", "chat", "chat/chennai/9",
          ["Green when: the last two engineers have VPN tokens."]),
        S("Claude Code Pilot", "Scott", "Scott", "🟢", "Org-wide rollout decision, Fri Nov 13", "David has the AI Platform names (chat).", "chat", "chat/ccp/10"),
    ]),
]


def step(who, what):
    print(f"\n== {who}: {what}")


def try_publish(doc, who, tab, lines, links, day, **kw):
    try:
        print("  ", d.publish(doc, who, tab, lines, links, day, **kw))
        return True
    except (ValueError, PermissionError) as e:
        print(f"   NOT WRITTEN: {e}")
        return False


def sec(status, ms, prog, extra=()):
    return [du.STATUSES[status], f"Next milestone: {ms}", f"Progress: {prog}", *extra]


def day1(doc):
    # Goldberg and Chema: engineers who own a tab are turned away, nothing written.
    for eng, upd in (("Goldberg", "Kyle"), ("Chema", "Kui")):
        rev = du.read_doc(doc)["revisionId"]
        step(eng, '"do my daily update"')
        assert d.is_engineer(du.read_doc(doc), eng)
        print(f"   Review: you own a tab but {upd} is its updater. Draft a note to {upd}? yes")
        print(f"   Draft (not sent): \"Hi {upd}, for today's update on my initiative: ...\" Nothing written, no config saved.")
        assert du.read_doc(doc)["revisionId"] == rev
        print("   doc revision unchanged")

    # Sahil covers Fast Harness for Kyle before Kyle runs.
    step("Sahil", '"also update Fast Harness Default for Kyle"')
    try_publish(doc, "Sahil", "Fast Harness Default (John Irby)",
                sec("🟢", "Fast becomes the default, Tue Nov 10", "Slice 3 merged and slice 4 is in review (merge request !371)."),
                [(2, "merge request !371", L("mr/371"))], FRI, cover_for="Kyle")

    # Kyle: traps first (vague date, wrong weekday), then the corrected draft; one write collides with Kui.
    step("Kyle", '"do my daily update"')
    try_publish(doc, "Kyle", "Composer UX (AlexD)",
                sec("🟡", "Product release sign-off, this week", "Product said they will start sign-off soon (chat)."),
                [(2, "chat", L("chat/ux/20"))], FRI)
    try_publish(doc, "Kyle", "Composer Planning APIs (Chandra)",
                sec("🟢", "Internal release, Wed Nov 10", "The Composer merge request merged (merge request !455)."),
                [(2, "merge request !455", L("mr/455"))], FRI)
    print("   (agent fixes both drafts, then shows the review; Kyle: publish)")
    try_publish(doc, "Kyle", "Composer UX (AlexD)",
                sec("🟡", "Product release sign-off, Fri Nov 13", "Product has not started sign-off; Josh is writing the experience pitch (chat).",
                    ["Green when: Product starts sign-off."]),
                [(2, "chat", L("chat/ux/20"))], FRI)

    def kui_edits():  # another leader writes to the doc between Kyle's read and write
        build.set_headline(doc, "Enterprise Automation (Kui)",
                           "🟡 At risk · The restructure comms plan still has no agreed date; the GenAI upgrade holds for Wed Nov 11. (Fri Nov 6)")
        print("   (Kui published the Enterprise Automation headline between Kyle's read and write)")

    try_publish(doc, "Kyle", "Composer Planning APIs (Chandra)",
                sec("🟢", "Internal release, Tue Nov 10", "The Composer merge request merged (merge request !455)."),
                [(2, "merge request !455", L("mr/455"))], FRI, between=kui_edits)
    print("   Goldberg sent Kyle a note: nightly run moved to Tue Nov 10 (newer than the meeting notes; used it).")
    try_publish(doc, "Kyle", "Composer Evals (Goldberg)",
                sec("🟡", "First full nightly eval run, Tue Nov 10", "The nightly run moved a day while a flaky suite is fixed (chat).",
                    ["Green when: the nightly run passes once."]),
                [(2, "chat", L("chat/evals/21"))], FRI)
    try_publish(doc, "Kyle", "Composer Resiliency (Joo)",
                sec("🟡", "Shared cache design approved, Wed Nov 11", "Joo posted the design doc for review (doc).",
                    ["Green when: the cache design is approved."]),
                [(2, "doc", L("doc/cache"))], FRI)
    r = d.publish(doc, "Kyle", "Fast Harness Default (John Irby)",
                  sec("🟢", "Fast becomes the default, Tue Nov 10", "Slice 4 went to review (merge request !371)."),
                  [(2, "merge request !371", L("mr/371"))], FRI)
    print("  ", r, "\n   Kyle: keep Sahil's section. Nothing written.")
    build.set_headline(doc, "Composer (Kyle)",
                       "🟡 At risk · The Evals nightly run moved to Tue Nov 10 and the Resiliency cache design needs approval by Wed Nov 11; Planning APIs and Fast Harness hold for Tue Nov 10. (Fri Nov 6)")

    # Sahil: raw URL trap, then fixed; Federated milestone met today.
    step("Sahil", '"do my daily update"')
    try_publish(doc, "Sahil", "Federated Agent Studio (Nima)",
                sec("🟢", "Federation pilot with two partners, Fri Nov 20", "All 5 smoke tests pass (https://example.test/mr/121)."),
                [(2, "example", L("mr/121"))], FRI)
    try_publish(doc, "Sahil", "Federated Agent Studio (Nima)",
                sec("🟢", "Federation pilot with two partners, Fri Nov 20", "All 5 smoke tests pass, so the Fri Nov 6 milestone is done (merge request !121)."),
                [(2, "merge request !121", L("mr/121"))], FRI)
    try_publish(doc, "Sahil", "AI Control Plane (Sahil)",
                sec("🟢", "Policy engine for the pilot, Fri Nov 13", "The policy engine's test environment came up two days early (chat)."),
                [(2, "chat", L("chat/acp/22"))], FRI)
    try_publish(doc, "Sahil", "Agent Studio Quality (Mahima)",
                sec("🟢", "Flaky test count under 5, Fri Nov 13", "Flaky tests are down to 6 (Jira AP-4301)."),
                [(2, "Jira AP-4301", L("jira/AP-4301"))], FRI)
    build.set_headline(doc, "Agents (Sahil)",
                       "🟢 On track · Federation smoke tests all pass and the pilot is set for Fri Nov 20; the policy engine holds for Fri Nov 13. (Fri Nov 6)")

    # Kui: own tabs; refused on Akhilesh's tab; AI Platform headline is Kui's.
    step("Kui", '"do my daily update"')
    try_publish(doc, "Kui", "Team Restructure (Kui)",
                sec("🟡", "Comms plan to the two teams, No date set yet", "Leads reviewed the comms plan; Kui is setting a date (doc).",
                    ["Green when: the comms plan has an agreed date."]),
                [(2, "doc", L("doc/restructure"))], FRI)
    try_publish(doc, "Kui", "GenAI Skills Model Upgrades (Chema)",
                sec("🟢", "Production rollout, Wed Nov 11", "Chema scheduled the rollout window (chat)."),
                [(2, "chat", L("chat/genai/23"))], FRI)
    step("Kui", '"update Deep Agents too, the date moved"')
    try_publish(doc, "Kui", "Deep Agents (Akhilesh)",
                sec("🟡", "Kata container sandboxes in production, Fri Nov 13", "x (chat)."), [(2, "chat", L("c"))], FRI)

    # Akhilesh in Pacific time, Thu 9:40pm PT = Fri 12:40am ET.
    step("Akhilesh", '"do my daily update" at Thu Nov 5, 9:40 PM PT')
    day = d.et_date(dt.datetime(2026, 11, 5, 21, 40, tzinfo=ZoneInfo("America/Los_Angeles")))
    print(f"   section date (ET): {du.label(day, True)}")
    try_publish(doc, "Akhilesh", "Deep Agents (Akhilesh)",
                sec("🟡", "Kata container sandboxes in production, Fri Nov 13", "Owen confirmed the sandbox scope; the date is still Fri Nov 13 (chat).",
                    ["Green when: Kata container sandboxes have a committed date."]),
                [(2, "chat", L("chat/deep/24"))], day)
    try_publish(doc, "Akhilesh", "Dev MCP / Tools (Akhilesh)",
                sec("🟢", "Jake's hackathon on the new software development kit, Tue Nov 17", "The port finished, so the Fri Nov 6 milestone is done (merge request !340)."),
                [(2, "merge request !340", L("mr/340"))], day)
    try_publish(doc, "Akhilesh", "API Desk (Akhilesh)", sec("⚪", "Restart after Dev MCP, Mon Nov 30", "No change since Thu Nov 5.",
                    ["Green when: Dev MCP / Tools frees up the team to restart."]), [], day)
    print("   EBC Support has no sources set up: nothing written; review asks Akhilesh for its sources.")

    # Scott: people-sensitive trap, then fixed.
    step("Scott", '"do my daily update"')
    try_publish(doc, "Scott", "AI Engineering Hiring (Scott)",
                sec("🟢", "Close the two open roles, Fri Nov 20", "Priya Raman accepted our offer (email)."),
                [(2, "email", L("mail/hiring/25"))], FRI)
    try_publish(doc, "Scott", "AI Engineering Hiring (Scott)",
                sec("🟢", "Close the two open roles, Fri Nov 20", "One of the two open roles is filled (email)."),
                [(2, "email", L("mail/hiring/25"))], FRI)
    try_publish(doc, "Scott", "Chennai Team Onboarding (Chandra)",
                sec("🟡", "All eight engineers set up, Wed Nov 11", "Seven of eight engineers have VPN tokens (chat).",
                    ["Green when: the last engineer has a VPN token."]),
                [(2, "chat", L("chat/chennai/26"))], FRI)
    try_publish(doc, "Scott", "Claude Code Pilot (Scott)",
                sec("🟢", "Org-wide rollout decision, Fri Nov 13", "Kui sent the Enterprise Automation names (chat).",
                    ["Confidence: Not confident"]),
                [(2, "chat", L("chat/ccp/27"))], FRI)
    print("   Scott: keep 🟢 and Not confident (the names are in, but legal review may slip). Publish.")
    try_publish(doc, "Scott", "Claude Code Pilot (Scott)",
                sec("🟢", "Org-wide rollout decision, Fri Nov 13", "Kui sent the Enterprise Automation names (chat).",
                    ["Confidence: Not confident"]),
                [(2, "chat", L("chat/ccp/27"))], FRI, confirm_mismatch=True)
    build.set_headline(doc, "Automation-wide (Scott)",
                       "🟡 At risk · Chennai onboarding is one VPN token short of the Wed Nov 11 date; one open role is filled. (Fri Nov 6)")
    step("Kui", '"do my daily update" (area tab only: AI Platform headline from Akhilesh\'s tabs)')
    build.set_headline(doc, "AI Platform (Kui)",
                       "🟡 At risk · Deep Agents waits on Kata container sandboxes for Fri Nov 13; the Dev MCP port is done, with Jake's hackathon Tue Nov 17. (Fri Nov 6)")
    print("   AI Platform headline refreshed")


def day2(doc):
    step("Kyle", '"do my daily update"')
    print("  ", d.publish(doc, "Kyle", "Composer Evals (Goldberg)",
                          sec("🟡", "First full nightly eval run, Tue Nov 10", "The flaky suite is fixed and the run is scheduled for tonight (chat).",
                              ["Green when: the nightly run passes once."]),
                          [(2, "chat", L("chat/evals/30"))], MON))
    step("Goldberg (a person, in the doc)", "edits Kyle's Evals sentence by hand")
    m.replace_in_para(doc, next(i.tab_id for i in du.model(du.read_doc(doc))[2] if i.name == "Composer Evals"),
                      "the run is scheduled for tonight", "the first run is booked for 8pm ET tonight")
    step("Kyle", '"do my daily update" again, with a new fact')
    edits = d.hand_edits(doc, "Kyle", "Composer Evals (Goldberg)", MON)
    print(f"   Review: a person changed these lines since you published: {edits}. Keep their wording? yes")
    assert edits, "hand edit not detected"
    kept = edits[0].replace("Progress: ", "")
    print("  ", d.publish(doc, "Kyle", "Composer Evals (Goldberg)",
                          sec("🟡", "First full nightly eval run, Tue Nov 10", kept.replace(" (chat).", "; Planning APIs passed quality engineering sign-off (chat)."),
                              ["Green when: the nightly run passes once."]),
                          [(2, "chat", L("chat/evals/30"))], MON))
    build.set_headline(doc, "Composer (Kyle)",
                       "🟡 At risk · The first full Evals nightly run is tonight, ahead of Tue Nov 10; the Resiliency cache design still needs approval by Wed Nov 11. (Mon Nov 9)")
    step("Sahil", '"do my daily update" (nothing changed on one tab)')
    try_publish(doc, "Sahil", "Agent Studio Quality (Mahima)", sec("🟢", "Flaky test count under 5, Fri Nov 13", "No change since Fri Nov 6."), [], MON)
    build.set_headline(doc, "Agents (Sahil)",
                       "🟢 On track · Flaky tests hold at 6 against the Fri Nov 13 target; the federation pilot holds for Fri Nov 20. (Mon Nov 9)")


def overview1(doc):
    build.set_thirty_seconds(doc, [
        ("🟡", "Composer Resiliency (Joo)", "the shared cache design needs your approval by Wed Nov 11."),
        ("🟡", "Composer Evals (Goldberg)", "the first full nightly run moved a day, to Tue Nov 10."),
        ("🟡", "Composer UX (AlexD)", "Product has not started release sign-off for Fri Nov 13."),
        ("🟢", "Federated Agent Studio (Nima)", "all 5 smoke tests pass; the partner pilot is set for Fri Nov 20."),
        ("🟢", "Dev MCP / Tools (Akhilesh)", "the software development kit port finished; Jake's hackathon is Tue Nov 17."),
    ])
    build.set_decisions(doc, "Medhat", [["Approve the shared cache design", "Joo's cache work is waiting on it",
                                        "Approve it, with Scott", "Wed Nov 11", "Scott"]], [L("doc/cache-design")])


def overview2(doc):
    build.set_thirty_seconds(doc, [
        ("🟡", "Composer Resiliency (Joo)", "the shared cache design still needs your approval by Wed Nov 11; Sahil now updates this tab."),
        ("🟡", "Composer Evals (Goldberg)", "the flaky suite is fixed and the first nightly run is tonight, 8pm ET."),
        ("🟡", "Composer UX (Chandra)", "Chandra now owns it; Product sign-off is still due Fri Nov 13."),
        ("🟢", "Composer Telemetry (Joo)", "new initiative; the dashboard goes live Fri Nov 20."),
        ("🟢", "Team Restructure (Kui)", "done Mon Nov 9; both teams now work in the new structure."),
    ])


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "create":
        print(build.create("E2E TEST exploratory daily update", "Automation", "Scott", "Medhat", STRUCTURE, dt.date(2026, 11, 5)))
    elif cmd in ("day1", "day2", "overview1", "overview2"):
        globals()[cmd](sys.argv[2])
