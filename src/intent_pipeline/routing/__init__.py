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
from intent_pipeline.routing.signal_bundle import ConstraintSignal, SignalBundle, build_signal_bundle

__all__ = [
    "ConstraintSignal",
    "REQUIRED_UPLIFT_SECTIONS",
    "ROUTING_CONTRACT_SCHEMA_VERSION",
    "RouteProfile",
    "RoutingBoundaryError",
    "RoutingBoundaryErrorCode",
    "RoutingContract",
    "SignalBundle",
    "build_signal_bundle",
    "validate_uplift_artifact",
]
