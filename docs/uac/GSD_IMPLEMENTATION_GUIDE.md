# GSD Implementation Guide: Universal Agentic Compiler (UAC)

This guide provides the exact sequence of steps to build the UAC system in this repository using the **Get Shit Done (GSD)** framework.

---

## 1. Environment Initialization
Navigate to the root of this repository and initialize the GSD project state.

```bash
cd ~/Desktop/Core-Prompts

# Map existing prompts and UAC spec files
/gsd:map-codebase

# Initialize the project lifecycle
/gsd:new-project
```

## 2. Setting the Architect's Intent
When GSD asks what you are building, use this exact prompt to ensure it sticks to the v0.6 specification and avoids "hallucinated simplification."

### The Intent Prompt:
> Build the Universal Agentic Compiler (UAC) v0.6 as a production system.
> 
> **PRIMARY SOURCE:**
> - Specification: `docs/uac/UAC_SPEC_V0.6.md`
> - Logic Engine: `system/uac/uac-agent.md`
> - Tool Mapping: `system/uac/cli_tool_matrix.yaml`
> 
> **CORE REQUIREMENTS:**
> 1. Implement the 7-stage compilation pipeline exactly as defined in the Spec.
> 2. The system must be 100% portable and self-contained.
> 3. Every compiled artifact MUST include the [Help Module] and Runtime Dependency Checks.
> 4. Updates to agents MUST use AST-level deterministic merging (JSON/YAML) to prevent markdown drift.
> 
> **PHASE 1 FOCUS:**
> Establish the CLI scaffold and Stage 1 (Two-Pass Sanitization) logic. The tool should be able to ingest one local file and output a clean, roleplay-free Intent Summary.

---

## 3. The Execution Sequence
Follow this order of operations to ensure logical integrity. **Do not skip phases.**

| Phase | Command | Success Criteria |
| :--- | :--- | :--- |
| **1. The Scaffold** | `/gsd:plan-phase 1` | CLI can ingest a file and run the "Sanitization Sub-routine." |
| **2. The Brain** | `/gsd:plan-phase 2` | 2026 Uplift Engine logic is implemented (Context/Intent layers). |
| **3. The Rosetta** | `/gsd:plan-phase 3` | Rosetta Stone integration; translates actions to CLI-specific tools. |
| **4. The Safety** | `/gsd:plan-phase 4` | Mock Execution loop and AST-level merging are functional. |
| **5. Portability** | `/gsd:plan-phase 5` | Help Module and Dependency Check injectors are active. |

---

## 4. Operational Best Practices
- **Validation:** After each phase, run `/gsd:progress` to ensure the "Current State" matches your expectations.
- **Drift Control:** If GSD proposes a simplified architecture, use `supercharge /constrain` to force it back to the detail density of the v0.6 Spec.
- **Handoffs:** If you close the chat, run `supercharge /catchup` when you return to get a forensic table of what is done vs. what is blocked.
