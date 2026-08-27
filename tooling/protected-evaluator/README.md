# Protected evaluator project template

Use this directory as the seed for a separate, private GitLab project. The public template contains orchestration only. Do not add sealed cases, labels, signing keys, credentials, raw traces, protected scorer implementations, judge implementations, or model credentials to Core-Prompts.

## Trust boundary

- Accept only a signed and unexpired `CandidateSubmission.v1` containing artifact hashes.
- Clone the reviewed evaluator, baseline, and candidate at full immutable Git commits into isolated workspaces. Make tracked files read-only before evaluation.
- Keep the sealed bundle on protected storage outside every repository and candidate-readable root.
- Give only Batman microrepo trials and adapter-conformance probes the exact preregistered `repo-write-subagents` policy and explicit tool allowlist. Run them in isolated Git workspaces with no remotes, isolated homes and temporary directories, and remote access denied.
- Keep deterministic scoring, semantic-judge qualification, verdict construction, validation, Git checkout, and signing tools-off with approvals and remote access denied.
- Pass commands only through protected configuration as argv arrays; never inherit an unregistered tool policy.
- Run the primary and reproduction on distinct protected runner identities with distinct preregistered run IDs and seeds.
- Verify each run's complete hash chain before scoring or signing it.
- Persist raw traces as protected artifacts. Publish only aggregate, redacted results.
- Embed signatures in adapter-conformance certificates, execution receipts, judge qualifications, the sealed-bundle attestation, and the final verdict only after their bound files are immutable.
- Sign through the pinned evaluator's canonical `core_prompts_eval.attestations.signature_message` domain-separated SHA-256 contract, then cross-verify every emitted signature with `validate_signed_attestation` before publication.
- Keep run manifests and `ProtectedScoreReport.v1` closed and unsigned. The signed verdict authenticates their exact hashes.
- Use a different Ed25519 key and key ID for each of the six embedded-signature purposes, including `global_token_ledger`. A trust root must authorize exactly one purpose.
- Assemble those six public roots into one closed `ProtectedTrustStore.v1`, bind its reviewed SHA-256 in protected configuration, and provide it through the protected `EVALUATOR_TRUST_STORE_FILE` variable. Keep individual roots inside the store for signing-key cross-checks; use the aggregate store for verification and UAC promotion intake.
- Return only signed, redacted public evidence. Never return sealed cases, labels, prompt bodies, response bodies, model credentials, commands, filesystem paths, or raw traces.
- Fail closed. A missing or stale seal, judge, key, receipt, score, reproduction, hash, commit, or token-cap binding cannot promote.

## Executable contract

`protected-runner` is the only executable entrypoint used by `gitlab-ci.template.yml`. It never accepts a command from a candidate submission and never invokes a shell. The closed `phase_commands` map binds each subcommand to one reviewed absolute executable and fixed leading argv.

Private signing-key paths never appear in configuration. Configuration binds only the six reviewed public key IDs. A signing invocation must provide exactly one `--signing-purpose` and matching `--signing-key`; non-signing, model, case-preparation, validation, scoring, and judging phases reject both flags. Signing phases accept unsigned artifacts only at their purpose-specific, fixed paths under private output and enforce the canonical evidence schema before signing.

The reviewed phase commands cover these operations:

- `adapter_conformance_command`: the protected Codex/Kiro probe controller described below.
- `capability_eval_command`: the pinned Core-Prompts `capability-eval compare` executable. The runner appends the reviewed repository root, baseline, candidate, adapter-bound run plan, promotion profile, explicit model-call authorization, and exact token cap.
- `score_command`: a deterministic protected scorer. It receives only fixed `--primary-run`, `--reproduction-run`, `--sealed-bundle`, and `--output` arguments and must emit one `ProtectedScoreReport.v1` JSON object.
- `judge_commands`: independently qualified semantic judges. Each receives fixed judge ID, run, sealed-bundle, and output arguments and must emit one passing `JudgeQualification.v1` JSON object.
- `verdict_command`: the reviewed verdict builder. It receives a hash-only protected input and output path and must emit an unsigned `PromotionVerdict.v2`. The runner signs it only when status is `promote` and every earlier gate passed. `PromotionVerdict.v1` is accepted only by its legacy read-only validator and is refused for promotion.

