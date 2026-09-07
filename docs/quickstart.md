# Core-Prompts Quickstart — Reviewed Home Installation

Start with [Getting Started](GETTING-STARTED.md) for capability selection and
[Installation Profiles](INSTALL-PROFILES.md) for the canonical installation procedure.
The selected Codex/Kiro/Grok profile installs skills; agent registrations are a
separate deployment surface. A file count alone does not establish installation.

## A prompt for your local agent

```text
Install Core-Prompts using its documented installation profile on this machine.
Inspect the repository instructions and docs/INSTALL-PROFILES.md first. Verify
repository identity, branch, dirty state, and remote main parity. Preserve local
changes; do not blindly pull into an existing checkout.

Resolve the supported harnesses and intended home target. Preview the profile in
a disposable target as documented. For the real home, pass an explicit --target
and --allow-nonlocal-target; the install wrapper otherwise targets the repository.
Create and review the exact dry-run plan before applying it. Stop on unknown
ownership, customization, or outdated standalone-bundle blockers; diagnose them
without overwriting or automatically adopting existing packages.

Use ssot/ as canonical source and the generated harness directories as outputs.
Do not use legacy skills/ or clis/ directories as the source. Do not require an
unrelated repository or secrets file merely to inspect or install these skills.

Verify the saved profile, ownership receipt, selected package hashes, installed
version and a fresh zero-action sync plan. Report each selected harness separately.
Distinguish files installed, CLI discovery, agent registration and authenticated
runtime acceptance. A directory count or successful copy is not proof of all four.
Preserve unrelated home files. Report blockers and partial results explicitly.
```

## Explicit home target

For an already prepared, compatible source bundle and home ownership state:

```bash
python3 scripts/deploy-profile.py --repo "$PWD" --target "$HOME" \
  --profile .meta/install-profiles/codex-kiro-grok.json --dry-run > /tmp/core-prompts-home-plan.json
```

Review the plan using [Installation Profiles](INSTALL-PROFILES.md) before applying
it. Initial adoption may require a separately reviewed standalone-bundle refresh;
a blocked plan is not permission to overwrite local customizations. A disposable
skills-only preview is not full updater enrollment: the installed-version and
zero-action sync acceptance checks apply after the prepared runtime bundle and
home profile have both been installed.

Codex receives `.agents/skills`, Kiro `.kiro/skills`, and Grok `.grok/skills` under
the selected home. Generated repository copies are intentional. To diagnose an
extra Crew Members row, distinguish Kiro CLI agents from KiroCrew's persistent
roster as described in [discovery and member registries](INSTALL-PROFILES.md#discovery-and-member-registries).
