"""Synthetic PUBLIC CLI: local stdout only, no network or file writes."""
import argparse
p = argparse.ArgumentParser(description="Inspect a local example")
p.add_argument("--format", choices=["text", "json"], default="text")
p.add_argument("--theme", choices=["light", "dark"], default="light")
args = p.parse_args()
print('{"ok": true}' if args.format == "json" else "ok")
