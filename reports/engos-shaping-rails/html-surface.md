# HTML Docs Surface Receipt

Artifact: `pm-query-lib-architecture-2026-09-17`

Adapter: `mermaid-markdown-passthrough`

Status: `passthrough`

The HTML/Markdown surface consumes the same source bundle without image
hosting. The rendered page is represented by
`reports/engos-shaping-rails/html-surface.html`; its Mermaid blocks and tables
are sourced from `exercise-source/` without semantic edits.

## Architecture Diagram

```mermaid
%% source: exercise-source/component.mmd
flowchart TB
  subgraph LCP["LCP / AE site"]
    PHQ["ProcessHQ UI<br/>browser-facing"]
    GATE["ProcessMiningGatingService<br/>resolve and gate"]
    CLIENT["AdsProcessMiningClientService<br/>feature-toggle route"]
    LIB["pm-query-lib<br/>in-process Kotlin library"]
  end
  DC["ADS Data Client<br/>shared gRPC client"]
  ADS["ADS<br/>DuckDB query and storage"]
  USER["User / browser"]
  USER -->|"HTTPS + session + CSRF"| PHQ
  PHQ -->|"REST request"| GATE
  GATE -->|"authorized appianId -> logUuid"| CLIENT
  CLIENT -->|"in-process call"| LIB
  LIB -->|"SQL via DataClient"| DC
  DC -->|"gRPC :5450+"| ADS
```

## Request Sequence

```mermaid
%% source: exercise-source/sequence.mmd
sequenceDiagram
  participant U as User
  participant PHQ as ProcessHQ UI
  participant GATE as Gating service
  participant LCP as LCP client
  participant LIB as pm-query-lib
  participant ADS as ADS
  U->>PHQ: Explore process data
  PHQ->>GATE: POST request with appianId
  GATE->>GATE: Resolve and authorize appianId -> logUuid
  alt authorized
    GATE->>LCP: Route request
    LCP->>LIB: aggregate / discover / explore
    LIB->>ADS: Query through Data Client over gRPC
    ADS-->>LIB: Result rows
    LIB-->>LCP: Structured response
    LCP-->>PHQ: JSON response
    PHQ-->>U: Rendered insight
  else unauthorized or invalid
    GATE-->>PHQ: Rejected request
    PHQ-->>U: Safe error response
  end
```

## Contract and security tables

See [contracts](exercise-source/contracts.md) and
[security owners](exercise-source/security-owners.md). Their rows are included
unchanged in the HTML build fixture.

## Receipt

```text
source_hash: computed from exercise-source/manifest.json and referenced files
representation: mermaid_markdown + markdown_tables
placement_status: passthrough
verified_by: local rendered HTML screenshot and DOM assertions
changed_meaning: false
```
