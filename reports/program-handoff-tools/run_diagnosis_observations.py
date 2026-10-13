"""Explicit disposable synthetic observations; not a production reproduction."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
cases = Path('sources/capability-resources/engos-debug-diagnose-failure/evals/diagnosis-cases.json')
frozen = cases.read_bytes()
source = b'def accepts(raw_now, expiry):\n    now = int(raw_now)\n    return not (now > expiry)\n'
namespace = {}; exec(compile(source, 'synthetic_expiry_fixture.py', 'exec'), namespace)
rows = [{'input':str(now),'parsed':int(str(now)),'expiry':10,'actual_accepts':namespace['accepts'](str(now),10),
         'contract_accepts':now < 10} for now in (9,10,11)]
intermittent = [{'attempt':i+1,'synthetic_failure_input':flag,'observed_failure':flag,'exit':0}
                for i,flag in enumerate([False,False,False])]
result = {'schema_version':'SyntheticDiagnosisObservations.v1','fixture_definition_sha256':hashlib.sha256(frozen).hexdigest(),
          'subject_source':source.decode(),'subject_source_sha256':hashlib.sha256(source).hexdigest(),
          'H-D1':rows,'H-D2':intermittent,'H-D3':{'required_input_available':False,'reproduction':'not_run',
          'exit':None,'reason':'Frozen case has no required input; no live reset or secret dump authorized.'}}
assert cases.read_bytes() == frozen
print(json.dumps(result,indent=2))
