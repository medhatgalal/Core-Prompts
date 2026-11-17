"""Thin wrapper over the `gws` CLI (Sheets and Drive only). No model call. Counts calls, 429 retries, final errors."""
import sys, json, os, subprocess, time, threading

STATS = {"calls": 0, "r429": 0, "errors": 0}
_lock = threading.Lock()


def col_letter(i):
    """0-based column index -> A, B, ..., AA"""
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def a1(r, c):
    """0-based row, col -> A1"""
    return f"{col_letter(c)}{r + 1}"


def _run(cmd, retries=6):
    delay = 5
    last = ""
    for attempt in range(retries):
        with _lock:
            STATS["calls"] += 1
        p = subprocess.run(cmd, capture_output=True, text=True)
        out = (p.stdout or "") + (p.stderr or "")
        if p.returncode == 0 and '"error"' not in p.stdout[:400]:
            body = p.stdout
            i = body.find("{")
            try:
                return json.loads(body[i:]) if i >= 0 else {}
            except Exception:
                return {"raw": body}
        last = out[:800]
        if "429" in out or "rateLimitExceeded" in out or "RESOURCE_EXHAUSTED" in out or "quota" in out.lower():
            with _lock:
                STATS["r429"] += 1
            time.sleep(delay)
            delay = min(delay * 2, 60)
            continue
        if "Unable to parse range" in out:      # a tab created seconds ago is sometimes not visible to the Values API yet
            time.sleep(4)
            continue
        if "503" in out or "500" in out or "timed out" in out.lower():
            time.sleep(3)
            continue
        break
    with _lock:
        STATS["errors"] += 1
    raise RuntimeError(f"gws failed: {' '.join(cmd[:6])} ... {last}")


def _guard(params):
    """The scratch Sheet was permanently deleted on 2026-11-12 (ledger lines 'drive file delete'); its id in data/config.json is a marker. Fail clearly, not with an API error."""
    for v in (params or {}).values():
        if isinstance(v, str) and v.startswith("DELETED-"):
            raise SystemExit("stop: this target is the scratch Sheet, which was permanently deleted on 2026-11-12 (see data/ledger.csv, 'drive file delete'). Use --target real, or a copy of the real Sheet.")


# v1.26 tab renames (user item 20): the code keeps the canonical names on the left; a Sheet that has been renamed uses the names on the right. Requests are translated to the
# Sheet's actual names and responses back to the canonical ones, decided per spreadsheet from its tab titles (a Sheet with no renamed tab is untouched). DASHBOARD_NO_TABSHIM=1 turns it off.
RENAMED = {"README": "About", "Coverage": "Sources", "Data_Dictionary": "Definitions", "Run_Log": "Log", "Alert details": "Alerts"}
_INV = {v: k for k, v in RENAMED.items()}
_state = {}


def _use_new(sid):
    if os.environ.get("DASHBOARD_NO_TABSHIM"):
        return None
    if sid not in _state:
        r = _run(["gws", "sheets", "spreadsheets", "get", "--params", json.dumps({"spreadsheetId": sid, "fields": "sheets(properties(title))"}, separators=(",", ":"))])
        titles = {x["properties"]["title"] for x in r.get("sheets", [])}
        _state[sid] = any(v in titles for v in RENAMED.values())
    return _state[sid]


def _tr_range(rng, use_new):
    if not isinstance(rng, str):
        return rng
    for old, new in RENAMED.items():
        for q in ("'", ""):
            pre = f"{q}{old}{q}!"
            if rng.startswith(pre):
                return (f"{q}{new}{q}!" + rng[len(pre):]) if use_new else rng
        if rng == old or rng == f"'{old}'":
            return (new if rng == old else f"'{new}'") if use_new else rng
    return rng


def _tr_body(o, use_new):
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if k == "title" and isinstance(v, str) and use_new and v in RENAMED:
                o[k] = RENAMED[v]
            else:
                _tr_body(v, use_new)
    elif isinstance(o, list):
        for v in o:
            _tr_body(v, use_new)


def _canon_response(r):
    if isinstance(r, dict):
        for s_ in r.get("sheets", []) or []:
            pr = s_.get("properties", {})
            if pr.get("title") in _INV:
                pr["title"] = _INV[pr["title"]]
    return r


HOLD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "crew", "agents", "sheet", "HOLD")


