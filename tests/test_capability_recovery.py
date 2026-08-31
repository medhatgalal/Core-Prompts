from __future__ import annotations

import importlib.util
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATE_STORE_PATH = ROOT / 'sources' / 'capability-resources' / 'analyze-context' / 'state_store.py'


def _load_state_store():
    spec = importlib.util.spec_from_file_location('analyze_context_state_store', STATE_STORE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ['git', '-C', str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(path, 'init', '-b', 'main')
    _git(path, 'config', 'user.email', 'tests@example.com')
    _git(path, 'config', 'user.name', 'Analyze Context Tests')
    (path / 'README.md').write_text('test\n', encoding='utf-8')
    _git(path, 'add', 'README.md')
    _git(path, 'commit', '-m', 'initial')
    return path


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
        'resources/state_store.py',
        '<sanitized-repository-slug>--<first-12-sha256>',
        'ANALYZE_CONTEXT_STATE_HOME',
        'task paths that escape the resolved state root',
        'mode `0700`',
        'mode `0600`',
        'atomic-replace write path',
        'One task has one writer at a time.',
        '`<task-id>-context.md`',
        '`<task-id>-todo.md`',
        '`<task-id>-insights.md`',
        'every checkbox in `<task-id>-todo.md` is checked',
        'Completed files may remain on disk.',
        'Hooks are optional reminders',
        'They must not invent findings, mark completion, move files, delete state, or bypass one-writer ownership.',
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


def test_analyze_context_project_id_is_stable_across_linked_worktrees(tmp_path: Path) -> None:
    state_store = _load_state_store()
    repo = _init_repo(tmp_path / 'primary-repository-name')
    first = tmp_path / 'first-worktree-name'
    second = tmp_path / 'completely-different-worktree-name'
    _git(repo, 'worktree', 'add', '-b', 'first-slice', str(first))
    _git(repo, 'worktree', 'add', '-b', 'second-slice', str(second))

    common_primary, project_primary = state_store.derive_project_id(repo)
    common_first, project_first = state_store.derive_project_id(first)
    common_second, project_second = state_store.derive_project_id(second)

    assert common_primary == common_first == common_second
    assert project_primary == project_first == project_second
    assert project_primary.startswith('primary-repository-name--')


def test_analyze_context_project_id_distinguishes_same_basename_repositories(tmp_path: Path) -> None:
    state_store = _load_state_store()
    first = _init_repo(tmp_path / 'first-parent' / 'shared-name')
    second = _init_repo(tmp_path / 'second-parent' / 'shared-name')

    _, first_id = state_store.derive_project_id(first)
    _, second_id = state_store.derive_project_id(second)

    assert first_id.startswith('shared-name--')
    assert second_id.startswith('shared-name--')
    assert first_id != second_id


@pytest.mark.parametrize('task_id', ['a', 'task-1', 'task_name', 'a' * 80])
def test_analyze_context_accepts_safe_task_ids(task_id: str) -> None:
    state_store = _load_state_store()
    assert state_store.validate_task_id(task_id) == task_id


@pytest.mark.parametrize(
    'task_id',
    ['', '../escape', '..', 'task/name', 'task\\name', 'Task', 'task.id', '-task', 'task-', 'a' * 81, 'task\nname'],
)
def test_analyze_context_rejects_unsafe_task_ids(task_id: str) -> None:
    state_store = _load_state_store()
    with pytest.raises(state_store.StateStoreError):
        state_store.validate_task_id(task_id)


def test_analyze_context_paths_permissions_atomic_writes_and_locking(tmp_path: Path) -> None:
    state_store = _load_state_store()
    repo = _init_repo(tmp_path / 'repo')
    state_home = tmp_path / 'external-state'
    layout = state_store.resolve_layout(repo, 'safe-task', state_home)

    assert layout.task_dir.is_relative_to(layout.state_root)
    assert not layout.task_dir.is_relative_to(repo)
    state_store.initialize(layout)

    assert {path.name for path in layout.task_dir.iterdir()} == {
        'safe-task-context.md',
        'safe-task-todo.md',
        'safe-task-insights.md',
    }
    assert stat.S_IMODE(layout.state_root.stat().st_mode) == 0o700
    assert stat.S_IMODE(layout.task_dir.stat().st_mode) == 0o700
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in layout.files.values())

    state_store.atomic_write(layout, 'todo', '# Todo\n\n- [x] Verified')
    assert layout.todo_path.read_text(encoding='utf-8').endswith('- [x] Verified\n')
    assert not list(layout.task_dir.glob('*.tmp'))

    with state_store.task_write_lock(layout):
        with pytest.raises(state_store.StateStoreError, match='another writer'):
            state_store.atomic_write(layout, 'todo', '# Todo\n')
        with pytest.raises(state_store.StateStoreError, match='another writer'):
            state_store.atomic_write(layout, 'todo', '# Todo\n')


def test_analyze_context_rejects_state_inside_worktree(tmp_path: Path) -> None:
    state_store = _load_state_store()
    repo = _init_repo(tmp_path / 'repo')
    with pytest.raises(state_store.StateStoreError, match='outside Git worktrees'):
        state_store.resolve_layout(repo, 'safe-task', repo / '.state')


def test_analyze_context_cli_write_initializes_all_three_files(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / 'repo')
    state_home = tmp_path / 'external-state'
    input_path = tmp_path / 'context-input.md'
    input_path.write_text('# Goal\n\nRepair durable state\n', encoding='utf-8')

    proc = subprocess.run(
        [
            sys.executable,
            str(STATE_STORE_PATH),
            'write',
            '--cwd',
            str(repo),
            '--state-home',
            str(state_home),
            '--task-id',
            'write-task',
            '--kind',
            'context',
            '--input',
            str(input_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    task_dir = Path(payload['task_dir'])

    assert {path.name for path in task_dir.iterdir()} == {
        'write-task-context.md',
        'write-task-todo.md',
        'write-task-insights.md',
    }
    assert (task_dir / 'write-task-context.md').read_text(encoding='utf-8').endswith('Repair durable state\n')


def test_analyze_context_generated_surfaces_and_helper_match_ssot() -> None:
    source_text = (ROOT / 'ssot' / 'analyze-context.md').read_text(encoding='utf-8')
    source_body = source_text.split('\n---\n', 1)[1].strip()
    helper_bytes = STATE_STORE_PATH.read_bytes()

    for surface in ('.codex', '.gemini', '.claude', '.kiro'):
        skill_text = (ROOT / surface / 'skills' / 'analyze-context' / 'SKILL.md').read_text(encoding='utf-8')
        assert source_body in skill_text, surface
        generated_helper = ROOT / surface / 'skills' / 'analyze-context' / 'resources' / 'state_store.py'
        assert generated_helper.read_bytes() == helper_bytes, surface


def test_analyze_context_current_quality_matrix_excludes_legacy_contract() -> None:
    descriptor = json.loads((ROOT / '.meta' / 'capabilities' / 'analyze-context.json').read_text(encoding='utf-8'))
    historical = json.dumps(descriptor['historical_baseline'])
    current = json.dumps(descriptor['quality_validation_matrix'])

    assert '.analyze-context-memory/' in historical
    assert '.analyze-context-memory/' not in current
    assert '~/.analyze-context' in current
    assert '<task-id>-context.md' in current
    assert '<task-id>-todo.md' in current
    assert '<task-id>-insights.md' in current


def test_capability_templates_exist_for_all_supported_types() -> None:
    template_dir = ROOT / '.meta' / 'capability-templates'
    for name in ('skill', 'agent', 'both'):
        payload = json.loads((template_dir / f'{name}.json').read_text(encoding='utf-8'))
        assert payload['template'] == name
        assert payload['required_headings']
        assert payload['benchmark_dimensions']
        assert payload['section_stubs']
