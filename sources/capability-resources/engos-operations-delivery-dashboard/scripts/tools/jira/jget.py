#!/usr/bin/env python3.14
"""GET-only Jira client for the scheduled path (no browser). Same idea as tools/ro.
 - Only the GET method exists here; there is no way to send anything else.
 - Only the configured Jira host and api.atlassian.com may be called; redirects are refused (so the credential never follows one).
 - The token is read from the environment variable NAMED in data/config.json (jira.auth.token_env), used for the Authorization header
   and nowhere else: it is never printed, logged, or put in an error message (messages are scrubbed).
 - Every call is counted in the object's .calls; callers write the count to calls_incremental.json.
 - Every call is appended to data/extracts/jira/jira-calls.log (override: env JIRA_CALL_LOG): UTC time, method, path with every query VALUE
   replaced by <masked>, HTTP status. Never the Authorization header, the token, the email, or a query value.
 - Self-test, no Jira call: python3.14 -I tools/jira/jget.py --selftest
"""
import sys, os, json, time, base64, datetime, urllib.request, urllib.error, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg

ALLOWED_HOSTS = {cfg.HOST, "api.atlassian.com"}
LOG = os.environ.get("JIRA_CALL_LOG") or os.path.join(os.environ.get("JIRA_EXTRACT_DIR") or os.path.join(cfg.ROOT, "data", "extracts", "jira"), "jira-calls.log")


def mask(path):
    """/rest/api/3/search/jql?jql=<x>&nextPageToken=<y> -> /rest/api/3/search/jql?jql=<masked>&nextPageToken=<masked>  (names kept, values never)."""
    u = urllib.parse.urlsplit(path)
    q = "&".join(urllib.parse.quote(k, safe="") + "=<masked>" for k, _ in urllib.parse.parse_qsl(u.query, keep_blank_values=True))
    return u.path + ("?" + q if q else "")


def log_call(path, outcome):
    """Append one line: UTC time, method (always GET), masked path, HTTP status (or ERROR). Append-only; no credential or header can reach it."""
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    line = "%s\tGET\t%s\t%s\n" % (datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), mask(path), str(outcome).replace("\t", " ")[:60])
    with open(LOG, "a") as f: f.write(line)


class NoAuth(Exception):
    """Missing variable, or the server answered 401/403/IP-block: the caller exits 2 with this plain message."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None


class JiraGet:
    def __init__(self, base=None):
        self.email = os.environ.get(cfg.ENV_EMAIL, ""); self._tok = os.environ.get(cfg.ENV_TOKEN, "")
        miss = [n for n, v in ((cfg.ENV_EMAIL, self.email), (cfg.ENV_TOKEN, self._tok)) if not v]
        if miss: raise NoAuth("Jira: environment variable %s is not set (the Jira API token and account email are read from it)" % " and ".join(miss))
        self.base = (base or cfg.BASE).rstrip("/")
        if urllib.parse.urlparse(self.base).hostname not in ALLOWED_HOSTS: raise NoAuth("Jira: host not allowed: " + self.base)
        self._auth = "Basic " + base64.b64encode(f"{self.email}:{self._tok}".encode()).decode()
        self.calls = 0; self.r429 = 0; self.errors = 0
        self._opener = urllib.request.build_opener(_NoRedirect)

    def _scrub(self, s): return str(s).replace(self._tok, "***").replace(self._auth, "***")

    def get(self, path, retries=6):
        """Return (status, parsed json or None, raw text). Backs off on 429 and on 403 with Retry-After; retries 5xx."""
        url = self.base + path
        for attempt in range(retries):
            req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json", "Authorization": self._auth})
            self.calls += 1
            try:
                with self._opener.open(req, timeout=60) as r: status, body, hdr = r.status, r.read().decode("utf-8", "replace"), r.headers
            except urllib.error.HTTPError as e:
                status, body, hdr = e.code, e.read().decode("utf-8", "replace"), e.headers
            except Exception as e:
                log_call(path, "ERROR"); time.sleep(5 * (attempt + 1)); last = self._scrub(e); continue
            log_call(path, status)
            ra = hdr.get("Retry-After") if hdr else None
            if status == 429 or (status == 403 and ra):
                self.r429 += 1; time.sleep(min(float(ra or 10) * (attempt + 1), 300)); continue
            if status >= 500: time.sleep(5 * (attempt + 1)); continue
            try: data = json.loads(body) if body.strip() else None
            except ValueError: data = None
            return status, data, body
        self.errors += 1
        raise RuntimeError("Jira GET failed after retries: " + path[:60])


def _selftest():
    """No network, no Jira call. Proves: GET only, query values masked, nothing secret reaches the log, the log is append-only."""
    import tempfile
    fake_tok, fake_mail = "selftest-FAKE-token-0123456789", "nobody@example.invalid"
    real = os.environ.get(cfg.ENV_TOKEN, "")   # compared against the log, never printed
    os.environ[cfg.ENV_TOKEN], os.environ[cfg.ENV_EMAIL] = fake_tok, fake_mail
    global LOG
    d = tempfile.mkdtemp(prefix="jget-selftest-", dir=os.path.join(cfg.ROOT, "data", "extracts"))
    LOG = os.path.join(d, "calls.log")
    ok = True
    def check(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name); ok = ok and bool(cond)
    check("mask keeps names, hides values", mask("/rest/api/3/search/jql?jql=project%3DX&nextPageToken=SECRET&maxResults=100") == "/rest/api/3/search/jql?jql=<masked>&nextPageToken=<masked>&maxResults=<masked>")
    check("mask of a path with no query is unchanged", mask("/rest/api/3/myself") == "/rest/api/3/myself")
    j = JiraGet()
    seen = []
    class _R:
        status = 200; headers = {}
        def read(self): return b'{"ok": true}'
        def __enter__(self): return self
        def __exit__(self, *a): return False
    def fake_open(req, timeout=0):
        seen.append((req.get_method(), req.full_url, bool(req.get_header("Authorization"))))
        return _R()
    j._opener.open = fake_open
    j.get("/rest/api/3/issue/ABC-1?expand=changelog&fields=status")
    j.get("/rest/api/3/search/jql?jql=assignee%20%3D%20someone&nextPageToken=TOKENISH")
    check("every request is a GET", all(m == "GET" for m, _, _ in seen) and len(seen) == 2)
    check("the Authorization header is sent (so it exists) but is never logged", all(a for _, _, a in seen))
    lines = open(LOG).read().splitlines()
    check("one log line per call", len(lines) == 2)
    f = lines[0].split("\t")
    check("line layout: time, GET, masked path, status", len(f) == 4 and f[1] == "GET" and f[2] == "/rest/api/3/issue/ABC-1?expand=<masked>&fields=<masked>" and f[3] == "200")
    blob = open(LOG).read()
    check("no query value, header, scheme or credential in the log", not any(x in blob for x in ("TOKENISH", "someone", "changelog", "Authorization", "Basic", fake_tok, fake_mail)) and not (real and real in blob))
    n = len(blob); log_call("/rest/api/3/myself", 200)
    check("append-only (the file only grows)", len(open(LOG).read()) > n and open(LOG).read().startswith(blob))
    for fn in os.listdir(d): os.remove(os.path.join(d, fn))
    os.rmdir(d)
    print("selftest", "OK" if ok else "FAILED"); return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv: sys.exit(_selftest())
    print("usage: python3.14 -I tools/jira/jget.py --selftest", file=sys.stderr); sys.exit(2)
