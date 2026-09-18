from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


REQUIRED_FIELDS = {
    "primary_job",
    "use_when",
    "works_on",
    "main_output",
    "not_for",
    "authority",
    "routing_question",
    "nearest_neighbors",
    "shape",
    "portfolio_action",
}


def _validate_skill_job_map(payload: dict[str, Any], expected_slugs: Iterable[str]) -> dict[str, Any]:
    if payload.get("schema_version") not in {"SkillJobMap.v1", "SkillJobMap.v2"}:
        raise ValueError("skill job map must use SkillJobMap.v1 or SkillJobMap.v2")
    skills = payload.get("skills")
    if not isinstance(skills, dict):
        raise ValueError("skill job map requires a skills object")
    expected = set(expected_slugs)
    actual = set(skills)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"skill job map slug mismatch; missing={missing}, extra={extra}")
    for slug, job in skills.items():
        if not isinstance(job, dict):
            raise ValueError(f"{slug}: job contract must be an object")
        missing_fields = sorted(REQUIRED_FIELDS - set(job))
        if missing_fields:
            raise ValueError(f"{slug}: job contract missing {missing_fields}")
        for field in REQUIRED_FIELDS - {"nearest_neighbors"}:
            if not isinstance(job[field], str) or not job[field].strip():
                raise ValueError(f"{slug}: {field} must be a non-empty string")
        validate_routing_fitness(job)
        for companion in (job.get("routing_fitness") or {}).get("conditional_companions", []):
            if companion["skill"] not in expected:
                raise ValueError(f"{slug}: unknown routing companion")
        neighbors = job["nearest_neighbors"]
        if not isinstance(neighbors, list) or any(item not in expected or item == slug for item in neighbors):
            raise ValueError(f"{slug}: nearest_neighbors must reference other known skills")
    if payload.get("schema_version") == "SkillJobMap.v2":
        derived = build_advisory_job_map(skills)
        for field in ("review_status", "plain_english_note"):
            if payload.get(field) != derived[field]:
                raise ValueError("routing map cannot assert review or behavioral readiness")
        expected = derived["receipt"]
        if payload.get("receipt") != expected:
            raise ValueError("routing map receipt mismatch")
    return payload


def load_skill_job_map(path: Path, expected_slugs: Iterable[str]) -> dict[str, Any]:
    return _validate_skill_job_map(json.loads(path.read_text(encoding="utf-8")), expected_slugs)


def draft_skill_job(slug: str, display_name: str, description: str) -> dict[str, Any]:
    summary = description.strip().rstrip(".") or f"Perform the canonical {display_name} job"
    return {
        "primary_job": f"{summary}.",
        "use_when": f"The request directly matches the canonical purpose of {display_name}.",
        "works_on": "The inputs and target declared by the canonical SSOT.",
        "main_output": "The required output declared by the canonical SSOT.",
        "not_for": "Requests outside the canonical purpose; neighboring skills are not yet reviewed.",
        "authority": "No authority beyond the canonical SSOT and the user's explicit request.",
        "routing_question": f"Does this request directly require {display_name}?",
        "nearest_neighbors": [],
        "shape": "unclassified_new_skill",
        "portfolio_action": "draft_new_skill_pending_review",
    }


def load_skill_job_map_for_build(path: Path, skill_specs: Mapping[str, Mapping[str, str]]) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    skills = payload.get("skills")
    if not isinstance(skills, dict):
        raise ValueError("skill job map requires a skills object")
    unknown = sorted(set(skills) - set(skill_specs))
    if unknown:
        raise ValueError(f"skill job map has entries without canonical SSOT: {unknown}")
    for slug, spec in skill_specs.items():
        if slug not in skills:
            skills[slug] = draft_skill_job(slug, spec["display_name"], spec["description"])
            payload["review_status"] = "draft_for_human_review"
    return _validate_skill_job_map(payload, skill_specs)


