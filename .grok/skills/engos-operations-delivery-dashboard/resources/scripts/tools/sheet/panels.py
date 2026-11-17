"""Non-Metrics tabs: Thresholds, Roster, Individual, README, Data_Dictionary, Prompt_Library, canvas_source, Run_Log, Dashboard text."""
import csv, json, os
import dash_text as DDB
from sheetlib import col_letter, a1
from tabs import SPECS, date_serial, serial


def thresholds_rows(cfg):
    rows = [["name", "value", "unit", "description"]]
    with open(cfg["paths"]["thresholds"], newline="") as f:
        for r in csv.DictReader(f):
            v = float(r["value"]) if "." in r["value"] else int(r["value"])
            rows.append([r["name"], v, r["unit"], r["description"]])
    return rows


def roster_rows(R):
    hdr = ["chart_name", "manager", "title", "group", "team", "start_date", "end_date", "note"]
    rows = [hdr]
    for r in sorted(R.rows, key=lambda x: x["chart_name"]):
        rows.append([r["chart_name"], r["manager"], r["title"], r["group"], r["team"], r["start_date"], r["end_date"], r["note"]])
    return rows


def history_rows(R):
    rows = [["person", "effective_from", "effective_to", "group", "team"]]
    for p in sorted(R.hist):
        for h in R.hist[p]:
            rows.append([h["person"], h["effective_from"], h["effective_to"], h["group"], h["team"]])
    return rows


# reader-facing column headers of the visible tabs (inbox 104: no field names, no underscores); the code keeps the field names
IND_HEADERS = {
    "person": "Person", "group": "Group", "team": "Team", "manager": "Manager", "end_date": "End date", "wip": "Work in progress", "blocked": "Blocked items",
    "oldest_ip_age_days": "Oldest in-progress item (days)",
    "wi_ours": "Tickets: ours", "wi_ours_pct": "Tickets: ours (share)", "wi_other": "Tickets: Other", "wi_other_pct": "Tickets: Other (share)",
    "wi_untagged": "Tickets: untagged", "wi_untagged_pct": "Tickets: untagged (share)", "wi_other_by": "Other tickets, by owning SBU or Group",
    "ch_ours": "Changes: ours", "ch_ours_pct": "Changes: ours (share)", "ch_other": "Changes: Other", "ch_other_pct": "Changes: Other (share)",
    "ch_untagged": "Changes: untagged", "ch_untagged_pct": "Changes: untagged (share)", "ch_other_by": "Other changes, by owning SBU or Group", "history": "History basis",
}
LOG_HEADERS = {"run_at_utc": "Run at (UTC)", "source": "Source", "rows": "Rows", "api_calls": "API calls", "retries_429": "Retries (429)", "final_errors": "Final errors", "note": "Note"}
DEF_HEADERS = ["Tab", "Column or metric", "Kind", "Unit", "Definition", "Source"]
SRC_HEADERS = {"metric": "Metric", "source_query": "Source query", "as_of_utc": "As of (UTC)", "defined_in": "Defined in"}

IND_COLS = [
    ("person", "Roster name (display name from the org chart)"),
    ("group", "Current Group (Other when the person has none)"),
    ("team", "Current Team (No team when the person has none)"),
    ("manager", "Manager, from the roster"),
    ("end_date", "Roster end date. Blank for everyone today: no person on the roster has an end date"),
    ("wip", "Jira work items in progress now"),
    ("blocked", "Open work items in a blocked status now"),
    ("oldest_ip_age_days", "Oldest in-progress item, days since start"),
    ("wi_ours", "Their work items (open now, or finished in the last 12 months, main series) that are ours by the ladder: count"),
    ("wi_ours_pct", "Share of their work items that are ours"),
    ("wi_other", "Their work items tagged outside Automation (count)"),
    ("wi_other_pct", "Share of their work items that are Other"),
    ("wi_untagged", "Their work items with no Team, Group or SBU tag (count); never in team numbers"),
    ("wi_untagged_pct", "Share of their work items that are untagged"),
    ("wi_other_by", "The Other work items by owning SBU, or Group when no SBU is set (exact counts)"),
    ("ch_ours", "Their merged, counted, ordinary changes in the last 12 months that are ours: by the primary linked ticket's tags at the merge date, or by the author's roster Group when no ticket is linked (count)"),
    ("ch_ours_pct", "Share of their changes that are ours"),
    ("ch_other", "Their changes whose linked ticket is tagged outside Automation (count)"),
    ("ch_other_pct", "Share of their changes that are Other"),
    ("ch_untagged", "Their changes whose linked ticket has no tag (count)"),
    ("ch_untagged_pct", "Share of their changes that are untagged"),
    ("ch_other_by", "The Other changes by owning SBU, or Group when no SBU is set (exact counts)"),
    ("history", "History basis: the roster is exact from the first snapshot (2026-11-08); the 12-month period starts earlier, so these counts are approximate"),
]


def _sup(n):
    """AC29: a count under 5 shows as '<5' (zero stays 0)"""
    return "<5" if 0 < n < 5 else n


def individual_rows(R, asof_dt, comp=None, first_snapshot="2026-11-08", window_start="", gids=None):
    """AC29 (v1.33, A56; A76: exact counts and shares on the person rows): one row per roster person: name, Group, Team, manager; work in progress, blocked and the oldest in-progress age (formulas); the composition of their tickets and changes in the period
    (ours, Other by owning SBU or Group, untagged) as counts and shares; no volume ranking, rows sort by name; exact counts and shares; no usernames."""
    comp = comp or {}
    hdr = [IND_HEADERS.get(c[0], c[0]) for c in IND_COLS]
    rows = [hdr]
    people = sorted(R.rows, key=lambda x: x["chart_name"])
    approx = "approximate" if (not window_start or window_start < first_snapshot) else "exact"
    for i, p in enumerate(people):
        rr = i + 2
        name = p["chart_name"]
        g, t = R.tg(name, asof_dt)
        A = f"$A{rr}"
        c = comp.get(name, {})
        row = [name, g, t, p.get("manager", ""), p["end_date"],
               f"=COUNTIFS(ji_owner,{A},ji_wip,1)",          # A76: person rows show exact counts and shares
               f"=COUNTIFS(ji_owner,{A},ji_blocked,1)",
               f'=IFERROR(MAXIFS(ji_start_age_days,ji_owner,{A},ji_wip,1),"")']
        for kd, pre in (("wi", "wi_"), ("ch", "ch_")):
            o, ot, u = c.get(pre + "ours", 0), c.get(pre + "other", 0), c.get(pre + "untagged", 0)
            base = o + ot + u
            by = c.get("other_by" if kd == "wi" else "ch_other_by", {})
            pct = lambda n, base=base: (round(100.0 * n / base, 1) if base > 0 else "")          # A76: exact shares (a person with no tickets or changes has no share)
            bys = ", ".join(f"{k or 'Other'} {v}" for k, v in sorted(by.items()))          # A76: exact counts in the per-person breakdown too
            lk = (lambda v, g=(gids or {}).get("W" if kd == "wi" else "C"): f'=HYPERLINK("#gid={g}&range=A1",{json.dumps(v) if isinstance(v, str) else v})' if g else v)          # A74: Other and untagged counts link to the item tab (Kind = other / untagged), not narrowed per person
            row += [o, pct(o), lk(ot), pct(ot), lk(u), pct(u), bys]
        row.append(f"{approx}: exact from {first_snapshot}")
        rows.append(row)
    return rows


CANVAS_COLS = ["open_work_items", "wip", "in_progress_no_owner", "stale_share_of_open", "done_last_week_main", "cycle_median_days",
               "cycle_p85_days", "merged_last_week", "open_to_merge_median_days", "first_review_median_hours", "A1_rate", "J1_pass_rate",
               "C1_pass_rate", "C3_pass_rate", "open_changes"]


def canvas_rows(G):
    """Formulas pointing at Team and Group level cells of Metrics only (no SBU-person data, no person rows). The left table is the existing level table;
    two blocks to its right carry the 6/12 data (D90): six12_* (long form: SBU, Group, Team x 7 metrics x 6 weeks and 12 months) and six12s_* (stat strip
    per entry and metric). Every cell is a formula over Metrics (m_612_long, m_612_stats)."""
    hdr = ["level", "group", "team"] + CANVAS_COLS
    rows = [hdr]
    for i, (lv, g, t) in enumerate(G.meta_lv):
        if lv == "SBU":
            continue
        r = G.lv_r0 + 2 + i
        rows.append([lv, g, t] + [f"=Metrics!{col_letter(G.meta_ci[c])}{r}" for c in CANVAS_COLS])
    # 6/12 blocks
    lr0, _, lr1, _ = G.names["m_612_long"]
    sr0, _, sr1, _ = G.names["m_612_stats"]
    long_hdr = ["six12_level", "six12_group", "six12_team", "six12_name", "six12_metric", "six12_period_type", "six12_period_label", "six12_period_start", "six12_value"]
    stat_hdr = ["six12s_level", "six12s_group", "six12s_team", "six12s_name", "six12s_metric", "six12s_last_week", "six12s_wow_pct", "six12s_avg_4w_before",
                "six12s_last_month", "six12s_mom_pct", "six12s_total_12m", "six12s_total_12m_basis"]
    width = len(hdr)
    n = max(len(rows), lr1 - lr0 + 1, sr1 - sr0 + 1)
    out = []
    for i in range(n):
        left = rows[i] if i < len(rows) else [""] * width
        if i == 0:
            lng, st = long_hdr, stat_hdr
        else:
            lm = lr0 + 1 + i            # Metrics row (1-based) of the i-th long row: header at lr0+1, first data row lr0+2
            lng = ([f"=Metrics!{c}{lm}" for c in "ABCDEFG"] + [f'=TEXT(Metrics!H{lm},"yyyy-mm-dd")', f"=Metrics!J{lm}"]) if lm <= lr1 + 1 else [""] * 9
            sm = sr0 + 1 + i
            st = [f"=Metrics!{col_letter(c)}{sm}" for c in range(12)] if sm <= sr1 + 1 else [""] * 12
        out.append(left + [""] + lng + [""] + st)
    return out


def run_log_rows(cfg, meta, stats, started):
    """One row per source: rows written, API calls, 429 retries, final errors (calls from each extractor's saved calls.json; pull only)."""
    rows = [[LOG_HEADERS[h] for h in ("run_at_utc", "source", "rows", "api_calls", "retries_429", "final_errors", "note")]]
    now = started
    C = meta["counts"]
    srcrows = {"jira": C["jira_issues"], "gitlab": meta.get("n_gitlab", ""), "github": meta.get("n_github", "")}
    for src, d in (("jira", cfg["paths"]["jira_dir"]), ("gitlab", cfg["paths"]["gitlab_dir"]), ("github", cfg["paths"]["github_dir"])):
        try:
            c = json.load(open(os.path.join(d, "calls.json")))
        except Exception:
            c = {}
        pick = lambda keys: next((c[k] for k in keys if k in c), 0)
        rows.append([now, src, srcrows[src], pick(("calls", "pull_calls", "calls_this_run")), pick(("r429", "retries_429", "retries")), pick(("errors", "final_errors", "failed")), "rows = issues or changes from this source; calls from the extractor's saved calls.json (pull only, D21)"])
    # every call that went through the GET-only wrapper, all callers (pull, verifier, tests): reported beside the pull totals (D21)
    lp = cfg["paths"].get("ro_log", "data/ro-calls.log")
    if os.path.exists(lp):
        tot = {}
        for line in open(lp, errors="ignore"):
            f = line.rstrip("\n").split("\t")
            if len(f) >= 5 and f[2] == "GET" and not f[4].startswith("REFUSED"):
                tot[f[1]] = tot.get(f[1], 0) + 1
        for tool, src in (("glab", "gitlab"), ("gh", "github")):
            rows.append([now, src + " (all callers)", "", tot.get(tool, 0), "", "", "every GET through the read-only wrapper (pull, verifier, tests); the pull-only figure is the row above (D21)"])
    for k, v in C.items():
        rows.append([now, "tab: " + k, v, 0, 0, 0, "rows written to the Sheet this run"])
    rows.append([now, "sheet build", "", stats["calls"], stats["r429"], stats["errors"], "gws calls made by this build"])
    for src, d in (("jira", cfg["paths"]["jira_dir"]), ("gitlab", cfg["paths"]["gitlab_dir"]), ("github", cfg["paths"]["github_dir"])):
        try:      # the last incremental pull of this source (AC35): its own row, from the extractor's calls_incremental.json
            c = json.load(open(os.path.join(d, "calls_incremental.json")))
        except Exception:
            continue
        pick = lambda keys: next((c[k] for k in keys if k in c), 0)
        rowsn = c.get("pulled") if src == "jira" else ((c.get("authored_updated", 0) + c.get("others_updated", 0)) if src == "gitlab" else c.get("prs_seen", 0))
        rows.append([now, src + " (incremental)", rowsn, pick(("calls",)), pick(("r429", "retries_429", "retries")), pick(("errors", "final_errors", "failed")),
                     "last incremental pull, as-of " + str(c.get("asof") or c.get("as_of") or "") + "; rows = items pulled or updated in that pull; calls from the extractor's calls_incremental.json"])
    rows.append([now, "as_of", meta["as_of"], "", "", "", "one as-of timestamp for the whole run"])
    return rows


