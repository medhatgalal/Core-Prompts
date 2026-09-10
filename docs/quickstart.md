# Core-Prompts Quickstart — Reviewed Home Installation

Start with [Getting Started](GETTING-STARTED.md) for capability selection and
[Installation Profiles](INSTALL-PROFILES.md) for the canonical installation procedure.
Fresh installs select skills by default; `--with-agents` explicitly includes named
agents. Repair independently recognizes existing skills and agents, including
installations without an updater or receipts. A file count alone does not establish
installation.

## A prompt for your local agent

```text
Install or repair Core-Prompts using its current installer on this machine.
Inspect the repository instructions and docs/INSTALL-PROFILES.md first. Verify
repository identity, branch, dirty state, and remote main parity. Preserve local
changes; do not blindly pull into an existing checkout.

Resolve the supported harnesses, selected surfaces, and intended home target. Preview in
a disposable target as documented. For the real home, pass an explicit --target
and --allow-nonlocal-target; the install wrapper otherwise targets the repository.
Create and review the exact dry-run plan before applying it. Historical recognition
must use complete trusted catalog identities or valid ownership receipts. Inspect
preserved packages and global blockers; do not overwrite custom or unknown packages.

Use ssot/ as canonical source and the generated harness directories as outputs.
Do not use legacy skills/ or clis/ directories as the source. Do not require an
unrelated repository or secrets file merely to inspect or install these skills.

Verify installation.json selection and ownership, selected package hashes, installed
version, and a fresh repeat plan. Report each selected harness separately, including
preservation conflicts even when independent packages were updated successfully.
Distinguish files installed, CLI discovery, agent registration and authenticated
runtime acceptance. A directory count or successful copy is not proof of all four.
Preserve unrelated home files and existing schedules. Installer enrollment supplies
a missing updater; create or change a schedule only if I explicitly request it.
Report blockers, partial results, and recovery transaction IDs explicitly.
```

## Explicit home target

From a trusted current release or verified source checkout, preview Kiro repair:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --cli kiro --repair --dry-run > /tmp/core-prompts-home-plan.json
```

Review the plan using [installation and recovery](INSTALL-PROFILES.md), then apply:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --apply-plan /tmp/core-prompts-home-plan.json
```

No earlier standalone updater refresh is required. Runtime conflicts still block
changes; preserved package conflicts return exit `2` and require attention. Normal
installation supplies the updater and saves concrete selection. Use
`~/update_core_prompts.sh --schedule-daily HH:MM` only to explicitly request a
schedule. Add `--notify-only` to disable automatic release acceptance; routine sync
of the existing bundle still runs.

For a Codex/Kiro/Grok skills-only selection, use
`--profile .meta/install-profiles/codex-kiro-grok.json` instead of `--cli kiro`.
Ordinary updates preserve the saved selection; explicit repair can adopt recognized
existing agents on selected providers. New resources inside owned selected packages
are reconciled without installing unrelated catalog entries.

Codex receives `.agents/skills`, Kiro `.kiro/skills`, and Grok `.grok/skills` under
the selected home. Generated repository copies are intentional. To diagnose an
extra Crew Members row, distinguish Kiro CLI agents from KiroCrew's persistent
roster as described in [discovery and member registries](INSTALL-PROFILES.md#discovery-and-member-registries).
