from __future__ import annotations

import re
import sys
from pathlib import Path


START_MARKER = "# >>> core-prompts codex agents start >>>"
END_MARKER = "# <<< core-prompts codex agents end <<<"
RETIRED_AGENT_SLUGS = {"mentor"}
LEGACY_NAMESPACE_AGENT_SLUGS = {
    "engos-delivery-address-code-review": "address-code-review",
    "engos-memory-context-continuity": "analyze-context",
    "engos-design-architecture": "architecture",
    "engos-optimization-auto-research": "auto-research",
    "engos-orchestration-batman": "batman",
    "engos-quality-code-review": "code-review",
    "engos-audit-code-health": "codebase-health-audit",
    "engos-reconciliation-converge": "converge",
    "engos-browser-demo-recorder": "demo-recorder",
    "engos-quality-docs-review": "docs-review-expert",
    "engos-content-dynamic-html-presentations": "dynamic-html-presentations",
    "engos-audit-engineering-progress": "eng-report",
    "engos-audit-feature-status": "feature-status",
    "engos-quality-gitops-review": "gitops-review",
    "engos-operations-ic-assistant": "ic-assistant",
    "engos-meta-instruction-editor": "instruction-editor",
    "engos-audit-pitch-review": "pitch",
    "engos-design-plan-to-goal": "plan-to-goal-design",
    "engos-triage-my-inbox-chat-pulse": "pulse",
    "engos-delivery-resolve-conflict": "resolve-conflict",
    "engos-meta-supercharge": "supercharge",
    "engos-quality-testing-review": "testing",
    "engos-memory-threader": "threader",
    "engos-meta-uac-import": "uac-import",
    "engos-audit-weekly-intel": "weekly-intel",
}


def drop_retired_agent_stanzas(
    source_lines: list[str],
    target_root: Path,
) -> list[str]:
    retired_headers = {f"[agents.{slug}]" for slug in RETIRED_AGENT_SLUGS}
    managed_files = {
        slug: (target_root / ".codex" / "agents" / f"{slug}.toml").resolve()
        for slug in RETIRED_AGENT_SLUGS
    }
    config_file_pattern = re.compile(r'^\s*config_file\s*=\s*(["\'])(.*?)\1\s*$')
    cleaned: list[str] = []
    in_managed_block = False
    index = 0

    while index < len(source_lines):
        line = source_lines[index]
        stripped = line.strip()
        if stripped == START_MARKER:
            in_managed_block = True
            cleaned.append(line)
            index += 1
            continue
        if stripped == END_MARKER:
            in_managed_block = False
            cleaned.append(line)
            index += 1
            continue
        if stripped not in retired_headers:
            cleaned.append(line)
            index += 1
            continue

        slug = stripped.removeprefix("[agents.").removesuffix("]")
        stanza_end = index + 1
        while stanza_end < len(source_lines):
            candidate = source_lines[stanza_end].strip()
            if candidate in {START_MARKER, END_MARKER} or re.match(
                r"^\s*\[[^\]]+\]\s*$", source_lines[stanza_end]
            ):
                break
            stanza_end += 1
        stanza = source_lines[index:stanza_end]
        targets_managed_file = any(
            (match := config_file_pattern.match(candidate)) is not None
            and Path(match.group(2)).expanduser().resolve() == managed_files[slug]
            for candidate in stanza[1:]
        )
        if not in_managed_block and not targets_managed_file:
            cleaned.extend(stanza)
        index = stanza_end

    return cleaned


