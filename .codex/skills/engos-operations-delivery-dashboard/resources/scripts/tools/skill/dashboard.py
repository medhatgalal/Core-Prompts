#!/usr/bin/env python3
#!/usr/bin/env python3
"""/engos-operations-delivery-dashboard command dispatcher. No model call anywhere in this file (AC55): `ask`, `insights rebuild`, and `canvas rebuild`
are performed by the agent that reads skill/SKILL.md; the script only prints their contract or hands over the cells to read.
Every write: --dry-run prints the PLAN and writes nothing; otherwise PLAN is shown and nothing happens until "apply" (or --apply/--yes).
Every applied write appends one line to data/ledger.csv: when, actor, command, person, field, before, after, reason."""
import argparse, csv, datetime as dt, json, os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "sheet"))
CFG_PATH = os.environ.get("DASHBOARD_CONFIG", "data/config.json")
LEDGER = os.environ.get("DASHBOARD_LEDGER", "data/ledger.csv")
PY = sys.executable


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_cfg():
    if not os.path.exists(CFG_PATH):
        sys.exit("No project config (data/config.json). Run the build first; I will not guess.")
    return json.load(open(CFG_PATH))


def sid_for(cfg, target):
    return {"real": cfg.get("sheet_id"), "scratch": cfg.get("scratch_sheet_id")}.get(target, target)


def is_real(cfg, target):
    return target == "real" or (bool(cfg.get("sheet_id")) and target == cfg.get("sheet_id"))


def hash_path(cfg, target, override=""):
    """The real Sheet's baseline is data/hashes.json; any other target (scratch, a fixture, another id) gets a scratch-only file."""
    real = is_real(cfg, target)
    if override:
        if not real and os.path.abspath(override) == os.path.abspath("data/hashes.json"):
            sys.exit("refusing to write the real Sheet's hash baseline (data/hashes.json) for a non-real target")
        return override
    return "data/hashes.json" if real else "data/hashes-scratch.json"


AS_USER = False


def need_actor(args=None):
    """D103: every ledger line reads '<account> via <role>'. A write without DASHBOARD_AGENT is refused unless --as-user is given (then 'via user')."""
    global AS_USER
    AS_USER = bool(getattr(args, "as_user", False))
    if not os.environ.get("DASHBOARD_AGENT") and not AS_USER:
        sys.exit("refused: DASHBOARD_AGENT is not set, so the ledger line would carry only the account. Set DASHBOARD_AGENT=<role> (for example sheet), or pass --as-user to act as the user ('via user').")


def actor(cfg, scratch=False):
    a = cfg.get("owner_account") or cfg.get("drive_account", "")
    ag = os.environ.get("DASHBOARD_AGENT", "") or ("user" if AS_USER else "")
    return a + (f" via {ag}" if ag else "")      # exactly '<account> via <role>'; the scratch marker is a '[scratch] ' prefix on the reason (ledger())


def ledger(cfg, command, person="", field="", before="", after="", reason="", scratch=False):
    if not os.environ.get("DASHBOARD_AGENT") and not AS_USER:
        sys.exit("refused: no ledger line without DASHBOARD_AGENT or --as-user (D103)")
    new = not os.path.exists(LEDGER)
    with open(LEDGER, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["when", "actor", "command", "person", "field", "before", "after", "reason"])
        w.writerow([now(), actor(cfg, scratch), command, person, field, before, after, ("[scratch] " + reason) if scratch else reason])


def confirm(args, plan):
    print("PLAN:")
    for l in plan:
        print("  " + l)
    if getattr(args, "dry_run", False):
        print("(dry run: nothing written)")
        return False
    need_actor(args)       # a write follows: refuse without DASHBOARD_AGENT or --as-user (D103)
    if getattr(args, "apply", False) or getattr(args, "yes", False):
        return True
    return input('Type "apply" to write: ').strip().lower() == "apply"


def out(args, obj, text=None):
    if getattr(args, "json", False):
        print(json.dumps(obj, indent=1, default=str))
    else:
        print(text if text is not None else json.dumps(obj, indent=1, default=str))


def need_reason(args):
    if not getattr(args, "reason", None):
        sys.exit("--reason is required for this command")


