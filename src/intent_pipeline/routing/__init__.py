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

__all__ = [
    "REQUIRED_UPLIFT_SECTIONS",
    "ROUTING_CONTRACT_SCHEMA_VERSION",
    "RouteProfile",
    "RoutingBoundaryError",
    "RoutingBoundaryErrorCode",
    "RoutingContract",
    "validate_uplift_artifact",
]
