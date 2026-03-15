"""SSOT audit, manifest, and handoff helpers for Capability Fabric."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from intent_pipeline.uac_assessment import UacAssessment, assess_uac_source
from intent_pipeline.uac_capabilities import (
    audit_surface_alignment,
    deployment_intent,
    emitted_surface_names,
    normalize_declared_capability,
)
from intent_pipeline.uac_extract import extract_uac_analysis_text
from intent_pipeline.uac_manifest import analyze_manifest_fit, build_capability_manifest, orchestrator_handoff_payload


@dataclass(frozen=True, slots=True)
class SsotEntry:
    path: Path
    slug: str
    description: str
    raw_text: str
    body: str
    frontmatter: dict[str, str]


@dataclass(frozen=True, slots=True)
class SsotAuditEntry:
    slug: str
    file: str
    description: str
    declared_capability: str | None
    inferred: UacAssessment
    expected_surface_names: tuple[str, ...]
    actual_surface_names: tuple[str, ...]
    audit_status: str
    audit_issues: tuple[str, ...]
    manifest: dict[str, object]
    cross_analysis: dict[str, object]

    def as_payload(self) -> dict[str, object]:
        return {
            "slug": self.slug,
            "file": self.file,
            "description": self.description,
            "declared_capability": self.declared_capability,
            "inferred_capability": self.inferred.capability_type,
            "confidence": round(self.inferred.confidence, 2),
            "deployment_intent": deployment_intent(self.inferred.capability_type, self.inferred.confidence),
            "signals": list(self.inferred.signals),
            "scorecard": dict(self.inferred.scorecard),
            "expected_surfaces": list(self.expected_surface_names),
            "actual_surfaces": list(self.actual_surface_names),
            "audit": {
                "status": self.audit_status,
                "issues": list(self.audit_issues),
            },
            "manifest": self.manifest,
            "cross_analysis": self.cross_analysis,
        }


def load_ssot_entries(ssot_dir: Path) -> list[SsotEntry]:
    entries: list[SsotEntry] = []
    for path in sorted(ssot_dir.glob("*.md")):
        raw_text = path.read_text(encoding="utf-8")
        frontmatter, body = parse_ssot_frontmatter_and_body(raw_text)
        slug = frontmatter.get("name") or path.stem
        description = frontmatter.get("description") or f"Surface prompt for {slug}"
        entries.append(
            SsotEntry(
                path=path,
                slug=slug,
                description=description,
                raw_text=raw_text,
                body=body,
                frontmatter=frontmatter,
            )
        )
    return entries


def _assess_entry(entry: SsotEntry) -> tuple[UacAssessment, dict[str, object], dict[str, object], dict[str, object]]:
    extraction = extract_uac_analysis_text(entry.raw_text, entry.path.name)
    inferred = assess_uac_source(
        entry.raw_text,
        analysis_text=extraction.analysis_text,
        source_metadata={
            "source_type": "LOCAL_FILE",
            "normalized_source": str(entry.path.resolve()),
            "policy_rule_id": f"ssot.{entry.slug}",
            "content_type": "text/markdown",
            "content_sha256": "ssot",
        },
        source_hint=entry.path,
    )
    summary = extraction.analysis_text[:800]
    uplift = {
        "primary_objective": None,
        "in_scope": [],
        "out_of_scope": [],
        "quality_constraints": [],
    }
    routing = {"route_profile": "SSOT_AUDIT"}
    manifest = build_capability_manifest(
        slug=entry.slug,
        source_metadata={
            "source_type": "LOCAL_FILE",
            "normalized_source": str(entry.path.resolve()),
            "policy_rule_id": f"ssot.{entry.slug}",
            "content_type": "text/markdown",
            "content_sha256": "ssot",
        },
        raw_text=entry.raw_text,
        summary=summary,
        assessment_payload=inferred.as_payload(),
        uplift_payload=uplift,
        routing_payload=routing,
        repo_root=entry.path.parents[1],
    )
    return inferred, manifest, uplift, routing


def audit_ssot_entries(root: Path) -> list[SsotAuditEntry]:
    ssot_dir = root / "ssot"
    entries = load_ssot_entries(ssot_dir)
    manifests: list[dict[str, object]] = []
    inferred_cache: dict[str, UacAssessment] = {}
    for entry in entries:
        inferred, manifest, _, _ = _assess_entry(entry)
        inferred_cache[entry.slug] = inferred
        manifests.append(manifest)

    audits: list[SsotAuditEntry] = []
    for entry, manifest in zip(entries, manifests):
        inferred = inferred_cache[entry.slug]
        declared_capability = normalize_declared_capability(
            entry.frontmatter.get("capability_type") or entry.frontmatter.get("kind") or entry.frontmatter.get("role")
        )
        expected_surfaces = set(emitted_surface_names(inferred.capability_type))
        actual_surfaces = discover_actual_surfaces(root, entry.slug)
        audit = audit_surface_alignment(
            declared_capability=declared_capability,
            inferred_capability=inferred.capability_type,
            expected_surfaces=expected_surfaces,
            actual_surfaces=actual_surfaces,
        )
        existing = [item for item in manifests if item.get("slug") != entry.slug]
        cross = analyze_manifest_fit(manifest, existing)
        audits.append(
            SsotAuditEntry(
                slug=entry.slug,
                file=str(entry.path.relative_to(root)),
                description=entry.description,
                declared_capability=declared_capability,
                inferred=inferred,
                expected_surface_names=tuple(sorted(expected_surfaces)),
                actual_surface_names=tuple(sorted(actual_surfaces)),
                audit_status=audit.status,
                audit_issues=audit.issues,
                manifest=manifest,
                cross_analysis=cross.as_payload(),
            )
        )
    return audits


def build_ssot_manifest_entry(entry: SsotEntry) -> dict[str, object]:
    inferred, manifest, _, _ = _assess_entry(entry)
    declared_capability = normalize_declared_capability(
        entry.frontmatter.get("capability_type") or entry.frontmatter.get("kind") or entry.frontmatter.get("role")
    )
    manifest["declared_capability"] = declared_capability
    manifest["inferred_capability"] = inferred.capability_type
    manifest["expected_surface_names"] = list(emitted_surface_names(inferred.capability_type))
    manifest["rubric_version"] = "capability-fabric.v0"
    return manifest


def build_ssot_handoff_contract(root: Path) -> dict[str, object]:
    manifests = [build_ssot_manifest_entry(entry) for entry in load_ssot_entries(root / "ssot")]
    return orchestrator_handoff_payload(manifests)


def parse_ssot_frontmatter_and_body(text: str) -> tuple[dict[str, str], str]:
    front: dict[str, str] = {}
    blocks: list[str] = []
    remainder = text
    while remainder.startswith('---\n'):
        end = remainder.find('\n---', 3)
        if end == -1:
            break
        block = remainder[4:end]
        blocks.append(block)
        remainder = remainder[end + 4 :]
        if remainder.startswith('\n'):
            remainder = remainder[1:]
    for block in blocks:
        for line in block.splitlines():
            line = line.strip()
            if not line or ':' not in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key not in front:
                front[key] = value
    return front, remainder.strip('\n')


def discover_actual_surfaces(root: Path, slug: str) -> set[str]:
    surface_paths = {
        "codex_skill": root / ".codex" / "skills" / slug / "SKILL.md",
        "codex_agent": root / ".codex" / "agents" / f"{slug}.toml",
        "gemini_command": root / ".gemini" / "commands" / f"{slug}.toml",
        "gemini_skill": root / ".gemini" / "skills" / slug / "SKILL.md",
        "gemini_agent": root / ".gemini" / "agents" / f"{slug}.md",
        "claude_command": root / ".claude" / "commands" / f"{slug}.md",
        "claude_agent": root / ".claude" / "agents" / f"{slug}.md",
        "kiro_prompt": root / ".kiro" / "prompts" / f"{slug}.md",
        "kiro_skill": root / ".kiro" / "skills" / slug / "SKILL.md",
        "kiro_agent": root / ".kiro" / "agents" / f"{slug}.json",
    }
    return {name for name, path in surface_paths.items() if path.exists()}


def render_audit_table(audits: Sequence[SsotAuditEntry]) -> str:
    headers = ("slug", "declared", "inferred", "status", "fit", "confidence")
    rows = [headers]
    for audit in audits:
        rows.append(
            (
                audit.slug,
                audit.declared_capability or "-",
                audit.inferred.capability_type,
                audit.audit_status,
                str(audit.cross_analysis.get("fit_assessment", "-")),
                f"{audit.inferred.confidence:.2f}",
            )
        )
    widths = [max(len(row[idx]) for row in rows) for idx in range(len(headers))]
    rendered = []
    for index, row in enumerate(rows):
        rendered.append(" | ".join(value.ljust(widths[pos]) for pos, value in enumerate(row)))
        if index == 0:
            rendered.append("-+-".join("-" * width for width in widths))
    return "\n".join(rendered)


__all__ = [
    "SsotAuditEntry",
    "SsotEntry",
    "audit_ssot_entries",
    "build_ssot_handoff_contract",
    "build_ssot_manifest_entry",
    "discover_actual_surfaces",
    "load_ssot_entries",
    "parse_ssot_frontmatter_and_body",
    "render_audit_table",
]
