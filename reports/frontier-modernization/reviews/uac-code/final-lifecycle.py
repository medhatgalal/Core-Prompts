"""Independent confirmation-time and quality-loop-off review-binding probes."""
from pathlib import Path
import copy
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
HELPER = importlib.util.spec_from_file_location('review_probe_helpers', Path(__file__).with_name('recheck-variations.py'))
helper = importlib.util.module_from_spec(HELPER); HELPER.loader.exec_module(helper)


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix='uac-final-review-') as temporary:
        temporary = Path(temporary)
        source = (ROOT/'ssot/engos-quality-code-review.md').read_text()
        approved = helper.review_for(source, source, 'engos-quality-code-review')
        approved_bytes = json.dumps(approved).encode()
        review_path = temporary/'review.json'; review_path.write_bytes(approved_bytes)
        command = [sys.executable, str(ROOT/'scripts/uac-import.py'), '--mode', 'judge', '--source', 'ssot/engos-quality-code-review.md', '--benchmark-search', 'off', '--clarity', 'off', '--requirement-review', str(review_path)]
        spec = importlib.util.spec_from_file_location('uac_final_lifecycle', ROOT/'scripts/uac-import.py')
        uac = importlib.util.module_from_spec(spec); spec.loader.exec_module(uac)
        for mode in ['on', 'off']:
            review_path.write_bytes(approved_bytes)
            payload = json.loads(subprocess.run(command + ['--quality-loop', mode], cwd=ROOT, text=True, capture_output=True, check=True).stdout)
            assert payload['quality_result']['status'] == 'structural_ready'
            for variation in ['revoked', 'bytes_only_changed', 'removed', 'corrupt_json', 'replacement_path', 'captured_path_only_revoked', 'revoked_at_confirmation']:
                review_path.write_bytes(approved_bytes)
                args = SimpleNamespace(yes=True, quality_loop=mode, requirement_review=[review_path])
                rejected = copy.deepcopy(approved); rejected['verdict'] = 'rejected'
                if variation in ['revoked', 'captured_path_only_revoked']:
                    review_path.write_text(json.dumps(rejected))
                elif variation == 'bytes_only_changed':
                    review_path.write_text(json.dumps(approved, indent=2))
                elif variation == 'removed':
                    review_path.unlink()
                elif variation == 'corrupt_json':
                    review_path.write_text('{')
                elif variation == 'replacement_path':
                    other = temporary/'replacement.json'; other.write_bytes(approved_bytes)
                    args.requirement_review = [other]
                elif variation == 'revoked_at_confirmation':
                    args.yes = False
                if variation == 'captured_path_only_revoked':
                    args.requirement_review = []
                workspace = temporary/f'{mode}-{variation}'; workspace.mkdir()
                uac.ROOT = workspace
                def confirm(_):
                    review_path.write_text(json.dumps(rejected))
                    return 'yes'
                with patch('builtins.input', confirm):
                    actual = uac._apply_payload(copy.deepcopy(payload), args, ['ssot/engos-quality-code-review.md'])
                unchanged = not list(workspace.iterdir())
                results.append({'quality_loop': mode, 'variation': variation, 'status': actual['status'], 'no_writes': unchanged})
                assert actual['status'] == 'stale_evidence' and unchanged, results[-1]
        # Positive control: unchanged files allow production apply to write the
        # fixture. Generators are absent, so build failure is expected afterward.
        review_path.write_bytes(approved_bytes)
        workspace = temporary/'unchanged-positive'; (workspace/'ssot').mkdir(parents=True)
        for directory in ['.meta/quality-profiles', '.meta/capability-templates']:
            (workspace/directory).mkdir(parents=True)
            for path in (ROOT/directory).glob('*.json'):
                shutil.copy2(path, workspace/directory/path.name)
        uac.ROOT = workspace
        actual = uac._apply_payload(copy.deepcopy(payload), SimpleNamespace(yes=True, quality_loop='off', requirement_review=[review_path]), ['ssot/engos-quality-code-review.md'])
        destination = workspace/'ssot/engos-quality-code-review.md'
        results.append({'variation': 'unchanged_positive_control', 'status': actual['status'], 'exact_ssot_written': destination.is_file() and destination.read_text() == source})
        assert results[-1]['exact_ssot_written'], results[-1]
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
