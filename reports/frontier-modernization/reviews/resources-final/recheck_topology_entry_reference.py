from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from core_prompts_eval.topology import compile_topology
from intent_pipeline.capability_resources import effective_capability_text
CASE=Path(__file__).with_name('recheck-entry-reference-fixture')
slug='review-entry'
entry=CASE/'ssot'/f'{slug}.md'
entry.parent.mkdir(parents=True,exist_ok=True)
entry.write_text('# Fixture\nMust read resources/resource-map.json and resources/absent.md.\n')
resource=CASE/'sources/capability-resources'/slug
resource.mkdir(parents=True,exist_ok=True)
(resource/'real.md').write_text('Required actual resource.\n')
(resource/'resource-map.json').write_text(json.dumps({'schema_version':'CapabilityResourceMap.v1','shared':[], 'routes':{'selected':['real.md']},'dependencies':{}}))
result={}
for name,fn in [('effective',lambda:effective_capability_text(CASE,slug,entry.read_text())),('topology',lambda:compile_topology(entry))]:
 try:
  fn(); result[name]={'accepted':True}
 except Exception as exc:
  result[name]={'accepted':False,'error':str(exc)}
Path(__file__).with_name('recheck-topology-entry-reference-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
