#!/usr/bin/env python3
"""GitLab incremental pull (AC36a). Plain shell, no agent, no model call (AC55). GET only, every call through tools/ro/.

  incremental.py --dir data/extracts/gitlab --asof <UTC> [--workers 8]

Pulls every roster change updated since the cursor (minus a 1 hour overlap): per roster person the merge_requests list with
updated_after for authored, approved-by and reviewer; then diffs, notes, commit messages only for those changes.
Staged in a temp folder; moved into place only when every call succeeded; then build.py rebuilds the CSVs (temp files, one swap);
cursor.json is written LAST. Exit codes: 0 ok, 1 failure, 2 sign-in / VPN / token problem. No call cap.
Writes data/extracts/gitlab/calls_incremental.json.
"""
import argparse, csv, datetime, json, os, subprocess, sys, shutil, threading, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glapi, pull

UTC = datetime.timezone.utc


class SignIn(Exception):
    pass


class Fail(Exception):
    pass


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(ts):
    return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def write_atomic(path, text):
    with open(path + ".tmp", "w") as f: f.write(text)
    os.replace(path + ".tmp", path)


class Client:
    """Same .get contract as pull.Budget so pull.diffs_for / notes_for can be reused."""
    def get(self, path):
        s, h, d = glapi.get(path)
        if s in (401,) or (s == 403 and "retry-after" not in h):
            raise SignIn(f"GitLab returned {s} for {path.split('?')[0]}: check VPN and GITLAB_TOKEN")
        return s, h, d


