"""Read-only selection and exact accepted-source parity; no semantic/host claims."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

HELPER = Path(__file__).resolve().parents[1] / 'sources/capability-resources/engos-design-shaping/scripts/handover_outputs.py'


def load_helper():
    spec = importlib.util.spec_from_file_location('handover_outputs', HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def complete(tmp_path):
    parts = ['# Handover\n\nAccepted proof and build/deferred/forbidden decisions.\n']
    diagrams = []
    for ident, source in [('component', 'flowchart LR\n A-->B'), ('sequence', 'sequenceDiagram\n A->>B: request'), ('data-flow', 'flowchart LR\n X-->Y')]:
        start = len(''.join(parts).splitlines()) + 1
        markdown = f'```mermaid\n{source}\n```\n'
        parts.append(markdown)
        end = len(''.join(parts).splitlines())
        caption = f'Figure: {ident} accepted caption.\n'
        caption_line = end + 1
        parts.append(caption)
        diagrams.append({'id': ident, 'locator': f'{start}:{end}', 'markdown': markdown.rstrip('\n'), 'caption_locator': f'{caption_line}:{caption_line}', 'caption': caption.rstrip('\n')})
    tables = []
    for ident, columns, rows in [('contracts', ['Input', 'Output', 'Owner'], [['request', 'result', 'team'], ['event', 'record', 'service']]), ('security', ['Responsibility', 'Owner', 'How enforced'], [['access', 'team', 'boundary'], ['audit', 'service', 'record']])]:
        parts.append('\n')
        start = len(''.join(parts).splitlines()) + 1
        markdown = '\n'.join(['| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join(['---'] * len(columns)) + ' |'] + ['| ' + ' | '.join(row) + ' |' for row in rows])
        parts.append(markdown + '\n')
        end = len(''.join(parts).splitlines())
        tables.append({'id': ident, 'locator': f'{start}:{end}', 'markdown': markdown, 'columns': columns, 'rows': rows})
    source = tmp_path / 'handover.md'
    source.write_text(''.join(parts))
    inventory = {'schema_version': 'HandoverSourceInventory.v1', 'source_id': 'handover-1', 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'diagrams': diagrams, 'tables': tables}
    return source, inventory


@pytest.mark.parametrize('choice,selected', [('HTML', ['html']), ('Google Doc', ['google-doc']), ('Word', ['word']), ('JSON', ['json']), ('Markdown', ['markdown']), ('all of them', ['html', 'google-doc', 'word', 'json', 'markdown'])])
def test_explicit_selection(complete, choice, selected):
    source, inventory = complete
    result = load_helper().plan_outputs(source, inventory, [choice])
    assert result['status'] == 'ready'
    assert result['selected'] == selected


@pytest.mark.parametrize('choices', [[], [''], ['   '], ['private conversion DOCX'], ['all four'], ['unknown'], ['Markdown', '']])
def test_empty_or_unsupported_choice_is_not_consent(complete, choices):
    source, inventory = complete
    result = load_helper().plan_outputs(source, inventory, choices)
    assert result['status'] == 'hold'
    assert result['selected'] == []


def test_private_docx_does_not_select_word(complete):
    source, inventory = complete
    result = load_helper().plan_outputs(source, inventory, ['Google Doc'])
    assert result['selected'] == ['google-doc']
    assert 'word' not in result['selected']


def test_markdown_is_idempotent_and_has_no_file_effect(complete):
    source, inventory = complete
    before = {p.name: p.read_bytes() for p in source.parent.iterdir()}
    first = load_helper().plan_outputs(source, inventory, ['Markdown'])
    second = load_helper().plan_outputs(source, inventory, ['markdown', 'Markdown'])
    assert first == second
    assert first['markdown'] == {'path': str(source), 'source_id': 'handover-1', 'sha256': inventory['source_sha256']}
    assert before == {p.name: p.read_bytes() for p in source.parent.iterdir()}
    assert first['semantic_review'] == 'not_established'


def test_changed_accepted_bytes_hold_without_overwrite(complete):
    source, inventory = complete
    original = source.read_bytes()
    source.write_text(source.read_text().replace('A-->B', 'A-->C'))
    changed = source.read_bytes()
    result = load_helper().plan_outputs(source, inventory, ['Markdown'])
    assert result['status'] == 'hold'
    assert result['reason'] == 'source_hash_mismatch'
    assert source.read_bytes() == changed != original


@pytest.mark.parametrize('change', ['diagram_source', 'caption', 'table_row', 'table_column', 'cross_span', 'missing_diagram', 'missing_table'])
def test_exact_inventory_mismatch_independently_holds(complete, change):
    source, inventory = complete
    # Keep source hash correct so inventory rejection is independently demonstrated.
    if change == 'diagram_source': inventory['diagrams'][0]['markdown'] = inventory['diagrams'][0]['markdown'].replace('A-->B', 'A-->C')
    elif change == 'caption': inventory['diagrams'][0]['caption'] = 'irrelevant quote'
    elif change == 'table_row': inventory['tables'][0]['rows'].pop()
    elif change == 'table_column': inventory['tables'][1]['columns'][0] = 'Different'
    elif change == 'cross_span': inventory['diagrams'][0]['locator'] = inventory['diagrams'][2]['locator']
    elif change == 'missing_diagram': inventory['diagrams'].pop()
    elif change == 'missing_table': inventory['tables'].pop()
    result = load_helper().plan_outputs(source, inventory, ['Markdown'])
    assert result['status'] == 'hold'
    assert result['reason'] != 'source_hash_mismatch'


def test_incomplete_accepted_source_requires_new_candidate_not_second_prose(complete):
    source, inventory = complete
    source.write_text(source.read_text().replace('```mermaid\nsequenceDiagram\n A->>B: request\n```', 'Missing sequence content'))
    inventory['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    incomplete = source.read_bytes()
    result = load_helper().plan_outputs(source, inventory, ['Markdown'])
    assert result['status'] == 'hold'
    assert result['repair'] == 'candidate_reconciliation_and_affected_review'
    assert source.read_bytes() == incomplete
    # An authorized caller supplies reviewed candidate bytes and renewed inventory.
    # The read-only helper grants no such authority and never modifies the snapshot.
    assert list(source.parent.iterdir()) == [source]


def test_cli_returns_same_source_and_json_hold(complete):
    source, inventory = complete
    binding = source.parent / 'inventory.json'
    binding.write_text(json.dumps(inventory))
    run = subprocess.run([sys.executable, str(HELPER), '--source', str(source), '--inventory', str(binding), '--choice', 'Markdown'], capture_output=True, text=True)
    assert run.returncode == 0
    assert json.loads(run.stdout)['markdown']['path'] == str(source)
    held = subprocess.run([sys.executable, str(HELPER), '--source', str(source), '--inventory', str(binding)], capture_output=True, text=True)
    assert held.returncode == 2
    assert json.loads(held.stdout)['status'] == 'hold'


def adapter_record(inventory, format_name):
    record = {'source_sha256': inventory['source_sha256'], 'content_sha256': inventory['source_sha256'],
              'text_inventory_sha256': inventory['source_sha256'], 'host_observation_ref': 'fake-test-host-observation',
              'target_id': 'saved-test-target', 'tables': [{'id': t['id'], 'columns': t['columns'], 'rows': t['rows']} for t in inventory['tables']],
              'diagrams': [{'id': d['id'], 'markdown': d['markdown'], 'caption': d['caption']} for d in inventory['diagrams']],
              'image_inventory': ['component', 'sequence', 'data-flow'], 'native_editable_tables': True,
              'reopened_saved_file': True, 'page_count': 3, 'inspected_pages': [1, 2, 3],
              'saved_page_pixels': ['fake-page-1', 'fake-page-2', 'fake-page-3'],
              'saved_revision': 'saved-revision-5', 'readback_revision': 'saved-revision-5',
              'saved_target_pixels': ['fake-saved-target-pixels'], 'parsed': True, 'reused_source': True}
    return record


@pytest.mark.parametrize('format_name', ['html', 'google-doc', 'word', 'json', 'markdown'])
def test_adapter_evidence_consistency_is_not_authenticity_or_delivery(complete, format_name):
    source, inventory = complete
    record = adapter_record(inventory, format_name)
    result = load_helper().plan_outputs(source, inventory, [format_name], {format_name: record})
    assert result['verification'][format_name]['status'] == 'evidence_consistent'
    assert result['verification'][format_name]['authenticity'] == 'not_established'
    assert result['delivery_status'] == 'pending'


@pytest.mark.parametrize('format_name,field,value,reason', [
    ('word', 'reopened_saved_file', False, 'word_not_reopened'),
    ('word', 'inspected_pages', [1, 3], 'word_pages_not_all_inspected'),
    ('word', 'saved_page_pixels', ['fake-first-page'], 'missing_saved_word_pixels'),
    ('word', 'page_count', True, 'invalid_word_page_count'),
    ('word', 'image_inventory', ['component'], 'delivery_image_inventory_mismatch'),
    ('word', 'text_inventory_sha256', 'source-only', 'delivery_text_inventory_mismatch'),
    ('google-doc', 'readback_revision', 'old-revision', 'google_saved_revision_not_read_back'),
    ('google-doc', 'native_editable_tables', False, 'tables_not_native_editable'),
    ('google-doc', 'saved_target_pixels', [], 'missing_saved_target_pixels'),
    ('google-doc', 'image_inventory', ['component', 'sequence'], 'delivery_image_inventory_mismatch'),
    ('html', 'saved_target_pixels', [], 'missing_saved_target_pixels'),
    ('json', 'parsed', False, 'json_not_parsed'),
    ('json', 'content_sha256', 'status-manifest-only', 'delivery_content_mismatch'),
    ('markdown', 'reused_source', False, 'markdown_not_reused'),
    ('google-doc', 'host_observation_ref', '', 'missing_host_observation'),
])
def test_saved_adapter_requirements_reject_each_independent_gap(complete, format_name, field, value, reason):
    _, inventory = complete
    record = adapter_record(inventory, format_name)
    record[field] = value
    result = load_helper().validate_delivery_evidence(format_name, inventory, record)
    assert result == {'status': 'hold', 'reason': reason}


@pytest.mark.parametrize('format_name', ['word', 'google-doc', 'json'])
def test_adapter_requires_every_native_table_row(complete, format_name):
    _, inventory = complete
    record = adapter_record(inventory, format_name)
    # JSON roundtrip avoids mutating the independent accepted inventory.
    record = json.loads(json.dumps(record))
    record['tables'][0]['rows'].pop()
    assert load_helper().validate_delivery_evidence(format_name, inventory, record)['reason'] == 'delivery_table_inventory_mismatch'


def test_unselected_word_evidence_cannot_turn_google_doc_conversion_into_word(complete):
    source, inventory = complete
    record = adapter_record(inventory, 'word')
    result = load_helper().plan_outputs(source, inventory, ['Google Doc'], {'word': record})
    assert result['status'] == 'hold'
    assert result['reason'] == 'unselected_delivery_evidence'


def test_renewed_reviewed_candidate_reuses_new_bytes_and_preserves_old_snapshot(complete):
    source, inventory = complete
    snapshot = source.read_bytes()
    candidate = source.parent / 'candidate.md'
    candidate.write_bytes(snapshot.replace(b'Accepted proof', b'Accepted proof, same scope'))
    renewed = json.loads(json.dumps(inventory))
    renewed['source_sha256'] = hashlib.sha256(candidate.read_bytes()).hexdigest()
    result = load_helper().plan_outputs(candidate, renewed, ['Markdown'])
    assert result['status'] == 'ready'
    assert result['markdown']['source_id'] == inventory['source_id']
    assert result['markdown']['sha256'] != inventory['source_sha256']
    assert source.read_bytes() == snapshot


def test_partial_table_span_cannot_hide_remaining_row(complete):
    source, inventory = complete
    table = inventory['tables'][0]
    start, end = map(int, table['locator'].split(':'))
    table['locator'] = f'{start}:{end-1}'
    table['markdown'] = '\n'.join(table['markdown'].splitlines()[:-1])
    table['rows'].pop()
    result = load_helper().plan_outputs(source, inventory, ['Markdown'])
    assert result['status'] == 'hold'
    assert result['reason'] == 'partial_table_span'


def test_symlink_is_not_same_source_reuse(complete):
    source, inventory = complete
    link = source.parent / 'alias.md'
    link.symlink_to(source)
    result = load_helper().plan_outputs(link, inventory, ['Markdown'])
    assert result['status'] == 'hold'
    assert result['reason'] == 'source_symlink_not_reusable'
    assert source.read_bytes() == link.read_bytes()


@pytest.mark.parametrize('change', ['extra_fence', 'truncated_fence', 'no_table_rows'])
def test_fresh_hash_does_not_make_incomplete_structural_content_valid(complete, change):
    source, inventory = complete
    if change == 'extra_fence':
        source.write_text(source.read_text() + '\n```mermaid\nflowchart LR\n Extra-->Diagram\n```\n')
    elif change == 'truncated_fence':
        source.write_text(source.read_text().replace('```mermaid\nsequenceDiagram\n A->>B: request\n```', '```mermaid\nsequenceDiagram\n A->>B: request'))
    else:
        inventory['tables'][0]['rows'] = []
    inventory['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    result = load_helper().plan_outputs(source, inventory, ['Markdown'])
    assert result['status'] == 'hold'
    assert result['reason'] != 'source_hash_mismatch'
