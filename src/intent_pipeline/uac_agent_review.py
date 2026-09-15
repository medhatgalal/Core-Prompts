"""Admission of new agent surfaces using existing independent UAC reviews."""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess

from pathlib import Path
from typing import Any, Mapping, Sequence

from intent_pipeline.uac_baselines import text_sha256, validate_requirement_review, validate_requirement_reviews
from intent_pipeline.uac_capabilities import emitted_surfaces_by_cli, normalize_declared_capability
from intent_pipeline.uac_ssot import parse_ssot_frontmatter_and_body


def agent_providers(text: str) -> set[str]:
    frontmatter, _ = parse_ssot_frontmatter_and_body(text)
    capability = normalize_declared_capability(
        frontmatter.get("capability_type") or frontmatter.get("kind") or frontmatter.get("role")
    ) or "skill"
    return {provider for provider, surfaces in emitted_surfaces_by_cli(capability).items()
            if any(surface.endswith("_agent") for surface in surfaces)}


def agent_surface_review(
    repo_root: Path, *, slug: str, candidate_text: str, effective_text: str,
    reviews: Sequence[Mapping[str, Any]] = (), original_texts: Sequence[str] = (),
    baseline_providers: set[str] | None = None, require_original_text: bool = True,
) -> dict[str, Any]:
    """Compare current canonical declarations; never infer a need from prose.

    Review binding and attested independent authorship are checked mechanically.
    Reviewer authenticity and the merits of the need remain human review duties.
    """
    canonical = repo_root / "ssot" / f"{slug}.md"
    current = canonical.read_text(encoding="utf-8") if canonical.is_file() else ""
    if baseline_providers is None and current and agent_providers(candidate_text):
        fields, _ = parse_ssot_frontmatter_and_body(current)
        declared = normalize_declared_capability(fields.get("capability_type") or fields.get("kind") or fields.get("role"))
        if declared is None:
            try:
                baseline, _ = _agent_baseline(repo_root)
                previous = next((entry for entry in baseline.get("ssot_sources", []) if entry["slug"] == slug), {})
                baseline_providers = {name.removesuffix("_agent") for name in previous.get("expected_surface_names", [])
                                      if name.endswith("_agent")}
            except (OSError, ValueError):
                baseline_providers = set()
    allowed = agent_providers(current) if baseline_providers is None else baseline_providers
    added = sorted(agent_providers(candidate_text) - allowed)
    blockers: list[str] = []
    attestations: list[dict[str, Any]] = []
    if added:
        originals = list(original_texts) + ([current] if current else [])
        if require_original_text:
            review_failures = validate_requirement_reviews(
                reviews, slug=slug, original_texts=originals,
                candidate_text=candidate_text, effective_text=effective_text,
            )
        else:
            review_failures = [failure for review in reviews for failure in validate_requirement_review(
                review, slug=slug, original_text=None, candidate_text=candidate_text,
                effective_text=effective_text, require_original_text=False,
            )]
        blockers.extend(review_failures)
        approved: set[str] = set()
        if not review_failures:
            for review in reviews:
                approved.update(item["provider"] for item in review.get("agent_execution_needs", []))
                if review.get("agent_execution_needs"):
                    attestations.append(_persisted_attestation(review))
        for provider in added:
            if provider not in approved:
                blockers.append(f"agent execution need review required for {provider}")
    return {
        "status": "manual_review" if blockers else "reviewed" if added else "unchanged",
        "added_providers": added, "blockers": blockers,
        "review_attestations": attestations if not blockers else [],
        "source_fidelity": "not_required" if not added else "validated_at_intake" if require_original_text else "intake_attestation_not_replayed",
        "identity_authenticated": False, "behavioral_status": "behavioral_pending",
    }


def preflight_agent_emission(repo_root: Path) -> list[str]:
    """Check all SSOT entries before generation against a Git release baseline.

    Archives use only the latest pinned release in the installer catalog. The
    current generated manifest is never its own admission baseline.
    """
    from intent_pipeline.capability_resources import effective_capability_text
    candidates = [(path.stem, path.read_text(encoding="utf-8"))
                  for path in sorted((repo_root / "ssot").glob("*.md"))]
    candidates = [(slug, text) for slug, text in candidates if agent_providers(text)]
    if not candidates:
        return []
    try:
        baseline, basis = _agent_baseline(repo_root)
    except (OSError, ValueError) as exc:
        return [f"Agent emission baseline unavailable: {exc}; fetch release history or set "
                "CORE_PROMPTS_RELEASE_BASE_REF to a verified release commit."]
    baseline_entries = {entry["slug"]: entry for entry in baseline.get("ssot_sources", [])}
    errors: list[str] = []
    for slug, candidate in candidates:
        previous = baseline_entries.get(slug, {})
        allowed = {surface.removesuffix("_agent") for surface in previous.get("expected_surface_names", [])
                   if surface.endswith("_agent")}
        if not (agent_providers(candidate) - allowed):
            continue
        descriptor_path = repo_root / ".meta" / "capabilities" / f"{slug}.json"
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8")) if descriptor_path.is_file() else {}
        reviews: list[Mapping[str, Any]] = []
        for report in descriptor.get("judge_reports", []):
            admission = report.get("agent_surface_review", {})
            reviews.extend(admission.get("review_attestations", []))
        admission = agent_surface_review(
            repo_root, slug=slug, candidate_text=candidate,
            effective_text=effective_capability_text(repo_root, slug, candidate),
            reviews=reviews, baseline_providers=allowed, require_original_text=False,
        )
        errors.extend(f"{slug}: {blocker}" for blocker in admission["blockers"])
    return errors


