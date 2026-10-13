# factual-audit recipe

## Selection and inputs
Caller names factual-audit recipe, or clearly requests the donor-specific output set below. Generic docs/release review alone does not select this recipe.

- Candidate README draft
- Candidate docs drafts
- Repository truth sources:
  - README.md
  - docs/
  - scripts/
  - AGENTS.md
  - .meta/manifest.json
  - .meta/surface-rules.json


Missing inputs: Require supplied candidate docs and accessible truth sources. Missing evidence yields unclear/needs_revision and content FAIL plus exact fixes, not invented facts or hosted readiness.

## Output precedence and authority
Only explicitly selected Docs recipe replaces default seven-section output assembly; all source/boundary/independent-review rules retain their actual triggers.

Docs explicit substantial-rewrite execution uses existing coordinator/writer/reviewer acceptance. Findings-only/ordinary recommendations/narrow formatting remain advisory. No corresponding cycle is added to GitOps.

Drafts, findings and proposed commands grant no overwrite, install, Git mutation or release authority. Read named source evidence; never invent unavailable commands or hosted results.

## Required artifacts, in order
1. factual_audit.json object
2. Recommended edits by file Markdown bullets
3. Release gate verdict: PASS or FAIL
4. If FAIL: minimum required fixes

## Retained donor-specific obligations
# Prompt E: Factual and Consistency Gate

```text
You are the final factual gate for docs drafts. Your role is to detect and fix unsupported claims, command drift, and consistency breaks.

## Scope
Review candidate docs and output:
1) factual_audit.json
2) revision recommendations grouped by file

## Inputs
- Candidate README draft
- Candidate docs drafts
- Repository truth sources:
  - README.md
  - docs/
  - scripts/
  - AGENTS.md
  - .meta/manifest.json
  - .meta/surface-rules.json

## Hard Rules
1) Flag any claim that is not backed by a file path.
2) Flag command lines that do not exist or mismatch script usage.
3) Flag unsupported CLI feature descriptions.
4) Reject unverifiable market claims ("best", "most used", "widely adopted") unless evidence exists in-repo.
5) Preserve approachable tone while rewriting risky claims to factual language.

## Output Schema
Return valid JSON with this shape:
{
  "summary": {
    "total_claims": 0,
    "verified": 0,
    "needs_revision": 0,
    "unclear": 0
  },
  "items": [
    {
      "claim": "",
      "file": "",
      "status": "verified|needs_revision|unclear",
      "source_paths": [],
      "issue": "",
      "safe_rewrite": ""
    }
  ]
}

Then return:
- "Recommended edits by file" as Markdown bullets.
- "Release gate verdict": PASS or FAIL.
- If FAIL, include minimum required fixes to pass.
```

## Legacy master array format
{
  "claim": "...",
  "source_paths": ["..."],
  "status": "verified|needs_revision|unclear",
  "rewrite_if_needed": "..."
}

## Validation and same-format roundtrip
{
  "path": "resources/scripts/factual_audit.py",
  "purpose": "One small Python standard-library helper for the two legacy shapes; validate without mutating inputs and reproduce valid payloads without field loss. No repository traversal, subprocesses, network, state store, scheduler or cross-format inference.",
  "minPython": "3.11",
  "commands": [
    {
      "argv": [
        "python3",
        "<skill>/resources/scripts/factual_audit.py",
        "validate",
        "--format",
        "master-array|prompt-e-object",
        "--input",
        "<file.json>"
      ],
      "stdout": "One stable JSON report: format, valid boolean, issues array of {path,code,message}. No audit payload rewriting.",
      "exitCodes": {
        "0": "valid shape and coherent counts",
        "2": "malformed/invalid payload or inconsistent counts",
        "3": "CLI/input I/O failure"
      }
    },
    {
      "argv": [
        "python3",
        "<skill>/resources/scripts/factual_audit.py",
        "roundtrip",
        "--format",
        "master-array|prompt-e-object",
        "--input",
        "<file.json>"
      ],
      "stdout": "On success only the original-format JSON payload with all values, object key order, array order and extension fields preserved. Whitespace/escape spelling may change; semantic equality required. On failure no payload stdout; structured diagnostic stderr.",
      "exitCodes": {
        "0": "validated payload emitted",
        "2": "invalid payload; no rewrite",
        "3": "CLI/input I/O failure"
      }
    }
  ],
  "inputSafety": "Read one explicitly supplied UTF-8 JSON file; duplicate object keys and NaN/Infinity fail before validation. Read-only, no output-path option or original overwrite. Error diagnostics identify paths/codes without echoing whole potentially private inputs. No auto-detected format and no silent fallback between formats.",
  "validationRules": [
    "master-array is an array; each object requires claim:string, source_paths:array of strings, status:enum(verified,needs_revision,unclear), rewrite_if_needed:string.",
    "prompt-e-object requires summary and items; summary requires total_claims/verified/needs_revision/unclear nonnegative integers (booleans invalid). Items require claim/file/issue/safe_rewrite strings, source_paths array of strings and status enum.",
    "Allow and preserve unknown extension keys at legacy object levels; known-field wrong types still fail. Do not require nonempty claim/source strings beyond actual donor contract without an explicit amendment.",
    "Prompt-E counts equal items length and counts by status. Count inconsistencies are errors with original values untouched, never repaired silently.",
    "Empty array and empty summary/items object with all zero counts are valid. Example literal verified|needs_revision|unclear is not a valid produced status."
  ],
  "schemaRelation": "Author JSON Schema Draft 2020-12 first in factual-audit.schema.json, with $defs master-array and prompt-e-object and unambiguous array/object oneOf. Schema checks structure; helper mirrors those narrow rules and adds count/duplicate-key/nonfinite semantic checks. Differential fixture tests compare helper structural results with installed CI jsonschema; no jsonschema runtime dependency is added to distributed skill.",
  "adapterBoundary": "roundtrip is same-format identity adaptation only. master\u2194E conversion unsupported; wrong selected format fails. No DocsFactualAudit.v1 envelope implementation in this slice because no actual new consumer needs it."
}

A future DocsFactualAudit.v1 could preserve source_format and a lossless payload only for an explicitly opted-in consumer; no envelope or format conversion is implemented.

## Exact JSON wire preservation

Validate numeric values through standard-library Decimal, including extension numbers. Genuine JSON numbers such as 0.10000000000000001, 1e-999, 1e999 and negative zero are finite decimal values; binary-float overflow/underflow is not their validity criterion. Reject NaN/Infinity and duplicate keys. Integer summary counts follow JSON Schema's numeric meaning: finite nonnegative integral values, including 0.0, are accepted; booleans, negative and fractional values fail. Counts must equal the observed item/status totals and are never repaired.

After validation, roundtrip emits the original UTF-8 JSON wire text unchanged, preserving numeric tokens, whitespace, escapes, CR/LF, extension keys and item/key order. Escaped lone surrogates in strings or keys remain escaped wire and roundtrip safely. Invalid UTF-8 input receives the structured I/O diagnostic; malformed/unsupported JSON receives a structured invalid-input diagnostic, never a payload or traceback. No numeric normalization or cross-format translation occurs.
