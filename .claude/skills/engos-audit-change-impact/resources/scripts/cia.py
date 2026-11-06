#!/usr/bin/env python3
"""Deterministic helpers for engos-audit-change-impact.

Every number in the report comes from this script, never from the model.
Standard library only. Shells out to `glab` (GitLab) and `gh` (GitHub) with
read-only GET calls.

Subcommands:
  preflight     check glab/gh/pandoc/gws are installed and signed in
  window        resolve the reporting window (--since 1w | --from/--to)
  roster-check  check a roster JSON for internal consistency
  accounts      map roster people to GitLab and GitHub accounts
  pull          fetch MRs/PRs authored by the roster inside the window
  counts        per-area counts table (markdown) from pulled items
  linkcheck     check every link in a report: state, window, roster author
  tally         count fact-check verdicts from reviewer JSON files
"""
import argparse
import datetime as dt
import glob
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

BACKPORT_HINT = re.compile(r"backport|cherry[- ]pick|\[\d+\.\d+\]|\(\d+\.\d+\)|-maint\b", re.I)
SECURITY_HINT = re.compile(r"\bcve-\d|\bsecurity\b|vulnerab|\bxss\b|injection|auth(entication|orization)? (bypass|check)|"
                           r"data[- ]exposure|privilege|\bssrf\b|\bcsrf\b|sanitiz", re.I)
COUNTED_STATUSES = {"onboard", "onboarding"}


class FetchError(RuntimeError):
    pass


# ---------- shared helpers ----------

