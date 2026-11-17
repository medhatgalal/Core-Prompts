"""Shared helpers for roster tools (files only; no network)."""
import csv, datetime, pathlib, re, unicodedata, getpass, json, os
ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = pathlib.Path(os.environ.get("ROSTER_DATA_DIR") or ROOT / "data")
CFG = json.load(open(ROOT / "data" / "roster_config.json"))
ROSTER = DATA / "roster.csv"
IGNORE = DATA / "roster_ignore.csv"
IDENT = DATA / "identity.csv"
OVERRIDES = DATA / "identity_overrides.csv"
LEDGER = DATA / "ledger.csv"
HISTORY = DATA / "roster_history.csv"
ROSTER_COLS = ["name", "chart_name", "manager", "title", "group", "team", "start_date", "end_date", "note"]
LEDGER_COLS = ["when", "actor", "command", "person", "field", "before", "after", "reason"]
HISTORY_COLS = ["person", "effective_from", "effective_to", "group", "team"]
GROUPS = CFG["groups"]

def now(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def today(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
def norm(s): return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s or "").lower())
def read_csv(path, cols=None):
    path = pathlib.Path(path)
    if not path.exists(): return []
    with path.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
def write_csv(path, rows, cols):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n"); w.writeheader()
        for r in rows: w.writerow({c: r.get(c, "") for c in cols})
AS_USER = False   # set by the roster tool when --as-user is passed
def ledger_actor():
    """'<account> via <role>' (skill-spec). Refuses (exit) when DASHBOARD_AGENT is unset, unless --as-user, then 'via user'. D103."""
    role = os.environ.get("DASHBOARD_AGENT")
    if not role:
        if not AS_USER:
            raise SystemExit("roster: refused: the ledger needs a role. Set DASHBOARD_AGENT=<your role> (for example DASHBOARD_AGENT=roster), or pass --as-user if the user is running this by hand.")
        role = "user"
    return f"{os.environ.get('ROSTER_ACTOR') or CFG['owner_account']} via {role}"
def ledger_append(command, person, field, before, after, reason, actor=None, path=None):
    path = pathlib.Path(path or LEDGER); new = not path.exists()
    actor = ledger_actor()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_COLS, lineterminator="\n")
        if new: w.writeheader()
        w.writerow({"when": now(), "actor": actor, "command": command, "person": person,
                    "field": field, "before": before, "after": after, "reason": reason})
