#!/usr/bin/env python3
"""Source-only CI preparation and optional local pytest launcher.

Provisioning is explicit; checks never install tools or change TMPDIR. The pytest
plugin checks the effective configuration before collection or fixture creation.
"""
from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON_DEPENDENCIES = {
    "pytest": "pytest>=8,<10",
    "jsonschema": "jsonschema>=4,<5",
    "cryptography": "cryptography>=43",
    "docx": "python-docx>=1.2,<2",
    "PIL": "Pillow>=11,<13",
}
REQUIRED_TOOLS = ("bash", "git", "python3", "tar", "zip", "ps")


def check_temporary_root(basetemp: str | None = None) -> None:
    # presentation_cache.selected_cache accepts receipts below these roots.
    # pytest puts each fixture's owned receipt below its basetemp, so equality
    # of basetemp and an accepted root is not itself a cache-policy conflict.
    system_root = Path(tempfile.gettempdir()).resolve()
    selected = Path(basetemp or os.environ.get("PYTEST_DEBUG_TEMPROOT") or system_root).resolve()
    accepted = (Path("/private/tmp"), system_root)
    if not any(selected.is_relative_to(root) for root in accepted):
        raise ValueError(
            f"pytest temporary root {selected} is outside the presentation cache's "
            f"accepted roots: {', '.join(map(str, accepted))}. "
            "Use --basetemp below an accepted root, or create a task-owned parent "
            "and set TMPDIR to that parent for this command only. "
            "Check --basetemp, pytest addopts and PYTEST_DEBUG_TEMPROOT."
        )


def pytest_configure(config) -> None:
    """Public pytest hook: includes CLI, addopts and configuration overrides."""
    import pytest

    try:
        check_temporary_root(config.getoption("basetemp"))
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install-python-deps", action="store_true",
        help="install the existing CI Python dependencies before checking them",
    )
    parser.add_argument("--basetemp", help="check a proposed pytest base temporary directory")
    parser.add_argument(
        "--pytest", nargs=argparse.REMAINDER, metavar="ARG",
        help="after checks, run pytest from the checkout using this Python and all remaining arguments",
    )
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        parser.exit(1, "error: Python 3.11+ is required; Python 3.14 is preferred.\n")
    if args.install_python_deps:
        result = subprocess.run([sys.executable, "-m", "pip", "install", *PYTHON_DEPENDENCIES.values()])
        if result.returncode:
            return result.returncode
    errors = []
    for tool in REQUIRED_TOOLS:
        if shutil.which(tool) is None:
            errors.append(f"missing executable '{tool}'; install it and add it to PATH (Linux: zip and procps provide zip and ps)")
    for module, requirement in PYTHON_DEPENDENCIES.items():
        try:
            importlib.import_module(module)
        except ImportError as error:
            errors.append(
                f"cannot import '{module}': {error}; run "
                f"{shlex.quote(sys.executable)} -m pip install {shlex.quote(requirement)}"
            )
    if args.pytest is None:
        try:
            check_temporary_root(args.basetemp)
        except ValueError as error:
            errors.append(str(error))
    if errors:
        print("Validation environment failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print(f"Validation environment ready: Python {sys.version.split()[0]}, checkout {ROOT}", flush=True)
    if args.pytest is not None:
        environment = os.environ.copy()
        # Only this child receives the plugin search path; no global settings.
        environment["PYTHONPATH"] = os.pathsep.join(filter(None, (
            str(Path(__file__).resolve().parent), environment.get("PYTHONPATH"),
        )))
        command = [sys.executable, "-m", "pytest", "-p", "validation_environment"]
        if args.basetemp:
            command += ["--basetemp", args.basetemp]
        result = subprocess.run(command + args.pytest, cwd=ROOT, env=environment)
        return result.returncode if result.returncode >= 0 else 128 - result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