def render_skill_job_map(payload: Mapping[str, Any], display_names: Mapping[str, str]) -> str:
    lines = [
        "# Skill Job Map",
        "",
        "This is a plain-English routing map, not behavioral proof and not a merger plan. The canonical behavior remains in `ssot/`.",
        "",
        "Version 2 includes source/effective-content bindings and source-clause routing fitness. This remains advisory; it does not configure native discovery, authorize actions, or establish behavioral improvement.",
        "",
        "Portfolio actions mean:",
        "",
        "- `keep`: the boundary is already focused.",
        "- `keep_and_clarify_boundary`: preserve the skill and sharpen how it differs from neighbors.",
        "- `keep_but_review_scope`: preserve it, then test whether its Swiss-army or advisory scope is too broad.",
        "- `experimental_keep_pending_evidence`: keep the experiment separate until routing and preservation evidence exists.",
        "- `keep_and_improve_process`: preserve the capability and improve its evidence or workflow controls.",
        "- `draft_new_skill_pending_review`: a new job is awaiting review; v2 includes source-backed clauses and explicit unresolved interpretations.",
        "",
        "No skill is marked for merger or deletion because current evidence does not justify either action.",
        "",
        "| Skill | Primary job | Use when | Main output | Not for | Closest neighbors | Portfolio action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for slug, job in payload["skills"].items():
        name = display_names.get(slug, slug)
        neighbors = ", ".join(f"`{item}`" for item in job["nearest_neighbors"]) or "none"
        cells = [
            f"`{slug}`<br>{name}",
            job["primary_job"],
            job["use_when"],
            job["main_output"],
            job["not_for"],
            neighbors,
            f"`{job['portfolio_action']}`",
        ]
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells) + " |")
    lines.extend(
        [
            "",
            "## Routing Questions",
            "",
        ]
    )
    for slug, job in payload["skills"].items():
        lines.append(f"- `{slug}`: {job['routing_question']}")
    lines.append("")
    return "\n".join(lines)


# The source compiler publishes descriptive evidence, never a runtime policy.
FITNESS_VERSION = "RoutingFitness.v1"
EXTRACTOR_VERSION = "source-clauses.v1"


def _digest(value: Any) -> str:
    import hashlib
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_clauses(text: str, path: str) -> list[dict[str, Any]]:
    """Keep paragraph/table-row boundaries and raw source locations; skip examples/code."""
    import re
    from .uac_extract import extract_uac_analysis_text
    analysis = extract_uac_analysis_text(text, path).analysis_text
    lines = text.splitlines()
    offset = text[:text.find(analysis)].count("\n") if analysis in text else 0
    heading, fence, pending, start = "", None, [], 0
    headings: list[tuple[int, str]] = []
    result: list[dict[str, Any]] = []
    def flush(end: int) -> None:
        if pending:
            result.append({"text": "\n".join(pending), "heading": heading,
                           "source": {"path": path, "start_line": start, "end_line": end,
                                      "sha256": _digest(text)}})
            pending.clear()
    for number, line in enumerate(analysis.splitlines(), offset + 1):
        stripped = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if marker:
            flush(number - 1)
            token = marker.group(1)
            if fence is None: fence = token
            elif token[0] == fence[0] and len(token) >= len(fence): fence = None
            continue
        if fence is not None: continue
        header = re.match(r"^(#{1,6}) +(.+)$", line)
        if header:
            flush(number - 1)
            level, title = len(header.group(1)), header.group(2).strip()
            headings[:] = [(depth, name) for depth, name in headings if depth < level]
            headings.append((level, title))
            heading = next((name for depth, name in headings if depth == 2), "")
            continue
        if not stripped or line.startswith("#") or stripped.startswith(">"):
            flush(number - 1); continue
        if any(word in title.lower() for _, title in headings for word in ("example", "rubric", "scorecard")): continue
        if stripped.startswith("|"):
            flush(number - 1)
            if re.fullmatch(r"[| :\-]+", stripped): continue
            result.append({"text": line, "heading": heading,
                           "source": {"path": path, "start_line": number, "end_line": number,
                                      "sha256": _digest(text)}})
            continue
        if not pending: start = number
        pending.append(line)
    flush(offset + len(analysis.splitlines()))
    return result


