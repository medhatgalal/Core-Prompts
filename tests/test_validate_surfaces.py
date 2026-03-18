from __future__ import annotations

import importlib.util
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
