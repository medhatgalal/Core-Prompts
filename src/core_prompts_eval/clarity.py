from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


def load_policy(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / ".meta" / "instruction-clarity.json").read_text(encoding="utf-8"))


def audit_text(text: str, policy: Mapping[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    for rule in policy.get("rules", []):
        pattern = rule.get("pattern")
        if not pattern:
            continue
        regex = re.compile(str(pattern), re.IGNORECASE)
        for number, line in enumerate(lines, start=1):
            if regex.search(line):
                findings.append(
                    {
                        "rule_id": rule["id"],
                        "line": number,
                        "class": rule["class"],
                        "risk": rule["risk"],
                        "message": rule["summary"],
                        "source_url": rule["source_url"],
                        "repair_permitted": bool(rule.get("deterministic_repair", False)),
                    }
                )
    return {
        "policy": policy["policy_id"],
        "finding_count": len(findings),
        "findings": findings,
        "advisory_only": True,
        "behavioral_claim": "none",
    }


def safe_fixes(text: str) -> tuple[str, list[dict[str, str]]]:
    """Apply only contract-neutral whitespace normalization."""
    original = text
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"
    ledger: list[dict[str, str]] = []
    if normalized != original:
        ledger.append({"rule_id": "IC-SAFE-001", "change": "trimmed trailing whitespace and normalized final newline"})
    return normalized, ledger
