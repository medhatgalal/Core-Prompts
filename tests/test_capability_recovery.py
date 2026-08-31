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
        closing = text.find('\n---\n', 4)
        assert closing != -1
        assert '\n---\nname:' not in text[closing + 5 :]
        for heading in headings:
            assert heading in text


def test_analyze_context_memory_is_repository_scoped_outside_worktrees() -> None:
    text = (ROOT / 'ssot' / 'analyze-context.md').read_text(encoding='utf-8')

    required_contract = [
        'Never write canonical analysis state inside a branch, linked worktree, or main checkout.',
        'Do not treat session end, compaction, branch removal, or worktree removal as completion or cleanup authority.',
        'ACTIVE_WORKTREE_ROOT="$(git rev-parse --show-toplevel)"',
        'REPO_COMMON_DIR="$(git rev-parse --path-format=absolute --git-common-dir)"',
        'ANALYZE_CONTEXT_STATE_HOME',
        'STATE_HOME="${ANALYZE_CONTEXT_STATE_HOME:-$HOME/.analyze-context}"',
        'TASK_DIR="$STATE_HOME/$PROJECT_ID/$TASK_ID"',
        'Verify `TASK_DIR` is outside every worktree',
        '`<task-id>-context.md`',
        '`<task-id>-todo.md`',
        '`<task-id>-insights.md`',
        'every checkbox in `<task-id>-todo.md` is checked',
        'Completed files may remain on disk.',
        'Hooks are optional reminders',
        'They must not invent findings, mark completion, move files, or delete state.',
    ]
    for clause in required_contract:
        assert clause in text

    assert 'Create these files in `.analyze-context-memory/` at the project root.' not in text
    assert 'Always create and update the set under `ACTIVE_WORKTREE_ROOT/.analyze-context-memory/`' not in text
    assert '- One task gets one context/todo/insights set.' in text
    assert '- Do not fork versioned analysis files for the same task.' in text
    assert 'Do not clean up an incomplete task.' in text


def test_analyze_context_repository_state_contract_is_discoverable() -> None:
    docs = {
        'README.md': (ROOT / 'README.md').read_text(encoding='utf-8'),
        'docs/GETTING-STARTED.md': (ROOT / 'docs' / 'GETTING-STARTED.md').read_text(encoding='utf-8'),
        'docs/EXAMPLES.md': (ROOT / 'docs' / 'EXAMPLES.md').read_text(encoding='utf-8'),
    }

    for path, text in docs.items():
        assert 'analyze-context' in text, path
        assert '.analyze-context' in text, path
        assert 'context' in text and 'todo' in text and 'insights' in text, path

    assert 'branch and worktree paths are metadata only' in docs['README.md']
    assert '~/.analyze-context/<project>/<task-id>/' in docs['docs/EXAMPLES.md']
    assert 'leave completed files on disk until later user-approved cleanup' in docs['docs/EXAMPLES.md']


def test_capability_templates_exist_for_all_supported_types() -> None:
    template_dir = ROOT / '.meta' / 'capability-templates'
    for name in ('skill', 'agent', 'both'):
        payload = json.loads((template_dir / f'{name}.json').read_text(encoding='utf-8'))
        assert payload['template'] == name
        assert payload['required_headings']
        assert payload['benchmark_dimensions']
        assert payload['section_stubs']
