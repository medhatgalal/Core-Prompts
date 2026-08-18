# Instruction Clarity Policy

Policy identifier: `instruction_clarity.v1`

Use the machine-readable policy at `.meta/instruction-clarity.json` when working in the Core-Prompts repository. This bundled reference explains the portable contract.

## Sources

The policy summarizes selected guidance from:

- https://developers.google.com/style/
- https://developers.google.com/style/voice
- https://developers.google.com/style/tone
- https://developers.google.com/style/accessibility
- https://developers.google.com/style/translation

It does not copy or adopt the entire Google guide.

## Classes

- `lint`: report a possible clarity problem.
- `safe_fix`: normalize formatting only when behavior is provably unchanged.
- `candidate_only`: propose the edit and require preservation evidence.
- `forbidden_auto_fix`: never change commands, modality, authority, safety, prerequisites, ordering, schemas, outputs, examples, exceptions, or fallbacks automatically.

## Decision rule

Clarity is a separate human-quality axis. Behavioral fitness comes from task-specific evaluation against the Goal Contract and topology. Neither axis substitutes for the other.
