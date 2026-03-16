from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from intent_pipeline.uac_sources import UacSourceCandidate


PROMPT_INCLUDE_PATTERNS = (
    "**/commands/**/*.toml",
    "**/prompts/**/*.md",
    "**/skills/**/*.md",
    "**/agents/**/*.md",
    "**/agents/**/*.toml",
    "**/agents/**/*.json",
    "**/SKILL.md",
)
PROMPT_IGNORE_PATTERNS = (
    "**/node_modules/**",
    "**/.git/**",
    "**/dist/**",
    "**/build/**",
    "**/.venv/**",
)


@dataclass(frozen=True, slots=True)
class RepomixCandidate:
    path: str
    content: str


def repomix_available() -> bool:
    return shutil.which("repomix") is not None


def collect_repomix_candidates(source: str, *, max_items: int = 50) -> list[RepomixCandidate]:
    if not repomix_available():
        return []
    command = [
        "repomix",
        "--style",
        "json",
        "--stdout",
        "--include",
        ",".join(PROMPT_INCLUDE_PATTERNS),
        "--ignore",
        ",".join(PROMPT_IGNORE_PATTERNS),
    ]
    if source.startswith("http://") or source.startswith("https://") or "/" in source and not Path(source).exists():
        command.extend(["--remote", source])
    else:
        command.append(source)
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=45, check=True)
    except Exception:
        return []
    try:
        payload = json.loads(proc.stdout)
    except Exception:
        return []
    files = payload.get("files") or {}
    candidates: list[RepomixCandidate] = []
    for path, content in files.items():
        if not isinstance(path, str) or not isinstance(content, str):
            continue
        candidates.append(RepomixCandidate(path=path, content=content))
        if len(candidates) >= max_items:
            break
    return candidates


def to_uac_candidates(candidates: Iterable[RepomixCandidate], *, source_label: str) -> list[UacSourceCandidate]:
    output: list[UacSourceCandidate] = []
    for candidate in candidates:
        output.append(
            UacSourceCandidate(
                source_type="REPOMIX_FILE",
                display_name=candidate.path,
                normalized_source=f"repomix://{source_label}/{candidate.path}",
                locator=candidate.path,
            )
        )
    return output


def materialize_repomix_candidate(candidate: RepomixCandidate) -> Path:
    suffix = Path(candidate.path).suffix or ".txt"
    tmp = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    with tmp:
        tmp.write(candidate.content)
    return Path(tmp.name)
