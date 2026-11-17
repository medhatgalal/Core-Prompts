#!/usr/bin/env python3
"""GitHub extractor (AC7, AC8, AC9, AC53 GitHub half). Every call goes through tools/ro/ro (GET only).
No titles/descriptions are stored: text is read in memory only to find Jira keys, class and lengths.
Resumable: one checkpoint JSON per login in data/extracts/github/checkpoints/. No model call anywhere (AC55).
Usage: python3 -I tools/github/pull.py [--workers 5] [--budget 20000] [--only login] ; then --assemble
"""
import argparse, csv, datetime as dt, json, os, re, subprocess, sys, threading, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RO = os.path.join(ROOT, "tools", "ro", "ro")
OUT = os.path.join(ROOT, "data", "extracts", "github")
CK = os.path.join(OUT, "checkpoints")
def _org():
    """GitHub org comes from data/roster_config.json (`github_org`), never from code (AC56)."""
    try:
        return json.load(open(os.path.join(ROOT, "data", "roster_config.json")))["github_org"]
    except Exception:
        raise SystemExit("github_org missing in data/roster_config.json")
ORG = _org()
KEY = re.compile(r"(?<![A-Za-z0-9-])[A-Z][A-Z0-9]+-\d+(?!\d)")
lock = threading.Lock()
slock = threading.Lock()
glock = threading.Lock()
state = {"calls": 0, "search": 0, "retries": 0, "fail": 0, "last_search": 0.0, "last_guard": -1000, "budget": 20000}

def core_guard(force=False):
    """Core quota is 5,000/hour: before it runs out, sleep until the reset instead of failing calls."""
    with glock:
        if not force and state["calls"] - state["last_guard"] < 100: return
        state["last_guard"] = state["calls"]
        for _ in range(3):
            r = subprocess.run([RO, "gh", "api", "rate_limit"], capture_output=True)
            with lock: state["calls"] += 1
            try: c = json.loads(r.stdout)["resources"]["core"]
            except Exception: return
            if c["remaining"] > 250 and not force: return
            if c["remaining"] > 50 and force: return
            wait = max(5, c["reset"] - time.time() + 5)
            print("core quota low (%d left); sleeping %ds" % (c["remaining"], wait), flush=True)
            time.sleep(wait); force = False

MAXTRY = 6

def ro(path, search=False):
    if not search: core_guard()
    for attempt in range(MAXTRY):
        if search:
            with slock:  # search API: 30/min, keep >= 2.2 s apart
                w = 2.2 - (time.time() - state["last_search"])
                if w > 0: time.sleep(w)
                state["last_search"] = time.time()
        with lock:
            if state["calls"] >= state["budget"]:
                raise SystemExit("BUDGET REACHED")
            state["calls"] += 1; state["search"] += search
        r = subprocess.run([RO, "gh", "api", path], capture_output=True)
        if r.returncode == 0:
            try: return json.loads(r.stdout)
            except Exception: pass
        err = (r.stderr or b"").decode("latin1")[:300] + (r.stdout or b"")[:200].decode("latin1")
        if "404" in err or "410" in err or "451" in err: return {"_missing": True}
        with lock: state["retries"] += 1
        if ("403" in err or "429" in err or "rate" in err.lower()) and not search: core_guard(True)
        time.sleep(10 * (attempt + 1) if ("rate" in err.lower() or "403" in err or "429" in err) else 3)
    with lock: state["fail"] += 1
    return {"_failed": True}

def q(s): return urllib.parse.quote(s, safe=":+><=.-_")

def search_count(query):
    d = ro("search/issues?q=%s&per_page=1" % q(query), True)
    return d.get("total_count") if isinstance(d, dict) and "total_count" in d else None

def search_rows(query):
    rows, page = [], 1
    while page <= 10:
        d = ro("search/issues?q=%s&per_page=100&page=%d&sort=created&order=asc" % (q(query), page), True)
        it = d.get("items") if isinstance(d, dict) else None
        if it is None: return rows, "failed"
        rows += it
        if len(it) < 100: break
        page += 1
    return rows, "ok"

