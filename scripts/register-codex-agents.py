from __future__ import annotations

import re
import sys
from pathlib import Path


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


def main() -> int:
    if len(sys.argv) < 4:
        raise SystemExit("usage: register-codex-agents.py <config_path> <target_root> <slug> [<slug> ...]")

    config_path = Path(sys.argv[1]).expanduser()
    target_root = Path(sys.argv[2]).expanduser().resolve()
    agent_slugs = sorted(set(sys.argv[3:]))

    start_marker = "# >>> core-prompts codex agents start >>>"
    end_marker = "# <<< core-prompts codex agents end <<<"

    if config_path.exists():
        original = config_path.read_text(encoding="utf-8")
    else:
        original = ""

    lines = original.splitlines() if original else []
    managed_section_headers = {f"[agents.{slug}]" for slug in agent_slugs}
    cleaned_lines = drop_legacy_managed_agent_stanzas(
        lines,
        start_marker,
        end_marker,
        managed_section_headers,
    )

    managed = [start_marker]
    for slug in agent_slugs:
        config_file = target_root / ".codex" / "agents" / f"{slug}.toml"
        managed.extend(
            [
                f"[agents.{slug}]",
                f'config_file = "{config_file}"',
                "",
            ]
        )
    managed.append(end_marker)

    managed_text = "\n".join(managed)
    prefix = "\n".join(cleaned_lines).rstrip("\n")
    updated = prefix + ("\n\n" if prefix else "") + managed_text + "\n"

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