README_LINES = [
    "{sheet_name}",
    "",
    "WHAT THIS IS",
    "One Sheet for the Head of Engineering and leaders. It shows what the {sbu_label} committed to and who owns it (Jira), what it delivered (merge requests and pull requests), and where the two agree or drift. Levels: SBU, Group, Team, Individual. Flow measures only (Shape Up); there are no estimates.",
    "",
    "AS-OF AND VERSION",
    "as_of_utc: see cell Metrics!B3 (named asof). Every age and window uses that one timestamp. All times are UTC. Weeks are ISO weeks (Monday start, UTC); the current partial week is excluded from weekly series.",
    "Roster as-of: {roster_asof} (latest effective date in Roster_History; the Roster tab lists the {roster_n} people; Roster_History has the dated team and group changes).",
    "",
    "SOURCES AND QUERIES",
    "{jira_source} {code_source} Source counts and call counts are in Log.",
    "Free text from Jira tickets and merge request or pull request titles and descriptions is never stored here. Only keys, numbers, lengths, and names of statuses, types, teams, and people.",
    "",
    "TABS",
    "Dashboard (last refresh, scorecard, then ten questions each with a chart, a plain table beside it and an answer card), Alerts (the items behind each alert), Individual, Thresholds (the only place a limit lives and the only tab you edit: column B), About (this tab), Definitions (what every number means), Sources (every metric, its source query and the as-of), Log (the last refresh and its call counts), Insights, Explore. Hidden and locked: Metrics (all formulas), canvas_source, Prompt_Library, Roster, Roster_History, Failing_Lists and the data tabs.",
    "",
    "DASHBOARD AND DETAIL",
    "The Dashboard shows ten question slots, in this order: D1 finishing as much as we start, D3 anything stuck, K1 blocked work, D4 shipping code, D5 code review speed, B1 bugs fixed against bugs created, customer incidents created and resolved, internal incidents created and resolved, I2 open incidents, M1 work mix by Work Category. Each has an Answer card under it: one sentence that is a formula over Metrics and Threshold cells; Each line chart has a one-line key under it (one entry per measure; weekly and monthly share a colour) and a plain table beside it. Each Items link opens its list on the Alerts tab or a Jira search (the count may differ, Jira is live); each item on Alerts has a link to its Jira issue, GitLab merge request or GitHub pull request. Charts that are not drawn (V1 to V13, D2, D6a, D6b, B2, I3, I4) keep their ranges on Metrics. Sources lists every metric with its source query and the as-of.",
    "THE SCORECARD. One row per question, in the order of the charts. Now is the number the answer card cites. Threshold says the limit in plain words; each limit is a cell on the Thresholds tab (column B): t_throughput_drop for finished and merged work, t_blocked_days, t_first_review_days, t_bug_net_weeks, t_incident_net_weeks, t_incident_open_days, and for the work mix t_cat_support_max, t_cat_ops_max and t_cat_features_min. Status is Needs attention (red) when Now breaks the limit, OK (green) when it does not, and No threshold set when the Thresholds cell is empty. The row for stuck work uses t_stuck_days (7 days): an item in progress longer than that is stuck. Each Threshold cell has a note with the rule.",
    "",
    "HIDDEN TABS",
    "Ten machinery tabs are hidden to keep the workbook readable: Metrics, Roster, Roster_History, Failing_Lists, Jira_Issues, Jira_Transitions, Daily_Status_Counts, Code_Changes, Code_Jira_Links, Code_Reviews. They are still read by the Dashboard and Individual formulas, by the ask path (gws reads hidden tabs), and by the checks and hashes. To see them: View, then Hidden sheets. People with comment-only access may not see hidden tabs.",
    "",
    "HOW TO ASK (for people and for AI)",
    "Ask in plain words, name the level and the measure. Examples: 'Which Groups have in-progress tickets with no owner?', 'What is the median cycle time for a Group?', 'How many open changes have waited past the review limit with no first review?' Prompt_Library has tested questions and their cited answers.",
    "",
    "ANSWER CONTRACT (AI readers must follow it)",
    "1. Cite the cell (tab and address, or the named range). 2. Quote the as-of timestamp. 3. State the definition from Data_Dictionary. 4. Decline to rank people or compare individuals. 5. Say 'not in the Sheet' for estimates, hill position, or anything the Sheet does not hold. 6. Never recompute a number: read the Metrics cell.",
    "",
    "WHO MAY USE THE INDIVIDUAL TAB",
    "Default (decision 9): leaders may use it to unblock and coach. It is not for ranking, leaderboards, or composite scores. Every individual number sits beside its counterpart numbers (for example WIP beside finished work). A rate for a person shows only when its denominator is at least the minimum in Thresholds (t_min_n); below that the cell shows the count and 'n under N'. The user can change this wording and the audience.",
    "",
    "KEY DEFINITIONS",
    "In progress with no owner is a problem: headline metric and top alert. Ownerless backlog (not started) is information only and never alerts. Ownerless means no assignee; Unmapped means an assignee who is not on the roster. Team and Group follow the person on the date of the event; a removed person stays in past weeks. No composite scores anywhere.",
    "Full definitions: Definitions. Thresholds are cells in Thresholds with names starting t_; no number for a threshold is typed in any formula. Dashboard attribution-health shares: ticket tiles are shares of all work items; the incident tile is a share of all incidents created in the last 12 months; the untagged tile is a share of the tickets credited to our people. Saved views (Data > Filter views) on Work items and Code changes hold the measure and the Group but never the period: add the period flag in the filter buttons. Editors: use Data > Filter views > Create new temporary filter view, or reset the saved view after.",
    "",
    "REFRESH",
    "One command from a plain shell: python3 tools/sheet/refresh.py --yes (or /engos-operations-delivery-dashboard refresh). No model call is involved. Insights and the Canvas are rebuilt only by their own commands.",
]



import re as _re
_CODE = r"(?:D[1-6][ab]?|V(?:1[0-3]|[1-9])[ab]?|K1|B[12]|T1|I[1-4][CI]?|P[1-5])"
_CODES = _re.compile(rf"\b{_CODE}\b")
_REF = r"(?:AC\d{1,3}[ab]?|A\d{2,3}[a-z]?|D\d{2,3})"          # internal criterion, ruling and decision numbers (AC44a, A36, D21): never shown to a reader


def scrub_codes(v):
    """slot codes (D1, V8, K1, B1, T1, I2, P5 ...) are working labels, not words a reader knows: strip them from every text a reader sees (AC44a).
    Removes '(D1)', '(D6a and D6b)', a leading 'D1: ', and any remaining bare code; tidies the spaces and punctuation left behind."""
    if not isinstance(v, str) or v.startswith("="):
        return v
    t = _re.sub(rf"\s*\((?:on Charts \(detail\):? ?)?{_CODE}(?:(?:,| and |/)\s*{_CODE})*\)", "", v)
    t = _re.sub(rf"^{_CODE}(?:(?: and |, |/){_CODE})*:\s*", "", t)
    t = _re.sub(rf"\b{_CODE}(?: and {_CODE})*\b:?\s*", "", t)
    t = _re.sub(r"\s*\((?:AC )?v1\.\d{1,2}(?: exception)?\)", "", t)          # version tags are not for readers: '(v1.28)', '(AC v1.14 exception)'
    t = _re.sub(r"\bv1\.\d{1,2}\b[:,]?\s*", "", t)
    for old_, new_ in (("Data_Dictionary", "Definitions"), ("Alert details", "Alerts"), ("Run_Log", "Log"), ("README", "About")):          # the tabs' reader-facing names
        t = _re.sub(rf"\b{old_}\b", new_, t)
    t = _re.sub(rf"\s*\({_REF}(?:(?:,| and |/)\s*{_REF})*\)", "", t)          # '(AC44a, AC44b)', '(A36)'
    t = _re.sub(rf",\s*{_REF}(?=\))", "", t)                                   # 'pull only, D21)'
    t = _re.sub(rf"\s*\b{_REF}\b", "", t)                                    # any bare number left
    t = _re.sub(r"\s{2,}", " ", t)
    t = _re.sub(r"\s+([,.;:)])", r"\1", t)
    t = _re.sub(r"\(\s*\)", "", t)
    t = t.strip()
    return (t[:1].upper() + t[1:]) if t and _CODES.search(v[:12] or "") else t


def scrub_grid(rows):
    return [[scrub_codes(x) for x in r] for r in rows]


def readme_rows(cfg, roster_asof="", roster_n=""):
    t = dict(cfg.get("texts", {}), roster_asof=roster_asof, roster_n=roster_n, sheet_name=cfg.get("sheet_name", "Dashboard"), sbu_label=cfg["jira"]["sbu_label"])
    return scrub_grid([[l.format(**t) if "{" in l else l] for l in README_LINES])


METRIC_DEFS = {
    "open_work_items": "Open (status category not Done) work items, excluding epics and initiatives",
    "open_containers": "Open epics and initiatives (shown separately)",
    "wip": "Work items in an In Progress category now",
    "open_not_started": "Open work items in the new (not started) category",
    "ownerless_open_work_items": "Open work items with no assignee (information only)",
    "ownerless_share_of_open": "Ownerless open work items divided by open work items",
    "stale_open_work_items": "Open work items not updated for more than t_jira_stale_days",
    "stale_share_of_open": "Stale open work items divided by open work items",
    "aging_wip_over_p85": "In-progress work items in progress (since start) for longer than t_stuck_days",
    "in_progress_no_owner": "In-progress work items with no assignee (headline problem)",
    "oldest_no_owner_age_days": "Oldest in-progress item with no owner, days since start",
    "done_last_week_main": "Main-series work items finished in the last complete week",
    "done_prior4_avg_main": "Average main-series finishes per week over the 4 weeks before the last complete week",
    "done_last4_avg_main": "Average main-series finishes per week over the last 4 complete weeks",
    "weeks_of_backlog": "Open work items divided by the last-4-week average of main-series throughput",
    "created_last_week": "Work items created in the last complete week",
    "throughput_drop_alert": "1 when last week's main throughput is below t_throughput_drop times the prior 4-week average",
    "cycle_n": "Finished main-series work items with a start (cycle-time population)",
    "cycle_median_days": "Median days, first start to final Done",
    "cycle_p85_days": "P85 days, first start to final Done (linear interpolation)",
    "lead_median_days": "Median days, created to final Done",
    "lead_p85_days": "P85 days, created to final Done",
    "merged_12m": "Changes merged in 12 months, counted once, all classes",
    "merged_normal_12m": "Of those, class normal",
    "merged_last_week": "Ordinary changes merged in the last complete week (counted once across GitLab and GitHub)",
    "merged_prior4_avg": "Average ordinary changes merged per week over the 4 weeks before the last complete week",
    "merge_drop_alert": "1 when last week's merged count is below t_throughput_drop times the prior 4-week average",
    "open_to_merge_median_days": "Median opened to merged days (draft time counts)",
    "open_to_merge_p85_days": "P85 opened to merged days",
    "first_review_median_hours": "Median hours opened to first review (merged changes with a review)",
    "merged_normal_no_review": "Merged normal changes with no first review",
    "open_changes": "Open changes now, counted once",
    "open_normal_changes": "Open changes of class normal",
    "open_age_median_days": "Median age in days of open changes",
    "open_age_p85_days": "P85 age in days of open changes",
    "open_age_max_days": "Maximum age in days of open changes",
    "reviews_per_week_12w": "Review events given per week by reviewers at this level, last 12 complete weeks (the headline)",
    "changes_reviewed_per_week_12w": "Distinct (change, reviewer) pairs with a review event, per week, last 12 complete weeks",
    "open_no_review_over_limit": "Open normal changes with no first review and older than t_first_review_days",
    "code_exempt_non_normal": "Merged or open changes not of class normal (exempt from C checks)",
    "jira_exempt_containers_open": "Open epics and initiatives (exempt from J checks)",
    "A1_linked": "Normal changes whose key state is linked",
    "A1_denominator": "Normal changes created in the 12-month window (open, merged, closed), counted once",
    "A1_rate": "A1 link rate = linked divided by normal changes",
    "A2_count": "In-progress code-type issues with no linked change activity within t_ip_stale_days (including none linked)",
    "A2_denominator": "In-progress code-type issues",
    "A2_rate": "A2 count divided by in-progress code-type issues",
    "A3_count": "Open work items whose linked changes are all merged (status lag)",
    "A3_denominator": "Open work items with at least one linked change",
    "A3_rate": "A3 count divided by its denominator",
    "A4_count": "Finished code-type work items with no merged linked change",
    "A4_denominator": "Finished code-type work items",
    "A4_rate": "A4 count divided by its denominator",
    "A5_count": "Merged normal changes with key state no_key (untracked work)",
    "A5_denominator": "Merged normal changes",
    "A5_rate": "A5 count divided by merged normal changes",
    "people_over_wip_limit": "People (Individual tab) whose in-progress count is above t_wip_per_person",
}
CHECK_DEFS = {
    "C1": "has a linked Jira key", "C2": "description at least 20 non-whitespace characters", "C3": "had a review before merge",
    "C4": "not merged by its author without a review (merged changes with a known merger)", "C5": "size at or below t_mr_size_lines, lockfiles and generated files excluded",
    "C6": "first review within t_first_review_days (merged or open normal changes; an open change with no review counts once it is older than the threshold)", "C7": "open and not stale (no activity beyond t_open_stale_days); drafts count when t_c7_include_drafts is 1",
    "C8": "draft not older than t_open_stale_days",
    "J1": "in progress has an owner", "J2": "in progress updated within t_ip_stale_days", "J3": "in progress not older than its Group's P85 cycle time",
    "J4": "finished work item has a resolution", "J5": "finished work item had an assignee at the final Done", "J6": "open work item has a parent epic or initiative",
}


