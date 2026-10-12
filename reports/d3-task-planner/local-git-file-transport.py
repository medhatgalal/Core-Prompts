import hashlib
import json
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
real_run = subprocess.run
observations = []

def file_transport(args, *positional, **kwargs):
    if (isinstance(args, list) and args[-2:] == ['cat-file', '--batch']
            and isinstance(kwargs.get('input'), bytes)
            and kwargs.get('stdout') == subprocess.PIPE):
        request = kwargs.pop('input')
        with tempfile.TemporaryFile() as input_file, tempfile.TemporaryFile() as output_file:
            input_file.write(request)
            input_file.seek(0)
            kwargs.update(stdin=input_file, stdout=output_file, timeout=45)
            result = real_run(args, *positional, **kwargs)
            output_file.seek(0)
            output = output_file.read()
        observations.append({'argument_tail': args[-2:], 'request_count': len(request.splitlines()),
            'input_sha256': hashlib.sha256(request).hexdigest(), 'output_bytes': len(output),
            'output_sha256': hashlib.sha256(output).hexdigest(), 'returncode': result.returncode})
        return subprocess.CompletedProcess(result.args, result.returncode, output, result.stderr)
    return real_run(args, *positional, **kwargs)

if '--calibrate' in sys.argv:
    oid = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD:README.md']).strip()
    args = ['git', '-C', str(repo), 'cat-file', '--batch']
    request = oid + b'\n'
    original = real_run(args, input=request, stdout=subprocess.PIPE, check=True, timeout=10)
    adapted = file_transport(args, input=request, stdout=subprocess.PIPE, check=True)
    assert original.stdout == adapted.stdout
    print(json.dumps({'calibration': 'exact byte equality on known original pipe observation', **observations[0]}))
else:
    subprocess.run = file_transport
    script = repo / 'scripts/build-legacy-catalog.py'
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), '--check']
    try:
        runpy.run_path(str(script), run_name='__main__')
    finally:
        subprocess.run = real_run
        receipt = {'evidence_class': 'Adapted local Git batch I/O transport; same script, args and validation',
            'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
            'source_script_changed': False, 'observations': observations}
        (repo / 'reports/d3-task-planner/local-git-transport.json').write_text(json.dumps(receipt, indent=2) + '\n')
