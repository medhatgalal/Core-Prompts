"""Human-view contracts; all underlying semantic receipts are explicit fixtures."""
from test_shaping_runtime import runtime, workshop, advance, prepare, version


def blocked(rt):
    rt.progress_context({'name':'Example <script>never run</script>', 'evidence_mode':'simulated',
        'requested_stop':'G4', 'observed_at':rt.utc_now() if hasattr(rt,'utc_now') else '2026-01-01T00:00:00Z',
        'evidence':'sources/original.txt','investment_appetite':'Fixture only'},version(rt))
    advance(rt,1)
    order,_=prepare(rt,'G2')
    rt.observe({'event_id':'waiting','run_id':order['run_id'],'version':version(rt),
        'generation':0,'work_order_id':order['work_order_id'],'kind':'held',
        'observed_at':'2026-01-01T00:00:00Z','actor':'fixture-controller','evidence':'sources/context.txt',
        'hold_type':'prerequisite','reason':'Caller lifecycle unknown','needed':'Existing source extract',
        'respondent':None,'next_action':'Identify the evidence owner'},version(rt))
    return rt.progress('2026-09-18T12:00:00Z')


def test_html_leads_with_action_and_gates_not_raw_hashes(workshop,runtime):
    p=blocked(workshop)
    result=runtime.render_progress(p,'html')
    assert 'id="flow-summary"' in result
    assert result.index('What happens next') < result.index('Revision and evidence details')
    assert result.index('Gate states') < result.index('Revision and evidence details')
    assert 'Needed respondent' in result and 'unassigned' in result
    assert 'Research' in result and 'Simulation' in result
    assert '<script>never run</script>' not in result
    assert 'Example &lt;script&gt;never run&lt;/script&gt;' in result
    assert p['revision'] in result  # Retained in secondary detail, not discarded.


def test_markdown_leads_with_action_and_preserves_projection(workshop,runtime):
    p=blocked(workshop)
    result=runtime.render_progress(p,'markdown')
    assert result.index('Next action') < result.index('Revision and evidence details')
    assert 'Gate states' in result and 'Research' in result
    assert 'Needed respondent' in result and 'unassigned' in result
    assert 'counts are not effort' in result
    assert p['revision'] in result


def test_unverifiable_view_never_announces_finish(tmp_path,runtime):
    p=runtime.Runtime(tmp_path/'missing').progress()
    for fmt in ('html','markdown'):
        result=runtime.render_progress(p,fmt)
        assert 'unverifiable' in result
        assert 'Requested scope complete' not in result


def test_requested_finish_names_the_actual_scope(workshop,runtime):
    rt=workshop
    rt.progress_context({'name':'Frame example','evidence_mode':'simulated','requested_stop':'G1',
        'observed_at':'2026-01-01T00:00:00Z','evidence':'sources/original.txt',
        'investment_appetite':'Fixture only'},version(rt))
    advance(rt,1)
    p=rt.progress()
    for fmt in ('html','markdown'):
        result=runtime.render_progress(p,fmt)
        primary=result.split('Revision and evidence details')[0]
        assert 'Framed — verified' in primary
        assert 'Requested result' in primary
        assert 'not_reached' not in primary and 'outside_scope' not in primary


def test_target_summary_distinguishes_saved_and_observed_revision(workshop,runtime):
    p=blocked(workshop)
    p['targets'][0].update(placement='verified',target_revision='saved-1',
        observed_target_revision='changed-2',remote_freshness='changed')
    result=runtime.render_progress(p,'html').split('Revision and evidence details')[0]
    assert 'Recorded placement' in result and 'observed revision changed-2' in result
