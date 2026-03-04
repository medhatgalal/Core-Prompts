# Universal Agentic Compiler (UAC) v0.6
## System Specification: The 2026 Uplift Engine & Abstraction Hierarchy

**Status:** Final, Standalone Specification  
**Target:** Production Build via GSD  
**Location:** `~/Desktop/Core-Prompts/docs/uac/UAC_SPEC_V0.6.md`

---

### I. System Overview
The UAC is an LLM-native compiler. It solves the problem of "legacy prompt bloat" by acting as an automated factory. It ingests legacy internet slop, strips it of hallucinations, rigorously restructures it, and outputs highly deterministic, platform-specific code.

---

### II. The Core AI Abstraction Hierarchy (Routing Logic)
The system MUST route every ingested intent into the correct architectural vessel:

*   **Command (`.toml` / Alias):** Use for UI shortcuts and repeatable workflow triggers. Contains no complex reasoning; simply sets the stage.
*   **Skill (`SKILL.md`):** Use for nuanced, interactive tasks requiring human collaboration, turn-taking, and standard operating procedures (SOPs).
*   **Agent (Sub-agent):** Use for massive, asynchronous tasks. Requires an isolated context window, autonomous tool loops, and deep focus.
*   **Extension (MCP / Plugin):** Use when the intent requires connecting to a secure external API (Jira, DB) or executing local system binaries.

---

### III. The 2026 Uplift Engine (The Transformation Core)
The UAC intercepts raw intent and forces it through the 2026 Agent Specification framework. Every compiled artifact MUST contain:

1.  **Context Layer:** Defines exactly what memory the agent can trust and what explicit files are required.
2.  **Intent Layer:** Replaces vague descriptions with strict Goals and Trade-offs (e.g., "Safety over Speed").
3.  **Task Decomposition:** Forces the breaking of intent into verifiably independent sub-tasks.
4.  **Constraint Architecture:** Injects strict boundary conditions (`MUST`, `MUST NOT`, `ESCALATE`).
5.  **Acceptance Criteria:** Injects a deterministic verification step (JSON schema or state mutation).

---

### IV. The 7-Stage Execution Pipeline

1.  **Ingestion & Two-Pass Sanitization:** 
    - Gate 1: Strip structural overrides.
    - Gate 2: Extract core intent, ignoring roleplay "jailbreak" fluff.
2.  **The 2026 Uplift Pass:** Generates the constrained, platform-agnostic AST.
3.  **Semantic Routing & Convergence:** Merges redundant concepts and selects the target vessel.
4.  **Target Tool Validation:** Validates AST against CLI tools. Performs **Fallback Degradation** (Agent -> Skill) if tools are missing.
5.  **Dialect Translation (The Rosetta Stone):** Maps abstract capabilities to specific CLI tools using `cli_tool_matrix.yaml`.
6.  **Clean Verification (Mock Execution):** Simulates an internal execution loop to ensure syntactical and logical validity.
7.  **Output Generation & Help Injection:** Writes files using AST-level merging. Appends a standard `[Help Module]` and **Runtime Dependency Checks** to every artifact.

---

### V. Reference Materials
- **Logic SSOT:** `system/uac/uac-agent.md`
- **Tool Mapping:** `system/uac/cli_tool_matrix.yaml`
