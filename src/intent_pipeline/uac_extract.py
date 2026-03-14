"""Extract analysis text from prompt wrappers such as TOML or JSON command files."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tomllib


@dataclass(frozen=True, slots=True)
class UacExtraction:
    analysis_text: str
    wrapper_kind: str
    prompt_field: str | None = None

    def as_payload(self) -> dict[str, str | None]:
        return {
            "wrapper_kind": self.wrapper_kind,
            "prompt_field": self.prompt_field,
        }


def extract_uac_analysis_text(raw_text: str, source_name: str) -> UacExtraction:
    suffix = Path(source_name).suffix.casefold()
    if suffix == ".toml":
        extraction = _extract_from_toml(raw_text)
        if extraction is not None:
            return extraction
    if suffix == ".json":
        extraction = _extract_from_json(raw_text)
        if extraction is not None:
            return extraction
    if suffix in {".md", ".markdown"}:
        extraction = _extract_from_markdown(raw_text)
        if extraction is not None:
            return extraction
    return UacExtraction(analysis_text=raw_text, wrapper_kind="raw_text")


def _extract_from_toml(raw_text: str) -> UacExtraction | None:
    try:
        payload = tomllib.loads(raw_text)
    except Exception:
        return None
    for key in ("prompt", "system_prompt", "developer_instructions"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return UacExtraction(analysis_text=value.strip(), wrapper_kind="toml_prompt", prompt_field=key)
    return None


def _extract_from_json(raw_text: str) -> UacExtraction | None:
    try:
        payload = json.loads(raw_text)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    for key in ("prompt", "system_prompt", "developer_instructions"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return UacExtraction(analysis_text=value.strip(), wrapper_kind="json_prompt", prompt_field=key)
    return None


def _extract_from_markdown(raw_text: str) -> UacExtraction | None:
    if not raw_text.startswith("---\n"):
        return None
    end = raw_text.find("\n---", 3)
    if end == -1:
        return None
    remainder = raw_text[end + 4 :]
    if remainder.startswith("\n"):
        remainder = remainder[1:]
    normalized = remainder.strip()
    if not normalized:
        return None
    return UacExtraction(analysis_text=normalized, wrapper_kind="frontmatter_markdown")


__all__ = ["UacExtraction", "extract_uac_analysis_text"]