def run(args, timeout=300):
    """Run a command with stdin closed so CLIs never block on a prompt. Returns (rc, out, err)."""
    try:
        p = subprocess.run(args, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout: {' '.join(args[:3])}"
    except FileNotFoundError as e:
        return 127, "", str(e)
    return p.returncode, p.stdout, p.stderr


def default_gitlab_host():
    rc, out, _ = run(["glab", "config", "get", "host"])
    return out.strip() if rc == 0 and out.strip() else None


def gl_api(host, path, want=list):
    """One GitLab GET. Raises FetchError on CLI failure or an unexpected body."""
    rc, out, err = run(["glab", "api", "--hostname", host, path])
    try:
        data = json.loads(out) if out.strip() else None
    except ValueError:
        data = None
    if rc != 0 or not isinstance(data, want):
        msg = data.get("message") if isinstance(data, dict) else (err or out)[:200]
        raise FetchError(f"GitLab {path.split('?')[0]}: {msg or 'no data'} (rc={rc})")
    return data


def gl_pages(host, path, max_pages=50):
    """Fetch every page of a GitLab list endpoint, one page at a time."""
    sep = "&" if "?" in path else "?"
    out = []
    for page in range(1, max_pages + 1):
        chunk = gl_api(host, f"{path}{sep}per_page=100&page={page}")
        out += chunk
        if len(chunk) < 100:
            return out
    raise FetchError(f"GitLab {path.split('?')[0]}: more than {max_pages * 100} results")


def gh_get(path_args):
    rc, out, err = run(["gh", "api", "-X", "GET"] + path_args)
    try:
        data = json.loads(out) if out.strip() else None
    except ValueError:
        data = None
    if rc != 0 or not isinstance(data, dict) or "items" not in data:
        raise FetchError(f"GitHub {path_args[0]}: {(data or {}).get('message') if isinstance(data, dict) else (err or out)[:200]} (rc={rc})")
    return data


def gh_search_all(query):
    """GitHub issue search, paginated to the API's 1000-result ceiling."""
    items, total = [], 0
    for page in range(1, 11):
        data = gh_get(["search/issues", "-f", f"q={query}", "-f", "per_page=100", "-f", f"page={page}"])
        total = data.get("total_count", 0)
        items += data["items"]
        if len(data["items"]) < 100 or len(items) >= total:
            break
        time.sleep(2.1)  # search API: 30 requests per minute
    return items, total


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso(d):
    return d.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_iso(s, name):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", s or ""):
        sys.exit(f"{name} must be an ISO UTC timestamp like 2026-10-16T04:00:00Z (use the output of `cia.py window`)")
    return s


def in_window(ts, start, end):
    return bool(ts) and start <= iso(parse_ts(ts)) <= end


def load(path):
    with open(path) as f:
        return json.load(f)


def dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def toks(s):
    return set(re.split(r"[\s.'-]+", fold(s or ""))) - {""}


# ---------- preflight ----------

def cmd_preflight(a):
    host = a.gitlab_host or default_gitlab_host()
    res = {"gitlab_host": host, "glab": "missing", "gh": "missing", "pandoc": bool(shutil.which("pandoc")), "gws": bool(shutil.which("gws"))}
    if shutil.which("glab"):
        if not host:
            res["glab"] = "no host: pass --gitlab-host or run `glab auth login --hostname <host>`"
        else:
            try:
                me = gl_api(host, "user", want=dict)
                res["glab"] = f"signed in as {me.get('username')}"
            except FetchError as e:
                res["glab"] = f"not signed in to {host}: {e}. Run `glab auth login --hostname {host}`"
    if shutil.which("gh"):
        rc, out, _ = run(["gh", "api", "user", "--jq", ".login"])
        res["gh"] = f"signed in as {out.strip()}" if rc == 0 and out.strip() else "not signed in: GitHub will be skipped (run `gh auth login`)"
    res["publish"] = "google-doc" if res["pandoc"] and res["gws"] else "markdown only (pandoc or gws missing)"
    res["ok"] = res["glab"].startswith("signed in")
    print(json.dumps(res, indent=1))
    sys.exit(0 if res["ok"] else 1)


# ---------- window ----------

def cmd_window(a):
    # Naive local datetimes + astimezone() give each date its own offset (DST-safe).
    local = lambda d: d.astimezone()
    now = dt.datetime.now().astimezone()
    if a.from_ and a.since:
        sys.exit("window: use either --since or --from/--to, not both")
    end = local(dt.datetime.fromisoformat(a.to).replace(hour=23, minute=59, second=59)) if a.to else now
    if a.from_:
        start = local(dt.datetime.fromisoformat(a.from_))
    else:
        m = re.fullmatch(r"(\d+)\s*([dw])", (a.since or "1w").strip().lower())
        if not m:
            sys.exit("window: --since must look like 7d, 14d, 1w or 3w")
        days = int(m.group(1)) * (7 if m.group(2) == "w" else 1)
        if a.to:  # whole days: N days ending on --to
            start = local(dt.datetime.fromisoformat(a.to) - dt.timedelta(days=days - 1))
        else:     # rolling: the last N x 24 hours
            start = now - dt.timedelta(days=days)
    if start >= end:
        sys.exit("window: start must be before end")
    fmt = lambda d: f"{d:%b} {d.day}, {d.year}"
    print(json.dumps({"start": iso(start), "end": iso(end), "timezone": now.tzname(),
                      "label": f"{fmt(start)} to {fmt(end)}", "days": round((end - start).total_seconds() / 86400, 1)}))


# ---------- roster-check ----------

def cmd_roster_check(a):
    roster = load(a.roster)
    problems, seen = [], {}
    for i, p in enumerate(roster):
        u = (p.get("username") or "").lower()
        if not u:
            problems.append(f"entry {i}: no username")
            continue
        if u in seen:
            problems.append(f"{u}: listed twice")
        seen[u] = p
    for u, p in seen.items():
        if p.get("lookup_failed"):
            problems.append(f"{u}: Home lookup failed")
        if not p.get("leaf_only"):
            missing = [r for r in p.get("direct_reports", []) if r.lower() not in seen]
            if missing:
                problems.append(f"{u}: direct reports missing from roster: {missing}")
    counted = [p for p in seen.values() if not p.get("exclude_from_pull") and (p.get("status") or "onboard").lower() in COUNTED_STATUSES]
    not_counted = sorted(u for u, p in seen.items() if p not in counted)
    def tally(key):
        out = {}
        for p in counted:
            k = "(none)" if p.get(key) is None else str(p.get(key))
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items()))
    print(json.dumps({"people_in_roster": len(seen), "people_counted": len(counted), "not_counted": not_counted,
                      "levels": tally("level"), "groups": tally("group"), "problems": problems}, indent=1))
    sys.exit(1 if problems else 0)


