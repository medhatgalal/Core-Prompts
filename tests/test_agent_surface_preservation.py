"""Explicit catalogue retirement cannot hide instruction or unrelated edits."""
from pathlib import Path
import subprocess
import pytest
from intent_pipeline.uac_agent_review import declaration_normalization

SLUG = 'engos-meta-supercharge'
ORIGINAL = f'---\nname: "{SLUG}"\ncapability_type: "both"\n---\n# Workflow\nPreserve independent review and user authority.\n'

@pytest.fixture
def committed(tmp_path):
    path=tmp_path/'ssot'/f'{SLUG}.md'
    path.parent.mkdir(); path.write_text(ORIGINAL)
    subprocess.run(['git','init','-q',str(tmp_path)],check=True)
    subprocess.run(['git','add','ssot'],cwd=tmp_path,check=True)
    subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','Existing canonical source'],cwd=tmp_path,check=True)
    return tmp_path,path

def test_catalogued_retirement_preserves_skill_without_new_quality_claim(committed):
    root,path=committed
    candidate=ORIGINAL.replace('"both"','"skill"')
    result=declaration_normalization(root,slug=SLUG,candidate_text=candidate)
    assert result['status']=='user_directed_agent_retirement'
    assert len(result['removed_surfaces'])==4
    assert len(result['retained_surfaces'])==5
    assert result['behavioral_status']=='not_retested'
    assert result['quality_evidence']=='skill_body_unchanged_not_rejudged'

@pytest.mark.parametrize('change',['body','extra_field','trailing_space','uncommitted_source','not_retired'])
def test_retirement_preservation_rejects_other_changes(committed,change):
    root,path=committed
    slug=SLUG
    candidate=ORIGINAL.replace('"both"','"skill"')
    if change=='body': candidate=candidate.replace('Preserve','Ignore')
    elif change=='extra_field': candidate=candidate.replace('# Workflow','model: other\n# Workflow')
    elif change=='trailing_space': candidate+=' '
    elif change=='uncommitted_source':
        path.write_text(ORIGINAL+'Unreviewed change.\n')
        candidate=path.read_text().replace('"both"','"skill"')
    else:
        slug='fixture'
        target=path.with_name('fixture.md')
        target.write_text(ORIGINAL.replace(SLUG,slug))
        candidate=target.read_text().replace('"both"','"skill"')
        subprocess.run(['git','add','ssot'],cwd=root,check=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','Non-retired source'],cwd=root,check=True)
    assert declaration_normalization(root,slug=slug,candidate_text=candidate) is None
