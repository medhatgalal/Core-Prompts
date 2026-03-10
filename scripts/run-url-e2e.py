#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from intent_pipeline.ingestion.url_policy import UrlSourceRejectedError
from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.phase6.contracts import ApprovalMode, ExecutionApprovalContract, ExecutionRequest
from intent_pipeline.phase6.engine import run_phase6
from intent_pipeline.pipeline import ingest_phase1_source, run_phase1_pipeline
from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uplift.engine import run_uplift_engine


def _normalize_path_prefix(url: str) -> str:
    parsed = urlsplit(url)
    return parsed.path or '/'


def _policy_rule_id(url: str) -> str:
    digest = sha256(url.encode('utf-8')).hexdigest()[:12]
    parsed = urlsplit(url)
    host = (parsed.hostname or 'unknown').replace('.', '-')
    return f'v1.url.{host}.{digest}'


def _extension_policy_payload() -> dict[str, object]:
    return {
        'schema_version': '1.0.0',
        'extension_mode': 'CONTROLLED',
        'rules': [
            {
                'rule_id': 'v1.url.allow',
                'source_kind': 'URL',
                'decision': 'ALLOW',
                'priority': 10,
                'evidence_paths': ['policy_contract.rules[0]'],
            }
        ],
    }


def _url_policy_payload(url: str, *, max_bytes: int, timeout_seconds: int) -> dict[str, object]:
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname:
        raise SystemExit('run-url-e2e.py requires an https URL with a host')
    return {
        'schema_version': '1.0.0',
        'rules': [
            {
                'rule_id': _policy_rule_id(url),
                'allowed_schemes': ['https'],
                'allowed_hosts': [parsed.hostname],
                'allowed_domains': [],
                'allowed_path_prefixes': [_normalize_path_prefix(url)],
                'allowed_content_types': ['text/markdown', 'text/plain'],
                'max_bytes': max_bytes,
                'redirect_limit': 2,
                'timeout_seconds': timeout_seconds,
                'priority': 10,
                'evidence_paths': ['url_policy.rules[0]'],
            }
        ],
    }


def _build_capability_matrix(route_spec_payload: dict[str, object]) -> dict[str, object]:
    route_profile = str(route_spec_payload['route_profile'])
    tool_id = f"tool-{route_profile.lower().replace('_', '-')}"
    return {
        'schema_version': '4.0.0',
        'tools': [
            {
                'tool_id': tool_id,
                'supported_route_profiles': [route_profile],
                'capabilities': ['cap.read', 'cap.write'],
            }
        ],
    }


def _build_policy_contract(route_spec_payload: dict[str, object], capability_matrix_payload: dict[str, object]) -> dict[str, object]:
    route_profile = str(route_spec_payload['route_profile'])
    tool_id = str(capability_matrix_payload['tools'][0]['tool_id'])
    capabilities = list(capability_matrix_payload['tools'][0]['capabilities'])
    return {
        'schema_version': '4.0.0',
        'route_to_tool': [{'route_profile': route_profile, 'tool_id': tool_id}],
        'required_capabilities': [{'route_profile': route_profile, 'capabilities': capabilities}],
        'blocked_dominant_rule_ids': [],
        'allowed_route_decisions': ['PASS_ROUTE'],
    }


def _build_registry(request: ExecutionRequest) -> dict[str, object]:
    return {
        'schema_version': '6.0.0',
        'entries': [
            {
                'adapter_id': 'hermetic-adapter',
                'route_profile': request.route_profile,
                'target_tool_id': request.target_tool_id,
                'capabilities': list(request.required_capabilities),
                'supports_simulation': True,
                'supports_execution': True,
                'rule_id': 'REGISTRY-RULE-001',
            }
        ],
    }


def _build_approval(request: ExecutionRequest, *, mode: ApprovalMode, key: str) -> ExecutionApprovalContract:
    return ExecutionApprovalContract(
        schema_version='6.0.0',
        approval_mode=mode,
        approval_id=f'approval-{mode.value.lower()}',
        approved_by='qa@example.com',
        approved_at='2026-03-10T10:00:00Z',
        expires_at='2026-03-11T10:00:00Z',
        idempotency_key=key,
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        required_capabilities=request.required_capabilities,
        policy_schema_version=request.policy_schema_version,
        policy_rule_ids=request.policy_rule_ids,
    )


def _compact(value: Any) -> Any:
    if hasattr(value, 'as_payload'):
        return value.as_payload()
    if is_dataclass(value):
        return asdict(value)
    return value


