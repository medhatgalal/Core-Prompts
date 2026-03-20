from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "smoke-clis.py"
SPEC = importlib.util.spec_from_file_location("smoke_clis", SCRIPT_PATH)
assert SPEC and SPEC.loader
smoke_clis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke_clis)


def test_expected_discovery_slugs_is_surface_aware() -> None:
    manifest = {
        "ssot_sources": [
            {"slug": "code-review", "expected_surface_names": ["codex_skill", "gemini_skill", "claude_skill"]},
            {"slug": "architecture", "expected_surface_names": ["codex_skill", "claude_agent", "kiro_agent"]},
            {"slug": "testing", "expected_surface_names": ["codex_skill", "kiro_skill"]},
        ]
    }

    assert smoke_clis.expected_discovery_slugs(manifest, ["gemini_skill"]) == ["code-review"]
    assert smoke_clis.expected_discovery_slugs(manifest, ["claude_agent"]) == ["architecture"]
    assert smoke_clis.expected_discovery_slugs(manifest, ["kiro_agent"]) == ["architecture"]


def test_expected_artifact_paths_uses_surface_rules_and_manifest() -> None:
    rules = json.loads((ROOT / ".meta" / "surface-rules.json").read_text(encoding="utf-8"))
    artifact_rules = smoke_clis.artifact_rules_by_name(rules)
    manifest = {
        "ssot_sources": [
            {
                "slug": "architecture",
                "expected_surface_names": ["claude_skill", "claude_agent", "kiro_skill", "kiro_agent"],
            }
        ]
    }

    claude_paths = smoke_clis.expected_artifact_paths(manifest, artifact_rules, "claude")
    kiro_paths = smoke_clis.expected_artifact_paths(manifest, artifact_rules, "kiro")

    assert ".claude/skills/architecture/SKILL.md" in claude_paths
    assert ".claude/agents/architecture.md" in claude_paths
    assert ".kiro/skills/architecture/SKILL.md" in kiro_paths
    assert ".kiro/agents/architecture.json" in kiro_paths


def test_discovery_pattern_builder_knows_supported_tools() -> None:
    assert smoke_clis.discovery_pattern_builder("gemini")
    assert smoke_clis.discovery_pattern_builder("claude")
    assert smoke_clis.discovery_pattern_builder("kiro")
    assert smoke_clis.discovery_pattern_builder("codex") is None


def test_approval_gated_output_is_detected() -> None:
    text = (
        "I need your permission to run this script. "
        "The command requires approval because it needs to execute the `claude agents` command."
    )
    assert smoke_clis.is_approval_gated_output(text) is True
    assert smoke_clis.is_approval_gated_output(
        "I need your permission to run the `claude agents` command. The system is requesting approval."
    ) is True
