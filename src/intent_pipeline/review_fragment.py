"""Check the shared recommendation review text in expanded SSOT files."""
from __future__ import annotations

import json
import re
from pathlib import Path

FRAGMENT = Path("ssot/fragments/recommendation-artifact-review.md")
RULES = Path(".meta/surface-rules.json")
SECTION = b"## Recommendation Artifact Review"
ROLES = b"### Three Roles"
CYCLE = b"### Finding and Repair Cycle"
HEADING = re.compile(rb"^#{1,3} [^\r\n]+$", re.MULTILINE)


def consumers(root: Path) -> list[str]:
    names = json.loads((root / RULES).read_bytes()).get("review_fragment_consumers")
    if (not isinstance(names, list) or not names
            or not all(isinstance(n, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", n) for n in names)
            or len(set(names)) != len(names)):
        raise ValueError(f"Invalid review_fragment_consumers in {RULES}")
    return names


def authored_fragment(root: Path) -> bytes:
    content = (root / FRAGMENT).read_bytes()
    headings = HEADING.findall(content)
    if (headings != [ROLES, CYCLE] or not content.startswith(ROLES + b"\n")
            or not content.endswith(b"\n") or content.endswith(b"\n\n")):
        raise ValueError(f"Expected the two review subsections and one final newline in {FRAGMENT}")
    return content


def review_slot(slug: str, raw: bytes) -> tuple[int, int]:
    headings = list(HEADING.finditer(raw))
    sections = [heading for heading in headings if heading[0] == SECTION]
    if len(sections) != 1:
        raise ValueError(f"{slug}: expected one recommendation review section")
    start = sections[0].end()
    boundary = next((h.start() for h in headings if h.start() > start and not h[0].startswith(b"### ")), len(raw))
    subsections = [h for h in headings if start < h.start() < boundary]
    titles = [h[0] for h in subsections]
    if (titles.count(ROLES) != 1 or titles.count(CYCLE) != 1
            or titles.index(CYCLE) != titles.index(ROLES) + 1):
        raise ValueError(f"{slug}: missing, duplicated or misplaced review headings")
    first = subsections[titles.index(ROLES)].start()
    after_cycle = titles.index(CYCLE) + 1
    if after_cycle < len(subsections):
        boundary = subsections[after_cycle].start()
    end = first + len(raw[first:boundary].rstrip(b"\n"))
    if raw[end:end + 1] != b"\n":
        raise ValueError(f"{slug}: missing final newline in shared review text")
    return first, end + 1


def check_copy(slug: str, raw: bytes, fragment: bytes) -> None:
    start, end = review_slot(slug, raw)
    if raw[start:end] != fragment:
        raise ValueError(f"{slug}: shared review text differs from {FRAGMENT}")


def check_candidate(root: Path, slug: str, text: str) -> None:
    # Isolated UAC callers can supply a source without a checkout or a policy.
    # A checkout with missing declarations must still fail closed.
    if not any((root / path).exists() for path in (RULES, FRAGMENT, "scripts/build-surfaces.py")):
        return
    if slug in consumers(root):
        # UAC persists one final newline when the selected candidate omits it.
        check_copy(slug, (text if text.endswith("\n") else text + "\n").encode(), authored_fragment(root))


def check_materializations(root: Path) -> None:
    fragment = authored_fragment(root)
    for slug in consumers(root):
        check_copy(slug, (root / "ssot" / f"{slug}.md").read_bytes(), fragment)