# ---------- accounts ----------

def name_variants(display):
    """Usernames built from a display name, e.g. 'José Antonio Sánchez Pozo' ->
    antonio.pozo, joseantonio.sanchezpozo, ..."""
    t = [x for x in re.split(r"[\s.'-]+", fold(display or "")) if x]
    out = []
    for k in range(1, len(t)):
        firsts, lasts = t[:k], t[k:]
        for f in dict.fromkeys(firsts + ["".join(firsts)]):
            for l in dict.fromkeys(["".join(lasts), lasts[-1]]):
                out.append(f"{f}.{l}")
    return list(dict.fromkeys(out))


def gitlab_account(host, p):
    """(username, id, matched_by). Placeholder (imported) accounts are rejected.
    A username match must also share a name token with the Home display name."""
    want = toks(p.get("displayName"))
    for u in dict.fromkeys(filter(None, [p["username"], (p.get("email") or "").split("@")[0]])):
        for c in gl_api(host, f"users?username={quote(u)}"):
            if "placeholder" in c.get("username", ""):
                continue
            if want and not (want & toks(c.get("name"))):
                return None, None, f"username-name-mismatch:{c['username']}={c.get('name')}"
            return c["username"], c["id"], "username"
    scored = {}
    for u in name_variants(p.get("displayName")):
        for c in gl_api(host, f"users?username={quote(u)}"):
            if "placeholder" in c.get("username", ""):
                continue
            have = toks(c.get("name"))
            scored[c["username"]] = (len(want & have) / len(want | have) if want | have else 0, c["id"])
    ranked = sorted(scored.items(), key=lambda kv: -kv[1][0])
    if not ranked or ranked[0][1][0] < 0.5:
        return None, None, None
    if len(ranked) > 1 and ranked[0][1][0] == ranked[1][1][0]:
        return None, None, "ambiguous:" + ",".join(u for u, _ in ranked)
    return ranked[0][0], ranked[0][1][1], "name-variant"


def github_logins(p, org, domain):
    emails = [p["email"]] if p.get("email") else [f"{p['username']}@{domain}"]
    logins = set()
    for e in emails:
        data = gh_get(["search/commits", "-f", f"q=author-email:{e} org:{org}", "-f", "per_page=5"])
        for i in data["items"]:
            if i.get("author") and not i["author"]["login"].endswith("[bot]"):
                logins.add(i["author"]["login"])
        time.sleep(2.1)
    return sorted(logins)


