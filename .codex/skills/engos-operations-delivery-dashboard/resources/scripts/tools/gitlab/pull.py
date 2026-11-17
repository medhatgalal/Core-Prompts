#!/usr/bin/env python3
"""GitLab bulk pull (AC7, AC8). GET only through tools/ro/ro. No model calls (AC55).
Stores keys, numbers, lengths, flags; never titles, descriptions, branch names, or note text.
Resumable: every list page and every per-change result is appended to a checkpoint file.
  pull.py --out DIR [--asof ISO] [--users a,b] [--budget 40000] [--narrow-at 36000] [--workers 8]
"""
import argparse, csv, datetime, json, os, re, sys, threading, time, queue
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glapi

KEY = re.compile(r"(?<![A-Za-z0-9-])[A-Z][A-Z0-9]+-\d+(?!\d)")
LOCK_RE = re.compile(r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|npm-shrinkwrap\.json|poetry\.lock|Pipfile\.lock|Cargo\.lock|go\.sum|composer\.lock|Gemfile\.lock|gradle\.lockfile|packages\.lock\.json)$|\.lock$")
GEN_RE = re.compile(r"(\.min\.(js|css)$|\.pb\.go$|_pb2(_grpc)?\.py$|\.snap$|(^|/)(generated|dist|build|vendor|node_modules)/|\.generated\.|\.map$)")
DOC_RE = re.compile(r"(\.(md|mdx|rst|adoc|txt)$|(^|/)docs?/|(^|/)(LICENSE|CHANGELOG|README)[^/]*$)", re.I)
BOT_RE = re.compile(r"(_bot$|^project_\d+_bot|^group_\d+_bot|-bot$|^svc[-_.]|[-_.]svc$|^ghost$|^gitlab-)", re.I)
APPROVE = "approved this merge request"


def iso(s):
    return s if s else ""


def parse(ts):
    return datetime.datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)


