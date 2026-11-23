#!/usr/bin/env python3
"""Check or update materialized recommendation review sections in source checkouts."""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_pipeline.review_fragment import FRAGMENT, authored_fragment, check_materializations, consumers, review_slot


def synchronize(root: Path, *, write: bool) -> int:
    if not write:
        check_materializations(root)
        return 0
    fragment = authored_fragment(root)
    pending = []
    previous = None
    for slug in consumers(root):
        path = root / "ssot" / f"{slug}.md"
        if path.resolve() != path or not path.is_file():
            raise ValueError(f"Expected a regular source file at {path}")
        raw = path.read_bytes()
        start, end = review_slot(slug, raw)
        if raw[start:end] == fragment:
            continue
        if previous is None:
            previous = subprocess.run(["git", "show", f"HEAD:{FRAGMENT.as_posix()}"],
                                      cwd=root, check=True, stdout=subprocess.PIPE).stdout
        if raw[start:end] != previous:
            raise ValueError(f"{slug}: local review text differs from both HEAD and the edited fragment")
        pending.append((path, raw, raw[:start] + fragment + raw[end:]))
    # Validate all copies before changing the first. Each complete file replacement
    # is atomic, so a retry after interruption can finish the remaining copies.
    for path, before, after in pending:
        descriptor, name = tempfile.mkstemp(dir=path.parent)
        temp_path = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as staged:
                staged.write(after)
            temp_path.chmod(path.stat().st_mode & 0o777)
            if path.is_symlink() or path.read_bytes() != before:
                raise ValueError(f"{path}: source changed during sync")
            os.replace(temp_path, path)
        finally:
            temp_path.unlink(missing_ok=True)
    return len(pending)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check every copy (default)")
    mode.add_argument("--sync", action="store_true", help="replace exact previous copies using HEAD as the prior source")
    args = parser.parse_args()
    try:
        count = synchronize(ROOT, write=args.sync)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Shared review text verified. Updated {count} files.")