def org_event_rows():
    """one plain-words line per org event (A57, A58, A60; no event ids, no ticket keys, counts only): how a bulk retag or a rename is treated when a ticket's tag is read at a past date"""
    import csv, os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "org_events.csv")
    if not os.path.exists(p):
        return []
    nm = {"team": "Team", "group": "Group", "sbu": "SBU"}
    out = []
    for e in csv.DictReader(open(p)):
        f = nm.get(e["field"], e["field"])
        if e["kind"] == "lineage" and e["to_value"]:
            d = f"The {f} {e['from_value']} is the same {f} as {e['to_value']} for every date (user ruling): tickets tagged {e['from_value']} count as {e['to_value']}, whatever the date."
        elif e["kind"] == "lineage":
            d = f"The {f} {e['from_value']} counts as ours through {e['valid_to']} (inclusive) and not after (user ruling): a ticket counts by the tag it had on the date being measured."
        else:
            frm = e["from_value"] or "no value"
            hrs = float(e["span_hours"] or 0)
            span = "in one moment" if hrs < 0.05 else f"within {hrs:.1f} hours"
            what = f"On {e['event_date'][:10]}, {e['ticket_count']} tickets had their {f} changed from {frm} to {e['to_value'] or 'no value'} {span}. "
            d = what + ("Counted as if the new value had always been there: a count for any earlier date uses the new value (restated)." if e["mode"] == "restate"
                        else "Each ticket keeps the value it had on the date being measured (the change is real, not restated).")
        out.append(["Org events", f"{f} change" if e["kind"] != "lineage" else f"{f} rename or end", "text", "", d, "Org-events table, built from the Jira change history and user rulings"])
    return out


KEY_LATE = ("Incident_Issues", "Other_Items")
IDENTITY_DEF_ROW = ["Identity", "(all columns)", "text", "", "One row per person of data/identity.csv, with that file's columns in file order (person, home username and source, Jira account id and email, GitLab username and id, GitHub login, each confidence and reason), then no GitHub login (yes when the GitHub login is blank) and as of (UTC) in row 2. Rebuilt from the file on every refresh. This is the one tab that shows names, usernames, emails and account ids besides Individual (AC84); Sources counts the flag.", "data/identity.csv"]


def dictionary_rows(G):
    rows = [list(DEF_HEADERS)]
    src = {"Jira_Issues": "Jira extract (filters named in README)", "Jira_Transitions": "Jira changelog", "Daily_Status_Counts": "Computed by script from Jira_Transitions",
           "Code_Changes": "Merge requests and pull requests by roster authors", "Code_Jira_Links": "Jira keys found in changes", "Code_Reviews": "GitLab approvals and notes, GitHub reviews", "State_History": "Computed by script: replay of Jira status and assignee changes", "Other_Items": "Computed by script from the Jira pull: tickets of roster people that are tagged outside Automation or untagged; counts only", "Incident_Issues": "Jira incident extract (projects EA and IA, any issue type) measured at the Sheet as-of (Metrics as_of_utc), not at the pull's own as-of; counts only, no titles or names"}
    late = []          # v1.43f: the Jira key rows of Incident_Issues and Other_Items sit AFTER the A3 row so that row 164 stays the A3 row (AC78 c, d411_remove); v1.43g: so does the Identity row
    for tab, (_, spec) in SPECS.items():
        for name, kind, unit, d in spec:
            (late if (tab in KEY_LATE and name == "key") else rows).append([tab, name, kind, unit, d, src[tab]])
    rows.append(list(DDB.DEF_ROW))          # D411: plain row at the same place in Data_Dictionary
    rows += late
    rows.append(list(IDENTITY_DEF_ROW))          # v1.43g AC84
    for name in G.meta_names:
        if name in METRIC_DEFS:
            d = METRIC_DEFS[name]
        else:
            k = name.split("_")[0]
            if k in CHECK_DEFS:
                suffix = name[len(k) + 1:]
                d = f"{k} ({CHECK_DEFS[k]}): {suffix.replace('_', ' ')}"
            elif name.startswith("backlog_age_"):
                d = "Open work items in the age bucket (days since created): " + name[len("backlog_age_"):].replace("_", " to ")
            else:
                d = name.replace("_", " ")
        rows.append(["Metrics (m_levels)", name, "num", "", d, "Formula over the data tabs and Thresholds"])
    rows += org_event_rows()
    for nm, d in [
        ("m_throughput", "V1 spec range, long form: week, series (SBU main, Won't Do, Duplicate, main per Group), count, rolling_avg (this week and 3 before). Header row is part of the range."), ("m_throughput_chart", "V1 chart range: formula-built wide pivot of m_throughput, one column per series (AC v1.14 exception)"),
        ("m_created_done", "V2: week, created, done"), ("m_cfd", "V3 spec range, long form: week end date, status category, count (cumulative done starts at 0)"), ("m_cfd_chart", "V3 chart range: wide pivot of m_cfd"),
        ("m_cycle_bins", "V4: 20 bins of cycle days, count, median, p85, and marker columns"),
        ("m_aging_wip", "V5: in-progress items: key, group, age since start, group P85"), ("m_wip", "V6: in progress by Group and Team"),
        ("m_backlog_age", "V7: open work items by age bucket"), ("m_noowner_ip", "V8: in progress with no owner by Group"), ("m_noowner_list", "V8: key, group, age_days of each in-progress item with no owner (status is in the next column)"),
        ("m_code_week", "V9 spec range, long form: week, platform, class, merged, median_first_review_hours"), ("m_code_week_chart", "V9 chart range: wide pivot of m_code_week (merged per platform and class; median first review hours of normal changes per platform)"),
        ("m_review_team", "V10: review events per week by Team"), ("m_hygiene", "V11 spec range, long form: system, check, group, pass_rate, failing_count, exempt_count"), ("m_hygiene_chart", "V11 chart range: wide pivot of m_hygiene (pass rate; checks by Group)"),
        ("m_align", "V12 spec range, long form: measure, level, name, count, rate"), ("m_align_chart", "V12 chart range: wide pivot of m_align (rate; measures by Group)"), ("m_cycle_bins_marks", "V4 helper: bin height where the median or P85 falls, to plot the markers"), ("m_open_changes", "V13: open normal changes: age, size, thresholds"),
        ("d_created_done", "D1: last 13 complete weeks, SBU: week, created (from m_created_done), done = the main throughput series, Won't Do and Duplicate excluded (from m_throughput)"), ("m_answers", "The cells the Answer sentences cite (dk_* names): each a formula over d_ ranges, m_ ranges or Metrics cells; the sentences only join them with text"), ("d_noowner", "D2: in progress with no owner by Group: group, count (from m_noowner_ip)"),
        ("d_stuck", "D3: in-progress items older than t_stuck_days, by Group: group, count, oldest_age_days (from m_aging_wip)"),
        ("d_blocked", "K1: open work items in a blocked status (Blocked) at the as-of, by Group and an SBU total row: group, blocked, median_blocked_age_days (as-of minus the last entry into a blocked status), unassigned (from Jira_Issues; counts only)"), ("d_merged", "D4: merged normal changes per week, both platforms, last 13 complete weeks (from m_code_week)"),
        ("d_first_review", "D5: median hours to first review of merged normal changes, both platforms, last 13 weeks (a combined median cannot be built from the per-platform medians, so it is computed from Code_Changes with the same filters)"), ("d_align", "D6a and D6b (range on Metrics, not drawn): A1 link rate and A4 Done-with-no-code count by Group (from m_align)"),
        ("Takeaway sentences", "Dashboard: one plain-English sentence under each of the ten slots (D1, D3, K1, D4, D5, B1, I1, I1, I2, M1), a formula over dk_* cells, d_ ranges and Threshold cells; no typed numbers"),
        ("m_levels", "Level table: SBU, Group, Team metrics"), ("m_headline", "Headline metrics with week-over-week change"), ("m_alerts", "Alerts in priority order"),
        ("m_time_in_status", "Median days per status"), ("m_backlog_status", "Open items by status"), ("m_backlog_type", "Open items by type"), ("m_merged_group", "Merged per week by Group")]:
        rows.append(["Metrics (named range)", nm, "range", "", d, "Metrics tab"])
    for nm, d in [
        ("d_flow612", "6/12 (D1): work items added, finished and net (finished minus added): the last 6 complete weeks, a blank gap row, then the last 12 complete months (EDATE months of the as-of); finished = main throughput series. Columns: label, added, finished and net per week, then per month, a zero line, then label columns that hold a value only at the points that get a data label (last point of each part, peak, low). The first month is partial."),
        ("d_code612", "6/12 (D4): ordinary code changes merged (GitLab and GitHub together), the last 6 complete weeks then the last 12 complete months; per-week and per-month columns plus label columns. The first month is partial."),
        ("d_review612", "6/12 (D5): median hours to first review of merged ordinary changes, the last 6 complete weeks then the last 12 complete months; per-week and per-month columns plus label columns (rounded to 0.1). The first month is partial."),
        ("m_612_periods", "The 18 periods of the 6/12 views (6 complete weeks, then 12 complete months): type, label, start, end (exclusive)"),
        ("m_612_long", "6/12 long form for the Explore canvas: one row per level entry (SBU, Group, Team), metric (created, finished, merged, median_first_review_hours, in_progress_no_owner, stuck, wip) and period; value is a formula over the data tabs or State_History; no person rows"),
        ("m_612_stats", "6/12 stat strip per level entry and metric: last week, week over week %, average of the 4 weeks before, last month, month over month %, 12-month figure and its basis; formulas over m_612_long"),
        ("d_bugs612", "B1: Bugs (Jira type Bug) created, fixed (final Done in the period, main series only) and net (fixed minus created) per period, SBU: period_type, period_label, period_start, created, fixed, net; the last 6 complete weeks then the last 12 complete months (18 rows; the first month is partial)"),
        ("d_bugs612_chart", "B1 chart range: the same values laid out for the 6/12 line chart: weekly columns, a blank gap row, monthly columns, a zero line, and label columns for the thinned data labels"),
        ("d_bugage", "B2: open Bugs at the as-of (status category not done) by level (SBU, each Group, each Team): level, name, open, median_age_days, p85_age_days, over_90 (older than 90 days); age = as-of minus created; Team rows with fewer than t_min_n open Bugs show counts only ('n under 10')"),
        ("d_bugage_prio", "B2: open Bugs at the as-of by Jira priority (SBU): priority, open, median_age_days, over_90"),
        ("d_workmix612", "M1 work mix: tickets finished in the period (main series) by Work Category (the epic's value at the finish date), SBU and each Group, last 6 complete weeks then 12 complete months: finished, customer, internal, ops, support, none, each category's share of the categorised ones (percent), features, none as a share of all. Limits on the Thresholds tab (t_cat_support_max, t_cat_ops_max, t_cat_features_min)."),
        ("d_workmix_yr", "M1 12-month shares and Status per row (SBU and each Group): finished tickets, each category's share, No category share of all, and Status against the three limits."),
        ("d_workmix612_chart", "M1 chart range: the SBU share per category for the 6/12 line chart (weekly, gap row, monthly) and the No category line."),
        ("d_stalled", "Stalled epics and initiatives: open ones, and those with no update under them for longer than t_epic_stalled_days or t_init_stalled_days, SBU and each Group. Epics and initiatives are never counted together."),
        ("d_inc612", "I1: incidents (Jira projects EA = customer, IA = internal; any issue type) per period and split: created, resolved (final Done in the period, any resolution), resolved_wontdo_dup (of those, Won't Do or Duplicate) and net (resolved minus created); the last 6 complete weeks then the last 12 complete months, 18 rows per split; counts only. Incidents are measured at the Sheet as-of (Metrics as_of_utc), not at the incident pull's own as-of: incidents created after it are not listed and incidents resolved after it count as open"),
        ("d_inc612_chart_customer", "I1 chart range, customer: the same values laid out for the 6/12 line chart (weekly columns, a blank gap row, monthly columns, a zero line, label columns); measured at the Sheet as-of (Metrics as_of_utc)"),
        ("d_inc612_chart_internal", "I1 chart range, internal: as above for internal incidents; measured at the Sheet as-of (Metrics as_of_utc)"),
        ("d_incopen", "I2: incidents open at the as-of by split and priority (SBU level): open, median_age_days, p85_age_days, over_30 (older than 30 days); 'All' is the split total. Measured at the Sheet as-of (Metrics as_of_utc)"),
        ("d_incttr", "I3: time to resolve (final Done minus created, days) per month for the last 12 complete months and split: resolved, median_days, p85_days; blank when nothing was resolved that month. Measured at the Sheet as-of (Metrics as_of_utc)"),
        ("d_incttr_chart", "I3 chart range: month, then median and P85 days to resolve for customer and internal incidents; measured at the Sheet as-of (Metrics as_of_utc)"),
        ("d_inctype", "I4: incidents by split and Jira issue type: created_12m, resolved_12m (last 12 complete months, first month partial) and open_now; exactly the types present in the incident extract; counts only. Measured at the Sheet as-of (Metrics as_of_utc)"),
        ("d_state612", "6/12 (P2): SBU work items in progress with no owner at the end of each of the last 6 complete weeks and 12 complete months, read from State_History")]:
        if nm.startswith("d_inc") and "d_inc612" not in G.names:       # incidents left out of this build
            continue
        rows.append(["Metrics (named range)", nm, "range", "", d, "Metrics tab"])
    for nm, d in getattr(G, "answer_defs", []):
        if nm.startswith(("dk_p1", "dk_p2", "dk_p4", "dk_p5", "dk_net", "dk_b1", "dk_b2", "dk_m1", "dk_i1", "dk_i2", "dk_i3", "dk_i4")):
            rows.append(["Metrics (answer cell)", nm, "num", "", d + ". Cited by an Answer sentence or a stat strip cell (AC44a, AC44b).", "Metrics m_answers"])
    for label, pre, cond in FAIL_LISTS:
        for what, d in (("id", "Change id or Jira key of an item failing the check"), ("group", "Its Group"), ("team", "Its Team")):
            rows.append(["Failing_Lists", f"{label}_{what}", "text", "", f"{d}: {label} ({CHECK_DEFS.get(label, 'alignment measure ' + label)}); spilled FILTER from row 2, thresholds apply live", "Formulas over the data tabs"])
    for cn, d in IND_COLS:
        rows.append(["Individual", IND_HEADERS.get(cn, cn), "num" if cn not in ("person", "group", "team", "end_date") else "text", "", d + ". Counts; a rate shows only when its denominator is at least t_min_n; no ranking", "Formulas over the data tabs"])
    for cn, d in [("chart_name", "Person's name as on the org chart"), ("manager", "Manager's name"), ("title", "Job title"), ("group", "Group (blank = none, shown as Other)"),
                  ("team", "Team (blank = none, shown as No team)"), ("start_date", "Roster start date"), ("end_date", "Roster end date; a removed person stays in past weeks"), ("note", "Where the line came from")]:
        rows.append(["Roster", cn, "text", "", d, "data/roster.csv (source of truth)"])
    for cn, d in [("person", "Person's name"), ("effective_from", "Date from which the team and group apply"), ("effective_to", "Date it stops applying, blank if current"),
                  ("group", "Group in that period"), ("team", "Team in that period")]:
        rows.append(["Roster_History", cn, "text", "", d, "data/roster_history.csv"])
    for cn, d in [("name", "Threshold name (named cell t_*)"), ("value", "Current value; edit here, formulas follow"), ("unit", "Unit"), ("description", "What the threshold does")]:
        rows.append(["Thresholds", cn, "num" if cn == "value" else "text", "", d, "Thresholds tab (the only place a threshold lives)"])
    for cn, d in [("level", "SBU, Group, or Team"), ("area", "Jira, Code, Hygiene, Alignment, Individual, or Decline"), ("question", "A tested question"),
                  ("answer", "The answer, a formula reading the cited cell (declines say so)"), ("cited_cell", "Cell the answer reads"), ("definition", "Definition of the measure"), ("as_of_utc", "As-of timestamp")]:
        rows.append(["Prompt_Library", cn, "text", "", d, "Formulas over Metrics and Individual"])
    for cn, d in [("run_at_utc", "When the build ran"), ("source", "jira, gitlab, github, a tab, the sheet build, or as_of"), ("rows", "Rows from or written for the source"),
                  ("api_calls", "API calls (pull only for sources)"), ("retries_429", "429 retries"), ("final_errors", "Errors after retries"), ("note", "Note")]:
        rows.append(["Log", LOG_HEADERS.get(cn, cn), "text", "", d, "Extractors' calls.json and the build"])
    for cn, d in [("column block per alert", "Alert details: one block of columns per alert (heading, count, column names, then the list of items behind the alert, a spilled formula over the data tabs, and a link column to the item in Jira, GitLab or GitHub)")]:
        rows.append(["Alerts", cn, "text", "", d, "Formulas over the data tabs and Metrics"])
    for cn, d in [("metric", "A metric or block range"), ("source_query", "Where its numbers come from: Jira filter ids with JQL text, GitLab and GitHub endpoint patterns"),
                  ("as_of_utc", "As-of timestamp of the run"), ("defined_in", "Where the definition is")]:
        rows.append(["Sources", SRC_HEADERS.get(cn, cn), "text", "", d, "Built from m_levels and the block ranges"])
    rows.append(["canvas_source", "level, group, team and metric columns", "num", "", "Team and Group rows only, each cell a formula pointing at the same-named column of m_levels; no person-level data", "Metrics"])
    rows.append(["Thresholds", "t_*", "num", "", "User-set threshold cells; the only place a threshold lives", "Thresholds tab"])
    rows.append(["Org events", "cleared tag", "text", "", "A cleared tag (a listed correction to blank) erases the earlier value for all dates: a ticket whose Group, Team or SBU a listed event set to blank counts as blank on every earlier date as well.", "Org-events table (A79)"])          # last row on purpose: the rows above keep their places, so a daily run writes one new row
    return scrub_grid(rows)


