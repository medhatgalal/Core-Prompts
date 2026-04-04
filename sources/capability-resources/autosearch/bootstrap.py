#!/opt/homebrew/bin/python3.14
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Mapping


def _slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    parts = [part for part in cleaned.split("-") if part]
    return "-".join(parts) or "autosearch"


def _clean(values: list[str]) -> list[str]:
    return [item.strip() for item in values if item.strip()]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _render_template(path: Path, values: Mapping[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def _bullet_block(values: list[str], placeholder: str) -> str:
    items = values or [placeholder]
    return "\n".join(f"- {item}" for item in items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Autosearch artifacts for a measurable improvement run.")
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
    parser.add_argument("--report-dir", default="reports/autosearch")
    args = parser.parse_args()

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    prefix = Path(args.report_dir) / f"{stamp}-{_slugify(args.target)}"
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
        "goal_contract": prefix.with_name(prefix.name + "-goal-contract.md"),
        "experiment_ledger": prefix.with_name(prefix.name + "-experiment-ledger.md"),
        "promotion_packet": prefix.with_name(prefix.name + "-promotion-packet.md"),
        "scorecard": prefix.with_name(prefix.name + "-scorecard.json"),
    }

    _write(outputs["goal_contract"], _render_template(template_dir / "goal-contract.md.tmpl", values))
    _write(outputs["experiment_ledger"], _render_template(template_dir / "experiment-ledger.md.tmpl", values))
    _write(outputs["promotion_packet"], _render_template(template_dir / "promotion-packet.md.tmpl", values))
    _write(outputs["scorecard"], _render_template(template_dir / "scorecard.json.tmpl", values))

    print(json.dumps({"created": {name: str(path) for name, path in outputs.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
