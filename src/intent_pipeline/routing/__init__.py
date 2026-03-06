"""Routing contract and normalization primitives for phase 3."""

from intent_pipeline.routing.contracts import (
    REQUIRED_UPLIFT_SECTIONS,
    ROUTING_CONTRACT_SCHEMA_VERSION,
    RouteProfile,
    RoutingBoundaryError,
    RoutingBoundaryErrorCode,
    RoutingContract,
    validate_uplift_artifact,
)
from intent_pipeline.routing.engine import SemanticRoutingResult, run_semantic_routing
from intent_pipeline.routing.rosetta import (
    ROSETTA_ROUTE_SPEC_SCHEMA_VERSION,
    RosettaEvidenceLink,
    RosettaRouteSpec,
    RosettaTranslationError,
    RosettaTranslationErrorCode,
    translate_to_route_spec,
)
from intent_pipeline.routing.semantic_router import (
    PRECEDENCE_ORDER,
    PROFILE_TIE_BREAK_ORDER,
    RouteSelection,
    select_route,
)
from intent_pipeline.routing.signal_bundle import ConstraintSignal, SignalBundle, build_signal_bundle

__all__ = [
    "ConstraintSignal",
    "PRECEDENCE_ORDER",
    "PROFILE_TIE_BREAK_ORDER",
    "REQUIRED_UPLIFT_SECTIONS",
    "ROSETTA_ROUTE_SPEC_SCHEMA_VERSION",
    "RosettaEvidenceLink",
    "RosettaRouteSpec",
    "RosettaTranslationError",
    "RosettaTranslationErrorCode",
    "RouteSelection",
    "ROUTING_CONTRACT_SCHEMA_VERSION",
    "RouteProfile",
    "RoutingBoundaryError",
    "RoutingBoundaryErrorCode",
    "RoutingContract",
    "SemanticRoutingResult",
    "SignalBundle",
    "build_signal_bundle",
    "run_semantic_routing",
    "select_route",
    "translate_to_route_spec",
    "validate_uplift_artifact",
]
