#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from intent_pipeline.uac_ssot import build_ssot_manifest_entry, load_ssot_entries

SSOT_DIR = ROOT / 'ssot'
META_DIR = ROOT / '.meta'
MANIFEST_PATH = META_DIR / 'manifest.json'

GEMINI_COMMAND_DIR = ROOT / '.gemini' / 'commands'
GEMINI_SKILL_DIR = ROOT / '.gemini' / 'skills'
GEMINI_AGENT_DIR = ROOT / '.gemini' / 'agents'
CLAUDE_COMMAND_DIR = ROOT / '.claude' / 'commands'
CLAUDE_AGENT_DIR = ROOT / '.claude' / 'agents'
KIRO_PROMPT_DIR = ROOT / '.kiro' / 'prompts'
KIRO_AGENT_DIR = ROOT / '.kiro' / 'agents'
KIRO_SKILL_DIR = ROOT / '.kiro' / 'skills'
CODEX_SKILL_DIR = ROOT / '.codex' / 'skills'
CODEX_AGENT_DIR = ROOT / '.codex' / 'agents'

for d in [
    GEMINI_COMMAND_DIR,
    GEMINI_SKILL_DIR,
    GEMINI_AGENT_DIR,
    CLAUDE_COMMAND_DIR,
    CLAUDE_AGENT_DIR,
    KIRO_PROMPT_DIR,
    KIRO_AGENT_DIR,
    KIRO_SKILL_DIR,
    CODEX_SKILL_DIR,
    CODEX_AGENT_DIR,
    META_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)


SURFACE_PATHS = {
    'gemini_command': lambda slug: GEMINI_COMMAND_DIR / f'{slug}.toml',
    'gemini_skill': lambda slug: GEMINI_SKILL_DIR / slug / 'SKILL.md',
    'gemini_agent': lambda slug: GEMINI_AGENT_DIR / f'{slug}.md',
    'claude_command': lambda slug: CLAUDE_COMMAND_DIR / f'{slug}.md',
    'claude_agent': lambda slug: CLAUDE_AGENT_DIR / f'{slug}.md',
    'kiro_prompt': lambda slug: KIRO_PROMPT_DIR / f'{slug}.md',
    'kiro_agent': lambda slug: KIRO_AGENT_DIR / f'{slug}.json',
    'kiro_skill': lambda slug: KIRO_SKILL_DIR / slug / 'SKILL.md',
    'codex_skill': lambda slug: CODEX_SKILL_DIR / slug / 'SKILL.md',
    'codex_agent': lambda slug: CODEX_AGENT_DIR / f'{slug}.toml',
}


def to_toml_str(name: str, desc: str, prompt: str) -> str:
    esc_desc = desc.replace('\\', '\\\\').replace('"', '\\"')
    prompt_escaped = prompt.replace('\\', '\\\\').replace('"', '\\"')
    return (
        f'name = "{name}"\n'
        f'description = "{esc_desc}"\n'
        f'prompt = """\n{prompt_escaped}\n"""\n'
    )


def toml_escape_inline(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"')


def to_toml_array(values: list[str]) -> str:
    escaped = [f'"{toml_escape_inline(v)}"' for v in values]
    return '[' + ', '.join(escaped) + ']'


def title_from_slug(slug: str) -> str:
    return ' '.join(part.capitalize() for part in slug.replace('_', '-').split('-'))


def write_skill(base_dir: Path, slug: str, desc: str, body: str):
    path = base_dir / slug / 'SKILL.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = (
        '---\n'
        f'name: "{slug}"\n'
        f'description: "{desc}"\n'
        '---\n'
        f'{body}\n'
    )
    path.write_text(txt, encoding='utf-8')
    return str(path.relative_to(ROOT))


def write_kiro_prompt(slug: str, desc: str, body: str):
    path = KIRO_PROMPT_DIR / f'{slug}.md'
    txt = (
        '---\n'
        f'description: "{desc}"\n'
        '---\n\n'
        f'# {title_from_slug(slug)} (Prompt Mode)\n\n'
        f'{body}\n'
    )
    path.write_text(txt, encoding='utf-8')
    return str(path.relative_to(ROOT))


def write_kiro_agent(slug: str, desc: str, body: str):
    path = KIRO_AGENT_DIR / f'{slug}.json'
    prompt_title = f'{title_from_slug(slug)} (Prompt Mode)'
    obj = {
        'name': slug,
        'description': desc,
        'prompt': f'# {prompt_title}\n\n{body}\n',
        'resources': [
            f'file://.kiro/prompts/{slug}.md',
            f'skill://.kiro/skills/{slug}/SKILL.md',
        ],
        'hooks': {
            'agentSpawn': [
                {
                    'command': 'if [ -x ./scripts/engos ]; then ./scripts/engos prime >/dev/null 2>&1 || true; elif [ -x ./engos ]; then ./engos context prime >/dev/null 2>&1 || true; fi'
                }
            ]
        },
        'tools': ['*'],
    }
    path.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
    return str(path.relative_to(ROOT))


def write_codex_skill(slug: str, desc: str, body: str):
    return write_skill(CODEX_SKILL_DIR, slug, desc, body)