def fmt(t): return t.strftime("%Y-%m-%dT%H:%M:%SZ")

def windows(base, start, end, total):
    """Split [start,end] so no window nears the 1000 cap. total = count for whole range."""
    if total is not None and total <= 900: return [(start, end)]
    if (end - start) < dt.timedelta(hours=2): return [(start, end)]
    mid = start + (end - start) / 2
    out = []
    for a, b in ((start, mid), (mid + dt.timedelta(seconds=1), end)):
        c = search_count("%s created:%s..%s" % (base, fmt(a), fmt(b)))
        out += windows(base, a, b, c)
    return out

def pull_search(base, start, end):
    total = search_count("%s created:%s..%s" % (base, fmt(start), fmt(end)))
    ws = windows(base, start, end, total)
    rows, status = [], "ok"
    for a, b in ws:
        r, s = search_rows("%s created:%s..%s" % (base, fmt(a), fmt(b)))
        rows += r; status = s if s != "ok" else status
    seen = {}
    for x in rows: seen[x["id"]] = x
    return total, list(seen.values()), len(ws), status

def keys_from(parts):
    found = []
    for src, text in parts:
        for k in KEY.findall(text or ""):
            if k not in [f[0] for f in found]: found.append((k, src))
    return found

def classify(pr, files):
    user = pr.get("user") or {}
    title = (pr.get("title") or "").lower(); ref = (pr["head"].get("ref") or "").lower()
    if user.get("type") == "Bot" or (user.get("login") or "").lower().endswith("[bot]"): return "bot"
    if title.startswith("revert") or ref.startswith("revert"): return "revert"
    if re.search(r"cherry[- ]?pick|backport", title + " " + ref): return "backport"
    if re.match(r"(release|merge[- ]train)", title) or re.match(r"(release|merge[-_ ]train)", ref): return "release"
    if files and all(re.match(r"(docs?/|.*\.(md|rst|adoc|txt)$)", f, re.I) for f in files): return "docs"
    return "normal"

def one_pr(item):
    repo = item["repository_url"].split("/repos/")[1]; n = item["number"]
    pr = ro("repos/%s/pulls/%d" % (repo, n))
    if "_failed" in pr or "_missing" in pr: return {"repo": repo, "number": n, "error": "detail"}
    files = None
    u = pr.get("user") or {}
    if u.get("type") != "Bot" and pr.get("changed_files", 0) <= 100 and not (pr.get("title") or "").lower().startswith(("revert",)):
        fl = ro("repos/%s/pulls/%d/files?per_page=100" % (repo, n))
        files = [f["filename"] for f in fl] if isinstance(fl, list) else None
    parts = [("title", pr.get("title")), ("branch", pr["head"].get("ref")), ("body", pr.get("body"))]
    reviews = []
    if pr.get("merged_at"):
        rv = ro("repos/%s/pulls/%d/reviews?per_page=100" % (repo, n))
        if isinstance(rv, list):
            reviews = [{"review_id": r["id"], "reviewer": (r.get("user") or {}).get("login"), "reviewer_type": (r.get("user") or {}).get("type"),
                        "state": r.get("state"), "submitted_at": r.get("submitted_at")} for r in rv]
        else: reviews = None
        if not keys_from(parts) and pr.get("merge_commit_sha"):
            c = ro("repos/%s/commits/%s" % (repo, pr["merge_commit_sha"]))
            if isinstance(c, dict): parts.append(("commit", (c.get("commit") or {}).get("message")))
    if True:
        hc = ro("repos/%s/commits/%s" % (repo, pr["head"]["sha"]))
        if isinstance(hc, dict): parts.append(("commit", (hc.get("commit") or {}).get("message")))
    ks = keys_from(parts)
    return {"head_commit_checked": True, "repo": repo, "number": n, "author": u.get("login"), "author_type": u.get("type"),
            "state": pr["state"], "draft": pr.get("draft"), "merged": bool(pr.get("merged_at")),
            "created_at": pr["created_at"], "merged_at": pr.get("merged_at"), "closed_at": pr.get("closed_at"),
            "updated_at": pr["updated_at"], "additions": pr.get("additions"), "deletions": pr.get("deletions"),
            "changed_files": pr.get("changed_files"), "body_len": len(pr.get("body") or ""), "head_sha": pr["head"]["sha"],
            "base_repo": pr["base"]["repo"]["full_name"], "head_repo": (pr["head"].get("repo") or {}).get("full_name"),
            "class": classify(pr, files), "files_checked": files is not None,
            "keys": ks, "reviews": reviews}

