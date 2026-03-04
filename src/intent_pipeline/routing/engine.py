"""Phase-3 semantic routing orchestration."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

from intent_pipeline.routing.contracts import ROUTING_CONTRACT_SCHEMA_VERSION, validate_routing_schema_version, validate_uplift_artifact
from intent_pipeline.routing.rosetta import RosettaRouteSpec, translate_to_route_spec
from intent_pipeline.routing.semantic_router import RouteSelection, select_route
from intent_pipeline.routing.signal_bundle import SignalBundle, build_signal_bundle
from intent_pipeline.uplift.contracts import UpliftContract


@dataclass(frozen=True, slots=True)
class SemanticRoutingResult:
    """Deterministic phase-3 orchestration output contract."""

    schema_version: str
    uplift_schema_version: str
    signal_bundle: SignalBundle
    route_selection: RouteSelection
    route_spec: RosettaRouteSpec

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", validate_routing_schema_version(self.schema_version))
        object.__setattr__(self, "uplift_schema_version", _normalize_text(self.uplift_schema_version))

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "uplift_schema_version": self.uplift_schema_version,
            "signal_bundle": self.signal_bundle.as_payload(),
            "route_selection": self.route_selection.as_payload(),
            "route_spec": self.route_spec.as_payload(),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


def run_semantic_routing(
    uplift: UpliftContract | Mapping[str, Any],
) -> SemanticRoutingResult:
    """Compose uplift validation, signal extraction, routing, and Rosetta translation."""
    uplift_payload = validate_uplift_artifact(uplift)
    signal_bundle = build_signal_bundle(uplift_payload)
    route_selection = select_route(signal_bundle)
    route_spec = translate_to_route_spec(route_selection, signal_bundle, uplift_payload)

    return SemanticRoutingResult(
        schema_version=ROUTING_CONTRACT_SCHEMA_VERSION,
        uplift_schema_version=str(uplift_payload["schema_version"]),
        signal_bundle=signal_bundle,
        route_selection=route_selection,
        route_spec=route_spec,
    )


def _normalize_text(value: str) -> str:
    return value.strip()


__all__ = ["SemanticRoutingResult", "run_semantic_routing"]
