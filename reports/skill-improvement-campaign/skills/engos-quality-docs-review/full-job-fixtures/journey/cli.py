"""PUBLIC synthetic tool: file writes only when init is explicitly invoked."""
import argparse
import csv
from pathlib import Path
p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="command", required=True)
init = sub.add_parser("init")
init.add_argument("--workspace", required=True)
summary = sub.add_parser("summarize")
summary.add_argument("--workspace", required=True)
summary.add_argument("--input", required=True)
a = p.parse_args()
workspace = Path(a.workspace)
if a.command == "init":
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "ready").write_text("ready\n")
    print("Workspace ready")
else:
    if not (workspace / "ready").is_file():
        p.error("workspace is not initialized; run init first")
    with Path(a.input).open() as f:
        count = sum(1 for _ in csv.DictReader(f))
    print(f"events={count}")
