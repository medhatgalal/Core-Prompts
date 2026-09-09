#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import stat
import sys
from pathlib import Path


# A successor is selected only after ``legacy_owned`` proves that the entire
# installed package is an unchanged member of the old standalone bundle.  The
# installed bundle determines which historical generation is present: the
# v1.12.2 population has 24 entries; plan-to-goal-design is discovered only
# from later bundles that actually contain it.
LEGACY_NAMESPACE_SLUGS = {
    "address-code-review": "engos-delivery-address-code-review",
    "analyze-context": "engos-memory-context-continuity",
    "architecture": "engos-design-architecture",
    "auto-research": "engos-optimization-auto-research",
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
}
RETIRED_LEGACY_SLUGS = {"mentor"}
CLI_ROOTS = {
    "codex": ".codex/skills",
    "gemini": ".gemini/skills",
    "claude": ".claude/skills",
    "kiro": ".kiro/skills",
}


def legacy_surface_paths(cli: str, slug: str) -> list[str]:
    """Return the closed set of historical package roots for one identity."""
    skill_root = CLI_ROOTS.get(cli)
    if skill_root is None:
        return []
    if cli == "codex":
        return [f"{skill_root}/{slug}", f".codex/agents/{slug}.toml", f".codex/agents/resources/{slug}"]
    if cli == "gemini":
        return [f"{skill_root}/{slug}", f".gemini/agents/{slug}.md", f".gemini/agents/resources/{slug}"]
    if cli == "claude":
        return [f"{skill_root}/{slug}", f".claude/agents/{slug}.md", f".claude/agents/resources/{slug}"]
    if cli == "kiro":
        return [f"{skill_root}/{slug}", f".kiro/agents/{slug}.json", f".kiro/agents/resources/{slug}"]
    return [f"{skill_root}/{slug}"]


def legacy_owned(target: Path, relative: str) -> bool:
    """Read-only proof for an exact old namespace path before retiring it."""
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts or len(rel.parts) < 3 or rel.parts[0] not in {'.codex', '.kiro', '.claude', '.gemini'}:
        return False
    prior = target / '.core-prompts-updater'
    current = target / rel
    def regular_tree(path):
        for parent in [path, *path.parents]:
            if parent.is_symlink():
                return None
            if parent == target:
                break
        if path.is_file():
            return {path}
        if not path.is_dir():
            return None
        found = set()
        for item in path.rglob('*'):
            if item.is_symlink():
                return None
            if item.is_file():
                found.add(item)
        return found
    try:
        if regular_tree(prior / '.meta/manifest.json') is None:
            return False
        manifest = json.loads((prior / '.meta/manifest.json').read_text())
        declared = {name for group in ('surfaces', 'resources')
                    for names in manifest.get(group, {}).values() for name in names}
        actual = regular_tree(current)
        original = regular_tree(prior / rel)
        if not actual or not original:
            return False
        actual_names = {p.relative_to(target).as_posix() for p in actual}
        prior_names = {p.relative_to(prior).as_posix() for p in original}
        if actual_names != prior_names or not actual_names <= declared:
            return False
        for name in actual_names:
            a, b = target / name, prior / name
            if (hashlib.sha256(a.read_bytes()).digest() != hashlib.sha256(b.read_bytes()).digest()
                    or stat.S_IMODE(a.stat().st_mode) != stat.S_IMODE(b.stat().st_mode)):
                return False
        return True
    except (OSError, ValueError, TypeError):
        return False


def legacy_successors(target: Path, clients: list[str]) -> list[str]:
    """Return only proven legacy successors (and the retired mentor marker).

    This deliberately probes a closed set of exact package paths.  It never
    scans a skills root, infers ownership from a name, or treats matching bytes
    without the prior standalone manifest as provenance.
    """
    result = set()
    for cli in clients:
        for old_slug, successor in LEGACY_NAMESPACE_SLUGS.items():
            if any(legacy_owned(target, path) for path in legacy_surface_paths(cli, old_slug)):
                result.add(successor)
        for old_slug in RETIRED_LEGACY_SLUGS:
            if any(legacy_owned(target, path) for path in legacy_surface_paths(cli, old_slug)):
                result.add(old_slug)
    return sorted(result)


def main(argv: list[str]) -> int:
    if argv and argv[0] == '--check-legacy-owned':
        return 0 if len(argv) == 3 and legacy_owned(Path(argv[1]), argv[2]) else 1
    if argv and argv[0] == '--legacy-successors':
        if len(argv) < 3:
            return 2
        print("\n".join(legacy_successors(Path(argv[1]), argv[2:])))
        return 0
    separator = argv.index("--")
    repo_root = Path(argv[0]).resolve()
    target_root = Path(argv[1]).resolve()
    selected = set(argv[2:separator])
    slug_filters = set(arg for arg in argv[separator + 1 :] if arg)
    manifest = json.loads((repo_root / ".meta" / "manifest.json").read_text(encoding="utf-8"))

    path_templates = {
        "grok_skill": [".grok/skills/{slug}/SKILL.md"],
        "gemini_skill": [".gemini/skills/{slug}/SKILL.md"],
        "gemini_agent": [".gemini/agents/{slug}.md"],
        "claude_skill": [".claude/skills/{slug}/SKILL.md"],
        "claude_agent": [".claude/agents/{slug}.md"],
        "kiro_skill": [".kiro/skills/{slug}/SKILL.md"],
        "kiro_agent": [".kiro/agents/{slug}.json"],
        "codex_skill": [".codex/skills/{slug}/SKILL.md"],
        "codex_agent": [".codex/agents/{slug}.toml"],
    }
    resource_dirs = {
        "grok_skill": ".grok/skills/{slug}/resources",
        "gemini_skill": ".gemini/skills/{slug}/resources",
        "gemini_agent": ".gemini/agents/resources/{slug}",
        "claude_skill": ".claude/skills/{slug}/resources",
        "claude_agent": ".claude/agents/resources/{slug}",
        "kiro_skill": ".kiro/skills/{slug}/resources",
        "kiro_agent": ".kiro/agents/resources/{slug}",
        "codex_skill": ".codex/skills/{slug}/resources",
        "codex_agent": ".codex/agents/resources/{slug}",
    }
    surface_cli = {
        "grok_skill": "grok",
        "gemini_skill": "gemini",
        "gemini_agent": "gemini",
        "claude_skill": "claude",
        "claude_agent": "claude",
        "kiro_skill": "kiro",
        "kiro_agent": "kiro",
        "codex_skill": "codex",
        "codex_agent": "codex",
    }

    for entry in manifest.get("ssot_sources", []):
        slug = entry.get("slug")
        if not slug:
            continue
        if slug_filters and slug not in slug_filters:
            continue
        for surface_name in entry.get("expected_surface_names", []):
            cli = surface_cli[surface_name]
            if cli not in selected:
                continue
            for template in path_templates[surface_name]:
                rel = template.format(slug=slug)
                src = repo_root / rel
                if src.exists():
                    print(f"{src}\t{target_root / rel}\t{surface_name}\t{slug}")
            for rel in manifest.get("resources", {}).get(surface_name, []):
                root = resource_dirs[surface_name].format(slug=slug)
                package = str(Path(root).parent) if surface_name.endswith("_skill") else root
                if not rel.startswith(package + "/"):
                    continue
                resource_path = repo_root / rel
                if not resource_path.is_file():
                    raise ValueError(f"missing generated resource: {rel}")
                print(f"{resource_path}\t{target_root / rel}\t{surface_name}\t{slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
