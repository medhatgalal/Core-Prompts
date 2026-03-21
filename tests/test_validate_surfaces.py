from __future__ import annotations

import importlib.util
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate-surfaces.py"
SPEC = importlib.util.spec_from_file_location("validate_surfaces_script", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_validate_portable_capability_metadata_rejects_absolute_local_refs(tmp_path: Path) -> None:
    path = tmp_path / "capability.json"
    path.write_text(
        """{
  "layers": {
    "minimal": {
      "resources": ["/Users/example/repo/ssot/architecture.md"],
      "source_provenance": {
        "normalized_source": "/Users/example/repo/ssot/architecture.md"
      }
    }
  }
}
""",
        encoding="utf-8",
    )

    errors = MODULE.validate_portable_capability_metadata(path)

    assert errors
    assert "absolute local source reference is not portable" in errors[0]


def test_validate_portable_capability_metadata_allows_repo_relative_refs(tmp_path: Path) -> None:
    path = tmp_path / "capability.json"
    path.write_text(
        """{
  "layers": {
    "minimal": {
      "resources": ["ssot/architecture.md"],
      "source_provenance": {
        "normalized_source": "ssot/architecture.md"
      }
    }
  }
}
""",
        encoding="utf-8",
    )

    assert MODULE.validate_portable_capability_metadata(path) == []


def test_validate_frontmatter_rejects_multiple_blocks(tmp_path: Path) -> None:
    path = tmp_path / "sample.md"
    path.write_text(
        """---
name: "sample"
description: "first"
---
---
kind: "skill"
---
# Sample
""",
        encoding="utf-8",
    )

    errors = MODULE.validate_frontmatter(path, ["name", "description"])

    assert any("multiple frontmatter blocks found" in item for item in errors)


def test_validate_toml_rejects_forbidden_tools_key(tmp_path: Path) -> None:
    path = tmp_path / "architecture.toml"
    path.write_text(
        """name = "architecture"
description = "Architecture Studio"
sandbox_mode = "workspace-write"
developer_instructions = '''
hello
'''
tools = ["Read", "Write"]
""",
        encoding="utf-8",
    )

    errors = MODULE.validate_toml(path, ["name", "description", "sandbox_mode", "developer_instructions"], "architecture", ["tools"])

    assert any("forbidden key tools" in item for item in errors)


def test_validate_toml_accepts_codex_agent_runtime_shape(tmp_path: Path) -> None:
    path = tmp_path / "converge.toml"
    path.write_text(
        """name = "converge"
description = "Universal Synthesis and Convergence"
sandbox_mode = "workspace-write"
developer_instructions = '''
hello
'''
""",
        encoding="utf-8",
    )

    errors = MODULE.validate_toml(path, ["name", "description", "sandbox_mode", "developer_instructions"], "converge", ["tools"])

    assert errors == []


def test_validate_ssot_source_rejects_descriptor_display_name_drift(tmp_path: Path) -> None:
    old_root = MODULE.ROOT
    try:
        MODULE.ROOT = tmp_path
        ssot_dir = tmp_path / "ssot"
        descriptor_dir = tmp_path / ".meta" / "capabilities"
        ssot_dir.mkdir(parents=True)
        descriptor_dir.mkdir(parents=True)
        path = ssot_dir / "sample.md"
        path.write_text(
            """---
name: "sample"
display_name: "Sample Skill"
description: "sample"
---
# Sample Skill

## Purpose
test
""",
            encoding="utf-8",
        )
        (descriptor_dir / "sample.json").write_text(
            """{
  "display_name": "Other Name",
  "layers": {"minimal": {"display_name": "Other Name"}}
}
""",
            encoding="utf-8",
        )

        errors = MODULE.validate_ssot_source(path)

        assert any("descriptor display_name drift" in item for item in errors)
    finally:
        MODULE.ROOT = old_root


def test_validate_ssot_source_rejects_missing_benchmark_sections(tmp_path: Path) -> None:
    old_root = MODULE.ROOT
    try:
        MODULE.ROOT = tmp_path
        ssot_dir = tmp_path / "ssot"
        descriptor_dir = tmp_path / ".meta" / "capabilities"
        ssot_dir.mkdir(parents=True)
        descriptor_dir.mkdir(parents=True)
        path = ssot_dir / "testing.md"
        path.write_text(
            """---
name: "testing"
description: "Testing Studio"
---
# Testing Studio

## Purpose
test
""",
            encoding="utf-8",
        )

        errors = MODULE.validate_ssot_source(path)

        assert any("benchmark contract missing section" in item for item in errors)
    finally:
        MODULE.ROOT = old_root


def test_safe_rglob_falls_back_to_os_walk_when_pathlib_walk_is_racy(tmp_path: Path) -> None:
    base = tmp_path / ".codex"
    target = base / "skills" / "sample" / "resources"
    target.mkdir(parents=True)
    capability = target / "capability.json"
    capability.write_text("{}", encoding="utf-8")

    with patch.object(Path, "rglob", side_effect=FileNotFoundError("transient")):
        matched = MODULE.safe_rglob(base, "capability.json")

    assert matched == [capability]
