#!/usr/bin/env python3
"""Build the GitLab CSVs from the saved pull (no API calls, no model calls). 
  build.py --dir data/extracts/gitlab [--identity data/identity.csv] [--jira data/extracts/jira/jira_issues.csv]
Writes code_changes.csv, code_jira_links.csv, code_reviews.csv, reviewed_others.csv, author_summary.csv in --dir."""
import argparse, csv, glob, json, os, re, sys, datetime, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BOT_RE = re.compile(r"(_bot$|^project_\d+_bot|^group_\d+_bot|-bot$|^svc[-_.]|[-_.]svc$|^ghost$|^gitlab-|^sa-)", re.I)
SRC_ORDER = {"title": 0, "branch": 1, "description": 2, "commit": 3}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True); ap.add_argument("--identity", default="data/identity.csv")
    ap.add_argument("--jira", default="data/extracts/jira/jira_issues.csv")
    ap.add_argument("--aliases", default="data/extracts/jira/key_aliases.csv")
    a = ap.parse_args()
    D = a.dir
    ident = list(csv.DictReader(open(a.identity)))
    roster = {r["gitlab_username"]: r["person"] for r in ident if r["gitlab_confidence"] in ("exact", "overridden")}
    jkeys, jproj = set(), set()
    if os.path.exists(a.jira):
        for r in csv.DictReader(open(a.jira)):
            jkeys.add(r["key"]); jproj.add(r["key"].rsplit("-", 1)[0])
    alias = {}
    if os.path.exists(a.aliases):
        for r in csv.DictReader(open(a.aliases)): alias[r["old_key"]] = r
    ck = os.path.join(D, "checkpoints")
    authored, others = {}, {}
    # base pull pages first, then incremental pages (named ...__incr-<asof>__p0001.json) in as-of order: later wins
    def page_order(f):
        n = os.path.basename(f)
        return ("__incr-" in n, n)
    for f in sorted(glob.glob(os.path.join(ck, "*.json")), key=page_order):
        tag = os.path.basename(f).rsplit("__p", 1)[0]
        kind, user = tag.split("__", 1)
        for m in json.load(open(f))["items"]:
            k = (m["project_id"], m["iid"])
            if kind == "authored": authored[k] = m
            else: others[k] = m
    detail = {}
    for dp in [os.path.join(D, "detail.jsonl")] + sorted(glob.glob(os.path.join(D, "detail_incr_*.jsonl"))):
        if not os.path.exists(dp): continue
        for l in open(dp):
            try: d = json.loads(l)
            except ValueError: continue
            detail[(d["project_id"], d["iid"])] = d
    cp = os.path.join(D, "commit_pass.jsonl")
    if os.path.exists(cp):
        for l in open(cp):
            try: r = json.loads(l)
            except ValueError: continue
            k = (r["project_id"], r["iid"])
            if k in detail: detail[k].setdefault("commit_keys", r["commit_keys"])
            else: detail[k] = {"project_id": k[0], "iid": k[1], "commit_keys": r["commit_keys"]}
    for cpi in sorted(glob.glob(os.path.join(D, "commit_pass_incr_*.jsonl"))):  # incremental: later wins (replaces)
        for l in open(cpi):
            try: r = json.loads(l)
            except ValueError: continue
            k = (r["project_id"], r["iid"])
            if k in detail: detail[k]["commit_keys"] = r["commit_keys"]
            else: detail[k] = {"project_id": k[0], "iid": k[1], "commit_keys": r["commit_keys"]}
    # mirror groups: same head sha in more than one project
    bysha = collections.defaultdict(list)
    for k, m in authored.items():
        if m["sha"]: bysha[m["sha"]].append((m["created_at"], k))
    mirror_primary = {}
    for sha, g in bysha.items():
        g.sort()
        multi = len({k[0] for _, k in g}) > 1
        for i, (_, k) in enumerate(g):
            mirror_primary[k] = 0 if (multi and i > 0 and k[0] != g[0][1][0]) else 1
    cc, links, rev = [], [], []
    stat = collections.Counter(); gained = 0; noalias = set()
    for k, m in authored.items():
        d = detail.get(k, {})
        cid = f"gitlab:{k[0]}!{k[1]}"
        keys = list(m["keys"]) + list(d.get("commit_keys", []))
        keys.sort(key=lambda x: SRC_ORDER[x[1]])  # stable: order within a source is kept
        seen, uniq = set(), []
        for kk, src in keys:
            if (kk, src) not in seen:
                seen.add((kk, src)); uniq.append((kk, src))
        def resolve(kk):
            """D13 / inbox 10: (key_check, resolved_key, alias_source)"""
            if kk in jkeys: return "linked", kk, "direct"
            al = alias.get(kk)
            if al is None: return "not_found", "", "no_alias_row"
            res = al["resolution"]
            if res == "in_extract": return "linked", al["new_key"], al["source"]
            if res in ("out_of_scope_group_or_sbu", "out_of_scope_type", "older_than_window", "resolved_scope_not_checked"): return "other_project_key", al["new_key"] or kk, al["source"]
            return "not_found", "", al["source"]
        res_list = [(kk, src) + resolve(kk) for kk, src in uniq]
        if m["keys"] and d.get("commit_keys"):
            before = {x[0] for x in m["keys"]}
            if any(x[0] not in before for x in d["commit_keys"]): gained += 1
        for r_ in res_list:
            if r_[4] == "no_alias_row": noalias.add(r_[0])
        for i, (kk, src, chk, rk, asrc) in enumerate(res_list):
            links.append([cid, kk, src, 1 if i == 0 else 0, chk, rk, asrc])
        checks = [r[2] for r in res_list]
        kstate = "linked" if "linked" in checks else ("other_project_key" if "other_project_key" in checks else "no_key")
        pk = uniq[0][0] if uniq else ""
        df = d.get("diff", {})
        au = m["author"]
        cl = m["title_class"]
        if BOT_RE.search(au): cl = "bot"
        elif cl == "normal" and (m["project_path"].startswith("docs/") or df.get("docs_only")): cl = "docs"
        events = d.get("notes", []) if d.get("review_detail") == "fetched" else None
        first, approvers = "", set()
        if events is not None:
            for who, ts, typ in events:
                if who == au or BOT_RE.search(who): continue
                first = ts if (not first or ts < first) else first
                if typ == "approval": approvers.add(who)
            for who, ts, typ in events:
                if who != au:
                    rev.append([cid, who, ts, typ, int(who in roster), int(bool(BOT_RE.search(who))), 1])
        end = m["merged_at"] or m["closed_at"]
        last = max(m["updated_at"], d.get("last_nonsys_note", "") or "")
        cc.append(["gitlab", m["project_path"], k[1], k[0], au, cl, m["created_at"], end, m["state"], int(m["draft"]),
                   df.get("lines", ""), df.get("lines_excl", ""), df.get("files", ""), int(bool(df.get("incomplete"))) if df else "",
                   m["desc_len"], m["merged_by"], m["sha"], f"{m['sha']}", mirror_primary.get(k, 1), first,
                   len(approvers) if events is not None else "", d.get("review_detail", "missing"), last, kstate, pk,
                   int(bool(m["merged_by"]) and m["merged_by"] == au), int(m["fork"])])
        stat[cl] += 1
    with open(os.path.join(D, "code_changes.csv.tmp"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["platform", "project", "number", "project_id", "author", "class", "opened", "merged_or_closed", "state", "draft",
                    "lines", "lines_excl_lockfiles_generated", "files", "diff_incomplete", "desc_nonws_len", "merged_by", "head_sha",
                    "mirror_key", "mirror_primary", "first_review_at", "approvals", "review_detail", "last_activity_at",
                    "key_state", "primary_key", "self_merged", "from_fork"])
        w.writerows(cc)
    with open(os.path.join(D, "code_jira_links.csv.tmp"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["change_id", "jira_key", "source", "primary", "key_check", "resolved_jira_key", "alias_source"]); w.writerows(links)
    ro = []
    for k, m in others.items():
        if k in authored: continue
        d = detail.get(k, {})
        cid = f"gitlab:{k[0]}!{k[1]}"
        ro.append([cid, m["project_path"], m["author"], m["state"], m["created_at"], m["merged_at"], d.get("review_detail", "missing")])
        for who, ts, typ in d.get("notes", []):
            if who in roster:
                rev.append([cid, who, ts, typ, 1, 0, 0])
    with open(os.path.join(D, "code_reviews.csv.tmp"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["change_id", "reviewer", "review_time", "review_type", "reviewer_in_roster", "reviewer_bot_guess", "change_author_in_roster_scope"]); w.writerows(rev)
    with open(os.path.join(D, "reviewed_others.csv.tmp"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["change_id", "project", "author", "state", "opened", "merged_at", "review_detail"]); w.writerows(ro)
    open(os.path.join(D, "keys_without_alias_row.txt.tmp"), "w").write("\n".join(sorted(noalias)) + ("\n" if noalias else ""))
    for name in ["code_changes.csv", "code_jira_links.csv", "code_reviews.csv", "reviewed_others.csv", "keys_without_alias_row.txt"]:
        os.replace(os.path.join(D, name + ".tmp"), os.path.join(D, name))  # all-or-nothing swap after every file was written
    ks = collections.Counter(r[23] for r in cc)
    print("MRs with title/branch/description key that gained a new key from commits:", gained, "| distinct keys with no alias row:", len(noalias))
    print("authored", len(cc), "classes", dict(stat), "key_state", dict(ks), "others", len(ro), "reviews", len(rev), "jira keys", len(jkeys))


if __name__ == "__main__":
    main()