def sh(cmd, check=True):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode:
        sys.exit(f"command failed: {' '.join(cmd[:4])}...\n{p.stdout[-800:]}{p.stderr[-800:]}")
    return p


# ------------------------------------------------------------------ commands
def cmd_help(args, cfg=None):
    print(__doc__.split("\n\n")[0] if False else HELP)


HELP = """/engos-operations-delivery-dashboard <noun> <verb> [args]   (no command = status)
  status                         one screen: as-of and age, row counts, alerts, sign-ins, last refresh
  doctor                         read-only health check
  refresh [--from-saved] [--dry-run] [--yes] [--target real|scratch]   pull, recompute, rewrite tabs and charts, re-baseline hashes
  insights rebuild               agent task (AI text); see skill
  ask "<question>"               agent task (AI answer under the answer contract); see skill
  roster list|show|add|remove|set-team|set-group|set-manager|set-title|set-note|set-identity|sync|ignore|unignore|diff|history|import|export
  team list|show|add|rename|move|remove
  threshold list | set <name> <value> --reason
  viewer list | add <email> | remove <email> | set-role <email> <role>   (--reason required; no notification mail)
  metric list | show <name>      definitions from Data_Dictionary
  alert list | show              current alerts in priority order
  chart list | rebuild           V1 to V13
  canvas rebuild                 agent task (the Sheet's own AI); see skill
  check                          run tools/checks (independent recompute) and print differences
Examples:
  /engos-operations-delivery-dashboard status
  /engos-operations-delivery-dashboard roster add "Pat Lee" --group "ALPHA GROUP" --team "Red Team" --reason "joined 2026-11-10"
  /engos-operations-delivery-dashboard threshold set t_wip_per_person 4 --reason "team agreed"
  /engos-operations-delivery-dashboard refresh --dry-run"""


def sheet_read(cfg, rng, target="real"):
    from sheetlib import values_get
    return values_get(sid_for(cfg, target), rng)


def cmd_status(args, cfg):
    from sheetlib import sheets, get_meta
    sid = sid_for(cfg, args.target)
    last = {}
    lb = os.path.join(cfg["paths"]["derived"], "last_build.json")
    if os.path.exists(lb):
        last = json.load(open(lb))
    asof = open(os.path.join(cfg["paths"]["jira_dir"], "as_of.txt")).read().strip() if os.path.exists(os.path.join(cfg["paths"]["jira_dir"], "as_of.txt")) else ""
    age = ""
    if asof:
        age = round((dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(asof.replace("Z", "+00:00"))).total_seconds() / 86400, 2)
    alerts = []
    try:
        alerts = [[r[0], r[1]] for r in sheet_read(cfg, "Dashboard!A5:B10", args.target)]
    except Exception as e:
        alerts = [["alerts unavailable", str(e)[:80]]]
    who = ""
    try:
        who = sh(["gws", "drive", "about", "get", "--params", '{"fields":"user"}']).stdout
        who = json.loads(who[who.index("{"):])["user"]["emailAddress"]
    except Exception:
        who = "gws not signed in"
    last_refresh = ""
    if os.path.exists(LEDGER):
        rows = [r for r in csv.reader(open(LEDGER)) if len(r) > 2 and r[2].startswith("refresh")]
        last_refresh = ",".join(rows[-1][:3]) if rows else "none"
    o = {"as_of": asof, "as_of_age_days": age, "sheet_id": sid, "row_counts": (last.get("meta") or {}).get("counts"), "alerts": alerts,
         "gws_account": who, "last_refresh": last_refresh, "built_at": last.get("built_at")}
    out(args, o, "\n".join([f"as-of {asof} ({age} days old)", f"sheet {sid}", f"rows {o['row_counts']}", "alerts:"] + [f"  {a[0]}: {a[1]}" for a in alerts] +
                           [f"gws signed in as {who}", f"last refresh: {last_refresh}", f"last build: {o['built_at']}"]))


