"""Portable, read-only identities for explicitly pinned first-party releases.

The catalog is shipped with the current installer. Never load historical
identity claims from the installation being inspected. Matching a package's
complete membership, file modes, and bytes remains the caller's responsibility.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re

CATALOG_PATH = ".meta/install-profiles/legacy-installations.json"
SUCCESSORS = {
    "address-code-review": "engos-delivery-address-code-review",
    "analyze-context": "engos-memory-context-continuity",
    "architecture": "engos-design-architecture",
    "auto-research": "engos-optimization-auto-research",
    "autosearch": "engos-optimization-auto-research",
    "batman": "engos-orchestration-batman",
    "code-review": "engos-quality-code-review",
    "codebase-health-audit": "engos-audit-code-health",
    "converge": "engos-reconciliation-converge",
    "demo-recorder": "engos-browser-demo-recorder",
    "docs-review-expert": "engos-quality-docs-review",
    "dynamic-html-presentations": "engos-content-dynamic-html-presentations",
    "eng-report": "engos-audit-engineering-progress",
    "feature-status": "engos-audit-feature-status",
    "gitops-review": "engos-quality-gitops-review",
    "ic-assistant": "engos-operations-ic-assistant",
    "instruction-editor": "engos-meta-instruction-editor",
    "pitch": "engos-audit-pitch-review",
    "plan-to-goal-design": "engos-design-plan-to-goal",
    "pulse": "engos-triage-my-inbox-chat-pulse",
    "resolve-conflict": "engos-delivery-resolve-conflict",
    "supercharge": "engos-meta-supercharge",
    "testing": "engos-quality-testing-review",
    "threader": "engos-memory-threader",
    "uac-import": "engos-meta-uac-import",
    "weekly-intel": "engos-audit-weekly-intel",
    "mentor": None,
}
SUCCESSORS.update({slug: slug for slug in tuple(SUCCESSORS.values()) if slug})
SUCCESSORS["engos-audit-opex-incident-review"] = "engos-audit-opex-incident-review"
PROVIDERS = {"codex": "toml", "gemini": "md", "claude": "md", "kiro": "json", "grok": None}


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(f"invalid legacy catalog: {message}")


def _path(value: object) -> bool:
    return (isinstance(value, str) and bool(value) and "\\" not in value
            and ":" not in value and not any(ord(c) < 32 for c in value)
            and not value.startswith("/") and PurePosixPath(value).as_posix() == value
            and all(p not in ("", ".", "..") for p in value.split("/")))


def validate_catalog(data: dict) -> dict:
    """Reject malformed paths and identities before any installation inspection."""
    _require(isinstance(data, dict) and type(data.get("schema")) is int and data["schema"] == 1, "schema")
    for key, kind in (("releases", dict), ("identities", dict), ("packages", list),
                      ("runtime", dict), ("launchers", dict)):
        _require(isinstance(data.get(key), kind), key)
    releases = data["releases"]
    for tag, release in releases.items():
        _require(isinstance(tag, str) and re.fullmatch(r"v1\.\d+(?:\.\d+)?", tag) is not None, "release tag")
        _require(isinstance(release, dict), "release object")
        for key in ("commit", "tag_object"):
            _require(isinstance(release.get(key), str) and re.fullmatch(r"[0-9a-f]{40}", release[key]) is not None, key)
    identities = data["identities"]
    for key, item in identities.items():
        _require(isinstance(key, str) and bool(key) and isinstance(item, dict), "identity")
        _require(isinstance(item.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None, "sha256")
        _require(type(item.get("mode")) is int and item["mode"] in (0o644, 0o755), "mode")
    for spec in data["packages"]:
        _require(isinstance(spec, dict), "package")
        provider, kind, slug = (spec.get(k) for k in ("provider", "kind", "slug"))
        _require(isinstance(provider, str) and provider in PROVIDERS, "provider")
        _require(isinstance(slug, str) and slug in SUCCESSORS, "first-party slug")
        _require(spec.get("successor") == SUCCESSORS[slug], "successor")
        roots = spec.get("roots")
        if kind == "skill":
            expected = [f".{provider}/skills/{slug}"]
            entry = expected[0] + "/SKILL.md"
        else:
            _require(kind == "agent" and PROVIDERS[provider] is not None, "kind")
            entry = f".{provider}/agents/{slug}.{PROVIDERS[provider]}"
            expected = [entry, f".{provider}/agents/resources/{slug}"]
        _require(isinstance(roots, list) and (roots == expected or (kind == "agent" and roots == expected[:1])), "roots")
        files = spec.get("files")
        _require(isinstance(files, dict) and entry in files, "package entrypoint")
        for name, identity in files.items():
            _require(_path(name) and any(name == root or name.startswith(root + "/") for root in roots), "package path")
            _require(isinstance(identity, str) and identity in identities, "package identity")
        tags = spec.get("releases")
        _require(isinstance(tags, list) and bool(tags) and all(isinstance(t, str) and t in releases for t in tags), "package releases")
    for section in ("runtime", "launchers"):
        for name, ids in data[section].items():
            _require(_path(name), "runtime path")
            if section == "launchers":
                _require(name == "update_core_prompts.sh", "launcher path")
            _require(isinstance(ids, list) and bool(ids) and all(isinstance(i, str) and i in identities for i in ids), "runtime identity")
    return data


def load_catalog(repo: Path) -> dict:
    """Load the trusted current bundle's catalog; no Git or target state needed."""
    try:
        return validate_catalog(json.loads((repo / CATALOG_PATH).read_text()))
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"cannot load legacy catalog: {exc}") from exc


def packages(catalog: dict) -> list[dict]:
    return [{**spec, "files": {name: dict(catalog["identities"][identity])
                              for name, identity in spec["files"].items()}}
            for spec in catalog["packages"]]


def runtime_identities(catalog: dict, rel: str) -> list[dict]:
    ids = catalog["runtime"].get(rel, []) + catalog["launchers"].get(rel, [])
    return [dict(catalog["identities"][identity]) for identity in dict.fromkeys(ids)]