def _is_write(args):
    return bool(args) and (args[0] in ("batchUpdate", "create") or (args[0] == "values" and len(args) > 1 and args[1] in ("update", "append", "clear", "batchUpdate", "batchClear")))


SHEET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "crew", "agents", "sheet")


def _hold(args, drive=False):
    """HARD HOLD (inbox 123): while crew/agents/sheet/HOLD exists every write to any Sheet (and any Drive write) is refused before any API call; reads are unaffected.
    Also: a write is refused while an inbox file newer than crew/agents/sheet/inbox_ack.txt exists (read the inbox, then write its number into that file)."""
    wr = _is_write(args) if not drive else bool(args) and any(a in ("copy", "delete", "update", "create", "emptyTrash", "trash", "untrash") for a in args)
    if not wr:
        return
    if os.path.exists(HOLD_FILE):
        raise SystemExit("stop: HOLD file present (crew/agents/sheet/HOLD): no write to any Sheet until the lead removes it")
    inbox = os.path.join(SHEET_DIR, "inbox")
    nums = [int(f[:-3]) for f in os.listdir(inbox) if f.endswith(".md") and f[:-3].isdigit()] if os.path.isdir(inbox) else []
    ack = os.path.join(SHEET_DIR, "inbox_ack.txt")
    done = int(open(ack).read().strip() or 0) if os.path.exists(ack) else 0
    if nums and max(nums) > done:
        raise SystemExit(f"stop: inbox {max(nums)} is newer than the last one read ({done}): read the inbox, then write its number into crew/agents/sheet/inbox_ack.txt")


