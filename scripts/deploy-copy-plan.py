#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    separator = argv.index("--")
    repo_root = Path(argv[0]).resolve()
    target_root = Path(argv[1]).resolve()
    selected = set(argv[2:separator])
    slug_filters = set(arg for arg in argv[separator + 1 :] if arg)
    manifest = json.loads((repo_root / ".meta" / "manifest.json").read_text(encoding="utf-8"))

    path_templates = {
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
            resource_root = repo_root / resource_dirs[surface_name].format(slug=slug)
            if resource_root.is_dir():
                for resource_path in sorted(path for path in resource_root.rglob("*") if path.is_file()):
                    rel = resource_path.relative_to(repo_root)
                    print(f"{resource_path}\t{target_root / rel}\t{surface_name}\t{slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
