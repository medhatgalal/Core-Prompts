"""Additional independent UAC probes; no canonical or generated source writes."""
from pathlib import Path
import copy
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
from intent_pipeline.uac_baselines import text_sha256, validate_requirement_review


def review_for(original, candidate, slug='fixture'):
    return {'schema_version': 'UACRequirementReview.v1', 'slug': slug,
            'original_sha256': text_sha256(original), 'candidate_sha256': text_sha256(candidate),
            'effective_sha256': text_sha256(candidate), 'verdict': 'approved',
            'reviewer': {'agent_id': 'independent-reviewer', 'author_agent_id': 'author', 'independent': True},
            'requirements': [{'id': 'all', 'source_start_line': 1, 'source_end_line': len(original.splitlines()),
                'disposition': 'preserved', 'candidate_excerpt': candidate,
                'rationale': 'The candidate is byte-identical to this original.'}]}


def main():
    results = {}
    original = 'Return findings.\n'
    valid = review_for(original, original)
    cases = []
    for field, value in [('slug', 'wrong'), ('verdict', 'rejected'), ('original_sha256', '0'*64), ('candidate_sha256', '0'*64), ('effective_sha256', '0'*64)]:
        invalid = copy.deepcopy(valid); invalid[field] = value
        for reviews in ([invalid], [valid, invalid], [invalid, valid]):
            cases.append(bool(quality.evaluate_imported_source_fidelity(original, original, slug='fixture', semantic_reviews=reviews)))
    results['all_15_stale_or_rejected_order_variations_blocked'] = all(cases)
    retired = copy.deepcopy(valid)
    retired['requirements'][0].update(disposition='retired', authorization='Synthetic conflicting authorization.')
    results['conflicting_approved_reviews_blocked'] = bool(quality.evaluate_imported_source_fidelity(original, original, slug='fixture', semantic_reviews=[valid, retired]))
    malformed = []
    for field in ['disposition', 'id', 'source_start_line', 'source_end_line', 'candidate_excerpt', 'rationale']:
        for value in [[], {}, False, None]:
            invalid = copy.deepcopy(valid); invalid['requirements'][0][field] = value
            malformed.append(bool(validate_requirement_review(invalid, slug='fixture', original_text=original, candidate_text=original, effective_text=original)))
    results['all_24_malformed_field_variations_refused_without_exception'] = all(malformed)
    results['same_mode_nested_rules_still_detect_conflict'] = bool(quality.semantic_review_findings('## Run mode\nAlways execute the prompt.\n### Rules\nNever execute the prompt.\n'))
    results['separate_module_headings_do_not_conflict'] = not quality.semantic_review_findings('## Module: Review\nNever execute the prompt.\n## Module: Execute\nAlways execute the prompt.\n')
    profile = quality.load_quality_profile(ROOT, 'fixture', 'default')
    report = {'judge_reports': [{'blockers': ['missing template heading: ## Required Output']}]}
    literals = ['````markdown\n```\n## Output Contract\nLiteral.\n````\n', '~~~~text\n~~~\n## Output Contract\nLiteral.\n~~~~\n', '```md\n``` invalid close\n## Output Contract\nLiteral.\n```\n', '    ## Output Contract\n    Literal.\n', '> ## Output Contract\n> Literal.\n']
    results['all_five_literal_variations_preserved'] = all(quality.refine_candidate_text(text, report, profile) == text for text in literals)
    with tempfile.TemporaryDirectory(prefix='uac-recheck-') as temporary:
        temporary = Path(temporary)
        source = (ROOT/'ssot/engos-quality-code-review.md').read_text()
        review = review_for(source, source, 'engos-quality-code-review')
        path = temporary/'review.json'; path.write_text(json.dumps(review))
        command = [sys.executable, str(ROOT/'scripts/uac-import.py'), '--mode', 'judge', '--source', 'ssot/engos-quality-code-review.md', '--benchmark-search', 'off', '--clarity', 'off', '--requirement-review', str(path)]
        payload = json.loads(subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True).stdout)
        results['valid_review_cli_positive_control'] = payload['quality_result']['status']
        review['verdict'] = 'rejected'; path.write_text(json.dumps(review))
        off = json.loads(subprocess.run(command + ['--quality-loop', 'off'], cwd=ROOT, text=True, capture_output=True, check=True).stdout)
        results['rejected_review_with_quality_loop_off'] = off['quality_result']['status']
        # Simulate the review file being replaced while apply awaits confirmation.
        # Production apply receives the genuinely approved earlier judge payload.
        spec = importlib.util.spec_from_file_location('uac_recheck', ROOT/'scripts/uac-import.py')
        uac = importlib.util.module_from_spec(spec); spec.loader.exec_module(uac)
        workspace = temporary/'workspace'; (workspace/'ssot').mkdir(parents=True)
        for directory in ['.meta/quality-profiles', '.meta/capability-templates']:
            (workspace/directory).mkdir(parents=True)
            for original_file in (ROOT/directory).glob('*.json'):
                shutil.copy2(original_file, workspace/directory/original_file.name)
        uac.ROOT = workspace
        applied = uac._apply_payload(payload, SimpleNamespace(yes=True, quality_loop='on', requirement_review=[path]), ['ssot/engos-quality-code-review.md'])
        results['review_changed_after_judge_apply_status'] = applied['status']
        results['review_changed_after_judge_ssot_written'] = (workspace/'ssot/engos-quality-code-review.md').is_file()
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
