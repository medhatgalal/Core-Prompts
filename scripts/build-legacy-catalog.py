#!/usr/bin/env python3
"""Build historical identities from the reviewed, dual-provider release pin set.

Development-only: Git supplies the complete trees and immutable blob bytes.
Installed migration uses core_install.catalog and this generated JSON without Git.
No historical script is executed; launcher heredocs and bundle root literals are
read as data. Regeneration never discovers or implicitly trusts new local tags.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

from core_install.catalog import CATALOG_PATH, PROVIDERS, SUCCESSORS, validate_catalog

PIN_PATH = ".meta/install-profiles/legacy-release-refs.json"


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def verified_releases(repo: Path, refs: dict) -> dict:
    """Check BOTH tag object and peeled commit against the reviewed pin set."""
    releases = {}
    for ref in sorted(refs):
        if not re.fullmatch(r"refs/tags/v1\.\d+(?:\.\d+)?", ref):
            continue
        tag_object = git(repo, "rev-parse", "--verify", ref).decode().strip()
        if tag_object != refs[ref]:
            raise ValueError(f"tag object differs from reviewed release pin: {ref}")
        commit = git(repo, "rev-parse", "--verify", ref + "^{commit}").decode().strip()
        if commit != refs.get(ref + "^{}", refs[ref]):
            raise ValueError(f"peeled commit differs from reviewed release pin: {ref}")
        releases[ref.removeprefix("refs/tags/")] = {"commit": commit, "tag_object": tag_object}
    if not releases:
        raise ValueError("reviewed release pin set contains no v1 releases")
    return releases


def tree(repo: Path, commit: str) -> dict:
    entries = {}
    for row in git(repo, "ls-tree", "-r", "-z", commit).split(b"\0"):
        if not row:
            continue
        meta, path = row.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        if kind == "blob" and mode in ("100644", "100755"):
            entries[path.decode()] = (oid, int(mode[-3:], 8))
    return entries


def read_blobs(repo: Path, oids: set[str]) -> dict[str, bytes]:
    ordered = sorted(oids)
    if not ordered:
        return {}
    output = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"],
                            input=("\n".join(ordered) + "\n").encode(),
                            stdout=subprocess.PIPE, check=True).stdout
    found, offset = {}, 0
    for oid in ordered:
        end = output.index(b"\n", offset)
        actual, kind, size = output[offset:end].split()
        if actual.decode() != oid or kind != b"blob":
            raise ValueError(f"unexpected Git object: {oid}")
        length = int(size)
        found[oid] = output[end + 1:end + 1 + length]
        offset = end + 2 + length
    return found


def bundle_roots(script: str) -> list[str]:
    """Literal deployed roots, including releases predating install-bundle.json."""
    function = script.partition("standalone_bundle_entries() {")[2]
    match = re.search(r"(?m)^roots = (\[.*?^\])", function, re.S)
    if match:
        roots = ast.literal_eval(match[1])
        if isinstance(roots, list) and all(isinstance(r, str) for r in roots):
            return roots
        raise ValueError("unsupported historical bundle root declaration")
    # Earlier releases still supply trusted identities for first-party surfaces
    # and metadata. A caller must match actual runtime files individually.
    return [f".{p}" for p in PROVIDERS] + [
        ".meta/manifest.json", ".meta/capability-handoff.json", ".meta/capabilities",
        ".meta/install-bundle.json", ".meta/install-profiles", "dist/consumer-shell",
        "sources/ssot-baselines", "scripts/deploy-copy-plan.py", "scripts/deploy-profile.py",
        "scripts/register-codex-agents.py", "scripts/deploy-surfaces.sh", "scripts/install-local.sh",
        "scripts/update-core-prompts.py", "VERSION", "RELEASE_SOURCE.env",
    ]


def launcher(script: str) -> bytes | None:
    section = script.partition("write_launcher() {")[2].partition("\n}\n")[0]
    match = re.search(r"cat > \"\$dst\" <<'EOF'\n(.*?)\nEOF\n", section, re.S)
    if match and 'chmod 755 "$dst"' in section:
        return (match[1] + "\n").encode()
    return None


def build(repo: Path) -> dict:
    pins = json.loads((repo / PIN_PATH).read_text())
    releases = verified_releases(repo, pins["refs"])
    result = {"schema": 1, "releases": releases, "identities": {}, "packages": [],
              "runtime": {}, "launchers": {}}
    blobs, identity_keys, package_versions = {}, {}, {}

    def identity(content: bytes, mode: int) -> str:
        digest = hashlib.sha256(content).hexdigest()
        key = (digest, mode)
        if key not in identity_keys:
            ident = f"i{len(identity_keys):05x}"
            identity_keys[key] = ident
            result["identities"][ident] = {"sha256": digest, "mode": mode}
        return identity_keys[key]

    for tag, release in releases.items():
        entries = tree(repo, release["commit"])
        script_rel = "scripts/deploy-surfaces.sh"
        script = git(repo, "show", f"{release['commit']}:{script_rel}").decode() if script_rel in entries else ""
        roots = bundle_roots(script)
        selected = {p for p in entries if any(p == r or p.startswith(r + "/") for r in roots)
                    and not p.endswith("/.DS_Store")}
        # Enumerate complete tree membership, not merely manifest entrypoints.
        candidates = []
        for provider, suffix in PROVIDERS.items():
            for slug, successor in sorted(SUCCESSORS.items()):
                skill_root = f".{provider}/skills/{slug}"
                if skill_root + "/SKILL.md" in entries:
                    candidates.append((provider, "skill", slug, successor, [skill_root]))
                entry = f".{provider}/agents/{slug}.{suffix}"
                if suffix and entry in entries:
                    resources = f".{provider}/agents/resources/{slug}"
                    agent_roots = [entry]
                    if any(p.startswith(resources + "/") for p in entries):
                        agent_roots.append(resources)
                    candidates.append((provider, "agent", slug, successor, agent_roots))
        package_files = []
        for provider, kind, slug, successor, roots in candidates:
            names = sorted(p for p in entries if any(p == r or p.startswith(r + "/") for r in roots))
            selected.update(names)
            package_files.append((provider, kind, slug, successor, roots, names))
        blobs.update(read_blobs(repo, {entries[p][0] for p in selected} - blobs.keys()))
        file_ids = {p: identity(blobs[entries[p][0]], entries[p][1]) for p in sorted(selected)}
        for p, ident in file_ids.items():
            values = result["runtime"].setdefault(p, [])
            if ident not in values:
                values.append(ident)
        for provider, kind, slug, successor, roots, names in package_files:
            spec = {"provider": provider, "kind": kind, "slug": slug, "successor": successor,
                    "roots": roots, "files": {p: file_ids[p] for p in names}}
            key = json.dumps(spec, sort_keys=True)
            if key not in package_versions:
                package_versions[key] = {**spec, "releases": []}
            package_versions[key]["releases"].append(tag)
        content = launcher(script)
        if content:
            ident = identity(content, 0o755)
            values = result["launchers"].setdefault("update_core_prompts.sh", [])
            if ident not in values:
                values.append(ident)
    result["packages"] = list(package_versions.values())
    return validate_catalog(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true", help="verify generated bytes without writing")
    args = parser.parse_args()
    data = build(args.repo)
    rendered = json.dumps(data, indent=2, sort_keys=True) + "\n"
    output = args.repo / CATALOG_PATH
    if args.check:
        if output.read_text() != rendered:
            raise SystemExit("historical catalog is stale; run scripts/build-legacy-catalog.py")
    else:
        output.write_text(rendered)
    print(f"legacy catalog: {len(data['releases'])} releases, {len(data['packages'])} package versions, "
          f"{len(data['identities'])} unique identities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
