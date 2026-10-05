#!/usr/bin/env python3
"""Read-only handover selection, source reuse and adapter evidence consistency.

The caller supplies an accepted, trusted inventory. This helper cannot authenticate
acceptance, host observations, visual meaning or human authority. It never writes,
converts, renders or publishes. 'ready' means a reuse/selection plan, not delivery.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

FORMATS = ('html', 'google-doc', 'word', 'json', 'markdown')
DIAGRAMS = ('component', 'sequence', 'data-flow')
TABLES = ('contracts', 'security')


class DeliveryHold(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise DeliveryHold(reason)


def select_outputs(choices):
    require(isinstance(choices, (list, tuple)) and bool(choices), 'output_choice_pending')
    aliases = {'html': 'html', 'google doc': 'google-doc', 'google-doc': 'google-doc',
               'word': 'word', 'json': 'json', 'markdown': 'markdown'}
    selected = set()
    for choice in choices:
        require(isinstance(choice, str) and bool(choice.strip()), 'output_choice_pending')
        choice = choice.strip().casefold()
        if choice in ('all', 'all of them'):
            selected.update(FORMATS)
        else:
            require(choice in aliases, 'unsupported_output_choice')
            selected.add(aliases[choice])
    return [name for name in FORMATS if name in selected]


def span(lines, locator):
    require(isinstance(locator, str) and re.fullmatch(r'[1-9]\d*:[1-9]\d*', locator) is not None, 'invalid_inventory_span')
    start, end = map(int, locator.split(':'))
    require(start <= end <= len(lines), 'invalid_inventory_span')
    return '\n'.join(lines[start - 1:end])


def table_cells(row):
    # Escape-aware splitting keeps a literal \| inside a cell.
    cells = re.split(r'(?<!\\)\|', row.strip())
    require(len(cells) >= 3 and cells[0] == cells[-1] == '', 'invalid_table')
    return [cell.strip().replace('\\|', '|') for cell in cells[1:-1]]


def validate_inventory(source, inventory):
    require(isinstance(inventory, dict) and inventory.get('schema_version') == 'HandoverSourceInventory.v1', 'invalid_source_inventory')
    require(isinstance(inventory.get('source_id'), str) and bool(inventory['source_id'].strip()), 'missing_source_identity')
    require(isinstance(inventory.get('source_sha256'), str) and re.fullmatch('[a-f0-9]{64}', inventory['source_sha256']) is not None, 'invalid_source_hash')
    require(hashlib.sha256(source).hexdigest() == inventory['source_sha256'], 'source_hash_mismatch')
    text = source.decode('utf-8')
    lines = text.splitlines()
    diagrams = inventory.get('diagrams')
    require(isinstance(diagrams, list) and len(diagrams) == 3 and {d.get('id') for d in diagrams if isinstance(d, dict)} == set(DIAGRAMS), 'incomplete_diagram_inventory')
    blocks = re.findall(r'^```mermaid\s*\n.*?^```\s*$', text, re.MULTILINE | re.DOTALL)
    # Compare the whole structural inventory, never keyword counts or substring presence.
    actual_blocks = [b.rstrip() for b in blocks]
    expected_blocks = []
    occupied = set()
    for diagram in diagrams:
        require(isinstance(diagram.get('markdown'), str), 'missing_diagram_source')
        content = span(lines, diagram.get('locator'))
        require(content == diagram['markdown'], 'diagram_source_inventory_mismatch')
        require(content.startswith('```mermaid\n') and content.endswith('\n```'), 'invalid_mermaid_fence')
        require(bool(content[11:-4].strip()), 'empty_diagram_source')
        if diagram['id'] == 'sequence':
            require(content.splitlines()[1].strip() == 'sequenceDiagram', 'invalid_sequence_source')
        require(bool(diagram.get('caption', '').strip()) and span(lines, diagram.get('caption_locator')) == diagram['caption'], 'caption_inventory_mismatch')
        require(diagram['locator'] not in occupied, 'duplicate_diagram_span')
        occupied.add(diagram['locator'])
        expected_blocks.append(content)
    require(actual_blocks == expected_blocks, 'mermaid_inventory_mismatch')
    tables = inventory.get('tables')
    require(isinstance(tables, list) and len(tables) == 2 and {t.get('id') for t in tables if isinstance(t, dict)} == set(TABLES), 'incomplete_table_inventory')
    table_spans = set()
    for table in tables:
        content = span(lines, table.get('locator'))
        require(content == table.get('markdown'), 'table_source_inventory_mismatch')
        start, end = map(int, table['locator'].split(':'))
        require((start == 1 or not lines[start - 2].lstrip().startswith('|')) and
                (end == len(lines) or not lines[end].lstrip().startswith('|')), 'partial_table_span')
        rows = content.splitlines()
        require(len(rows) >= 3, 'empty_table')
        columns = table_cells(rows[0])
        separators = table_cells(rows[1])
        require(len(columns) == len(separators) and all(re.fullmatch(r':?-{3,}:?', c) for c in separators), 'invalid_table_separator')
        cells = [table_cells(row) for row in rows[2:]]
        require(all(len(row) == len(columns) for row in cells), 'incomplete_table_row')
        require(columns == table.get('columns') and cells == table.get('rows'), 'table_inventory_mismatch')
        require(table['locator'] not in table_spans, 'duplicate_table_span')
        table_spans.add(table['locator'])
    return text


def expected_tables(inventory):
    return [{'id': t['id'], 'columns': t['columns'], 'rows': t['rows']} for t in inventory['tables']]


def expected_diagrams(inventory):
    return [{'id': d['id'], 'markdown': d['markdown'], 'caption': d['caption']} for d in inventory['diagrams']]


def validate_delivery_evidence(format_name, inventory, evidence):
    """Validate explicit adapter records, not their authenticity or pixel meaning.

    content_sha256/text_inventory_sha256 are canonical normalized full-content
    digests reconstructed by the adapter from independent saved-target readback,
    NOT raw DOCX/HTML/cloud target byte hashes. This helper checks declarations;
    it cannot establish that reconstruction happened or that pixels were inspected.
    """
    try:
        require(format_name in FORMATS and isinstance(evidence, dict), 'invalid_delivery_evidence')
        require(evidence.get('source_sha256') == inventory['source_sha256'], 'delivery_source_mismatch')
        require(evidence.get('content_sha256') == inventory['source_sha256'], 'delivery_content_mismatch')
        require(evidence.get('tables') == expected_tables(inventory), 'delivery_table_inventory_mismatch')
        require(evidence.get('diagrams') == expected_diagrams(inventory), 'delivery_diagram_inventory_mismatch')
        require(isinstance(evidence.get('host_observation_ref'), str) and bool(evidence['host_observation_ref'].strip()), 'missing_host_observation')
        if format_name == 'markdown':
            require(evidence.get('reused_source') is True, 'markdown_not_reused')
        else:
            require(isinstance(evidence.get('target_id'), str) and bool(evidence['target_id'].strip()), 'missing_saved_target')
        if format_name in ('word', 'google-doc'):
            require(evidence.get('native_editable_tables') is True, 'tables_not_native_editable')
            require(evidence.get('image_inventory') == list(DIAGRAMS), 'delivery_image_inventory_mismatch')
            require(evidence.get('text_inventory_sha256') == inventory['source_sha256'], 'delivery_text_inventory_mismatch')
        if format_name == 'word':
            require(evidence.get('reopened_saved_file') is True, 'word_not_reopened')
            count = evidence.get('page_count')
            require(type(count) is int and count > 0, 'invalid_word_page_count')
            require(evidence.get('inspected_pages') == list(range(1, count + 1)), 'word_pages_not_all_inspected')
            pixels = evidence.get('saved_page_pixels')
            require(isinstance(pixels, list) and len(pixels) == count and all(isinstance(ref, str) and ref.strip() for ref in pixels), 'missing_saved_word_pixels')
        if format_name == 'google-doc':
            revision = evidence.get('saved_revision')
            require(isinstance(revision, str) and bool(revision.strip()) and evidence.get('readback_revision') == revision, 'google_saved_revision_not_read_back')
        if format_name in ('html', 'google-doc'):
            pixels = evidence.get('saved_target_pixels')
            require(isinstance(pixels, list) and bool(pixels) and all(isinstance(ref, str) and ref.strip() for ref in pixels), 'missing_saved_target_pixels')
        if format_name == 'json':
            require(evidence.get('parsed') is True, 'json_not_parsed')
        return {'status': 'evidence_consistent', 'authenticity': 'not_established', 'visual_semantic_review': 'not_established'}
    except (DeliveryHold, KeyError, TypeError) as error:
        return {'status': 'hold', 'reason': str(error)}


def plan_outputs(source_path, accepted_inventory, choices, evidence=None):
    selected = []
    try:
        selected = select_outputs(choices)
        path = Path(source_path)
        require(not path.is_symlink(), 'source_symlink_not_reusable')
        source = path.read_bytes()
        validate_inventory(source, accepted_inventory)
        result = {'status': 'ready', 'selected': selected, 'delivery_status': 'pending',
                  'semantic_review': 'not_established', 'host_authenticity': 'not_established',
                  'limitations': 'Trusted accepted inventory and host observations are caller responsibilities; no writing, rendering or publishing occurs.'}
        if 'markdown' in selected:
            result['markdown'] = {'path': str(path), 'source_id': accepted_inventory['source_id'], 'sha256': accepted_inventory['source_sha256']}
        if evidence is not None:
            require(isinstance(evidence, dict) and set(evidence) <= set(selected), 'unselected_delivery_evidence')
            result['verification'] = {name: validate_delivery_evidence(name, accepted_inventory, evidence.get(name)) for name in selected}
        return result
    except (DeliveryHold, OSError, UnicodeError, TypeError, KeyError, AttributeError) as error:
        return {'status': 'hold', 'selected': selected, 'reason': str(error),
                'repair': 'candidate_reconciliation_and_affected_review', 'delivery_status': 'pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, help='Existing complete handover source; never written')
    parser.add_argument('--inventory', required=True, help='Trusted accepted HandoverSourceInventory.v1 JSON')
    parser.add_argument('--choice', action='append', default=[], help='Explicit selected output; repeat for multiple')
    parser.add_argument('--evidence', help='Optional selected-format adapter evidence JSON')
    args = parser.parse_args()
    try:
        inventory = json.loads(Path(args.inventory).read_text())
        evidence = json.loads(Path(args.evidence).read_text()) if args.evidence else None
        result = plan_outputs(args.source, inventory, args.choice, evidence)
    except (OSError, ValueError) as error:
        result = {'status': 'hold', 'reason': str(error), 'delivery_status': 'pending'}
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'ready' and all(v['status'] == 'evidence_consistent' for v in result.get('verification', {}).values()) else 2


if __name__ == '__main__':
    raise SystemExit(main())
