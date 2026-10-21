#!/usr/bin/env python3
"""Read current catalog identities and conditional routing suggestions. Never execute a route."""

from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

OWNER = "engos-orchestration-route-intent"
SLUG = re.compile(r"[a-z][a-z0-9-]*\Z")
KINDS = {"sequence", "iterate", "return", "parallel", "support"}
MAX_BYTES = 2_000_000


def read_json(path):
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError(f"Input exceeds size limit: {path.name}")
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def inspect(root=None, skills_roots=(), table_path=None, selected=()):
    table_path = (
        table_path or Path(__file__).resolve().parents[1] / "routing-relations.json"
    )
    table, table_hash = read_json(table_path)
    if table.get("schema_version") != "SkillRoutingRelations.v1":
        raise ValueError("Unsupported routing table schema")
    skills = {
        k: dict(v, inventory_basis="bundled_snapshot")
        for k, v in table["catalog"].items()
    }
    if root is not None:
        descriptors = root / ".meta/capabilities"
        if not descriptors.is_dir():
            raise ValueError(
                "Explicit Core root has no capability descriptor directory"
            )
        skills = {}
        for path in sorted(descriptors.glob("*.json")):
            d, sha = read_json(path)
            slug = d.get("slug")
            if (
                not isinstance(slug, str)
                or not SLUG.fullmatch(slug)
                or path.stem != slug
            ):
                raise ValueError("Descriptor slug/path mismatch")
            minimal = d.get("layers", {}).get("minimal", {})
            skills[slug] = {
                "summary": minimal.get("summary", "Read the complete skill contract"),
                "descriptor_sha256": sha,
                "inventory_basis": "current_explicit_root",
            }
    for value in skills.values():
        value["availability"] = "catalog_only"
        value["observed_entries"] = []
    for directory in skills_roots:
        if not directory.is_dir():
            raise ValueError(f"Explicit skill directory unavailable: {directory}")
        for entry in sorted(directory.glob("*/SKILL.md")):
            slug = entry.parent.name
            if not SLUG.fullmatch(slug):
                continue
            raw = entry.read_bytes()
            if len(raw) > MAX_BYTES:
                raise ValueError("Skill entry exceeds size limit")
            value = skills.setdefault(
                slug,
                {
                    "summary": "Unmapped entry: read its complete contract",
                    "descriptor_sha256": None,
                    "inventory_basis": "explicit_skill_directory",
                    "observed_entries": [],
                },
            )
            value["observed_entries"].append(
                {"path": str(entry), "sha256": hashlib.sha256(raw).hexdigest()}
            )
            value["availability"] = "entry_observed_not_native_discovery"
    edges = []
    ids = set()
    for edge in table["relationships"]:
        if edge.get("id") in ids or edge.get("kind") not in KINDS:
            raise ValueError("Duplicate relationship id or unsupported kind")
        ids.add(edge["id"])
        if not all(
            isinstance(edge.get(k), str) and edge[k].strip()
            for k in ("from", "to", "when", "handoff", "stop")
        ):
            raise ValueError("Incomplete relationship condition")
        refs = edge.get("source_refs", [])
        endpoints = {edge["from"], edge["to"]}
        if {r.get("slug") for r in refs} != endpoints:
            raise ValueError("Relationship must bind both endpoint contracts")
        status = (
            "matched"
            if all(
                r["slug"] in skills
                and skills[r["slug"]].get("descriptor_sha256")
                == r.get("descriptor_sha256")
                and r.get("descriptor_sha256")
                for r in refs
            )
            else "stale_or_missing"
        )
        edges.append({**edge, "binding_status": status})
    unknown = sorted(set(selected) - set(skills))
    if selected:
        skills = {s: v for s, v in skills.items() if s in selected}
        edges = [e for e in edges if e["from"] in selected or e["to"] in selected]
    return {
        "schema_version": "SkillRoutingInspection.v1",
        "table_sha256": table_hash,
        "grants_authority": False,
        "native_discovery_verified": False,
        "binding_match_is_not_applicability": True,
        "skills": skills,
        "relationships": edges,
        "unknown_requested_skills": unknown,
        "limits": [
            "Read selected complete skill contracts; metadata is advisory.",
            "New or changed skills remain selectable even without a matched relationship.",
            "Parallel suggestions require actual independence, allowed writes and host authority.",
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--root",
        type=Path,
        help="Explicit trusted source or verified support root; not a trust check",
    )
    p.add_argument(
        "--skills-root",
        type=Path,
        action="append",
        default=[],
        help="Explicit session skill directory; observation is not native discovery",
    )
    p.add_argument("--table", type=Path)
    p.add_argument(
        "--skill",
        action="append",
        default=[],
        help="Limit returned rows and neighboring suggestions",
    )
    a = p.parse_args()
    try:
        print(json.dumps(inspect(a.root, a.skills_root, a.table, a.skill), indent=2))
    except (ValueError, OSError, KeyError, TypeError) as e:
        p.exit(2, f"Catalog inspection incomplete: {e}\n")


if __name__ == "__main__":
    main()
