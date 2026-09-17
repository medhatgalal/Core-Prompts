---
name: "engos-delivery-artifact-embed"
description: "Place an authored shaping-artifact bundle onto a selected HTML, PR/MR, chat, Google Doc, or wiki surface through explicit adapters. Use Mermaid/Markdown passthrough where native rendering exists and fail loudly with a named human step when a surface cannot prove placement."
display_name: "Shaping Artifact Embed — Surface Adapters and Placement Evidence"
kind: "workflow"
capability_type: "skill"
version: "v1.0"
---
# Shaping Artifact Embed — Surface Adapters and Placement Evidence

## Purpose

Place a completed shaping-artifact bundle on the surface where the pitch lives
without changing the artifact's meaning. The durable input is the Mermaid
source, contract table, security-owner matrix, evidence ledger, and manifest
from `engos-delivery-diagram-contract-artifacts`. This skill selects a thin
surface adapter, preserves source identity, and returns placement evidence. It
does not author architecture, judge a pitch, or treat an attempted upload as a
successful embed.

## Primary Objective

Make surface choice and placement deterministic: use native Mermaid/Markdown
when available, use a render-and-place path only when required, and stop with a
specific human action when environment constraints prevent verified placement.

## Invocation Hints

Use when a user asks to put shaping diagrams and contract tables into a docs
site, Google Doc, wiki/Confluence page, PR/MR description, or review chat. Ask
for the target surface only when it is not present in the pitch context. Do not
ask the user to pick a rendering technology when the target has a documented
native path.

## Required Inputs

- a complete authored artifact bundle and manifest
- one target surface: `html`, `github_pr`, `gitlab_mr`, `chat`, `google_doc`,
  or `wiki`
- target identity and write authorization when the surface is external
- renderer capability and placement evidence available in the current runtime

## Required Output

Return a placement receipt:

```text
surface: <surface>
artifact_id: <stable id>
adapter: <adapter name>
representation: mermaid_markdown | rendered_image_plus_markdown | native_table
source_hash: <hash or stable source reference>
placement_status: placed | passthrough | blocked | human_step_required
verified_by: <observable page/file/revision or explicit human step>
changed_meaning: false
blockers: []
```

For `blocked` or `human_step_required`, name the exact missing permission,
runtime capability, or human action. Do not report `placed` from a successful
file upload, a zero exit code, or a stale page view alone.

## Adapter Matrix

| Surface | Diagram representation | Contract/security representation | Placement rule |
| --- | --- | --- | --- |
| HTML docs site | Mermaid fenced blocks | Markdown tables | Passthrough; verify the built page renders the diagrams and tables |
| GitHub PR / GitLab MR | Mermaid fenced blocks | Markdown tables | Passthrough; verify the exact description revision |
| Chat / review | Mermaid or embedded image reference | Markdown/inline table | Prefer Mermaid/text; verify the sent message if sending is authorized |
| Google Doc | Rendered PNG/SVG inserted inline | Native Docs tables plus source link/hash | Render, upload through the supported path, insert, then read back; never rely on a public URL assumption |
| Wiki / Confluence | Native Mermaid macro when supported, otherwise attachment | Native table | Detect the page capability, choose one path, and verify the saved page |

## Workflow

1. Validate the input manifest and source hash. Refuse incomplete bundles unless
   the caller explicitly requests a diagnostic receipt.
2. Detect the target surface and its native diagram/table capabilities. Keep
   the core bundle unchanged.
3. For HTML, PR/MR, and chat, emit the same Mermaid fences and Markdown tables
   as a passthrough adapter. No image hosting step is needed.
4. For Google Docs, render Mermaid to an image only at the adapter boundary.
   Use the environment-supported Drive upload form (`--upload`, not a blocked
   `--upload-file` form when the runtime exposes that distinction), retain the
   source link/hash, use a supported insertion mechanism, and read back the
   saved document revision. `insertInlineImage` behavior that requires a
   public URL is not a valid fallback when corporate Drive sharing blocks
   public publication; report `human_step_required` if no supported insertion
   path is available.
5. For a wiki, probe the documented native macro or attachment path once. If
   capability detection is unavailable, return a blocker rather than trying
   undocumented APIs.
6. Verify the resulting surface: Mermaid is rendered rather than shown as
   broken source where native rendering is promised; tables retain all rows;
   source identity is recoverable; and the page/file revision is current.
7. Return the placement receipt and preserve any blockers in the evidence
   ledger. Never silently downgrade a failed image placement to an untracked
   text-only result.

## Rules

- The artifact source is authoritative; surface formatting is an adapter.
- Prefer zero-hosting Mermaid passthrough when the target supports it.
- Rendered images are derived and must carry a source identity.
- Never make a document public merely to unblock image insertion.
- Never transmit a pitch or personal file to an external target without the
  caller's explicit authorization for that target.
- A human step is an honest result when the environment blocks a verified
  adapter; it is not a failure to hide.
- Keep placement evidence separate from authoring and review evidence.
- Do not create Jira tickets, implementation code, or a native agent surface.

## Constraints

- The adapter must not rewrite component names, contract states, owners, or
  evidence claims.
- Google Docs placement is not considered complete until the saved revision is
  read back and the image/table is observable there.
- Public Drive sharing is never a required prerequisite for a private Google
  Doc. If the only available image insertion path requires a public URL, stop
  and name the human or platform-level unblock.
- External write actions require target-specific authorization and should be
  prepared as a dry-run receipt before execution.

## Examples

### Example Request

> Put the authored shaping artifact bundle into the HTML docs site and the
> Google Doc. Use Mermaid in the site. For the Doc, use the supported private
> image path and tell me exactly what remains human-owned if this environment
> cannot verify insertion.

### Example Output Shape

- HTML receipt: `passthrough`, exact page/revision, source hash
- Google Doc receipt: `placed` with saved revision readback, or
  `human_step_required` with the public-URL/upload blocker named
- unchanged-source assertion
- visual verification notes

## Evaluation Rubric

| Check | What Passing Looks Like |
| --- | --- |
| Adapter selection | Target surface determines the adapter; no hardcoded Google-Doc path |
| Source preservation | Source hash and semantic content remain unchanged |
| Native-path preference | Mermaid/Markdown targets avoid unnecessary image hosting |
| Placement proof | Receipt names an observable saved page/file/revision or a precise human step |
| Failure honesty | Upload, public-sharing, click, or renderer blockers are explicit and fail closed |
| Security boundary | No public sharing or external transmission is performed implicitly |
| Extensibility | Adding a surface requires one adapter entry and its verification contract |