def prompt_rows(G, meta, cfg, person=None):
    """>= 15 tested prompts; answers are formulas that read the cited Metrics cell."""
    L = cfg["labels"]
    LV = G.meta_lv
    ci = G.meta_ci
    g1 = meta["groups"][0]
    tm = next((t for (lv, g, t) in LV if lv == "Team" and t not in (L["no_team"], L["ownerless"], L["unmapped"])), L["no_team"])
    def row_of(lv, g, t):
        return G.lv_r0 + 2 + LV.index((lv, g, t))
    def cell(name, key):
        return f"Metrics!{col_letter(ci[name])}{row_of(*key)}"
    S = ("SBU", "*", "*")
    GR = ("Group", g1, "*")
    TM = None
    for x in LV:
        if x[0] == "Team" and x[2] == tm:
            TM = x
            break
    P = [
        ("SBU", "Jira", "How many work items are in progress with no owner right now?", cell("in_progress_no_owner", S), "count of in-progress work items with no assignee"),
        ("SBU", "Jira", "How many work items are in progress right now?", cell("wip", S), "work items in an In Progress category at the as-of time"),
        ("SBU", "Jira", "How many open work items are there (excluding epics and initiatives)?", cell("open_work_items", S), "open = status category not Done"),
        ("SBU", "Jira", "What is the median cycle time in days for finished work items?", cell("cycle_median_days", S), "first start to final Done, 12-month finished main-series items"),
        ("SBU", "Jira", "What is the P85 cycle time in days?", cell("cycle_p85_days", S), "linear interpolation percentile"),
        ("SBU", "Jira", "How many weeks of backlog are there at the current pace?", cell("weeks_of_backlog", S), "open work items over the last-4-week average of main-series throughput"),
        ("SBU", "Jira", "How many main-series work items finished in the last complete week?", cell("done_last_week_main", S), "ISO week, UTC, excludes Won't Do and Duplicate"),
        ("Group", "Jira", f"How many in-progress work items have no owner in {g1}?", cell("in_progress_no_owner", GR), "same definition at Group level"),
        ("Group", "Jira", f"What is the median cycle time in days in {g1}?", cell("cycle_median_days", GR), "Group of the owner at the final Done"),
        ("Team", "Jira", f"How many work items are in progress in the team {tm}?", cell("wip", TM), "Team of the owner"),
        ("SBU", "Code", "How many changes were merged in the last complete week?", cell("merged_last_week", S), "ordinary changes, counted once across GitLab and GitHub"),
        ("SBU", "Code", "What is the median opened-to-merge time in days?", cell("open_to_merge_median_days", S), "changes merged in the 12-month window, draft time included"),
        ("SBU", "Code", "How many open normal changes have waited past the review limit with no first review?", cell("open_no_review_over_limit", S), "limit is t_first_review_days in Thresholds"),
        ("Group", "Code", f"How many changes did {g1} merge in the last complete week?", cell("merged_last_week", GR), "Group of the author at the merge date"),
        ("SBU", "Hygiene", "What share of normal changes carry a linked Jira key (C1)?", cell("C1_pass_rate", S), "C1 over normal merged or open changes"),
        ("SBU", "Hygiene", "How many in-progress work items fail J1 (no owner)?", cell("J1_fail", S), "J1 fail count"),
        ("SBU", "Alignment", "What is the A1 link rate?", cell("A1_rate", S), "normal changes with a linked key over normal changes"),
        ("SBU", "Alignment", "How many merged normal changes have no Jira key (A5)?", cell("A5_count", S), "untracked merged work"),
        ("Group", "Alignment", f"How many finished code-type issues in {g1} have no merged change (A4)?", cell("A4_count", GR), "A4 count"),
        ("Team", "Jira", f"How many open work items does the team {tm} own?", cell("open_work_items", TM), "open = status category not Done; Team of the owner"),
        ("Team", "Code", f"How many changes did the team {tm} merge in the last complete week?", cell("merged_last_week", TM), "Team of the author at the merge date"),
        ("Team", "Alignment", f"What is the A1 link rate for the team {tm}?", cell("A1_rate", TM), "normal changes with a linked Jira key over normal changes"),
    ]
    if person:
        pname, prow = person
        ic = [c[0] for c in IND_COLS]
        for nm_, q_, d_ in (("wip", "How many work items does {p} have in progress?", "Jira work items in progress now (a count, not a ranking)"),
                            ("blocked", "How many open work items of {p} are blocked?", "open work items in a blocked status now (a count, not a ranking)"),
                            ("oldest_ip_age_days", "How old is the oldest in-progress item of {p}?", "days since start of the oldest in-progress item (not a ranking)")):
            cl = f"Individual!{col_letter(ic.index(nm_))}{prow}"
            P.append(("Individual", "Individual", q_.format(p=pname), cl, d_))
    P += [
        ("SBU", "Decline", "Who is the slowest engineer?", None, "Decline: the Sheet does not rank people or compare individuals."),
        ("SBU", "Decline", "What is the estimate in story points for the open work?", None, "Not in the Sheet: estimates are not used."),
    ]
    rows = [["level", "area", "question", "answer", "cited_cell", "definition", "as_of_utc"]]
    for lvl, area, q, c, d in P:
        if c:
            rows.append([lvl, area, q, f"={c}", c, d, "=TEXT(asof,\"yyyy-mm-dd hh:mm:ss\")&\"Z\""])
        else:
            rows.append([lvl, area, q, d, "", "decline", "=TEXT(asof,\"yyyy-mm-dd hh:mm:ss\")&\"Z\""])
    return rows


