# Independent defect reproductions

Run from the task worktree. These use the actual loader with disposable fixtures; no test-source or product edits. The fixture root is resolved because macOS's default `/var` temporary path is itself a symlink and the new import policy rejects symlink ancestors.

```sh
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
import tempfile,json,hashlib
from intent_pipeline.capability_resources import load_capability_bundle,validate_shared_resource_imports

def fixture(p,raw=b'{"type":"object"}\n'):
 for slug in ('owner','consumer'):
  (p/'ssot').mkdir(exist_ok=True);(p/'ssot'/f'{slug}.md').write_text(f'---\nname: {slug}\n---\n')
  root=p/'sources/capability-resources'/slug;root.mkdir(parents=True)
  manifest={'schema_version':'CapabilityResourceMap.v1','shared':[],'routes':{'contract':['schema.json']},'dependencies':{}}
  if slug=='consumer':manifest['shared_imports']=['contract-v1']
  (root/'resource-map.json').write_text(json.dumps(manifest))
 (p/'sources/capability-resources/owner/schema.json').write_bytes(raw)
 (p/'.meta').mkdir();(p/'.meta/shared-resource-imports.json').write_text(json.dumps({'schema_version':'SharedResourceImports.v1','imports':[{'id':'contract-v1','owner':'owner','source':'schema.json','sha256':hashlib.sha256(raw).hexdigest(),'consumers':[{'slug':'consumer','destination':'schema.json'}]}]}))
 return load_capability_bundle(p,'consumer','','contract')
with tempfile.TemporaryDirectory() as d:
 p=Path(d).resolve(); b=fixture(p); root=p/'sources/capability-resources/consumer'
 for item in b['resources']:(root/item['path']).write_text(item['content'])
 (root/'shared-resource-imports.json').write_text(json.dumps(b['shared_imports']))
 (p/'.meta/shared-resource-imports.json').unlink()
 print('registry_missing_canonical_receipt:',validate_shared_resource_imports(p),load_capability_bundle(p,'consumer','','contract')['sha256']==b['sha256'])
with tempfile.TemporaryDirectory() as d:
 p=Path(d).resolve();b=fixture(p,b'{"\\u0024ref":"https://example.invalid/external-schema"}')
 print('escaped_json_ref_accepted:',b['resources'][0]['content'])
PY
```

Observed exit code: 0. Output:

```text
registry_missing_canonical_receipt: {} True
escaped_json_ref_accepted: {"\u0024ref":"https://example.invalid/external-schema"}
```

Both cases should fail closed. The first is high severity because detached receipt consistency substitutes for missing canonical registry authority. The second is medium severity because valid escaped JSON keys bypass a stated unsupported dependency-closure guard. No download or execution occurred.

Exact original, candidate and effective-package hashes are recorded in `review-source-bindings-pre-repair.json`. The loader hash in that receipt identifies the inspected implementation before repairs. Candidate source remains a four-line addition after the exact 864-line original; no approval attestation has yet been issued.
