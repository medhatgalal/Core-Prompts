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
INFRASTRUCTURE = frozenset({"resource-map.json", "scripts/load_module.py", "capability.json", "shared-resource-imports.json"})
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


def _manifest(resource_root: Path, *, check_files: bool = True) -> tuple[Path, dict, set[str], str]:
    try:
        root = Path(resource_root).resolve(strict=True)
        manifest_bytes = _file(root, "resource-map.json").read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ResourceContractError(f"Cannot read resource-map.json: {error}") from error
    required = {"schema_version", "shared", "routes", "dependencies"}
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise ResourceContractError("Manifest requires schema_version, shared, routes, dependencies")
    if set(manifest) - required - {"notes", "shared_imports"} or manifest["schema_version"] != MAP_SCHEMA:
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
    imports = manifest.get("shared_imports", [])
    if not isinstance(imports, list) or any(not isinstance(i, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", i) for i in imports) or len(set(imports)) != len(imports):
        raise ResourceContractError("Invalid shared_imports declaration")
    if check_files:
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


def _strict_file(root: Path, relative: str) -> Path:
    root = Path(root).absolute()
    path = root / _relative_path(relative)
    for part in (root, *root.parents, path, *path.parents):
        if part.is_symlink():
            raise ResourceContractError(f"Symlink in shared resource path: {path}")
    return _file(root.resolve(), relative)


def _json_file(root: Path, relative: str) -> dict:
    try:
        value = json.loads(_strict_file(root, relative).read_text(encoding="utf-8"), object_pairs_hook=_pairs)
        if not isinstance(value, dict):
            raise ResourceContractError(f"Shared resource JSON must be an object: {relative}")
        return value
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ResourceContractError(f"Invalid shared resource JSON: {relative}") from error


def _fields(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ResourceContractError(f"Invalid {label} fields")


def _token(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", value):
        raise ResourceContractError(f"Invalid shared resource identity: {value!r}")
    return value


def _binding(value):
    _fields(value, {"id", "owner", "source", "destination", "sha256"}, "binding")
    _token(value["id"]); _token(value["owner"])
    for key in ("source", "destination"):
        path = _relative_path(value[key])
        if any(path == item or path.startswith(item + "/") or item.startswith(path + "/") for item in INFRASTRUCTURE):
            raise ResourceContractError(f"Reserved shared resource path: {path}")
    if not isinstance(value["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", value["sha256"]):
        raise ResourceContractError("Invalid shared resource digest")


def _bindings_check(bindings, manifest, declared):
    ids, destinations = set(), set()
    for b in bindings:
        _binding(b)
        dst = b["destination"]
        if b["id"] in ids or any(dst == d or dst.startswith(d + "/") or d.startswith(dst + "/") for d in destinations):
            raise ResourceContractError("Duplicate or colliding shared resource binding")
        ids.add(b["id"]); destinations.add(dst)
        if dst not in declared:
            raise ResourceContractError(f"Undeclared shared destination: {dst}")
    if ids != set(manifest.get("shared_imports", [])):
        raise ResourceContractError("Shared import declaration/receipt mismatch")



def _check_shared_json_references(content, binding, bindings, manifest, owner_map=None):
    """Admit only the explicit TaskPlan -> sibling TaskContract closure.

    Canonical callers supply the owner map. Detached callers can establish local
    receipt consistency only; authenticity requires an external package identity.
    """
    try:
        value = json.loads(content, object_pairs_hook=_pairs)
    except json.JSONDecodeError:
        return  # Non-JSON text still follows the resources/ reference contract.
    refs = []

    def visit(node):
        if isinstance(node, dict):
            if {"$dynamicRef", "$id", "$anchor", "$dynamicAnchor", "$recursiveRef", "$recursiveAnchor"}.intersection(node):
                raise ResourceContractError("Shared JSON base-changing references are forbidden by closure policy")
            if "$ref" in node:
                refs.append(node["$ref"])
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    for ref in refs:
        if (binding["owner"] != "engos-design-plan-implementation"
                or binding["source"] != "schemas/task-plan.schema.json"
                or binding["destination"] != binding["source"]
                or ref != "task-contract.schema.json"):
            raise ResourceContractError("Shared JSON references require the explicit TaskPlan sibling closure")
        target = "schemas/task-contract.schema.json"
        paired = [b for b in bindings if b["owner"] == binding["owner"]
                  and b["source"] == target and b["destination"] == target]
        if len(paired) != 1:
            raise ResourceContractError("Missing same-owner sibling reference binding")
        if target not in manifest["dependencies"].get(binding["destination"], []):
            raise ResourceContractError("Missing direct consumer sibling dependency edge")
        _closure([binding["destination"]], manifest["dependencies"])
        if owner_map is not None:
            if target not in owner_map["dependencies"].get(binding["source"], []):
                raise ResourceContractError("Missing direct owner sibling dependency edge")
            _closure([binding["source"]], owner_map["dependencies"])


def _local_receipt(root, manifest, declared):
    path = root / "shared-resource-imports.json"
    if not manifest.get("shared_imports"):
        if path.exists() or path.is_symlink():
            raise ResourceContractError("Unexpected shared import receipt")
        return None
    receipt = _json_file(root, "shared-resource-imports.json")
    _fields(receipt, {"schema_version", "consumer", "imports"}, "receipt")
    if receipt["schema_version"] != "SharedResourceImportReceipt.v1" or not isinstance(receipt["imports"], list):
        raise ResourceContractError("Invalid shared import receipt")
    _token(receipt["consumer"])
    _bindings_check(receipt["imports"], manifest, declared)
    if receipt["imports"] != sorted(receipt["imports"], key=lambda b: b["id"]):
        raise ResourceContractError("Noncanonical import receipt order")
    for b in receipt["imports"]:
        if b["owner"] == receipt["consumer"]:
            raise ResourceContractError("Shared import self cycle")
        raw = _strict_file(root, b["destination"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != b["sha256"]:
            raise ResourceContractError("Shared import digest drift")
    for b in receipt["imports"]:
        content = _strict_file(root, b["destination"]).read_text(encoding="utf-8")
        _check_shared_json_references(content, b, receipt["imports"], manifest)
    return receipt


def validate_shared_resource_imports(repo_root: Path) -> dict[str, list[dict]]:
    """Validate the complete finite registry, returning normalized consumer bindings."""
    repo_root = Path(repo_root)
    registry_path = repo_root / ".meta/shared-resource-imports.json"
    if not registry_path.exists() and not registry_path.is_symlink():
        # Absence grants no authority; still inspect canonical declarations below.
        registry = {"schema_version": "SharedResourceImports.v1", "imports": []}
    else:
        registry = _json_file(repo_root, ".meta/shared-resource-imports.json")
    _fields(registry, {"schema_version", "imports"}, "registry")
    if registry["schema_version"] != "SharedResourceImports.v1" or not isinstance(registry["imports"], list):
        raise ResourceContractError("Invalid shared resource registry")
    result, owners, ids, sources = {}, {}, set(), set()

    def capability(slug):
        _token(slug)
        if slug not in owners:
            text = _strict_file(repo_root, f"ssot/{slug}.md").read_text(encoding="utf-8")
            front = text.split("---", 2)
            names = re.findall(r"^name:\s*['\"]?([^'\"\n]+)['\"]?\s*$", front[1] if len(front) == 3 else "", re.M)
            if names != [slug]:
                raise ResourceContractError(f"Canonical owner/consumer name mismatch: {slug}")
            base = repo_root / "sources/capability-resources" / slug
            _strict_file(repo_root, f"sources/capability-resources/{slug}/resource-map.json")
            owners[slug] = _manifest(base, check_files=False)
        return owners[slug]

    for row in registry["imports"]:
        _fields(row, {"id", "owner", "source", "sha256", "consumers"}, "registry row")
        _binding({k: row[k] for k in ("id", "owner", "source", "sha256")} | {"destination": row["source"]})
        source_key = (row["owner"], row["source"])
        if row["id"] in ids or source_key in sources:
            raise ResourceContractError("Duplicate shared import ID or source")
        ids.add(row["id"]); sources.add(source_key)
        _, owner_map, declared, _ = capability(row["owner"])
        if row["source"] not in declared:
            raise ResourceContractError("Shared source is not owner-declared")
        raw = _strict_file(repo_root, f"sources/capability-resources/{row['owner']}/{row['source']}").read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ResourceContractError("Shared source digest drift")
        if not isinstance(row["consumers"], list) or not row["consumers"]:
            raise ResourceContractError("Shared import requires consumers")
        for consumer in row["consumers"]:
            _fields(consumer, {"slug", "destination"}, "consumer")
            capability(consumer["slug"])
            binding = {k: row[k] for k in ("id", "owner", "source", "sha256")} | {"destination": consumer["destination"]}
            result.setdefault(consumer["slug"], []).append(binding)
    _closure(list(result), {slug: [b["owner"] for b in bindings] for slug, bindings in result.items()})
    for slug, bindings in result.items():
        root, manifest, declared, _ = capability(slug)
        _bindings_check(bindings, manifest, declared)
        destinations = {b["destination"] for b in bindings}
        for relative in INFRASTRUCTURE - {"resource-map.json"}:
            p = root / relative
            if p.exists() or p.is_symlink():
                raise ResourceContractError("Authored generated infrastructure shadow")
        for b in bindings:
            target = root / b["destination"]
            if target.exists() or target.is_symlink() or any(p.is_file() or p.is_symlink() for p in target.parents if p != root and p.is_relative_to(root)):
                raise ResourceContractError("Authored local shared resource shadow")
            package = repo_root / "sources/skill-package-resources" / slug / "resources"
            for relative in [b["destination"], *INFRASTRUCTURE]:
                p = package / relative
                if p.exists() or p.is_symlink() or any(q.is_file() or q.is_symlink() for q in p.parents if q.is_relative_to(package)):
                    raise ResourceContractError("Package shared resource shadow")
            if any(o["destination"] == b["source"] for o in result.get(b["owner"], [])):
                raise ResourceContractError("Shared source cannot be reexported")
            owner_root, owner_map, _, _ = capability(b["owner"])
            dependencies = _closure([b["source"]], owner_map["dependencies"])[:-1]
            for dep in dependencies:
                if not any(x["owner"] == b["owner"] and x["source"] == dep and x["destination"] == dep for x in bindings):
                    raise ResourceContractError("Missing explicit shared dependency binding")
                if dep not in _closure([b["destination"]], manifest["dependencies"]):
                    raise ResourceContractError("Missing consumer dependency edge")
            content = _strict_file(owner_root, b["source"]).read_text(encoding="utf-8")
            _check_references(content, set(_closure([b["source"]], owner_map["dependencies"])), b["source"])
            _check_references(content, set(_closure([b["destination"]], manifest["dependencies"])), b["source"])
            _check_shared_json_references(content, b, bindings, manifest, owner_map)
        for relative in declared - destinations:
            _strict_file(root, relative)
        result[slug] = sorted(bindings, key=lambda b: b["id"])
    for receipt_path in (repo_root / "sources/capability-resources").glob("*/shared-resource-imports.json"):
        raise ResourceContractError(f"Canonical source contains generated receipt: {receipt_path}")
    for manifest_path in (repo_root / "sources/capability-resources").glob("*/resource-map.json"):
        if manifest_path.parent.name not in owners:
            data = _json_file(repo_root, manifest_path.relative_to(repo_root).as_posix())
            if data.get("shared_imports"):
                capability(manifest_path.parent.name)
    for slug, (root, manifest, declared, _) in owners.items():
        if (root / "shared-resource-imports.json").exists() or (root / "shared-resource-imports.json").is_symlink():
            raise ResourceContractError("Canonical source contains generated receipt")
        imported_paths = {b["destination"] for b in result.get(slug, [])}
        for relative in declared - imported_paths:
            _strict_file(root, relative)
        if set(manifest.get("shared_imports", [])) != {b["id"] for b in result.get(slug, [])}:
            raise ResourceContractError("Unmatched shared import declaration")
    return result


def load_resource_bundle(resource_root: Path, route: str = "all", *, entry_text: str | None = None) -> dict:
    """Return complete ordered content and byte hashes for a validated route."""
    root, manifest, declared, manifest_sha256 = _manifest(resource_root)
    if manifest.get("shared_imports"):
        _strict_file(Path(resource_root), "resource-map.json")
    receipt = _local_receipt(root, manifest, declared)
    return _assemble(root, manifest, declared, manifest_sha256, route, entry_text, {}, receipt)


def _assemble(root, manifest, declared, manifest_sha256, route, entry_text, imported, receipt):
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
            raw = imported[relative] if relative in imported else _file(root, relative).read_bytes()
            content = raw.decode("utf-8")
        except (OSError, UnicodeError) as error:
            raise ResourceContractError(f"Cannot read UTF-8 resource: {relative}") from error
        _check_references(content, set(ordered), relative)
        item = {"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "content": content}
        if receipt is not None:
            binding = next((b for b in receipt["imports"] if b["destination"] == relative), None)
            if binding is not None:
                item["source_path"] = f"sources/capability-resources/{binding['owner']}/{binding['source']}"
        resources.append(item)
    identity = {"schema_version": BUNDLE_SCHEMA, "manifest_sha256": manifest_sha256, "route": route,
                "resources": [{"path": item["path"], "sha256": item["sha256"]} for item in resources]}
    if receipt is not None:
        identity["shared_imports"] = receipt
    result = {
        "schema_version": BUNDLE_SCHEMA,
        "route": route,
        "manifest_sha256": manifest_sha256,
        "resources": resources,
        "sha256": hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "delivery_claim": "assembled_not_proof_of_consumption",
    }
    if receipt is not None:
        result["shared_imports"] = receipt
    return result


def load_capability_bundle(repo_root: Path, slug: str, entry_text: str, route: str = "all") -> dict | None:
    """Load a canonical package; missing declared manifests never become legacy fallback."""
    if not slug or "/" in slug or "\\" in slug or slug in {".", ".."}:
        raise ResourceContractError(f"Invalid capability slug: {slug!r}")
    root = Path(repo_root) / "sources" / "capability-resources" / slug
    receipt_path = root / "shared-resource-imports.json"
    if receipt_path.exists() or receipt_path.is_symlink():
        raise ResourceContractError("Canonical source contains generated receipt")
    manifest_path = root / "resource-map.json"
    if not manifest_path.exists() and not manifest_path.is_symlink():
        if "resource-map.json" in entry_text or "CapabilityResourceMap.v1" in entry_text:
            raise ResourceContractError(f"Declared resource-map.json is missing for capability: {slug}")
        return None
    registry = validate_shared_resource_imports(repo_root)
    bindings = registry.get(slug, [])
    root, manifest, declared, digest = _manifest(root, check_files=False)
    _bindings_check(bindings, manifest, declared)
    if not bindings:
        return load_resource_bundle(root, route, entry_text=entry_text)
    imported = {b["destination"]: _strict_file(Path(repo_root), f"sources/capability-resources/{b['owner']}/{b['source']}").read_bytes() for b in bindings}
    for binding in bindings:
        if hashlib.sha256(imported[binding["destination"]]).hexdigest() != binding["sha256"]:
            raise ResourceContractError("Shared source changed during assembly")
    receipt = {"schema_version": "SharedResourceImportReceipt.v1", "consumer": slug, "imports": bindings}
    return _assemble(root, manifest, declared, digest, route, entry_text, imported, receipt)


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
