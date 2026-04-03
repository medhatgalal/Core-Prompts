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


def test_validate_advisory_policy_metadata_rejects_non_advisory_handoff(tmp_path: Path) -> None:
    path = tmp_path / "capability-handoff.json"
    path.write_text(
        """{
  "advisory_only": false
}
""",
        encoding="utf-8",
    )

    errors = MODULE.validate_advisory_policy_metadata(path)

    assert any("advisory_only=true" in item for item in errors)


def test_validate_advisory_policy_metadata_requires_forbidden_control_plane_terms(tmp_path: Path) -> None:
    path = tmp_path / "capability.json"
    path.write_text(
        """{
  "layers": {
    "minimal": {
      "tool_policy": {
        "forbidden": ["orchestration"]
      }
    }
  }
}
""",
        encoding="utf-8",
    )

    errors = MODULE.validate_advisory_policy_metadata(path)

    assert any("delegation decisions" in item for item in errors)
    assert any("runtime execution control" in item for item in errors)


def test_validate_secret_like_literals_flags_real_secrets(tmp_path: Path) -> None:
    path = tmp_path / "sample.md"
    path.write_text(
        """# Sample

api_key = "prod_token_1234567890abcdefghi"
""",
        encoding="utf-8",
    )

    errors = MODULE.validate_secret_like_literals(path)

    assert any("secret-like literal detected" in item for item in errors)


def test_check_schema_cache_warns_when_unhealthy_source_has_cached_artifact(tmp_path: Path) -> None:
    old_root = MODULE.ROOT
    old_manifest = MODULE.SCHEMA_CACHE_MANIFEST
    try:
        MODULE.ROOT = tmp_path
        cache_dir = tmp_path / ".meta" / "schema-cache"
        cache_dir.mkdir(parents=True)
        cached_artifact = cache_dir / "cached.json"
        cached_artifact.write_text("cached", encoding="utf-8")
        manifest = {
            "generated_at": "2026-04-02T00:00:00+00:00",
            "entries": [
                {
                    "url": "https://example.com/schema",
                    "ok": False,
                    "cache_path": ".meta/schema-cache/cached.json",
                    "fetched_at": "2026-04-02T00:00:00+00:00",
                }
            ],
        }
        manifest_path = cache_dir / "manifest.json"
        manifest_path.write_text(__import__("json").dumps(manifest), encoding="utf-8")
        MODULE.SCHEMA_CACHE_MANIFEST = manifest_path

        warnings: list[str] = []
        errors, checked = MODULE.check_schema_cache(
            [{"schema_mode": "remote", "source_urls": ["https://example.com/schema"]}],
            strict=True,
            ttl_days=14,
            warnings=warnings,
        )

        assert errors == []
        assert checked == ["https://example.com/schema"]
        assert any("using cached artifact" in item for item in warnings)
    finally:
        MODULE.ROOT = old_root
        MODULE.SCHEMA_CACHE_MANIFEST = old_manifest
