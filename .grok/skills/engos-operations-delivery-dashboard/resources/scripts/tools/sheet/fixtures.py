#!/usr/bin/env python3
"""Generate the small fictional fixtures: `clean` (no alert should fire) and `seeded` (each alert fires).
Output: tools/sheet/fixture/<case>/ (input CSVs and config.json). Deterministic. Fictional names only (AC56)."""
import csv, json, os, random, shutil, datetime as dt

UTC = dt.timezone.utc
ASOF = dt.datetime(2026, 11, 8, 20, 28, 50, tzinfo=UTC)
OUT = os.path.join(os.path.dirname(__file__), "fixture")


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def w(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        cw = csv.DictWriter(f, fieldnames=header)
        cw.writeheader()
        for r in rows:
            cw.writerow({k: r.get(k, "") for k in header})


PEOPLE = [  # name, group, team, jira, gitlab, github
    ("Ann Example", "CLEAN GROUP", "Red Team"), ("Bob Example", "CLEAN GROUP", "Red Team"),
    ("Cy Example", "CLEAN GROUP", "Blue Team"), ("Di Example", "SEEDED GROUP", "Green Team"),
    ("Ed Example", "SEEDED GROUP", "Green Team"), ("Fay Example", "", ""),
]


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def rel(p):
    return os.path.relpath(p, REPO)


def uname(n):
    return n.lower().replace(" ", ".")


def build(case):
    global ASOF
    ASOF = dt.datetime(2026, 10, 4, 20, 28, 50, tzinfo=UTC) if case == "stale" else dt.datetime(2026, 11, 8, 20, 28, 50, tzinfo=UTC)
    seeded = case in ("seeded", "alerts", "stale")
    split = case in ("alerts", "stale")     # one Sheet holds both: the CLEAN GROUP never alerts, the SEEDED GROUP fires every alert
    rnd = random.Random(11)
    d = os.path.join(OUT, case)
    shutil.rmtree(d, ignore_errors=True)
    jd, gd, hd = [os.path.join(d, "extracts", x) for x in ("jira", "gitlab", "github")]
    os.makedirs(jd), os.makedirs(gd), os.makedirs(hd)
    # roster
    w(os.path.join(d, "roster.csv"), "name,chart_name,manager,title,group,team,start_date,end_date,note".split(","),
      [{"name": n, "chart_name": n, "manager": "Fay Example" if n != "Fay Example" else "", "title": "Engineer", "group": g, "team": t, "note": "fixture"} for n, g, t in PEOPLE])
    w(os.path.join(d, "roster_history.csv"), "person,effective_from,effective_to,group,team".split(","),
      [{"person": n, "effective_from": "2026-01-01", "effective_to": "", "group": g, "team": t} for n, g, t in PEOPLE])
    ihead = "person,home_username,home_source,jira_account_id,jira_email,jira_confidence,jira_reason,gitlab_username,gitlab_id,gitlab_confidence,gitlab_reason,github_login,github_confidence,github_reason".split(",")
    w(os.path.join(d, "identity.csv"), ihead,
      [{"person": n, "home_username": uname(n), "jira_account_id": "acct-" + uname(n), "jira_confidence": "exact", "gitlab_username": uname(n),
        "gitlab_confidence": "exact", "github_login": uname(n).replace(".", "-"), "github_confidence": "exact"} for n, g, t in PEOPLE])
    open(os.path.join(jd, "as_of.txt"), "w").write(iso(ASOF))
    # ------------------------------------------------------------ jira
    eng = [p for p in PEOPLE if p[1]]
    weeks = []
    mon = dt.datetime(ASOF.year, ASOF.month, ASOF.day, tzinfo=UTC) - dt.timedelta(days=13)          # last complete week (the as-of is a Sunday)
    for k in range(9):
        weeks.append(mon - dt.timedelta(days=7 * k))
    issues, trans = [], []
    n = 0

    def add_issue(key, grp, owner, created, start, done, status, cat, resolution="Done", wip_owner=None, updated=None, parent="FX-P1", typ="Story"):
        issue = {"key": key, "type": typ, "code_type_flag": "Y", "status": status, "status_category": cat,
                 "assignee_id": ("acct-" + uname(owner)) if (owner and cat != "done") else "",
                 "assignee_id_at_final_done": ("acct-" + uname(owner)) if (owner and cat == "done") else "",
                 "priority": "Medium", "created": iso(created), "first_start": iso(start) if start else "", "first_start_basis": "in_progress" if start else "",
                 "final_done": iso(done) if done else "", "final_done_source": "changelog" if done else "none", "updated": iso(updated or done or start or created),
                 "parent_key": parent, "mr_field_present": "N", "resolution": resolution if done else "", "resolution_date": iso(done) if done else "",
                 "group_field": grp, "population": "done" if done else "open", "changelog_total": "3"}
        issues.append(issue)
        if start:
            trans.append({"issue": key, "from_status": "To Do", "to_status": "In Progress", "from_category": "new", "to_category": "indeterminate", "changed_at": iso(start)})
        if done:
            trans.append({"issue": key, "from_status": "In Progress", "to_status": "Closed", "from_category": "indeterminate", "to_category": "done", "changed_at": iso(done)})

    done_keys = {}
    for wk, ws in enumerate(weeks):
        for grp, cnt in (("CLEAN GROUP", 6), ("SEEDED GROUP", 4)):
            c = cnt
            if seeded and wk == 0 and (not split or grp == "SEEDED GROUP"):
                c = 0 if split else (1 if grp == "CLEAN GROUP" else 0)     # last complete week collapses (alert 4)
            for i in range(c):
                owner = rnd.choice([p[0] for p in eng if p[1] == grp])
                st = ws + dt.timedelta(days=1, hours=rnd.randint(0, 8))
                dn = st + dt.timedelta(days=rnd.choice([1, 2, 3, 4]), hours=rnd.randint(0, 5))
                n += 1
                key = f"FX-{n}"
                add_issue(key, grp, owner, st - dt.timedelta(days=3), st, dn, "Closed", "done", wip_owner=None)
                done_keys[key] = (grp, dn, owner)
    # open work in progress
    wip = []     # (key, owner, group, start_offset_days)
    base = [("Ann Example", "CLEAN GROUP"), ("Ann Example", "CLEAN GROUP"), ("Bob Example", "CLEAN GROUP"), ("Di Example", "SEEDED GROUP"), ("Ed Example", "SEEDED GROUP")]
    for owner, grp in base:
        wip.append((owner, grp, 0.3))
    if seeded:
        po = "Di Example" if split else "Ann Example"
        pg = "SEEDED GROUP" if split else "CLEAN GROUP"
        wip.append((po, pg, 0.3))
        wip.append((po, pg, 0.3))
        if split:
            wip.append((po, pg, 0.3))    # alert 3: Di has 4 in progress (limit 3)
        wip.append(("", "SEEDED GROUP", 0.3))                 # alert 1: no owner
        wip.append(("Ed Example", "SEEDED GROUP", 38))        # alert 2: older than P85
    wip_keys = []
    for owner, grp, age in wip:
        n += 1
        key = f"FX-{n}"
        st = ASOF - dt.timedelta(days=age)
        add_issue(key, grp, owner, st - dt.timedelta(days=2), st, None, "In Progress", "indeterminate", updated=ASOF - dt.timedelta(days=1))
        wip_keys.append((key, owner, grp))
    # one open backlog item, ownerless (information only: no alert)
    n += 1
    add_issue(f"FX-{n}", "SEEDED GROUP", "", ASOF - dt.timedelta(days=10), None, None, "To Do", "new", updated=ASOF - dt.timedelta(days=9))
    pjk = "FX-P1"
    issues.append({"key": pjk, "type": "Epic", "code_type_flag": "N", "status": "In Progress", "status_category": "indeterminate", "created": iso(ASOF - dt.timedelta(days=200)),
                   "updated": iso(ASOF - dt.timedelta(days=1)), "priority": "Medium", "mr_field_present": "N", "resolution": "", "final_done_source": "none", "group_field": "CLEAN GROUP",
                   "population": "open", "changelog_total": "1", "first_start": "", "first_start_basis": "", "final_done": "", "parent_key": "", "assignee_id": "", "assignee_id_at_final_done": "", "resolution_date": ""})
    w(os.path.join(jd, "jira_issues.csv"), "key,type,code_type_flag,status,status_category,assignee_id,assignee_id_at_final_done,priority,created,first_start,first_start_basis,final_done,final_done_source,updated,parent_key,mr_field_present,resolution,resolution_date,group_field,population,changelog_total".split(","), issues)
    w(os.path.join(jd, "jira_assignee_changes.csv"), "issue,changed_at,from_assignee_id,to_assignee_id".split(","), [])
    w(os.path.join(jd, "jira_transitions.csv"), "issue,from_status,to_status,from_category,to_category,changed_at".split(","), trans)
    # ------------------------------------------------------------ code
    ch, links, revs = [], [], []
    num = 0

    def change(author, opened, merged, state, first_review, last_act, key=None, cls="normal", lines=120, draft=0):
        nonlocal num
        num += 1
        cid_num = str(num)
        c = {"platform": "gitlab", "project": "fixture/app", "number": cid_num, "project_id": "1", "author": uname(author), "class": cls,
             "opened": iso(opened), "merged_or_closed": iso(merged) if merged else "", "state": state, "draft": str(draft), "lines": str(lines),
             "lines_excl_lockfiles_generated": str(lines), "files": "3", "diff_incomplete": "0", "desc_nonws_len": "200", "merged_by": uname(author) if merged else "",
             "head_sha": f"{num:040d}", "mirror_key": f"{num:040d}", "mirror_primary": "1", "first_review_at": iso(first_review) if first_review else "",
             "approvals": "1" if first_review else "0", "review_detail": "fetched", "last_activity_at": iso(last_act), "key_state": "linked" if key else "no_key",
             "primary_key": key or "", "self_merged": "0", "from_fork": "0"}
        ch.append(c)
        cid = f"gitlab:1!{cid_num}"
        if key:
            links.append({"change_id": cid, "jira_key": key, "source": "title", "primary": "1", "key_check": "linked", "resolved_jira_key": key, "alias_source": "same_key"})
        if first_review:
            reviewer = next(p[0] for p in eng if uname(p[0]) != uname(author))
            revs.append({"change_id": cid, "reviewer": uname(reviewer), "review_time": iso(first_review), "review_type": "approval", "reviewer_in_roster": "1", "reviewer_bot_guess": "0", "change_author_in_roster_scope": "1"})
        return cid

    for wk, ws in enumerate(weeks):
        for grp, mc in (("CLEAN GROUP", 5 if split else 8), ("SEEDED GROUP", 3 if split else 0)):
            if seeded and wk == 0 and (not split or grp == "SEEDED GROUP"):
                mc = 0 if split else 1
            if not split and grp == "SEEDED GROUP":
                continue
            pool = [p[0] for p in eng if (p[1] == grp)] if split else [p[0] for p in eng]
            for i in range(mc):
                a = rnd.choice(pool)
                op = ws + dt.timedelta(days=1, hours=rnd.randint(0, 6))
                mg = op + dt.timedelta(hours=rnd.randint(8, 30))
                fk = rnd.choice([k for k, v in done_keys.items() if (not split) or v[0] == grp])
                change(a, op, mg, "merged", op + dt.timedelta(hours=3), mg, key=fk)
    # open changes: one per WIP code-type issue with recent activity and a first review (clean)
    for key, owner, grp in wip_keys:
        if seeded and key == wip_keys[-1][0]:
            continue                                             # alert 6: this WIP issue has no linked change activity
        if seeded and owner == "" :
            continue
        a = owner or "Ann Example"
        op = ASOF - dt.timedelta(days=1)
        change(a, op, None, "opened", op + dt.timedelta(hours=2), ASOF - dt.timedelta(days=0.5), key=key)
    if seeded:
        change("Di Example" if split else "Bob Example", ASOF - dt.timedelta(days=9), None, "opened", None, ASOF - dt.timedelta(days=1), key=wip_keys[0][0])   # alert 5: open, no first review, older than the limit
    hdr = "platform,project,number,project_id,author,class,opened,merged_or_closed,state,draft,lines,lines_excl_lockfiles_generated,files,diff_incomplete,desc_nonws_len,merged_by,head_sha,mirror_key,mirror_primary,first_review_at,approvals,review_detail,last_activity_at,key_state,primary_key,self_merged,from_fork".split(",")
    w(os.path.join(gd, "code_changes.csv"), hdr, ch)
    w(os.path.join(gd, "code_jira_links.csv"), "change_id,jira_key,source,primary,key_check,resolved_jira_key,alias_source".split(","), links)
    w(os.path.join(gd, "code_reviews.csv"), "change_id,reviewer,review_time,review_type,reviewer_in_roster,reviewer_bot_guess,change_author_in_roster_scope".split(","), revs)
    w(os.path.join(gd, "reviewed_others.csv"), "change_id,project,author,state,opened,merged_at,review_detail".split(","), [])
    w(os.path.join(hd, "github_prs.csv"), "login,repo,number,author,state,draft,merged,created_at,merged_at,closed_at,updated_at,additions,deletions,changed_files,body_len,head_sha,head_repo,class,primary_key,key_count,mirror_key,first_review_at,note".split(","), [])
    w(os.path.join(hd, "github_pr_jira_keys.csv"), "repo,number,key,source,rank".split(","), [])
    w(os.path.join(hd, "github_pr_key_state.csv"), "repo,number,key,source,rank,key_state,alias_used,alias_resolution".split(","), [])
    w(os.path.join(hd, "github_pr_link_state.csv"), "repo,number,class,primary_key,primary_state,pr_state,key_count".split(","), [])
    w(os.path.join(hd, "github_pr_reviews.csv"), "repo,number,review_id,reviewer,reviewer_type,state,submitted_at".split(","), [])
    w(os.path.join(hd, "github_reviewed_by.csv"), "reviewer_login,repo,number,pr_author,created_at,state,merged".split(","), [])
    for src in (jd, gd, hd):
        json.dump({"calls": 0, "errors": 0, "r429": 0, "note": "fixture"}, open(os.path.join(src, "calls.json"), "w"))
    # thresholds (defaults) and config
    tpath = os.path.join(d, "thresholds.csv")
    shutil.copy("data/thresholds.csv", tpath) if os.path.exists("data/thresholds.csv") else None
    cfg = {"groups": ["CLEAN GROUP", "SEEDED GROUP"], "labels": {"other": "Other", "unknown": "Unknown", "ownerless": "Ownerless", "unmapped": "Unmapped", "no_team": "No team"},
           "jira": {"code_types": ["Story", "Task", "Bug"], "container_types": ["Epic", "Initiative"], "series_resolutions": {"wont_do": "Won't Do", "duplicate": "Duplicate"},
                    "in_progress_category": "indeterminate", "done_category": "done", "group_field_column": "group_field",
                    "group_aliases": {"FORMER GROUP": "CLEAN GROUP"}, "sbu_label": "Example SBU", "sbu_only_groups": [],
                    "fields": {"team": "customfield_00000"}},
           "window_days": 365, "sheet_name": "Fixture Dashboard",
           "paths": {"roster": rel(f"{d}/roster.csv"), "roster_history": rel(f"{d}/roster_history.csv"), "identity": rel(f"{d}/identity.csv"),
                     "jira_dir": rel(jd), "gitlab_dir": rel(gd), "github_dir": rel(hd), "thresholds": rel(tpath), "derived": rel(f"{d}/derived")},
           "texts": {"jira_source": "Jira: fictional fixture.", "code_source": "Code: fictional fixture.", "version": "fixture"},
           "scratch_sheet_id": "FIXTURE_SCRATCH_SHEET_ID", "sheet_id": "FIXTURE_SHEET_ID", "name_prefix": "x_"}
    json.dump(cfg, open(os.path.join(d, "config.json"), "w"), indent=2)
    return d


if __name__ == "__main__":
    for c in ("clean", "seeded", "alerts", "stale"):
        print(build(c))
