#!/opt/homebrew/bin/python3.14
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping


def _slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    parts = [part for part in cleaned.split("-") if part]
    return "-".join(parts) or "auto-research"


def _clean(values: list[str]) -> list[str]:
    return [item.strip() for item in values if item.strip()]


def _write(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(text.rstrip() + "\n")
    except FileExistsError:
        return False
    return True


def _render_template(path: Path, values: Mapping[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def _bullet_block(values: list[str], placeholder: str) -> str:
    items = values or [placeholder]
    return "\n".join(f"- {item}" for item in items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Auto-Research artifacts for a measurable improvement run.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--editable-scope", action="append", default=[])
    parser.add_argument("--must-not-change", action="append", default=[])
    parser.add_argument("--baseline-evidence", action="append", default=[])
    parser.add_argument("--promotion-threshold", action="append", default=[])
    parser.add_argument("--budget", default="3 trials / 1 hour / operator-reviewed")
    parser.add_argument(
        "--profile",
        choices=["dry-run-advisory", "bounded-execution", "promotion-prep"],
        default="dry-run-advisory",
    )
    parser.add_argument("--report-dir", required=True, help="Chosen parent directory for stable task artifacts; existing files are preserved.")
    args = parser.parse_args()

    task_dir = Path(args.report_dir) / _slugify(args.target)
    editable_scope = _clean(args.editable_scope)
    must_not_change = _clean(args.must_not_change)
    baseline_evidence = _clean(args.baseline_evidence)
    promotion_threshold = _clean(args.promotion_threshold)
    template_dir = Path(__file__).resolve().parent / "templates"
    values = {
        "target": args.target,
        "goal": args.goal,
        "profile": args.profile,
        "budget": args.budget,
        "editable_scope": _bullet_block(editable_scope, "[define editable scope]"),
        "must_not_change": _bullet_block(must_not_change, "[define protected surfaces]"),
        "baseline_evidence": _bullet_block(baseline_evidence, "[define baseline evidence]"),
        "promotion_threshold": _bullet_block(promotion_threshold, "[define promotion threshold]"),
    }

    outputs = {
        "goal_contract": task_dir / "goal-contract.md",
        "experiment_ledger": task_dir / "experiment-ledger.md",
        "scorecard": task_dir / "scorecard.json",
    }
    if args.profile == "promotion-prep":
        outputs["promotion_packet"] = task_dir / "promotion-packet.md"

    rendered = {name: _render_template(template_dir / (path.name + ".tmpl"), values)
                for name, path in outputs.items()}
    result: dict[str, dict[str, str]] = {"created": {}, "preserved": {}}
    for name, path in outputs.items():
        disposition = "created" if _write(path, rendered[name]) else "preserved"
        result[disposition][name] = str(path)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
