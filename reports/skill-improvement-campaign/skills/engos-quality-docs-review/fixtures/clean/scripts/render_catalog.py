"""Synthetic PUBLIC generator; emits documentation to stdout only."""
import json
from pathlib import Path
source = json.loads((Path(__file__).resolve().parents[1] / "catalog.json").read_text())
print("# Catalog\n\nGenerated from catalog.json; regenerate, do not hand-edit.\n")
for item in source["commands"]:
    print("- `" + item + "`")