Adapter credentials are explicit and provider-specific. Codex accepts only the masked, protected `OPENAI_API_KEY` environment variable, and only after its protected conformance certificate proves the corresponding redacted credential binding. Kiro requires `KIRO_SERVICE_CREDENTIAL_FILE`, an absolute, mode-`0600`, nonsymlink protected service credential documented by `documentation_reference`; personal `~/.kiro`, AWS profiles, cached sessions, and copied home configuration are forbidden. Missing credentials make conformance and the affected trial phase inconclusive before model calls. Child stderr and credential values are never published.

The global raw-token cap is exactly 5,000,000 across adapter conformance, primary, reproduction, and judge/adjudication work together. `global_token_budget.allocations` may partition or lower that cap but may not exceed it. Every protected model call reserves before execution, records observed usage afterward, and carries the signed cumulative ledger to the next GitLab job. No phase-local cap resets the global ledger.

`registered_trial_tool_policy` is the single authority registration for Batman model calls. Primary, reproduction, and conformance policies must match it exactly. The controller rejects tools-off trial plans, broader allowlists, different modes, and per-cell drift. This exception never applies to scoring, judging, verdict construction, or signing.

`adapter_conformance_command` must use an absolute, protected executable path. It runs one fixed, minimal Codex probe and one fixed, minimal Kiro probe from the isolated probe workspace on protected main. The command must preserve complete raw evidence privately and return the closed probe receipt consumed by the controller. Set `CONFORMANCE_RUNNER_IDENTITY` to the dedicated GitLab runner's `CI_RUNNER_ID`; the controller verifies it before either probe.

For each cell, the command writes `probe-evidence.json`, `raw-trace.jsonl`, hash-named fixture receipts under `fixture-receipts/`, and hash-named live receipts under `probe-receipts/`. The controller verifies every file commitment; exact model identity; complete raw, cached, and billed usage; one attempt with verified retry semantics; isolated session identity; fixed dispatch, implementation, test, and review events; and disjoint controller, implementer, and reviewer authorship. It then emits an embedded-signed `AdapterConformance.v1` certificate and materializes canonical primary and reproduction run plans with per-cell certificate path/hash bindings. Any missing requirement produces an inconclusive phase result and stops before promotion trials.

The CI phases are ordered, runner-bound, and split by trust domain:

1. `validate-submission`
2. `authorize-global-budget`
3. `adapter-conformance` under a credentialed model UID with no seal or signing keys
4. `sign-adapter-conformance` under a signer UID with no model credentials
5. `prepare-sealed-cases` and `prepare-gold-evidence` on the sealed-data runner
6. `evaluate-primary` and `evaluate-reproduction` with prompt-only inputs, bounded credentials, signed conformance, and no seal, labels, or keys
7. `score-and-judge` with model outputs and gold evidence, tools off, and no candidate execution or signing keys
8. `finalize-protected-verdict` with validated hash-only artifacts and purpose-separated signing keys, but no model execution, prompt bodies, gold labels, or adapter credentials

Every secret-bearing job uses an explicit protected runner tag and checks `CI_RUNNER_ID`. Model jobs must use a separate UID/container or mount namespace that cannot read sealed storage, gold labels, private evaluator output, or signing-key paths. Prompt and gold artifacts are produced by separate jobs so model jobs cannot download the gold artifact. Primary and reproduction raw artifacts travel between protected jobs under maintainer-only access. Only `public-output/` is suitable for external publication.

