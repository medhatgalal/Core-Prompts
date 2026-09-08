from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from core_prompts_eval.contracts import artifact_hash
from core_prompts_eval import adapters
from test_resource_delivery import setup_run,bind_arm,run
HERE=Path(__file__).parent
CASE=HERE/'real-pipe-fixture'
CASE.mkdir(exist_ok=True)
repo,plan_path=setup_run(CASE)
bind_arm(repo,plan_path,'baseline','Historical exact module.\r\nDo not use the candidate instructions.\r\n')
bind_arm(repo,plan_path,'candidate','New candidate exact module with Unicode: é λ.\n')
plan=json.loads(plan_path.read_text())
observations=[]
OriginalPopen=adapters.subprocess.Popen
class ObservedPopen(OriginalPopen):
 def communicate(self,input=None,timeout=None):
  stdout,stderr=super().communicate(input=input,timeout=timeout)
  if input is not None:
   request=json.loads(input)
   if request.get('schema_version')=='EvalAdapterRequest.v1':
    observations.append({'argv':self.args,'stdin':request,'stdin_sha256':hashlib.sha256(input).hexdigest(),'stdout':json.loads(stdout),'stderr':stderr.decode(),'returncode':self.returncode})
  return stdout,stderr
adapters.subprocess.Popen=ObservedPopen
try:
 result=run(repo,plan_path)
finally:
 adapters.subprocess.Popen=OriginalPopen
assert result['status']=='completed',result
assert len(observations)==4,observations
run_dir=Path(result['artifact_path'])
for index,obs in enumerate(observations):
 request=obs['stdin']
 arm='baseline' if request['entry_sha256']==plan['baseline_sha256'] else 'candidate'
 expected='Historical exact module.\r\nDo not use the candidate instructions.\r\n' if arm=='baseline' else 'New candidate exact module with Unicode: é λ.\n'
 excluded='New candidate exact module' if arm=='baseline' else 'Historical exact module'
 assert expected in request['artifact']
 assert excluded not in request['artifact']
 assert request['artifact_sha256']==artifact_hash(request['artifact'])
 trace=json.loads((run_dir/'traces'/f'{index:06d}.json').read_text())
 assert trace['request_sha256']==artifact_hash(request)
 assert trace['artifact_delivery']['resource_binding']==request['resource_binding']
 assert obs['returncode']==0 and obs['stderr']==''
 assert obs['stdout']['output']=='fixture:'+hashlib.sha256(f"{request['trial_id']}\0{request['artifact_sha256']}".encode()).hexdigest()
(HERE/'real-pipe-observations.json').write_text(json.dumps({'result':result,'observations':observations,'evidence_limit':'Actual subprocess stdin delivery and transport bindings; no model consumption or compliance proof.'},indent=2)+'\n')
print(json.dumps({'status':result['status'],'subprocess_requests_captured':len(observations),'trace_bindings_match':True,'historical_candidate_separation':True,'paid_model_calls':0},indent=2))
