#!/usr/bin/env bash
# GitHub refresh (AC55): no agent, no model call. Re-pulls everything from data/identity.csv through tools/ro/ (GET only).
# Usage: tools/github/refresh.sh [AS_OF]   AS_OF defaults to now (UTC, YYYY-MM-DDTHH:MM:SSZ), window = AS_OF minus 365 days.
# Old checkpoints are moved to data/extracts/github/checkpoints.prev-<AS_OF> (never deleted). Resumable: if interrupted, rerun
# with the SAME AS_OF and the stages skip finished logins/PRs. Stops a stage if its call budget is reached.
set -euo pipefail
cd "$(dirname "$0")/../.."
ASOF="${1:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
D=data/extracts/github
PY="python3 -I"
mkdir -p "$D"
if [ "$(cat $D/as_of.txt 2>/dev/null || true)" != "$ASOF" ]; then
  [ -d "$D/checkpoints" ] && mv "$D/checkpoints" "$D/checkpoints.prev-$(echo "$ASOF" | tr -d ':')"
  mkdir -p "$D/checkpoints"; echo "$ASOF" > "$D/as_of.txt"
fi
$PY tools/github/pull.py --asof "$ASOF" --workers 4 --budget 12500       # authored, reviews, reviewed-by, head-commit keys
$PY tools/github/pull.py --allcommits --workers 4 --budget 3500         # keys from every commit message (v1.12)
$PY tools/github/pull.py --gatec --workers 4 --budget 3500              # merged_by, non-whitespace body, lines excl lockfiles
$PY tools/github/keystate.py                                             # key states from data/extracts/jira/key_aliases.csv
$PY tools/github/projection.py
printf '{"github": "%s"}\n' "$ASOF" > "$D/cursor.json"                     # a full refresh sets the cursor for later incremental runs
