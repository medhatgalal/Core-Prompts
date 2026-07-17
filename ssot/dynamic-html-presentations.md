---
name: "dynamic-html-presentations"
display_name: "Dynamic HTML Presentations"
description: "Creates polished, responsive, standalone HTML slide decks with optional deterministic PNG and image-faithful PPTX export. Use for presentations, pitch decks, reviews, talks, and visual narratives that need browser-native interactivity and portable outputs."
capability_type: "skill"
install_target: "global"
compatibility: "HTML works in modern browsers; bundled PNG exporter requires macOS 13+; PPTX helper requires Python 3.9+."
---

# Dynamic HTML Presentations

## Purpose
Use this capability to turn a topic, source material, or rough outline into a polished presentation whose canonical artifact is a standalone HTML file. It is appropriate for executive reviews, technical talks, product updates, proposals, training, and other visual narratives where strong formatting, browser-native interaction, portability, and optional PNG or PPTX delivery matter.

## Primary Objective
Create a coherent, visually rigorous deck that communicates one clear narrative, works interactively as a self-contained 16:9 HTML presentation, and can be exported predictably to exact-size PNG images and a visually faithful image-only PPTX when requested.

## Start With the Output Choice
Before building, identify the requested delivery format. If the user has not specified it, ask one concise question and offer exactly these choices:

1. **Interactive HTML only** — editable source, keyboard navigation, deep links, fullscreen, and presenter notes.
2. **PNG images** — one deterministic image per slide, normally 1920×1080.
3. **PPTX** — a widescreen, image-only PowerPoint assembled from the PNGs.
4. **All formats** — HTML as the source of truth, then PNG, then PPTX.

Do not ask again when the request already names a format. If the user cannot decide, recommend HTML plus PNG for portability, or all formats when a conventional presentation file is a delivery requirement. Explain that the bundled PPTX workflow preserves appearance exactly but does not make individual slide elements editable.

## Output Directory
Honor a user-specified destination. Otherwise create one descriptive deck directory:

```text
<deck-slug>/
├── index.html
├── slides/
│   ├── slide-01.png
│   └── ...
└── <deck-slug>.pptx
```

Only create `slides/` and the PPTX when those formats were requested. Keep source notes or research beside the deck only when the user asks for them.

## Discovery Inputs
Gather only information that materially changes the deck. Use existing context instead of interrogating the user.

- audience and decision or behavior the deck should drive
- presentation length or target slide count
- core narrative and required sections
- evidence, metrics, quotes, diagrams, and source citations
- brand constraints, tone, colors, and logo policy
- whether claims are factual, illustrative, or placeholders
- speaker-note expectations
- delivery format and target viewport
- appendix needs and confidentiality constraints

When evidence is incomplete, label assumptions and illustrative values explicitly. Never invent a source, quotation, customer claim, or measured result.

## Workflow
1. **Set the contract.** Confirm audience, purpose, delivery format, approximate slide count, and hard constraints.
2. **Build the story before the layout.** Write a one-line claim for each slide and arrange the claims into context → evidence → implication → decision or action. Put supporting detail in an appendix rather than weakening the main narrative.
3. **Choose a visual grammar.** Define CSS variables, typography, spacing, semantic colors, card styles, diagram shapes, table rules, and footer behavior once.
4. **Author the standalone HTML.** Use semantic slide sections, inline CSS and JavaScript, local or inline assets, keyboard controls, hash routing, fullscreen, notes, and export mode.
5. **Make evidence visual.** Prefer charts, proportional bars, flows, matrices, timelines, annotated diagrams, and metric cards over paragraphs. Put caveats beside the evidence they qualify.
6. **Validate the live DOM at the target viewport.** Check slide state, clipping, collisions, required wording, console errors, and interactive controls before trusting screenshots.
7. **Export only when requested.** Produce PNGs in one browser process, verify every image, then build PPTX from the verified PNGs.
8. **Review as a presentation.** Read the deck end to end for narrative continuity, visual rhythm, accessible contrast, and a clear final action.
9. **Report artifacts and evidence.** Return exact output paths, formats created, validation performed, limitations, and any unresolved content assumptions.