def cmd_doctor(args, cfg):
    problems, notes = [], []
    sid = sid_for(cfg, args.target)
    for name, path in (("roster", cfg["paths"]["roster"]), ("identity", cfg["paths"]["identity"]), ("thresholds", cfg["paths"]["thresholds"])):
        if not os.path.exists(path):
            problems.append(f"missing {name} file {path}")
    ro = os.path.join("tools", "ro", "ro")
    notes.append("GET-only wrapper present" if os.path.exists(ro) else "GET-only wrapper tools/ro/ro missing")
    # roster problems: no identity, duplicates (zero changes in 12 months is reported from the extract when it exists)
    try:
        ros = list(csv.DictReader(open(cfg["paths"]["roster"])))
        names = [r["name"] for r in ros]
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            problems.append(f"duplicate roster names: {sorted(dup)}")
        ident = {r["person"]: r for r in csv.DictReader(open(cfg["paths"]["identity"]))}
        noid = [n for n in names if n not in ident]
        if noid:
            problems.append(f"{len(noid)} roster people with no identity row")
        gl = os.path.join(cfg["paths"]["gitlab_dir"], "code_changes.csv")
        if os.path.exists(gl):
            authors = {r["author"].lower() for r in csv.DictReader(open(gl))}
            zero = [n for n in names if ident.get(n, {}).get("gitlab_username", "").lower() not in authors and ident.get(n, {}).get("gitlab_confidence") in ("exact", "overridden")]
            if zero:
                notes.append(f"{len(zero)} roster people with an exact GitLab identity and zero changes in the extract")
    except Exception as e:
        problems.append(f"roster check failed: {e}")
    # sharing
    try:
        p = sh(["gws", "drive", "permissions", "list", "--params", json.dumps({"fileId": sid, "fields": "permissions(role,emailAddress)"})]).stdout
        perms = json.loads(p[p.index("{"):])["permissions"]
        notes.append("sharing: " + ", ".join(f"{x['emailAddress']}:{x['role']}" for x in perms))
        if any(x["role"] in ("fileOrganizer", "organizer") for x in perms):          # v1.43e rev 2: leaders are writers (editors) by ruling; an organizer role is still a problem
            problems.append("someone other than the owner has organizer access")
    except Exception as e:
        problems.append(f"sharing check failed: {str(e)[:100]}")
    # thresholds in Sheet vs file
    try:
        cur = {r[0]: r[1] for r in sheet_read(cfg, "Thresholds!A:B", args.target) if len(r) > 1}
        miss = [r["name"] for r in csv.DictReader(open(cfg["paths"]["thresholds"])) if r["name"] not in cur]
        if miss:
            problems.append(f"thresholds missing in the Sheet: {miss}")
    except Exception as e:
        problems.append(f"threshold read failed: {str(e)[:80]}")
    # hashes
    hp = hash_path(cfg, args.target)
    if os.path.exists(hp):
        r = sh([PY, "tools/sheet/hashes.py", "verify", "--target", args.target, "--file", hp], check=False)
        (notes if r.returncode == 0 else problems).append(r.stdout.strip())
    else:
        notes.append("no hash baseline yet (data/hashes.json); refresh creates one")
    try:
        asof = open(os.path.join(cfg["paths"]["jira_dir"], "as_of.txt")).read().strip()
        thr = {r["name"]: float(r["value"]) for r in csv.DictReader(open(cfg["paths"]["thresholds"]))}
        age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(asof.replace("Z", "+00:00"))).total_seconds() / 86400
        if age > thr.get("t_freshness_days", 7):
            problems.append(f"data is stale: as-of {asof} is {age:.1f} days old")
    except FileNotFoundError as e:
        problems.append(f"no saved extracts here ({os.path.basename(str(e.filename))} missing): run the pull or restore data/extracts")
    except Exception as e:
        problems.append(f"as-of check failed: {str(e)[:100]}")
    o = {"problems": problems, "notes": notes, "ok": not problems}
    out(args, o, "\n".join(["PROBLEMS:"] + (["  " + p for p in problems] or ["  none"]) + ["NOTES:"] + ["  " + n for n in notes]))
    sys.exit(1 if problems else 0)


LOCK = "data/refresh.lock"
INC_FILE = "data/last_incremental.json"
INC_CMDS = (("jira", "bash tools/jira/refresh.sh --incremental --asof {asof}"),
            ("gitlab", "tools/gitlab/refresh.sh --incremental --asof {asof}"),
            ("github", "python3 -I tools/github/pull.py --incremental --asof {asof}"))
