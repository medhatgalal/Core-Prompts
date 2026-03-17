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

from intent_pipeline.uac_descriptors import build_descriptor, load_descriptor, save_descriptor, source_note_path
from intent_pipeline.uac_ssot import build_ssot_handoff_contract, build_ssot_manifest_entry, load_ssot_entries

SSOT_DIR = ROOT / 'ssot'
META_DIR = ROOT / '.meta'
MANIFEST_PATH = META_DIR / 'manifest.json'
HANDOFF_PATH = META_DIR / 'capability-handoff.json'
CAPABILITY_DIR = META_DIR / 'capabilities'

GEMINI_COMMAND_DIR = ROOT / '.gemini' / 'commands'
GEMINI_SKILL_DIR = ROOT / '.gemini' / 'skills'
GEMINI_AGENT_DIR = ROOT / '.gemini' / 'agents'
CLAUDE_COMMAND_DIR = ROOT / '.claude' / 'commands'
CLAUDE_AGENT_DIR = ROOT / '.claude' / 'agents'
CLAUDE_RESOURCE_DIR = CLAUDE_AGENT_DIR / 'resources'
KIRO_PROMPT_DIR = ROOT / '.kiro' / 'prompts'
KIRO_AGENT_DIR = ROOT / '.kiro' / 'agents'
KIRO_AGENT_RESOURCE_DIR = KIRO_AGENT_DIR / 'resources'
KIRO_SKILL_DIR = ROOT / '.kiro' / 'skills'
CODEX_SKILL_DIR = ROOT / '.codex' / 'skills'
CODEX_AGENT_DIR = ROOT / '.codex' / 'agents'
CODEX_AGENT_RESOURCE_DIR = CODEX_AGENT_DIR / 'resources'

