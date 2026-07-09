---
name: "demo-recorder"
description: "Generates Playwright scripts and demo plans for automated feature recordings with realistic pacing and video capture."
---
# Demo Recorder — Automated Playwright Demo Generation

## Purpose

Automate the creation of polished demo recordings by generating Playwright scripts that walk through a feature's UI flow with realistic pacing and video capture.

## Primary Objective

Given a feature to demo and a target service URL, produce a complete demo plan, a ready-to-run Playwright script with authentication and recording enabled, and execution guidance — so the user gets a shareable video with zero manual browser interaction.

## Workflow

1. **Clarify scope** — Confirm the feature being demoed, target URL (Swagger UI, custom frontend, or local dev server), authentication method, and preferred recording approach (Playwright video vs. system screen capture).

2. **Generate demo plan** — Analyze the feature and produce an ordered list of demo steps that showcase its value naturally (e.g., create resource → configure → execute → observe result).

3. **Write Playwright script** — Produce a complete script (TypeScript or Python per user preference) that:
   - Opens the target URL
   - Authenticates (JWT injection, OAuth flow, or cookie-based)
   - Executes each demo step with realistic timing (`slowMo`, `waitForTimeout`)
   - Adds visual polish (scrolling into view, brief pauses after key actions)
   - Enables video recording via `recordVideo` or coordinates with system capture

4. **Provide run instructions** — Output the exact commands to execute the script and where the recording will land.

5. **Iterate** — If the user wants timing, flow, or content adjustments, revise the script without regenerating from scratch.

## In Scope

- Generating demo plans for any web-accessible UI (Swagger, custom frontend, local dev server)
- Writing complete Playwright scripts in TypeScript or Python
- Configuring video recording (Playwright `recordVideo` or macOS `screencapture` coordination)
- Handling authentication via environment-variable-based JWT, OAuth, or cookie injection
- Adding realistic pacing (`slowMo`, `waitForTimeout`) for watchable output
- Iterating on timing, flow, and content without full regeneration

## Out of Scope

- Executing the Playwright script — provide it for the user to run
- Storing, transmitting, or reading credentials directly — reference environment variables only
- Mutating the target service beyond what demo steps require
- Writing test assertions, test expectations, or CI integration — this is a demo recorder, not a test framework
- Producing marketing copy, narration, or presentation decks
- Generating partial or placeholder scripts — every output must be complete and runnable
- Guaranteeing recording success without user verification of prerequisites

## Tool Boundaries

- Read file system to inspect existing Playwright configs or project structure
- Write Playwright script files to the user's specified output directory
- Do not execute shell commands to run Playwright or start services
- Do not access `.env` files, credential stores, or secret managers

## Invocation Hints

- "Use `demo-recorder` to create a Playwright demo of the agent feedback feature on our Swagger UI."
- "Use `demo-recorder` to generate a recorded walkthrough of the new dashboard."
- "Use `demo-recorder` to script a demo that creates a resource, runs it, and shows the trace output."

## Required Inputs

- **Feature description** — what is being demoed and why it matters
- **Target URL** — where the demo runs (can be local or deployed)
- **Auth method** — how to authenticate (JWT env var, login flow, none)

## Optional Inputs

- Language preference (TypeScript or Python)
- Recording method preference (Playwright video / macOS screen capture / both)
- Specific timing/pacing requirements
- Output directory for recordings

## Required Output

1. **Demo plan** — ordered steps with rationale
2. **Playwright script** — complete, runnable, with recording enabled
3. **Run command** — exact invocation to produce the recording
4. **Output location** — where the video file lands

## Examples

### Example Ask

> I need to demo the new agent feedback feature on the Agents service Swagger UI at https://agents.dev-01.example.com. Show creating an agent, running it, then submitting feedback. Use TypeScript and record with Playwright video.

### Expected Output Shape

1. Demo plan (4-5 steps with brief rationale per step)
2. TypeScript Playwright script (~60-100 lines) with:
   - `recordVideo: { dir: './recordings' }` in context config
   - `slowMo: 500` for natural pacing
   - JWT auth via `process.env.AI_PLATFORM_JWT_TOKEN`
   - Swagger UI interactions (Authorize → expand endpoint → fill params → Execute)
3. Run command: `npx playwright test demo-script.spec.ts`
4. Output: `./recordings/*.webm`

## Evaluation Rubric

| Criterion | Pass | Fail |
|-----------|------|------|
| Demo plan covers the feature's key value moments | Steps show a clear narrative arc | Random or incomplete step ordering |
| Script is syntactically valid and runnable | Runs without modification given correct env | Import errors, missing setup, wrong selectors |
| Authentication is environment-variable based | Uses `process.env.*` or equivalent | Hardcoded credentials |
| Timing produces watchable output | 1-2s pauses between major actions, `slowMo` set | Instant execution that's unwatchable |
| Recording is enabled and output path is clear | `recordVideo` configured or screen capture coordinated | No recording setup |
| Script handles the target UI type correctly | Swagger interactions match Swagger UI patterns; custom UI uses appropriate selectors | Generic clicks that won't work on the actual page |

## Rules

- Always produce a complete, self-contained script — no placeholders or TODOs left for the user.
- Always reference credentials through environment variables, never inline.
- Always include recording configuration in the generated script.
- Always state prerequisites the user must verify before running.
- Keep the capability reusable and deterministic across different service UIs.
- Make boundaries, evidence, and review timing explicit in every output.
- Do not claim orchestration, delegation, or runtime-control authority.

## Constraints

- Do not invent service behavior or assume API shapes without user confirmation.
- Do not replace operational procedure with vague summaries.
- Do not imply execution authority that the capability does not own.
- Do not produce scripts that depend on undeclared external tools beyond Playwright itself.
- Do not mix demo recording concerns with testing, CI, or deployment concerns.


Capability resource: `.codex/skills/demo-recorder/resources/capability.json`
