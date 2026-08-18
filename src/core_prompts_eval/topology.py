from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .contracts import artifact_hash


NORMATIVE = re.compile(r"\b(must|must not|never|required|only|forbidden|explicit approval|do not|shall)\b", re.I)
GUARD = re.compile(r"\b(if|when|unless|only when)\b", re.I)
COMMAND = re.compile(r"(?<![\w/])/[a-z][a-z0-9-]*(?:\s+/[a-z][a-z0-9-]*)*", re.I)
MODE_HEADING = re.compile(r"^#{2,4}\s+(?:Mode\s+\d+\s*:\s*)?(.+)$", re.I)


def _body(text: str) -> str:
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) == 3:
            return parts[2]
    return text


def _clause_id(slug: str, line_number: int, line: str) -> str:
    return f"{slug}:L{line_number}:{artifact_hash(line)[:12]}"


def compile_topology(path: Path) -> dict[str, Any]:
    slug = path.stem
    text = path.read_text(encoding="utf-8")
    body = _body(text)
    lines = body.splitlines()
    commands: set[str] = set()
    modes: list[dict[str, Any]] = []
    clauses: list[dict[str, Any]] = []
    resources: list[str] = []
    handoffs: list[str] = []
    outputs: list[str] = []
    current_heading = "root"
    for number, line in enumerate(lines, start=1):
        heading = MODE_HEADING.match(line)
        if heading:
            current_heading = heading.group(1).strip()
            if re.search(r"\b(mode|module|command|workflow|pass|phase)\b", current_heading, re.I):
                modes.append({"id": artifact_hash(current_heading)[:12], "label": current_heading, "source_line": number})
        commands.update(COMMAND.findall(line))
        if NORMATIVE.search(line):
            clauses.append(
                {
                    "id": _clause_id(slug, number, line.strip()),
                    "heading": current_heading,
                    "source_line": number,
                    "sha256": artifact_hash(line.strip()),
                    "text": line.strip(),
                    "kind": "guarded_invariant" if GUARD.search(line) else "invariant",
                    "mapped_to": [],
                }
            )
        if re.search(r"\b(resources?|references?|fallback)\b", line, re.I) and line.lstrip().startswith(("-", "|")):
            resources.append(line.strip())
        if re.search(r"\b(handoff|route to|companion capability)\b", line, re.I):
            handoffs.append(line.strip())
        if current_heading.lower().startswith(("required output", "output contract", "output format")) and line.lstrip().startswith(("-", "|")):
            outputs.append(line.strip())

    ambiguities = detect_ambiguities(slug, text)
    mapped = 0
    return {
        "schema_version": "CapabilityTopology.v1",
        "slug": slug,
        "ssot_sha256": artifact_hash(text),
        "explicit_invocations": sorted(commands),
        "semantic_triggers": [],
        "aliases_shortcuts": [],
        "auto_routes": [],
        "nodes": {"commands": sorted(commands), "modes_modules": modes, "controls": [], "modifiers": []},
        "composition": {"legal_pairs": [], "forbidden_pairs": [], "canonical_order": [], "requirements": [], "supersession": []},
        "state_machine": {"states": [], "transitions": [], "forbidden_transitions": []},
        "outputs": outputs,
        "authority_boundaries": [c["id"] for c in clauses if re.search(r"approval|forbidden|never|do not", c["text"], re.I)],
        "resources": sorted(set(resources)),
        "handoffs": sorted(set(handoffs)),
        "protected_invariants": clauses,
        "risk_tiers": {"critical": [], "high": [], "standard": []},
        "source_references": [{"path": f"ssot/{slug}.md", "sha256": artifact_hash(text)}],
        "known_ambiguities": ambiguities,
        "coverage_policy": {
            "normative_clauses": "100_percent_mapped_or_waived",
            "nodes": "positive_and_boundary",
            "transitions": "all_legal_and_forbidden",
            "module_pairs": "all_legal_pairs",
            "high_risk_tuples": "assigned_strength",
            "critical_mutants": "100_percent_killed",
        },
        "normative_clause_coverage": {"total": len(clauses), "mapped": mapped, "waived": 0},
        "review_status": "blocked" if ambiguities else "draft",
        "compiler_note": "Draft extraction is not human approval. mapped remains zero until cases or waivers reference stable clause IDs.",
    }


def detect_ambiguities(slug: str, text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    lower = text.lower()
    numbered_modes = re.findall(r"^#{2,4}\s+Mode\s+(\d+)\s*:\s*(.+)$", text, re.I | re.M)
    mode_numbers = [number for number, _ in numbered_modes]
    mode_labels = [label.strip().lower() for _, label in numbered_modes]
    if len(mode_numbers) != len(set(mode_numbers)):
        findings.append({"id": "TOPOLOGY-DUPLICATE-MODE-NUMBER", "message": "A numbered mode identifier is declared more than once."})
    if len(mode_labels) != len(set(mode_labels)):
        findings.append({"id": "TOPOLOGY-DUPLICATE-MODE-LABEL", "message": "A mode label is declared more than once."})
    rules = (
        ("SC-ULT-OUTPUT", "exactly two sections", "mandatory output structure", "Terminal output count conflicts with the mandatory structure."),
        ("SC-GASLIGHT-COUNT", "2–4", "1–3", "Technique cardinality is contradictory."),
        ("SC-GASLIGHT-COUNT-ASCII", "2-4", "1-3", "Technique cardinality is contradictory."),
    )
    for finding_id, left, right, message in rules:
        if left in lower and right in lower:
            findings.append({"id": finding_id, "message": message})
    if "separate response into exactly:" in lower and "`approach decision`" in lower and "`generated prompt`" in lower:
        findings.append({"id": "SC-ULT-OUTPUT", "message": "The exact terminal section count conflicts with the mandatory output structure."})
    if slug == "supercharge":
        findings.extend(
            [
                {"id": "SC-TERMINAL-PRECEDENCE", "message": "Terminal controls claim overlapping section-only and supersession behavior; precedence needs one canonical rule."},
                {"id": "SC-MULTIPLE-MODIFIERS", "message": "Behavior for multiple mutually exclusive modifiers is not explicit."},
            ]
        )
    if slug == "pulse":
        if "only during `/sweep`" in lower and "`pulse /delete" in lower:
            findings.append({"id": "PULSE-DELETE-BOUNDARY", "message": "The tool boundary permits trash only during /sweep while /delete is a distinct quick-delete command."})
        if "all commands compose" in lower:
            findings.append({"id": "PULSE-COMPOSITION", "message": "The universal composition claim lacks legal and forbidden combinations for read, write, and destructive commands."})
        if "the skill itself never changes" in lower and "rewrites the config blocks in place" in lower:
            findings.append({"id": "PULSE-CONFIG-MUTATION", "message": "The config contract both denies and requires mutation of the skill file."})
    return findings