def write_codex_agent(slug: str, desc: str, body: str, tools: list[str]):
    path = CODEX_AGENT_DIR / f'{slug}.toml'
    esc_desc = toml_escape_inline(desc)
    instructions = body.replace('\\', '\\\\').replace('"', '\\"')
    txt = (
        f'name = "{slug}"\n'
        f'description = "{esc_desc}"\n'
        f'developer_instructions = """\n{instructions}\n"""\n'
    )
    if tools:
        txt += f'tools = {to_toml_array(tools)}\n'
    path.write_text(txt, encoding='utf-8')
    return str(path.relative_to(ROOT))


def write_gemini_command(slug: str, desc: str, body: str):
    path = GEMINI_COMMAND_DIR / f'{slug}.toml'
    path.write_text(to_toml_str(slug, desc, body), encoding='utf-8')
    return str(path.relative_to(ROOT))


def write_gemini_skill(slug: str, desc: str, body: str):
    return write_skill(GEMINI_SKILL_DIR, slug, desc, body)


def write_gemini_agent(slug: str, desc: str, body: str):
    path = GEMINI_AGENT_DIR / f'{slug}.md'
    txt = (
        '---\n'
        f'name: "{slug}"\n'
        'kind: local\n'
        f'description: "{desc}"\n'
        'max_turns: 15\n'
        'timeout_mins: 5\n'
        '---\n\n'
        f'{body}\n'
    )
    path.write_text(txt, encoding='utf-8')
    return str(path.relative_to(ROOT))


def write_claude_command(slug: str, desc: str, body: str):
    path = CLAUDE_COMMAND_DIR / f'{slug}.md'
    txt = (
        '---\n'
        f'description: "{desc}"\n'
        '---\n\n'
        f'{body}\n'
    )
    path.write_text(txt, encoding='utf-8')
    return str(path.relative_to(ROOT))


def write_claude_agent(slug: str, desc: str, body: str):
    path = CLAUDE_AGENT_DIR / f'{slug}.md'
    txt = (
        '---\n'
        f'name: {slug}\n'
        f'description: "{desc}"\n'
        'tools: Read, Write, Edit, Bash, Grep, Glob\n'
        '---\n\n'
        f'{body}\n'
    )
    path.write_text(txt, encoding='utf-8')
    return str(path.relative_to(ROOT))


def write_kiro_skill(slug: str, desc: str, body: str):
    return write_skill(KIRO_SKILL_DIR, slug, desc, body)


def cleanup_slug_outputs(slug: str) -> None:
    for surface_name, path_fn in SURFACE_PATHS.items():
        path = path_fn(slug)
        if path.name == 'SKILL.md':
            if path.parent.exists() and path.parent.is_dir():
                shutil.rmtree(path.parent)
        elif path.exists():
            path.unlink()


def parse_tools(frontmatter: dict[str, str]) -> list[str]:
    raw = (frontmatter.get('agent_tools') or frontmatter.get('tools') or '').strip()
    if not raw:
        return []
    normalized = raw.strip('[]')
    tools = [part.strip().strip('"').strip("'") for part in normalized.split(',') if part.strip()]
    return tools or ['*']


def main():
    entries = load_ssot_entries(SSOT_DIR)
    if not entries:
        raise SystemExit('No SSOT files found in ssot/')

    generated = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'generator': {
            'script': 'scripts/build-surfaces.py',
            'python': '3.11+',
            'version': '5.0',
            'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        'ssot_sources': [],
        'surfaces': {name: [] for name in SURFACE_PATHS},
    }

    for entry in entries:
        cleanup_slug_outputs(entry.slug)
        manifest_entry = build_ssot_manifest_entry(entry)
        generated['ssot_sources'].append(manifest_entry)
        emitted = set(manifest_entry['expected_surface_names'])
        tools = parse_tools(entry.frontmatter)

        if 'gemini_command' in emitted:
            generated['surfaces']['gemini_command'].append(write_gemini_command(entry.slug, entry.description, entry.body))
        if 'gemini_skill' in emitted:
            generated['surfaces']['gemini_skill'].append(write_gemini_skill(entry.slug, entry.description, entry.body))
        if 'gemini_agent' in emitted:
            generated['surfaces']['gemini_agent'].append(write_gemini_agent(entry.slug, entry.description, entry.body))
        if 'claude_command' in emitted:
            generated['surfaces']['claude_command'].append(write_claude_command(entry.slug, entry.description, entry.body))
        if 'claude_agent' in emitted:
            generated['surfaces']['claude_agent'].append(write_claude_agent(entry.slug, entry.description, entry.body))
        if 'kiro_prompt' in emitted:
            generated['surfaces']['kiro_prompt'].append(write_kiro_prompt(entry.slug, entry.description, entry.body))
        if 'kiro_agent' in emitted:
            generated['surfaces']['kiro_agent'].append(write_kiro_agent(entry.slug, entry.description, entry.body))
        if 'kiro_skill' in emitted:
            generated['surfaces']['kiro_skill'].append(write_kiro_skill(entry.slug, entry.description, entry.body))
        if 'codex_skill' in emitted:
            generated['surfaces']['codex_skill'].append(write_codex_skill(entry.slug, entry.description, entry.body))
        if 'codex_agent' in emitted:
            generated['surfaces']['codex_agent'].append(write_codex_agent(entry.slug, entry.description, entry.body, tools))

    MANIFEST_PATH.write_text(json.dumps(generated, indent=2) + '\n', encoding='utf-8')
    print('Generated', len(entries), 'ssot entries')


if __name__ == '__main__':
    main()
