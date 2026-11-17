"""Build data/identity.csv (Jira, GitLab, GitHub identity per roster person, confidence exact|overridden|none)
and propose data/identity_overrides.csv. READ-ONLY calls: acli search, tools/ro/ro (GET only).
Usage: identity.py [--only "Name"] [--skip-github]   Applies overrides from data/identity_overrides.csv (rows with a handle)."""
import sys, json, collections, subprocess, time, re, unicodedata, pathlib, argparse
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import *
RO = str(ROOT / "tools/ro/ro"); CACHE = ROOT / "data/extracts/roster/identity_cache.json"
IDCOLS = ["person","home_username","home_source","jira_account_id","jira_email","jira_confidence","jira_reason",
          "gitlab_username","gitlab_id","gitlab_confidence","gitlab_reason","github_login","github_confidence","github_reason"]
OVCOLS = ["person","system","handle","reason","candidates"]
def fold(s): return re.sub(r"[^a-z0-9.]", "", unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower())
def run(cmd, timeout=90):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout); return r.returncode, r.stdout, r.stderr
def usernames(r):
    out = []
    hu = {norm(x["person"]): x["username"] for x in read_csv(DATA / "roster_home_usernames.csv")}
    if norm(r["name"]) in hu: return [hu[norm(r["name"])]]   # a Home-confirmed username is the only candidate
    for nm in (r["name"], r["chart_name"]):
        t = [fold(x) for x in nm.split() if fold(x)]
        if len(t) >= 2:
            for c in (f"{t[0]}.{t[-1]}", f"{t[0]}.{''.join(t[1:])}"):
                if c not in out: out.append(c)
    return out
def jira_lookup(email):
    code, o, e = run(["acli","jira","workitem","search","--jql",f'assignee = "{email}" OR reporter = "{email}"',"--fields","assignee,reporter","--limit","3","--json"])
    if code != 0: return None, f"acli error: {e.strip()[:80]}"
    try: items = json.loads(o)
    except Exception: return None, "acli output not JSON"
    for it in items:
        for k in ("assignee","reporter"):
            u = (it.get("fields") or {}).get(k) or {}
            if (u.get("emailAddress") or "").lower() == email.lower(): return u["accountId"], ""
    return None, "no issue found with this person as assignee or reporter" if not items else "issues found but email not visible"
def gl_lookup(u):
    code, o, e = run([RO,"glab","api",f"/users?username={u}"])
    if code != 0: return None, None, f"glab error {code}"
    try: d = json.loads(o)
    except Exception: return None, None, "bad json"
    for x in d:
        if x["username"].lower() == u.lower(): return x["username"], x["id"], ""
    return None, None, "no exact username match"
_members = None
def gh_members():
    global _members
    if _members is None:
        code, o, e = run([RO,"gh","api",f"/orgs/{CFG['github_org']}/members?per_page=100","--paginate"], 300)
        _members = []
        for chunk in re.findall(r"\[.*?\]", o.replace("]\n[", "]\n[")) if False else [o]:
            pass
        dec = json.JSONDecoder(); i = 0; o = o.strip()
        while i < len(o):
            v, j = dec.raw_decode(o, i); _members += [m["login"] for m in v]; i = j
            while i < len(o) and o[i].isspace(): i += 1
        _members = sorted(set(_members))
    return _members
def gh_lookup(r, cache):
    names = {norm(r["name"]), norm(r["chart_name"])}
    last = fold(r["chart_name"].split()[-1]); first = fold(r["chart_name"].split()[0])
    cands = [m for m in gh_members() if len(last) >= 3 and last in fold(m)] 
    hits, seen = [], []
    for m in cands:
        if m not in cache:
            code, o, e = run([RO,"gh","api",f"/users/{m}"]); 
            try: cache[m] = json.loads(o).get("name") or ""
            except Exception: cache[m] = ""
        seen.append(m)
        if norm(cache[m]) in names: hits.append(m)
    if len(hits) == 1: return hits[0], "", seen
    if len(hits) > 1: return None, f"{len(hits)} org members share this profile name", hits
    return None, ("no org member has a profile name equal to the chart or directory name" + (f"; {len(seen)} login(s) contain the surname, none matched" if seen else "; no login contains the surname")), seen
