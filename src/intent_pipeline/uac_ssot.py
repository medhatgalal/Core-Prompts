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
    emitted_surfaces_by_cli,
    normalize_declared_capability,
)
from intent_pipeline.uac_descriptors import load_descriptor, normalize_descriptor_summary
from intent_pipeline.uac_extract import extract_uac_analysis_text
from intent_pipeline.uac_manifest import (
    analyze_manifest_fit,
    build_capability_manifest,
    normalize_persisted_source_reference,
    orchestrator_handoff_payload,
    packaging_profile,
)


@dataclass(frozen=True, slots=True)
class SsotEntry:
    path: Path
    slug: str
    display_name: str
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
                display_name=extract_display_name(body, slug),
                description=description,
                raw_text=raw_text,
                body=body,
                frontmatter=frontmatter,
            )
        )
    return entries


def _assess_entry(entry: SsotEntry) -> tuple[UacAssessment, dict[str, object], dict[str, object], dict[str, object]]:
    extraction = extract_uac_analysis_text(entry.raw_text, entry.path.name)
    repo_root = entry.path.parents[1]
    persisted_source = normalize_persisted_source_reference(
        str(entry.path.resolve()),
        source_type="LOCAL_FILE",
        repo_root=repo_root,
    )
    inferred = assess_uac_source(
        entry.raw_text,
        analysis_text=extraction.analysis_text,
        source_metadata={
            "source_type": "LOCAL_FILE",
            "normalized_source": persisted_source,
            "policy_rule_id": f"ssot.{entry.slug}",
            "content_type": "text/markdown",
            "content_sha256": "ssot",
        },
        source_hint=entry.path,
    )
    summary = entry.description.strip() or extraction.analysis_text[:240]
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
            "normalized_source": persisted_source,
            "policy_rule_id": f"ssot.{entry.slug}",
            "content_type": "text/markdown",
            "content_sha256": "ssot",
        },
        raw_text=entry.raw_text,
        summary=summary,
        assessment_payload=inferred.as_payload(),
        uplift_payload=uplift,
        routing_payload=routing,
        repo_root=repo_root,
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
        manifests.append(_merge_descriptor_overlay(root, entry.slug, manifest))

    audits: list[SsotAuditEntry] = []
    for entry, manifest in zip(entries, manifests):
        inferred = inferred_cache[entry.slug]
        declared_capability = normalize_declared_capability(
            entry.frontmatter.get("capability_type") or entry.frontmatter.get("kind") or entry.frontmatter.get("role")
        )
        effective_capability = declared_capability or inferred.capability_type
        expected_surfaces = set(emitted_surface_names(effective_capability))
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


def build_ssot_manifest_entry(entry: SsotEntry, repo_root: Path | None = None, *, merge_descriptor: bool = True) -> dict[str, object]:
    inferred, manifest, _, _ = _assess_entry(entry)
    repo_root = repo_root or entry.path.parents[1]
    if merge_descriptor:
        manifest = _merge_descriptor_overlay(repo_root, entry.slug, manifest)
    declared_capability = normalize_declared_capability(
        entry.frontmatter.get("capability_type") or entry.frontmatter.get("kind") or entry.frontmatter.get("role")
    )
    effective_capability = declared_capability or inferred.capability_type
    minimal = dict(manifest.get("layers", {}).get("minimal") or {})
    minimal["capability_type"] = effective_capability
    minimal["display_name"] = str(
        minimal.get("display_name")
        or manifest.get("display_name")
        or entry.frontmatter.get("display_name")
        or entry.display_name
    )
    minimal["packaging_profile"] = packaging_profile(effective_capability, emitted_surfaces_by_cli(effective_capability))
    minimal["emitted_surfaces"] = {cli: list(values) for cli, values in emitted_surfaces_by_cli(effective_capability).items()}
    manifest.setdefault("layers", {})
    manifest["layers"]["minimal"] = minimal
    manifest["display_name"] = minimal["display_name"]
    manifest["declared_capability"] = declared_capability
    manifest["inferred_capability"] = inferred.capability_type
    manifest["expected_surface_names"] = list(emitted_surface_names(effective_capability))
    manifest["rubric_version"] = "capability-fabric.v0"
    return manifest


def build_ssot_handoff_contract(root: Path) -> dict[str, object]:
    manifests = [build_ssot_manifest_entry(entry, root) for entry in load_ssot_entries(root / "ssot")]
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


def extract_display_name(body: str, slug: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return " ".join(part.capitalize() for part in slug.replace("_", "-").split("-"))


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


def _merge_descriptor_overlay(repo_root: Path, slug: str, manifest: dict[str, object]) -> dict[str, object]:
    descriptor = load_descriptor(repo_root, slug)
    if not descriptor:
        return manifest
    merged = dict(manifest)
    fallback_summary = str(((merged.get("layers") or {}).get("minimal") or {}).get("summary") or "")
    for key in (
        "display_name",
        "descriptor_version",
        "family_slug",
        "shared_summary",
        "shared_constraints",
        "modes",
        "benchmark_sources",
        "quality_profile",
        "quality_status",
        "judge_reports",
        "consumption_hints",
        "quality_pass_count",
        "quality_stop_reason",
    ):
        if key in descriptor:
            merged[key] = descriptor[key]
    descriptor_layers = descriptor.get("layers")
    if isinstance(descriptor_layers, dict):
        merged_layers = dict(merged.get("layers") or {})
        for layer_name, layer_payload in descriptor_layers.items():
            base = dict(merged_layers.get(layer_name) or {})
            if isinstance(layer_payload, dict):
                base.update(layer_payload)
                if layer_name == "minimal":
                    base["summary"] = normalize_descriptor_summary(base.get("summary"), fallback_summary)
            merged_layers[layer_name] = base
        merged["layers"] = merged_layers
    if "shared_summary" in merged:
        merged["shared_summary"] = normalize_descriptor_summary(merged.get("shared_summary"), fallback_summary)
    return merged


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
