#!/usr/bin/env bash
# GitLab refresh: full re-pull, then rebuild. No agent, no model call (AC55). Every GitLab call goes through tools/ro/ro (GET only).
#   tools/gitlab/refresh.sh [AS_OF_UTC]          full pull (default as-of: now)
#   tools/gitlab/refresh.sh --from-saved         rebuild CSVs from the saved pull, no GitLab calls
#   tools/gitlab/refresh.sh --incremental --asof <UTC>   pull only what changed since data/extracts/gitlab/cursor.json (AC36a);
#                                                exit 0 ok, 1 failure, 2 sign-in / VPN / token; calls in calls_incremental.json
# Reads data/identity.csv (exact/overridden GitLab usernames) and data/extracts/jira/{jira_issues,key_aliases}.csv.
# Writes data/extracts/gitlab/*.csv. A new as-of moves the previous pull to data/extracts/gitlab/archive_<old as-of>/ first.
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT=data/extracts/gitlab
if [ "${1:-}" = "--incremental" ]; then
  shift
  exec python3 -I tools/gitlab/incremental.py --dir "$OUT" "$@"
fi
if [ "${1:-}" != "--from-saved" ]; then
  ASOF="${1:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
  if [ -f "$OUT/as_of.txt" ] && [ "$(tr -d '\n' < "$OUT/as_of.txt")" != "$ASOF" ]; then
    OLD="$(tr -d '\n' < "$OUT/as_of.txt")"; ARC="$OUT/archive_${OLD//:/}"; mkdir -p "$ARC"
    for f in checkpoints detail.jsonl commit_pass.jsonl calls.json list_counts.csv; do [ -e "$OUT/$f" ] && mv "$OUT/$f" "$ARC/"; done
  fi
  python3 -I tools/gitlab/pull.py --out "$OUT" --asof "$ASOF" --workers 8 --budget 58000 --narrow-at 57600
  python3 -I tools/gitlab/commitpass.py --dir "$OUT" --budget 58000 --stop-at 57600
fi
python3 -I tools/gitlab/build.py --dir "$OUT"
if [ "${1:-}" != "--from-saved" ]; then python3 -I tools/gitlab/recount.py --dir "$OUT"; fi
