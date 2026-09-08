from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'src'))
from core_prompts_eval.topology import compile_topology
out={'descriptors':[],'topologies':[],'mode_rows':0,'clause_rows':0,'source_hash_rows':0}
for slug in ['engos-meta-supercharge','engos-optimization-auto-research']:
 canonical=json.loads((ROOT/'.meta/capabilities'/f'{slug}.json').read_bytes())
 paths=[ROOT/'.meta/capabilities'/f'{slug}.json']
 for host in ['codex','claude','gemini','kiro','grok']:
  paths.append(ROOT/f'.{host}/skills/{slug}/resources/capability.json')
  if host!='grok': paths.append(ROOT/f'.{host}/agents/resources/{slug}/capability.json')
 for path in paths:
  value=json.loads(path.read_bytes())
  assert value['modes']==canonical['modes'],path
  rows=[]
  for mode in value['modes']:
   assert len(mode['source_refs'])==1,mode
   source=mode['source_refs'][0]
   assert source==f'ssot/{slug}.md' or source.startswith(f'sources/capability-resources/{slug}/'),source
   raw=(ROOT/source).read_bytes().decode('utf-8').splitlines()[mode['source_line']-1]
   # Directly inspect the referenced declaration; do not re-run the mode extractor.
   declaration=re.sub(r'^[# ]+', '',raw).replace('`','').replace('*','')
   declaration=re.sub(r'^(?:Nested\s+)?MODULE:\s*','',declaration,flags=re.I)
   declaration=re.sub(r'^(?:\d+(?:\.\d+)*\.?\s+|Mode\s+\d+\s*:\s*)','',declaration,flags=re.I)
   assert declaration.strip()==mode['display_name'],(path,mode,raw)
   rows.append({'mode_slug':mode['mode_slug'],'source':source,'source_line':mode['source_line'],'raw_declaration':raw})
   out['mode_rows']+=1
  out['descriptors'].append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'modes':rows})
 topology=compile_topology(ROOT/'ssot'/f'{slug}.md')
 checked_in=json.loads((ROOT/'evals/topologies'/f'{slug}.json').read_bytes())
 assert topology==checked_in,slug
 for clause in topology['protected_invariants']:
  lines=(ROOT/clause['source']).read_bytes().decode('utf-8').splitlines()
  assert lines[clause['source_line']-1].strip()==clause['text'],clause
  out['clause_rows']+=1
 for source in topology['source_references']:
  assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256'],source
  out['source_hash_rows']+=1
 out['topologies'].append({'slug':slug,'resource_bundle_sha256':topology['resource_bundle_sha256'],'compiled_matches_checked_in':True,'clauses':len(topology['protected_invariants'])})
(HERE/'recheck-mode-provenance-result.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['descriptors','topologies']}|{'descriptors':len(out['descriptors']),'topologies':len(out['topologies'])},indent=2))