def compile_skill_job(repo_root: Path, slug: str, raw_text: str, *, display_name: str,
                      description: str, existing: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Source-grounded draft. Existing curation survives; absence never becomes permission."""
    import re
    from .capability_resources import load_capability_bundle, effective_capability_text
    job = json.loads(json.dumps(existing)) if existing else draft_skill_job(slug, display_name, description)
    previous = job.pop("routing_fitness", {})
    path = f"ssot/{slug}.md"
    clauses = _source_clauses(raw_text, path)
    bundle = load_capability_bundle(repo_root, slug, raw_text)
    resources = []
    if bundle:
        for item in bundle["resources"]:
            resource_path = f"sources/capability-resources/{slug}/{item['path']}"
            resources.append({"path": resource_path, "sha256": item["sha256"]})
            clauses.extend(_source_clauses(item["content"], resource_path))
    def section(*names: str) -> list[dict[str, Any]]:
        return [c for c in clauses if c["heading"].casefold() in {s.casefold() for s in names}]
    root_clauses = [c for c in clauses if c["source"]["path"] == path]
    field_sources: dict[str, Any] = {}
    if job.get("portfolio_action") == "draft_new_skill_pending_review":
        for key, headings in {"primary_job": ("Primary Objective", "Purpose"),
                              "use_when": ("Invocation Hints",), "works_on": ("Required Inputs",),
                              "main_output": ("Required Output",), "not_for": ("Out of Scope",),
                              "authority": ("Tool Boundaries",)}.items():
            selected = next(([c for c in root_clauses if c["heading"].casefold() == h.casefold()] for h in headings
                             if any(c["heading"].casefold() == h.casefold() for c in root_clauses)), [])
            if selected:
                job[key] = "\n\n".join(c["text"] for c in selected)
                field_sources[key] = selected
    missing_job_fields = sorted({"primary_job", "use_when", "works_on", "main_output", "not_for", "authority"} - set(field_sources)) if job.get("portfolio_action") == "draft_new_skill_pending_review" else []
    # Only an explicit owner-activation sentence can classify an explicit-only skill.
    owner = [c for c in root_clauses if c["heading"] in ("Purpose", "Agent Operating Contract", "Invocation Hints")]
    from .uac_extract import extract_uac_analysis_text
    from .uac_ssot import extract_display_name
    owner_name = extract_display_name(extract_uac_analysis_text(raw_text, path).analysis_text, slug).split("—", 1)[0].strip()
    subject = rf"(?:This (?:skill|capability)|{re.escape(owner_name)})"
    target = rf"(?:it|this (?:skill|capability)|`?{re.escape(slug)}`?)"
    invocation = rf"(?:invokes|(?:explicitly )?(?:requests|names)|(?:explicitly )?asks for)\s+{target}(?=[\s.,;]|$)"
    operative = re.compile(rf"^{subject}\s+is\s+(?:active|activated|invoked)\s+only when the user\s+(?:explicitly )?{invocation}", re.I)
    explicit = [c for c in owner if operative.search(" ".join(c["text"].split()))
                and not re.search(r"\b(?:unless|except)\b", c["text"], re.I)]
    timing = [c for c in section("Purpose", "Invocation Hints", "Review Timing", "Workflow")
              if re.search(r"\b(before|after|during|once|until)\b", c["text"], re.I)]
    boundaries = section("Tool Boundaries", "Constraints", "Out of Scope", "Boundaries")
    negatives = section("Out of Scope") + [c for c in section("Purpose", "Invocation Hints", "Constraints")
                                          if re.search(r"\b(?:do not|never|not for|not use)\b", c["text"], re.I)]
    companions = []
    unknown_companions = []
    companion_issues = []
    for clause in clauses:
        if "companion" not in clause["heading"].lower(): continue
        targets = sorted(set(re.findall(r"\bengos-[a-z0-9]+(?:-[a-z0-9]+)+\b", clause["text"])))
        for target in targets:
            if target == slug:
                companion_issues.append({"issue": "self_reference", "skill": target, "clause": clause})
                continue
            if not (repo_root / "ssot" / f"{target}.md").is_file():
                unknown_companions.append(target)
                companion_issues.append({"issue": "unavailable_in_corpus", "skill": target, "clause": clause})
                continue
            companions.append({"skill": target, "condition_and_handoff": clause["text"],
                               "source": clause["source"], "interpretation": "source_clause_requires_stage_review"})
    # Clauses are faithfully collected; semantic phase/risk interpretation is not inferred.
    unresolved = ["task_phase_interpretation", "risk_authority_interpretation"] + ["job_contract." + key for key in missing_job_fields]
    if any(x["issue"] == "self_reference" for x in companion_issues): unresolved.append("self_companion_reference")
    if unknown_companions: unresolved.append("unavailable_companions:" + ",".join(sorted(set(unknown_companions))))
    if not explicit: unresolved.append("implicit_activation_eligibility")
    if not timing: unresolved.append("task_phases")
    if not boundaries: unresolved.append("risk_authority_ceiling")
    if not negatives: unresolved.append("negative_examples")
    provenance = {"ssot_path": path, "ssot_sha256": _digest(raw_text),
                  "effective_sha256": _digest(effective_capability_text(repo_root, slug, raw_text)),
                  "resources": resources, "extractor_version": EXTRACTOR_VERSION,
                  "binding_scope": "SSOT and CapabilityResourceMap.v1 closure; other external references are not resolved",
                  "field_sources": field_sources, "unresolved_companion_clauses": companion_issues, "curated_fields": sorted(REQUIRED_FIELDS - set(field_sources)),
                  "curated_binding": "preserved_not_independently_revalidated"}
    fitness = {"schema_version": FITNESS_VERSION, "mapping_status": "source_derived_draft",
               "task_phases": {"kind": "source_conditions", "clauses": timing},
               "activation": {"mode": "explicit_only" if explicit else "unknown", "evidence": explicit},
               "risk_authority_ceiling": {"grants_authority": False, "clauses": boundaries},
               "negative_examples": {"kind": "source_exclusions_not_synthetic_prompts", "clauses": negatives},
               "conditional_companions": companions,
               "pack_hints": {"lead": slug, "companions": "only_after_applicable_source_conditions_are_checked",
                              "default_bulk_activation": False},
               "provenance": provenance, "unresolved_fields": unresolved}
    if previous.get("mapping_status") == "stale" or (previous.get("provenance") and
            previous["provenance"].get("effective_sha256") != provenance["effective_sha256"]):
        fitness["mapping_status"] = "stale"
    job["routing_fitness"] = fitness
    # Bind the job contract, including preserved curation; never retain self-asserted review grants.
    fitness["provenance"]["mapping_sha256"] = _digest(job)
    return job


def build_advisory_job_map(jobs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """One deterministic derived view. No timestamps or model-consumption claims."""
    skills = json.loads(json.dumps(dict(sorted(jobs.items()))))
    return {"schema_version": "SkillJobMap.v2", "review_status": "draft_for_human_review",
            "plain_english_note": "Source-bound advisory mapping; no runtime behavior or permission grant.",
            "skills": skills,
            "receipt": {"schema_version": "SkillJobMapReceipt.v1", "skills_sha256": _digest(skills),
                        "advisory_only": True, "behavioral_verified": False,
                        "source_bindings": {s: {k: j["routing_fitness"]["provenance"][k]
                                                for k in ("ssot_sha256", "effective_sha256", "mapping_sha256")}
                                            for s, j in skills.items()}}}


def validate_routing_fitness(job: Mapping[str, Any], repo_root: Path | None = None, slug: str | None = None) -> None:
    fitness = job.get("routing_fitness")
    if fitness is None: return  # Explicit legacy compatibility, not approval.
    required = {"schema_version", "mapping_status", "task_phases", "activation", "risk_authority_ceiling",
                "negative_examples", "conditional_companions", "pack_hints", "provenance", "unresolved_fields"}
    if not isinstance(fitness, dict) or required - set(fitness) or fitness.get("schema_version") != FITNESS_VERSION:
        raise ValueError("invalid RoutingFitness.v1 contract")
    containers = {"task_phases": dict, "activation": dict, "risk_authority_ceiling": dict,
                  "negative_examples": dict, "conditional_companions": list, "pack_hints": dict,
                  "provenance": dict, "unresolved_fields": list}
    if any(not isinstance(fitness[key], kind) for key, kind in containers.items()):
        raise ValueError("invalid routing fitness field types")
    if fitness["activation"].get("mode") not in {"unknown", "explicit_only"}:
        raise ValueError("automatic implicit eligibility is not established by this compiler")
    unresolved = fitness["unresolved_fields"]
    required_unresolved = {"task_phase_interpretation", "risk_authority_interpretation"}
    if fitness["activation"].get("mode") == "unknown": required_unresolved.add("implicit_activation_eligibility")
    if any(not isinstance(x, str) for x in unresolved) or not required_unresolved <= set(unresolved):
        raise ValueError("routing interpretation uncertainty is missing")
    import re
    from pathlib import PurePosixPath
    def check_clause(clause: Any) -> None:
        if not isinstance(clause, dict) or not isinstance(clause.get("text"), str) or not clause["text"].strip():
            raise ValueError("invalid source clause")
        source = clause.get("source", {})
        path = source.get("path", "")
        if (not isinstance(path, str) or not path or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts
                or "\\" in path or not re.fullmatch(r"[a-f0-9]{64}", str(source.get("sha256", "")))
                or type(source.get("start_line")) is not int or type(source.get("end_line")) is not int
                or not 1 <= source["start_line"] <= source["end_line"]):
            raise ValueError("invalid source clause binding")
    for field in ("task_phases", "risk_authority_ceiling", "negative_examples"):
        values = fitness[field].get("clauses")
        if not isinstance(values, list): raise ValueError("routing field requires source clauses")
        for clause in values: check_clause(clause)
    activation_evidence = fitness["activation"].get("evidence")
    if not isinstance(activation_evidence, list): raise ValueError("activation evidence must be an array")
    if fitness["activation"]["mode"] == "explicit_only" and not activation_evidence:
        raise ValueError("explicit-only activation needs source evidence")
    for clause in activation_evidence: check_clause(clause)
    for companion in fitness["conditional_companions"]:
        if not isinstance(companion, dict) or companion.get("skill") == fitness["pack_hints"].get("lead"):
            raise ValueError("invalid or self-referencing companion")
        if not re.fullmatch(r"engos-[a-z0-9]+(?:-[a-z0-9]+)+", str(companion.get("skill", ""))):
            raise ValueError("invalid companion identity")
        check_clause({"text": companion.get("condition_and_handoff"), "source": companion.get("source")})
        if companion.get("interpretation") != "source_clause_requires_stage_review":
            raise ValueError("companion cannot become an unconditional requirement")
        if repo_root is not None and not (repo_root / "ssot" / (companion["skill"] + ".md")).is_file():
            raise ValueError("unknown companion identity")
    provenance = fitness["provenance"]
    if any(not re.fullmatch(r"[a-f0-9]{64}", str(provenance.get(k, ""))) for k in ("ssot_sha256", "effective_sha256", "mapping_sha256")):
        raise ValueError("invalid routing provenance hashes")
    if fitness["mapping_status"] not in {"source_derived_draft", "stale"}:
        raise ValueError("routing fitness has no admitted review; status must remain draft or stale")
    if fitness["risk_authority_ceiling"].get("grants_authority") is not False or fitness["pack_hints"].get("default_bulk_activation") is not False:
        raise ValueError("routing metadata cannot grant authority or activate a bulk pack")
    candidate = json.loads(json.dumps(job))
    expected = candidate["routing_fitness"]["provenance"].pop("mapping_sha256", None)
    if expected != _digest(candidate): raise ValueError("routing mapping content hash mismatch")
    if repo_root is not None and slug is not None:
        source = (repo_root / "ssot" / f"{slug}.md").read_text(encoding="utf-8")
        from .capability_resources import effective_capability_text
        if fitness["provenance"].get("ssot_sha256") != _digest(source) or fitness["provenance"].get("effective_sha256") != _digest(effective_capability_text(repo_root, slug, source)):
            raise ValueError("routing source/effective content binding mismatch")

        rebuilt = compile_skill_job(repo_root, slug, source, display_name=slug, description="", existing=job)
        if rebuilt != job: raise ValueError("routing fields do not match their source-derived draft")
