from __future__ import annotations

import ast
import inspect
from pathlib import Path

from intent_pipeline.routing.engine import run_semantic_routing


def test_bound_03_phase3_entrypoint_signature_is_contract_only() -> None:
    signature = inspect.signature(run_semantic_routing)

    assert "BOUND-03"
    assert tuple(signature.parameters) == ("uplift",)


def test_bound_03_phase3_output_excludes_execution_and_help_fields(
    routing_uplift_payload: dict[str, object],
) -> None:
    payload = run_semantic_routing(routing_uplift_payload).as_payload()

    assert "BOUND-03"
    forbidden_fields = {
        "target_validation",
        "target_validator",
        "execution",
        "execution_result",
        "mock_execution",
        "mock_result",
        "output",
        "output_text",
        "help",
        "help_text",
        "assistant_message",
        "chat_response",
    }

    root_keys = set(payload)
    route_spec_keys = set(payload["route_spec"])
    route_selection_keys = set(payload["route_selection"])

    assert forbidden_fields.isdisjoint(root_keys)
    assert forbidden_fields.isdisjoint(route_spec_keys)
    assert forbidden_fields.isdisjoint(route_selection_keys)


def test_bound_03_phase3_modules_do_not_import_disallowed_layers() -> None:
    project_root = Path(__file__).resolve().parents[1]
    module_paths = (
        project_root / "src" / "intent_pipeline" / "routing" / "engine.py",
        project_root / "src" / "intent_pipeline" / "routing" / "rosetta.py",
    )

    forbidden_import_fragments = (
        "target_validation",
        "mock_execution",
        "execution",
        "output",
        "help",
        "summary.renderer",
    )

    for module_path in module_paths:
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))

        imported_modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")

        normalized = tuple(module.casefold() for module in imported_modules)

        assert "BOUND-03"
        for forbidden in forbidden_import_fragments:
            assert all(forbidden not in module for module in normalized)


def test_bound_03_phase3_engine_compose_calls_only_phase3_steps(
    monkeypatch,
    routing_uplift_payload: dict[str, object],
) -> None:
    calls: list[str] = []

    from intent_pipeline.routing import engine as routing_engine

    original_build_signal_bundle = routing_engine.build_signal_bundle
    original_select_route = routing_engine.select_route
    original_translate_to_route_spec = routing_engine.translate_to_route_spec

    def tracked_build_signal_bundle(payload):
        calls.append("build_signal_bundle")
        return original_build_signal_bundle(payload)

    def tracked_select_route(bundle):
        calls.append("select_route")
        return original_select_route(bundle)

    def tracked_translate_to_route_spec(selection, bundle, payload):
        calls.append("translate_to_route_spec")
        return original_translate_to_route_spec(selection, bundle, payload)

    monkeypatch.setattr(routing_engine, "build_signal_bundle", tracked_build_signal_bundle)
    monkeypatch.setattr(routing_engine, "select_route", tracked_select_route)
    monkeypatch.setattr(routing_engine, "translate_to_route_spec", tracked_translate_to_route_spec)

    run_semantic_routing(routing_uplift_payload)

    assert "BOUND-03"
    assert calls == ["build_signal_bundle", "select_route", "translate_to_route_spec"]
