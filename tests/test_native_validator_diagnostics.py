from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from test_validate_surfaces import MODULE, ROOT


@pytest.mark.parametrize(
    ("code", "output", "fails"),
    [
        (0, "", False),
        (0, "Error: Json supplied is invalid", True),
        (0, "\x1b[mError: \x1b[0mJson supplied is invalid", True),
        (1, "validation failed", True),
    ],
)
def test_kiro_native_validation_checks_diagnostics(
    code: int, output: str, fails: bool
) -> None:
    rules = json.loads((ROOT / ".meta/surface-rules.json").read_text())
    rule = next(rule for rule in rules["artifacts"] if rule["name"] == "kiro_agent")
    with patch.object(MODULE.shutil, "which", return_value="/fake/kiro-cli"), patch.object(
        MODULE, "run_command", return_value=(code, output)
    ):
        errors = MODULE.run_artifact_validator(Path("agent.json"), rule, True, [])
    assert bool(errors) is fails


def test_diagnostic_patterns_are_rule_scoped() -> None:
    rule = {"validator": {"command": ["other-validator"]}}
    with patch.object(MODULE.shutil, "which", return_value="/fake/validator"), patch.object(
        MODULE, "run_command", return_value=(0, "Error: quoted example in valid output")
    ):
        assert MODULE.run_artifact_validator(Path("artifact"), rule, True, []) == []