def _write_allow(args, params):
    """data/write_allow.txt (one spreadsheet id per line): when the file exists, a write (batchUpdate or any values write) to an id not on it is refused. No file = no restriction (as before)."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "write_allow.txt")
    if not os.path.exists(p):
        return
    ids = {x.strip() for x in open(p) if x.strip() and not x.startswith("#")}
    sid = (params or {}).get("spreadsheetId")
    is_write = bool(args) and (args[0] in ("batchUpdate", "create") or (args[0] == "values" and len(args) > 1 and args[1] in ("update", "append", "clear", "batchUpdate", "batchClear")))
    if is_write and sid not in ids:
        raise SystemExit(f"stop: write to {sid} refused: not on data/write_allow.txt")


_WLOG = {}          # (spreadsheet id, tab or sheetId, kind) -> [first time, last time, count]


_SIZES = []          # v1.42: every write call as sent: (time, spreadsheet id, kind, body bytes as sent)


def _log_size(args, params, body):
    if not _is_write(args):
        return
    import datetime as _dt
    n = len(json.dumps(body, separators=(",", ":"))) if body is not None else 0
    _SIZES.append((_dt.datetime.now(_dt.timezone.utc).strftime("%H:%M:%SZ"), (params or {}).get("spreadsheetId", "")[:6], " ".join(args[:2]), n))


_PENDING = []          # keys of the write call in flight; its outcome is recorded when the call returns or fails


def _write_log(args, params, body):
    """v1.41 write protocol (inbox 137/138): every write is recorded per tab and kind with first and last time from the clock in UTC; flushed at exit to crew/agents/sheet/write-log-auto-<pid>.txt (or $WRITE_LOG)"""
    if not _is_write(args):
        return []
    import datetime as _dt, re as _re
    t = _dt.datetime.now(_dt.timezone.utc).strftime("%H:%M:%SZ")
    sid = (params or {}).get("spreadsheetId", "")[:6]
    keys = []
    if args[0] == "batchUpdate":
        for rq in (body or {}).get("requests", []):
            k = next(iter(rq)); v = rq[k]
            sh = v.get("range", {}).get("sheetId") if isinstance(v.get("range"), dict) else (v.get("sheetId") if isinstance(v, dict) else None)
            if sh is None and isinstance(v.get("properties"), dict):
                sh = v["properties"].get("sheetId", v["properties"].get("title"))
            keys.append((sid, f"sheetId {sh}", k))
    else:
        rng = (params or {}).get("range") or ",".join((body or {}).get("ranges", [])[:1]) or ",".join(str(d.get("range")) for d in (body or {}).get("data", [])[:1])
        keys.append((sid, _re.split(r"!", str(rng))[0].strip("'") or "?", "values " + (args[1] if len(args) > 1 else "")))
    for k in keys:
        e = _WLOG.setdefault(k, [t, t, 0, 0, 0]); e[1] = t; e[2] += 1
    return keys


def _flush_write_log():
    if not _WLOG:
        return
    p = os.environ.get("WRITE_LOG") or os.path.join(SHEET_DIR, f"write-log-auto-{os.getpid()}.txt")
    with open(p, "a") as f:
        f.write(f"# {os.path.basename(sys.argv[0])} {' '.join(sys.argv[1:])[:160]}\n")
        if _SIZES:          # every call as sent: time, spreadsheet, kind, body bytes (the largest first line is the summary)
            f.write(f"# calls as sent: {len(_SIZES)}; largest body {max(x[3] for x in _SIZES):,} B; total {sum(x[3] for x in _SIZES):,} B\n")
            for t, sd, kd, n in _SIZES:
                f.write(f"#   {t}  {sd}  {kd}  body {n:,} B\n")
        for (sid, tab, kind), (t0, t1, n, ok, bad) in sorted(_WLOG.items(), key=lambda kv: kv[1][0]):
            f.write(f"{t0}-{t1}  {sid}  {tab}  {kind}  x{n}" + (f"  OK x{ok}" if ok else "") + (f"  FAILED x{bad}" if bad else "") + (f"  (planned, no call)" if not ok and not bad else "") + "\n")


import atexit as _atexit
_atexit.register(_flush_write_log)


_PLAN_ID = [900000]


def _plan_reply(rq):
    """plan mode only: an addSheet request gets a reply with a made-up sheetId (900000 and up), so a later step of the same plan can name the new tab; no call is made, nothing exists on the Sheet"""
    if isinstance(rq, dict) and "addSheet" in rq:
        pr = dict(rq["addSheet"].get("properties", {})); _PLAN_ID[0] += 1; pr.setdefault("sheetId", _PLAN_ID[0])
        return {"addSheet": {"properties": pr}}
    return {}


def sheets(*args, params=None, body=None):
    _guard(params)
    if not (os.environ.get("SHEET_PLAN_ONLY") and _is_write(args)):          # a plan-only write makes NO call (below), so HOLD and the allowlist have nothing to refuse; every real write still meets both
        _hold(args)
        _write_allow(args, params)
    _keys = _write_log(args, params, body)
    _log_size(args, params, body)
    if os.environ.get("SHEET_PLAN_ONLY") and _is_write(args):          # plan mode: record the write (tab, kind, count) in the write log and make NO call
        if os.environ.get("PLAN_DUMP"):          # plan mode: keep the exact requests (offline review of ranges and sizes)
            with open(os.environ["PLAN_DUMP"], "a") as _f:
                _f.write(json.dumps({"args": list(args), "params": {k: v for k, v in (params or {}).items()}, "body": body}) + "\n")
        return {"replies": [_plan_reply(rq) for rq in (body or {}).get("requests", [])], "updatedCells": 0}
    sid = (params or {}).get("spreadsheetId")
    use_new = _use_new(sid) if sid else None
    if use_new is not None and params:
        params = dict(params)
        for k in ("range",):
            if k in params:
                params[k] = _tr_range(params[k], use_new)
        if "ranges" in params and isinstance(params["ranges"], list):
            params["ranges"] = [_tr_range(x, use_new) for x in params["ranges"]]
    if use_new and body is not None and args and args[0] in ("batchUpdate",):
        import copy
        body = copy.deepcopy(body)
        _tr_body(body, use_new)
    cmd = ["gws", "sheets", "spreadsheets", *args]
    if params is not None:
        cmd += ["--params", json.dumps(params, separators=(",", ":"))]
    if body is not None:
        cmd += ["--json", json.dumps(body, separators=(",", ":"))]
    def _batch_name():
        return "; ".join(f"{t} {k}" for (_s, t, k) in _keys) or " ".join(args)
    try:
        r = _run(cmd)
        if _keys and isinstance(r, dict) and r.get("error"):
            raise RuntimeError("non-success response: " + str(r["error"])[:200])
    except BaseException as e_:
        for k_ in _keys:
            _WLOG[k_][4] += 1          # the write call failed: recorded as FAILED, never as written
        if _keys and not isinstance(e_, SystemExit):
            raise SystemExit(f"HARD STOP: a write call failed and nothing after it was sent. Failed batch: {_batch_name()} ({len(_keys)} request(s)). {type(e_).__name__}: {str(e_)[-240:]}")
        raise
    for k_ in _keys:
        _WLOG[k_][3] += 1
    if args and args[0] == "batchUpdate" and sid:
        _state.pop(sid, None)
    return _canon_response(r) if use_new is not None else r


def drive(*args, params=None, body=None):
    _guard(params)
    _hold(args, drive=True)
    cmd = ["gws", "drive", *args]
    if params is not None:
        cmd += ["--params", json.dumps(params, separators=(",", ":"))]
    if body is not None:
        cmd += ["--json", json.dumps(body, separators=(",", ":"))]
    return _run(cmd)


BODY_STOP = 80_000          # v1.42: no batchUpdate piece may be over 80 KB; the gws command line cannot carry more ("Argument list too long")


def batch_pieces(requests):
    """Split requests in order into pieces of at most BODY_STOP bytes (as sent). HARD STOP, before ANY piece is sent, when one request alone is over BODY_STOP. Changes no request."""
    pieces, chunk, size = [], [], 0
    for i, rq in enumerate(requests):
        n = len(json.dumps(rq, separators=(",", ":")))
        if n > BODY_STOP:
            raise SystemExit(f"HARD STOP before any send: batchUpdate request {i + 1} of {len(requests)} is {n:,} B, over the {BODY_STOP:,} B piece limit; nothing was sent")
        if chunk and size + n > BODY_STOP:
            pieces.append(chunk); chunk, size = [], 0
        chunk.append(rq); size += n
    if chunk:
        pieces.append(chunk)
    return pieces


def batch(sid, requests):
    if not requests:
        return {}
    pieces = batch_pieces(requests)          # all pieces are checked before the first one is sent
    if len(pieces) == 1:
        return sheets("batchUpdate", params={"spreadsheetId": sid}, body={"requests": requests})
    replies = []
    for ch in pieces:
        replies += (sheets("batchUpdate", params={"spreadsheetId": sid}, body={"requests": ch}) or {}).get("replies", [{} for _ in ch])
    return {"replies": replies}


def _selftest_batch():
    small = [{"a": "x" * 100} for _ in range(10)]
    big = [{"a": "x" * 30_000} for _ in range(5)]
    ok = len(batch_pieces(small)) == 1 and len(batch_pieces(big)) == 3 and sum(len(p) for p in batch_pieces(big)) == 5
    ok &= all(len(json.dumps({"requests": pc}, separators=(",", ":"))) <= BODY_STOP + 20 for pc in batch_pieces(big))
    try:
        batch_pieces(small + [{"a": "x" * 90_000}] + small); ok = False          # one request over 80 KB must stop
    except SystemExit as e:
        ok &= "nothing was sent" in str(e)
    calls = []
    global sheets
    real = sheets
    sheets = lambda *a, **k: calls.append(1) or {}
    try:
        batch("X", small + [{"a": "x" * 90_000}])
        ok = False
    except SystemExit:
        ok &= calls == []          # not one call was made before the stop
    finally:
        sheets = real
    import tempfile                                                          # plan-only write under HOLD: recorded, no call; a real write under HOLD: refused
    tmp = tempfile.mkdtemp(); hold = os.path.join(tmp, "HOLD"); open(hold, "w").write("x")
    global HOLD_FILE, _run
    h0, run0, env0 = HOLD_FILE, _run, {k: os.environ.get(k) for k in ("SHEET_PLAN_ONLY", "WRITE_LOG")}
    HOLD_FILE = hold; calls2 = []; _run = lambda cmd: calls2.append(cmd) or {}; os.environ["WRITE_LOG"] = os.path.join(tmp, "wl.txt")
    try:
        os.environ["SHEET_PLAN_ONLY"] = "1"
        sheets("batchUpdate", params={"spreadsheetId": "SELFTEST"}, body={"requests": [{"updateCells": {"range": {"sheetId": 1}}}]}); ok &= calls2 == []
        for verb in ("update", "append", "clear", "batchUpdate", "batchClear"):          # every values write verb: zero gws processes under HOLD in plan mode
            sheets("values", verb, params={"spreadsheetId": "SELFTEST", "range": "A1"}, body={"values": [["x"]]})
        ok &= calls2 == []
        sheets("get", params={"spreadsheetId": "SELFTEST"}); ok &= len(calls2) >= 1          # a read still runs (the counter works)
        calls2.clear()
        os.environ.pop("SHEET_PLAN_ONLY")
        try:
            sheets("batchUpdate", params={"spreadsheetId": "SELFTEST"}, body={"requests": [{"updateCells": {"range": {"sheetId": 1}}}]}); ok = False
        except SystemExit as e:
            ok &= "HOLD" in str(e) and calls2 == []
        for verb in ("update", "append", "clear", "batchUpdate", "batchClear"):          # without plan mode every values write verb is refused by HOLD, no process started
            try:
                sheets("values", verb, params={"spreadsheetId": "SELFTEST", "range": "A1"}, body={"values": [["x"]]}); ok = False
            except SystemExit as e:
                ok &= "HOLD" in str(e)
        ok &= calls2 == []
    finally:
        HOLD_FILE, _run = h0, run0
        for k, v in env0.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    print("sheetlib batch selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def get_meta(sid, fields="sheets(properties(sheetId,title,gridProperties),charts(chartId)),namedRanges"):
    return sheets("get", params={"spreadsheetId": sid, "fields": fields})


def values_update(sid, rng, values, option="USER_ENTERED"):
    return sheets("values", "update", params={"spreadsheetId": sid, "range": rng, "valueInputOption": option},
                  body={"values": values})


def values_get(sid, rng, render="FORMATTED_VALUE"):
    r = sheets("values", "get", params={"spreadsheetId": sid, "range": rng, "valueRenderOption": render})
    return r.get("values", [])



def _norm(v):
    if v is None or v == "":
        return ""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return round(float(v), 9)
    return str(v)


def write_diff(sid, sheet_title, rows, option="USER_ENTERED", log=None, chunk=1500):
    """Write only the rows whose content differs from what the tab holds now (daily path: a cell that already holds the same text or value is not touched, so nothing
    recalculates for no reason). The current content is read in chunks (formulas as text for USER_ENTERED, raw values for RAW). Rows below len(rows) are not touched here.
    Returns the number of rows written. One log line per write."""
    n = len(rows)
    ncols = max((len(r) for r in rows), default=0)
    render = "FORMULA" if option == "USER_ENTERED" else "UNFORMATTED_VALUE"
    changed = []
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        cur = values_get(sid, f"'{sheet_title}'!{a1(a, 0)}:{a1(b - 1, max(ncols - 1, 0))}", render)
        for i in range(a, b):
            old = cur[i - a] if i - a < len(cur) else []
            new = rows[i]
            oldn = [_norm(x) for x in old] + [""] * (ncols - len(old))
            newn = [_norm(x) for x in new] + [""] * (ncols - len(new))
            if oldn != newn:
                changed.append(i)
                if os.environ.get("DASHBOARD_DIFF_DEBUG") and len(changed) == 1 and log:
                    j = next((k for k in range(ncols) if oldn[k] != newn[k]), 0)
                    log(f"{sheet_title}: first difference row {i + 1} col {j + 1}: sheet {oldn[j]!r} vs new {newn[j]!r}")
    written = 0
    runs = []
    for i in changed:
        if runs and i == runs[-1][1] + 1:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    for a, b in runs:
        for c0 in range(a, b + 1, 500):
            c1 = min(b, c0 + 499)
            block = [list(r) + [""] * (ncols - len(r)) for r in rows[c0:c1 + 1]]
            values_update(sid, f"'{sheet_title}'!{a1(c0, 0)}", block, option)
            written += len(block)
            if log:
                log(f"{sheet_title}: rows {c0 + 1} to {c1 + 1} written ({len(block)} changed rows)")
    if log:
        log(f"{sheet_title}: {n} rows compared, {written} written, {n - written} left untouched")
    return written


def write_grid(sid, sheet_title, rows, start_row=0, start_col=0, max_bytes=600_000, option="USER_ENTERED", log=None):
    """Write a 2D list in chunks of rows that fit max_bytes. Strings starting with '=' are formulas (USER_ENTERED)."""
    i = 0
    n = len(rows)
    while i < n:
        size = 0
        j = i
        while j < n and (size == 0 or size + len(json.dumps(rows[j], separators=(",", ":"))) < max_bytes):
            size += len(json.dumps(rows[j], separators=(",", ":"))) + 1
            j += 1
        rng = f"'{sheet_title}'!{a1(start_row + i, start_col)}"
        values_update(sid, rng, rows[i:j], option)
        if log:
            log(f"{sheet_title} rows {i}-{j} of {n}")
        i = j