def cmd_accounts(a):
    host = a.gitlab_host or default_gitlab_host()
    if not host:
        sys.exit("accounts: no GitLab host; pass --gitlab-host")
    everyone = load(a.roster)
    counted = lambda p: not p.get("exclude_from_pull") and (p.get("status") or "onboard").lower() in COUNTED_STATUSES
    roster = [p for p in everyone if counted(p)]
    use_gh = not a.no_github and shutil.which("gh") and run(["gh", "api", "user"])[0] == 0
    out, errors = [], []
    for p in roster:
        try:
            gl_user, gl_id, how = gitlab_account(host, p)
        except FetchError as e:
            gl_user, gl_id, how = None, None, None
            errors.append(f"{p['username']}: {e}")
        gh = p.get("github_logins") or []
        # Never derive an email from a name-variant GitLab match: it may be the wrong person.
        # After the person confirms such a match, they set "email" in the roster and re-run.
        if use_gh and not gh and (p.get("email") or how != "name-variant"):
            try:
                gh = github_logins(p, a.github_org, a.email_domain)
            except FetchError as e:
                errors.append(f"{p['username']} (GitHub): {e}")
        out.append({**p, "counted": True, "gitlab_host": host, "gitlab_user": gl_user, "gitlab_id": gl_id,
                    "gitlab_matched_by": how, "github_logins": gh})
    # Not-counted people stay in the file (no accounts) so area inheritance through managers works.
    out += [{**p, "counted": False, "gitlab_host": host, "gitlab_user": None, "gitlab_id": None,
             "gitlab_matched_by": None, "github_logins": []} for p in everyone if not counted(p)]
    dump(out, a.out)
    out = [p for p in out if p["counted"]]
    print(json.dumps({
        "gitlab_host": host,
        "people": len(out),
        "review_these_matches": [f"{p['username']} -> {p['gitlab_user'] or p['gitlab_matched_by']}" for p in out
                                 if p["gitlab_matched_by"] and p["gitlab_matched_by"] != "username"],
        "shared_gitlab_accounts": sorted({p["gitlab_user"] for p in out if p["gitlab_user"]
                                          and sum(q["gitlab_user"] == p["gitlab_user"] for q in out) > 1}),
        "no_gitlab": [p["username"] for p in out if not p["gitlab_id"]],
        "no_github": [p["username"] for p in out if not p["github_logins"]] if use_gh else "skipped: gh missing, signed out, or --no-github",
        "errors": errors,
    }, indent=1))
    sys.exit(1 if errors else 0)


# ---------- pull ----------

def area_for(person, users, area_map, depth=0):
    groups = area_map.get("groups") or {}
    g = person.get("group") or ""
    if not groups:
        return g or "(no group)"
    if g in groups:
        return groups[g]
    mgr = users.get((person.get("manager") or "").lower())
    if mgr and depth < 6:
        return area_for(mgr, users, area_map, depth + 1)
    return area_map.get("default_area") or "(unassigned)"