## Narrative and Slide Design Rules
- One principal claim per slide. A title should state the point, not merely the topic.
- Use a repeatable hierarchy: eyebrow or section label, optional time badge, headline, primary visual or evidence, implication, and caveat/footer.
- Keep the main narrative short enough to present. Move deep methodology, backup tables, and edge cases to an appendix.
- Alternate visual density deliberately. Follow a dense evidence slide with a simpler implication, quote, or decision slide.
- Prefer a few large elements over many small ones. Do not shrink text to rescue an overloaded slide; simplify the slide.
- Use exact proportional geometry for ratio claims. A 70/30 claim should render as 70% and 30%, not as visually equal boxes.
- Distinguish observed facts, targets, forecasts, and illustrative values through labels and color semantics.
- Keep claim, source, caveat, and time period close enough to be understood together.
- Reuse card, metric, grid, flow, quote, callout, table, and timeline components rather than styling each slide ad hoc.
- Use restrained color roles: neutral canvas, one primary accent, one secondary accent, and explicit success/warning/risk colors.
- Avoid decorative gradients, shadows, or animation that compete with the story. Motion should clarify slide entry or focus and must be disabled for export.
- Preserve whitespace. Never solve hierarchy by filling every available area.

## HTML Architecture
Create one portable HTML file unless the user explicitly approves external assets. Inline CSS and JavaScript. Inline small SVG diagrams. Embed images as data URIs or keep them in a user-approved local asset directory when file size makes embedding unreasonable.

Use semantic slides:

```html
<section class="slide active" data-title="Opening claim" aria-hidden="false">
  <p class="eyebrow">Quarterly review</p>
  <h1>A decision-oriented headline</h1>
  <div class="visual">...</div>
  <aside class="speaker-note" hidden>...</aside>
</section>
```

The runtime must maintain exactly one active slide during normal viewing. Implement:

- Arrow Right, Arrow Left, Space, Page Up, Page Down, Home, and End
- hash deep links such as `#slide-3`
- visible next/previous controls that do not cover slide content
- current slide number and progress indicator
- fullscreen toggle
- presenter-notes toggle
- help toggle
- optional appendix jump when appendix slides exist
- `aria-hidden` state updates and accessible button labels

Keep presentation state in a small, readable script. Do not add a framework for a single-file deck.

## Fixed 16:9 Visual System
Design against a 16:9 stage. The default export target is 1920×1080, but layout should scale down without changing composition.

```css
:root {
  --canvas: #f5f7fb;
  --ink: #172033;
  --muted: #5e6b82;
  --accent: #2457d6;
  --accent-2: #00a6a6;
  --safe-x: clamp(32px, 5vw, 96px);
  --safe-y: clamp(28px, 5vh, 64px);
}
.deck {
  width: min(100vw, calc(100vh * 16 / 9));
  height: min(100vh, calc(100vw * 9 / 16));
  aspect-ratio: 16 / 9;
}
.slide {
  position: absolute;
  inset: 0;
  padding: var(--safe-y) var(--safe-x);
}
```

Keep important content inside a consistent safe area. Reserve space for footers and controls instead of allowing them to overlap content. Use `clamp()` for responsive type, but set sensible minimums and test the smallest supported viewport.

## Export Mode Contract
Every deck intended for export must support an explicit `?export=1` mode and an equivalent `body.export` class. Export mode must hide interface chrome and remove nondeterministic motion while leaving slide content untouched.

```css
body.export .controls,
body.export .help,
body.export .progress,
body.export .notes { display: none !important; }
body.export .slide.active { animation: none !important; }
```

Initialize export mode from the URL:

```js
const params = new URLSearchParams(location.search);
document.body.classList.toggle("export", params.get("export") === "1");
```