def do_login(login, start, end, asof, inner):
    path = os.path.join(CK, login + ".json")
    if os.path.exists(path): return
    base = "org:%s type:pr author:%s" % (ORG, login)
    total, rows, nwin, st = pull_search(base, start, end)
    # second method: the same population counted by state, different queries
    alt = {}
    for s in ("is:open", "is:merged", "is:closed is:unmerged"):
        alt[s] = search_count("%s %s created:%s..%s" % (base, s, fmt(start), fmt(end)))
    prs = list(inner.map(one_pr, rows))
    rbase = "org:%s type:pr reviewed-by:%s" % (ORG, login)
    rtotal, rrows, rwin, rst = pull_search(rbase, start, end)
    reviewed = [{"repo": x["repository_url"].split("/repos/")[1], "number": x["number"], "author": (x.get("user") or {}).get("login"),
                 "created_at": x["created_at"], "state": x["state"], "merged": bool((x.get("pull_request") or {}).get("merged_at"))} for x in rrows]
    rec = {"login": login, "as_of": asof, "window": [fmt(start), fmt(end)], "authored_total_count": total, "authored_rows": len(prs),
           "authored_windows": nwin, "authored_status": st, "recount_by_state": alt,
           "reviewed_total_count": rtotal, "reviewed_rows": len(reviewed), "reviewed_windows": rwin, "reviewed_status": rst,
           "prs": prs, "reviewed": reviewed}
    tmp = path + ".tmp"
    json.dump(rec, open(tmp, "w")); os.replace(tmp, path)
    save_calls()

def repair():
    """Re-fetch reviews/files that failed earlier (checkpoint rows with reviews None or files not checked)."""
    n = 0
    for f in sorted(os.listdir(CK)):
        if not f.endswith(".json"): continue
        path = os.path.join(CK, f); c = json.load(open(path)); dirty = False
        for i, p in enumerate(c["prs"]):
            need = p.get("error") or p["reviews"] is None or (not p["files_checked"] and p["author_type"] != "Bot" and (p["changed_files"] or 0) <= 100 and p["class"] != "revert")
            if need:
                new = one_pr({"repository_url": "https://api.github.com/repos/" + p["repo"], "number": p["number"]})
                if not new.get("error"): c["prs"][i] = new; dirty = True; n += 1
        if dirty:
            json.dump(c, open(path + ".tmp", "w")); os.replace(path + ".tmp", path)
    print("repaired", n, flush=True)

def recommit(workers, everyone=False):
    """AC53 fix: the head commit message is the 4th key source. For every PR with no key in title, branch or body,
    read the head commit (api repos/<repo>/commits/<head_sha>), run the key pattern, store keys and source only."""
    stats = {"checked": 0, "changed": 0, "gained_extra": 0, "failed": 0, "calls0": state["calls"]}
    def work(job):
        c, i = job; p = c["prs"][i]
        d = ro("repos/%s/commits/%s" % (p["repo"], p["head_sha"]))
        if not isinstance(d, dict) or "commit" not in d: return (c, i, None)
        return (c, i, keys_from([("commit", (d["commit"] or {}).get("message"))]))
    for f in sorted(os.listdir(CK)):
        if not f.endswith(".json"): continue
        path = os.path.join(CK, f); c = json.load(open(path))
        jobs = [(c, i) for i, p in enumerate(c["prs"]) if not p.get("error") and not p.get("head_commit_checked")
                and (everyone or not any(src in ("title", "branch", "body") for _, src in p["keys"]))]
        if not jobs: continue
        with ThreadPoolExecutor(workers) as ex:
            for cc, i, ks in ex.map(work, jobs):
                if ks is None: stats["failed"] += 1; continue
                p = cc["prs"][i]; stats["checked"] += 1; p["head_commit_checked"] = True
                have = [k for k, _ in p["keys"]]
                new = [(k, s2) for k, s2 in ks if k not in have]
                if new:
                    was = bool(p["keys"]); p["keys"] += new
                    if not was: stats["changed"] += 1
                    else: stats["gained_extra"] += 1
        json.dump(c, open(path + ".tmp", "w")); os.replace(path + ".tmp", path)
    stats["calls"] = state["calls"] - stats.pop("calls0")
    print("recommit", stats, flush=True); save_calls(); assemble(open(os.path.join(OUT, "as_of.txt")).read().strip())

