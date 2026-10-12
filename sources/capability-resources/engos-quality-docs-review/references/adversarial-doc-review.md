# adversarial-doc-review recipe

## Selection and inputs
Caller names adversarial-doc-review recipe, or clearly requests the donor-specific output set below. Generic docs/release review alone does not select this recipe. Full F ship review defaults to release gate; an explicit narrower user request is labeled partial scope and cannot count as full F ship acceptance.

Repo path: <repo_path>/Core-Prompts

Primary target changes to evaluate:
- docs/prompt-pack/*
- docs/README_TECHNICAL.md
- docs/GETTING-STARTED.md
- docs/ARCHITECTURE.md
- docs/FAQ.md
- README.md
- docs/CLI-REFERENCE.md


Missing inputs: Require candidate identity/content and repository truth. Missing content or any required ship evidence yields FAIL with minimum fixes, never a PASS command sequence. Hosted evidence is needed only to assert shipping readiness, not to identify content findings.

## Output precedence and authority
Only explicitly selected Docs recipe replaces default seven-section output assembly; all source/boundary/independent-review rules retain their actual triggers.

Docs explicit substantial-rewrite execution uses existing coordinator/writer/reviewer acceptance. Findings-only/ordinary recommendations/narrow formatting remain advisory. No corresponding cycle is added to GitOps.

Drafts, findings and proposed commands grant no overwrite, install, Git mutation or release authority. Read named source evidence; never invent unavailable commands or hosted results.

## Required artifacts, in order
1. Inversion Analysis
2. Adversarial Findings
3. Scorecard: Area | Score (0-10) | Evidence paths | Risks, one row per five validation areas
4. Ship Verdict: PASS or FAIL
5. If FAIL: minimum fixes
6. If PASS: exact current proposed command plan from currentShipCommandContract and matching GitOps proposed_steps for the requested gate. For full ship scope: scoped commit/push → independent review and both exact-head CI → merge and main parity → package from verified merged main → same tag object pushed to both remotes → publish and verify downloads. Never tag before package, never origin-only publication, and never emit placeholders as exact commands.

## Retained donor-specific obligations
# Prompt F: Adversarial Evaluation and Ship Gate

```text
You are a release gate reviewer for this repository.
Your job is to aggressively test whether recent documentation and prompt-pack changes are correct, truthful, and shippable.

## Mode
- Primary reflective mode: realism
- Secondary style pressure: edge (push hard on blind spots and weak assumptions)

## Context
Repo path: <repo_path>/Core-Prompts

Primary target changes to evaluate:
- docs/prompt-pack/*
- docs/README_TECHNICAL.md
- docs/GETTING-STARTED.md
- docs/ARCHITECTURE.md
- docs/FAQ.md
- README.md
- docs/CLI-REFERENCE.md

## Inversion First (Mandatory)
Start with failure analysis:
1) Top 3 ways this docs update could fail users or maintainers.
2) "Dogs not barking": missing information that should exist but does not.
3) Trigger conditions that would make release unsafe.

## Adversarial Review (Mandatory)
Red-team the changes:
- Find contradictions between README and docs.
- Find any unsupported command, CLI feature, or process claim.
- Find navigation dead ends.
- Find tone risks (hype over factual accuracy).
- Find accessibility risks (missing alt-text guidance, unclear visual semantics).

## Validation Checks (Must run all)
1) Truthfulness:
   - Every command in docs appears in actual scripts/docs.
   - No unsupported CLI or fabricated feature claims.
   - No unverifiable market claims.
2) Approachability:
   - Purpose clear in first screenful.
   - "Get started" path is prominent.
   - Clear onward links with no dead ends.
3) Separation:
   - README stays concise.
   - Technical depth is delegated to docs pages.
4) Visual policy:
   - Mixed visuals policy is explicit.
   - Alt text requirements are explicit.
   - Diagram guidance maps to real architecture.
5) AI-installability:
   - Handoff snippet is present and actionable.
   - New contributor can run build/validate/deploy from docs flow.

## Output Format (Strict)
Return in this order:

1) Inversion Analysis
2) Adversarial Findings
3) Scorecard table with one row per validation area:
   - Area
   - Score (0-10)
   - Evidence paths
   - Risks
4) Ship Verdict: PASS or FAIL
5) If FAIL: minimum required fixes
6) Historical source command sequence (D8-COMPAT-SHIP-ORDER; never active commands):
   - git add ...
   - git commit ...
   - git push ...
   - git tag ...
   - git push origin <tag>
   - scripts/package-surfaces.sh --version <next-version>

## Hard Constraints
- Do not assume facts not present in repository files.
- Cite file paths for every major claim.
- Be conservative: if uncertain, fail the gate.
```

## Active ship readiness and command order
sources/capability-resources/engos-quality-docs-review/schemas/docs-ship-handoff.schema.json

DocsShipHandoff.v1

engos-quality-docs-review

One allowlisted import into sources/capability-resources/engos-quality-gitops-review/schemas/docs-ship-handoff.schema.json using already accepted .meta/shared-resource-imports.json semantics; generated GitOps copies preserve owner source_path/hash. Integrator owns registry edit. If shared mechanism unavailable on actual branch, integrate prerequisite D2.S2 first; do not hand-copy an independent authored schema.

{
  "schema_version": "DocsShipHandoff.v1",
  "kind": "request",
  "gate": "commit|merge|release",
  "candidate": {
    "target_kind": "committed|snapshot (required explicit discriminator)",
    "base_sha": "full resolved baseline commit SHA",
    "head_sha": "full resolved candidate commit SHA for committed; contextual current HEAD only for snapshot, never certification of snapshot bytes",
    "manifest_version": "DocsCandidateManifest.v1",
    "content_digest": "SHA-256 of exact canonical manifest encoding defined in contentManifestContract",
    "files": "sorted unique entries {path,state:present|deleted,mode:100644|100755|null,sha256:64 lowercase hex|null}; all declared reviewed target files and changed documentation paths in scope are represented; no omitted deletion",
    "scope_note": "Explicit declared documentation review scope; this content manifest is not evidence that unrelated code received review."
  },
  "content_result": {
    "verdict": "PASS|FAIL",
    "evidence": "array of inspectable source refs",
    "unknowns": "array of explicit unknowns"
  },
  "requested_checks": "list appropriate to gate",
  "authority": "list of actual authorized actions; advisory default, not inferred from verdict"
}

{
  "schema_version": "DocsShipHandoff.v1",
  "kind": "response",
  "candidate": "same request identity including content_digest",
  "gate": "same requested gate",
  "status": "ready|blocked|unknown",
  "observed_at": "UTC observation timestamp",
  "checks": "array {name,status(pass|fail|unknown|not_applicable),evidence_ref,observed_head,reason}; for merge/release every applicable hosted check must identify the exact committed candidate head and result. not_applicable requires gate-specific reason and cannot substitute for a required check.",
  "version_prerequisites": "{version,top_changelog_version,unreleased_empty,release_base,package_verified}; unresolved values explicit null/unknown",
  "proposed_steps": "ordered {phase,argv,preconditions,evidence_refs}; shell argument vectors, never executed by receipt",
  "unknowns": "array",
  "blockers": "array",
  "authority": "echo actual relevant authorization; readiness never grants it",
  "manifest_verification": {
    "method": "committed_tree_reproduced|snapshot_bytes_observed",
    "verified_target_kind": "committed|snapshot",
    "verified_head": "exact committed candidate head for tree reproduction; contextual head for snapshot only",
    "reproduced_content_digest": "freshly recomputed canonical digest",
    "evidence_ref": "inspectable record of target extraction/hash and scope completeness",
    "limitation": "Snapshot observation proves only supplied bytes; it cannot certify committed/main/hosted readiness."
  }
}

Docs assembler verifies full identity and canonical manifest rather than trusting digest echo. GitOps independently reproduces every present file raw byte/mode and every deletion from the exact committed candidate tree for merge/release and recomputes its digest; a worktree copy is not proof of that relation. Require committed target kind, scope completeness, matching tree reproduction receipt and all applicable hosted checks for that exact head. Timestamp alone cannot establish freshness. Recheck candidate/upstream at decision; change invalidates affected evidence. Snapshot is permitted only for explicitly labeled commit-scope content review and has status/limits that cannot establish full F ship readiness. A subsequent commit requires a new committed identity, reproduction and matching CI; no auto-promotion. Host may transport evidence; neither skill requires an installed sibling or new runtime.

Docs owns F content findings, five-area scorecard and strict assembled artifact. GitOps owns hosted/git/package readiness. F Ship Verdict PASS requires content PASS and matching ready response for requested ship gate; missing/uncertain/failing required evidence yields FAIL. E Release gate verdict remains docs-content only. Merge/release PASS additionally requires committed target kind and independent exact-tree manifest reproduction. Snapshot content PASS never implies merge/release readiness.

F retains Inversion Analysis, Adversarial Findings, scorecard, Ship Verdict and conditional minimum fixes or proposed commands. Cite GitOps evidence/limits under existing verdict/findings slots; do not append GitOps generic report to strict F output. No numeric pass threshold invented.

Use oneOf request/response branches keyed kind and candidate target_kind; schema constrains known fields/states. Focused fixture tests verify canonical hashing, target-tree relation, gate matching and freshness. Implement these comparisons within recipe instructions and existing test utilities; no additional runtime, collector or schema engine is required.

The unchanged F-style full ship review defaults to release scope and requires the complete release readiness/command plan before Ship Verdict PASS. A caller explicitly narrowing the gate to commit or merge receives that labeled partial scope; its PASS must say commit-only or merge-only and must not claim the original full ship gate passed. Generic GitOps may assess any declared gate.

{
  "version": "DocsCandidateManifest.v1",
  "pathRules": "Repo-relative exact POSIX paths using /; reject leading slash, empty path/components, . or .. components, backslash, NUL, CR and LF. Do not resolve/normalize case, Unicode or symlinks into a different identity. Duplicate exact paths are errors, never last-write-wins. Only regular files are supported in this seam; symlink/gitlink/special targets return unsupported/blocked.",
  "entries": "Each entry has exactly path, state, mode, sha256. For present, mode is 100644 or 100755 and sha256 is raw file-content bytes SHA-256 (not Git object ID; no newline/text/filter transformation). For deleted, mode and sha256 are null. A deletion must be present at base and absent from reviewed target. Represent rename as deleted old path plus present new path; no implicit rename detection.",
  "ordering": "Sort entries lexicographically by their path encoded as UTF-8 bytes, ascending. Input ordering differences must canonicalize identically; duplicate paths fail before sorting.",
  "serialization": "Serialize exactly {manifest_version:\"DocsCandidateManifest.v1\",target_kind:<candidate.target_kind>,files:<sorted entries>} as JSON with object keys recursively sorted lexicographically, UTF-8 encoding, ensure_ascii=false, separators=(\",\",\":\"), allow_nan=false, and no leading/trailing whitespace or newline. SHA-256 those bytes as lowercase hex. In Python: json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(\",\",\":\"),allow_nan=False).encode(\"utf-8\"). No floating-point data appears in this manifest.",
  "identityEquality": "Match target_kind, base_sha, head_sha, manifest_version, exact normalized manifest and content_digest, not only an echoed digest. Changing snapshot to committed changes target kind/digest even if content bytes happen to match; commit/head evidence is renewed.",
  "scopeCompleteness": "Manifest covers every changed documentation target under the declared scope between base and committed head, including deletions, plus unchanged target files explicitly reviewed. For snapshot use declared exact files/deletions and disclose snapshot scope; completeness outside supplied scope is not inferred. Evidence sources read for claims remain separately cited."
}

target_kind=snapshot with gate=merge or release always blocks readiness regardless of head SHA/green CI. With gate=commit it may support a labeled commit-only content review of exact snapshot bytes; the response states no hosted/main/release certification and must not reuse HEAD checks as tests of those bytes. Full F default release gate cannot PASS from this state.
{
  "kind": "proposed_command_plan_only",
  "sourceLines": "docs/RELEASE-PACKAGING.md:10-46,57-62,163-173 plus script checks",
  "steps": [
    {
      "phase": "prepare-commit",
      "sequence": [
        "Inspect exact authorized files and same-slice docs/changelog",
        "git add -- <exact approved paths>",
        "git commit -m <reviewed message>"
      ],
      "condition": "scope and source review pass; never broad git add ."
    },
    {
      "phase": "candidate-checks",
      "sequence": [
        "git push gitlab <task-branch>",
        "git push origin <task-branch>",
        "Open/refresh actual PR/MR; verify exact-head required checks and independent reviews on both providers"
      ],
      "condition": "Use actual remote identities; no release claim from local-only checks"
    },
    {
      "phase": "merge",
      "sequence": [
        "Use current verified protected merge procedure for GitLab primary and GitHub mirror",
        "Fetch both main refs, require same intended integrated commit and required post-merge checks"
      ],
      "condition": "Actual merge authority and branch protection; no invented universal merge CLI command"
    },
    {
      "phase": "merged-release-preflight",
      "sequence": [
        "Use a clean task-owned checkout of verified integrated main",
        "Verify VERSION, top CHANGELOG release entry and empty Unreleased; preceding release tag object/commit agree on both providers",
        "Set CORE_PROMPTS_RELEASE_BASE_REF to the verified preceding release",
        "Run current documented local release gates and rebuild distribution with bin/capability-fabric build"
      ],
      "condition": "Separate explicit release scope; respect source-defined validate-before-build ordering on committed checkout; current help/docs governs exact gate commands"
    },
    {
      "phase": "package",
      "sequence": [
        "scripts/package-surfaces.sh --version <exact VERSION value>",
        "Verify expected archive contents/checksums and candidate identity"
      ],
      "condition": "Merged-state package complete before tag; no fabricated next-version"
    },
    {
      "phase": "tag",
      "sequence": [
        "git tag -a <exact version tag> <verified merged SHA> -m <reviewed message>",
        "git push gitlab <exact version tag>",
        "git push origin <exact version tag>"
      ],
      "condition": "Explicit exact tag/release authority; same local tag object pushed to both, no replace/force"
    },
    {
      "phase": "publish-verify",
      "sequence": [
        "Use verified current GitLab/GitHub release tooling for exact reviewed assets/checksums",
        "Download assets from each provider and compare actual bytes/digests; installation separately authorized"
      ],
      "condition": "Exact verified artifact paths and provider commands supplied from current help, not fabricated defaults"
    }
  ],
  "renderingRule": "These are design placeholders, not executable output or permission. For F PASS output, GitOps must render exact argv/identities for the requested authorized gate using current CLI help and actual candidate state. If required identity/help/evidence unavailable, F FAIL with minimum fix; do not label placeholders exact commands. For commit/merge gate, future release steps stay explicitly out-of-scope, not executed. Current program release hold remains."
}