The interactive URL without `?export=1` must restore controls, progress, and notes behavior. Test both modes; an export stylesheet that permanently hides controls is a defect.

## Presenter Notes
Store notes with each slide in a hidden `.speaker-note` element so notes travel with the standalone file. Render the active slide's notes into a separate notes panel only when the presenter toggles it.

When the user requests notes:
- write concise speaking prompts rather than a transcript
- default to 5–7 bullets for a substantive slide
- include the claim, evidence interpretation, transition, caveat, and likely question
- do not expose hidden notes in PNG export
- keep source citations or private presenter reminders out of the visible slide unless needed by the audience

## Validation
Validate the actual page, not only the source text.

### Structural checks
- exact expected slide count
- exactly one `.slide.active` in interactive mode
- unique hash target for every slide
- every slide has a title or accessible label
- notes exist when requested
- controls are visible interactively and hidden only in export mode
- no external network dependency unless explicitly approved

### Geometry checks at 1920×1080
Activate each slide and inspect every visible element's `getBoundingClientRect()`:

- `left >= 0`, `top >= 0`, `right <= 1920`, `bottom <= 1080`
- no slide content intersects fixed controls, notes panel, or footer zones
- no unexpected horizontal or vertical scrollbars
- no clipped text, SVG labels, table rows, or footnotes
- exact proportions for quantitative visuals

A useful in-page check is:

```js
const visible = [...document.querySelectorAll(".slide.active *")]
  .filter(el => getComputedStyle(el).display !== "none" && el.getClientRects().length);
const overflow = visible.filter(el => {
  const r = el.getBoundingClientRect();
  return r.left < -0.5 || r.top < -0.5 ||
         r.right > innerWidth + 0.5 || r.bottom > innerHeight + 0.5;
});
```

Also check the browser console, required phrases, dates, units, business-context labels, citations, and caveats. A clean accessibility tree and correct DOM state are stronger evidence than a single screenshot.

## PNG Export
On macOS, prefer the bundled `resources/export_slides.swift` helper. It uses one `WKWebView`, loads the deck once, activates slides sequentially, waits for paint, takes snapshots, and writes exact-size RGBA PNGs.

```bash
swift resources/export_slides.swift \
  --input /absolute/path/to/index.html \
  --output /absolute/path/to/slides \
  --width 1920 \
  --height 1080
```

Use `--force` only when replacing existing `slide-*.png` files is intended. The exporter defaults to `.slide`, discovers the count in page JavaScript, adds `body.export`, waits briefly for native paint using the configurable settle delay, and fails on timeout or missing output.

After export verify:
- PNG count equals slide count
- filenames sort naturally (`slide-01.png`, `slide-02.png`, ...)
- every file is nonempty
- every image is exactly the requested dimensions
- several representative slides differ visually and contain their expected headline

Use native OCR or image inspection for representative content when available, but do not treat OCR as a substitute for DOM geometry checks.

### Cross-platform fallback
If Playwright or Puppeteer is already part of the environment, use one browser process and one page, set the viewport once, activate slides sequentially, and capture each slide. Do not add a browser dependency merely for convenience without telling the user. Do not spawn one Chrome process per slide; that pattern is slow, can leave orphan processes, and becomes worse when parallelized.

## PPTX Export
PPTX export depends on successful PNG export. Use the bundled `resources/images_to_pptx.py` helper with the exact pinned dependency in a temporary directory so the project environment is not modified:

```bash
DEPS="$(mktemp -d)"
python3 -m pip install --target "$DEPS" 'python-pptx==1.0.2'
PYTHONPATH="$DEPS" python3 resources/images_to_pptx.py \
  /absolute/path/to/slides \
  /absolute/path/to/deck.pptx \
  --title "Quarterly Product Review"
```

