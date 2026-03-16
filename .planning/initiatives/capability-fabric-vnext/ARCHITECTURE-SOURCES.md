# Architecture Source Assessment

## Harish Garg architecture folder
Source: `https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/architecture`

Assessment:
- Useful family skeleton
- Reads as one architecture skill family
- Weak raw deterministic structure for objective/in-scope extraction
- Raw import is acceptable only as a landing scaffold, not as final SSOT quality

Outcome:
- Imported through UAC
- Landed as `ssot/architecture.md`
- Then manually uplifted into a stronger family entry with explicit mode contracts

## Alexanderdunlop ai-architecture-prompts
Source: `https://github.com/Alexanderdunlop/ai-architecture-prompts`

Assessment:
- Stronger architecture-quality reference
- Better black-box boundary and replaceability framing
- Better fit as design input for Capability Fabric and as benchmark for the final architecture family

Outcome:
- Used to shape the final architecture family summary, standards, and mode expectations
- Preserved in `.meta/capabilities/architecture.json` and `.meta/capabilities/architecture.sources.md` as benchmark lineage
