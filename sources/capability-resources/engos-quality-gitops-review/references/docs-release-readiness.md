# docs-release-readiness recipe

## Selection and inputs
Caller requests documentation ship readiness for a supplied candidate, or host supplies a bounded F companion request under existing authority. Generic GitOps review retains its default output.

DocsShipHandoff.v1 request with explicit committed/snapshot target kind, deterministic content manifest/digest, exact head/base, requested gate and content evidence; fresh independently reproduced target-tree and hosted/version/command evidence as required. Snapshot allowed only for explicitly limited commit-scope content review.

Missing inputs: Return blocked/unknown response with exact gaps. Never infer live CI or release authority from content PASS; no package dependency on installed Docs skill.

## Output precedence and authority
Preserve default GitOps seven-section output. Companion JSON is embedded evidence, not a new independent review workflow.

Docs explicit substantial-rewrite execution uses existing coordinator/writer/reviewer acceptance. Findings-only/ordinary recommendations/narrow formatting remain advisory. No corresponding cycle is added to GitOps.

Drafts, findings and proposed commands grant no overwrite, install, Git mutation or release authority. Read named source evidence; never invent unavailable commands or hosted results.

## Required artifacts, in order
1. Default seven GitOps sections, with DocsShipHandoff.v1 response JSON inside Recommended Commands or Actions; default headings remain. The F assembler consumes this response as evidence, not an extra eighth top-level section.

## Candidate and evidence protocol
### schemaPath
sources/capability-resources/engos-quality-docs-review/schemas/docs-ship-handoff.schema.json

### version
DocsShipHandoff.v1

### canonicalOwner
engos-quality-docs-review

### gitopsBundling
One allowlisted import into sources/capability-resources/engos-quality-gitops-review/schemas/docs-ship-handoff.schema.json using already accepted .meta/shared-resource-imports.json semantics; generated GitOps copies preserve owner source_path/hash. Integrator owns registry edit. If shared mechanism unavailable on actual branch, integrate prerequisite D2.S2 first; do not hand-copy an independent authored schema.

### requestFields
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

### responseFields
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

### matchingAndFreshness
Docs assembler verifies full identity and canonical manifest rather than trusting digest echo. GitOps independently reproduces every present file raw byte/mode and every deletion from the exact committed candidate tree for merge/release and recomputes its digest; a worktree copy is not proof of that relation. Require committed target kind, scope completeness, matching tree reproduction receipt and all applicable hosted checks for that exact head. Timestamp alone cannot establish freshness. Recheck candidate/upstream at decision; change invalidates affected evidence. Snapshot is permitted only for explicitly labeled commit-scope content review and has status/limits that cannot establish full F ship readiness. A subsequent commit requires a new committed identity, reproduction and matching CI; no auto-promotion. Host may transport evidence; neither skill requires an installed sibling or new runtime.

### verdictOwnership
Docs owns F content findings, five-area scorecard and strict assembled artifact. GitOps owns hosted/git/package readiness. F Ship Verdict PASS requires content PASS and matching ready response for requested ship gate; missing/uncertain/failing required evidence yields FAIL. E Release gate verdict remains docs-content only. Merge/release PASS additionally requires committed target kind and independent exact-tree manifest reproduction. Snapshot content PASS never implies merge/release readiness.

### assembly
F retains Inversion Analysis, Adversarial Findings, scorecard, Ship Verdict and conditional minimum fixes or proposed commands. Cite GitOps evidence/limits under existing verdict/findings slots; do not append GitOps generic report to strict F output. No numeric pass threshold invented.

### schemaValidation
Use oneOf request/response branches keyed kind and candidate target_kind; schema constrains known fields/states. Focused fixture tests verify canonical hashing, target-tree relation, gate matching and freshness. Implement these comparisons within recipe instructions and existing test utilities; no additional runtime, collector or schema engine is required.

### gateScope
The unchanged F-style full ship review defaults to release scope and requires the complete release readiness/command plan before Ship Verdict PASS. A caller explicitly narrowing the gate to commit or merge receives that labeled partial scope; its PASS must say commit-only or merge-only and must not claim the original full ship gate passed. Generic GitOps may assess any declared gate.

### contentManifestContract
{
  "version": "DocsCandidateManifest.v1",
  "pathRules": "Repo-relative exact POSIX paths using /; reject leading slash, empty path/components, . or .. components, backslash, NUL, CR and LF. Do not resolve/normalize case, Unicode or symlinks into a different identity. Duplicate exact paths are errors, never last-write-wins. Only regular files are supported in this seam; symlink/gitlink/special targets return unsupported/blocked.",
  "entries": "Each entry has exactly path, state, mode, sha256. For present, mode is 100644 or 100755 and sha256 is raw file-content bytes SHA-256 (not Git object ID; no newline/text/filter transformation). For deleted, mode and sha256 are null. A deletion must be present at base and absent from reviewed target. Represent rename as deleted old path plus present new path; no implicit rename detection.",
  "ordering": "Sort entries lexicographically by their path encoded as UTF-8 bytes, ascending. Input ordering differences must canonicalize identically; duplicate paths fail before sorting.",
  "serialization": "Serialize exactly {manifest_version:\"DocsCandidateManifest.v1\",target_kind:<candidate.target_kind>,files:<sorted entries>} as JSON with object keys recursively sorted lexicographically, UTF-8 encoding, ensure_ascii=false, separators=(\",\",\":\"), allow_nan=false, and no leading/trailing whitespace or newline. SHA-256 those bytes as lowercase hex. In Python: json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(\",\",\":\"),allow_nan=False).encode(\"utf-8\"). No floating-point data appears in this manifest.",
  "identityEquality": "Match target_kind, base_sha, head_sha, manifest_version, exact normalized manifest and content_digest, not only an echoed digest. Changing snapshot to committed changes target kind/digest even if content bytes happen to match; commit/head evidence is renewed.",
  "scopeCompleteness": "Manifest covers every changed documentation target under the declared scope between base and committed head, including deletions, plus unchanged target files explicitly reviewed. For snapshot use declared exact files/deletions and disclose snapshot scope; completeness outside supplied scope is not inferred. Evidence sources read for claims remain separately cited."
}

### snapshotAcceptance
target_kind=snapshot with gate=merge or release always blocks readiness regardless of head SHA/green CI. With gate=commit it may support a labeled commit-only content review of exact snapshot bytes; the response states no hosted/main/release certification and must not reuse HEAD checks as tests of those bytes. Full F default release gate cannot PASS from this state.

## Active command contract
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

## Historical source compatibility (never active commands)
6) If PASS: exact ship command sequence:
   - git add ...
   - git commit ...
   - git push ...
   - git tag ...
   - git push origin <tag>
   - scripts/package-surfaces.sh --version <next-version>
