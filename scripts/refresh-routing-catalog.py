#!/usr/bin/env python3
"""Refresh the router's portable catalog from canonical capability descriptors."""

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
OWNER = "engos-route-intent"


def refresh(root, check):
    path = root / "sources/capability-resources" / OWNER / "routing-relations.json"
    table = json.loads(path.read_bytes())
    if table["schema_version"] != "SkillRoutingRelations.v1" or table["owner"] != OWNER:
        raise ValueError(f"Unexpected routing table at {path}")

    catalog = {}
    for descriptor in sorted((root / ".meta/capabilities").glob("*.json")):
        raw = descriptor.read_bytes()
        data = json.loads(raw)
        slug = data["slug"]
        summary = data["layers"]["minimal"]["summary"]
        if slug != descriptor.stem or not isinstance(summary, str) or not summary.strip():
            raise ValueError(f"Invalid capability identity or summary in {descriptor}")

        row = {"summary": summary, "descriptor_sha256": hashlib.sha256(raw).hexdigest()}
        if slug == OWNER:
            # This table contributes to its own descriptor hash.
            row.update(descriptor_sha256=None, self_routing="not_a_downstream_candidate")
        catalog[slug] = row

    if OWNER not in catalog:
        raise ValueError(f"Missing {OWNER} descriptor under {root}")
    if table["catalog"] == catalog:
        return True
    if check:
        return False

    # Relationship endpoint hashes are reviewed evidence, independent of inventory.
    table["catalog"] = catalog
    with TemporaryDirectory(dir=path.parent) as directory:
        staged = Path(directory) / path.name
        staged.write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
        staged.chmod(path.stat().st_mode)
        staged.replace(path)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Core-Prompts source checkout")
    parser.add_argument("--check", action="store_true", help="Fail on drift without writing")
    args = parser.parse_args()
    try:
        current = refresh(args.root, args.check)
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.exit(2, f"Cannot refresh routing catalog: {error}\n")
    if not current:
        parser.exit(1, "Bundled routing catalog is stale. Run refresh-routing-catalog.py without --check.\n")


if __name__ == "__main__":
    main()
