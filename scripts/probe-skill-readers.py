"""Optional installed-reader check in disposable homes; no model turn or account state."""
import argparse
import os, json, subprocess, tempfile, selectors, time
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--codex', required=True, help='Absolute native Codex executable (not a home-dependent shim)')
parser.add_argument('--grok', required=True, help='Absolute Grok executable')
parser.add_argument('--output', required=True, type=Path)
args=parser.parse_args()
root=Path(tempfile.mkdtemp(prefix='core-prompts-readers-')); home=root/'home'; repo=root/'repo'; home.mkdir();repo.mkdir()
subprocess.run(['git','init','-q',str(repo)],check=True)
def skill(base,name,label):
 p=base/'skills'/name/'SKILL.md';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(f'---\nname: {name}\ndescription: {label}\n---\n{label}\n'); return p
paths={}
for vendor in ['.agents','.codex','.grok','.claude']:
 paths[vendor]=skill(home/vendor,'identity-probe',vendor+' user source')
rp=skill(repo/'.grok','identity-probe','native repository source')
crp=skill(repo/'.codex','repo-identity-probe','Codex generated repo source')
cap=skill(repo/'.agents','agents-repo-probe','Codex standard repo source')
env={'HOME':str(home),'CODEX_HOME':str(home/'.codex'),'PATH':os.environ['PATH'],'TERM':'dumb','GROK_CLAUDE_SKILLS_ENABLED':'false','GROK_CURSOR_SKILLS_ENABLED':'false'}
report={'fixture_root':str(root), 'policy':'disposable home; Claude and Cursor compatibility disabled; no model calls', 'scenarios':[]}
def grok(label):
 p=subprocess.run([args.grok,'inspect','--json'],cwd=repo,env=env,capture_output=True,text=True,timeout=25)
 x=json.loads(p.stdout) if p.returncode==0 else {'error':p.stderr}
 report['scenarios'].append({'name':label,'exit':p.returncode,'skills':x.get('skills',x)})
grok('repository native takes precedence')
rp.unlink();grok('home native plus agents compatibility')
(home/'.grok/config.toml').write_text('[skills]\nignore = ['+json.dumps(str(paths['.agents'].parent))+']\n')
grok('exact agents ignore keeps native home source')
paths['.grok'].unlink()
grok('agents ignore without native leaves only disabled compatibility skill')
(home/'.grok/config.toml').write_text('')
grok('agents fallback when native absent and ignore cleared')
# JSON-RPC app server only; no model turn, auth copy, or account request.
codex=args.codex
p=subprocess.Popen([codex,'app-server','--stdio'],cwd=repo,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
def request(message):
 p.stdin.write(json.dumps(message)+'\n');p.stdin.flush()
 end=time.monotonic()+20
 while time.monotonic()<end:
  if sel.select(1):
   line=p.stdout.readline()
   if not line:break
   x=json.loads(line)
   if x.get('id')==message['id']:return x
 return {'error':'timeout'}
try:
 report['codex_initialize']=request({'id':1,'method':'initialize','params':{'clientInfo':{'name':'source_probe','version':'1.0'},'capabilities':{'experimentalApi':True}}})
 result=request({'id':2,'method':'skills/list','params':{'cwds':[str(repo)],'forceReload':True}})
 report['codex_skills']=result
 paths['.codex'].unlink()
 result=request({'id':3,'method':'skills/list','params':{'cwds':[str(repo)],'forceReload':True}})
 report['codex_after_retirement']=result
finally:p.terminate();p.wait(timeout=10)
for key in ['codex_skills','codex_after_retirement']:
 for entry in report[key].get('result',{}).get('data',[]):
  entry['skills']=[s for s in entry['skills'] if s['scope']!='system']
report['grok_version']=subprocess.check_output([args.grok,'--version'],env=env,text=True).strip()
report['codex_version']=subprocess.check_output([args.codex,'--version'],env=env,text=True).strip()
errors=[]
expected=[rp.resolve(),paths['.grok'].resolve(),paths['.grok'].resolve(),None,paths['.agents'].resolve()]
for scenario, path in zip(report['scenarios'],expected):
 skills=[s for s in scenario['skills'] if s['name']=='identity-probe' and not s.get('disabled',False)]
 if scenario['exit'] or (path and (len(skills)!=1 or Path(skills[0]['source']['path']).resolve()!=path)) or (path is None and skills):
  errors.append(scenario['name'])
ignored=report['scenarios'][3]['skills']
if not any(s.get('disabled') and Path(s['source']['path']).resolve()==paths['.claude'].resolve() for s in ignored):
 errors.append('compatibility skill disabled-state readback')
for key,expected_home in [('codex_skills',{paths['.agents'].resolve(),paths['.codex'].resolve()}),('codex_after_retirement',{paths['.agents'].resolve()})]:
 data=report[key].get('result',{}).get('data',[])
 skills=[s for item in data for s in item['skills'] if s['enabled']]
 actual_home={Path(s['path']).resolve() for s in skills if s['name']=='identity-probe'}
 if actual_home != expected_home:
  errors.append(key+' home source identities')
 if {Path(s['path']).resolve() for s in skills if s['scope']=='repo'} != {crp.resolve(),cap.resolve()}:
  errors.append(key+' repository source identities')
report['errors']=errors
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'report':str(args.output),'errors':errors}))
raise SystemExit(bool(errors))
