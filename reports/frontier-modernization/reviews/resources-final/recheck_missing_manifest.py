from pathlib import Path
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'src'))
from intent_pipeline.capability_resources import effective_capability_text, ResourceContractError
from core_prompts_eval.topology import compile_topology
CASE = Path(__file__).with_name('recheck-missing-manifest-fixture')
slug = 'review-fixture'
entry = CASE/'ssot'/f'{slug}.md'
entry.parent.mkdir(parents=True, exist_ok=True)
entry.write_text('# Fixture\nMust use resources/resource-map.json to load the required module.\n')
resources = CASE/'sources/capability-resources'/slug
resources.mkdir(parents=True, exist_ok=True)
(resources/'module.md').write_text('# Module\nBehavioral instruction without a normative marker.\n')
manifest = resources/'resource-map.json'
manifest.write_text(json.dumps({'schema_version':'CapabilityResourceMap.v1','shared':[], 'routes':{'selected':['module.md']}, 'dependencies':{}}))
before = compile_topology(entry)
review = CASE/'evals/reviews'/f'{slug}.json'
review.parent.mkdir(parents=True, exist_ok=True)
ids=[c['id'] for c in before['protected_invariants']]
review.write_text(json.dumps({'schema_version':'CapabilityTopologyReview.v1','slug':slug, 'ssot_sha256':before['ssot_sha256'], 'resource_bundle_sha256':before['resource_bundle_sha256'], 'clause_mappings':{i:['fixture-case'] for i in ids},'waivers':[], 'risk_tiers':{'critical':[],'high':[],'standard':ids},'review_status':'human_reviewed'}))
manifest.rename(resources/'resource-map.removed.json')
results = {'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/intent_pipeline/capability_resources.py', ROOT/'src/core_prompts_eval/topology.py']}, 'entry_explicitly_requires_manifest':True}
try:
 effective = effective_capability_text(CASE,slug,entry.read_text())
 results['effective_missing_map'] = {'accepted':True, 'entry_only':effective==entry.read_text()}
except Exception as exc:
 results['effective_missing_map'] = {'accepted':False, 'exception':str(exc)}
try:
 after = compile_topology(entry)
 results['topology_missing_map'] = {'accepted':True,'review_status':after['review_status'],'resource_bundle_sha256':after.get('resource_bundle_sha256'),'source_references':after['source_references']}
except Exception as exc:
 results['topology_missing_map'] = {'accepted':False,'exception':str(exc)}
Path(__file__).with_name('recheck-missing-manifest-result.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