for d in [
    GEMINI_COMMAND_DIR,
    GEMINI_SKILL_DIR,
    GEMINI_AGENT_DIR,
    CLAUDE_COMMAND_DIR,
    CLAUDE_AGENT_DIR,
    CLAUDE_RESOURCE_DIR,
    KIRO_PROMPT_DIR,
    KIRO_AGENT_DIR,
    KIRO_AGENT_RESOURCE_DIR,
    KIRO_SKILL_DIR,
    CODEX_SKILL_DIR,
    CODEX_AGENT_DIR,
    CODEX_AGENT_RESOURCE_DIR,
    META_DIR,
    CAPABILITY_DIR,
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


RESOURCE_PATHS = {
    'codex_skill': lambda slug: CODEX_SKILL_DIR / slug / 'resources' / 'capability.json',
    'codex_agent': lambda slug: CODEX_AGENT_RESOURCE_DIR / slug / 'capability.json',
    'gemini_skill': lambda slug: GEMINI_SKILL_DIR / slug / 'resources' / 'capability.json',
    'gemini_agent': lambda slug: GEMINI_AGENT_DIR / 'resources' / slug / 'capability.json',
    'claude_agent': lambda slug: CLAUDE_RESOURCE_DIR / slug / 'capability.json',
    'kiro_skill': lambda slug: KIRO_SKILL_DIR / slug / 'resources' / 'capability.json',
    'kiro_agent': lambda slug: KIRO_AGENT_RESOURCE_DIR / slug / 'capability.json',
}


def descriptor_defaults(slug: str, display_name: str) -> dict[str, object]:
    defaults: dict[str, dict[str, object]] = {
        'architecture': {
            'display_name': 'Architecture Studio',
            'consumption_hints': {
                'preferred_use_cases': [
                    'API design',
                    'database design',
                    'design-pattern selection',
                    'system design',
                    'migration-safe architecture review',
                ],
                'artifact_conventions': [
                    'reports/architecture/<timestamp>-summary.md',
                    'reports/architecture/<timestamp>-decision-log.md',
                    'architecture/spec.md',
                    'architecture/decision-log.md',
                    'architecture/migration-plan.md',
                    'architecture/validation-plan.md',
                ],
                'invocation_style': 'interactive_or_artifact_oriented',
                'requires_human_confirmation': False,
            },
            'layer_overrides': {
                'expanded': {
                    'quality_criteria': [
                        'Score against the published architecture scorecard on every significant design branch',
                        'Include rejected alternatives and explicit trade-offs for major design decisions',
                        'Keep migration, rollback, and validation concrete enough to execute',
                        'Meet or exceed the Harish/Alexanderdunlop source bar and the local code-review/resolve-conflict bar',
                    ],
                    'quality_gate': {
                        'min_pass_score': 9,
                        'required_no_zero_for': [
                            'Failure-Aware Decisions',
                            'Migration Clarity',
                            'Benchmark Fit',
                        ],
                    },
                },
            },
        },
        'code-review': {
            'display_name': 'Commit Review — Git Commit Quality Gate',
            'consumption_hints': {
                'preferred_use_cases': [
                    'pre-merge commit review',
                    'scope creep detection',
                    'over-engineering checks',
                ],
                'artifact_conventions': [
                    'reports/code-reviews/<timestamp>-<commit>.md',
                ],
                'invocation_style': 'git_commit_review',
                'requires_human_confirmation': False,
            },
        },
        'resolve-conflict': {
            'display_name': 'Merge Conflict Resolution — Structured Conflict Analysis',
            'consumption_hints': {
                'preferred_use_cases': [
                    'merge conflict analysis',
                    'additive conflict resolution planning',
                    'contradiction detection before merge',
                ],
                'artifact_conventions': [
                    'reports/merge-conflicts/<descriptive-name>.md',
                ],
                'invocation_style': 'conflict_analysis',
                'requires_human_confirmation': True,
            },
        },
        'testing': {
            'display_name': 'Testing Studio — Test Design and Coverage Analysis',
            'consumption_hints': {
                'preferred_use_cases': [
                    'unit test design',
                    'end-to-end test design',
                    'edge-case discovery',
                    'coverage gap analysis',
                ],
                'artifact_conventions': [
                    'reports/testing/<timestamp>-plan.md',
                    'reports/testing/<timestamp>-coverage-gap.md',
                    'reports/testing/<timestamp>-edge-cases.md',
                ],
                'invocation_style': 'analysis_or_generation',
                'requires_human_confirmation': False,
            },
        },
        'uac-import': {
            'display_name': 'UAC Import — Capability Intake, Quality Review, and Uplift',
            'consumption_hints': {
                'preferred_use_cases': [
                    'external prompt import',
                    'multi-source capability convergence',
                    'descriptor and handoff generation',
                ],
                'artifact_conventions': [
                    'ssot/<slug>.md',
                    '.meta/capabilities/<slug>.json',
                    'reports/quality-reviews/<slug>/LATEST.md',
                ],
                'invocation_style': 'assistant_first_but_scriptable',
                'requires_human_confirmation': True,
            },
        },
    }
    payload = defaults.get(slug, {})
    if not payload:
        return {'display_name': display_name}
    return payload


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


def write_skill(base_dir: Path, slug: str, desc: str, body: str, resource_hint: str | None = None):
    path = base_dir / slug / 'SKILL.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    resource_block = f'\n\nCapability resource: `{resource_hint}`\n' if resource_hint else '\n'
    txt = (
        '---\n'
        f'name: "{slug}"\n'
        f'description: "{desc}"\n'
        '---\n'
        f'{body.rstrip()}\n{resource_block}'
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


def write_kiro_agent(slug: str, desc: str, body: str, resource_uri: str, include_skill_ref: bool):
    path = KIRO_AGENT_DIR / f'{slug}.json'
    prompt_title = f'{title_from_slug(slug)} (Prompt Mode)'
    resources = [
        f'file://.kiro/prompts/{slug}.md',
        resource_uri,
    ]
    if include_skill_ref:
        resources.append(f'skill://.kiro/skills/{slug}/SKILL.md')
    obj = {
        'name': slug,
        'description': desc,
        'prompt': f'# {prompt_title}\n\n{body}\n\nCapability resource: `{resource_uri}`\n',
        'resources': resources,
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


def write_codex_skill(slug: str, desc: str, body: str, resource_hint: str | None = None):
    return write_skill(CODEX_SKILL_DIR, slug, desc, body, resource_hint=resource_hint)


def write_codex_agent(slug: str, desc: str, body: str, tools: list[str], resource_hint: str | None = None):
    path = CODEX_AGENT_DIR / f'{slug}.toml'
    esc_desc = toml_escape_inline(desc)
    augmented = body.rstrip()
    if resource_hint:
        augmented += f'\n\nCapability resource: `{resource_hint}`\n'
    instructions = augmented.replace('\\', '\\\\').replace('"', '\\"')
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


def write_gemini_skill(slug: str, desc: str, body: str, resource_hint: str | None = None):
    return write_skill(GEMINI_SKILL_DIR, slug, desc, body, resource_hint=resource_hint)


def write_gemini_agent(slug: str, desc: str, body: str, resource_hint: str | None = None):
    path = GEMINI_AGENT_DIR / f'{slug}.md'
    resource_block = f'\n\nCapability resource: `{resource_hint}`\n' if resource_hint else '\n'
    txt = (
        '---\n'
        f'name: "{slug}"\n'
        'kind: local\n'
        f'description: "{desc}"\n'
        'max_turns: 15\n'
        'timeout_mins: 5\n'
        '---\n\n'
        f'{body.rstrip()}\n{resource_block}'
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


def write_claude_agent(slug: str, desc: str, body: str, resource_hint: str | None = None):
    path = CLAUDE_AGENT_DIR / f'{slug}.md'
    resource_block = f'\n\nCapability resource: `{resource_hint}`\n' if resource_hint else '\n'
    txt = (
        '---\n'
        f'name: {slug}\n'
        f'description: "{desc}"\n'
        'tools: Read, Write, Edit, Bash, Grep, Glob\n'
        '---\n\n'
        f'{body.rstrip()}\n{resource_block}'
    )
    path.write_text(txt, encoding='utf-8')
    return str(path.relative_to(ROOT))


def write_kiro_skill(slug: str, desc: str, body: str, resource_hint: str | None = None):
    return write_skill(KIRO_SKILL_DIR, slug, desc, body, resource_hint=resource_hint)


def cleanup_slug_outputs(slug: str) -> None:
    for path_fn in SURFACE_PATHS.values():
        path = path_fn(slug)
        if path.name == 'SKILL.md':
            if path.parent.exists() and path.parent.is_dir():
                shutil.rmtree(path.parent)
        elif path.exists():
            path.unlink()
    for path_fn in RESOURCE_PATHS.values():
        path = path_fn(slug)
        if path.exists():
            path.unlink()
        parent = path.parent
        while parent != ROOT and parent.exists() and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent


def parse_tools(frontmatter: dict[str, str]) -> list[str]:
    raw = (frontmatter.get('agent_tools') or frontmatter.get('tools') or '').strip()
    if not raw:
        return []
    normalized = raw.strip('[]')
    tools = [part.strip().strip('"').strip("'") for part in normalized.split(',') if part.strip()]
    return tools or ['*']


def write_resource(surface_name: str, slug: str, descriptor: dict[str, object]) -> str:
    path = RESOURCE_PATHS[surface_name](slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(descriptor, indent=2) + '\n', encoding='utf-8')
    return str(path.relative_to(ROOT))


def resolve_descriptor(entry, manifest_entry: dict[str, object]) -> dict[str, object]:
    defaults = descriptor_defaults(entry.slug, entry.display_name)
    descriptor = load_descriptor(ROOT, entry.slug)
    if descriptor:
        resolved = build_descriptor(
            manifest=manifest_entry,
            display_name=str(
                descriptor.get('display_name')
                or ((descriptor.get('layers') or {}).get('minimal') or {}).get('display_name')
                or defaults.get('display_name')
                or entry.display_name
            ),
            family_slug=str(descriptor.get('family_slug') or entry.slug),
            shared_summary=str(descriptor.get('shared_summary') or manifest_entry['layers']['minimal'].get('summary') or ''),
            shared_constraints=tuple(descriptor.get('shared_constraints') or ()),
            modes=tuple(descriptor.get('modes') or ()),
            benchmark_sources=tuple(descriptor.get('benchmark_sources') or ()),
            quality_profile=str(descriptor.get('quality_profile')) if descriptor.get('quality_profile') is not None else None,
            quality_status=str(descriptor.get('quality_status')) if descriptor.get('quality_status') is not None else None,
            judge_reports=tuple(descriptor.get('judge_reports') or ()),
            consumption_hints=dict(descriptor.get('consumption_hints') or defaults.get('consumption_hints') or {}),
            quality_pass_count=descriptor.get('quality_pass_count'),
            quality_stop_reason=str(descriptor.get('quality_stop_reason')) if descriptor.get('quality_stop_reason') is not None else None,
        )
        descriptor_layers = descriptor.get('layers') or {}
        if isinstance(descriptor_layers, dict):
            resolved_layers = resolved.setdefault('layers', {})
            for layer_name, layer_payload in descriptor_layers.items():
                if not isinstance(layer_payload, dict):
                    continue
                base = dict(resolved_layers.get(layer_name) or {})
                if layer_name == 'minimal':
                    for key, value in layer_payload.items():
                        if key not in {
                            'capability_type',
                            'summary',
                            'display_name',
                            'required_inputs',
                            'expected_outputs',
                            'tool_policy',
                            'resources',
                            'packaging_profile',
                            'install_target',
                            'emitted_surfaces',
                            'source_provenance',
                            'confidence',
                            'rationale',
                            'review_status',
                        } and key not in base:
                            base[key] = value
                else:
                    base.update(layer_payload)
                resolved_layers[layer_name] = base
        for layer_name, layer_payload in (defaults.get('layer_overrides') or {}).items():
            if isinstance(layer_payload, dict):
                resolved.setdefault('layers', {}).setdefault(layer_name, {}).update(layer_payload)
    else:
        resolved = build_descriptor(
            manifest=manifest_entry,
            display_name=str(defaults.get('display_name') or entry.display_name),
            consumption_hints=dict(defaults.get('consumption_hints') or {}),
        )
        for layer_name, layer_payload in (defaults.get('layer_overrides') or {}).items():
            if isinstance(layer_payload, dict):
                resolved.setdefault('layers', {}).setdefault(layer_name, {}).update(layer_payload)
    hints = resolved.setdefault('consumption_hints', {})
    if isinstance(hints, dict):
        artifact_conventions = hints.get('artifact_conventions')
        if isinstance(artifact_conventions, list):
            hints['artifact_conventions'] = [
                item.replace('.meta/quality-reviews/', 'reports/quality-reviews/')
                if isinstance(item, str)
                else item
                for item in artifact_conventions
            ]
    save_descriptor(ROOT, entry.slug, resolved)
    return resolved


def main():
    entries = load_ssot_entries(SSOT_DIR)
    if not entries:
        raise SystemExit('No SSOT files found in ssot/')

    generated = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'generator': {
            'script': 'scripts/build-surfaces.py',
            'python': '3.11+',
            'version': '6.0',
            'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        'ssot_sources': [],
        'surfaces': {name: [] for name in SURFACE_PATHS},
        'resources': {name: [] for name in RESOURCE_PATHS},
    }

    for entry in entries:
        cleanup_slug_outputs(entry.slug)
        manifest_entry = build_ssot_manifest_entry(entry, ROOT, merge_descriptor=False)
        resolve_descriptor(entry, manifest_entry)
        manifest_entry = build_ssot_manifest_entry(entry, ROOT)
        descriptor = load_descriptor(ROOT, entry.slug) or {}
        generated['ssot_sources'].append(manifest_entry)
        emitted = set(manifest_entry['expected_surface_names'])
        tools = parse_tools(entry.frontmatter)
        source_note = source_note_path(ROOT, entry.slug)

        skill_resource_hint = {}
        agent_resource_hint = {}
        for surface_name in emitted:
            if surface_name in RESOURCE_PATHS:
                resource_rel = write_resource(surface_name, entry.slug, descriptor)
                generated['resources'][surface_name].append(resource_rel)
                if surface_name.endswith('skill'):
                    skill_resource_hint[surface_name] = resource_rel
                else:
                    agent_resource_hint[surface_name] = resource_rel
        if source_note.exists():
            pass

        if 'gemini_command' in emitted:
            generated['surfaces']['gemini_command'].append(write_gemini_command(entry.slug, entry.description, entry.body))
        if 'gemini_skill' in emitted:
            generated['surfaces']['gemini_skill'].append(write_gemini_skill(entry.slug, entry.description, entry.body, skill_resource_hint.get('gemini_skill')))
        if 'gemini_agent' in emitted:
            generated['surfaces']['gemini_agent'].append(write_gemini_agent(entry.slug, entry.description, entry.body, agent_resource_hint.get('gemini_agent')))
        if 'claude_command' in emitted:
            generated['surfaces']['claude_command'].append(write_claude_command(entry.slug, entry.description, entry.body))
        if 'claude_agent' in emitted:
            generated['surfaces']['claude_agent'].append(write_claude_agent(entry.slug, entry.description, entry.body, agent_resource_hint.get('claude_agent')))
        if 'kiro_prompt' in emitted:
            generated['surfaces']['kiro_prompt'].append(write_kiro_prompt(entry.slug, entry.description, entry.body))
        if 'kiro_agent' in emitted:
            generated['surfaces']['kiro_agent'].append(
                write_kiro_agent(
                    entry.slug,
                    entry.description,
                    entry.body,
                    f"file://{RESOURCE_PATHS['kiro_agent'](entry.slug).relative_to(ROOT)}",
                    'kiro_skill' in emitted,
                )
            )
        if 'kiro_skill' in emitted:
            generated['surfaces']['kiro_skill'].append(write_kiro_skill(entry.slug, entry.description, entry.body, skill_resource_hint.get('kiro_skill')))
        if 'codex_skill' in emitted:
            generated['surfaces']['codex_skill'].append(write_codex_skill(entry.slug, entry.description, entry.body, skill_resource_hint.get('codex_skill')))
        if 'codex_agent' in emitted:
            generated['surfaces']['codex_agent'].append(write_codex_agent(entry.slug, entry.description, entry.body, tools, agent_resource_hint.get('codex_agent')))

    MANIFEST_PATH.write_text(json.dumps(generated, indent=2) + '\n', encoding='utf-8')
    HANDOFF_PATH.write_text(json.dumps(build_ssot_handoff_contract(ROOT), indent=2) + '\n', encoding='utf-8')
    print('Generated', len(entries), 'ssot entries')


if __name__ == '__main__':
    main()