The signed token ledger advances explicitly across those domains: budget authorization writes `000000`; conformance signing validates that predecessor and writes `000001`; primary models read `000001` and the primary reconciler signs `000002`; reproduction models read `000002` and the reproduction reconciler signs `000003`; scoring and judging read `000003`; finalization signs `000004` with `status: final` and binds that exact file into `PromotionVerdict.v2.token_ledger_binding`. No command discovers a sibling ledger implicitly.

## Initial setup

1. Create a private GitLab project from this template and restrict membership to evaluation maintainers.
2. Protect the default branch, tags, environments, runners, and signing variables. Disable fork pipelines.
3. Store sealed material outside the checkout. Give only the protected evaluator identity read access.
4. Copy `config/protected-evaluator.example.json` to `config/protected-evaluator.json`. Pin the evaluator, baseline, and candidate to reviewed 40-character commits. Set distinct primary and reproduction runner identities.
5. Generate one signing key per purpose on an offline or protected maintainer host. For example:

   ```bash
   python3 scripts/generate_signing_key.py \
     --private-key-out /protected/evaluator/execution-receipt.key \
     --trust-root-out /protected/evaluator/execution-receipt-root.json \
     --key-id evaluator-execution-receipt-2026-01 \
     --purpose execution_receipt \
     --not-before 2026-08-27T00:00:00Z \
     --expires-at 2027-02-27T00:00:00Z
   ```

   Repeat for `adapter_conformance`, `global_token_ledger`, `judge_qualification`, `sealed_bundle`, and `promotion_verdict`, changing both paths and key IDs. The command writes no key material to stdout. Each private file is created with mode `0600` and refuses to overwrite an existing path. Publish only the aggregate reviewed trust-store JSON.

6. Provision a separate submission-signing key restricted to `candidate_submission`. Give the protected evaluator only its public trust root. Do not authorize the submission key to sign evaluator evidence.
7. Install the reviewed protected scorer, qualified judges, and verdict builder in the private project. Their command paths belong only in protected configuration; candidate submissions cannot alter them.
8. Copy `gitlab-ci.template.yml` to `.gitlab-ci.yml`. Configure masked, protected file variables for the candidate submission, submission trust root, evaluator trust store, sealed bundle, sealed attestation, primary and reproduction run plans, and every purpose-separated private signing key named by the template. Record each signing key ID and the reviewed trust-store SHA-256 in `config/protected-evaluator.json`; do not create parallel evaluator-root file variables.
9. Assign every trust-domain job to its documented protected runner tag and expected `CI_RUNNER_ID`. Primary and reproduction identities must differ. Enforce separate UIDs or containers and mount only the job-scoped inputs shown by the template. Keep fork pipelines disabled and require protected main.

## Public and private outputs

Public output is hash- and aggregate-only:

- phase result records;
- the public purpose-separated evaluator trust store used by `bin/uac apply --promotion-trust-root`;
- signed promotion verdict;
- signed sealed-bundle attestation;
- closed aggregate score report whose exact hash is signed by the verdict;
- signed judge qualifications;
- closed primary and reproduction manifests whose exact hashes are signed by the verdict;
- signed execution receipts, which contain commitments and usage but no prompt or response bodies.

Private output includes run manifests, signed receipts, raw trial records, raw traces, the hash-only verdict input, and unsigned intermediate files. Retention and access controls for private output are part of the protected evaluator's operational policy.

After independently transferring the reviewed public bundle into Core-Prompts, UAC consumes the exact published store rather than any individual evaluator root:

```bash
bin/uac apply <candidate-source> \
  --promotion-verdict <public-bundle>/promotion-verdict.json \
  --promotion-trust-root <public-bundle>/evaluator-trust-store.json \
  --yes
```

## Rotation and revocation

Create a new purpose-specific key ID before expiry, overlap only long enough to finish in-flight runs, replace that public root inside the reviewed trust store, and update the bound store hash. To revoke a key, set `revoked_at` in its store entry and stop its protected pipelines. Never reuse a revoked or expired key for another purpose.

This repository intentionally contains no real key, sealed case, label, protected scoring implementation, qualified judge implementation, model credential, or executed model result.