INC_CMDS_COPY = (("jira", "JIRA_EXTRACT_DIR={d}/jira bash tools/jira/refresh.sh --incremental --asof {{asof}}"),
                 ("gitlab", "python3 -I tools/gitlab/incremental.py --dir {d}/gitlab --asof {{asof}}"),
                 ("github", "python3 -I tools/github/pull.py --incremental --data-dir {d}/github --asof {{asof}}"))


def take_lock():
    """data/refresh.lock holds pid and start time. Returns None when taken, or a message when another run holds it (exit 3).
    A lock whose pid is gone is a crashed run: cleared and reported."""
    for _ in range(2):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                pid, since = open(LOCK).read().split()[:2]
                os.kill(int(pid), 0)
                return f"refresh already running since {since}"
            except (ProcessLookupError, ValueError, IndexError):
                print("cleared a stale refresh.lock (its process is gone)", file=sys.stderr)
                try: os.remove(LOCK)
                except FileNotFoundError: pass
                continue
            except PermissionError:
                return "refresh already running (lock held by another user's process)"
        with os.fdopen(fd, "w") as f:
            f.write(f"{os.getpid()} {now()}\n")
        return None
    return "could not take data/refresh.lock"


def cmd_incremental(args, cfg):
    """AC36a: one as-of; jira, gitlab, github incremental pulls (roster excluded); recompute; rewrite the Sheet in place; one summary line.
    Exit 0 ok, 1 a source failed (its cursor kept, Sheet not rewritten), 2 sign-in / VPN / network, 3 another run holds the lock."""
    scratch = not is_real(cfg, args.target)
    hp = hash_path(cfg, args.target, args.hash_file)
    asof = getattr(args, "asof", "") or now()      # --asof only for tests (same window twice)
    if not getattr(args, "dry_run", False):
        need_actor(args)       # D103: refuse before anything is written
    dd = getattr(args, "data_dir", "") or ""
    cmds, inc_file, cfg_file = INC_CMDS, INC_FILE, args.config_file
    if dd:      # tests: pull into a COPY (dd/jira, dd/gitlab, dd/github); the build reads the copy through a temp config (scratch targets only)
        if is_real(cfg, args.target):
            print("--data-dir is for tests: use it with --target scratch", file=sys.stderr)
            return 1
        dd = os.path.abspath(dd)
        cmds = tuple((n, c.format(d=dd)) for n, c in INC_CMDS_COPY)
        inc_file = os.path.join(dd, "last_incremental.json")
        c2 = json.loads(json.dumps(cfg))
        c2["paths"].update({"jira_dir": f"{dd}/jira", "gitlab_dir": f"{dd}/gitlab", "github_dir": f"{dd}/github", "derived": f"{dd}/derived", "incremental_log": inc_file})
        os.makedirs(f"{dd}/derived", exist_ok=True)
        cfg_file = os.path.join(dd, "config.json")
        json.dump(c2, open(cfg_file, "w"), indent=1)
    plan = [f"incremental as-of {asof}: " + "; ".join(c.format(asof=asof) for _, c in cmds),
            f"rewrite the Sheet in place on {sid_for(cfg, args.target)} ({args.target}); keep Insights and the Canvas", f"re-baseline hashes in {hp}"]
    if getattr(args, "dry_run", False):
        print("PLAN:\n  " + "\n  ".join(plan) + "\n(dry run: nothing written)", file=sys.stderr)
        return 0
    if not (getattr(args, "yes", False) or getattr(args, "apply", False)):
        print("PLAN:\n  " + "\n  ".join(plan), file=sys.stderr)
        if input('Type "apply" to write: ').strip().lower() != "apply":
            return 0
    who = "scheduled" if getattr(args, "scheduled", False) else "manual"
    msg = take_lock()
    if msg:
        print(msg, file=sys.stderr)
        return 3
    try:
        parts, rc_all, summ = [], [], {}
        for src, c in cmds:
            r = subprocess.run(c.format(asof=asof), shell=True, capture_output=True, text=True)
            lines = [l for l in r.stdout.splitlines() if l.strip()]
            line = lines[-1] if lines else ""
            m = re.search(r"(\d+) calls", line)
            summ[src] = {"rc": r.returncode, "line": line, "calls": int(m.group(1)) if m else 0}
            rc_all.append(r.returncode)
            if r.returncode:
                err = (r.stderr.strip().splitlines() or ["no message"])[-1]
                print(f"{src} incremental failed (exit {r.returncode}): {err}", file=sys.stderr)
                parts.append(f"{src} FAILED exit {r.returncode}")
            else:
                parts.append(re.sub(rf"^{src} incremental \S+: ", f"{src} ", line))
        if any(rc_all):
            code = 2 if 2 in rc_all else 1
            hint = "sign-in, VPN or network missing" if code == 2 else "a source failed; its cursor is kept; rerun, or `refresh --full` for that source"
            summary = f"incremental {asof} {who}: " + "; ".join(parts) + f"; Sheet NOT updated ({hint})"
            print(summary)
            ledger(cfg, "refresh --incremental", after=f"exit {code}", reason=summary[:400], scratch=scratch)
            return code
        # one as-of for the run: the extractors keep their own cursors; the build reads each source's as_of.txt
        for d in ((f"{dd}/jira", f"{dd}/gitlab") if dd else (cfg["paths"]["jira_dir"], cfg["paths"]["gitlab_dir"])):
            open(os.path.join(d, "as_of.txt"), "w").write(asof + "\n")
        json.dump({"asof": asof, "run": who, "sources": summ}, open(inc_file, "w"), indent=1)
        if getattr(args, "no_build", False):      # tests of the pulls only: no Sheet write
            summary = f"incremental {asof} {who}: " + "; ".join(parts) + "; Sheet not written (--no-build)"
            print(summary)
            return 0
        b = subprocess.run([PY, "tools/sheet/build.py", "--target", args.target] + (["--config", cfg_file] if cfg_file else []), capture_output=True, text=True)
        if b.returncode:
            print("build failed: " + (b.stderr.strip().splitlines() or ["no message"])[-1], file=sys.stderr)
            summary = f"incremental {asof} {who}: " + "; ".join(parts) + "; Sheet build FAILED"
            print(summary)
            ledger(cfg, "refresh --incremental", after="exit 1", reason=summary[:400], scratch=scratch)
            return 1
        if subprocess.run([PY, "tools/sheet/hashes.py", "snapshot", "--target", args.target, "--file", hp], capture_output=True).returncode:
            print("hash snapshot failed", file=sys.stderr)
            return 1
        summary = f"incremental {asof} {who}: " + "; ".join(parts) + "; Sheet updated in place; hashes re-baselined"
        print(summary)
        ledger(cfg, "refresh --incremental", after=sid_for(cfg, args.target), reason=summary[:400], scratch=scratch)
        return 0
    finally:
        try: os.remove(LOCK)
        except FileNotFoundError: pass


