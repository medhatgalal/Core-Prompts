from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TEMPLATE_DIR = ".meta/capability-templates"


@dataclass(frozen=True, slots=True)
class CapabilityTemplate:
    name: str
    payload: dict[str, Any]

    @property
    def required_headings(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.payload.get("required_headings") or ())

    @property
    def preferred_headings(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.payload.get("preferred_headings") or ())

    @property
    def section_stubs(self) -> dict[str, str]:
        return {str(key): str(value) for key, value in dict(self.payload.get("section_stubs") or {}).items()}

    @property
    def benchmark_dimensions(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.payload.get("benchmark_dimensions") or ())

    @property
    def minimum_word_count(self) -> int:
        return int(self.payload.get("minimum_word_count") or 0)


def capability_template_dir(repo_root: Path) -> Path:
    return repo_root / TEMPLATE_DIR


def load_capability_template(repo_root: Path, capability_type: str) -> CapabilityTemplate:
    normalized = capability_type if capability_type in {"skill", "agent", "both"} else "skill"
    path = capability_template_dir(repo_root) / f"{normalized}.json"
    if not path.exists():
        raise FileNotFoundError(f"capability template not found: {path}")
    return CapabilityTemplate(name=normalized, payload=json.loads(path.read_text(encoding="utf-8")))


__all__ = [
    "CapabilityTemplate",
    "TEMPLATE_DIR",
    "capability_template_dir",
    "load_capability_template",
]