def _positive_report(url: str, *, max_bytes: int, timeout_seconds: int, execute_approved: bool) -> dict[str, Any]:
    extension_policy = _extension_policy_payload()
    url_policy = _url_policy_payload(url, max_bytes=max_bytes, timeout_seconds=timeout_seconds)
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_root = Path(temp_dir) / 'snapshots'
        journal_root = Path(temp_dir) / 'journals'
        now = datetime.now(timezone.utc)

        ingestion = ingest_phase1_source(
            url,
            extension_mode='CONTROLLED',
            route_profile='IMPLEMENTATION',
            requested_capabilities=('cap.read',),
            extension_policy=extension_policy,
            url_policy=url_policy,
            snapshot_root=snapshot_root,
        )
        summary = run_phase1_pipeline(
            url,
            extension_mode='CONTROLLED',
            route_profile='IMPLEMENTATION',
            requested_capabilities=('cap.read',),
            extension_policy=extension_policy,
            url_policy=url_policy,
            snapshot_root=snapshot_root,
        )
        uplift = run_uplift_engine(ingestion.raw_text, source_metadata=ingestion.source_metadata)
        routing = run_semantic_routing(uplift)
        capability_matrix_payload = _build_capability_matrix(routing.route_spec.as_payload())
        policy_contract_payload = _build_policy_contract(routing.route_spec.as_payload(), capability_matrix_payload)
        phase4_result = run_phase4(routing.route_spec.as_payload(), capability_matrix_payload, policy_contract_payload)
        phase5_result = run_phase5(phase4_result)
        request = ExecutionRequest.from_phase_results(
            phase4_result,
            phase5_result,
            policy_schema_version='4.0.0',
            policy_rule_ids=('POLICY-RULE-001',),
        )
        registry = _build_registry(request)
        phase6_simulate = run_phase6(
            request,
            _build_approval(request, mode=ApprovalMode.SIMULATE_ONLY, key='run-url-e2e-simulate'),
            registry,
            journal_root=journal_root / 'simulate',
            now=now,
        )
        phase6_execute = None
        if execute_approved and routing.route_selection.decision.value == 'PASS_ROUTE':
            phase6_execute = run_phase6(
                request,
                _build_approval(request, mode=ApprovalMode.EXECUTE_APPROVED, key='run-url-e2e-execute'),
                registry,
                journal_root=journal_root / 'execute',
                now=now,
            )

    uplift_payload = uplift.as_payload()
    routing_payload = routing.as_payload()
    phase4_payload = phase4_result.as_payload()
    phase5_payload = phase5_result.as_payload()
    simulate_payload = phase6_simulate.as_payload()
    execute_payload = phase6_execute.as_payload() if phase6_execute is not None else None
    return {
        'url': url,
        'normalized_source': ingestion.source_metadata['normalized_source'],
        'policy_rule_id': ingestion.source_metadata['policy_rule_id'],
        'content_sha256': ingestion.source_metadata['content_sha256'],
        'rendered_summary': summary,
        'uplift': {
            'primary_objective': uplift_payload['intent'].get('primary_objective'),
            'in_scope': uplift_payload['intent'].get('in_scope'),
            'out_of_scope': uplift_payload['intent'].get('out_of_scope'),
        },
        'routing': {
            'decision': routing_payload['route_selection']['decision'],
            'route_profile': routing_payload['route_selection']['route_profile'],
            'dominant_rule_id': routing_payload['route_selection']['dominant_rule_id'],
            'missing_evidence': routing_payload['route_selection']['missing_evidence'],
        },
        'phase4': {
            'validation_decision': phase4_payload['validation']['decision'],
            'validation_can_proceed': phase4_payload['validation']['can_proceed'],
            'fallback_decision': phase4_payload['fallback']['decision'],
        },
        'phase5': {
            'terminal_status': phase5_payload['output']['machine_payload']['terminal_status'],
            'output_code': phase5_payload['output']['machine_payload']['output_code'],
        },
        'phase6_simulate': {
            'decision': simulate_payload['decision'],
            'decision_code': simulate_payload['decision_code'],
            'journal_path': simulate_payload['journal_path'],
            'produced_artifacts': simulate_payload['produced_artifacts'],
        },
        'phase6_execute': None if execute_payload is None else {
            'decision': execute_payload['decision'],
            'decision_code': execute_payload['decision_code'],
            'journal_path': execute_payload['journal_path'],
            'produced_artifacts': execute_payload['produced_artifacts'],
        },
    }


def _rejection_report(error: UrlSourceRejectedError, url: str) -> dict[str, Any]:
    rejection = error.rejection
    return {
        'url': url,
        'normalized_source': rejection.normalized_source,
        'policy_rule_id': rejection.matched_rule_id,
        'rejection_code': rejection.code.value,
        'terminal_status': rejection.terminal_status,
        'detail': rejection.detail,
        'evidence_paths': list(rejection.evidence_paths),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run one URL through the intent pipeline end to end.')
    parser.add_argument('--url', required=True, help='HTTPS URL to process')
    parser.add_argument('--expect', choices=('accepted', 'rejected'), default='accepted')
    parser.add_argument('--execute-approved', action='store_true', help='Also run EXECUTE_APPROVED on the hermetic path')
    parser.add_argument('--max-bytes', type=int, default=524288)
    parser.add_argument('--timeout-seconds', type=int, default=15)
    args = parser.parse_args(argv)

    try:
        report = _positive_report(
            args.url,
            max_bytes=args.max_bytes,
            timeout_seconds=args.timeout_seconds,
            execute_approved=args.execute_approved,
        )
    except UrlSourceRejectedError as error:
        report = _rejection_report(error, args.url)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if args.expect == 'rejected' else 2

    print(json.dumps(report, indent=2, sort_keys=True))
    if args.expect == 'rejected':
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