def cmd_refresh(args, cfg):
    """refresh: pull (configured commands), derive, rewrite tabs, charts, canvas_source, hashes. --from-saved skips the pull."""
    if getattr(args, "incremental", False):
        sys.exit(cmd_incremental(args, cfg))
    scratch = not is_real(cfg, args.target)
    hp = hash_path(cfg, args.target, args.hash_file)
    if not args.from_saved and os.path.exists(INC_FILE):
        os.remove(INC_FILE)      # a full pull replaces the incremental record shown in Run_Log
    pulls = [] if args.from_saved else cfg.get("refresh", {}).get("pull_commands", [])
    plan = []
    if args.from_saved:
        plan.append("recompute from the saved CSVs and the stored as-of timestamp (no pull)")
    elif pulls:
        plan += [f"pull: {c}" for c in pulls]
    else:
        plan.append("pull: none configured (config refresh.pull_commands is empty); the build runs on the saved CSVs")
    plan += [f"rewrite data tabs, Metrics, Individual, Dashboard charts, canvas_source on {sid_for(cfg, args.target)} ({args.target})",
             "keep Insights and the Canvas untouched", f"re-baseline hashes in {hp}"]
    if not confirm(args, plan):
        return
    for c in pulls:
        print("pull:", c)
        r = subprocess.run(c, shell=True)
        if r.returncode:
            sys.exit(f"pull failed: {c}")
    b = [PY, "tools/sheet/build.py", "--target", args.target]
    if args.config_file:
        b += ["--config", args.config_file]
    if subprocess.run(b).returncode:
        ledger(cfg, "refresh", reason="FAILED during build", scratch=scratch)
        sys.exit("build failed")
    if subprocess.run([PY, "tools/sheet/hashes.py", "snapshot", "--target", args.target, "--file", hp]).returncode:
        sys.exit("hash snapshot failed")
    ledger(cfg, "refresh" + (" --from-saved" if args.from_saved else ""), after=sid_for(cfg, args.target), reason=args.reason or "refresh", scratch=scratch)
    print("refresh done")


