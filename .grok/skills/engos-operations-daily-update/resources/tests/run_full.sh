#!/bin/sh
# Full exploratory run on a fresh E2E TEST doc: Create, two days, every persona.
# Prints the doc id, then rule results (verify.py) and reader issues (usability.py).
cd "$(dirname "$0")"
export DU_TEST=1
# The test days are fixed in Nov 2026; read their yearless dates against that week, whatever today is.
export DU_TODAY=2026-11-09
SK=../scripts
EMAIL=${DU_TEST_EMAIL:-$(gws gmail users getProfile --params '{"userId":"me"}' 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin)[\"emailAddress\"])")}
export DU_TEST_EMAIL="$EMAIL"
START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
DOC=$(python3 exploratory.py create 2>/dev/null | tail -1)
echo "DOC $DOC"
python3 exploratory.py day1 "$DOC" 2>/dev/null
python3 $SK/sweep.py "$DOC" 2026-11-06 --owner Scott --publish --tag --people '{"Scott":"'"$EMAIL"'"}' 2>/dev/null | grep -E "TAGGED|LANDED|DID NOT"
python3 exploratory.py overview1 "$DOC" 2>/dev/null
python3 $SK/overview.py "$DOC" 2026-11-06 "4:00 PM ET" --publish >/dev/null 2>&1
python3 exploratory.py day2 "$DOC" 2>/dev/null
python3 day_mon_nov9.py "$DOC" 2>/dev/null
python3 $SK/sweep.py "$DOC" 2026-11-09 --owner Scott --publish --tag --people '{"Scott":"'"$EMAIL"'","Kyle":"kyle.test@example.invalid"}' 2>/dev/null | grep -E "TAGGED|LANDED|DID NOT"
python3 -c "import sys; sys.path.insert(0, '$SK'); import modes; modes.archive('$DOC', 'Team Restructure (Kui)', 'done Mon Nov 9')" 2>/dev/null
python3 exploratory.py overview2 "$DOC" 2>/dev/null
python3 $SK/overview.py "$DOC" 2026-11-09 "4:00 PM ET" --publish >/dev/null 2>&1
python3 $SK/verify.py "$DOC" 2026-11-09 --since 2026-11-05 --started "$START" 2>/dev/null | tail -8
python3 $SK/usability.py "$DOC" 2026-11-09 --since 2026-11-05 2>/dev/null
python3 $SK/send.py "$DOC" '[{"name":"Medhat","email":"medhat.test@example.invalid","channel":"email"}]' 2>/dev/null