The helper refuses to overwrite an existing PPTX unless `--force` is supplied. With `--force`, it writes and verifies a temporary file in the destination directory, then atomically replaces the old PPTX. It also validates that all images have consistent 16:9 dimensions, creates a 13.333333×7.5 inch presentation, and places one image full bleed on each blank slide. Reopen the generated file programmatically and verify slide count.

State the tradeoff clearly:
- **Benefit:** visual output matches the validated PNGs.
- **Limitation:** text, diagrams, and shapes are flattened and not independently editable.

Do not promise editable PPTX conversion unless a separate native-slide authoring workflow is explicitly requested and validated.

## Optional Google Slides Delivery
Only upload when the user explicitly requests Google Slides and the local `gws` CLI is authenticated. Convert the PPTX through Drive, dry-run first, then verify the presentation:

```bash
gws drive files create --dry-run \
  --params '{"fields":"id,name,mimeType,webViewLink"}' \
  --json '{"name":"Deck Title","mimeType":"application/vnd.google-apps.presentation"}' \
  --upload /absolute/path/to/deck.pptx
```

Run the same command without `--dry-run` only after reviewing the request. Verify with `gws slides presentations get` that page size is widescreen, slide count matches, and each image-only slide has exactly one image.

For Google Slides speaker notes, use each slide's `slideProperties.notesPage.notesProperties.speakerNotesObjectId`. Insert all notes in one atomic `presentations.batchUpdate` request and read the notes pages back to verify exact text.

## Known Failure Modes and Preferred Responses
- **Stale DevTools screenshots:** a browser screenshot tool may return a stale compositor frame even when the DOM and accessibility tree show the correct active slide. Retry through a deterministic exporter and verify the output file; do not accept the stale capture as proof.
- **Hung headless Chrome processes:** repeated isolated launches, especially in parallel, can leave orphan processes or time out. Use one long-lived browser process.
- **Single-pass print-to-PDF timeouts:** do not make PDF printing the default route to PNG. Snapshot slides individually in one loaded page.
- **Square Quick Look thumbnails:** native HTML thumbnailing may choose a square viewport and distort `vw`/`vh` layouts. It is not a trusted export path.
- **Keynote automation timeouts:** AppleScript and AppleEvent automation can hang even after application startup. Treat it as a non-preferred fallback.
- **Invalid bitmap configuration:** four samples per pixel with `hasAlpha: false` is inconsistent. The macOS exporter must use RGBA: `samplesPerPixel: 4` and `hasAlpha: true`.
- **Hidden interactive controls:** export-mode rules must be scoped under `body.export`, not applied globally.
- **Overflow rescued by tiny text:** do not reduce readability to pass bounds checks; split or simplify the slide.
- **Unlabeled sample data:** mark illustrative metrics and replace them before final delivery when factual evidence is required.

## Tool Boundaries
- allowed: inspect source material, create or edit local presentation artifacts, run local HTML validation, run the bundled local exporters, and inspect generated files
- requires notice: install the pinned temporary Python dependency, introduce a new browser runtime, or use local fonts/assets that reduce portability
- requires explicit request: upload or convert a deck to Google Slides or another external service
- forbidden: transmit private source material to third parties without authorization, invent evidence, silently scrape external assets, or claim export success without checking generated files

## Rules
- Keep HTML as the canonical editable source.
- Make the user's chosen output format explicit before expensive export work.
- Use standalone inline HTML by default.
- Preserve a strict 16:9 composition and validate the actual target viewport.
- Build narrative structure before visual polish.
- Prefer visual explanation over dense prose.
- Keep evidence, time period, source, and caveat together.
- Disable animation and hide controls only in explicit export mode.
- Export all PNGs through one long-lived rendering process.
- Create PPTX only from verified PNGs.
- Label flattened PPTX output as image-only and non-editable.
- Keep examples generic and free of confidential names, internal URLs, or unsupported claims.

## Required Inputs
- topic, source material, or outline
- audience and desired outcome
- requested output: HTML, PNG, PPTX, or all
- target duration or slide count when constrained
- evidence and branding requirements when applicable
- speaker-note and appendix expectations