def cmd_threshold(args, cfg):
    sid = sid_for(cfg, args.target)
    rows = sheet_read(cfg, "Thresholds!A:D", args.target)
    if args.verb == "list":
        out(args, [dict(zip(rows[0], r)) for r in rows[1:]], "\n".join("\t".join(r) for r in rows))
        return
    need_reason(args)
    names = [r[0] for r in rows]
    if args.name not in names:
        sys.exit(f"unknown threshold {args.name}; known: {names[1:]}")
    i = names.index(args.name)
    before = rows[i][1]
    if not confirm(args, [f"Thresholds!B{i+1} ({args.name}): {before} -> {args.value}"]):
        return
    from sheetlib import values_update
    values_update(sid, f"Thresholds!B{i+1}", [[float(args.value) if "." in args.value else int(args.value)]])
    ledger(cfg, "threshold set", field=args.name, before=before, after=args.value, reason=args.reason, scratch=args.target == "scratch")
    print("threshold changed; formulas recalculate in the Sheet")


def cmd_viewer(args, cfg):
    sid = sid_for(cfg, args.target)
    p = sh(["gws", "drive", "permissions", "list", "--params", json.dumps({"fileId": sid, "fields": "permissions(id,role,emailAddress,type)"})]).stdout
    perms = json.loads(p[p.index("{"):])["permissions"]
    if args.verb == "list":
        out(args, perms, "\n".join(f"{x.get('emailAddress','')}\t{x['role']}" for x in perms))
        return
    need_reason(args)
    cur = {x.get("emailAddress", "").lower(): x for x in perms}
    e = args.email.lower()
    if args.verb == "add":
        role = args.role or "writer"          # v1.43e rev 2 (user ruling 15 Nov 2026): leaders are editors; every tab is owner-locked except the open ranges
        if e in cur:
            sys.exit(f"{e} already has {cur[e]['role']}")
        if not confirm(args, [f"add {e} as {role} (no notification mail)"]):
            return
        sh(["gws", "drive", "permissions", "create", "--params", json.dumps({"fileId": sid, "sendNotificationEmail": False, "supportsAllDrives": True}),
            "--json", json.dumps({"type": "user", "role": role, "emailAddress": args.email})])
        ledger(cfg, "viewer add", person=e, field="role", before="", after=role, reason=args.reason, scratch=args.target == "scratch")
    elif args.verb == "remove":
        if e not in cur or cur[e]["role"] == "owner":
            sys.exit("not a removable viewer")
        if not confirm(args, [f"remove {e} ({cur[e]['role']})"]):
            return
        sh(["gws", "drive", "permissions", "delete", "--params", json.dumps({"fileId": sid, "permissionId": cur[e]["id"], "supportsAllDrives": True})])
        ledger(cfg, "viewer remove", person=e, field="role", before=cur[e]["role"], after="", reason=args.reason, scratch=args.target == "scratch")
    elif args.verb == "set-role":
        if e not in cur or cur[e]["role"] == "owner":
            sys.exit("not a changeable viewer")
        if not confirm(args, [f"{e}: {cur[e]['role']} -> {args.role}"]):
            return
        sh(["gws", "drive", "permissions", "update", "--params", json.dumps({"fileId": sid, "permissionId": cur[e]["id"], "supportsAllDrives": True}),
            "--json", json.dumps({"role": args.role})])
        ledger(cfg, "viewer set-role", person=e, field="role", before=cur[e]["role"], after=args.role, reason=args.reason, scratch=args.target == "scratch")


def cmd_metric(args, cfg):
    rows = sheet_read(cfg, "Data_Dictionary!A:F", args.target)
    hdr, body = rows[0], rows[1:]
    if args.verb == "list":
        out(args, [dict(zip(hdr, r)) for r in body], "\n".join(f"{r[0]}\t{r[1]}" for r in body))
    else:
        hit = [dict(zip(hdr, r)) for r in body if len(r) > 1 and r[1] == args.name]
        out(args, hit, "\n".join(json.dumps(h) for h in hit) or "no such metric or column")


