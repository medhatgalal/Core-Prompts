"""GitLab GET helper: every call goes through tools/ro/ro (AC39). No model calls (AC55)."""
import json, os, subprocess, threading, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RO = os.path.join(ROOT, "tools", "ro", "ro")
STATS = {"calls": 0, "retries": 0, "retries_429": 0, "retries_403_rate": 0, "final_errors": 0}
_LOCK = threading.Lock()


class ApiError(Exception):
    pass


def get(path, retries=6):
    """Return (status, headers dict lower-cased, parsed JSON or None).
    Backs off and retries on 429, on 403 that carries a Retry-After header (rate limit), and on 5xx or a dead call."""
    delay = 2
    for attempt in range(retries + 1):
        with _LOCK:
            STATS["calls"] += 1
        r = subprocess.run([RO, "glab", "api", "-i", path], capture_output=True)
        raw = r.stdout
        sep = raw.find(b"\r\n\r\n")
        sl = 4
        if sep < 0:
            sep, sl = raw.find(b"\n\n"), 2
        head = raw[:sep].decode("latin1") if sep >= 0 else ""
        lines = head.splitlines()
        status = int(lines[0].split()[1]) if lines and lines[0].startswith("HTTP") else 0
        hdr = {}
        for l in lines[1:]:
            if ":" in l:
                k, v = l.split(":", 1)
                hdr[k.strip().lower()] = v.strip()
        body = raw[sep + sl:] if sep >= 0 else b""
        rate403 = status == 403 and "retry-after" in hdr
        if status in (429, 500, 502, 503, 504) or status == 0 or rate403:
            if attempt < retries:
                with _LOCK:
                    STATS["retries"] += 1
                    if status == 429: STATS["retries_429"] += 1
                    if rate403: STATS["retries_403_rate"] += 1
                try:
                    wait = float(hdr.get("retry-after", delay))
                except ValueError:
                    wait = delay
                time.sleep(min(wait, 120))
                delay *= 2
                continue
        data = None
        if body.strip():
            try:
                data = json.loads(body)
            except ValueError:
                data = None
        if status >= 400 or status == 0:
            with _LOCK:
                STATS["final_errors"] += 1
        return status, hdr, data
    return status, hdr, None
