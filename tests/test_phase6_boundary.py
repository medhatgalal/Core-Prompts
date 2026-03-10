from __future__ import annotations

import ast
from pathlib import Path

from intent_pipeline.phase6.contracts import Phase6BoundaryErrorCode, Phase6BoundaryViolation


PROJECT_ROOT = Path(__file__).resolve().parents[1]


FORBIDDEN_IMPORT_FRAGMENTS = (
    "subprocess",
    "requests",
    "httpx",
    "socket",
    "urllib.request",
)
FORBIDDEN_CALLS = {
    "os.system",
    "subprocess.run",
    "subprocess.Popen",
    "requests.get",
    "httpx.get",
    "urllib.request.urlopen",
    "socket.create_connection",
}


def test_phase6_control_modules_do_not_import_forbidden_network_or_process_layers() -> None:
    module_paths = (
        PROJECT_ROOT / "src" / "intent_pipeline" / "phase6" / "engine.py",
        PROJECT_ROOT / "src" / "intent_pipeline" / "phase6" / "authorizer.py",
        PROJECT_ROOT / "src" / "intent_pipeline" / "phase6" / "executor_registry.py",
        PROJECT_ROOT / "src" / "intent_pipeline" / "phase6" / "journal.py",
    )

    for module_path in module_paths:
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
        imported_modules: list[str] = []
        call_targets: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    call_targets.append(f"{node.func.value.id}.{node.func.attr}")
                elif isinstance(node.func, ast.Name):
                    call_targets.append(node.func.id)

        normalized_imports = tuple(module.casefold() for module in imported_modules)

        assert "BOUND-06"
        for forbidden in FORBIDDEN_IMPORT_FRAGMENTS:
            if "." in forbidden:
                assert all(forbidden != module for module in normalized_imports)
                continue
            assert all(forbidden not in module.split(".") for module in normalized_imports)
        for forbidden in FORBIDDEN_CALLS:
            assert forbidden not in call_targets


def test_phase4_and_phase5_do_not_import_phase6_layers() -> None:
    module_paths = (
        PROJECT_ROOT / "src" / "intent_pipeline" / "phase4" / "engine.py",
        PROJECT_ROOT / "src" / "intent_pipeline" / "phase4" / "fallback.py",
        PROJECT_ROOT / "src" / "intent_pipeline" / "phase5" / "engine.py",
        PROJECT_ROOT / "src" / "intent_pipeline" / "phase5" / "help.py",
        PROJECT_ROOT / "src" / "intent_pipeline" / "phase5" / "runtime_checks.py",
    )

    for module_path in module_paths:
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
        imported_modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")

        normalized_imports = tuple(module.casefold() for module in imported_modules)
        assert all("phase6" not in module for module in normalized_imports)


def test_phase6_typed_boundary_codes_and_evidence_paths_are_deterministic() -> None:
    violation = Phase6BoundaryViolation(
        code=Phase6BoundaryErrorCode.FORBIDDEN_NETWORK_IMPORT,
        evidence_paths=("phase6.boundary.module:engine", "phase6.boundary.import:socket", "phase6.boundary.module:engine"),
        detail="forbidden network import detected in phase6 control plane",
    )
    payload = violation.as_payload()

    assert "BOUND-06"
    assert payload["code"].startswith("BOUND-06-")
    assert payload["evidence_paths"] == sorted(payload["evidence_paths"])
    assert payload["evidence_paths"] == [
        "phase6.boundary.import:socket",
        "phase6.boundary.module:engine",
    ]
