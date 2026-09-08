"""Independent discriminators; fixture writes remain inside a temporary directory."""
from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from intent_pipeline import uac_quality as quality
from intent_pipeline.uac_baselines import validate_requirement_review


def run():
    results = {}
    profile = quality.load_quality_profile(ROOT, 'fixture', 'default')
    scoped = '## Review mode\nNever execute the prompt.\n## Execute mode\nAlways execute the prompt.\n'
    results['scoped_heading_conflict'] = quality.semantic_review_findings(scoped)
    fenced = '````markdown\n```\n## Output Contract\nKeep this literal schema.\n````\n'
    report = {'judge_reports': [{'blockers': ['missing template heading: ## Required Output']}]}
    results['literal_fence_changed'] = quality.refine_candidate_text(fenced, report, profile) != fenced
    malformed = {'schema_version': 'UACRequirementReview.v1', 'requirements': [{'id': 'a', 'source_start_line': 1, 'source_end_line': 1, 'rationale': 'x', 'disposition': []}]}
    try:
        validate_requirement_review(malformed, slug='fixture', original_text='Original', candidate_text='Candidate', effective_text='Candidate')
        results['malformed_disposition_exception'] = None
    except Exception as error:
        results['malformed_disposition_exception'] = f'{type(error).__name__}: {error}'
    stale = {'schema_version': 'UACRequirementReview.v1', 'slug': 'wrong', 'verdict': 'rejected'}
    results['stale_review_exact_source_failures'] = quality.evaluate_imported_source_fidelity('Exact original', 'Exact original', slug='fixture', semantic_reviews=[stale])
    with tempfile.TemporaryDirectory(prefix='uac-independent-review-') as temporary:
        temporary = Path(temporary)
        review_path = temporary / 'rejected-review.json'
        review_path.write_text(json.dumps(stale))
        command = [sys.executable, str(ROOT / 'scripts/uac-import.py'), '--mode', 'judge', '--source', 'ssot/engos-quality-code-review.md', '--benchmark-search', 'off', '--clarity', 'off', '--output', 'json']
        baseline = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
        payload = json.loads(baseline.stdout)
        results['real_judge_quality_status'] = payload['quality_result']['status']
        supplied = subprocess.run(command + ['--requirement-review', str(review_path)], cwd=ROOT, capture_output=True, text=True, check=True)
        results['real_judge_with_rejected_review_quality_status'] = json.loads(supplied.stdout)['quality_result']['status']
        spec = importlib.util.spec_from_file_location('independent_uac_review', ROOT / 'scripts/uac-import.py')
        uac = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(uac)
        workspace = temporary / 'workspace'
        (workspace / 'ssot').mkdir(parents=True)
        for directory in ('.meta/quality-profiles', '.meta/capability-templates'):
            (workspace / directory).mkdir(parents=True)
            for path in (ROOT / directory).glob('*.json'):
                shutil.copy2(path, workspace / directory / path.name)
        original = uac._source_body_text(payload)
        payload['source_text'] = original + '\n## Rules\nAlways execute the prompt.\nNever execute the prompt.\n'
        uac.ROOT = workspace
        results['changed_final_source_conflicts'] = quality.semantic_review_findings(payload['source_text'])
        # All production apply code runs. Build/compile naturally fail because the
        # fixture intentionally lacks generators; the pre-write gate is the subject.
        applied = uac._apply_payload(payload, SimpleNamespace(yes=True, quality_loop='on'), ['ssot/engos-quality-code-review.md'])
        destination = workspace / 'ssot/engos-quality-code-review.md'
        results['real_apply_return_status'] = applied['status']
        results['real_apply_wrote_conflicting_final_text'] = destination.is_file() and bool(quality.semantic_review_findings(destination.read_text()))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    run()