def cmd_pull(a):
    start, end = check_iso(a.start, "--start"), check_iso(a.end, "--end")
    everyone = load(a.accounts)
    hosts = {p.get("gitlab_host") for p in everyone} - {None}
    host = a.gitlab_host or (hosts.pop() if len(hosts) == 1 else None)
    if not host or (a.gitlab_host and hosts and a.gitlab_host not in hosts):
        sys.exit(f"pull: GitLab host must match the one used by `accounts` ({sorted(hosts) or 'none recorded'})")
    acct = [p for p in everyone if p.get("counted", True)]
    area_map = load(a.area_map) if a.area_map else {}
    users = {p["username"].lower(): p for p in everyone}
    org_ns = tuple(x.strip() for x in a.org_namespaces.split(",") if x.strip())
    items, errors, warnings = [], [], []

    def gl_pull(p):
        if not p.get("gitlab_id"):
            return [], None
        try:
            got = gl_pages(host, f"merge_requests?author_id={p['gitlab_id']}&scope=all&updated_after={start}")
        except FetchError as e:
            return [], f"{p['username']}: {e}"
        res = []
        for m in got:
            merged_at = m.get("merged_at") or ""
            if in_window(merged_at, start, end) or (m["state"] == "opened" and in_window(m["created_at"], start, end)):
                res.append({"username": p["username"], "project": m["references"]["full"].split("!")[0], "iid": m["iid"],
                            "title": m["title"], "state": "merged" if merged_at else m["state"], "merged_at": merged_at,
                            "created_at": m["created_at"], "url": m["web_url"], "target_branch": m.get("target_branch"),
                            "draft": bool(m.get("draft")), "labels": m.get("labels", []),
                            "desc": re.sub(r"\s+", " ", m.get("description") or "")[:1500]})
        return res, None

    with ThreadPoolExecutor(8) as ex:
        for res, err in ex.map(gl_pull, acct):
            items += res
            if err:
                errors.append(err)

    use_gh = not a.no_github and shutil.which("gh") and run(["gh", "api", "user"])[0] == 0
    if use_gh:
        d0, d1 = start[:10], end[:10]
        for p in acct:
            for login in p.get("github_logins", []):
                for state, q in (("merged", f"is:pr org:{a.github_org} author:{login} merged:{d0}..{d1}"),
                                 ("opened", f"is:pr org:{a.github_org} author:{login} is:open created:{d0}..{d1}")):
                    try:
                        found, total = gh_search_all(q)
                    except FetchError as e:
                        errors.append(f"{p['username']} ({login}, {state}): {e}")
                        continue
                    if total > len(found):
                        warnings.append(f"GitHub search ceiling for {login} ({state}): {total} results, {len(found)} fetched")
                    for i in found:
                        merged_at = (i.get("pull_request") or {}).get("merged_at") or ""
                        # The search uses whole UTC dates; keep only items inside the exact window.
                        if not (in_window(merged_at, start, end) if state == "merged" else in_window(i["created_at"], start, end)):
                            continue
                        items.append({"username": p["username"], "project": "github:" + i["repository_url"].split("/repos/")[1],
                                      "iid": i["number"], "title": i["title"], "state": state,
                                      "merged_at": (i.get("pull_request") or {}).get("merged_at") or "",
                                      "created_at": i["created_at"], "url": i["html_url"], "target_branch": None,
                                      "draft": bool(i.get("draft")), "labels": [x["name"] for x in i.get("labels", [])],
                                      "desc": re.sub(r"\s+", " ", i.get("body") or "")[:1500]})
                    time.sleep(2.1)
    else:
        warnings.append("GitHub skipped: gh missing, signed out, or --no-github")

    seen, dedup, excluded_ns = set(), [], {}
    for x in items:
        if x["url"] in seen:
            continue
        seen.add(x["url"])
        x["personal"] = not x["project"].startswith(org_ns)
        if x["personal"]:
            ns = x["project"].split("/")[0]
            excluded_ns[ns] = excluded_ns.get(ns, 0) + 1
        x["area"] = next((r["area"] for r in area_map.get("repo_rules", []) if re.search(r["pattern"], x["project"])), None) \
            or area_for(users.get(x["username"].lower(), {}), users, area_map)
        x["backport"] = bool(BACKPORT_HINT.search(x["title"]) or re.search(r"maint|release", x.get("target_branch") or "", re.I))
        x["security_hint"] = bool(SECURITY_HINT.search(x["title"] + " " + " ".join(x["labels"])))
        dedup.append(x)
    dump(dedup, a.out)
    print(json.dumps({
        "items": len(dedup),
        "counted": sum(not x["personal"] for x in dedup),
        "excluded_as_personal_by_namespace": dict(sorted(excluded_ns.items(), key=lambda kv: -kv[1])),
        "security_hint_items": sum(x["security_hint"] for x in dedup if not x["personal"]),
        "people_with_items": len({x["username"] for x in dedup if not x["personal"]}),
        "people_with_no_items": sorted(p["username"] for p in acct if (p.get("gitlab_id") or p.get("github_logins"))
                                       and p["username"] not in {x["username"] for x in dedup if not x["personal"]}),
        "warnings": warnings, "errors": errors}, indent=1))
    sys.exit(1 if errors else 0)


# ---------- counts ----------

def cmd_counts(a):
    items = [x for x in load(a.items) if not x["personal"]]
    areas = sorted({x["area"] for x in items}, key=lambda k: (k != a.first, k))
    rows = ["| Area | Merged | Open | Contributors | Main repos (by MR count) |", "|---|---|---|---|---|"]
    tm = to = 0
    tp, tr = set(), set()
    for k in areas:
        v = [x for x in items if x["area"] == k]
        m = sum(x["state"] == "merged" for x in v)
        o = len(v) - m
        top = {}
        for x in v:
            top[x["project"]] = top.get(x["project"], 0) + 1
        names = [p.replace("github:", "").split("/")[-1] + (" (GitHub)" if p.startswith("github:") else "")
                 for p, _ in sorted(top.items(), key=lambda kv: -kv[1])[:4]]
        rows.append(f"| {k} | {m} | {o} | {len({x['username'] for x in v})} | {', '.join(names)} |")
        tm += m; to += o; tp |= {x["username"] for x in v}; tr |= {x["project"] for x in v}
    rows.append(f"| Total | {tm} | {to} | {len(tp)} | {len(tr)} repos in all |")
    print("\n".join(rows))
    print(json.dumps({"merged": tm, "open": to, "contributors": len(tp), "repos": len(tr),
                      "backports": sum(x["backport"] for x in items)}))


