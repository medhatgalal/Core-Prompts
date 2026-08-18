from __future__ import annotations

import re
from copy import deepcopy
from collections.abc import Iterable, Mapping
from typing import Any


HEADING = re.compile(r"^(#{2,4})\s+(.+?)\s*$")
TABLE_COMMAND = re.compile(r"^\|\s*`([^`]+)`\s*\|")
MODULE_HEADING = re.compile(r"^(?:Nested\s+)?Module:\s*(.+)$", re.I)
NUMBERED_PREFIX = re.compile(r"^(?:\d+(?:\.\d+)*\.?\s+|Mode\s+\d+\s*:\s*)", re.I)


def _clean_label(value: str) -> str:
    return re.sub(r"[`*]", "", value).strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _invocation(value: str) -> str | None:
    commands = re.findall(r"/[a-z][a-z0-9-]*", value, re.I)
    return " ".join(commands) if commands else None


def _entry(
    *,
    slug: str,
    label: str,
    kind: str,
    source_line: int,
    invocations: list[str] | None = None,
) -> dict[str, Any]:
    display_name = NUMBERED_PREFIX.sub("", _clean_label(label)).strip()
    canonical_invocations = list(dict.fromkeys(invocations or []))
    identity = display_name if kind == "command" else (canonical_invocations[-1] if canonical_invocations else display_name)
    return {
        "mode_slug": _slug(identity),
        "display_name": display_name,
        "entry_kind": kind,
        "invocations": canonical_invocations,
        "source_refs": [f"ssot/{slug}.md"],
        "source_line": source_line,
        "mode_summary": f"Explicitly declared {kind} in the canonical skill.",
        "required_inputs": [],
        "expected_outputs": [],
        "examples": [],
        "uplift_notes": ["Composition and state rules belong to CapabilityTopology.v1."],
    }


def extract_declared_modes(slug: str, body: str) -> list[dict[str, Any]]:
    """Return only explicitly declared modes, modules, and command entries.

    General headings, examples, workflow steps, and prose mentions are ignored.
    Table variants with the same base command are combined into one entry.
    """
    entries: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    active_section: str | None = None

    def add(entry: dict[str, Any]) -> None:
        if not entry["mode_slug"]:
            return
        key = (str(entry["entry_kind"]), str(entry["mode_slug"]))
        existing = seen.get(key)
        if existing:
            existing["invocations"] = list(dict.fromkeys([*existing["invocations"], *entry["invocations"]]))
            return
        seen[key] = entry
        entries.append(entry)

    for number, line in enumerate(body.splitlines(), start=1):
        heading = HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            label = _clean_label(heading.group(2))
            module = MODULE_HEADING.match(label)
            if module:
                module_label = module.group(1).strip()
                invocation = _invocation(module_label.split("—", 1)[0])
                add(
                    _entry(
                        slug=slug,
                        label=module_label,
                        kind="module",
                        source_line=number,
                        invocations=[invocation] if invocation else [],
                    )
                )
            if level == 2:
                normalized = NUMBERED_PREFIX.sub("", label).strip().lower()
                if normalized in {"modes", "operating modes", "modes of operation"}:
                    active_section = "mode"
                elif normalized == "commands":
                    active_section = "command"
                elif normalized == "invocation":
                    active_section = "invocation_table"
                else:
                    active_section = None
                continue
            if level == 3 and active_section in {"mode", "command"}:
                invocation = _invocation(label)
                add(
                    _entry(
                        slug=slug,
                        label=label,
                        kind=active_section,
                        source_line=number,
                        invocations=[invocation] if invocation else [],
                    )
                )
            continue

        if active_section == "invocation_table":
            command_match = TABLE_COMMAND.match(line)
            if not command_match:
                continue
            full_invocation = _clean_label(command_match.group(1))
            parts = full_invocation.split()
            if not parts or parts[0].lower() != slug.lower():
                continue
            slash = next((part for part in parts[1:] if part.startswith("/")), None)
            canonical = f"{slug} {slash}" if slash else slug
            add(
                _entry(
                    slug=slug,
                    label=slash or "default",
                    kind="command",
                    source_line=number,
                    invocations=[full_invocation, canonical],
                )
            )
    return entries


def normalize_mode_entries(entries: Iterable[Mapping[str, Any]], slug: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in entries:
        entry = deepcopy(dict(raw))
        entry.setdefault("entry_kind", "mode")
        entry.setdefault("invocations", [])
        entry.setdefault("source_refs", [f"ssot/{slug}.md"])
        normalized.append(entry)
    return normalized
