"""Offline checks for the status rules, the pre-publish check, Missing a plan, milestone labels and the migration
mapping. No doc and no network.

    python3 rules_test.py
"""
import datetime as dt
import os
import sys

os.environ.setdefault("DU_TODAY", "2026-11-06")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import daily  # noqa: E402
import dudoc as du  # noqa: E402
import migrate  # noqa: E402

FAILS = []
D = dt.date


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


class Sec:
    def __init__(self, date, milestone, lines=(), status="🟡"):
        self.date, self.milestone = date, milestone
        self.lines = [(f"Next milestone: {milestone}", None)] if milestone else []
        self.lines = [(status, None)] + self.lines + [(t, None) for t in lines]

    def line(self, p):
        return next((t for t, _ in self.lines if t.startswith(p)), None)

    @property
    def status(self):
        return self.lines[0][0][:1]

    unconfirmed = False

    @property
    def no_change(self):
        return any(t.startswith("Progress: No change since") for t, _ in self.lines)


class Init:
    def __init__(self, name, sections, owner="Ann"):
        self.name, self.owner, self.sections, self.tab_id = name, owner, sections, "t." + name

    def newest(self, attr=None):
        return next((s for s in self.sections if attr is None or getattr(s, attr)), None)


def kinds(probs):
    return [("warn" if p.startswith("warn:") else "block") + ":" + p.split(":", 1)[-1].strip()[:30] for p in probs]


