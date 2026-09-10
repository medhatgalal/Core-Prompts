"""Validate public packet integrity; never dispatch models or score architecture prose."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from intent_pipeline.capability_resources import ResourceContractError, load_resource_bundle


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    results = []
    identity = json.loads((PACKET / 'identity.json').read_text())
    for path, record in identity['development_incumbent']['files'].items():
        assert digest(ROOT / path) == record['sha256'], f'Incumbent drift: {path}'
    results.append('incumbent and historical/control file identities unchanged')
    candidate = PACKET / 'candidate' / 'engos-design-architecture.md'
    resource_root = candidate.parent / 'resources'
    route_map = json.loads((resource_root / 'resource-map.json').read_text())
    routes = ['design-api', 'design-database', 'design-patterns', 'system-design']
    assert set(route_map['routes']) == set(routes)
    bundle_all = load_resource_bundle(resource_root, entry_text=candidate.read_text())
    bundles = {}
    for route in routes:
        b = load_resource_bundle(resource_root, route, entry_text=candidate.read_text())
        assert {x['path'] for x in b['resources']} == {'references/decision-and-evolution.md', f'references/{route}.md'}
        bundles[route] = {'sha256': b['sha256'], 'files': [x['path'] for x in b['resources']]}
    assert len(bundle_all['resources']) == 5
    results.append('existing resource loader assembled every complete route and mixed union')
    # A missing declared dependency must be a real failure, not a simulated label.
    with TemporaryDirectory(prefix='architecture-resource-control-') as tmp:
        t = Path(tmp)
        for path in resource_root.rglob('*'):
            if path.is_file() and path.name != 'design-api.md':
                dest = t / path.relative_to(resource_root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(path.read_bytes())
        for route in ['design-api', 'design-patterns']:
            try:
                load_resource_bundle(t, route)
            except ResourceContractError as exc:
                assert 'Missing or invalid resource file' in str(exc)
            else:
                raise AssertionError(f'Missing resource accepted for {route}')
    results.append('actually omitted resource rejected in selected and other route validation')
    cases = [json.loads(line) for line in (PACKET / 'public-cases.jsonl').read_text().splitlines()]
    ids = {x['id'] for x in cases}
    assert len(cases) == len(ids) == 17
    for c in cases:
        p = (PACKET / c['fixture']).resolve(strict=True)
        assert p.is_relative_to(PACKET / 'public-fixtures')
        assert p.stat().st_size > 100 and c['public_synthetic'] and not c['held_out']
        for rel in c.get('context_files', []):
            context = (PACKET / rel).resolve(strict=True)
            assert context.is_relative_to(PACKET / 'public-fixtures')
            assert context.stat().st_size > 0
            if context.suffix == '.json':
                json.loads(context.read_text())
    expected = json.loads((PACKET / 'public-expectations.json').read_text())['cases']
    assert {x['id'] for x in expected} == ids
    assert all(x['required_useful_outcomes'] and x['hard_veto_examples'] for x in expected)
    results.append('17 unique public tasks and matching expectations; instructional controls labeled')
    mapping = json.loads((PACKET / 'preservation-map.json').read_text())
    original = json.loads((ROOT / 'evals/contracts/engos-design-architecture.json').read_text())
    assert {x['source_clause_sha256'] for x in mapping['extracted_clause_mapping']} == set(original['protected_behaviors'])
    for m in mapping['extracted_clause_mapping'] + mapping['semantic_mapping']:
        assert set(m['public_cases']) <= ids and m['candidate_location']
    assert len(mapping['semantic_mapping']) == 12
    results.append('all 30 extracted clauses plus 12 semantic groups have author-proposed mappings')
    # Input-bound public oracle calculations, not a model-output scorer.
    oracle_expectations = {
        'system_overload': (60, 18000, 450, False),
        'system_capacity_variant': (60, 4800, 120, True),
        'system_capacity_feasible': (32, 0, 0, True),
    }
    calculated = {}
    for name, expected_values in oracle_expectations.items():
        data = json.loads((PACKET / 'public-fixtures' / (name + '.json')).read_text())['workload']
        capacity = data['workers'] / data['mean_service_s']
        backlog = max(0, (data['arrival_jobs_per_s'] - capacity) * data['burst_s'])
        assert capacity > data['after_jobs_per_s'], 'Drain undefined for this control'
        drain = backlog / (capacity - data['after_jobs_per_s'])
        queue_fits = backlog <= data['queue_limit']
        assert (capacity, backlog, drain, queue_fits) == expected_values, name
        calculated[name] = dict(capacity=capacity, backlog=backlog, drain=drain,
                               queue_fits=queue_fits, fluid_wait=backlog/capacity)
    variant = json.loads((PACKET / 'public-fixtures/system_capacity_variant.json').read_text())['workload']
    assert calculated['system_capacity_variant']['fluid_wait'] > variant['completion_target_s']
    assert calculated['system_capacity_feasible']['backlog'] == 0
    witness = json.loads((PACKET / 'public-fixtures/uniqueness_scenario.json').read_text())
    unique = lambda rows, fields: len({tuple(row[i] for i in fields) for row in rows}) == len(rows)
    assert unique(witness['old_rows'], witness['old_key_fields'])
    assert unique(witness['old_rows'], witness['new_key_fields'])
    assert unique(witness['new_rows'], witness['new_key_fields'])
    assert not unique(witness['new_rows'], witness['old_key_fields'])
    results.append('structured workload and uniqueness inputs drive public calculations; expected outcomes match')
    results.append('catalog SQL/API/requirements context resolves and JSON parses; emitted design not yet produced')
    manifest_path = PACKET / 'packet-manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for p, meta in manifest['files'].items():
            assert digest(PACKET / p) == meta['sha256'], f'Packet changed: {p}'
        results.append('frozen candidate, resources, tasks and assessment protocol hashes match')
    print(json.dumps({'status': 'pass', 'checks': results, 'route_bundles': bundles,
                      'model_calls': 0, 'proves': 'static public preparation integrity only',
                      'does_not_prove': ['runtime isolation', 'model quality', 'behavioral preservation', 'comparative improvement', 'formal promotion']}, indent=2))


if __name__ == '__main__':
    main()