## Required Output
Every substantial delivery must include:
- `Narrative` — the story arc and slide-level claims
- `Artifacts` — exact paths to HTML, PNG directory, and/or PPTX
- `Interaction` — navigation, notes, fullscreen, and deep-link behavior implemented
- `Validation` — slide count, active-state, geometry, console, export-mode, and file checks actually run
- `Export Tradeoffs` — platform requirements and image-only PPTX limitation
- `Open Assumptions` — illustrative data, missing sources, or content still needing confirmation

## Bundled Resources
- `resources/example.html` — sanitized standalone five-slide quarterly product review demonstrating the visual system and interaction contract
- `resources/export_slides.swift` — macOS single-process `WKWebView` PNG exporter
- `resources/images_to_pptx.py` — natural-sort, dimension-validating image-to-PPTX helper

Use these as starting points, not as immutable templates. Replace the example narrative and adapt the design system to the user's audience and content.

## Examples
### Example Request
> Create a six-slide quarterly product review for leadership. Give me the interactive HTML, 1920×1080 PNGs, an image-faithful PPTX, and concise speaker notes. Clearly label the sample metrics as illustrative.

### Example Output Shape
- narrative: opening decision, evidence, workflow impact, risks, recommendation, appendix
- artifacts: `quarterly-review/index.html`, six files under `slides/`, and `quarterly-review.pptx`
- interaction: keyboard, hash links, fullscreen, notes, help, and appendix jump
- validation: six slides, one active slide, no 1920×1080 overflow, no console errors, six valid PNGs, six PPTX pages
- tradeoff: PPTX is visually exact but flattened
- assumptions: sample metrics remain illustrative pending source data

### Example Request: HTML Only
> Turn this technical proposal into a polished browser presentation. Keep it self-contained and do not create images or upload anything.

### Example Output Shape
- one standalone `index.html`
- no external assets or network requests
- explicit narrative and slide map
- keyboard, hash, fullscreen, notes, and export-mode support
- viewport and console validation evidence

## Completion Checklist
- [ ] User-selected output format is recorded.
- [ ] Audience, purpose, and narrative arc are clear.
- [ ] Every slide has one principal claim.
- [ ] HTML is standalone unless external assets were approved.
- [ ] Exactly one slide is active interactively.
- [ ] Keyboard, hash, controls, fullscreen, help, and notes work.
- [ ] Export mode hides chrome and disables motion without affecting normal mode.
- [ ] Every slide passes target-viewport bounds and collision checks.
- [ ] Claims, periods, sources, and caveats are adjacent.
- [ ] Illustrative data is labeled.
- [ ] PNG count, dimensions, and nonempty files are verified when requested.
- [ ] PPTX slide count is verified and non-editability is disclosed when requested.
- [ ] No confidential names, internal URLs, credentials, or unintended source content appear.
- [ ] Final response lists paths, checks, assumptions, and limitations.

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Output contract | The user receives exactly the requested HTML, PNG, PPTX, or all-formats package, with tradeoffs stated |
| Narrative quality | The deck has a decision-oriented arc and one clear claim per slide |
| Visual quality | Hierarchy, spacing, typography, semantic color, reusable components, and evidence visuals are consistent |
| Interactivity | Keyboard navigation, deep links, progress, fullscreen, help, and presenter notes work without a framework |
| Export safety | Export mode is explicit, motionless, and hides only presentation chrome |
| Geometry | Every visible slide element fits the validated 16:9 viewport without collisions or tiny rescue text |
| Evidence integrity | Facts, illustrative values, sources, periods, and caveats are labeled accurately |
| PNG reliability | One long-lived renderer produces the expected count of nonempty, exact-dimension images |
| PPTX fidelity | Verified PNGs fill widescreen slides exactly and the flattened-content limitation is disclosed |
| Portability and privacy | The HTML is self-contained by default and contains no unintended private names, URLs, assets, or credentials |