def cmd_alert(args, cfg):
    rows = sheet_read(cfg, "Dashboard!A5:E10", args.target)
    o = [{"priority": i + 1, "alert": r[0], "count": r[1], "unit": r[2] if len(r) > 2 else "", "status": r[3] if len(r) > 3 else ""} for i, r in enumerate(rows)]
    if args.verb == "show":
        keys = sheet_read(cfg, "Metrics!A1:D1", args.target)
        o.append({"failing_lists": "Metrics named ranges m_noowner_list (keys), m_aging_wip, m_open_changes; per-Team counts in m_levels"})
    out(args, o, "\n".join(f"{x.get('priority','')}. {x.get('alert','')}: {x.get('count','')} {x.get('unit','')} {x.get('status','')}" for x in o if 'alert' in x))


def cmd_chart(args, cfg):
    if args.verb == "list":
        out(args, ["V1 throughput", "V2 created vs done", "V3 cumulative flow", "V4 cycle time", "V5 aging WIP", "V6 WIP by team", "V7 backlog age", "V8 no owner",
                   "V9a merged per week", "V9b first review", "V10 review load", "V11 hygiene", "V12 alignment", "V13 open changes"])
        return
    plan = [f"delete and rebuild all charts on the Dashboard of {sid_for(cfg, args.target)}"]
    if confirm(args, plan):
        sh([PY, "tools/sheet/build.py", "--target", args.target, "--only", "charts"])
        ledger(cfg, "chart rebuild", reason=args.reason or "chart rebuild", scratch=args.target == "scratch")


def cmd_check(args, cfg):
    outp = []
    for f in sorted(os.listdir("tools/checks")):
        if f.startswith("gatec_") and f.endswith(".py") and f != "gatec_lib.py":
            r = sh([PY, os.path.join("tools/checks", f)], check=False)
            outp.append({"script": f, "exit": r.returncode, "tail": (r.stdout + r.stderr)[-600:]})
    out(args, outp, "\n".join(f"{o['script']} exit {o['exit']}\n{o['tail']}" for o in outp))


def read_roster():
    return list(csv.DictReader(open(load_cfg()["paths"]["roster"])))


def cmd_team(args, cfg):
    ros = read_roster()
    teams = {}
    for r in ros:
        if r["team"]:
            teams.setdefault((r["group"], r["team"]), []).append(r["chart_name"])
    if args.verb == "list":
        out(args, [{"group": g, "team": t, "members": len(m)} for (g, t), m in sorted(teams.items())], "\n".join(f"{g}\t{t}\t{len(m)}" for (g, t), m in sorted(teams.items())))
        return
    if args.verb == "show":
        o = [{"group": g, "team": t, "members": m} for (g, t), m in teams.items() if t == args.team]
        out(args, o)
        return
    need_reason(args)
    members = [r["chart_name"] for r in ros if r["team"] == args.team]
    roster = os.path.join("tools", "roster", "roster")
    cmds = []
    if args.verb == "rename":
        cmds = [[roster, "set-team", m, args.to, "--reason", args.reason] for m in members]
    elif args.verb == "move":
        cmds = [[roster, "set-group", m, args.to, "--reason", args.reason] for m in members]
    elif args.verb == "remove":
        cmds = [[roster, "set-team", m, "", "--reason", args.reason] for m in members]
    elif args.verb == "add":
        cmds = [[roster, "set-team", m, args.team, "--reason", args.reason] for m in (args.members or "").split(",") if m]
    plan = [" ".join(c) for c in cmds] or ["nothing to do"]
    if not cmds or not confirm(args, plan):
        return
    for c in cmds:
        sh(c + ["--apply"])
    print("team change applied through the roster commands (ledger lines written there)")


def cmd_roster(args, cfg):
    sys.exit(subprocess.run([os.path.join("tools", "roster", "roster")] + args.rest).returncode)