def drop_legacy_managed_agent_stanzas(
    source_lines: list[str],
    start_marker: str,
    end_marker: str,
    managed_section_headers: set[str],
    legacy_section_headers: set[str] | None = None,
    legacy_config_files: set[Path] | None = None,
) -> list[str]:
    legacy_section_headers = legacy_section_headers or set()
    legacy_config_files = legacy_config_files or set()
    config_file_pattern = re.compile(r'^\s*config_file\s*=\s*(["\'])(.*?)\1\s*$')
    cleaned: list[str] = []
    index = 0

    while index < len(source_lines):
        line = source_lines[index]
        stripped = line.strip()
        if stripped in {start_marker, end_marker}:
            index += 1
            continue

        if stripped in managed_section_headers or stripped in legacy_section_headers:
            stanza_end = index + 1
            while stanza_end < len(source_lines):
                candidate = source_lines[stanza_end].strip()
                if candidate == start_marker or candidate == end_marker or re.match(
                    r"^\s*\[[^\]]+\]\s*$", source_lines[stanza_end]
                ):
                    break
                stanza_end += 1
            stanza = source_lines[index:stanza_end]
            drop_stanza = stripped in managed_section_headers
            if stripped in legacy_section_headers:
                drop_stanza = any(
                    (match := config_file_pattern.match(candidate)) is not None
                    and Path(match.group(2)).expanduser().resolve() in legacy_config_files
                    for candidate in stanza[1:]
                )
            if not drop_stanza:
                cleaned.extend(stanza)
            index = stanza_end
            continue

        cleaned.append(line)
        index += 1

    return cleaned


def prune_retired_only(config_path: Path, target_root: Path) -> int:
    if not config_path.exists():
        return 0
    original = config_path.read_text(encoding="utf-8")
    cleaned_lines = drop_retired_agent_stanzas(original.splitlines(), target_root)
    updated = "\n".join(cleaned_lines).rstrip("\n")
    if updated:
        updated += "\n"
    if updated != original:
        config_path.write_text(updated, encoding="utf-8")
    return 0


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--prune-retired-only":
        return prune_retired_only(
            Path(sys.argv[2]).expanduser(),
            Path(sys.argv[3]).expanduser().resolve(),
        )
    if len(sys.argv) < 4:
        raise SystemExit(
            "usage: register-codex-agents.py <config_path> <target_root> <slug> [<slug> ...]"
            " | register-codex-agents.py --prune-retired-only <config_path> <target_root>"
        )

    config_path = Path(sys.argv[1]).expanduser()
    target_root = Path(sys.argv[2]).expanduser().resolve()
    agent_slugs = sorted(set(sys.argv[3:]) - RETIRED_AGENT_SLUGS)
    deprecated_agent_aliases = {
        "engos-optimization-auto-research": {"autosearch"},
    }

    if config_path.exists():
        original = config_path.read_text(encoding="utf-8")
    else:
        original = ""

    lines = drop_retired_agent_stanzas(
        original.splitlines() if original else [],
        target_root,
    )
    managed_section_headers = {f"[agents.{slug}]" for slug in agent_slugs}
    for slug in agent_slugs:
        for alias in deprecated_agent_aliases.get(slug, set()):
            managed_section_headers.add(f"[agents.{alias}]")
    legacy_slugs = {
        LEGACY_NAMESPACE_AGENT_SLUGS[slug]
        for slug in agent_slugs
        if slug in LEGACY_NAMESPACE_AGENT_SLUGS
    }
    legacy_section_headers = {f"[agents.{slug}]" for slug in legacy_slugs}
    legacy_config_files = {
        (target_root / ".codex" / "agents" / f"{slug}.toml").resolve()
        for slug in legacy_slugs
    }
    cleaned_lines = drop_legacy_managed_agent_stanzas(
        lines,
        START_MARKER,
        END_MARKER,
        managed_section_headers,
        legacy_section_headers,
        legacy_config_files,
    )

    managed = [START_MARKER]
    for slug in agent_slugs:
        config_file = target_root / ".codex" / "agents" / f"{slug}.toml"
        managed.extend(
            [
                f"[agents.{slug}]",
                f'config_file = "{config_file}"',
                "",
            ]
        )
    managed.append(END_MARKER)

    managed_text = "\n".join(managed)
    prefix = "\n".join(cleaned_lines).rstrip("\n")
    updated = prefix + ("\n\n" if prefix else "") + managed_text + "\n"

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
