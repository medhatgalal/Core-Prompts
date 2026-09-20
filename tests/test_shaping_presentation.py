"""Synthetic public fixtures; mechanical presentation checks are not visual review."""
import base64
import importlib.util
import json
import os
import struct
import zlib
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'sources/capability-resources/engos-delivery-artifact-embed/scripts/artifact_export.py'
SPEC = importlib.util.spec_from_file_location('presentation_export', SOURCE)
export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export)


def png():
    def chunk(tag, raw):
        return struct.pack('>I', len(raw)) + tag + raw + struct.pack('>I', zlib.crc32(tag + raw))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 1, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\x00\xff\x00\x00\x00\xff\x00')) + chunk(b'IEND', b''))


@pytest.fixture
def shaped(tmp_path):
    root = tmp_path/'bundle'; root.mkdir()
    (root/'pitch.md').write_text('# Example proposal\n\n*Draft for discussion*\n\n## Architecture\n\nFirst **important** line\ncontinues with [evidence](https://example.org/evidence).\n\n- First item\n- Second *item*\n\n## Sequence\n\n3. Step three\n4. Step four\n\n## Contracts\n\nContract context.\n')
    headers = ['ID','Interface','Purpose','State','Owner','Producer','Consumer','Inputs','Outputs','Errors','Retry','Consistency','Security']
    values = ['C-1'] + ['value '+h for h in headers[1:]]
    (root/'contracts.md').write_text('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*13)+' |\n| '+' | '.join(values)+' |\n')
    (root/'security-owners.md').write_text('| Responsibility | Owner | How enforced | Boundary | Evidence |\n| --- | --- | --- | --- | --- |\n| Access | Team A | Policy | Service | Review pending |\n')
    mapping = {'schema_version':'ShapingPresentation.v1','diagrams':{}}
    for name, section in zip(export.DIAGRAMS, ['architecture','sequence','contracts']):
        (root/name).write_text('flowchart LR\n A[Input] --> B[Output]\n')
        mapping['diagrams'][name] = {'section_id':'pitch.md#'+section,'caption':name+' caption','alt':name+' alternative'}
    (root/'presentation.json').write_text(json.dumps(mapping))
    return root


def rich(root):
    return export.bundle(root, profile='shaped', presentation='presentation.json')


def assets(root, tmp_path, monkeypatch):
    def renderer(argv, timeout):
        if '--version' in argv:
            return 'test-renderer 1.0'
        target = Path(argv[argv.index('-o')+1])
        target.write_bytes(png() if target.suffix == '.png' else b'<svg xmlns="http://www.w3.org/2000/svg" width="2" height="1" viewBox="0 0 2 1"><text x="0" y="1">A to B</text></svg>')
        return ''
    monkeypatch.setattr(export, 'run_renderer', renderer)
    images = tmp_path/'images'
    export.render(rich(root), root, images, '/trusted/test-renderer')
    return images


def test_framed_profile_needs_only_requested_prose(tmp_path):
    (tmp_path/'pitch.md').write_text('# Problem\n\nA **bounded** problem\nwith *context*.\n\n- First\n- Second\n')
    data = export.bundle(tmp_path, profile='framed')
    assert data['diagrams'] == []
    result = export.html_document(data, self_contained=True)
    assert '<strong>bounded</strong>' in result and '<em>context</em>' in result
    assert '<ul>' in result and result.count('<li>') == 2
    assert '<p>A ' in result and 'problem with' in result
    assert '<script' not in result and 'cdn.' not in result
    assert data['documents'][0]['markdown'] == (tmp_path/'pitch.md').read_text()


def test_compact_tables_keep_every_field_and_stable_links(shaped):
    data = rich(shaped)
    result = export.html_document(data)
    assert '<th>Producer</th>' not in result
    assert 'value Producer' in result and 'value Security' in result
    assert '<dt>Producer</dt>' in result
    assert 'href="#contracts.md--C-1"' in result
    assert 'id="contracts.md--C-1"' in result
    assert '<th>How enforced</th>' in result
    assert '<dt>Evidence</dt>' in result
    assert '<ol start="3">' in result
    assert '<a href="https://example.org/evidence">evidence</a>' in result
    assert result.index('component.mmd caption') < result.index('>Sequence</h2>')
    for doc in data['documents'][1:]:
        table = next(b for b in doc['blocks'] if b['kind']=='table')
        for value in table['rows'][0]:
            assert value in result


def test_long_inline_evidence_tokens_have_narrow_screen_wrapping(shaped):
    token = 'a' * 64
    path = shaped / 'pitch.md'
    path.write_text(path.read_text() + '\nEvidence hash `' + token + '`.\n')
    result = export.html_document(rich(shaped))
    assert '<code>' + token + '</code>' in result
    assert 'code{overflow-wrap:anywhere}' in result


def test_explicit_native_acceptance_table_keeps_its_schema(shaped):
    path = shaped/'contracts.md'
    path.write_text(path.read_text()+'\n## Acceptance\n\n| Check | Given | Expected |\n| --- | --- | --- |\n| A1 known | Value supplied | Exact value retained |\n')
    mapping_path = shaped/'presentation.json'
    mapping = json.loads(mapping_path.read_text())
    mapping['tables'] = {'contracts.md': [None, {'layout':'native'}]}
    mapping_path.write_text(json.dumps(mapping))
    data = rich(shaped)
    tables = [b for b in data['documents'][1]['blocks'] if b['kind']=='table']
    assert 'presentation' in tables[0] and 'presentation' not in tables[1]
    assert tables[1]['rows'] == [['A1 known','Value supplied','Exact value retained']]
    result = export.html_document(data)
    assert '<th>Check</th>' in result and '<th>Expected</th>' in result
    assert 'A1 known' in result and 'Exact value retained' in result


@pytest.mark.parametrize('damage', ['missing-map','bad-anchor','unknown-field','duplicate-row'])
def test_shaped_requires_complete_explicit_mapping(shaped, damage):
    if damage == 'missing-map':
        (shaped/'presentation.json').write_text('{}')
    elif damage == 'bad-anchor':
        path = shaped/'presentation.json'; path.write_text(path.read_text().replace('pitch.md#sequence','pitch.md#missing'))
    else:
        path = shaped/'contracts.md'
        path.write_text(path.read_text().replace('Security','Mystery') if damage=='unknown-field' else path.read_text()+path.read_text().splitlines()[-1]+'\n')
    with pytest.raises(export.ExportError): rich(shaped)


def test_source_bound_svg_png_manifest_and_offline_html(shaped, tmp_path, monkeypatch):
    images = assets(shaped,tmp_path,monkeypatch)
    manifest = json.loads((images/'render-manifest.json').read_text())
    entry = manifest['component.mmd']
    assert entry['svg_dimensions'] == [2,1] and entry['png_dimensions'] == [2,1]
    assert entry['renderer']['version'] == 'test-renderer 1.0'
    assert entry['renderer']['config']['htmlLabels'] is False
    assert entry['section_id'] == 'pitch.md#architecture'
    result = export.html_document(rich(shaped), images=images, self_contained=True)
    assert result.count('data:image/svg+xml;base64,') == 3
    assert '<script' not in result and 'cdn.jsdelivr' not in result
    assert 'component.mmd alternative' in result
    assert 'Full-size figure' in result
    assert base64.b64encode((images/'component.svg').read_bytes()).decode() in result


@pytest.mark.parametrize('damage', ['missing','stale-source','stale-caption','changed-svg','changed-png','wrong-dimensions','traversal','symlink'])
def test_local_assets_fail_closed(shaped,tmp_path,monkeypatch,damage):
    images = assets(shaped,tmp_path,monkeypatch)
    manifest_path = images/'render-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    entry = manifest['component.mmd']
    if damage == 'missing': (images/'component.svg').unlink()
    elif damage == 'stale-source': (shaped/'component.mmd').write_text('flowchart LR\n X-->Y')
    elif damage == 'stale-caption': entry['caption'] = 'wrong caption'
    elif damage == 'changed-svg': (images/'component.svg').write_text('<svg/>')
    elif damage == 'changed-png': (images/'component.png').write_bytes(b'bad')
    elif damage == 'wrong-dimensions': entry['svg_dimensions'] = [999,999]
    elif damage == 'traversal': entry['svg'] = '../component.svg'
    else:
        (images/'component.svg').unlink(); (images/'component.svg').symlink_to(images/'sequence.svg')
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(export.ExportError):
        export.html_document(rich(shaped), images=images, self_contained=True)


@pytest.mark.parametrize('body', ['<script>alert(1)</script>', '<g onclick="x()"/>', '<foreignObject/>', '<image href="https://example.org/a.png"/>', '<use href="file:///tmp/a"/>', '<style>@import "https://example.org/x";</style>', '<style>text{fill:url(https://example.org/x)}</style>', '<animate attributeName="href" values="x"/>'])
def test_unsafe_svg_rejected(body):
    with pytest.raises(export.ExportError):
        export.svg_dimensions(('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1">'+body+'</svg>').encode())


@pytest.mark.parametrize('target', ['javascript:alert','data:text/html,evil','file:///private/a','//example.org/a'])
def test_unsafe_links_never_become_active(tmp_path,target):
    (tmp_path/'pitch.md').write_text('# Frame\n\n[unsafe]('+target+')')
    result = export.html_document(export.bundle(tmp_path,profile='framed'))
    assert 'href="'+target not in result
    assert target in result


def test_self_contained_requires_assets_and_render_failure_has_no_manifest(shaped,tmp_path,monkeypatch):
    with pytest.raises(export.ExportError): export.html_document(rich(shaped),self_contained=True)
    def fail(*args): raise export.ExportError('renderer unavailable')
    monkeypatch.setattr(export,'run_renderer',fail)
    with pytest.raises(export.ExportError,match='unavailable'):
        export.render(rich(shaped),shaped,tmp_path/'failed','missing')
    assert not (tmp_path/'failed/render-manifest.json').exists()


def test_frame_filename_and_explicit_inventory_do_not_require_shaped_files(tmp_path):
    content = '# Framed question\n\nStatus: **uncertain**. No chosen solution.\n'
    (tmp_path/'framed.md').write_text(content)
    assert export.bundle(tmp_path,profile='framed')['documents'][0]['markdown'] == content
    (tmp_path/'other-frame.md').write_text(content)
    data = export.bundle(tmp_path,['other-frame.md'],profile='framed')
    assert data['documents'][0]['id'] == 'other-frame.md' and data['diagrams'] == []
    assert export.main(['html','--profile','framed','--documents','framed.md','--bundle',str(tmp_path),'--output',str(tmp_path/'out.html'),'--self-contained']) == 0
    assert 'Status: <strong>uncertain</strong>' in (tmp_path/'out.html').read_text()


def test_real_header_vocabulary_with_synthetic_values(shaped):
    headers = ['ID','Method / interface','Purpose','Direction; producer → consumer','Inputs / bounds','Output / meaning','Material errors','Timeout / retry / idempotency','Consistency / persistence / lifecycle','Trust / access','State / evidence','Owner / action','Non-responsibility']
    values = ['C-2'] + ['synthetic '+str(n) for n in range(1,len(headers))]
    (shaped/'contracts.md').write_text('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n| '+' | '.join(values)+' |\n')
    data = rich(shaped)
    table = data['documents'][1]['blocks'][0]
    assert table['presentation']['headers'] == ['ID','Interface','Purpose','State','Owner']
    assert table['presentation']['records'][0]['fields'] == list(zip(headers,values))
    security_headers = ['ID','Responsibility','Owner','How enforced / control','Enforcement location','Trust / data boundary','Evidence / state','Explicit negative responsibility and actual owner','Gap / next action']
    security_values = ['SEC-1']+['synthetic security '+str(n) for n in range(1,len(security_headers))]
    (shaped/'security-owners.md').write_text('| '+' | '.join(security_headers)+' |\n| '+' | '.join(['---']*len(security_headers))+' |\n| '+' | '.join(security_values)+' |\n')
    table = rich(shaped)['documents'][2]['blocks'][0]
    assert table['presentation']['records'][0]['fields'] == list(zip(security_headers,security_values))
    assert table['presentation']['records'][0]['id'] == 'security-owners.md--SEC-1'


@pytest.mark.parametrize('damage',[None,'omit','duplicate','unknown','wrong-id'])
def test_explicit_table_map_is_exhaustive(shaped,damage):
    path = shaped/'contracts.md'
    path.write_text('| Key | Seam | Finding | Custodian | Retained note |\n| --- | --- | --- | --- | --- |\n| C-1 | Manual step | Unknown | Unassigned | Keep this exact text |\n')
    mapping = json.loads((shaped/'presentation.json').read_text())
    table_map = {'id_field':'Key','primary':{'ID':['Key'],'Interface':['Seam'],'State':['Finding'],'Owner':['Custodian']},'detail':['Retained note']}
    mapping['tables'] = {'contracts.md':[table_map]}
    if damage == 'omit': table_map['detail'] = []
    elif damage == 'duplicate': table_map['detail'].append('Seam')
    elif damage == 'unknown': table_map['detail'] = ['No such header']
    elif damage == 'wrong-id': table_map['id_field'] = 'No such header'
    (shaped/'presentation.json').write_text(json.dumps(mapping))
    if damage:
        with pytest.raises(export.ExportError): rich(shaped)
    else:
        result = export.html_document(rich(shaped))
        assert '<dt>Retained note</dt><dd>Keep this exact text</dd>' in result
        assert 'id="contracts.md--C-1"' in result


def test_large_text_and_long_rows_remain_reachable(shaped):
    long_text = 'Long supporting evidence with uncertainty. '*150
    path = shaped/'contracts.md'
    path.write_text(path.read_text().replace('value Producer',long_text))
    result = export.html_document(rich(shaped))
    assert long_text.strip() in result
    # Prose/table words retain natural wrapping; only indivisible code tokens
    # (e.g. SHA256 evidence) may break to avoid page-wide mobile overflow.
    cell_css = result.split('th,td{', 1)[1].split('}', 1)[0]
    assert 'overflow-wrap:anywhere' not in cell_css and 'word-break:normal' in cell_css


def test_render_refuses_malicious_svg_even_with_fresh_hash(shaped,tmp_path,monkeypatch):
    images = assets(shaped,tmp_path,monkeypatch)
    raw = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1"><script>bad()</script></svg>'
    (images/'component.svg').write_bytes(raw)
    path = images/'render-manifest.json'; manifest = json.loads(path.read_text())
    manifest['component.mmd']['svg_sha256'] = export.digest(raw); path.write_text(json.dumps(manifest))
    with pytest.raises(export.ExportError,match='SVG'):
        export.html_document(rich(shaped),images,self_contained=True)


@pytest.mark.parametrize('body', [
    '<style><g/>@import url("https://review.invalid/style.css");</style>',
    '<style>rect{mask-image:image-set("//review.invalid/a.png" 1x)}</style>',
    '<style>rect{animation:dash 1s infinite}</style>',
])
def test_reviewer_css_bypasses_are_rejected(body):
    with pytest.raises(export.ExportError):
        export.svg_dimensions(('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10">'+body+'</svg>').encode())


@pytest.mark.parametrize('encoding',['utf-16','utf-16-le','utf-16-be','utf-32'])
def test_encoded_dtd_entity_rejected(encoding):
    xml = '<!DOCTYPE svg [<!ENTITY x "expanded">]><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10"><text>&x;</text></svg>'
    with pytest.raises(export.ExportError): export.svg_dimensions(xml.encode(encoding))


def test_only_unused_known_mermaid_animation_css_is_normalized():
    raw = b'<svg xmlns="http://www.w3.org/2000/svg" id="my-svg" viewBox="0 0 20 10"><style>@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#my-svg .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#my-svg .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}</style><defs><filter id="shadow"><feDropShadow dx="2" dy="2" stdDeviation="0" flood-opacity="0.06" flood-color="#000000"/></filter></defs><text>Static</text></svg>'
    normalized, transforms = export.normalize_renderer_svg(raw)
    assert export.svg_dimensions(normalized) == [20,10]
    assert b'animation' not in normalized and b'feDropShadow' in normalized
    assert transforms and raw != normalized
    for hostile in [raw.replace(b'<text>',b'<text class="edge-animation-slow">'), raw.replace(b'50s',b'2s')]:
        with pytest.raises(export.ExportError): export.normalize_renderer_svg(hostile)


def test_static_init_preserved_but_security_overrides_refused():
    directive = '%%{init: {"theme":"base","themeVariables":{"actorBkg":"#326ce5"},"themeCSS":"rect.actor[name=\\"A\\"]{fill:#ffffff!important;}"}}%%\nsequenceDiagram\n A->>B: hello\n'
    settings = export.validate_mermaid(directive)
    assert settings['theme'] == 'base' and 'themeCSS' in settings
    assert export.svg_dimensions(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10"><style>text.actor&gt;tspan{fill:black;stroke:none;}</style></svg>') == [20,10]
    assert export.svg_dimensions(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10"><defs><symbol id="arrow"><path d="M0 0 L2 1"/></symbol></defs><use href="#arrow"/></svg>') == [20,10]
    for value in ['{"securityLevel":"loose"}', '{"themeCSS":"rect{mask:image-set(\\"//review.invalid/a\\" 1x)}"}', '{"themeVariables":{"fontFamily":"url(https://review.invalid/font)"}}', '{"flowchart":{"htmlLabels":true}}']:
        with pytest.raises(export.ExportError): export.validate_mermaid('%%{init: '+value+'}%%\nflowchart LR\n A-->B')


def test_fragments_and_suffix_collisions(tmp_path):
    (tmp_path/'framed.md').write_text('# Bounds\n\n[See bounds](#bounds)\n\n## Bounds\n\n## Bounds-2\n')
    data = export.bundle(tmp_path,profile='framed')
    ids = [b['id'] for b in data['documents'][0]['blocks'] if b['kind']=='heading']
    assert len(ids) == len(set(ids)) == 3
    result = export.html_document(data,self_contained=True)
    assert 'href="#framed.md#bounds"' in result
    (tmp_path/'framed.md').write_text('# Frame\n\n[Missing](#absent)\n')
    with pytest.raises(export.ExportError,match='fragment'):
        export.html_document(export.bundle(tmp_path,profile='framed'))


@pytest.mark.skipif(not os.environ.get('ENGOS_TEST_MMDC'),reason='opt-in cached local Mermaid integration')
def test_real_cached_mermaid_static_render(shaped,tmp_path):
    (shaped/'sequence.mmd').write_text('%%{init: {"theme":"base","themeVariables":{"actorBkg":"#326ce5"},"themeCSS":"rect.actor{stroke:#183b56;}"}}%%\nsequenceDiagram\n A->>B: Synthetic request\n')
    images = tmp_path/'real-images'
    data = rich(shaped)
    receipts = export.render(data,shaped,images,os.environ['ENGOS_TEST_MMDC'],node=os.environ['ENGOS_TEST_NODE'],puppeteer_config=Path(os.environ['ENGOS_TEST_PUPPETEER']))
    assert len(receipts) == 3
    assert all(e['svg_original_sha256'] and e['svg_normalization'] for e in receipts.values())
    export.verify_assets(data,images,require_svg=True)
    assert '<script' not in export.html_document(data,images,self_contained=True)


def test_quotes_and_exported_document_links(shaped):
    path = shaped/'pitch.md'
    raw = path.read_text()+'\n> Quoted **uncertainty**\n> continues here.\n\n[Contracts](contracts.md) [Research](research.md#bounds) [External source](../research/raw.md)\n'
    path.write_text(raw)
    (shaped/'research.md').write_text('# Research\n\n## Bounds\n\nUnknown.\n')
    data = export.bundle(shaped,[*export.DOCUMENTS,'research.md'],profile='shaped',presentation='presentation.json')
    result = export.html_document(data)
    assert '<blockquote><p>Quoted <strong>uncertainty</strong> continues here.</p></blockquote>' in result
    assert 'href="#contracts.md"' in result
    assert 'href="#research.md#bounds"' in result
    assert 'External source (../research/raw.md)' in result
    assert '[External source]' not in result and 'href="../' not in result
    assert data['documents'][0]['markdown'] == raw


def test_figure_metadata_bound_and_single_expandable_image(shaped,tmp_path,monkeypatch):
    path = shaped/'presentation.json'; mapping = json.loads(path.read_text())
    mapping['diagrams']['component.mmd'].update(title='A supplied figure title',legend='Dashed: proposed. Solid: supplied existing behavior.')
    path.write_text(json.dumps(mapping))
    images = assets(shaped,tmp_path,monkeypatch)
    data = rich(shaped); result = export.html_document(data,images,self_contained=True)
    assert result.count('data:image/svg+xml;base64,') == 3
    assert 'A supplied figure title' in result and 'Dashed: proposed.' in result
    assert '<details class="full-size"' not in result
    assert 'type="checkbox"' in result and ':checked' in result
    manifest = json.loads((images/'render-manifest.json').read_text())
    assert manifest['component.mmd']['title'] == 'A supplied figure title'
    assert manifest['component.mmd']['legend'].startswith('Dashed:')
    assert manifest['component.mmd']['presentation_sha256'] == export.diagram_metadata_hash(data['diagrams'][0])
    for field in ('title','legend'):
        altered = json.loads(json.dumps(data)); altered['diagrams'][0][field] = 'Changed metadata'
        with pytest.raises(export.ExportError): export.html_document(altered,images,self_contained=True)


def test_explicit_source_link_to_generated_detail_id(shaped):
    path = shaped/'pitch.md'; path.write_text(path.read_text()+'\n[Contract C-1](#contracts.md--C-1)\n')
    result = export.html_document(rich(shaped))
    assert '<a href="#contracts.md--C-1">Contract C-1</a>' in result
    assert 'id="contracts.md--C-1"' in result
