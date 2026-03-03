#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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
    META_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)

for old in [ROOT / 'clis', ROOT / '.kiro', ROOT / '.gemini', ROOT / '.claude', ROOT / '.codex']:
    if old.exists() and old == ROOT / 'clis':
        # legacy source kept untouched
        pass


def read_md_metadata_and_body(path: Path):
    text = path.read_text(encoding='utf-8')
    front = {}
    # parse all YAML-like blocks at file head
    blocks = []
    remainder = text
    while remainder.startswith('---\n'):
        end = remainder.find('\n---', 3)
        if end == -1:
            break
        block = remainder[4:end]
        blocks.append(block)
        remainder = remainder[end + 4 :]
        if remainder.startswith('\n'):
            remainder = remainder[1:]

    for block in blocks:
        for line in block.splitlines():
            line = line.strip()
            if not line or ':' not in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in ('name', 'description') and key not in front:
                front[key] = value

    body = remainder.strip('\n')
    return front, body


def to_toml_str(name: str, desc: str, prompt: str) -> str:
    esc_desc = desc.replace('\\', '\\\\').replace('"', '\\"')
    prompt_escaped = prompt.replace('\\', '\\\\').replace('"', '\\"')
    return (
        f'name = "{name}"\n'
        f'description = "{esc_desc}"\n'
        f'prompt = """\n{prompt_escaped}\n"""\n'
    )


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


def main():
    entries = sorted(SSOT_DIR.glob('*.md'))
    if not entries:
        raise SystemExit('No SSOT files found in ssot/')

    generated = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'generator': {
            'script': 'scripts/build-surfaces.py',
            'python': '3.11+',
            'version': '4.0',
            'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        'ssot_sources': [],
        'surfaces': {
            'gemini_command': [],
            'gemini_skill': [],
            'gemini_agent': [],
            'claude_command': [],
            'claude_agent': [],
            'kiro_prompt': [],
            'kiro_agent': [],
            'kiro_skill': [],
            'codex_skill': [],
        },
    }

    for entry in entries:
        front, body = read_md_metadata_and_body(entry)
        slug = front.get('name') or entry.stem
        desc = front.get('description', f'Surface prompt for {slug}')
        generated['ssot_sources'].append({
            'file': f'ssot/{entry.name}',
            'slug': slug,
            'name': front.get('name', slug),
            'description': desc,
        })
        generated['surfaces']['gemini_command'].append(write_gemini_command(slug, desc, body))
        generated['surfaces']['gemini_skill'].append(write_gemini_skill(slug, desc, body))
        generated['surfaces']['gemini_agent'].append(write_gemini_agent(slug, desc, body))
        generated['surfaces']['claude_command'].append(write_claude_command(slug, desc, body))
        generated['surfaces']['claude_agent'].append(write_claude_agent(slug, desc, body))
        generated['surfaces']['kiro_prompt'].append(write_kiro_prompt(slug, desc, body))
        generated['surfaces']['kiro_agent'].append(write_kiro_agent(slug, desc, body))
        generated['surfaces']['kiro_skill'].append(write_kiro_skill(slug, desc, body))
        generated['surfaces']['codex_skill'].append(write_codex_skill(slug, desc, body))

    MANIFEST_PATH.write_text(json.dumps(generated, indent=2) + '\n', encoding='utf-8')
    print('Generated', len(entries), 'ssot entries')


if __name__ == '__main__':
    main()
