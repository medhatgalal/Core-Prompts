from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


PROVIDERS = {
    "codex": {"command": "codex", "version": ["--version"], "native_discovery": False, "required_grade": "A"},
    "gemini": {"command": "gemini", "version": ["--version"], "native_discovery": True, "required_grade": "A"},
    "claude": {"command": "claude", "version": ["-v"], "native_discovery": False, "required_grade": "A"},
    "kiro": {"command": "kiro-cli", "version": ["--version"], "native_discovery": True, "required_grade": "B"},
}


def probe_runtime(repo_root: Path) -> dict[str, Any]:
    providers: list[dict[str, Any]] = []
    for name, spec in PROVIDERS.items():
        path = shutil.which(spec["command"])
        if not path:
            providers.append({"host": name, "result": "NOT_RUN", "reason": "binary unavailable"})
            continue
        proc = subprocess.run(
            [path, *spec["version"]],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        version = (proc.stdout or proc.stderr).strip().splitlines()
        providers.append(
            {
                "host": name,
                "result": "available" if proc.returncode == 0 else "NOT_RUN",
                "binary": path,
                "version": version[0] if version else "unknown",
                "native_discovery": spec["native_discovery"],
                "promotion_evidence_grade": spec["required_grade"],
                "model_calls": 0,
            }
        )
    inspect_available = False
    inspect_version = None
    try:
        import importlib.metadata

        inspect_version = importlib.metadata.version("inspect_ai")
        inspect_available = True
    except importlib.metadata.PackageNotFoundError:
        pass
    return {
        "schema_version": "RuntimeProbe.v1",
        "providers": providers,
        "inspect": {
            "available": inspect_available,
            "version": inspect_version,
            "role": "replaceable_execution_substrate",
        },
        "model_calls": 0,
    }
