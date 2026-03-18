from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_docs_review_and_gitops_review_land_as_both() -> None:
    docs = json.loads((ROOT / '.meta' / 'capabilities' / 'docs-review-expert.json').read_text(encoding='utf-8'))
    gitops_path = ROOT / '.meta' / 'capabilities' / 'gitops-review.json'
    if gitops_path.exists():
        gitops = json.loads(gitops_path.read_text(encoding='utf-8'))
    else:
        gitops = None

    assert docs['layers']['minimal']['capability_type'] == 'both'
    assert docs['layers']['minimal']['emitted_surfaces']['codex'] == ['codex_skill', 'codex_agent']
    assert docs['display_name'].startswith('Docs Review Expert')
    assert gitops is not None
    assert gitops['layers']['minimal']['capability_type'] == 'both'
    assert 'codex_agent' in gitops['layers']['minimal']['emitted_surfaces']['codex']


def test_rewritten_ssot_files_have_single_frontmatter_and_required_sections() -> None:
    expectations = {
        'supercharge.md': ['## Purpose', '## Primary Objective', '## Agent Operating Contract', '## Required Output', '## Evaluation Rubric'],
        'analyze-context.md': ['## Purpose', '## Primary Objective', '## Workflow', '## Required Output', '## Evaluation Rubric'],
        'converge.md': ['## Purpose', '## Primary Objective', '## Agent Operating Contract', '## Required Output', '## Evaluation Rubric'],
        'docs-review-expert.md': ['## Purpose', '## Agent Operating Contract', '## Review Timing', '## Evaluation Rubric'],
        'gitops-review.md': ['## Purpose', '## Agent Operating Contract', '## Required Companion Reviews', '## Evaluation Rubric'],
    }

    for name, headings in expectations.items():
        text = (ROOT / 'ssot' / name).read_text(encoding='utf-8')
        assert text.startswith('---\n')
        assert text.count('\n---\n') == 1
        for heading in headings:
            assert heading in text


def test_capability_templates_exist_for_all_supported_types() -> None:
    template_dir = ROOT / '.meta' / 'capability-templates'
    for name in ('skill', 'agent', 'both'):
        payload = json.loads((template_dir / f'{name}.json').read_text(encoding='utf-8'))
        assert payload['template'] == name
        assert payload['required_headings']
        assert payload['benchmark_dimensions']
        assert payload['section_stubs']