CODE_PREFIX = ("merged_", "open_to_merge", "first_review", "open_changes", "open_normal", "open_age", "reviews_per_week", "changes_reviewed", "open_no_review",
               "code_exempt", "merge_drop", "C1_", "C2_", "C3_", "C4_", "C5_", "C6_", "C7_", "C8_")
ALIGN_PREFIX = ("A1_", "A2_", "A3_", "A4_", "A5_")


def coverage_rows(G, cfg):
    """One row per metric: its source query (Jira: filter id and JQL; code: endpoint pattern) and the as-of."""
    t = cfg.get("texts", {})
    jira = t.get("jira_query_open", "") + " ; " + t.get("jira_query_done", "")
    code = t.get("gitlab_endpoints", "") + " ; " + t.get("github_endpoints", "")
    asof = '=TEXT(asof,"yyyy-mm-dd hh:mm:ss")&"Z"'
    rows = []
    for name in G.meta_names:
        if name.startswith(ALIGN_PREFIX):
            src = "Both. Jira: " + jira + " | Code: " + code + " | joined on the Jira key found in the change (Code_Jira_Links)"
        elif name.startswith(CODE_PREFIX):
            src = code
        else:
            src = jira
        rows.append([name, src, asof, "Data_Dictionary (m_levels column)", ""])
    extra = [("rolling_avg (m_throughput)", jira), ("time_in_status (m_time_in_status)", jira), ("backlog by status and type (m_backlog_status, m_backlog_type)", jira),
             ("created vs done (m_created_done)", jira), ("cumulative flow (m_cfd)", jira), ("cycle time bins (m_cycle_bins)", jira),
             ("aging WIP (m_aging_wip)", jira), ("in progress with no owner (m_noowner_ip, m_noowner_list)", jira),
             ("merged per week (m_code_week)", code), ("review load by Team (m_review_team)", code), ("open changes (m_open_changes)", code),
             ("hygiene (m_hygiene)", "Jira: " + jira + " | Code: " + code), ("alignment (m_align)", "Both. Jira: " + jira + " | Code: " + code),
             ("alerts 1 to 6 (m_alerts)", "Jira: " + jira + " | Code: " + code),
             ("Individual (all columns)", "Jira: " + jira + " | Code: " + code)]
    for n_, src in extra:
        rows.append([n_, src, asof, "Data_Dictionary", ""])
    return rows


def coverage_tab_rows(G, cfg):
    """Coverage tab: one header row, then one row per metric: source query and as-of."""
    rows = [[SRC_HEADERS[h] for h in ("metric", "source_query", "as_of_utc", "defined_in")]]
    for r in coverage_rows(G, cfg):
        rows.append(r[:4])
    import identity_tab as _IDT          # v1.43g AC84: one row, its number a formula over the Identity flag column
    rows.append(["people with no GitHub login (identity)", _IDT.sources_formula(), '=TEXT(asof,"yyyy-mm-dd hh:mm:ss")&"Z"', "Definitions"])
    return rows


TAKEAWAYS = [
    # one sentence per Dashboard chart, in chart order (alerts 1, 2, 4, 4, 5). Every number is a Metrics cell (dk_* in m_answers); the sentence only joins them (AC44a).
    '=TEXT(dk_noowner_total,"0")&" items in progress have no owner; most in "&dk_noowner_max_group&" ("&TEXT(dk_noowner_max,"0")&")."',
    '=TEXT(dk_stuck_total,"0")&" items are older than normal for their Group; the oldest is "&TEXT(dk_stuck_oldest,"0")&" days."',
    '="Last week "&TEXT(dk_finished_last,"0")&" work items were finished and "&TEXT(dk_added_last,"0")&" were added (net "&TEXT(dk_net_last,"+0;-0;0")&"): "&dk_keeping_up&"."',
    '=TEXT(dk_merged_last,"0")&" changes were merged last week, "&TEXT(dk_merged_change,"0%")&" "&dk_merged_dir&" the average of the 4 weeks before."',
    '="The median first review took "&TEXT(dk_review_last,"0.0")&" hours last week (limit "&TEXT(dk_review_limit,"0")&" hours)."',
]
DETAIL_ANSWERS = {
    # Answer cards under the detail charts: formulas that join dk_* cells in m_answers (AC44a); build.py adds the 'Answer: ' lead-in
    "V1": '=TEXT(dk_v1_total,"0")&" work items were finished last week in total; the 4-week average is "&TEXT(dk_v1_avg4,"0")&"."',
    "V2": '="Last week "&TEXT(dk_v2_created,"0")&" work items were created and "&TEXT(dk_v2_done,"0")&" were finished (all resolutions)."',
    "V3": '="There are "&TEXT(dk_v3_open,"0")&" open work items, "&TEXT(dk_v3_inprog,"0")&" of them in progress. Done so far in the window: "&TEXT(dk_v3_done,"0")&" (not drawn: it would dwarf the open work)."',
    "V4": '="Half of finished items take under "&TEXT(dk_v4_median,"0.0")&" days and 85% finish within "&TEXT(dk_v4_p85,"0.0")&" days. The first bin holds "&TEXT(dk_v4_first,"0")&" items; the left axis stops lower so the other bins can be read."',
    "V5": '=TEXT(dk_v5_old,"0")&" of "&TEXT(dk_v5_wip,"0")&" in-progress items are older than the 85th-percentile limit for their Group."',
    "V6": '="Most work in progress is in "&dk_v6_label&" ("&TEXT(dk_v6_max,"0")&" items); "&TEXT(dk_v6_total,"0")&" items are in progress in total."',
    "V7": '=TEXT(dk_v7_old,"0")&" of "&TEXT(dk_v7_total,"0")&" open work items ("&TEXT(dk_v7_share,"0%")&") are more than a year old."',
    "V8": '=TEXT(dk_v8_total,"0")&" items in progress have no owner; the longest has been in progress "&TEXT(dk_v8_oldest,"0")&" days."',
    "V9a": '="Last week "&TEXT(dk_v9a_last,"0")&" changes were merged in total across GitLab and GitHub, all kinds of change."',
    "V9b": '="Last week the median first review took "&TEXT(dk_v9b_gitlab,"0.0")&" hours on GitLab and "&TEXT(dk_v9b_github,"0.0")&" hours on GitHub."',
    "V10": '="Teams gave "&TEXT(dk_v10_total,"0")&" reviews a week in total; the most active Team is "&dk_v10_team&" ("&TEXT(dk_v10_max,"0")&" a week)."',
    "V11": '=TEXT(dk_v11_c1,"0%")&" of ordinary code changes name a Jira issue (check C1) and "&TEXT(dk_v11_j1,"0%")&" of in-progress Jira items have an owner (check J1)."',
    "V12": '=TEXT(dk_v12_a1,"0%")&" of ordinary code changes link to Jira (A1); "&TEXT(dk_v12_a4,"0")&" Done items have no merged code (A4)."',
    "V13": '=TEXT(dk_v13_open,"0")&" ordinary changes are open; the oldest is "&TEXT(dk_v13_oldest,"0")&" days old."',
    "P1": '="Last week "&TEXT(dk_p1_wk_fin,"0")&" work items were finished ("&TEXT(dk_p1_wk_wow,"+0;-0;0")&" on the week before; average of the 4 weeks before "&TEXT(dk_p1_wk_avg4,"0")&") and "&TEXT(dk_p1_wk_added,"0")&" were added: net "&TEXT(dk_p1_wk_net,"+0;-0;0")&", "&dk_p1_wk_dir&". Last month "&TEXT(dk_p1_mo_fin,"0")&" were finished ("&TEXT(dk_p1_mo_mom,"+0;-0;0")&" on the month before) and "&TEXT(dk_p1_mo_added,"0")&" were added: net "&TEXT(dk_p1_mo_net,"+0;-0;0")&", "&dk_p1_mo_dir&"."',
    "P4": '="Last week "&TEXT(dk_p4_wk,"0")&" ordinary code changes were merged ("&TEXT(dk_p4_wow,"+0;-0;0")&" on the week before; average of the 4 weeks before "&TEXT(dk_p4_avg4,"0")&"). Last month "&TEXT(dk_p4_mo,"0")&" were merged ("&TEXT(dk_p4_mom,"+0;-0;0")&" on the month before); "&TEXT(dk_p4_yr,"#,##0")&" over the 12 months."',
    "P5": '="Last week the median first review took "&TEXT(dk_p5_wk,"0.0")&" hours ("&TEXT(dk_p5_wow,"+0.0;-0.0;0.0")&" on the week before; median of all changes in the 4 weeks before "&TEXT(dk_p5_avg4,"0.0")&"). Last month it took "&TEXT(dk_p5_mo,"0.0")&" hours ("&TEXT(dk_p5_mom,"+0.0;-0.0;0.0")&" on the month before); "&TEXT(dk_p5_yr,"0.0")&" over the 12 months (median of all changes)."',
    "B1": '="Last week "&TEXT(dk_b1_wk_fixed,"0")&" bugs were fixed ("&TEXT(dk_b1_wk_wow,"+0;-0;0")&" on the week before; average of the 4 weeks before "&TEXT(dk_b1_wk_avg4,"0")&") and "&TEXT(dk_b1_wk_created,"0")&" were created: net "&TEXT(dk_b1_wk_net,"+0;-0;0")&", "&dk_b1_wk_dir&". Last month "&TEXT(dk_b1_mo_fixed,"0")&" were fixed ("&TEXT(dk_b1_mo_mom,"+0;-0;0")&" on the month before) and "&TEXT(dk_b1_mo_created,"0")&" were created: net "&TEXT(dk_b1_mo_net,"+0;-0;0")&", "&dk_b1_mo_dir&"."',
    "B2": '=TEXT(dk_b2_open,"#,##0")&" bugs are open: half are older than "&TEXT(dk_b2_median,"0")&" days and 85% are younger than "&TEXT(dk_b2_p85,"0")&" days. "&TEXT(dk_b2_over90,"#,##0")&" ("&TEXT(dk_b2_over90_share,"0%")&") are older than 90 days; most in "&dk_b2_top_group&" ("&TEXT(dk_b2_top_over90,"#,##0")&")."',
    "M1": '=TEXT(dk_m1_feature_yr,"0.0")&"% of the finished tickets that have a category were features over the last 12 months, "&TEXT(dk_m1_support_yr,"0.0")&"% Support and "&TEXT(dk_m1_ops_yr,"0.0")&"% Ops & Maintenance; "&TEXT(dk_m1_none_yr,"0.0")&"% of all "&TEXT(dk_m1_finished_yr,"#,##0")&" finished tickets had no category. Limits: features at least "&t_cat_features_min&"%, Support at most "&t_cat_support_max&"%, Ops & Maintenance at most "&t_cat_ops_max&"%. Measured at "&TEXT(asof,"d mmm yyyy hh:mm")&" UTC."',
    "I1C": '="Customer incidents: last week "&TEXT(dk_i1c_wk_res,"0")&" were resolved ("&TEXT(dk_i1c_wk_wow,"+0;-0;0")&" on the week before; average of the 4 weeks before "&TEXT(dk_i1c_wk_avg4,"0.0")&") and "&TEXT(dk_i1c_wk_created,"0")&" were created: net "&TEXT(dk_i1c_wk_net,"+0;-0;0")&", "&dk_i1c_wk_dir&". Last month "&TEXT(dk_i1c_mo_res,"0")&" were resolved ("&TEXT(dk_i1c_mo_mom,"+0;-0;0")&" on the month before) and "&TEXT(dk_i1c_mo_created,"0")&" were created: net "&TEXT(dk_i1c_mo_net,"+0;-0;0")&", "&dk_i1c_mo_dir&". Over the 12 months "&TEXT(dk_i1c_yr_res,"#,##0")&" were resolved, "&TEXT(dk_i1c_yr_wd,"#,##0")&" of them as Won\'t Do or Duplicate."',
    "I1I": '="Internal incidents: last week "&TEXT(dk_i1i_wk_res,"0")&" were resolved ("&TEXT(dk_i1i_wk_wow,"+0;-0;0")&" on the week before; average of the 4 weeks before "&TEXT(dk_i1i_wk_avg4,"0.0")&") and "&TEXT(dk_i1i_wk_created,"0")&" were created: net "&TEXT(dk_i1i_wk_net,"+0;-0;0")&", "&dk_i1i_wk_dir&". Last month "&TEXT(dk_i1i_mo_res,"0")&" were resolved ("&TEXT(dk_i1i_mo_mom,"+0;-0;0")&" on the month before) and "&TEXT(dk_i1i_mo_created,"0")&" were created: net "&TEXT(dk_i1i_mo_net,"+0;-0;0")&", "&dk_i1i_mo_dir&". Over the 12 months "&TEXT(dk_i1i_yr_res,"#,##0")&" were resolved, "&TEXT(dk_i1i_yr_wd,"#,##0")&" of them as Won\'t Do or Duplicate."',
    "I2": '="Customer: "&TEXT(dk_i2c_open,"#,##0")&" incidents are open; half are older than "&TEXT(dk_i2c_median,"0")&" days, 85% younger than "&TEXT(dk_i2c_p85,"0")&" days, "&TEXT(dk_i2c_over30,"#,##0")&" older than "&t_incident_open_days&" days. Internal: "&TEXT(dk_i2i_open,"#,##0")&" are open; half are older than "&TEXT(dk_i2i_median,"0")&" days, 85% younger than "&TEXT(dk_i2i_p85,"0")&" days, "&TEXT(dk_i2i_over30,"#,##0")&" older than "&t_incident_open_days&" days."',
    "I3": '="Last month customer incidents took a median "&TEXT(dk_i3c_median,"0.0")&" days to resolve (85% within "&TEXT(dk_i3c_p85,"0.0")&" days; "&TEXT(dk_i3c_res,"0")&" resolved); internal incidents a median "&TEXT(dk_i3i_median,"0.0")&" days (85% within "&TEXT(dk_i3i_p85,"0.0")&" days; "&TEXT(dk_i3i_res,"0")&" resolved)."',
    "I4": '="Over the last 12 months "&TEXT(dk_i4c_created,"#,##0")&" customer incidents were created ("&TEXT(dk_i4c_resolved,"#,##0")&" resolved, "&TEXT(dk_i4c_open,"#,##0")&" open now) across "&TEXT(dk_i4c_types,"0")&" issue types, and "&TEXT(dk_i4i_created,"#,##0")&" internal incidents ("&TEXT(dk_i4i_resolved,"#,##0")&" resolved, "&TEXT(dk_i4i_open,"#,##0")&" open now) across "&TEXT(dk_i4i_types,"0")&" types."',
    "D1": TAKEAWAYS[2],
    "D4": TAKEAWAYS[3],
    "D5": TAKEAWAYS[4],
    "P2": '="Right now "&TEXT(dk_p2_asof,"0")&" items in progress have no owner; at the end of last week it was "&TEXT(dk_p2_last_wk,"0")&", and the highest point in the last year was "&TEXT(dk_p2_max,"0")&"."',
    "D6a": '=TEXT(dk_a1_sbu,"0%")&" of code changes name a Jira issue (lowest: "&dk_a1_low_group&", "&TEXT(dk_a1_low,"0%")&")."',
    "D6b": '=TEXT(dk_a4_total,"0")&" Done Jira items have no merged code; most in "&dk_a4_max_group&" ("&TEXT(dk_a4_max,"0")&")."',
}
_I1C_RAW = DETAIL_ANSWERS["I1C"]
for _k in ("I1C", "I1I", "I2", "I3", "I4"):      # A38: incidents are measured at the Sheet's as-of, and every incident answer card says so
    DETAIL_ANSWERS[_k] += '&" Measured at the Sheet as-of "&TEXT(asof,"d mmm yyyy hh:mm")&" UTC."'
