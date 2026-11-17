#!/usr/bin/env bash
# Jira refresh. No agent, no model call.
#   --incremental: needs only JIRA_EMAIL and JIRA_TOKEN in the environment (read-only GETs through tools/jira/jget.py); add --browser to use the Home browser instead.
#   full refresh (no flag): still reads through the Home browser on CDP 9222 with an Atlassian tab signed in.
# Writes only data/extracts/jira/ (or $JIRA_EXTRACT_DIR). Run from anywhere:
#   bash tools/jira/refresh.sh                                          full re-pull of open items and Done-in-365-days, ~8 minutes
#   bash tools/jira/refresh.sh --incremental --asof 2026-11-11T11:00:00Z   only what changed since cursor.json (AC36a)
# Incremental exit codes: 0 ok, 1 failure (cursor kept), 2 sign-in / browser / network problem (message says what to fix).
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=/opt/homebrew/opt/python@3.14/bin/python3.14
D="${JIRA_EXTRACT_DIR:-data/extracts/jira}"
if [ "${1:-}" = "--incremental" ] || [ "${1:-}" = "--backfill-ids" ] || [ "${1:-}" = "--repair-parents" ]; then
  exec "$PY" -I tools/jira/incremental.py "$@"
fi
if [ "${1:-}" = "--incidents" ]; then
  shift
  exec "$PY" -I tools/jira/incidents.py "$@"
fi
mkdir -p "$D"
[ -f "$D/calls.json" ] && mv "$D/calls.json" "$D/calls_$(date -u +%Y%m%dT%H%M%SZ).json"   # fresh per-refresh call counter (5,000 cap applies per full refresh)
echo '{"calls": 0, "note": "refresh run", "errors": 0, "r429": 0}' > "$D/calls.json"
rm -rf "$D/checkpoints"                                                                      # a full refresh starts from page 1, not resume
date -u +%Y-%m-%dT%H:%M:%SZ > "$D/as_of.txt"                                                 # one as-of per run
"$PY" -I tools/jira/extract.py pull open
"$PY" -I tools/jira/extract.py pull done
"$PY" -I tools/jira/extract.py build
printf '{"cursor": "%s", "written_at": "%s"}\n' "$(cat "$D/as_of.txt")" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$D/cursor.json"   # a full refresh resets the cursor
echo "jira refresh done: as-of $(cat "$D/as_of.txt"); calls $("$PY" -I -c "import json,sys;print(json.load(open(sys.argv[1]))['calls'])" "$D/calls.json")"
