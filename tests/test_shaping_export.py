"""Mechanical export coverage, never a semantic/visual/Google Docs certificate."""
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'sources/capability-resources/engos-delivery-artifact-embed/scripts/artifact_export.py'
SPEC = importlib.util.spec_from_file_location('shaping_export', SOURCE)
export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export)


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'bundle'; root.mkdir()
    (root/'pitch.md').write_text('# Fixture pitch\n\nUnverified proposal <script>alert(1)</script>\n', encoding='utf-8')
    for name in ('contracts.md','security-owners.md'):
        (root/name).write_text('# Table\n\n| ID | Meaning |\n| --- | --- |\n| A | one |\n| B | two |\n', encoding='utf-8')
    for name in export.DIAGRAMS:
        (root/name).write_text('flowchart LR\n A-->B\n', encoding='utf-8')
    return root


def test_full_source_and_all_rows_survive_json_and_html(source, tmp_path):
    data = export.bundle(source)
    assert data['table_row_counts']['contracts.md'] == [2]
    assert data['table_row_counts']['security-owners.md'] == [2]
    for item in data['documents']:
        assert item['markdown'] == (source/item['id']).read_text()
    rendered = export.html_document(data)
    assert rendered.count('<tr>') == 6
    assert rendered.count('class="mermaid"') == 3
    assert '<script>alert(1)</script>' not in rendered
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in rendered
    result = tmp_path/'export.json'
    assert export.main(['json','--bundle',str(source),'--output',str(result)]) == 0
    assert json.loads(result.read_text())['source_hash'] == data['source_hash']


def test_unchanged_repeat_is_noop_changed_export_refuses_overwrite(source, tmp_path):
    target = tmp_path/'export.html'
    args = ['html','--bundle',str(source),'--output',str(target)]
    assert export.main(args) == export.main(args) == 0
    previous = target.read_bytes()
    (source/'pitch.md').write_text('# Changed\n', encoding='utf-8')
    assert export.main(args) == 2
    assert target.read_bytes() == previous


@pytest.mark.parametrize('name', export.DOCUMENTS + export.DIAGRAMS)
def test_missing_required_content_fails(source, name):
    (source/name).unlink()
    with pytest.raises(export.ExportError):
        export.bundle(source)


def test_source_symlink_and_path_escape_rejected(source, tmp_path):
    outside = tmp_path/'outside.md'; outside.write_text('private')
    (source/'pitch.md').unlink(); (source/'pitch.md').symlink_to(outside)
    with pytest.raises(export.ExportError): export.bundle(source)
    with pytest.raises(export.ExportError): export.read_source(source, '../outside.md')


def test_tables_fail_on_malformed_rows_and_keep_escaped_pipe():
    with pytest.raises(export.ExportError): export.blocks('| A | B |\n| --- | --- |\n| one |')
    assert export.blocks('| A | B |\n| --- | --- |\n| x | y\\|z |')[0]['rows'] == [['x','y|z']]
    with pytest.raises(export.ExportError): export.blocks('```text\nunfinished')


def test_empty_tables_and_duplicate_document_inventory_refused(source):
    with pytest.raises(export.ExportError): export.bundle(source, [*export.DOCUMENTS,'pitch.md'])
    (source/'contracts.md').write_text('| A |\n| --- |\n')
    with pytest.raises(export.ExportError): export.bundle(source)


def test_section_identity_survives_unrelated_paragraph_insertion(source):
    first = export.bundle(source)['documents'][0]['blocks'][0]['id']
    pitch = source/'pitch.md'
    pitch.write_text('Introductory note\n\n'+pitch.read_text())
    heading = next(b for b in export.bundle(source)['documents'][0]['blocks'] if b['kind']=='heading')
    assert heading['id'] == first


def test_output_parent_symlink_is_refused(source, tmp_path):
    real = tmp_path/'real'; real.mkdir()
    link = tmp_path/'link'; link.symlink_to(real, target_is_directory=True)
    assert export.main(['json','--bundle',str(source),'--output',str(link/'out.json')]) == 2
    assert not (real/'out.json').exists()


def test_docx_missing_images_reports_error_without_creating_output(source, tmp_path):
    target = tmp_path/'out.docx'
    assert export.main(['docx','--bundle',str(source),'--output',str(target)]) == 2
    assert not target.exists()


def test_render_refuses_symlink_parent_before_launch(source, tmp_path, monkeypatch):
    real = tmp_path/'real'; real.mkdir()
    link = tmp_path/'link'; link.symlink_to(real, target_is_directory=True)
    calls = []
    def fake_run(argv, **kwargs):
        calls.append(argv)
        Path(argv[argv.index('-o')+1]).write_bytes(b'fixture image')
    monkeypatch.setattr(export.subprocess, 'run', fake_run)
    with pytest.raises(export.ExportError):
        export.render(export.bundle(source), source, link/'rendered', 'renderer')
    assert calls == []
    assert not (real/'rendered').exists()


def test_renderer_timeout_and_nonzero_are_bounded(tmp_path):
    start = time.monotonic()
    with pytest.raises(export.ExportError, match='timed out'):
        export.run_renderer([sys.executable, '-c', 'import time; time.sleep(10)'], .1)
    assert time.monotonic()-start < 3
    with pytest.raises(export.ExportError, match='exit 7') as error:
        export.run_renderer([sys.executable, '-c', 'import sys; print("x"*100000); sys.exit(7)'], 2)
    assert len(str(error.value)) < 18000


def test_exclusive_publication_rejects_late_destination_substitution(tmp_path, monkeypatch):
    target = tmp_path/'result.json'
    real_open = os.open
    def racing_open(path, flags, *args, **kwargs):
        if str(path) == target.name and flags & os.O_EXCL:
            target.write_bytes(b'user content')
        return real_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(export.os, 'open', racing_open)
    with pytest.raises(export.ExportError): export.write_new(target, b'generated')
    assert target.read_bytes() == b'user content'
