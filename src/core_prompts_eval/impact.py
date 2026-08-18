from __future__ import annotations

from typing import Any, Iterable

from .contracts import PROFILE_TOKEN_CAPS


PROFILE_ORDER = ("static", "native", "routing-canary", "canary", "promotion", "cross-host", "sweep")

CHANGE_PROFILE = {
    "formatting": "static",
    "safe_metadata": "static",
    "name_description": "routing-canary",
    "invocation_hints": "routing-canary",
    "module_output": "canary",
    "state": "promotion",
    "safety": "promotion",
    "authority": "promotion",
    "tools": "promotion",
    "new_skill": "promotion",
    "merge": "promotion",
    "shared_template": "canary",
    "generator": "canary",
    "uac_engine": "canary",
    "model_effort": "cross-host",
    "unknown": "canary",
}


def build_impact_plan(slug: str, change_classes: Iterable[str], affected_clauses: Iterable[str] = ()) -> dict[str, Any]:
    normalized = sorted(set(change_classes)) or ["unknown"]
    profiles = [CHANGE_PROFILE.get(item, "canary") for item in normalized]
    selected = max(profiles, key=PROFILE_ORDER.index)
    return {
        "schema_version": "EvalImpactPlan.v1",
        "slug": slug,
        "change_classes": normalized,
        "affected_clause_ids": sorted(set(affected_clauses)),
        "minimum_profile": selected,
        "hard_token_cap": PROFILE_TOKEN_CAPS[selected],
        "narrowing_policy": "reviewed waiver required; narrowed runs cannot claim full promotion",
        "deterministic_fail_fast": True,
    }
