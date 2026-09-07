from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/eng-report.py'


@pytest.fixture
def report_config(tmp_path: Path) -> Path:
    repo = tmp_path / 'fixture-repo'
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
    (repo / 'example.txt').write_text('one line\n')
    subprocess.run(['git', '-C', str(repo), 'add', 'example.txt'], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Fixture',
                    '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
                    'commit', '-qm', 'feat: add fixture'], check=True)
    # The script reads remote-tracking history; no remote/network is configured.
    subprocess.run(['git', '-C', str(repo), 'update-ref', 'refs/remotes/origin/main', 'HEAD'], check=True)
    config = tmp_path / 'config.yaml'
    config.write_text(f'repos:\n  - name: fixture\n    path: {repo}\n')
    return config


def run_report(config: Path, output: Path, *options: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), 'run', '--config', str(config),
                           '--since', '2000-01-01', '--output', str(output), *options],
                          text=True, capture_output=True, check=True)


@pytest.mark.parametrize('existing', [False, True])
def test_json_returns_metrics_without_creating_or_overwriting_reports(
    report_config: Path, tmp_path: Path, existing: bool,
) -> None:
    output = tmp_path / 'reports'
    if existing:
        output.mkdir()
        (output / 'fixture.html').write_text('preserve this report')
        (output / 'eng-report-modal.js').write_bytes(b'preserve this JavaScript\x00')
        (output / '_index.html').write_text('preserve this index')
    before = {p.name: p.read_bytes() for p in output.glob('*')}
    result = run_report(report_config, output, '--json')
    rows = json.loads(result.stdout)
    assert rows[0]['commits'] == 1
    assert rows[0]['added'] == 1
    assert rows[0]['commit_subjects'] == ['feat: add fixture']
    assert {p.name: p.read_bytes() for p in output.glob('*')} == before
    assert output.exists() is existing


def test_html_report_still_renders(report_config: Path, tmp_path: Path) -> None:
    output = tmp_path / 'reports'
    run_report(report_config, output)
    assert 'feat: add fixture' in (output / 'fixture.html').read_text()
    assert (output / '_index.html').is_file()
    assert (output / 'eng-report-modal.js').is_file()
