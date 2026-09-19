# Discover repository context at runtime

Use this resource only when Research needs repository evidence. Repository context
comes from the project in which the shaping workflow is running or from locations
the user explicitly supplies. Never encode a product repository, sibling checkout,
module name or organization-specific path as a skill default.

## Establish the boundary

1. Resolve the current repository/workspace root and revision without switching
   branches or fetching. Read applicable repo-local instructions and relevant
   workspace metadata, manifests, project indexes and architecture/knowledge files.
2. If there is one clear project root and the accepted question identifies the
   capability, inspect the smallest relevant scope directly. Do not ask the user
   to repeat facts already available from the workspace.
3. Ask which folders or modules are relevant only when multiple roots are plausible,
   the monorepo scope is materially broad, or the requested capability cannot be
   located safely. Offer the likely choices and explain what the selection changes.
4. Do not scan outside the current repository/workspace, assume sibling repositories,
   or turn a discovered path into a reusable skill convention. Additional roots
   require an explicit supplied location or a separately authorized discovery step.

## Choose the cheapest sufficient inspection capability

Use available capabilities in this order when they can answer the assigned question:

1. Repo-local project knowledge, architecture indexes or maintained system maps.
2. An active language server or equivalent semantic index for definition,
   references, implementations, call hierarchy and type-aware symbol search.
3. Host-native indexed code search, repository search or approved knowledge tool.
4. Bounded file/text search such as `rg`, followed by opening enough surrounding
   callers, tests, configuration and contracts to understand the result.
5. A human-evidence request when required sources or capabilities are unavailable.

Capability names vary by host. Detect what is actually available; do not require
an LSP, start a new server, install an indexer or claim semantic coverage from text
search. A fast index result still needs source/revision binding and relevant context.

## Record coverage

Record repository/workspace identity, revision and dirty-state limits; selected
roots/modules; instructions and indexes consulted; search capability used; queries
or symbols; paths and lines opened; callers/tests/configuration covered; excluded
scope; no-hit meaning; and the smallest next evidence request. Keep this in the
existing research evidence record rather than creating a second repository tracker.

No repository is required for document-only shaping. When repository evidence is
not material, record why code inspection is not applicable and continue with the
appropriate documents or human evidence.