def commit_keys_all(c, m):
    out = []
    if m.get("squash_commit_sha"):
        s, h, d = c.get(f"/projects/{m['project_id']}/repository/commits/{m['squash_commit_sha']}")
        if s == 200 and d: out += [[x, "commit"] for x in pull.KEY.findall(d.get("message") or "")]
        elif s != 404: raise Fail(f"squash commit status {s} for {m['project_id']}!{m['iid']}")
    s, h, d = c.get(f"/projects/{m['project_id']}/merge_requests/{m['iid']}/commits?per_page=100")
    if s != 200: raise Fail(f"commits status {s} for {m['project_id']}!{m['iid']}")
    for cm in d: out += [[x, "commit"] for x in pull.KEY.findall(cm.get("message") or "")]
    seen, u = set(), []
    for x in out:
        if x[0] not in seen: seen.add(x[0]); u.append(x)
    return u, len(d) >= 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/extracts/gitlab"); ap.add_argument("--identity", default="data/identity.csv")
    ap.add_argument("--asof", required=True); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cursor", default="", help="override the stored cursor (tests only)")
    a = ap.parse_args()
    D, t0 = a.dir, datetime.datetime.now(UTC)
    asof = parse(a.asof)
    c = Client()
    # 1. sign-in check first: exit 2 with a plain message
    s, h, d = glapi.get("/user")
    if s != 200:
        print(f"GitLab returned {s} for /user: check VPN and GITLAB_TOKEN", file=sys.stderr)
        return 2
    # 2. cursor
    cur_path = os.path.join(D, "cursor.json")
    if a.cursor: cursor = a.cursor
    elif os.path.exists(cur_path): cursor = json.load(open(cur_path))["gitlab"]
    else: cursor = open(os.path.join(D, "as_of.txt")).read().strip()  # first run: the last full pull's as-of
    gap_days = (asof - parse(cursor)).days
    if gap_days > 365:
        print(f"gap of {gap_days} days is over 365: run the full pull instead (tools/gitlab/refresh.sh)", file=sys.stderr)
        return 1
    if gap_days > 30:
        print(f"large gap: {gap_days} days; this will take a while (about {gap_days * 600 // 390 + 1} minutes)", flush=True)
    start = iso(parse(cursor) - datetime.timedelta(hours=1))
    created_after = iso(asof - datetime.timedelta(days=365))
    tag = a.asof.replace(":", "")
    W = f"scope=all&updated_after={start}&updated_before={a.asof}&created_after={created_after}"
    ident = list(csv.DictReader(open(a.identity)))
    people = [r["gitlab_username"] for r in ident if r["gitlab_confidence"] in ("exact", "overridden")]
    stage = os.path.join(D, f".incr_tmp_{os.getpid()}")
    shutil.rmtree(stage, ignore_errors=True); os.makedirs(stage)
    try:
        # 3. lists, in parallel
        def list_all(q):
            items, page = [], 1
            while True:
                s, h, d = c.get(f"/merge_requests?{q}&{W}&per_page=100&page={page}")
                if s != 200: raise Fail(f"list status {s} for {q.split('=')[0]}")
                items += [pull.slim(m) for m in d]
                if not h.get("x-next-page"): return items
                page = int(h["x-next-page"])
        jobs = []
        for u in people:
            jobs += [("authored", f"author_username={u}"), ("approved", f"approved_by_usernames[]={u}&not[author_username]={u}"),
                     ("reviewer", f"reviewer_username={u}&not[author_username]={u}")]
        authored, others = {}, {}
        with cf.ThreadPoolExecutor(a.workers) as ex:
            for (kind, q), items in zip(jobs, ex.map(lambda j: list_all(j[1]), jobs)):
                for m in items:
                    k = (m["project_id"], m["iid"])
                    if kind == "authored": authored[k] = m
                    else: others[k] = m
        others = {k: m for k, m in others.items() if k not in authored}
        # 4. per-change detail, notes, commits
        det_lines, cp_lines = [], []
        lock = threading.Lock()
        def work(item):
            k, m, kind = item
            rec = {"project_id": k[0], "iid": k[1], "kind": kind}
            if kind == "authored":
                rec["diff"] = pull.diffs_for(c, *k)
                keys, more = commit_keys_all(c, m)
                cpl = {"project_id": k[0], "iid": k[1], "commit_keys": keys, "more_commits": more}
            else:
                cpl = None
            rec["notes"], rec["last_nonsys_note"] = pull.notes_for(c, *k)
            rec["review_detail"] = "fetched"
            with lock:
                det_lines.append(json.dumps(rec))
                if cpl: cp_lines.append(json.dumps(cpl))
        todo = [(k, m, "authored") for k, m in authored.items()] + [(k, m, "other") for k, m in others.items()]
        with cf.ThreadPoolExecutor(a.workers) as ex:
            list(ex.map(work, todo))
        # 5. stage files, then move them into place together
        ck = os.path.join(D, "checkpoints"); os.makedirs(ck, exist_ok=True)
        files = {
            os.path.join(stage, f"authored__incr-{tag}__p0001.json"): os.path.join(ck, f"authored__incr-{tag}__p0001.json"),
            os.path.join(stage, f"approved__incr-{tag}__p0001.json"): os.path.join(ck, f"approved__incr-{tag}__p0001.json"),
            os.path.join(stage, f"detail_incr_{tag}.jsonl"): os.path.join(D, f"detail_incr_{tag}.jsonl"),
            os.path.join(stage, f"commit_pass_incr_{tag}.jsonl"): os.path.join(D, f"commit_pass_incr_{tag}.jsonl"),
        }
        names = list(files)
        dsts = list(files.values())

        def merged_items(dst, new):
            """A rerun with the same as-of must not lose the earlier run's rows: merge into the file already there, new wins."""
            cur = {}
            if os.path.exists(dst):
                for m in json.load(open(dst))["items"]: cur[(m["project_id"], m["iid"])] = m
            cur.update(new)
            return [cur[k] for k in sorted(cur)]

        def merged_lines(dst, new_lines):
            cur = {}
            if os.path.exists(dst):
                for l in open(dst):
                    if l.strip(): d = json.loads(l); cur[(d["project_id"], d["iid"])] = l.rstrip("\n")
            for l in new_lines: d = json.loads(l); cur[(d["project_id"], d["iid"])] = l
            return "".join(cur[k] + "\n" for k in sorted(cur))
        json.dump({"items": merged_items(dsts[0], authored), "x_total": None, "next": ""}, open(names[0], "w"))
        json.dump({"items": merged_items(dsts[1], others), "x_total": None, "next": ""}, open(names[1], "w"))
        open(names[2], "w").write(merged_lines(dsts[2], det_lines))
        open(names[3], "w").write(merged_lines(dsts[3], cp_lines))
        for src, dst in files.items(): os.replace(src, dst)
    except SignIn as e:
        print(str(e), file=sys.stderr); return 2
    except Exception as e:
        print(f"GitLab incremental pull failed, nothing was written: {e}", file=sys.stderr); return 1
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    # 6. rebuild the CSVs (build.py writes temp files and swaps them together)
    r = subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build.py"), "--dir", D], capture_output=True, text=True)
    if r.returncode != 0:
        print("GitLab incremental merge failed in build.py (CSVs unchanged, cursor not moved): " + r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "build.py failed", file=sys.stderr)
        return 1
    # 7. cursor last, then the call log
    write_atomic(os.path.join(D, "as_of.txt"), a.asof + "\n")  # keep the folder's as-of equal to the cursor
    write_atomic(cur_path, json.dumps({"gitlab": a.asof, "updated": iso(datetime.datetime.now(UTC)), "previous": cursor}, indent=1))
    t1 = datetime.datetime.now(UTC)
    summary = {"source": "gitlab", "asof": a.asof, "cursor_before": cursor, "window_start": start, "calls": glapi.STATS["calls"],
               "retries": glapi.STATS["retries"], "retries_429": glapi.STATS["retries_429"], "retries_403_rate": glapi.STATS["retries_403_rate"],
               "final_errors": glapi.STATS["final_errors"], "authored_updated": len(authored), "others_updated": len(others),
               "seconds": round((t1 - t0).total_seconds(), 1), "finished": iso(t1)}
    write_atomic(os.path.join(D, "calls_incremental.json"), json.dumps(summary, indent=1))
    print(f"gitlab incremental {a.asof}: {len(authored)} authored + {len(others)} reviewed updated ({glapi.STATS['calls']} calls, {summary['seconds']} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
