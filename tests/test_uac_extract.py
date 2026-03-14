from __future__ import annotations

from intent_pipeline.uac_extract import extract_uac_analysis_text


def test_extract_uac_analysis_text_from_toml_prompt() -> None:
    text = 'prompt = """Primary Objective: Design an API.\n\nIn Scope:\n- Endpoints\n"""\n'

    extraction = extract_uac_analysis_text(text, 'design-api.toml')

    assert extraction.wrapper_kind == 'toml_prompt'
    assert extraction.prompt_field == 'prompt'
    assert 'Primary Objective' in extraction.analysis_text


def test_extract_uac_analysis_text_from_markdown_frontmatter() -> None:
    text = '---\nname: sample\n---\n\n# Prompt\n\nPrimary Objective: Test\n'

    extraction = extract_uac_analysis_text(text, 'sample.md')

    assert extraction.wrapper_kind == 'frontmatter_markdown'
    assert extraction.prompt_field is None
    assert '# Prompt' in extraction.analysis_text