def _catalog_agent_baseline(repo_root: Path) -> tuple[dict[str, Any], str]:
    # Reuse the installer's existing validator and pinned identity catalog; do
    # not invent a second grandfather list or union retired historical agents.
    validator = Path(__file__).resolve().parents[2] / "scripts" / "core_install" / "catalog.py"
    spec = importlib.util.spec_from_file_location("uac_legacy_catalog", validator)
    if spec is None or spec.loader is None:
        raise ValueError("installer catalog validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    catalog = module.load_catalog(repo_root)
    if not catalog["releases"]:
        raise ValueError("pinned catalog contains no releases")
    latest = max(catalog["releases"], key=lambda value: tuple(int(part) for part in value[1:].split(".")))
    surfaces: dict[str, set[str]] = {}
    for package in catalog["packages"]:
        if package["kind"] == "agent" and latest in package["releases"] and package.get("successor"):
            surfaces.setdefault(package["successor"], set()).add(f"{package['provider']}_agent")
    baseline = {"ssot_sources": [{"slug": slug, "expected_surface_names": sorted(names)}
                                  for slug, names in surfaces.items()]}
    return baseline, f"pinned-install-catalog:{latest}@{catalog['releases'][latest]['commit']}"


def _agent_baseline(repo_root: Path) -> tuple[dict[str, Any], str]:
    from intent_pipeline.consumer_shell import resolve_release_baseline
    baseline, basis = resolve_release_baseline(repo_root)
    return (baseline, basis) if baseline is not None else _catalog_agent_baseline(repo_root)


def _persisted_attestation(review: Mapping[str, Any]) -> dict[str, Any]:
    """Persist only execution review data; never distribute imported originals.

    Source fidelity was checked against original bytes at intake. Build checks
    attested source hashes/line mapping and candidate bindings without replaying
    original content or authenticating reviewer identity.
    """
    retained = {key: review[key] for key in (
        "schema_version", "slug", "original_sha256", "candidate_sha256", "effective_sha256", "verdict")}
    retained["reviewer"] = {key: review["reviewer"][key] for key in ("agent_id", "author_agent_id", "independent")}
    retained["requirements"] = [
        {"id": f"requirement-{index}", **{key: requirement[key] for key in (
            "source_start_line", "source_end_line", "disposition", "candidate_excerpt")
            if key in requirement and (key != "candidate_excerpt" or requirement["disposition"] != "retired")}}
        for index, requirement in enumerate(review["requirements"], 1)
    ]
    retained["source_line_count"] = review["requirements"][-1]["source_end_line"]
    retained["agent_execution_needs"] = [{key: need[key] for key in (
        "provider", "execution_need", "why_generic_worker_insufficient", "candidate_excerpt")}
        for need in review["agent_execution_needs"]]
    return retained


def declaration_normalization(repo_root: Path, *, slug: str, candidate_text: str) -> dict[str, Any] | None:
    """Recognize only insertion of a missing declaration for released surfaces.

    This preserves a previously shipped contract; it is neither a template
    uplift nor a new quality or behavioral verdict. Every other byte is fixed.
    """
    canonical = repo_root / "ssot" / f"{slug}.md"
    if not canonical.is_file():
        return None
    current = canonical.read_text(encoding="utf-8")
    old_fields, _ = parse_ssot_frontmatter_and_body(current)
    new_fields, _ = parse_ssot_frontmatter_and_body(candidate_text)
    if "capability_type" in old_fields or "capability_type" not in new_fields:
        return None
    capability = normalize_declared_capability(new_fields["capability_type"])
    if capability not in {"agent", "both"} or old_fields.get("name") != slug or new_fields.get("name") != slug:
        return None
    if not candidate_text.startswith("---\n"):
        return None
    header_end = candidate_text.find("\n---\n", 4)
    if header_end < 0:
        return None
    header = candidate_text[:header_end + 1]
    matches = list(re.finditer(r"^capability_type:[^\n]*\n", header, re.MULTILINE))
    if len(matches) != 1:
        return None
    match = matches[0]
    if candidate_text[:match.start()] + candidate_text[match.end():] != current:
        return None
    try:
        baseline, basis = _agent_baseline(repo_root)
    except (OSError, ValueError):
        return None
    if not basis.startswith("git:"):
        return None
    revision = basis.split("@", 1)[-1].split(" ", 1)[0]
    try:
        released_source = subprocess.run(
            ["git", "show", f"{revision}:ssot/{slug}.md"], cwd=repo_root,
            capture_output=True, timeout=10, check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    if canonical.read_bytes() != released_source:
        return None
    previous = next((entry for entry in baseline.get("ssot_sources", []) if entry["slug"] == slug), {})
    released = set(previous.get("expected_surface_names", []))
    candidate_surfaces = {surface for surfaces in emitted_surfaces_by_cli(capability).values() for surface in surfaces}
    if not any(name.endswith("_agent") for name in released) or candidate_surfaces != released:
        return None
    return {"status": "preserved_existing_contract", "baseline": basis,
            "original_sha256": text_sha256(current), "candidate_sha256": text_sha256(candidate_text),
            "surfaces": sorted(released), "quality_evidence": "retained_not_rejudged",
            "behavioral_status": "not_retested"}
