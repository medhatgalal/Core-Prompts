#!/usr/bin/env python3
"""One bounded native AGY intake call; preserve input and native output exactly."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import select
import shutil
import signal
import stat
import subprocess
import sys
import time

MARKER = "CORE_PROMPTS_AGY_INTAKE_ACTIVE"
MAX_SECONDS = 240.0
CLEANUP_SECONDS = 0.5


class IntakeError(Exception):
    """A local setup problem, before native completion."""


def timeout_value(value: str) -> float:
    seconds = float(value)
    if not math.isfinite(seconds) or not 0 < seconds <= MAX_SECONDS:
        raise argparse.ArgumentTypeError("timeout must be greater than 0 and at most 240 seconds")
    return seconds


def read_request(path: str | None, deadline: float, interrupted: list[int]) -> str:
    """Read UTF-8 without newline translation; waiting for stdin consumes the budget."""
    owned = path is not None
    if owned:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    else:
        fd = sys.stdin.fileno()
        if os.isatty(fd):
            raise IntakeError("supply --prompt-file FILE or redirect a request on stdin")
    try:
        if owned and not stat.S_ISREG(os.fstat(fd).st_mode):
            raise IntakeError("prompt file must be a regular file")
        chunks = []
        while True:
            if interrupted:
                raise InterruptedError
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            ready, _, _ = select.select([fd], [], [], min(remaining, 0.1))
            if not ready:
                continue
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        request = b"".join(chunks).decode("utf-8")
        if not request.strip() or "\x00" in request:
            raise IntakeError("request must be nonempty UTF-8 without NUL bytes")
        return request
    finally:
        if owned:
            os.close(fd)


def invocation(request: str) -> list[str]:
    if os.name != "posix":
        raise IntakeError("this launcher requires POSIX process groups")
    if MARKER in os.environ:
        raise IntakeError("nested AGY intake is disabled; use the current conversation")
    executable = shutil.which("agy")
    if executable is None:
        raise IntakeError("agy is not on PATH; install/configure it separately")
    resources = Path(__file__).resolve().parents[1]
    package = resources.parent
    if package.name != "engos-route-intent" or not (package / "SKILL.md").is_file():
        raise IntakeError("run this helper from a complete engos-route-intent skill package")
    schema = (resources / "schemas/agy-intake.schema.json").read_bytes().decode("utf-8")
    json.loads(schema)
    return [str(Path(executable).resolve()), "--mode", "plan", "--sandbox",
            "--add-dir", str(package.parent), "--output-format", "stream-json",
            "--json-schema", schema, "-p", request]


def signal_group(child: subprocess.Popen, signum: int) -> str:
    """Only ESRCH proves absence; a permission denial remains an error state."""
    try:
        os.killpg(child.pid, signum)
        return "sent"
    except ProcessLookupError:
        return "absent"
    except PermissionError:
        return "denied"


def stop_group(child: subprocess.Popen, signum: int, deadline: float) -> str | None:
    """Bounded cleanup of the fixed group created by start_new_session=True.

    Retry denied signals/probes within this budget; never select another group
    or infer absence from EPERM. poll() reaps the direct child without waiting.
    """
    started = time.monotonic()
    end = min(deadline, started + CLEANUP_SECONDS)
    force_at = started + max(0, end - started) / 2
    sent = None
    absent = False
    denied = set()
    while True:
        now = time.monotonic()
        requested = signum if now < force_at else signal.SIGKILL
        if not absent and sent != requested:
            result = signal_group(child, requested)
            if result == "absent":
                absent = True
            elif result == "sent":
                sent = requested
            else:
                denied.add(int(requested))
        if not absent:
            result = signal_group(child, 0)
            absent = result == "absent"
            if result == "denied":
                denied.add(0)
        reaped = child.poll() is not None
        if absent and reaped:
            return None
        remaining = end - time.monotonic()
        if remaining <= 0:
            detail = "group absence unverified" if not absent else "direct child reaping unverified"
            if denied:
                detail += "; permission denied for signals " + ",".join(map(str, sorted(denied)))
            return detail
        time.sleep(min(0.02, remaining))


def main(argv: list[str] | None = None) -> int:
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-file", help="UTF-8 request file; otherwise read stdin")
    parser.add_argument("--timeout-seconds", type=timeout_value, default=MAX_SECONDS,
                        help="total input/setup/native budget, greater than 0 and at most 240 (default: 240)")
    args = parser.parse_args(argv)
    deadline = started + args.timeout_seconds
    interrupted: list[int] = []
    previous = {}
    child = None
    result_code = 2

    def remember_signal(signum, _frame):
        if not interrupted:
            interrupted.append(signum)

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, remember_signal)
        if os.name != "posix":
            raise IntakeError("this launcher requires POSIX process groups")
        if MARKER in os.environ:
            raise IntakeError("nested AGY intake is disabled; use the current conversation")
        request = read_request(args.prompt_file, deadline, interrupted)
        command = invocation(request)
        if interrupted:
            raise InterruptedError
        # Reserve cleanup inside the overall deadline, including short test budgets.
        stop_at = deadline - min(CLEANUP_SECONDS, args.timeout_seconds / 4)
        if time.monotonic() >= stop_at:
            raise TimeoutError
        env = os.environ.copy()
        env[MARKER] = "1"
        child = subprocess.Popen(command, shell=False, stdin=subprocess.DEVNULL,
                                 env=env, start_new_session=True)
        while True:
            if interrupted:
                raise InterruptedError
            code = child.poll()
            if code is not None:
                result_code = code if code >= 0 else 128 - code
                break
            remaining = stop_at - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            time.sleep(min(0.05, remaining))
    except TimeoutError:
        print("agy-intake: total time budget expired", file=sys.stderr)
        result_code = 124
    except InterruptedError:
        result_code = 128 + interrupted[0] if interrupted else 130
    except IntakeError as exc:
        print(f"agy-intake: {exc}", file=sys.stderr)
        result_code = 2
    except (OSError, UnicodeError, ValueError):
        # Do not echo request/schema contents from exception messages.
        print("agy-intake: invalid input, package or runtime; check UTF-8 input, bundled schema and agy on PATH", file=sys.stderr)
        result_code = 2
    finally:
        cleanup_problem = None
        try:
            if child is not None:
                cleanup_problem = stop_group(child, interrupted[0] if interrupted else signal.SIGTERM, deadline)
        except Exception as exc:
            # Preserve the primary result and avoid exposing exception payloads.
            cleanup_problem = "cleanup inspection failed (" + type(exc).__name__ + ")"
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)
        if cleanup_problem:
            print(f"agy-intake: cleanup incomplete; original_status={result_code}; "
                  f"native_status={getattr(child, 'returncode', None)}; {cleanup_problem}", file=sys.stderr)
            if result_code == 0:
                result_code = 2
    return result_code


if __name__ == "__main__":
    raise SystemExit(main())