def all_commit_keys(repo, number):
    """Keys from every commit message of a PR (max 250 commits, the endpoint limit). None if a call failed."""
    msgs, page = [], 1
    while page <= 3:
        d = ro("repos/%s/pulls/%d/commits?per_page=100&page=%d" % (repo, number, page))
        if not isinstance(d, list): return None
        msgs += [("commit", (x.get("commit") or {}).get("message")) for x in d]
        if len(d) < 100: break
        page += 1
    return keys_from(msgs)

def allcommits(workers):
    """v1.12: Jira keys from ANY commit message of the PR. Reads repos/<repo>/pulls/<n>/commits (paginated, 100 per page,
    message text is read in memory only); stores keys with source `commit`. Checkpointed per login."""
    stats = {"prs": 0, "gained_key": 0, "was_nokey_now_key": 0, "failed": 0, "calls0": state["calls"]}
    def work(job):
        c, i = job; p = c["prs"][i]
        return (c, i, all_commit_keys(p["repo"], p["number"]))
    for f in sorted(os.listdir(CK)):
        if not f.endswith(".json"): continue
        path = os.path.join(CK, f); c = json.load(open(path))
        jobs = [(c, i) for i, p in enumerate(c["prs"]) if not p.get("error") and not p.get("all_commits_checked")]
        if not jobs: continue
        with ThreadPoolExecutor(workers) as ex:
            for cc, i, ks in ex.map(work, jobs):
                p = cc["prs"][i]
                if ks is None: stats["failed"] += 1; continue
                stats["prs"] += 1; p["all_commits_checked"] = True
                have = [k for k, _ in p["keys"]]; new = [(k, s2) for k, s2 in ks if k not in have]
                if new:
                    stats["gained_key"] += 1
                    if not have: stats["was_nokey_now_key"] += 1
                    p["keys"] += new
        json.dump(c, open(path + ".tmp", "w")); os.replace(path + ".tmp", path)
        save_calls()
    stats["calls"] = state["calls"] - stats.pop("calls0")
    print("allcommits", stats, flush=True); save_calls(); assemble(open(os.path.join(OUT, "as_of.txt")).read().strip())

LOCK = re.compile(r"(^|/)(package-lock\.json|npm-shrinkwrap\.json|yarn\.lock|pnpm-lock\.yaml|Pipfile\.lock|poetry\.lock|Gemfile\.lock|composer\.lock|go\.sum|Cargo\.lock|gradle\.lockfile|packages\.lock\.json|[^/]*\.lock)$", re.I)
GEN = re.compile(r"(^|/)(node_modules|dist|build|generated|__generated__|vendor)/|\.min\.(js|css)$|\.map$|\.pb\.go$|_pb2\.py$|\.generated\.|\.g\.(cs|dart)$|\.designer\.cs$", re.I)

def gatec_fields(p, size_t=800):
    """merged_by, non-whitespace description length, lines excluding lockfiles/generated files. None if a call failed."""
    d = ro("repos/%s/pulls/%d" % (p["repo"], p["number"]))
    if not isinstance(d, dict) or "number" not in d: return None
    out = {"merged_by": (d.get("merged_by") or {}).get("login") or "", "body_nonws_len": len("".join((d.get("body") or "").split()))}
    tot = (p["additions"] or 0) + (p["deletions"] or 0)
    if tot > size_t or p["state"] == "open":
        lines = ex_files = 0; pg = 1
        while pg <= 30:
            fl = ro("repos/%s/pulls/%d/files?per_page=100&page=%d" % (p["repo"], p["number"], pg))
            if not isinstance(fl, list): return None
            for f in fl:
                if LOCK.search(f["filename"]) or GEN.search(f["filename"]): ex_files += 1
                else: lines += (f.get("additions") or 0) + (f.get("deletions") or 0)
            if len(fl) < 100: break
            pg += 1
        out.update({"lines_excl": lines, "excluded_files": ex_files, "lines_basis": "files_filtered" if (p["changed_files"] or 0) <= 3000 else "files_truncated"})
    else:
        out.update({"lines_excl": tot, "excluded_files": 0, "lines_basis": "total_le_threshold"})
    return out

