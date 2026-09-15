"""Namespace migration preserves registrations outside the selected update."""
import subprocess
import sys
import tomllib
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_filtered_namespace_registration_preserves_unselected_and_custom(tmp_path):
    config = tmp_path / '.codex' / 'config.toml'
    config.parent.mkdir()
    config.write_text('\n'.join([
        '# >>> core-prompts codex agents start >>>',
        '[agents.architecture]',
        f'config_file = "{tmp_path}/.codex/agents/architecture.toml"',
        '[agents.supercharge]',
        f'config_file = "{tmp_path}/.codex/agents/supercharge.toml"',
        '# <<< core-prompts codex agents end <<<',
        '[agents.pitch]',
        'config_file = "/custom/pitch.toml"',
    ]))
    command = [sys.executable, str(ROOT / 'scripts/register-codex-agents.py'),
               str(config), str(tmp_path), 'engos-meta-supercharge']
    subprocess.run(command, check=True)
    first = config.read_bytes()
    agents = tomllib.loads(first.decode())['agents']
    assert set(agents) == {'architecture', 'pitch', 'engos-meta-supercharge'}
    assert agents['architecture']['config_file'].endswith('/architecture.toml')
    assert agents['pitch']['config_file'] == '/custom/pitch.toml'
    assert agents['engos-meta-supercharge']['config_file'].endswith('/engos-meta-supercharge.toml')
    subprocess.run(command, check=True)
    assert config.read_bytes() == first


@pytest.mark.parametrize("empty_shell_argument", [False, True])
def test_prune_retired_clears_only_missing_catalogued_registrations(tmp_path, empty_shell_argument):
    config=tmp_path/'.codex/config.toml';config.parent.mkdir()
    live=tmp_path/'.codex/agents/engos-meta-supercharge.toml';live.parent.mkdir();live.write_text('name="approved"\n')
    config.write_text('\n'.join([
      '[agents.engos-design-architecture]',f'config_file = "{tmp_path}/.codex/agents/engos-design-architecture.toml"',
      '[agents.engos-meta-supercharge]',f'config_file = "{live}"',
      '[agents.personal]','config_file = "/custom/personal.toml"',
    ]))
    subprocess.run([sys.executable,str(ROOT/'scripts/register-codex-agents.py'),'--prune-retired-only',str(config),str(tmp_path)]+([''] if empty_shell_argument else []),check=True)
    assert set(tomllib.loads(config.read_text())['agents'])=={'engos-meta-supercharge','personal'}


def test_filtered_retirement_does_not_prune_unselected_missing_registrations(tmp_path):
    config=tmp_path/'.codex/config.toml';config.parent.mkdir()
    config.write_text('\n'.join([
      '[agents.engos-design-architecture]',f'config_file = "{tmp_path}/.codex/agents/engos-design-architecture.toml"',
      '[agents.engos-meta-supercharge]',f'config_file = "{tmp_path}/.codex/agents/engos-meta-supercharge.toml"',
    ]))
    subprocess.run([sys.executable,str(ROOT/'scripts/register-codex-agents.py'),'--prune-retired-only',str(config),str(tmp_path),'engos-meta-supercharge'],check=True)
    assert set(tomllib.loads(config.read_text())['agents'])=={'engos-design-architecture'}
