"""Data tab column specs: name, kind, unit, source, definition. Used to write the tabs, name ranges, and build Data_Dictionary."""
import datetime as dt, json, os

_JF = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "config.json")))["jira"]["fields"]          # the Jira field ids named in the definitions below (config jira.fields)

UTC = dt.timezone.utc
EPOCH = dt.datetime(1899, 12, 30, tzinfo=UTC)
FMT_DT = 'yyyy-mm-dd"T"hh:mm:ss"Z"'
FMT_DATE = "yyyy-mm-dd"


def serial(d):
    return round((d - EPOCH).total_seconds() / 86400.0, 6)


def date_serial(s):
    """'YYYY-MM-DD' (or ISO) text -> integer day serial"""
    y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
    return (dt.date(y, m, d) - dt.date(1899, 12, 30)).days


# (column, kind, unit, definition)  kind: text int num dt date
JI = [
    ("key", "text", "", "Jira issue key"),
    ("type", "text", "", "Jira issue type name"),
    ("is_work_item", "int", "0/1", "1 unless the type is an initiative or epic (those appear only in backlog size)"),
    ("is_code_type", "int", "0/1", "1 when the type is in the code-type list in data/config.json"),
    ("status", "text", "", "Current status name"),
    ("status_category", "text", "", "Current status category: new, indeterminate (in progress), done"),
    ("population", "text", "", "done = Done by status-category change in the 12-month window; open = not Done now"),
    ("owner", "text", "", "Credited person: assignee at the final Done for finished items, current assignee for open items; Ownerless or Unmapped when none or not on the roster"),
    ("owner_kind", "text", "", "person, ownerless (no assignee), or unmapped (assignee not on the roster)"),
    ("team", "text", "", "Team of the owner on the event date (final Done date, or as-of for open items); Ownerless or Unmapped as labels"),
    ("group", "text", "", "Group of the owner on the event date; for Ownerless and Unmapped items the Group comes from the Jira group field, Other if not a listed group, Unknown if empty"),
    ("field_group", "text", "", "Raw value of the Jira group field"),
    ("priority", "text", "", "Jira priority name"),
    ("created", "dt", "UTC", "Created timestamp"),
    ("first_start", "dt", "UTC", "Start: first transition into an In Progress category; issues that skip In Progress use the first transition out of To Do"),
    ("first_start_basis", "text", "", "in_progress or skip_in_progress"),
    ("final_done", "dt", "UTC", "Done: last transition into the Done category"),
    ("updated", "dt", "UTC", "Last updated timestamp at the as-of time"),
    ("parent_key", "text", "", "Parent epic or initiative key"),
    ("mr_field_present", "text", "Y/N", "Whether the Jira merge-request URL field is set (recorded, not required)"),
    ("resolution", "text", "", "Resolution name (blank if none)"),
    ("series", "text", "", "Throughput series for finished work items: main, wont_do, duplicate"),
    ("created_week", "date", "UTC", "ISO week (Monday, UTC) of created"),
    ("done_week", "date", "UTC", "ISO week (Monday, UTC) of the final Done"),
    ("wip", "int", "0/1", "1 for work items in an In Progress category at the as-of time"),
    ("in_cycle_pop", "int", "0/1", "1 for finished main-series work items with a start and a final Done (cycle time population)"),
    ("cycle_days", "num", "days", "Final Done minus first start"),
    ("lead_days", "num", "days", "Final Done minus created (finished main-series work items)"),
    ("age_days", "num", "days", "As-of minus created (open items)"),
    ("age_whole_days", "int", "days", "Whole days since created (floor); the backlog age buckets use it"),
    ("start_age_days", "num", "days", "As-of minus first start (work items in progress)"),
    ("days_since_update", "num", "days", "As-of minus updated (open items)"),
    ("group_p85_cycle_days", "num", "days", "P85 cycle time of the item's Group, or of the SBU when the Group has fewer than 30 finished items"),
    ("p85_basis", "text", "", "group or sbu: which P85 the previous column uses"),
    ("age_over_group_p85", "int", "0/1", "1 when an in-progress work item's age since start exceeds its P85"),
    ("j1_pass", "int", "0/1", "J1: in progress has an owner (1 pass, 0 fail; blank when not in progress)"),
    ("j3_pass", "int", "0/1", "J3: in progress not older than its group's P85 cycle time"),
    ("j4_pass", "int", "0/1", "J4: finished work item has a resolution"),
    ("j5_pass", "int", "0/1", "J5: finished work item had an assignee at the final Done"),
    ("j6_pass", "int", "0/1", "J6: open work item has a parent epic or initiative"),
    ("linked_changes", "int", "count", "Counted changes (MRs and PRs) linked to this issue through Code_Jira_Links"),
    ("linked_merged", "int", "count", "Of those, merged"),
    ("linked_open", "int", "count", "Of those, still open"),
    ("linked_merged_incl_mirrors", "int", "count", "Merged linked changes including mirror copies (the same commit merged); A4 uses it"),
    ("wip_prev_week", "int", "0/1", "1 when the work item was in an In Progress category one week before the as-of (week-over-week change)"),
    ("no_owner_wip_prev_week", "int", "0/1", "1 when it was also unassigned then"),
    ("days_since_linked_activity", "num", "days", "As-of minus the latest last-activity time among linked changes"),
    ("a3_status_lag", "int", "0/1", "A3: open work item whose linked changes are all merged (and there is at least one)"),
    ("a4_no_code", "int", "0/1", "A4: finished code-type work item with no merged linked change"),
    ("blocked", "int", "0/1", "K1: 1 for an open work item whose current status is in the blocked status list (Blocked)"),
    ("blocked_age_days", "num", "days", "K1: as-of minus the time the item last entered a blocked status (blocked items only)"),
    ("level", "text", "", "Attribution level by the ladder (A53) at the finish date, or the as-of for open items: Team, Group or SBU (SBU-only tickets count in the SBU row only)"),
    ("tag_conflict", "int", "0/1", "1 when the ticket is ours at some level and another of its Team, Group or SBU tags is not Automation, or its Team belongs to another Automation Group"),
    ("sbu", "text", "", "SBU tag of the ticket at the same date"),
    ("project", "text", "", "Jira project key"),
    ("ours_c", "int", "0/1", "1 when the ticket was ours (by the ladder) at its creation date; created counts use the Group and Team at creation"),
    ("group_c", "text", "", "Group by the ladder at the creation date (SBU only when only the SBU tag applied)"),
    ("team_c", "text", "", "Team by the ladder at the creation date (No team when none)"),
    ("work_category", "text", "", "Work Category (Customer Feature, Internal Feature, Ops & Maintenance, Support): an epic or initiative carries its own; every other ticket takes its parent epic's value at the finish date (today for open work); blank when neither has one"),
    ("stalled_days", "int", "days", "Open epics and initiatives only: days since the newest update (Jira updated, UTC) among the OPEN child tickets (an initiative: the tickets under its child epics; closed tickets and sub-tasks are ignored); with no child tickets at all, the days the item has been open; blank when every child ticket is done, and for everything that is not an open epic or initiative"),
    ("kids_done", "int", "0/1", "Open epics and initiatives only: 1 when it has child tickets and every one of them is done (an epic that could be closed), else 0; blank for everything else"),
]
JT = [
    ("issue", "text", "", "Jira issue key"),
    ("from_status", "text", "", "Status before the transition"),
    ("to_status", "text", "", "Status after the transition"),
    ("from_category", "text", "", "Status category before"),
    ("to_category", "text", "", "Status category after"),
    ("changed_at", "dt", "UTC", "Transition timestamp"),
    ("days_in_from_status", "num", "days", "Time spent in from_status: this transition minus the previous one (or created)"),
    ("in_cycle_pop", "int", "0/1", "1 when the issue is in the cycle-time population (time-in-status population)"),
]
DS = [
    ("date", "date", "UTC", "Day"),
    ("status_category", "text", "", "new, indeterminate, or done"),
    ("count", "int", "count", "Work items in the category at the end of the day; done counts items whose final Done is on or before the day (starts at 0 on window day 1)"),
]
CC = [
    ("change_id", "text", "", "gitlab:<project id>!<iid> or github:<repo>#<number>"),
    ("platform", "text", "", "gitlab or github"),
    ("project", "text", "", "Repository path"),
    ("number", "text", "", "Merge request iid or pull request number"),
    ("author", "text", "", "Author (roster name, or Unmapped)"),
    ("author_kind", "text", "", "person or unmapped"),
    ("team", "text", "", "Author's team on the merge date (as-of for open changes)"),
    ("group", "text", "", "Author's group on the same date"),
    ("class", "text", "", "normal, bot, revert, docs, backport, release"),
    ("state", "text", "", "open, merged, closed"),
    ("draft", "int", "0/1", "Draft flag"),
    ("counted", "int", "0/1", "1 when the change is counted once; 0 for a mirror copy (same head commit as another change)"),
    ("opened", "dt", "UTC", "Opened timestamp"),
    ("merged_at", "dt", "UTC", "Merged timestamp"),
    ("closed_at", "dt", "UTC", "Closed-without-merge timestamp"),
    ("lines", "int", "lines", "Changed lines (added plus removed)"),
    ("lines_excl", "int", "lines", "Changed lines without lockfiles and generated files (GitHub: from the file list where the total exceeds the review threshold, else the total)"),
    ("desc_nonws_len", "int", "chars", "Description length, non-whitespace characters (length only; text is never stored)"),
    ("merged_by", "text", "", "Merger login or username (blank when not fetched)"),
    ("self_merged", "int", "0/1", "1 when merged by its author"),
    ("head_sha", "text", "", "Head commit SHA"),
    ("mirror_key", "text", "", "Mirror pair key (head SHA plus repo)"),
    ("first_review_at", "dt", "UTC", "First review: first approval or non-system note by someone other than the author, bots excluded"),
    ("approvals", "int", "count", "Approvals"),
    ("review_detail", "text", "", "fetched when review detail was pulled for this change"),
    ("last_activity_at", "dt", "UTC", "Last activity timestamp"),
    ("key_state", "text", "", "linked, other_project_key, or no_key (any key linked counts as linked)"),
    ("primary_key", "text", "", "First Jira key found, in source order"),
    ("open_age_days", "num", "days", "As-of minus opened (open changes)"),
    ("days_since_activity", "num", "days", "As-of minus last activity (open changes)"),
    ("open_to_merge_days", "num", "days", "Merged minus opened (merged changes, draft time included)"),
    ("hours_to_first_review", "num", "hours", "First review minus opened"),
    ("merged_week", "date", "UTC", "ISO week (Monday, UTC) of merge"),
    ("created_week", "date", "UTC", "ISO week (Monday, UTC) of opened"),
    ("c1_pass", "int", "0/1", "C1: has a Jira key (state linked); normal counted changes only"),
    ("c2_pass", "int", "0/1", "C2: description has at least 20 non-whitespace characters"),
    ("c3_pass", "int", "0/1", "C3: had a review before merge (merged changes)"),
    ("c4_pass", "int", "0/1", "C4: not merged by its author without a review (merged changes with a known merger)"),
    ("lines_for_c5", "int", "lines", "Size used by C5 for normal counted changes (excluding lockfiles and generated files); C5 compares it to the size threshold in the Sheet"),
    ("attrib", "text", "", "ticket when the primary linked ticket is ours at the merge date (A53), author when the author's roster Group and Team decide (also when the primary linked ticket is untagged or tagged outside Automation at the merge date, or when no ticket is linked: A77)"),
    ("level", "text", "", "Attribution level: Team, Group or SBU (blank when the author is not mapped)"),
    ("comp_kind", "text", "", "For a merged, counted, ordinary change by a roster person: ours, other (the primary linked ticket is tagged outside Automation) or untagged (that ticket has no tag); blank for other changes (A74)"),
]
OI = [
    ("kind", "text", "", "other (a ticket of one of our people tagged outside Automation) or untagged (no Team, Group or SBU tag); the few tickets of our people that are not in Jira_Issues (A74); no person or title is stored; the Jira key is in the last column (v1.43f, AC65)"),
    ("type", "text", "", "Jira issue type name"),
    ("status_category", "text", "", "Current status category: new, indeterminate (in progress), done"),
    ("created", "dt", "UTC", "Created timestamp"),
    ("final_done", "dt", "UTC", "Done timestamp, blank when open"),
    ("owning", "text", "", "Owning SBU, or Group when no SBU is set (blank for untagged)"),
    ("key", "text", "", "Jira key of the ticket (v1.43f, AC65): the only identifier stored; shown as a link on Work items"),
]
CL = [
    ("change_id", "text", "", "Change id"),
    ("jira_key", "text", "", "Key as found in the change"),
    ("source", "text", "", "Where it was found: title, branch, description, commit"),
    ("primary", "int", "0/1", "1 for the first key found in source order"),
    ("key_check", "text", "", "linked, other_project_key, or not_found against the Jira extract"),
    ("resolved_jira_key", "text", "", "Key in the extract after alias resolution (blank unless linked)"),
    ("alias_source", "text", "", "How the key was resolved: same_key, direct, jira_resolved, changelog_key_field, inferred_project_rename_same_number, not_found"),
]
CR = [
    ("change_id", "text", "", "Change id"),
    ("platform", "text", "", "gitlab or github"),
    ("reviewer", "text", "", "Roster reviewer. One row per review event (GitLab approval or non-system note; GitHub review) on a change that is not the reviewer's own; bots excluded"),
    ("reviewer_team", "text", "", "Reviewer's team as of the as-of date"),
    ("reviewer_group", "text", "", "Reviewer's group as of the as-of date"),
    ("review_time", "dt", "UTC", "Time of the review event"),
    ("review_week", "date", "UTC", "ISO week (Monday, UTC) of the review event"),
    ("review_type", "text", "", "approval or comment"),
]
SH = [
    ("kind", "text", "", "week (end of an ISO week), month (end of a calendar month), or asof"),
    ("label", "text", "", "Plain label of the period"),
    ("snapshot_at", "dt", "UTC", "The moment the state is measured: 00:00 UTC after the period's last day (the as-of timestamp for the asof row)"),
    ("level", "text", "", "SBU, Group or Team: which rows this row covers (one row per snapshot and level entry; no person rows)"),
    ("group", "text", "", "Group of the entry (* on the SBU row). Each item is attributed to the Group and Team its owner had at the snapshot (dated roster history); ownerless items go to the Ownerless Team and unmapped owners to Unmapped"),
    ("team", "text", "", "Team of the entry (* on the SBU and Group rows)"),
    ("open_work_items", "int", "count", "Work items open at that moment, replayed from the changelog (items in the extract only)"),
    ("in_progress", "int", "count", "Work items in an In Progress category at that moment"),
    ("in_progress_no_owner", "int", "count", "Of those, with no assignee at that moment (replayed from assignee changes)"),
    ("in_progress_stuck", "int", "count", "Of those, started longer ago at that moment than the Group's 85th-percentile cycle time (the limit as of now)"),
]
INC = [
    ("project", "text", "", "Jira project of the incident: EA (customer incident) or IA (internal incident)"),
    ("split", "text", "", "customer (EA) or internal (IA)"),
    ("type", "text", "", "Jira issue type (any type: Customer Incident, Help, Internal, Internal incident); no title, description, customer, reporter or assignee is stored; the Jira key is the only identifier (AC65, v1.43f)"),
    ("priority", "text", "", "Jira priority name"),
    ("created", "dt", "UTC", "Created timestamp (incidents are measured at the Sheet as-of, Metrics as_of_utc: incidents created after it are not listed)"),
    ("final_done", "dt", "UTC", "Final Done timestamp when it is on or before the Sheet's as-of; blank for an incident that is open at the as-of"),
    ("resolution", "text", "", "Resolution name for a resolved incident (blank when Jira has none)"),
    ("wontdo_dup", "int", "0/1", "1 when the resolution is Won't Do or Duplicate (still counted as resolved)"),
    ("open_at_asof", "int", "0/1", "1 when the incident is not resolved at the Sheet's as-of"),
    ("age_days", "num", "days", "As-of minus created, for an open incident"),
    ("ttr_days", "num", "days", "Final Done minus created, for a resolved incident"),
    ("group", "text", "", "Jira Group field of the incident (" + _JF["group"] + ") when it is a roster Group; otherwise Other Group (tied by Team). An incident with neither a roster Group nor a roster Team is not in this tab at all (v1.28)"),
    ("team", "text", "", "Jira Team field of the incident (" + _JF["team"] + ", the Team's name) when it is a roster Team; blank otherwise (v1.28)"),
    ("level", "text", "", "Attribution level by the ladder at the event date: Team, Group or SBU (SBU-only incidents count in the SBU row only)"),
    ("ours_c", "int", "0/1", "1 when the incident was ours by the ladder at its creation date; an incident untagged at creation is not in the created counts"),
    ("group_c", "text", "", "Group by the ladder at the creation date (SBU only when only the SBU tag applied); blank when not ours then"),
    ("team_c", "text", "", "Team by the ladder at the creation date (No team when none); blank when not ours then"),
    ("key", "text", "", "Jira key of the incident (EA or IA, v1.43f, AC65): the only identifier stored; shown as a link on Work items"),
]
SPECS = {
    "Jira_Issues": ("ji", JI),
    "Jira_Transitions": ("jt", JT),
    "Daily_Status_Counts": ("ds", DS),
    "Code_Changes": ("cc", CC),
    "Code_Jira_Links": ("cl", CL),
    "Code_Reviews": ("cr", CR),
    "State_History": ("sh", SH),
    "Incident_Issues": ("ii", INC),
    "Other_Items": ("oi", OI),
}
RENAME = {  # spec column -> derive dict key
    ("Jira_Issues", "group"): "group",
}


def conv(kind, v):
    if v is None or v == "":
        return ""
    if kind == "dt":
        return serial(v) if hasattr(v, "year") else serial(_p(v))
    if kind == "date":
        return date_serial(v) if isinstance(v, str) else v
    if kind in ("int",):
        return int(v)
    if kind == "num":
        return round(float(v), 4)
    return v


def _p(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def tab_rows(tab, rows):
    prefix, spec = SPECS[tab]
    out = [[c[0] for c in spec]]
    keys = [c[0] for c in spec]
    kinds = [c[1] for c in spec]
    for r in rows:
        out.append([conv(k, r.get(n)) for n, k in zip(keys, kinds)])
    return out