# v1.22: the answer cards of the eight Dashboard charts. I1 joins its customer and internal sentences (one chart, two splits); the as-of is stated once at the end.
DASH_ANSWERS = {      # v1.26: number first, one plain sentence group, no slot codes; each cites dk_* cells and Thresholds cells only (AC44a)
    "D1": '=TEXT(dk_p1_wk_fin,"0")&" work items were finished last week and "&TEXT(dk_p1_wk_added,"0")&" were added: "&TEXT(ABS(dk_p1_wk_net),"0")&IF(dk_p1_wk_net>=0," more finished than added."," more added than finished.")&" The 4 weeks before averaged "&TEXT(dk_p1_wk_avg4,"0")&" finished a week. Last month: "&TEXT(dk_p1_mo_fin,"#,##0")&" finished and "&TEXT(dk_p1_mo_added,"#,##0")&" added."',
    "D3": '=TEXT(dk_stuck_total,"0")&" in-progress items are older than normal for their Group; the oldest has been in progress "&TEXT(dk_stuck_oldest,"#,##0")&" days."',
    "K1": '=TEXT(dk_k1_total,"0")&" items are blocked right now, "&TEXT(dk_k1_unassigned,"0")&" of them with no owner. Half have been blocked for more than "&TEXT(dk_k1_median,"0")&" days and "&TEXT(dk_k1_over,"0")&" for longer than the "&t_blocked_days&"-day limit. Most are in "&dk_k1_top_group&" ("&TEXT(dk_k1_top,"0")&")."',
    "D4": '=TEXT(dk_p4_wk,"#,##0")&" code changes were merged last week, "&TEXT(ABS(dk_p4_wow),"#,##0")&IF(dk_p4_wow>=0," more"," fewer")&" than the week before. The 4 weeks before averaged "&TEXT(dk_p4_avg4,"0")&" a week. Last month: "&TEXT(dk_p4_mo,"#,##0")&" merged."',
    "D5": '=TEXT(dk_p5_wk,"0.0")&" hours: the median time to first review last week, "&TEXT(ABS(dk_p5_wow),"0.0")&IF(dk_p5_wow>=0," hours slower"," hours faster")&" than the week before. The median over the 4 weeks before was "&TEXT(dk_p5_avg4,"0.0")&" hours. Last month: "&TEXT(dk_p5_mo,"0.0")&" hours."',
    "B1": '=TEXT(dk_b1_wk_fixed,"0")&" bugs were fixed last week and "&TEXT(dk_b1_wk_created,"0")&" were created: "&TEXT(ABS(dk_b1_wk_net),"0")&IF(dk_b1_wk_net>=0," more fixed than created."," more created than fixed.")&" Last month: "&TEXT(dk_b1_mo_fixed,"0")&" fixed and "&TEXT(dk_b1_mo_created,"0")&" created."',
    "I1C": '=TEXT(dk_i1c_wk_res,"0")&" customer incidents were resolved last week and "&TEXT(dk_i1c_wk_created,"0")&" were created: "&TEXT(ABS(dk_i1c_wk_net),"0")&IF(dk_i1c_wk_net>=0," more resolved than created."," more created than resolved.")&" Last month: "&TEXT(dk_i1c_mo_res,"0")&" resolved and "&TEXT(dk_i1c_mo_created,"0")&" created."',
    "I1": '=TEXT(dk_i1i_wk_res,"0")&" internal incidents were resolved last week and "&TEXT(dk_i1i_wk_created,"0")&" were created: "&TEXT(ABS(dk_i1i_wk_net),"0")&IF(dk_i1i_wk_net>=0," more resolved than created."," more created than resolved.")&" Last month: "&TEXT(dk_i1i_mo_res,"0")&" resolved and "&TEXT(dk_i1i_mo_created,"0")&" created. Measured at "&TEXT(asof,"d mmm yyyy hh:mm")&" UTC."',
    "I2": '=TEXT(dk_i2c_open,"#,##0")&" customer incidents are open; half are older than "&TEXT(dk_i2c_median,"0")&" days and "&TEXT(dk_i2c_over_limit,"#,##0")&" are older than "&t_incident_open_days&" days. Internal: "&TEXT(dk_i2i_open,"#,##0")&" open, half older than "&TEXT(dk_i2i_median,"0")&" days. Measured at "&TEXT(asof,"d mmm yyyy hh:mm")&" UTC."',
    "M1": '=TEXT(dk_m1_feature_yr,"0.0")&"% of the finished tickets that have a category were features over the last 12 months, "&TEXT(dk_m1_support_yr,"0.0")&"% Support and "&TEXT(dk_m1_ops_yr,"0.0")&"% Ops & Maintenance; "&TEXT(dk_m1_none_yr,"0.0")&"% of all "&TEXT(dk_m1_finished_yr,"#,##0")&" finished tickets had no category. Limits: features at least "&t_cat_features_min&"%, Support at most "&t_cat_support_max&"%, Ops & Maintenance at most "&t_cat_ops_max&"%. Measured at "&TEXT(asof,"d mmm yyyy hh:mm")&" UTC."',
}
DETAIL_ANSWERS = {k: DETAIL_ANSWERS[k] for k in ("P1", "P4", "P5", "B1", "I1C", "I1I", "I2", "M1")}      # the other cards were on Charts (detail), removed in v1.22; their dk_* cells stay on Metrics
ALERT_ACTIONS = ["Assign an owner to each item", "Find out why these items are stuck", "Move work off the people over the limit (names are on the Individual tab)",
                 "Look at why the weekly numbers dropped", "Assign a reviewer to each change", "Link or update the code for these issues"]
ALERT_TITLES = ["In progress with no owner", "In progress for longer than the stuck limit", "People over the WIP limit",
                "Group throughput or merged changes below the drop threshold", "Open change past the review limit with no first review",
                "In-progress code-type issue with no linked change activity"]


def dashboard_header(G, meta, cfg=None):
    """Top of the Dashboard tab: title, one plain freshness sentence, alerts in priority order. Then the eight charts."""
    rows = []
    rows.append([(cfg or {}).get("sheet_name", "Dashboard"), "", "", "", ""])
    rows.append(['="Data is "&TEXT(NOW()-asof,"0.0")&" days old (as of "&TEXT(asof,"d mmm yyyy hh:mm")&" UTC). Fresh means newer than "&t_freshness_days&" days."&IF(NOW()-asof>t_freshness_days," STALE: refresh before relying on these numbers.","")', "", "", "", ""])
    rows.append([DDB.A3_TEXT, "", "", "", ""])          # D411: the one plain line
    rows.append(["Alert", "Count", "Unit", "What to do", ""])
    units = ["items", "items", "people", "flags", "changes", "items"]
    for i in range(5):          # D72: the Dashboard lists five alerts; alert 6 stays on Alert details
        a = f"alert{i+1}"
        rows.append([f"{i+1}. {ALERT_TITLES[i]}", "{ALERT_LINK_%d}" % (i + 1), units[i], f'=IF({a}>0,"{ALERT_ACTIONS[i]}","Clear")', ""])
    rows.append(["", "", "", "", ""])
    return rows


ALERT_HEADERS = {
    "key": "Key", "group": "Group", "status": "Status", "age_days": "Age (days)", "link": "Link", "team": "Team",
    "group_p85_days": "Group's 85th percentile (days)", "stuck_limit_days": "Stuck limit (days)", "people_over_limit": "People over the limit",
    "jira_done_last_week": "Jira items finished last week", "jira_prior_4wk_avg": "Jira finished, average of the 4 weeks before",
    "merged_last_week": "Changes merged last week", "merged_prior_4wk_avg": "Merged, average of the 4 weeks before",
    "change_id": "Change", "platform": "Platform", "project": "Project", "number": "Number",
    "days_since_linked_activity": "Days since linked activity", "blocked": "Blocked now", "median_blocked_age_days": "Median days blocked",
    "unassigned": "Unassigned", "incidents": "Incidents", "priority": "Priority", "open_now": "Open now",
    "median_age_days": "Median age (days)", "p85_age_days": "85th percentile age (days)", "open_over_30_days": '="Open more than "&t_incident_open_days&" days"',
}