def gatec(workers, size_t=800):
    """Gate C fields for `normal` merged-or-open PRs: merged_by, non-whitespace description length, and lines excluding
    lockfiles/generated files (files list read only when total lines > size_t or the PR is open). Numbers and logins only."""
    stats = {"prs": 0, "files_prs": 0, "failed": 0, "calls0": state["calls"]}
    def work(job):
        c, i = job
        return (c, i, gatec_fields(c["prs"][i], size_t))
    for f in sorted(os.listdir(CK)):
        if not f.endswith(".json"): continue
        path = os.path.join(CK, f); c = json.load(open(path))
        jobs = [(c, i) for i, p in enumerate(c["prs"]) if not p.get("error") and not p.get("gatec_done") and p["class"] == "normal" and (p["merged"] or p["state"] == "open")]
        if not jobs: continue
        with ThreadPoolExecutor(workers) as ex:
            for cc, i, out in ex.map(work, jobs):
                if out is None: stats["failed"] += 1; continue
                cc["prs"][i].update(out); cc["prs"][i]["gatec_done"] = True; stats["prs"] += 1
                stats["files_prs"] += out["lines_basis"] != "total_le_threshold"
        json.dump(c, open(path + ".tmp", "w")); os.replace(path + ".tmp", path); save_calls()
    stats["calls"] = state["calls"] - stats.pop("calls0")
    print("gatec", stats, flush=True); save_calls(); assemble(open(os.path.join(OUT, "as_of.txt")).read().strip())

def die(code, msg):
    print(msg, file=sys.stderr, flush=True); sys.exit(code)

def inc_search(base, start, end):
    """All search hits for `base` updated in [start, end]; splits the window if it reaches the 1,000-result cap."""
    qs = "%s updated:%s..%s" % (base, fmt(start), fmt(end)); rows = []
    for page in range(1, 11):
        d = ro("search/issues?q=%s&per_page=100&page=%d&sort=updated&order=asc" % (q(qs), page), True)
        it = d.get("items") if isinstance(d, dict) else None
        if it is None: raise RuntimeError("GitHub search failed: " + qs)
        rows += it
        if len(it) < 100: return rows
    mid = start + (end - start) / 2
    seen = {}
    for x in inc_search(base, start, mid) + inc_search(base, mid + dt.timedelta(seconds=1), end): seen[x["id"]] = x
    return list(seen.values())

def refresh_pr(item):
    """Everything the full pull stores for one PR: detail, files class, reviews, head commit, all commit keys, Gate C fields."""
    repo = item["repository_url"].split("/repos/")[1]; n = item["number"]
    p = one_pr(item)
    if p.get("error") or (p["merged"] and p["reviews"] is None): raise RuntimeError("GitHub call failed for %s#%d" % (repo, n))
    ks = all_commit_keys(repo, n)
    if ks is None: raise RuntimeError("GitHub commits call failed for %s#%d" % (repo, n))
    have = [k for k, _ in p["keys"]]; p["keys"] += [(k, sc) for k, sc in ks if k not in have]
    p["all_commits_checked"] = True
    if p["class"] == "normal" and (p["merged"] or p["state"] == "open"):
        g = gatec_fields(p)
        if g is None: raise RuntimeError("GitHub files call failed for %s#%d" % (repo, n))
        p.update(g); p["gatec_done"] = True
    return json.loads(json.dumps(p))   # same shape as a stored row (tuples become lists)