def gh_commit_email(email):
    """Second method: commits in the org authored with the person's work email; the login must be an org member."""
    time.sleep(2.6)
    code, o, e = run([RO, "gh", "api", f"/search/commits?q=author-email:{email}+org:{CFG['github_org']}&per_page=10", "-q", "[.items[].author.login // empty] | unique | join(\",\")"])
    if code != 0: return None, f"commit search error {code}"
    logins = [x for x in o.strip().split(",") if x]
    if len(logins) != 1: return None, ("no org commit authored with this email shows a GitHub login" if not logins else f"commits with this email map to {len(logins)} logins")
    c, _, _ = run([RO, "gh", "api", f"/orgs/{CFG['github_org']}/members/{logins[0]}", "--silent"])
    return (logins[0], "") if c == 0 else (None, f"login {logins[0]} from commits is not an org member")
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--only"); ap.add_argument("--skip-github", action="store_true"); a = ap.parse_args()
    ros = read_csv(ROSTER); ov = {(o["person"],o["system"]): o for o in read_csv(OVERRIDES) if o.get("handle")}
    cache = json.load(open(CACHE)) if CACHE.exists() else {}
    ident = {i["person"]: i for i in read_csv(IDENT)}; props = []; done = set()
    for r in ros:
        if a.only and r["name"] not in a.only.split("|"): continue
        done.add(r["name"])
        row = {c: "" for c in IDCOLS}; row["person"] = r["name"]
        user = None; row["jira_confidence"] = "none"
        for c in usernames(r):
            aid, why = jira_lookup(c + "@" + CFG["email_domain"])
            if aid: user, row["jira_account_id"], row["jira_email"], row["jira_confidence"], row["home_source"] = c, aid, c + "@" + CFG["email_domain"], "exact", "pattern first.last, confirmed by Jira email"; break
        if not user: row["jira_reason"] = why + f" (tried {', '.join(c + '@' + CFG['email_domain'] for c in usernames(r))})"
        o = ov.get((r["name"], "jira"))
        if o: row.update(jira_account_id=o["handle"], jira_confidence="overridden", jira_reason=o["reason"])
        cand_user = user or (usernames(r) or [""])[0]
        hu = {norm(x["person"]): x for x in read_csv(DATA / "roster_home_usernames.csv")}.get(norm(r["name"]))
        row["home_username"] = user or (hu["username"] if hu else "")
        if not user: row["home_source"] = (hu["source"] + "; no Jira email match") if hu else "unverified: no Jira email match and not in the Home username list"
        gu, gid, gwhy = None, None, ""
        for c in ([user] if user else usernames(r)):
            gu, gid, gwhy = gl_lookup(c)
            if gu: break
        o = ov.get((r["name"], "gitlab"))
        if o: row.update(gitlab_username=o["handle"], gitlab_confidence="overridden", gitlab_reason=o["reason"])
        elif gu: row.update(gitlab_username=gu, gitlab_id=gid, gitlab_confidence="exact")
        else: row.update(gitlab_confidence="none", gitlab_reason=(gwhy or "") + (" for the Home username" if (user or hu) else " (Home username unverified)"))
        if not a.skip_github:
            o = ov.get((r["name"], "github"))
            if o: row.update(github_login=o["handle"], github_confidence="overridden", github_reason=o["reason"]); seen = []
            else:
                gl, gwhy2, seen = gh_lookup(r, cache)
                if gl: row.update(github_login=gl, github_confidence="exact", github_reason="profile name equals chart or directory name; org member")
                else:
                    em = row["jira_email"] or ((row["home_username"] + "@" + CFG["email_domain"]) if row["home_username"] else "")
                    gl2, why2 = gh_commit_email(em) if em else (None, "no work email known")
                    if gl2: row.update(github_login=gl2, github_confidence="exact", github_reason="org commit authored with the work email; org member")
                    else: row.update(github_confidence="none", github_reason=gwhy2 + "; commit-email method: " + why2)
        else: row.update(github_confidence="none", github_reason="not run")
        ident[r["name"]] = row
        for sysn, conf, cands in (("jira", row["jira_confidence"], []), ("gitlab", row["gitlab_confidence"], []), ("github", row["github_confidence"], seen if not a.skip_github else [])):
            if conf == "none": props.append({"person": r["name"], "system": sysn, "handle": "", "reason": "", "candidates": "|".join(cands[:6])})
        print(r["name"], row["jira_confidence"], row["gitlab_confidence"], row["github_confidence"], flush=True)
    for sysn, key, conf in (("jira", "jira_account_id", "jira_confidence"), ("gitlab", "gitlab_id", "gitlab_confidence"), ("github", "github_login", "github_confidence")):
        byid = collections.defaultdict(list)
        for pn, row in ident.items():
            if row[key] and row[conf] == "exact": byid[row[key]].append(pn)
        for k, people in byid.items():
            if len(people) > 1:
                for pn in people:
                    ident[pn][conf] = "none"; ident[pn][sysn + "_reason"] = f"one account matches {len(people)} roster rows ({', '.join(people)}); user to decide (user-entry.md)"
                    ident[pn][key] = ""
                    if sysn == "jira": ident[pn]["jira_email"] = ""
                    props.append({"person": pn, "system": sysn, "handle": "", "reason": "", "candidates": k})
    write_csv(IDENT, [ident[r["name"]] for r in ros if r["name"] in ident], IDCOLS)
    old = [o for o in read_csv(OVERRIDES)]; keep = {(o["person"],o["system"]) for o in old if o.get("handle")}
    write_csv(OVERRIDES, [o for o in old if o.get("handle") or o["person"] not in done] + [p for p in props if (p["person"],p["system"]) not in keep], OVCOLS)
    CACHE.parent.mkdir(parents=True, exist_ok=True); json.dump(cache, open(CACHE,"w"))
main()
