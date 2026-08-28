from __future__ import annotations

import re
import sys
from pathlib import Path


START_MARKER = "# >>> core-prompts codex agents start >>>"
END_MARKER = "# <<< core-prompts codex agents end <<<"
RETIRED_AGENT_SLUGS = {"mentor"}


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
) -> list[str]:
    cleaned: list[str] = []
    in_managed_block = False
    skipping_legacy_stanza = False

    for line in source_lines:
        stripped = line.strip()
        if stripped == start_marker:
            in_managed_block = True
            continue
        if in_managed_block:
            if stripped == end_marker:
                in_managed_block = False
            continue

        is_section_header = bool(re.match(r"^\s*\[[^\]]+\]\s*$", line))
        if stripped in managed_section_headers:
            skipping_legacy_stanza = True
            continue
        if skipping_legacy_stanza and is_section_header:
            skipping_legacy_stanza = False
        if skipping_legacy_stanza:
            continue
        cleaned.append(line)

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
        "auto-research": {"autosearch"},
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
    cleaned_lines = drop_legacy_managed_agent_stanzas(
        lines,
        START_MARKER,
        END_MARKER,
        managed_section_headers,
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
