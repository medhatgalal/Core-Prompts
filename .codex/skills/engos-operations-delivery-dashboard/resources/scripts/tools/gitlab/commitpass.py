#!/usr/bin/env python3
"""Commit-key pass (inbox 12, D14): read commit messages for authored MRs that already had a key from title/branch/description.
Calls per MR: 1 (MR commits list, first 100 commits) + 1 (squash commit, when a squash sha exists). GET only via tools/ro/ro.
Stores keys and source only. Resumable: commit_pass.jsonl. No model calls."""
import argparse, glob, json, os, sys, threading, queue
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pull, glapi

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default="data/extracts/gitlab"); ap.add_argument("--workers", type=int, default=8)
ap.add_argument("--budget", type=int, default=50000); ap.add_argument("--stop-at", type=int, default=49000)
a = ap.parse_args()
D = a.dir
B = pull.Budget(os.path.join(D, "calls.json"), a.budget, a.stop_at)
authored = {}
for f in glob.glob(os.path.join(D, "checkpoints", "authored__*.json")):
    for m in json.load(open(f))["items"]: authored[(m["project_id"], m["iid"])] = m
detail = {}
for l in open(os.path.join(D, "detail.jsonl")):
    try: d = json.loads(l); detail[(d["project_id"], d["iid"])] = d
    except ValueError: pass
path = os.path.join(D, "commit_pass.jsonl")
done = set()
if os.path.exists(path):
    for l in open(path):
        try: d = json.loads(l); done.add((d["project_id"], d["iid"]))
        except ValueError: pass
todo = [(m["created_at"], k, m) for k, m in authored.items() if m["keys"] and "commit_keys" not in detail.get(k, {}) and k not in done]
todo.sort(key=lambda t: t[0], reverse=True)
print(f"todo {len(todo)} (already done {len(done)}), calls so far {B.n}", flush=True)
q = queue.Queue(); [q.put(t) for t in todo]
lock = threading.Lock(); fh = open(path, "a"); st = {"n": 0, "fail": 0, "stopped": False}


def work():
    while True:
        try: _, k, m = q.get_nowait()
        except queue.Empty: return
        if B.n >= B.narrow_at:
            st["stopped"] = True; return
        try:
            keys = []
            if m["squash_commit_sha"]:
                s, h, d = B.get(f"/projects/{k[0]}/repository/commits/{m['squash_commit_sha']}")
                if s == 200 and d: keys += [[x, "commit"] for x in pull.KEY.findall(d.get("message") or "")]
                elif s != 404: raise RuntimeError(f"squash status {s}")
            s, h, d = B.get(f"/projects/{k[0]}/merge_requests/{k[1]}/commits?per_page=100")
            if s != 200: raise RuntimeError(f"commits status {s}")
            for c in d: keys += [[x, "commit"] for x in pull.KEY.findall(c.get("message") or "")]
            seen, u = set(), []
            for x in keys:
                if x[0] not in seen: seen.add(x[0]); u.append(x)
            with lock:
                fh.write(json.dumps({"project_id": k[0], "iid": k[1], "commit_keys": u, "more_commits": len(d) >= 100}) + "\n"); fh.flush()
                st["n"] += 1
                if st["n"] % 500 == 0: print(f"{st['n']}/{len(todo)} calls {B.n} errors {B.errors}", flush=True)
        except RuntimeError as e:
            with lock: st["fail"] += 1
            print("FAIL", k, e, flush=True)
            if B.stop: return


ths = [threading.Thread(target=work) for _ in range(a.workers)]
[t.start() for t in ths]; [t.join() for t in ths]
B.save()
print("FINISHED", json.dumps({"done_this_run": st["n"], "failed": st["fail"], "stopped_at_stop_point": st["stopped"], "calls": B.n}), flush=True)