def alert_link_notes(starts, cfg, meta=None):
    """[(row index, column index, note)] for every linked number in Alerts blocks 7 and 8 (v1.41: item-tab links; the note is the filter line, or says why there is no list)"""
    import links as _LC
    out = []
    gn = list(cfg["groups"]) + [cfg["labels"]["other"], cfg["labels"]["unknown"], "SBU"]
    for k, g in enumerate(gn):
        u = _LC.work_open("blocked", "sbu" if g == "SBU" else ("group", g))
        out.append((3 + k, starts[6] + 1, _LC.note(u)))
        out.append((3 + k, starts[6] + 2, _LC.note(u, True)))
        out.append((3 + k, starts[6] + 3, "List link: opens this Group's blocked items. The owner is not on the item tabs, so the unassigned ones among them cannot be told apart; the rows left are MORE than this number. " + _LC.F.describe(str(u)) + "."))
    # block 4 (v1.41 3c): a fixed table, one row per level (SBU, each Group, Other, Unknown); every count has its own note with the exact filter (the averages are list links)
    lv4 = ["sbu"] + [("group", g) for g in list(cfg["groups"]) + [cfg["labels"]["other"], cfg["labels"]["unknown"]]]
    for k, sc4 in enumerate(lv4):
        for j, (key, is_list, extra) in enumerate(((_LC.work_period("fin", "wk", sc4), False, ""), (_LC.work_period("fin", "wk", sc4), True, " An average over the 4 weeks before: this list is last week's items, for context."),
                                                   (_LC.gl_merged("wk", sc4), False, " Ordinary changes only."), (_LC.gl_merged("wk", sc4), True, " Ordinary changes. An average over the 4 weeks before: this list is last week's changes, for context."))):
            out.append((3 + k, starts[3] + 1 + j, (_LC.F.howto_avg4(str(key), " Ordinary changes only." if j == 3 else "") if j in (1, 3) else _LC.note(key, is_list) + extra)))          # v1.43i (q121): the two 4-week average cells get their own true note
    pri = ["All"] + list((meta or {}).get("inc_priorities", []))
    for k in range(2 * len(pri)):
        proj = "EA" if k < len(pri) else "IA"
        pr = pri[k % len(pri)]
        o, ol = _LC.inc_open(proj, "sbu", pr), _LC.inc_open(proj, "sbu", pr, over30=True)
        for j, nt in ((2, _LC.note(o)), (3, _LC.note(o, True)), (4, _LC.note(o, True)), (5, _LC.note(ol))):
            out.append((3 + k, starts[7] + j, nt))
    return out


# v1.41 (verify-c q73, the 50% rule): reserved rows per block 1..6 = 1.5 x the largest count at the user's limits (stuck 7 days 137 -> 210, open change past the review limit 1,242 -> 1,870, quiet 7 days 162 -> 250)
# G5 (q92): a ticket has "no parent epic" when it has no parent, or its parent is on the tab and is not an Epic (a Story parent: 2 on copy-7 data, AN-316626 and AN-316641). A parent that is not on the tab is not judged (417: epics finished before the window).
NO_EPIC_COND = '((ji_parent_key="")+(COUNTIFS(ji_key,ji_parent_key,ji_type,"<>Epic")>0)>0)'


def no_parent_epic(rows):
    """the same rule in Python, for the selftest: rows [{key, type, parent_key, is_work_item}] -> keys with no parent epic"""
    typ = {r["key"]: r["type"] for r in rows}
    return [r["key"] for r in rows if r["is_work_item"] == 1 and (not r["parent_key"] or (r["parent_key"] in typ and typ[r["parent_key"]] != "Epic"))]


def selftest():
    rows = [{"key": "E-1", "type": "Epic", "parent_key": "", "is_work_item": 0}, {"key": "S-1", "type": "Story", "parent_key": "E-1", "is_work_item": 1},
            {"key": "T-1", "type": "Task", "parent_key": "", "is_work_item": 1}, {"key": "D-1", "type": "DART", "parent_key": "S-1", "is_work_item": 1},
            {"key": "T-2", "type": "Task", "parent_key": "GONE-1", "is_work_item": 1}]
    ok = no_parent_epic(rows) == ["T-1", "D-1"]          # no parent, and a Story parent; an Epic parent and a parent off the tab are not
    src = open(__file__).read()
    ok &= "<>Epic" in NO_EPIC_COND and src.count("' + NO_EPIC" + "_COND + '") == 2 and ('ji_parent_key,"")&" ' + 'tickets') not in src          # the list (block 10) and its count line both use the one rule
    print("panels selftest:", "PASS" if ok else "FAIL"); return 0 if ok else 1


ALERT_CAPS = [60, 210, 20, 10, 1870, 250, 20, 20, 470, 2310]          # blocks 9 and 10 (v1.43c AC77): 1.5 x the 313 blank-category epics (11 Nov), 1.5 x about 1,536 tickets with no parent epic


def alert_details_rows(G, cfg, counts=None, meta=None):
    """Visible 'Alert details' tab: each alert's items under its own heading, side by side. Row 1 heading, row 2 count, row 3 column names,
    row 4 on: a spilled list, plus a per-row link column to the item's system of record (Jira issue, GitLab MR, GitHub PR). Hosts come from data/config.json."""
    counts = counts or ALERT_CAPS
    jh = cfg.get("jira", {}).get("host", "")
    gl = cfg.get("gitlab", {}).get("host", "")
    gh = cfg.get("github", {}).get("host", "")
    jira_link = lambda r: f'=IF(A{{r}}="","",HYPERLINK("https://{jh}/browse/"&A{{r}},"Open in Jira"))'
    blocks = [
        ("1. In progress with no owner", ["key", "group", "status", "age_days"],
         'IFERROR(FILTER({ji_key,ji_group,ji_status,ji_start_age_days},ji_wip=1,ji_owner_kind="ownerless"),"")', "jira"),
        ("2. In progress for longer than the stuck limit", ["key", "group", "age_days", "stuck_limit_days"],
         'IFERROR(FILTER({ji_key,ji_group,ji_start_age_days,ARRAYFORMULA(IF(ji_key<>"",t_stuck_days,""))},ji_wip=1,ISNUMBER(ji_start_age_days),ji_start_age_days>t_stuck_days),"")', "jira"),
        ("3. People over the WIP limit (names are on the Individual tab, wip column)", ["team", "group", "people_over_limit"],
         'IFERROR(FILTER({lv_team,lv_group,lv_people_over_wip_limit},lv_level="Team",lv_people_over_wip_limit>0),"")', None),
        ("4. Throughput or merged changes below the drop threshold", ["group", "jira_done_last_week", "jira_prior_4wk_avg", "merged_last_week", "merged_prior_4wk_avg"],
         'IFERROR(LET(f,FILTER({ARRAYFORMULA(IF(lv_group="*","SBU",lv_group)),lv_done_last_week_main,lv_done_prior4_avg_main,lv_merged_last_week,lv_merged_prior4_avg},lv_level<>"Team",((lv_throughput_drop_alert=1)+(lv_merge_drop_alert=1))>0),HSTACK(INDEX(f,0,1),'
         'ARRAYFORMULA(HYPERLINK("#gid=" & GID_W & "&range=A1",INDEX(f,0,2))),ARRAYFORMULA(HYPERLINK("#gid=" & GID_W & "&range=A1",INDEX(f,0,3))),'
         'ARRAYFORMULA(HYPERLINK("#gid=" & GID_C & "&range=A1",INDEX(f,0,4))),ARRAYFORMULA(HYPERLINK("#gid=" & GID_C & "&range=A1",INDEX(f,0,5))))),"")', None),
        ("5. Open change past the review limit with no first review", ["change_id", "group", "team", "age_days", "platform", "project", "number"],
         'IFERROR(FILTER({cc_change_id,cc_group,cc_team,cc_open_age_days,cc_platform,ARRAYFORMULA(IF(REGEXMATCH(cc_project,"^(appian|docs)/"),cc_project,"personal project")),cc_number},cc_counted=1,cc_state="open",cc_class="normal",cc_first_review_at="",cc_open_age_days>t_first_review_days),"")', "code"),
        ("6. In-progress code-type issue with no linked change activity", ["key", "group", "days_since_linked_activity"],
         'IFERROR(FILTER({ji_key,ji_group,ji_days_since_linked_activity},ji_wip=1,ji_is_code_type=1,((ji_days_since_linked_activity>t_ip_stale_days)+(ji_days_since_linked_activity="")>0)),"")', "jira"),
        ("7. Blocked work (K1): open items in a blocked status, by Group (counts only)", ["group", "blocked", "median_blocked_age_days", "unassigned"],
         'ARRAYFORMULA(INDEX(d_blocked,2,1):INDEX(d_blocked,ROWS(d_blocked),4))', None),
        ("8. Open incidents (I2): by customer or internal and priority (counts only)", ["incidents", "priority", "open_now", "median_age_days", "p85_age_days", "open_over_30_days"],
         'LET(f,FILTER(INDEX(d_incopen,2,1):INDEX(d_incopen,ROWS(d_incopen),6),1-(((INDEX(d_incopen,2,2):INDEX(d_incopen,ROWS(d_incopen),2)="Blocker")+(INDEX(d_incopen,2,2):INDEX(d_incopen,ROWS(d_incopen),2)="Not Set")>0)*(INDEX(d_incopen,2,3):INDEX(d_incopen,ROWS(d_incopen),3)=0))),HSTACK(ARRAYFORMULA(IF(INDEX(f,0,1)="customer","Customer incidents","Internal incidents")),INDEX(f,0,2),INDEX(f,0,3),INDEX(f,0,4),INDEX(f,0,5),INDEX(f,0,6)))', None),
        ("9. No category (DATA INTEGRITY): epics with no Work Category, by project", ["key", "project", "group"],
         'IFERROR(SORT(FILTER({ji_key,ji_project,ji_group},ji_type="Epic",ji_work_category=""),2,TRUE,1,TRUE),"")', "jira"),
        ("10. No category (DATA INTEGRITY): tickets with no parent epic (sub-tasks are not tickets)", ["key", "project", "group"],
         'IFERROR(FILTER({ji_key,ji_project,ji_group},ji_is_work_item=1,' + NO_EPIC_COND + '),"")', "jira"),
    ]
    import links as _LG          # v1.41 3c: block 4 counts link to the item tabs (an array HYPERLINK, so the spilled list keeps its size)
    blocks = [(t_, c_, f_.replace('" & GID_W & "', str(_LG._gid("W"))).replace('" & GID_C & "', str(_LG._gid("C"))), k_) for t_, c_, f_, k_ in blocks]
    widths = [len(b[1]) + (1 if b[3] else 0) + 1 for b in blocks]
    ncol = sum(widths)
    nrow = 3 + max(counts)
    rows = [["" for _ in range(ncol)] for _ in range(nrow)]
    starts = []
    c = 0
    for i, (title, cols, f, kind) in enumerate(blocks):
        starts.append(c)
        rows[0][c] = title
        rows[1][c] = (f'=alert{i+1}&" in the Dashboard count"' if i < 6 else "Counts only, the same numbers as the Dashboard chart and table; no names." if i < 8 else
                      '=COUNTIFS(ji_type,"Epic",ji_work_category,"")&" epics have no Work Category. DATA INTEGRITY: no default category is applied; they show as No category in the work mix."' if i == 8 else
                      '=SUMPRODUCT((ji_is_work_item=1)*' + NO_EPIC_COND + ')&" tickets have no parent epic, so they cannot inherit a category. DATA INTEGRITY: no default category is applied."')
        names = list(cols) + (["link"] if kind else [])
        for j, name in enumerate(names):
            rows[2][c + j] = ALERT_HEADERS.get(name, name)          # plain reader words, no field names (inbox 104)
        if i in (3, 6, 7):
            pass          # block 4 (v1.41: a fixed table, one formula per cell, so every count is a link with its own note), blocks 7 and 8: one formula per cell below, so every number can be a link (v1.31)
        else:
            rows[3][c] = "=" + f
        lc = c + len(cols)
        if kind:
            for k in range(counts[i]):
                r = 4 + k
                if kind == "jira":
                    rows[3 + k][lc] = f'=IF({col_letter(c)}{r}="","",HYPERLINK("https://{jh}/browse/"&{col_letter(c)}{r},"Open in Jira"))'
                else:
                    ch, pl, pr, nm = (col_letter(c + x) for x in (0, 4, 5, 6))
                    real = f"INDEX(cc_project,MATCH({ch}{r},cc_change_id,0))"          # the visible project may read 'personal project'; the link keeps the real path (A51)
                    import links as _LC2
                    nsre = "^(" + "|".join(cfg.get("items", {}).get("code_namespaces", ["appian", "docs"])) + ")/"
                    # AC65: a change in a personal namespace has a username in its URL, so its link goes to the Code changes tab; the others open the change itself
                    rows[3 + k][lc] = (f'=IF({ch}{r}="","",IF(REGEXMATCH({real},"{nsre}"),HYPERLINK(IF({pl}{r}="gitlab","https://{gl}/"&{real}&"/-/merge_requests/"&{nm}{r},"https://{gh}/"&{real}&"/pull/"&{nm}{r}),'
                                       f'"Open in "&IF({pl}{r}="gitlab","GitLab","GitHub")),HYPERLINK("#gid={_LC2._gid("C")}&range=A1","Open the Code changes tab (personal project)")))')
        if i == 0 and cfg.get("texts", {}).get("jira_no_owner_jql") and jh:
            import urllib.parse
            url = "https://" + jh + "/issues/?jql=" + urllib.parse.quote(cfg["texts"]["jira_no_owner_jql"])
            rows[1][c + 2] = f'=HYPERLINK("{url}","Open the same search live in Jira (its count can differ if tickets changed since the as-of)")'
        c += widths[i]
    # ---- v1.41 (3c, A66): every link in Alerts blocks 2, 4, 7 and 8 opens the item tab (counts only, no names, no usernames); a block no item-tab column can list says so in plain words
    import links as _LC          # A61/A66: the item-tab links
    wi_link = lambda key, text: "=" + _LC.link(key, '"' + text + '"')
    rows[1][starts[0] + 2] = "No item-tab list: the owner is not on the item tabs. Each row below links to its own ticket."
    rows[1][starts[1] + 2] = wi_link(_LC.work_open("wip", "sbu"), "Open the Work items tab: Stuck now = 1 (the same items as this list)")
    rows[1][starts[2] + 1] = "No list can show this without people's names."
    rows[1][starts[3] + 1] = wi_link(_LC.work_period("fin", "wk", "sbu"), "Open the Work items tab: Finished last week = 1")
    rows[1][starts[3] + 3] = wi_link(_LC.gl_merged("wk", "sbu"), "Open the Code changes tab: Merged last week = 1")
    rows[1][starts[3] + 4] = "Changes are ordinary changes only, counted once across GitLab and GitHub: the same basis as the Dashboard's shipping-code row. A Group marked (below the limit) is under t_throughput_drop of its average in Jira throughput or in merged changes."
    # block 4: one row per level (SBU, each Group, Other, Unknown), always shown; the row's own cells are exact links (v1.41 3c, the user's R4 example)
    c4 = starts[3]
    lv_rows = [("SBU", "*", "SBU", "sbu")] + [("Group", g, g, ("group", g)) for g in list(cfg["groups"]) + [cfg["labels"]["other"], cfg["labels"]["unknown"]]]
    for k, (lvl, grp, label, sc_) in enumerate(lv_rows):
        m_ = f'MATCH(1,INDEX((lv_level="{lvl}")*(lv_group="{grp}"),0),0)'
        gl_ = lambda col, w: f'INDEX({col},{m_})'
        rows[3 + k][c4] = f'=IFERROR("{label}"&IF(INDEX(lv_throughput_drop_alert,{m_})+INDEX(lv_merge_drop_alert,{m_})>0," (below the limit)",""),"")'
        for j, (col, key) in enumerate((("lv_done_last_week_main", _LC.work_period("fin", "wk", sc_)), ("lv_done_prior4_avg_main", _LC.work_period("fin", "wk", sc_)),
                                        ("lv_merged_last_week", _LC.gl_merged("wk", sc_)), ("lv_merged_prior4_avg", _LC.gl_merged("wk", sc_)))):
            rows[3 + k][c4 + 1 + j] = "=IFERROR(" + _LC.link(key, f"INDEX({col},{m_})") + ',"")'
    rows[1][starts[4] + 2] = f'=HYPERLINK("#gid={_LC._gid("C")}&range=A1","Open the Code changes tab: filter State = open and Class = normal. Each change below links to its own page.")'
    rows[1][starts[5] + 2] = "No item-tab list: the quiet test uses linked code activity, which is not on the item tabs. Each row below links to its own ticket."
    # block 7: blocked work by Group (rows follow d_blocked: the Groups, Other, Unknown, then the SBU total); every Group name, Other and Unknown included, filters the item tab by Group
    gnames = list(cfg["groups"]) + [cfg["labels"]["other"], cfg["labels"]["unknown"], "SBU"]
    c7 = starts[6]
    for k, gname in enumerate(gnames):
        sc_ = "sbu" if gname == "SBU" else ("group", gname)
        ix = lambda col: f"INDEX(d_blocked,{k + 2},{col})"
        rows[3 + k][c7] = "=" + ix(1)
        rows[3 + k][c7 + 1] = "=" + _LC.link(_LC.work_open("blocked", sc_), ix(2))
        rows[3 + k][c7 + 2] = "=" + _LC.link(_LC.work_open("blocked", sc_), f'IF({ix(3)}="","n/a",{ix(3)})')
        rows[3 + k][c7 + 3] = "=" + _LC.link(_LC.work_open("blocked", sc_), ix(4))          # unassigned: a list link to the Group's blocked items (the owner is not on the item tabs; the note says so)
    # block 8: open incidents by split and priority (every priority row), item-tab links by Kind and Priority
    c8 = starts[7]
    k = 0
    for sp_ in ("customer", "internal"):
        proj = "EA" if sp_ == "customer" else "IA"
        for pr_ in ["All"] + list((meta or {}).get("inc_priorities", [])):
            ix = lambda col, kk=k: f"INDEX(d_incopen,{kk + 2},{col})"
            rows[3 + k][c8] = "=" + ix(1)
            rows[3 + k][c8 + 1] = "=" + ix(2)
            rows[3 + k][c8 + 2] = "=" + _LC.link(_LC.inc_open(proj, "sbu", pr_), ix(3))
            rows[3 + k][c8 + 3] = "=" + _LC.link(_LC.inc_open(proj, "sbu", pr_), f'IF({ix(4)}="","n/a",{ix(4)})')
            rows[3 + k][c8 + 4] = "=" + _LC.link(_LC.inc_open(proj, "sbu", pr_), f'IF({ix(5)}="","n/a",{ix(5)})')
            rows[3 + k][c8 + 5] = "=" + _LC.link(_LC.inc_open(proj, "sbu", pr_, over30=True), ix(6))
            k += 1
    rows[0] = [scrub_codes(x) for x in rows[0]]
    return rows, starts