class Budget:
    def __init__(self, path, budget, narrow_at):
        self.path, self.budget, self.narrow_at = path, budget, narrow_at
        self.lock = threading.Lock()
        self.n = 0; self.r429 = 0; self.errors = 0
        if os.path.exists(path):
            d = json.load(open(path)); self.n = d.get("pull_calls", 0); self.r429 = d.get("retries_429", 0); self.errors = d.get("final_errors", 0)
        self.stop = False

    def save(self):
        json.dump({"pull_calls": self.n, "retries_429": self.r429, "final_errors": self.errors,
                   "budget": self.budget, "narrow_at": self.narrow_at, "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
                  open(self.path + ".tmp", "w")); os.replace(self.path + ".tmp", self.path)

    def get(self, path):
        with self.lock:
            if self.n >= self.budget:
                self.stop = True
                raise RuntimeError("BUDGET HARD STOP")
            self.n += 1
            if self.n % 20 == 0: self.save()
        s, h, d = glapi.get(path)
        if s == 429:
            with self.lock: self.r429 += 1
        if s >= 400 or s == 0:
            with self.lock: self.errors += 1
        return s, h, d


def list_pages(B, base_q, ckdir, tag):
    """All pages of a list query; one checkpoint file per page. Returns (items, x_total_first)."""
    os.makedirs(ckdir, exist_ok=True)
    items, page, xtotal = [], 1, None
    while True:
        f = os.path.join(ckdir, f"{tag}__p{page:04d}.json")
        if os.path.exists(f):
            blob = json.load(open(f))
        else:
            s, h, d = B.get(f"/merge_requests?{base_q}&per_page=100&page={page}")
            if s != 200:
                raise RuntimeError(f"list {tag} page {page} status {s}")
            blob = {"items": [slim(m) for m in d], "x_total": h.get("x-total"), "next": h.get("x-next-page") or ""}
            json.dump(blob, open(f + ".tmp", "w")); os.replace(f + ".tmp", f)
        if page == 1: xtotal = blob["x_total"]
        items += blob["items"]
        if not blob["next"]: break
        page = int(blob["next"])
    return items, xtotal


def slim(m):
    """Derive what we keep from a list item. Titles/descriptions/branches are read here, never stored."""
    title, branch, desc = m.get("title") or "", m.get("source_branch") or "", m.get("description") or ""
    keys = []
    for src, text in (("title", title), ("branch", branch), ("description", desc)):
        for k in KEY.findall(text):
            keys.append([k, src])
    low = (title + " " + branch).lower()
    if re.match(r"^(revert|reapply)\b", title.lower()) or branch.lower().startswith("revert"): cl = "revert"
    elif re.search(r"cherry[- ]?pick|backport", low): cl = "backport"
    elif re.search(r"\brelease\b|merge[- ]train", low): cl = "release"
    else: cl = "normal"
    web = m.get("web_url", "")
    path = web.split("/-/merge_requests")[0].split("://", 1)[-1].split("/", 1)[-1] if web else ""
    au = (m.get("author") or {}).get("username", "")
    return {"project_id": m["project_id"], "iid": m["iid"], "project_path": path, "author": au,
            "state": m["state"], "draft": bool(m.get("draft")), "created_at": iso(m.get("created_at")),
            "merged_at": iso(m.get("merged_at")), "closed_at": iso(m.get("closed_at")), "updated_at": iso(m.get("updated_at")),
            "sha": m.get("sha") or "", "squash_commit_sha": m.get("squash_commit_sha") or "", "merge_commit_sha": m.get("merge_commit_sha") or "",
            "merged_by": (m.get("merged_by") or m.get("merge_user") or {}).get("username", ""),
            "fork": m.get("source_project_id") != m.get("target_project_id"),
            "desc_len": len(re.sub(r"\s", "", desc)), "title_class": cl, "keys": keys,
            "reviewers_assigned": [r.get("username", "") for r in (m.get("reviewers") or [])]}


def notes_for(B, pid, iid):
    notes, p = [], 1
    while True:
        s, h, d = B.get(f"/projects/{pid}/merge_requests/{iid}/notes?per_page=100&page={p}&sort=asc")
        if s != 200: raise RuntimeError(f"notes {pid}/{iid} status {s}")
        notes += d
        if not h.get("x-next-page"): break
        p = int(h["x-next-page"])
    ev = []
    last_nonsys = ""
    for n in notes:
        au = (n.get("author") or {}).get("username", "")
        if n.get("system"):
            if (n.get("body") or "").startswith(APPROVE):
                ev.append([au, n["created_at"], "approval"])
        else:
            ev.append([au, n["created_at"], "comment"])
            last_nonsys = max(last_nonsys, n["created_at"])
    return ev, last_nonsys


def diffs_for(B, pid, iid):
    p, files, tot, excl, incomplete, allfiles_docs = 1, 0, 0, 0, False, True
    while True:
        s, h, d = B.get(f"/projects/{pid}/merge_requests/{iid}/diffs?per_page=100&page={p}")
        if s != 200: raise RuntimeError(f"diffs {pid}/{iid} status {s}")
        for f in d:
            files += 1
            name = f.get("new_path") or f.get("old_path") or ""
            text = f.get("diff") or ""
            if f.get("too_large") or f.get("collapsed"): incomplete = True
            n = sum(1 for l in text.split("\n") if (l.startswith("+") or l.startswith("-")))
            tot += n
            if not (LOCK_RE.search(name) or GEN_RE.search(name)): excl += n
            if not DOC_RE.search(name): allfiles_docs = False
        if not h.get("x-next-page"): break
        p = int(h["x-next-page"])
    return {"files": files, "lines": tot, "lines_excl": excl, "incomplete": incomplete, "docs_only": files > 0 and allfiles_docs}


def commit_keys(B, m):
    out = []
    if m.get("squash_commit_sha"):
        s, h, d = B.get(f"/projects/{m['project_id']}/repository/commits/{m['squash_commit_sha']}")
        if s == 200 and d:
            out += [[k, "commit"] for k in KEY.findall((d.get("message") or ""))]
    if not out:
        s, h, d = B.get(f"/projects/{m['project_id']}/merge_requests/{m['iid']}/commits?per_page=100")
        if s == 200 and d:
            for c in d:
                out += [[k, "commit"] for k in KEY.findall(c.get("message") or "")]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--asof", required=True)
    ap.add_argument("--identity", default="data/identity.csv")
    ap.add_argument("--users", default=""); ap.add_argument("--budget", type=int, default=45000)
    ap.add_argument("--narrow-at", type=int, default=40500); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--review-months", type=int, default=12, help="D8: 6 = notes only for changes merged (or, if not merged, updated) in the last 6 months before as-of")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    asof = parse(a.asof); start = (asof - datetime.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    six = asof - datetime.timedelta(days=182)
    narrow_all = a.review_months == 6
    open(os.path.join(a.out, "as_of.txt"), "w").write(a.asof + "\n")
    B = Budget(os.path.join(a.out, "calls.json"), a.budget, a.narrow_at)
    ident = [r for r in csv.DictReader(open(a.identity))]
    only = set(filter(None, a.users.split(",")))
    people = [r for r in ident if r["gitlab_confidence"] in ("exact", "overridden") and (not only or r["gitlab_username"] in only)]
    roster_users = {r["gitlab_username"] for r in ident if r["gitlab_confidence"] in ("exact", "overridden")}
    W = f"scope=all&created_after={start}&created_before={a.asof}"
    ck = os.path.join(a.out, "checkpoints")
    authored, others, counts = {}, {}, []
    for r in people:
        u = r["gitlab_username"]
        items, xt = list_pages(B, f"author_username={u}&{W}&order_by=created_at&sort=desc", ck, f"authored__{u}")
        counts.append([r["person"], u, "authored", xt if xt is not None else len(items), len(items)])
        for m in items: authored[(m["project_id"], m["iid"])] = m
        for kind, q in (("approved", f"approved_by_usernames[]={u}&not[author_username]={u}"), ("reviewer", f"reviewer_username={u}&not[author_username]={u}")):
            items, xt = list_pages(B, f"{q}&{W}&order_by=created_at&sort=desc", ck, f"{kind}__{u}")
            counts.append([r["person"], u, kind, xt if xt is not None else len(items), len(items)])
            for m in items:
                k = (m["project_id"], m["iid"])
                others.setdefault(k, {"mr": m, "by": {}})["by"].setdefault(u, set()).add(kind)
    B.save()
    with open(os.path.join(a.out, "list_counts.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["person", "gitlab_username", "kind", "x_total_first_page", "rows_pulled"]); w.writerows(counts)
    print(f"lists done: authored {len(authored)}, others-only {len([k for k in others if k not in authored])}, calls {B.n}", flush=True)

    # per-change detail, newest first; resumable
    dpath = os.path.join(a.out, "detail.jsonl")
    done, done_full = set(), set()
    if os.path.exists(dpath):
        for l in open(dpath):
            try:
                d = json.loads(l); done.add((d["project_id"], d["iid"]))
                if "diff" in d: done_full.add((d["project_id"], d["iid"]))
            except ValueError: pass
    tasks = []
    for k, m in authored.items(): tasks.append((m["created_at"], k, m, "authored"))
    for k, o in others.items():
        if k not in authored: tasks.append((o["mr"]["created_at"], k, o["mr"], "other"))
    tasks.sort(key=lambda t: t[0], reverse=True)
    q = queue.Queue()
    for t in tasks:
        if (t[3] == "authored" and t[1] not in done_full) or (t[3] != "authored" and t[1] not in done): q.put(t)
    wl = threading.Lock(); fh = open(dpath, "a"); stats = {"done": len(done), "narrowed": False, "narrow_after_calls": None, "fail": 0}

    def work():
        while True:
            try: _, k, m, kind = q.get_nowait()
            except queue.Empty: return
            try:
                rec = {"project_id": k[0], "iid": k[1], "kind": kind}
                if B.n >= B.narrow_at:
                    # D11: do not narrow on our own; stop and report
                    B.stop = True
                    if not stats["narrowed"]:
                        stats["narrowed"] = True; stats["narrow_after_calls"] = B.n
                        print(f"STOP at {B.n} calls (narrow_at reached); reporting, not narrowing", flush=True)
                    q.put((m["created_at"], k, m, kind))
                    return
                narrowed = False
                recent = parse(m["merged_at"] or m["updated_at"] or m["created_at"]) >= six
                want_notes = (not (narrowed or narrow_all)) or recent
                if kind == "authored":
                    rec["diff"] = diffs_for(B, *k)
                    if not m["keys"]:
                        rec["commit_keys"] = commit_keys(B, m)
                if want_notes:
                    rec["notes"], rec["last_nonsys_note"] = notes_for(B, *k)
                    rec["review_detail"] = "fetched"
                else:
                    rec["review_detail"] = "not_fetched_6mo_narrowing"
                with wl:
                    fh.write(json.dumps(rec) + "\n"); fh.flush(); stats["done"] += 1
                    if stats["done"] % 200 == 0:
                        print(f"detail {stats['done']}/{len(tasks)} calls {B.n} r429 {B.r429} errors {B.errors}", flush=True)
            except RuntimeError as e:
                with wl: stats["fail"] += 1
                print("FAIL", k, e, flush=True)
                if B.stop: return
    ths = [threading.Thread(target=work) for _ in range(a.workers)]
    [t.start() for t in ths]; [t.join() for t in ths]
    B.save()
    json.dump({"tasks": len(tasks), "done": stats["done"], "failed": stats["fail"], "narrowed": stats["narrowed"],
               "narrow_after_calls": stats["narrow_after_calls"], "pull_calls": B.n, "stopped_at_budget": B.stop},
              open(os.path.join(a.out, "pull_summary.json"), "w"), indent=1)
    print("FINISHED", json.dumps({"tasks": len(tasks), "done": stats["done"], "failed": stats["fail"], "calls": B.n, "narrowed": stats["narrowed"]}), flush=True)


if __name__ == "__main__":
    main()
