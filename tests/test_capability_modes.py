from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_multi_mode_capabilities_have_descriptor_modes() -> None:
    for slug in ("supercharge", "pulse", "auto-research", "ic-assistant", "instruction-editor"):
        descriptor = json.loads((ROOT / ".meta" / "capabilities" / f"{slug}.json").read_text(encoding="utf-8"))
        assert descriptor["modes"], f"{slug} descriptor lost its declared mode index"
        assert all(mode["source_refs"] == [f"ssot/{slug}.md"] for mode in descriptor["modes"])


def test_generated_descriptors_do_not_expose_legacy_ship_as_promotion() -> None:
    for path in (ROOT / ".meta" / "capabilities").glob("*.json"):
        descriptor = json.loads(path.read_text(encoding="utf-8"))
        assert descriptor.get("quality_status") != "ship"