def cmd_agent(args, cfg):
    msgs = {
        "ask": "`ask` is answered by the agent reading the Sheet through gws under the answer contract (README tab). This script makes no model call. See skill/SKILL.md 'ask'.",
        "insights": "`insights rebuild` is done by the Insights author agent from the current Metrics cells, then the number-match check (AC45). See skill/SKILL.md.",
        "canvas": "`canvas rebuild` needs the user's Google sign-in and the Sheet's own AI. See skill/SKILL.md and tools/canvas/NOTES.md.",
    }
    print(msgs[args.cmd])
    if args.cmd == "ask":
        print("Contract: cite the cell; quote the as-of timestamp; state the definition; decline to rank people or compare individuals; say 'not in the Sheet' for estimates.")
        print("Question:", args.question)


def parser():
    ap = argparse.ArgumentParser(prog="dashboard", description="Automation dashboard commands. No command = status.")
    ap.add_argument("--target", default="real", help="real (default), scratch, or a spreadsheet id")
    ap.add_argument("--json", action="store_true")
    sp = ap.add_subparsers(dest="cmd")

    def common(p, write=False):
        p.add_argument("--json", action="store_true")
        p.add_argument("--as-user", action="store_true", help="act as the user: the ledger line reads 'via user' (without it, DASHBOARD_AGENT must be set for a write)")
        p.add_argument("--target", default=argparse.SUPPRESS)
        if write:
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--apply", action="store_true")
            p.add_argument("--reason")
    sp.add_parser("help")
    p = sp.add_parser("status"); common(p)
    p = sp.add_parser("doctor"); common(p)
    p = sp.add_parser("refresh"); common(p, True)
    p.add_argument("--from-saved", action="store_true"); p.add_argument("--yes", action="store_true")
    p.add_argument("--incremental", action="store_true"); p.add_argument("--scheduled", action="store_true"); p.add_argument("--data-dir", default=""); p.add_argument("--asof", default=""); p.add_argument("--no-build", action="store_true")
    p.add_argument("--config-file", default=""); p.add_argument("--hash-file", default="")
    p = sp.add_parser("threshold"); common(p, True); p.add_argument("verb", choices=["list", "set"]); p.add_argument("name", nargs="?"); p.add_argument("value", nargs="?")
    p = sp.add_parser("viewer"); common(p, True); p.add_argument("verb", choices=["list", "add", "remove", "set-role"]); p.add_argument("email", nargs="?"); p.add_argument("role", nargs="?")
    p.add_argument("--role", dest="role2")
    p = sp.add_parser("metric"); common(p); p.add_argument("verb", choices=["list", "show"]); p.add_argument("name", nargs="?")
    p = sp.add_parser("alert"); common(p); p.add_argument("verb", choices=["list", "show"])
    p = sp.add_parser("chart"); common(p, True); p.add_argument("verb", choices=["list", "rebuild"])
    p = sp.add_parser("check"); common(p)
    p = sp.add_parser("team"); common(p, True); p.add_argument("verb", choices=["list", "show", "add", "rename", "move", "remove"]); p.add_argument("team", nargs="?"); p.add_argument("--to"); p.add_argument("--members")
    p = sp.add_parser("roster"); p.add_argument("rest", nargs=argparse.REMAINDER)
    p = sp.add_parser("ask"); p.add_argument("question")
    p = sp.add_parser("insights"); p.add_argument("verb", choices=["rebuild"])
    p = sp.add_parser("canvas"); p.add_argument("verb", choices=["rebuild"])
    return ap


def main():
    ap = parser()
    args = ap.parse_args()
    cmd = args.cmd or "status"
    if cmd == "help":
        print(HELP)
        return
    if not args.cmd:
        args = ap.parse_args(["status"] + sys.argv[1:])
    cfg = load_cfg()
    if cmd == "viewer" and getattr(args, "role2", None):
        args.role = args.role2
    if cmd == "refresh":
        args.yes = args.yes or args.apply
    {"status": cmd_status, "doctor": cmd_doctor, "refresh": cmd_refresh, "threshold": cmd_threshold, "viewer": cmd_viewer, "metric": cmd_metric,
     "alert": cmd_alert, "chart": cmd_chart, "check": cmd_check, "team": cmd_team, "roster": cmd_roster, "ask": cmd_agent, "insights": cmd_agent,
     "canvas": cmd_agent}[cmd](args, cfg)


if __name__ == "__main__":
    main()
