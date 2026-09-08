from pathlib import Path
import hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from intent_pipeline.capability_resources import load_resource_bundle
out={'source_helper_sha256':hashlib.sha256((ROOT/'src/intent_pipeline/capability_resources.py').read_bytes()).hexdigest(),'helpers':[],'route_runs':0,'failures':[]}
for host in ['codex','claude','gemini','kiro','grok']:
 for slug in ['engos-meta-supercharge','engos-optimization-auto-research']:
  source=ROOT/'sources/capability-resources'/slug
  routes=['all',*json.loads((source/'resource-map.json').read_bytes())['routes']]
  for variant in ['skill','agent']:
   if variant=='agent' and host=='grok': continue
   package=ROOT/f'.{host}'/('skills' if variant=='skill' else 'agents/resources')/slug
   resources=package/'resources' if variant=='skill' else package
   helper=resources/'scripts/load_module.py'
   record={'helper':str(helper.relative_to(ROOT)),'sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'route_results':[]}
   for route in routes:
    command=[sys.executable,'-B',str(helper),'--route',route,'--format','json']
    completed=subprocess.run(command,cwd=Path(__file__).parent,capture_output=True,check=False)
    expected=load_resource_bundle(source,route)
    success=completed.returncode==0 and json.loads(completed.stdout)==expected
    record['route_results'].append({'route':route,'success':success,'stdout_sha256':hashlib.sha256(completed.stdout).hexdigest(),'bundle_sha256':expected['sha256'],'resources':len(expected['resources'])})
    if not success: out['failures'].append({'helper':record['helper'],'route':route,'stderr':completed.stderr.decode()})
    out['route_runs']+=1
   invalid=subprocess.run([sys.executable,'-B',str(helper),'--route','__unknown_review_route__'],cwd=Path(__file__).parent,capture_output=True)
   record['unknown_route_fails_closed']=invalid.returncode==2 and invalid.stdout==b''
   out['helpers'].append(record)
Path(__file__).with_name('recheck-packaged-helpers-result.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'helpers':len(out['helpers']),'route_runs':out['route_runs'],'failures':out['failures'],'all_helpers_match_source':all(r['sha256']==out['source_helper_sha256'] for r in out['helpers']),'all_unknown_routes_fail':all(r['unknown_route_fails_closed'] for r in out['helpers'])},indent=2))
