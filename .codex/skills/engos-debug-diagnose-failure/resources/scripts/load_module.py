"""Validate and assemble declared capability resources using only the standard library.

This file is also copied verbatim to bundled resources/scripts/load_module.py.
Assembly proves which bytes were emitted, not that a model consumed or obeyed them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


MAP_SCHEMA = "CapabilityResourceMap.v1"
BUNDLE_SCHEMA = "CapabilityResourceBundle.v1"
INFRASTRUCTURE = frozenset({"resource-map.json", "scripts/load_module.py", "capability.json"})
RESOURCE_REF = re.compile(r"(?<![\w/])resources/([^\s`\"'<>\[\](){}]+)")


class ResourceContractError(ValueError):
    """A required resource or its declaration is invalid or incomplete."""


def _relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        raise ResourceContractError(f"Invalid resource path: {value!r}")
    path = PurePosixPath(value)
    if (path.is_absolute() or value.startswith("resources/") or "\\" in value
            or ":" in value or "\x00" in value or any(p in {"", ".", ".."} for p in value.split("/"))):
        raise ResourceContractError(f"Invalid resource path: {value!r}")
    return value


def _file(root: Path, relative: str) -> Path:
    try:
        resolved = (root / _relative_path(relative)).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ResourceContractError(f"Missing or invalid resource file: {relative}") from error
    if not resolved.is_relative_to(root):
        raise ResourceContractError(f"Resource path escapes root: {relative}")
    if not resolved.is_file():
        raise ResourceContractError(f"Resource is not a file: {relative}")
    return resolved


def _pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResourceContractError(f"Duplicate manifest key: {key}")
        result[key] = value
    return result


def _paths(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ResourceContractError(f"{label} must be a list of resource paths")
    return [_relative_path(item) for item in value]


def _manifest(resource_root: Path) -> tuple[Path, dict, set[str], str]:
    try:
        root = Path(resource_root).resolve(strict=True)
        manifest_bytes = _file(root, "resource-map.json").read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ResourceContractError(f"Cannot read resource-map.json: {error}") from error
    required = {"schema_version", "shared", "routes", "dependencies"}
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise ResourceContractError("Manifest requires schema_version, shared, routes, dependencies")
    if set(manifest) - required - {"notes"} or manifest["schema_version"] != MAP_SCHEMA:
        raise ResourceContractError("Unsupported resource manifest fields or schema_version")
    declared = set(_paths(manifest["shared"], "shared"))
    for field in ("routes", "dependencies"):
        if not isinstance(manifest[field], dict):
            raise ResourceContractError(f"{field} must be an object")
        for key, values in manifest[field].items():
            if field == "dependencies":
                declared.add(_relative_path(key))
            elif key == "all" or re.fullmatch(r"[^\s]+(?: [^\s]+)*", key) is None:
                raise ResourceContractError(f"Invalid or reserved route: {key!r}")
            declared.update(_paths(values, f"{field}.{key}"))
    # Validate the complete declaration even when this invocation selects one route.
    for relative in sorted(declared):
        _file(root, relative)
    _closure(sorted(declared), manifest["dependencies"])
    return root, manifest, declared, hashlib.sha256(manifest_bytes).hexdigest()


def _closure(seeds: list[str], dependencies: dict[str, list[str]]) -> list[str]:
    ordered: list[str] = []
    visited: set[str] = set()
    active: set[str] = set()

    def visit(relative: str) -> None:
        if relative in active:
            raise ResourceContractError(f"Resource dependency cycle at: {relative}")
        if relative in visited:
            return
        active.add(relative)
        for dependency in dependencies.get(relative, []):
            visit(dependency)
        active.remove(relative)
        visited.add(relative)
        ordered.append(relative)

    for seed in seeds:
        visit(seed)
    return ordered


def _check_references(text: str, available: set[str], owner: str) -> None:
    for match in RESOURCE_REF.finditer(text):
        relative = _relative_path(match.group(1).rstrip(".,;!?"))
        if relative not in available and relative not in INFRASTRUCTURE:
            raise ResourceContractError(f"{owner} references undeclared or unloaded resource: {relative}")


def load_resource_bundle(resource_root: Path, route: str = "all", *, entry_text: str | None = None) -> dict:
    """Return complete ordered content and byte hashes for a validated route."""
    root, manifest, declared, manifest_sha256 = _manifest(resource_root)
    if entry_text is not None:
        _check_references(entry_text, declared, "entry")
    routes = manifest["routes"]
    if route != "all" and route not in routes:
        raise ResourceContractError(f"Unknown resource route: {route}")
    seeds = list(manifest["shared"])
    for selected in routes if route == "all" else [route]:
        seeds.extend(routes[selected])
    ordered = _closure(seeds, manifest["dependencies"])
    resources = []
    for relative in ordered:
        try:
            raw = _file(root, relative).read_bytes()
            content = raw.decode("utf-8")
        except (OSError, UnicodeError) as error:
            raise ResourceContractError(f"Cannot read UTF-8 resource: {relative}") from error
        _check_references(content, set(ordered), relative)
        resources.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "content": content})
    identity = {"schema_version": BUNDLE_SCHEMA, "manifest_sha256": manifest_sha256, "route": route,
                "resources": [{"path": item["path"], "sha256": item["sha256"]} for item in resources]}
    return {
        "schema_version": BUNDLE_SCHEMA,
        "route": route,
        "manifest_sha256": manifest_sha256,
        "resources": resources,
        "sha256": hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "delivery_claim": "assembled_not_proof_of_consumption",
    }


def load_capability_bundle(repo_root: Path, slug: str, entry_text: str, route: str = "all") -> dict | None:
    """Load a canonical package; missing declared manifests never become legacy fallback."""
    if not slug or "/" in slug or "\\" in slug or slug in {".", ".."}:
        raise ResourceContractError(f"Invalid capability slug: {slug!r}")
    root = Path(repo_root) / "sources" / "capability-resources" / slug
    manifest_path = root / "resource-map.json"
    if not manifest_path.exists() and not manifest_path.is_symlink():
        if "resource-map.json" in entry_text or "CapabilityResourceMap.v1" in entry_text:
            raise ResourceContractError(f"Declared resource-map.json is missing for capability: {slug}")
        return None
    return load_resource_bundle(root, route, entry_text=entry_text)


def effective_capability_text(repo_root: Path, slug: str, entry_text: str, route: str = "all") -> str:
    """Expose declared resources to static review, preserving legacy entries exactly."""
    bundle = load_capability_bundle(repo_root, slug, entry_text, route)
    if bundle is None:
        return entry_text
    sections = [f"<!-- resource-bundle: route={route} manifest_sha256={bundle['manifest_sha256']} sha256={bundle['sha256']} -->"]
    sections.extend(f"<!-- resource: {item['path']} sha256={item['sha256']} -->\n{item['content'].rstrip()}" for item in bundle["resources"])
    return entry_text.rstrip() + "\n\n" + "\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--route", default="all")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        bundle = load_resource_bundle(args.resource_root, args.route)
    except ResourceContractError as error:
        print(f"Resource assembly failed: {error}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(bundle, ensure_ascii=False, indent=2))
    else:
        print(f"{bundle['schema_version']} route={bundle['route']} manifest_sha256={bundle['manifest_sha256']} sha256={bundle['sha256']} {bundle['delivery_claim']}")
        for item in bundle["resources"]:
            print(f"\n<!-- resource: {item['path']} sha256={item['sha256']} -->")
            print(item["content"], end="" if item["content"].endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