def main():
    base = ["🟡 At risk", "Next milestone: Fast becomes the default engine in the Composer release, Tue Nov 10",
            "Progress: All known work merged (meeting notes).", "Blocked on: None.", "Green when: the bug bash closes."]

    # Status rules: a missing date is not a colour.
    p = daily.checks(["🟢 On track", "Next milestone: Work intake inbox for every group, No date set yet",
                      "Progress: No change since Thu Nov 5.", "Blocked on: None."], [])
    check("green with no date is allowed", not daily.blocking(p), p)
    check("no date is a warning for the review", any("no date" in x for x in p if x.startswith("warn:")), p)
    p = daily.checks(["🟢 On track", "Progress: No change since Thu Nov 5.", "Blocked on: None."], [])
    check("no next milestone is a warning", any("no next milestone" in x for x in p if x.startswith("warn:")), p)

    # Confidence is gone.
    p = daily.checks(base[:2] + ["Confidence: Not confident"] + base[2:], [])
    check("a Confidence line blocks the write", any("Confidence" in x for x in daily.blocking(p)), p)
    norm = du.normalize(["🟡", base[1][0:], "Confidence: Slightly confident", base[2], base[3], base[4]])
    check("normalize drops Confidence", not any(x.startswith("Confidence:") for x in norm), norm)

    # Stale date carried forward (the Fast Harness case).
    prev = Sec(D(2026, 11, 5), "Fast becomes the default engine in the Composer release, Tue Nov 10")
    moved = base[:2] + ["Progress: All known work merged (meeting notes). The team moved the internal release to "
                        "Thu Nov 12 (meeting notes)."] + base[3:]
    p = daily.checks(moved, [], prev=prev)
    check("carried date with 'moved' in Progress warns", any("carried from Thu Nov 5" in x for x in p), p)
    later = base[:2] + ["Progress: The internal release is now on Thu Nov 12 (meeting notes)."] + base[3:]
    p = daily.checks(later, [], prev=prev)
    check("carried date with a later date in Progress warns", any("later date (Thu Nov 12)" in x for x in p), p)
    fresh = ["🟡 At risk", "Next milestone: Fast becomes the default engine in the Composer release, Thu Nov 12",
             "Progress: The team moved the internal release to Thu Nov 12 (meeting notes).", "Blocked on: None.",
             "Green when: x."]
    p = daily.checks(fresh, [], prev=prev)
    check("an updated date does not warn", not any("carried" in x for x in p), p)
    p = daily.checks(base, [], prev=prev)
    check("an unchanged date with nothing moved does not warn", not any("carried" in x for x in p), p)

    # Hard stops still hold.
    p = daily.checks(base[:2] + ["Progress: See https://example.com (chat)."] + base[3:], [])
    check("a raw URL blocks", any("raw URL" in x for x in daily.blocking(p)), p)
    p = daily.checks(base[:2] + ["Progress: All known work merged."] + base[3:], [])
    check("a line with no link or source label blocks", any("no link" in x for x in daily.blocking(p)), p)
    p = daily.checks(base[:2] + ["Progress: Priya Raman accepted our offer (email)."] + base[3:], [], known_names=["Priya"])
    check("a people-sensitive line blocks", any("people-sensitive" in x for x in daily.blocking(p)), p)
    p = daily.checks(base[:2] + ["Progress: It moved to next week (chat)."] + base[3:], [])
    check("a vague date blocks", any("vague" in x for x in daily.blocking(p)), p)
    p = daily.checks(["🟢 On track", "Next milestone: Ship, Fri Nov 6", "Progress: Done (chat).", "Blocked on: None.",
                      "Green when: x."], [])
    check("a green section with Green when blocks", any("Green when" in x for x in daily.blocking(p)), p)

    # No false alarms from ordinary words.
    p = daily.checks(base[:2] + ["Progress: It missed the release candidate cut, and the dashboard offers the new "
                                 "agent (chat)."] + base[3:], [], known_names=["Scott", "Kyle"])
    check("'release candidate' and 'offers the' are not people-sensitive", not daily.blocking(p), p)
    p = daily.checks(base[:2] + ["Progress: Scott made Kyle an offer (email)."] + base[3:], [], known_names=["Scott", "Kyle"])
    check("a known person next to 'offer' still blocks", any("people-sensitive" in x for x in daily.blocking(p)), p)
    p = daily.checks(base[:2] + ["Progress: Quality engineering (QE) signed off; QE found nothing (chat)."] + base[3:], [])
    check("a spelled-out acronym is not flagged", not any("shorthand" in x for x in p), p)
    p = daily.checks(base[:2] + ["Progress: The store moved onto the new cache on Fri Nov 6 (chat)."] + base[3:], [], prev=prev)
    check("'moved' that is not about timing does not warn", not any("carried" in x for x in p), p)

    # Missing a plan.
    today = D(2026, 11, 6)
    inits = [
        Init("Work Intake", [Sec(D(2026, 11, 6), None, ["Progress: No change since Thu Nov 5."]),
                             Sec(D(2026, 11, 5), "One triaged inbox, No date set yet"),
                             Sec(D(2026, 10, 20), "One triaged inbox, No date set yet"),
                             Sec(D(2026, 10, 15), "Inbox pilot, Fri Oct 16")]),
        Init("API Desk", [Sec(D(2026, 11, 5), "No date set yet")]),
        Init("Dated", [Sec(D(2026, 11, 5), "Ship, Mon Nov 9")]),
        Init("Paused", [Sec(D(2026, 11, 5), "Start, No date set yet", status="⚪")]),
        Init("Finished", [Sec(D(2026, 11, 5), "Ship, Thu Nov 5", ["Progress: Done Thu Nov 5: shipped (chat)."])]),
        Init("Done milestone", [Sec(D(2026, 11, 5), "Ship, Mon Nov 2, done Thu Nov 5.")]),
    ]
    rows = {i.name: (what, since) for i, what, since in du.missing_plan(inits, today)}
    check("Missing a plan lists only open initiatives without a dated milestone",
          sorted(rows) == ["API Desk", "Work Intake"], sorted(rows))
    check("Since is the start of the undated run", rows.get("Work Intake", (0, 0))[1] == D(2026, 10, 20), rows)
    check("'No date set yet' alone reads as no next milestone", rows.get("API Desk", ("",))[0] == "No next milestone", rows)
    check("an undated milestone reads as no date", rows.get("Work Intake", ("",))[0] == "Milestone has no date", rows)
    import overview
    cell = overview.missing_cells(inits[0], "Milestone has no date", D(2026, 10, 20), today)
    check("over two weeks is marked", cell[3] == "Tue Oct 20 (over 2 weeks)", cell)

    # Short labels for Next 2 weeks.
    full = ("Composer's shared session store runs on Cache-as-a-Service (CaaS) in production, so restarts lose "
            "no user work")
    check("a long milestone is never cut", du.commitment(full + ", Thu Nov 12") == full, du.commitment(full + ", Thu Nov 12"))
    p = daily.checks(["🟢 On track", f"Next milestone: {full}, Thu Nov 12", "Progress: Merged (chat).", "Blocked on: None."], [])
    check("a long milestone is a warning to reword it", any("is long" in x for x in p if x.startswith("warn:")), p)
    p = daily.checks(["🟢 On track", "Next milestone: Restart-safe Composer sessions, Thu Nov 12", "Progress: Merged (chat).",
                      "Blocked on: None."], [])
    check("a short milestone does not warn", not any("is long" in x for x in p), p)
    check("a short milestone keeps its words", du.commitment("Pilot live, Fri Nov 13") == "Pilot live")

    # Separate Next milestone and Date columns.
    sp = du.split_milestone
    check("split a dated milestone", sp("Pilot live, Fri Nov 13") == ("Pilot live", "Fri Nov 13"))
    check("split an undated milestone", sp("Work intake inbox, No date set yet") == ("Work intake inbox", "No date set yet"))
    check("split a bare 'No date set yet'", sp("No date set yet") == ("None", "No date set yet"))
    check("split keeps a note after no date", sp("Boost confirmed, No date set yet (waiting on Sanat)") ==
          ("Boost confirmed", "No date set yet (waiting on Sanat)"))
    check("split a done milestone", sp("Endpoints delivered, done Thu Nov 5") == ("Endpoints delivered", "done Thu Nov 5"))
    check("row_cells makes five cells for the new table",
          du.row_cells(["A", "Ann", "🟢 On track", "Ship, Mon Nov 9"], 5) == ["A", "Ann", "🟢 On track", "Ship", "Mon Nov 9"])
    check("row_cells leaves an old four-column table alone", du.row_cells(["A", "Ann", "🟢", "Ship, Mon Nov 9"], 4)[3] == "Ship, Mon Nov 9")
    check("a split row reads back as the full milestone",
          du.milestone_date(du.Area.row_milestone(["A", "Ann", "🟢", "Ship", "Mon Nov 9"])) == D(2026, 11, 9))

    # Headlines carry no colour.
    import build
    check("a leading colour is removed from a headline",
          build.strip_colour("🟡 At risk · Claude 5.5 is due Fri Nov 13. (Thu Nov 5)") == "Claude 5.5 is due Fri Nov 13. (Thu Nov 5)")
    check("a headline without colour is unchanged", build.strip_colour("Plain (Fri Nov 6)") == "Plain (Fri Nov 6)")

    # Migration colour mapping.
    m = migrate.new_status
    check("yellow, slightly confident, not blocked -> green", m("🟡", "Slightly confident", "Blocked on: None.") == "🟢")
    check("yellow, not confident -> yellow", m("🟡", "Not confident", "Blocked on: None.") == "🟡")
    check("yellow, blocked on another team -> yellow", m("🟡", "Slightly confident", "Blocked on: Sanat: confirm (from Scott).") == "🟡")
    check("green, not confident -> yellow", m("🟢", "Not confident", "Blocked on: None.") == "🟡")
    check("red and paused unchanged", m("🔴", "Very confident", "Blocked on: None.") == "🔴" and m("⚪", None, None) == "⚪")
    check("no Confidence and not blocked keeps yellow (no evidence)", m("🟡", None, "Blocked on: None.") == "🟡")

    print(f"\n{'ALL PASSED' if not FAILS else str(len(FAILS)) + ' FAILED: ' + ', '.join(FAILS)}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