# ---------- linkcheck ----------

OPEN_HEADING = re.compile(r"in flight|\(open\)", re.I)
OPEN_LINE = re.compile(r"\bOpen:|\(open\)|\(drafts?\)|\bopen \(draft\)|\ban open (MR|PR)\b", re.I)


def cmd_linkcheck(a):
    start, end = check_iso(a.start, "--start"), check_iso(a.end, "--end")
    text = re.sub(r"\\([!()\[\]_*#.-])", r"\1", open(a.report).read())  # undo Google Docs markdown-export escapes
    acct = [p for p in load(a.accounts) if p.get("counted", True)]
    allowed = {}
    for x in a.allow or []:
        m = re.match(r"^(https?://[^=\s]+)=(.+)$", x)
        if not m:
            sys.exit(f"linkcheck: --allow must be URL=reason, got {x!r}")
        allowed[m.group(1)] = m.group(2)
    org_ns = tuple(x.strip() for x in a.org_namespaces.split(",") if x.strip())
    gl_users = {(p.get("gitlab_user") or "").lower() for p in acct} - {""}
    gh_users = {l.lower() for p in acct for l in p.get("github_logins", [])}
    # Each link is judged with its heading and its top-level bullet, because the
    # bullet format puts links on a sub-line under the labelled parent bullet.
    occurrences, heading, bullet = {}, "", ""
    for line in text.splitlines():
        if line.startswith("#"):
            heading, bullet = line, ""
        elif re.match(r"^[-*] |^\d+\. ", line):
            bullet = line
        for url in re.findall(r"\]\((https?://[^)\s]+)\)", line):
            occurrences.setdefault(url, []).append((heading, line if line == bullet else bullet + " " + line))

    def check(url):
        m = re.match(r"https://([^/]+)/(.+?)/-/merge_requests/(\d+)", url)
        try:
            if m:
                d = gl_api(m.group(1), f"projects/{quote(m.group(2), safe='')}/merge_requests/{m.group(3)}", want=dict)
                return url, d.get("state"), d.get("merged_at") or "", d.get("created_at") or "", (d.get("author") or {}).get("username", ""), "gl", None
            m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
            if m:
                rc, out, err = run(["gh", "pr", "view", m.group(3), "--repo", f"{m.group(1)}/{m.group(2)}", "--json", "state,mergedAt,createdAt,author"])
                if rc:
                    raise FetchError(err[:200])
                d = json.loads(out)
                return url, d["state"].lower(), d.get("mergedAt") or "", d.get("createdAt") or "", d["author"]["login"], "gh", None
        except (FetchError, ValueError, KeyError) as e:
            return url, None, "", "", "", "err", str(e)
        return url, "not-an-mr", "", "", "", "other", None

    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(check, sorted(occurrences)))
    flagged, states = [], {}
    for url, state, merged, created, author, kind, err in results:
        states[state or "unreadable"] = states.get(state or "unreadable", 0) + 1
        if kind == "other":
            continue
        issues = []
        if err:
            issues.append(f"could-not-read: {err}")
        else:
            if state not in ("merged", "opened", "open"):
                issues.append(f"state={state}")
            if state == "merged" and not in_window(merged, start, end):
                issues.append("merged-outside-window")
            if state in ("opened", "open"):
                if not in_window(created, start, end):
                    issues.append("open-but-opened-before-window")
                for h, line in occurrences[url]:
                    if not (OPEN_HEADING.search(h) or OPEN_LINE.search(line)):
                        issues.append(f"open-but-not-labelled-open: {line.strip()[:70]}")
            if author.lower() not in (gl_users if kind == "gl" else gh_users):
                issues.append(f"author-not-on-roster: {author}")
            proj = re.sub(r"^https://[^/]+/(.+?)/-/merge_requests/.*", r"\1", url) if kind == "gl" else \
                "github:" + re.sub(r"^https://github\.com/([^/]+/[^/]+)/pull/.*", r"\1", url)
            if not proj.startswith(org_ns):
                issues.append(f"personal-sandbox-link: {proj}")
        if issues and url in allowed:
            continue
        if issues:
            flagged.append({"url": url, "state": state, "author": author, "issues": issues})
    print(json.dumps({"links": len(results), "states": states, "allowed": allowed, "flagged": flagged}, indent=1))
    sys.exit(1 if flagged else 0)


