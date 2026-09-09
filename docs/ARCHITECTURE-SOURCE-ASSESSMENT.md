# Historical Architecture Source Assessment

This records the original architecture capability intake. It is historical source context, not current installation, routing, or validation guidance. Use the [Skill Job Map](SKILL-JOB-MAP.md) and [UAC usage](UAC-USAGE.md) for active workflows.

## Harish Garg architecture folder
- Source: `https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/architecture`
- Best use: family skeleton
- Classification: architecture skill family
- Limitation: weak deterministic objective/in-scope extraction in raw form
- Result: imported and uplifted into `ssot/engos-design-architecture.md`, but only after replacing the default scaffold with a stronger family-level SSOT entry

## Alexanderdunlop ai-architecture-prompts
- Source: `https://github.com/Alexanderdunlop/ai-architecture-prompts`
- Best use: architecture quality benchmark and design input
- Strength: black-box interfaces, replaceability, constant velocity, human cognitive load
- Result: used as the benchmark for the shipped `engos-design-architecture` family and for the Capability Fabric boundary design itself
