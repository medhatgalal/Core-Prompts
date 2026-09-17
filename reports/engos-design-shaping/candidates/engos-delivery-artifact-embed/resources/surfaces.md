# Surface capability and house-style contract

| Target | Preferred route | Required observation |
| --- | --- | --- |
| Mermaid-enabled HTML | Mermaid fences and full Markdown tables | Built target shows all SVG diagrams and complete readable tables |
| GitHub PR / GitLab MR | Native Mermaid plus Markdown | Actual description renderer/version supports it; current description retains full content |
| Google Doc | Mermaid PNGs in DOCX, converted/imported to native Doc | Saved native document has every inline image and native table; pixels inspected |
| Wiki / Confluence | Native Mermaid macro if enabled, otherwise attachment | Macro capability or attachment placement verified on saved page |
| Chat | Native renderer if available, otherwise allowed image reference | Actual message rendering and full table coverage verified |

## Google Docs style supplied by the user

Title 18 pt; H1 13 pt; H2 11.5 pt. Use bold and role-consistent color to carry
hierarchy, not decorative underlines. Body 11 pt is a proposed readable default.
No exact brand hex was supplied for headings: use the target's approved palette
when available and record the selected fallback. Keep full table rows, sensible
column widths and captions beside images. Render at the target content width.

## Known failure history and decision rail

The supplied failure report says `--upload-file` was blocked, public Drive sharing
returned `publishOutNotPermitted`, and a Chrome click method did not operate the
page. These are historical environment observations. They do not justify
bypassing access controls or blindly calling a nonexistent `sky_click` API.

Inspect current CLI/schema help once; use supported `--upload`. Keep sharing
private. Prefer native document conversion with embedded image bytes over making
a Drive PNG public. For existing-doc insertion, validate the upstream temporary
DOCX/image-URI route and its readback before relying on it. If an actual policy
denies an operation, report its exact scope and stop that operation rather than
switching tools to evade it. A syntax compatibility issue is different from a
policy denial; record which was observed.

Supported browser actions vary by host. Use the documented runtime; verify the
resulting page state. A failed semantic click calls for inspection of visible
state and a supported alternate interaction, not unbounded click retries.

## Extension point

Each new surface supplies capability detection, lossless representation mapping,
write authority/account identity, placement operation, saved-content comparison,
pixel check and failure/human-step receipt. It cannot modify the core artifact
semantics or reduce a gate. One extra adapter does not require a new shaper.