# ---------- tally ----------

def cmd_tally(a):
    allowed = ("VERIFIED", "PARTLY", "UNSUPPORTED", "WRONG")
    counts, bad, files = {v: 0 for v in allowed}, [], sorted({f for pat in a.verdicts for f in glob.glob(pat)})
    if not files:
        sys.exit("tally: no verdict files matched")
    for f in files:
        rows = load(f)
        if not isinstance(rows, list):
            sys.exit(f"tally: {f} must hold a JSON list of verdict objects")
        for i, row in enumerate(rows):
            v = str((row or {}).get("verdict", "")).strip().upper()
            if v in allowed:
                counts[v] += 1
            else:
                bad.append(f"{f}[{i}]: {v or 'missing'}")
    print(json.dumps({"files": len(files), "claims": sum(counts.values()), "verdicts": counts, "invalid": bad}))
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, gh=True):
        p.add_argument("--gitlab-host", help="GitLab host; default: `glab config get host`")
        if gh:
            p.add_argument("--github-org", default="appian")
            p.add_argument("--no-github", action="store_true")

    p = sub.add_parser("preflight"); common(p, gh=False)
    p = sub.add_parser("window"); p.add_argument("--since"); p.add_argument("--from", dest="from_"); p.add_argument("--to")
    p = sub.add_parser("roster-check"); p.add_argument("--roster", required=True)
    p = sub.add_parser("accounts"); p.add_argument("--roster", required=True); p.add_argument("--out", required=True)
    p.add_argument("--email-domain", default="appian.com"); common(p)
    p = sub.add_parser("pull"); p.add_argument("--accounts", required=True); p.add_argument("--start", required=True)
    p.add_argument("--end", required=True); p.add_argument("--out", required=True); p.add_argument("--area-map"); common(p)
    p.add_argument("--org-namespaces", default="appian/,docs/,github:",
                   help="comma-separated project prefixes that count as org work; anything else is a personal sandbox")
    p = sub.add_parser("counts"); p.add_argument("--items", required=True); p.add_argument("--first", help="area to list first")
    p = sub.add_parser("linkcheck"); p.add_argument("--report", required=True); p.add_argument("--accounts", required=True)
    p.add_argument("--start", required=True); p.add_argument("--end", required=True)
    p.add_argument("--allow", action="append", help="URL=reason for a flag the person has accepted; listed in the output")
    p.add_argument("--org-namespaces", default="appian/,docs/,github:")
    p = sub.add_parser("tally"); p.add_argument("--verdicts", nargs="+", required=True, help="reviewer JSON files or globs")
    a = ap.parse_args()
    {"preflight": cmd_preflight, "window": cmd_window, "roster-check": cmd_roster_check, "accounts": cmd_accounts,
     "pull": cmd_pull, "counts": cmd_counts, "linkcheck": cmd_linkcheck, "tally": cmd_tally}[a.cmd](a)


if __name__ == "__main__":
    main()
