# Core-Prompts Quickstart — One Prompt, Full Install

> **How to use:** Open a terminal anywhere. Run `kiro-cli chat -a`.
> Paste the prompt below. Kiro clones, installs skills across all your
> AI CLIs, and verifies everything works.

---

## The Prompt

```
You are installing Core-Prompts (skills and agents for AI CLIs) on this machine.
Follow every step in order. If any step fails, diagnose the root cause, give me
the exact fix, wait for confirmation, then retry. Do not skip or defer.

## Phase 1: Prerequisites Check

Before installing Core-Prompts, verify:
1. Does ~/Desktop/dotfiles exist and is it installed?
   - Check: ls ~/.secrets.env && which kiro-cli
   - If either fails: STOP and say "Install dotfiles first. See ~/Desktop/dotfiles/docs/quickstart.md"
2. Is git available? git --version

## Phase 2: Clone Core-Prompts

Check: does ~/Desktop/Core-Prompts exist?
- If yes: cd ~/Desktop/Core-Prompts && git pull (get latest)
- If no: give me the exact git clone command and wait for confirmation

## Phase 3: Inspect Before Installing

cd ~/Desktop/Core-Prompts
1. Check: ls scripts/install-local.sh (must exist)
2. Check: is it executable? If not: chmod +x scripts/install-local.sh
3. Show me what CLIs this will install to (read the script header or --help)
4. Count current skills: ls ~/.kiro/skills/ 2>/dev/null | wc -l

## Phase 4: Install

Run: scripts/install-local.sh --cli all

This installs skills and agents to:
- ~/.kiro/skills/ (Kiro)
- ~/.claude/ (Claude, if available)
- ~/.gemini/ (Gemini, if available)
- ~/.codex/ (Codex, if available)

If the script fails:
- Permission error: chmod +x scripts/install-local.sh && retry
- Missing dependency: identify what's needed and tell me the install command
- Partial install: note which CLI surfaces failed and continue with the rest

## Phase 5: Verify Skills Installed

Check each surface:
1. ls ~/.kiro/skills/ | wc -l (must be > 10, expect ~20+)
2. ls ~/.kiro/skills/ | head -10 (show me some skill names)
3. ls ~/.claude/skills/ 2>/dev/null | wc -l (optional — 0 is OK if Claude not used)
4. ls ~/.gemini/ 2>/dev/null | wc -l (optional)

## Phase 6: Verify Key Skills Work

Test that critical skills are reachable:
1. ls ~/.kiro/skills/code-review/ (must exist)
2. ls ~/.kiro/skills/supercharge/ (must exist)
3. ls ~/.kiro/skills/mentor/ (must exist)
4. For each: confirm SKILL.md file exists inside

If any critical skill is missing:
- Re-run: scripts/install-local.sh --cli kiro
- If still missing: check if the skill source exists in the repo
  ls skills/ or ls capabilities/ and tell me what's there

## Phase 7: Verify Agents (if applicable)

Check: ls ~/.kiro/agents/ 2>/dev/null | wc -l
- If agents directory exists with content: list them
- If empty or missing: that may be expected for your version — note it

## Phase 8: Final Confirmation

Run these checks:
1. Skill count: ls ~/.kiro/skills/ | wc -l (should be 15+)
2. No broken symlinks: find ~/.kiro/skills/ -type l ! -exec test -e {} \; -print (should be empty)
3. Key skills present: ls ~/.kiro/skills/{code-review,supercharge,mentor,auto-research}/SKILL.md

If ALL pass: report "✓ Core-Prompts fully installed — N skills across M CLI surfaces"
If any fail: diagnose and fix (go back to Phase 4)

## Rules
- The install order is: dotfiles FIRST, then Core-Prompts, then EngOS.
- If dotfiles is not installed, stop and redirect there first.
- Never guess at skill paths — read the installer output.
- Give exact commands, not descriptions.
- If you need my input (repo URLs, which CLIs to target), ask and wait.
```

---

## Launch

```bash
kiro-cli chat -a
# paste the prompt above
```

---

## After This

Once Core-Prompts is installed, you can install EngOS in any target repo:
- See: https://gitlab.appian-stratus.com/medhat.galal/EngOS/-/blob/main/docs/getting-started/quickstart.md