FAIL_LISTS = []   # (label, id range, group range, team range, conditions)
_cn = 'cc_counted=1,cc_class="normal",cc_state<>"closed"'
_c = lambda extra: _cn + "," + extra
FAIL_LISTS = [
    ("C1", "cc", _c("cc_c1_pass=0")), ("C2", "cc", _c("cc_c2_pass=0")), ("C3", "cc", _c("cc_c3_pass=0")), ("C4", "cc", _c("cc_c4_pass=0")),
    ("C5", "cc", _c("cc_lines_for_c5>t_mr_size_lines")),
    ("C6", "cc", 'cc_counted=1,cc_class="normal",cc_state<>"closed",((cc_state="merged")*(cc_first_review_at="")+(cc_hours_to_first_review>t_first_review_days*hpd)+(cc_state="open")*(cc_first_review_at="")*(cc_open_age_days>t_first_review_days)>0)'),
    ("C7", "cc", 'cc_counted=1,cc_class="normal",cc_state="open",((cc_draft=0)+(t_c7_include_drafts=1)>0),cc_days_since_activity>t_open_stale_days'),
    ("C8", "cc", 'cc_counted=1,cc_class="normal",cc_state="open",cc_draft=1,cc_open_age_days>t_open_stale_days'),
    ("J1", "ji", "ji_j1_pass=0"), ("J2", "ji", "ji_wip=1,ji_days_since_update>t_ip_stale_days"), ("J3", "ji", "ji_j3_pass=0"),
    ("J4", "ji", "ji_j4_pass=0"), ("J5", "ji", "ji_j5_pass=0"), ("J6", "ji", "ji_j6_pass=0"),
    ("A1", "cc", 'cc_counted=1,cc_class="normal",cc_key_state<>"linked"'),
    ("A2", "ji", 'ji_wip=1,ji_is_code_type=1,((ji_days_since_linked_activity>t_ip_stale_days)+(ji_days_since_linked_activity="")>0)'),
    ("A3", "ji", "ji_a3_status_lag=1"), ("A4", "ji", "ji_a4_no_code=1"),
    ("A5", "cc", 'cc_counted=1,cc_class="normal",cc_state="merged",cc_key_state="no_key"'),
]
FAIL_ROWS = 12000


def failing_rows():
    """Failing lists for every check: three columns each (id, group, team), a spilled FILTER from row 2. Row 1 is the only header row."""
    hdr, f = [], []
    for label, pre, cond in FAIL_LISTS:
        idr = "cc_change_id" if pre == "cc" else "ji_key"
        for what, rng in (("id", idr), ("group", f"{pre}_group"), ("team", f"{pre}_team")):
            hdr.append(f"{label}_{what}")
            f.append(f'=IFERROR(FILTER({rng},{cond}),"")')
    return [hdr, f]


# Stat strips under the 6/12 charts on Charts (detail): (label, dk cell, number format). Six cells each (AC44b); P1 adds net for last week and last month.
STRIPS = {
    "I1C": [("Last week resolved", "dk_i1c_wk_res", "0"), ("Week over week", "dk_i1c_wk_wow", "+0;-0;0"), ("Average of the 4 weeks before", "dk_i1c_wk_avg4", "0.0"),
           ("Net last week", "dk_i1c_wk_net", "+0;-0;0"), ("Last month resolved", "dk_i1c_mo_res", "0"), ("Month over month", "dk_i1c_mo_mom", "+0;-0;0"),
           ("Net last month", "dk_i1c_mo_net", "+0;-0;0"), ("12 months resolved (first month partial)", "dk_i1c_yr_res", "#,##0")],
    "I1I": [("Last week resolved", "dk_i1i_wk_res", "0"), ("Week over week", "dk_i1i_wk_wow", "+0;-0;0"), ("Average of the 4 weeks before", "dk_i1i_wk_avg4", "0.0"),
           ("Net last week", "dk_i1i_wk_net", "+0;-0;0"), ("Last month resolved", "dk_i1i_mo_res", "0"), ("Month over month", "dk_i1i_mo_mom", "+0;-0;0"),
           ("Net last month", "dk_i1i_mo_net", "+0;-0;0"), ("12 months resolved (first month partial)", "dk_i1i_yr_res", "#,##0")],
    "B1": [("Last week fixed", "dk_b1_wk_fixed", "0"), ("Week over week", "dk_b1_wk_wow", "+0;-0;0"), ("Average of the 4 weeks before", "dk_b1_wk_avg4", "0.0"),
           ("Net last week", "dk_b1_wk_net", "+0;-0;0"), ("Last month fixed", "dk_b1_mo_fixed", "0"), ("Month over month", "dk_b1_mo_mom", "+0;-0;0"),
           ("Net last month", "dk_b1_mo_net", "+0;-0;0"), ("12 months fixed (first month partial)", "dk_b1_yr_fixed", "#,##0")],
    "M1": [("Features, 12 months (%)", "dk_m1_feature_yr", "0.0"), ("Support, 12 months (%)", "dk_m1_support_yr", "0.0"), ("Ops & Maintenance, 12 months (%)", "dk_m1_ops_yr", "0.0"),
           ("No category (% of all finished)", "dk_m1_none_yr", "0.0"), ("Features, last week (%)", "dk_m1_feature_wk", "0.0"), ("Finished tickets, 12 months", "dk_m1_finished_yr", "#,##0")],
    "P1": [("Last week finished", "dk_p1_wk_fin", "0"), ("Week over week", "dk_p1_wk_wow", "+0;-0;0"), ("Average of the 4 weeks before", "dk_p1_wk_avg4", "0"),
           ("Net last week", "dk_p1_wk_net", "+0;-0;0"), ("Last month finished", "dk_p1_mo_fin", "0"), ("Month over month", "dk_p1_mo_mom", "+0;-0;0"),
           ("Net last month", "dk_p1_mo_net", "+0;-0;0"), ("12 months finished (first month partial)", "dk_p1_yr_fin", "#,##0")],
    "P4": [("Last week merged", "dk_p4_wk", "0"), ("Week over week", "dk_p4_wow", "+0;-0;0"), ("Average of the 4 weeks before", "dk_p4_avg4", "0"),
           ("Last month merged", "dk_p4_mo", "0"), ("Month over month", "dk_p4_mom", "+0;-0;0"), ("12 months merged (first month partial)", "dk_p4_yr", "#,##0")],
    "P5": [("Last week median hours", "dk_p5_wk", "0.0"), ("Week over week", "dk_p5_wow", "+0.0;-0.0;0.0"), ("Median of the 4 weeks before (all changes)", "dk_p5_avg4", "0.0"),
           ("Last month median hours", "dk_p5_mo", "0.0"), ("Month over month", "dk_p5_mom", "+0.0;-0.0;0.0"), ("12 months median (all changes; first month partial)", "dk_p5_yr", "0.0")],
}

# v1.22: stat strips under the 6/12 charts on the Dashboard: [(row label or None, cells)]
DASH_STRIPS = {}      # v1.24: no stat strips on the Dashboard; the answer cards state the figures (AC44b)


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        sys.exit(selftest())
