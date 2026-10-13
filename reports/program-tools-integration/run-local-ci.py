"""Execute the current thirteen GitLab-aligned product checks, preserving receipts."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[2]
config = root / ".gitlab-ci.yml"
output = root / "reports/program-tools-integration/local-ci"
output.mkdir(exist_ok=True)
commands = [line.strip()[2:] for line in config.read_text().splitlines()
            if line.strip().startswith("- ")]
checks = [c for c in commands if c.startswith((
    "python3 scripts/build-", "python3 -m pytest", "python3 scripts/smoke-",
    "bin/capability-", "python3 scripts/validate-"))]
assert len(checks) == 13, "Review the changed CI sequence before executing it"
clock = lambda: dt.datetime.now(dt.timezone.utc).isoformat()
receipt = {"schema_version": "ProgramLocalCI.v1", "alignment": "current GitLab product checks",
           "gitlab_config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
           "startedAt": clock(), "steps": [], "status": "running"}
env = dict(os.environ)
env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env["PATH"]
env["PYTHON_BIN"] = sys.executable
env["PYTHONPATH"] = str(root / "src")
def save():
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
save()
for index, source_command in enumerate(checks, 1):
    args = shlex.split(source_command)
    if args[0] == "python3":
        args[0] = sys.executable
    log = output / f"{index:02d}.log"
    print(f"Check {index}/13: {source_command[:110]}", flush=True)
    started = time.monotonic()
    with log.open("wb") as stream:
        completed = subprocess.run(args, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
    lines = log.read_text(errors="replace").splitlines()
    receipt["steps"].append({"index": index, "sourceCommand": source_command,
        "exitCode": completed.returncode, "seconds": round(time.monotonic()-started, 3),
        "log": str(log.relative_to(root)), "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "tail": lines[-8:]})
    receipt["updatedAt"] = clock()
    save()
    print(f"Check {index}: exit {completed.returncode}; " + (lines[-1] if lines else "empty output"), flush=True)
    if completed.returncode:
        receipt["status"] = "failed"
        save()
        raise SystemExit(completed.returncode)
receipt["status"] = "passed"
receipt["completedAt"] = clock()
save()
print("All thirteen current GitLab-aligned checks passed", flush=True)