def incremental(a):
    """AC36a: pull what changed since the cursor, upsert by (repo, PR number), swap files in, then advance the cursor."""
    global MAXTRY
    t0 = time.time(); cur_path = os.path.join(OUT, "cursor.json")
    try: cursor = json.load(open(cur_path))["github"]
    except Exception:
        try: cursor = open(os.path.join(OUT, "as_of.txt")).read().strip()
        except Exception: die(1, "GitHub incremental: no cursor and no as_of.txt in %s; run the full pull first" % OUT)
    p_utc = lambda t: dt.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    asof = a.asof; end = p_utc(asof); cur = p_utc(cursor)
    if end == cur:                                   # empty window: nothing to pull, nothing written, cursor unchanged
        print("github incremental %s: nothing new (as-of equals the cursor); no calls made" % asof, flush=True); return
    if end < cur: die(1, "GitHub incremental: as-of %s is before the cursor %s" % (asof, cursor))
    since = cur - dt.timedelta(hours=1); win_start = end - dt.timedelta(days=365)
    r = subprocess.run([RO, "gh", "api", "user"], capture_output=True)
    if r.returncode != 0:
        die(2, "GitHub returned an error for /user: check the gh sign-in (run: gh auth status) and the network or VPN")
    state["budget"] = 10 ** 9; MAXTRY = 12      # no call cap; rate limits are waited out
    stats = {"as_of": asof, "since": fmt(since), "logins": 0, "new_logins": 0, "prs_seen": 0, "prs_new": 0, "prs_changed": 0,
             "reviewed_seen": 0, "reviewed_new": 0, "reviewed_changed": 0}
    def save_inc(ok):
        with lock:
            json.dump(dict(stats, calls=state["calls"], search=state["search"], retries=state["retries"], failed=state["fail"],
                           seconds=round(time.time() - t0), ok=ok, at=fmt(dt.datetime.now(dt.timezone.utc))),
                      open(os.path.join(OUT, "calls_incremental.json"), "w"))
    try:
        logins = [x["github_login"].strip() for x in csv.DictReader(open(a.identity)) if x["github_confidence"] == "exact" and x["github_login"].strip()]
        logins = list(dict.fromkeys(logins)); updates = {}
        with ThreadPoolExecutor(a.workers) as inner:
            for login in logins:
                path = os.path.join(CK, login + ".json"); stats["logins"] += 1
                if not os.path.exists(path):          # a person added since the full pull: pull the whole window once
                    do_login(login, win_start, end, asof, inner); stats["new_logins"] += 1; continue
                c = json.load(open(path))
                hits = inc_search("org:%s type:pr author:%s" % (ORG, login), since, end)
                hits = [x for x in hits if p_utc(x["created_at"]) >= win_start]
                stats["prs_seen"] += len(hits)
                idx = {(x["repo"], x["number"]): i for i, x in enumerate(c["prs"])}
                changed = False
                for item, newp in zip(hits, inner.map(refresh_pr, hits)):
                    k = (newp["repo"], newp["number"])
                    if k in idx:
                        if json.dumps(c["prs"][idx[k]], sort_keys=True) != json.dumps(newp, sort_keys=True):
                            c["prs"][idx[k]] = newp; stats["prs_changed"] += 1; changed = True
                    else:
                        c["prs"].append(newp); idx[k] = len(c["prs"]) - 1; stats["prs_new"] += 1; changed = True
                rh = inc_search("org:%s type:pr reviewed-by:%s" % (ORG, login), since, end)
                rh = [x for x in rh if p_utc(x["created_at"]) >= win_start]
                stats["reviewed_seen"] += len(rh)
                ridx = {(x["repo"], x["number"]): i for i, x in enumerate(c["reviewed"])}
                for x in rh:
                    row = {"repo": x["repository_url"].split("/repos/")[1], "number": x["number"], "author": (x.get("user") or {}).get("login"),
                           "created_at": x["created_at"], "state": x["state"], "merged": bool((x.get("pull_request") or {}).get("merged_at"))}
                    k = (row["repo"], row["number"])
                    if k in ridx:
                        if c["reviewed"][ridx[k]] != row: c["reviewed"][ridx[k]] = row; stats["reviewed_changed"] += 1; changed = True
                    else:
                        c["reviewed"].append(row); stats["reviewed_new"] += 1; changed = True
                if changed:
                    c["authored_rows"] = c["authored_total_count"] = len(c["prs"]); c["reviewed_rows"] = c["reviewed_total_count"] = len(c["reviewed"])
                    n_open = sum(1 for x in c["prs"] if x["state"] == "open"); n_mrg = sum(1 for x in c["prs"] if x["merged"])
                    c["recount_by_state"] = {"is:open": n_open, "is:merged": n_mrg, "is:closed is:unmerged": len(c["prs"]) - n_open - n_mrg}
                    c["authored_status"] = c["reviewed_status"] = "ok"; c["as_of"] = asof
                    updates[login] = c
        for login, c in updates.items():              # stage done: swap each checkpoint in, then the CSVs, then the cursor
            path = os.path.join(CK, login + ".json"); json.dump(c, open(path + ".tmp", "w")); os.replace(path + ".tmp", path)
        assemble(asof)
        kr = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "github", "keystate.py"), OUT], capture_output=True)
        if kr.returncode != 0: raise RuntimeError("key-state step failed: " + kr.stderr.decode()[-300:])
        json.dump({"github": asof, "written_at": fmt(dt.datetime.now(dt.timezone.utc))}, open(cur_path + ".tmp", "w")); os.replace(cur_path + ".tmp", cur_path)
    except SystemExit: save_inc(False); raise
    except Exception as e:
        save_inc(False); die(1, "GitHub incremental failed (cursor not advanced): %s" % e)
    save_inc(True)
    print("github incremental %s: %d PRs seen (%d new, %d changed), %d reviewed rows new or changed, %d calls" % (
        asof, stats["prs_seen"], stats["prs_new"], stats["prs_changed"], stats["reviewed_new"] + stats["reviewed_changed"], state["calls"]), flush=True)

def save_calls():
    with lock:
        json.dump({"calls_this_run": state["calls"], "search": state["search"], "retries": state["retries"], "failed": state["fail"],
                   "budget": state["budget"], "at": fmt(dt.datetime.now(dt.timezone.utc))}, open(os.path.join(OUT, "calls.json"), "w"))

def assemble(asof):
    cks = [json.load(open(os.path.join(CK, f))) for f in sorted(os.listdir(CK)) if f.endswith(".json")]
    staged = []
    def w(name, cols, rows):   # write to a temp file; all are swapped in together at the end
        tmp = os.path.join(OUT, name + ".tmp")
        with open(tmp, "w", newline="") as f:
            cw = csv.writer(f); cw.writerow(cols); cw.writerows(rows)
        staged.append((tmp, os.path.join(OUT, name)))
    P, K, R, V, C = [], [], [], [], []
    for c in cks:
        for p in c["prs"]:
            if p.get("error"): continue
            mk = "%s|%s" % (p["head_sha"], p["base_repo"].lower())
            first = ""
            if p["reviews"]:
                ok = [r for r in p["reviews"] if r["reviewer"] and r["reviewer"] != p["author"] and r["reviewer_type"] != "Bot"
                      and r["state"] in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED") and r["submitted_at"]]
                if ok: first = min(r["submitted_at"] for r in ok)
            prim = p["keys"][0][0] if p["keys"] else ""
            P.append([c["login"], p["repo"], p["number"], p["author"], p["state"], p["draft"], p["merged"], p["created_at"], p["merged_at"] or "",
                      p["closed_at"] or "", p["updated_at"], p["additions"], p["deletions"], p["changed_files"], p["body_len"], p["head_sha"],
                      p["head_repo"] or "", p["class"], prim, len(p["keys"]), mk, first, "" if p["reviews"] is not None else "reviews_failed",
                      p.get("merged_by", ""), p.get("body_nonws_len", ""), p.get("lines_excl", ""), p.get("lines_basis", ""), p.get("excluded_files", "")])
            for i, (k, src) in enumerate(p["keys"]): K.append([p["repo"], p["number"], k, src, i + 1])
            for r in (p["reviews"] or []): R.append([p["repo"], p["number"], r["review_id"], r["reviewer"], r["reviewer_type"], r["state"], r["submitted_at"]])
        for x in c["reviewed"]: V.append([c["login"], x["repo"], x["number"], x["author"], x["created_at"], x["state"], x["merged"]])
        a = c["recount_by_state"]; ssum = sum(v or 0 for v in a.values())
        C.append([c["login"], c["authored_total_count"], c["authored_rows"], ssum, c["authored_windows"], c["authored_status"],
                  c["reviewed_total_count"], c["reviewed_rows"], c["reviewed_windows"], c["reviewed_status"],
                  sum(1 for p in c["prs"] if p.get("error"))])
    w("github_prs.csv", ["login", "repo", "number", "author", "state", "draft", "merged", "created_at", "merged_at", "closed_at", "updated_at",
        "additions", "deletions", "changed_files", "body_len", "head_sha", "head_repo", "class", "primary_key", "key_count", "mirror_key",
        "first_review_at", "note", "merged_by", "body_nonws_len", "lines_excl", "lines_basis", "excluded_files"], P)
    w("github_pr_jira_keys.csv", ["repo", "number", "key", "source", "rank"], K)
    w("github_pr_reviews.csv", ["repo", "number", "review_id", "reviewer", "reviewer_type", "state", "submitted_at"], R)
    w("github_reviewed_by.csv", ["reviewer_login", "repo", "number", "pr_author", "created_at", "state", "merged"], V)
    w("github_counts.csv", ["login", "search_total", "rows_pulled", "recount_by_state", "authored_windows", "authored_status",
        "reviewed_search_total", "reviewed_rows", "reviewed_windows", "reviewed_status", "detail_errors"], C)
    open(os.path.join(OUT, "as_of.txt.tmp"), "w").write(asof + "\n")
    staged.append((os.path.join(OUT, "as_of.txt.tmp"), os.path.join(OUT, "as_of.txt")))
    for tmp, final in staged: os.replace(tmp, final)
    print("assembled", len(cks), "logins", len(P), "prs")

def main():
    global OUT, CK
    ap = argparse.ArgumentParser()
    ap.add_argument("--identity", default=os.path.join(ROOT, "data", "identity.csv"))
    ap.add_argument("--asof", default=None)
    ap.add_argument("--workers", type=int, default=5); ap.add_argument("--budget", type=int, default=20000)
    ap.add_argument("--only"); ap.add_argument("--assemble", action="store_true"); ap.add_argument("--commits", action="store_true"); ap.add_argument("--commits-all", action="store_true"); ap.add_argument("--allcommits", action="store_true"); ap.add_argument("--gatec", action="store_true")
    ap.add_argument("--incremental", action="store_true"); ap.add_argument("--data-dir", default=None)
    a = ap.parse_args()
    a.asof = a.asof or open(os.path.join(ROOT, "data", "extracts", "gitlab", "as_of.txt")).read().strip()
    if a.data_dir: OUT = os.path.abspath(a.data_dir); CK = os.path.join(OUT, "checkpoints")
    os.makedirs(CK, exist_ok=True)
    if a.incremental: return incremental(a)
    if a.assemble: return assemble(a.asof)
    state["budget"] = a.budget
    if a.gatec: return gatec(a.workers)
    if a.allcommits: return allcommits(a.workers)
    if a.commits or a.commits_all: return recommit(a.workers, a.commits_all)
    end = dt.datetime.strptime(a.asof, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    start = end - dt.timedelta(days=365)
    logins = [r["github_login"].strip() for r in csv.DictReader(open(a.identity)) if r["github_confidence"] == "exact" and r["github_login"].strip()]
    logins = [l for l in dict.fromkeys(logins) if not a.only or l == a.only]
    print("logins", len(logins), "asof", a.asof, flush=True)
    repair()
    with ThreadPoolExecutor(a.workers) as inner:
        for i, l in enumerate(logins):
            do_login(l, start, end, a.asof, inner)
            print(i + 1, l, "calls", state["calls"], flush=True)
    save_calls(); assemble(a.asof)

if __name__ == "__main__":
    main()
