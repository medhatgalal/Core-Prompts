# Local export and render helper

Run `python3 scripts/artifact_export.py --help` from the resolved skill's
resources directory (not the skill package root). This helper converts a selected local inventory; it does not publish,
review semantics, certify visual quality or advance a gate. Python standard
library suffices for JSON, HTML and invoking a trusted renderer. DOCX needs
python-docx in the approved host document runtime. No installation is performed.
Use absolute authorized bundle/output/image paths when they live outside this
resource directory, so generated documents stay in the project's artifact home.

## Profiles and exact arguments

The default `--profile legacy` preserves the prior CLI and required inventory:
pitch.md, contracts.md, security-owners.md and component.mmd, sequence.mmd,
data-flow.mmd. `--documents` may add sidecars but must retain those three prose
files for legacy/shaped. Select relevant files explicitly; do not export unrelated
private input merely because it shares a directory.

`--profile framed` prefers framed.md; pitch.md is a compatibility fallback when
framed.md does not exist. `--documents framed.md` or another explicit prose list
requires only those documents. No contracts, security table, diagrams or images
are required. Wording, titles and uncertainty remain the supplied author's;
conversion neither adds a solution nor certifies that supplied prose is framed.

`--profile shaped --presentation presentation.json` requires a bundle-relative
mapping, anchors all three figures to actual sections and compacts contract and
security tables without dropping source fields. Blue title/primary headings,
green subordinate headings, dark-blue table headers and white header text reflect
the requested hierarchy. Native DOCX uses Letter portrait, Title 18pt, H1 13pt,
H2 11.5pt, Arial 11pt body, repeating headers, bookmarks, links and inline figures.
Legacy DOCX retains landscape layout and accepts earlier PNG-only manifests.
Tall legacy figures switch to portrait. Figure dimensions are bounded by the
actual section's usable width/height with reserved caption/paragraph space;
long captions and page layout still need rendered visual inspection.

```text
python3 scripts/artifact_export.py json --bundle BUNDLE --output NEW_EXPORT/pitch.json
python3 scripts/artifact_export.py html --profile framed --documents framed.md --bundle FRAME_BUNDLE --self-contained --output NEW_EXPORT/frame.html
python3 scripts/artifact_export.py docx --profile framed --documents framed.md --bundle FRAME_BUNDLE --output NEW_EXPORT/frame.docx
python3 scripts/artifact_export.py json --profile shaped --presentation presentation.json --bundle BUNDLE --output NEW_EXPORT/pitch.json
python3 scripts/artifact_export.py render --profile shaped --presentation presentation.json --bundle BUNDLE --output FRESH_IMAGES --mmdc TRUSTED_MERMAID_CLI
python3 scripts/artifact_export.py html --profile shaped --presentation presentation.json --bundle BUNDLE --images FRESH_IMAGES --self-contained --output NEW_EXPORT/pitch.html
python3 scripts/artifact_export.py docx --profile shaped --presentation presentation.json --bundle BUNDLE --images FRESH_IMAGES --output NEW_EXPORT/pitch.docx
```

Replace uppercase placeholders with actual scoped paths. Differing outputs are
never overwritten; choose a new revision directory. Identical JSON/HTML repeats
are no-ops. Rendering always requires a fresh directory.

For a cached JavaScript CLI, add `--node APPROVED_NODE --mmdc CACHED_CLI_JS`.
An operator-selected `--puppeteer-config LOCAL_BROWSER_JSON` can select the
existing local browser/launch options. Its bytes are snapshotted and SHA256 is
recorded; it is not supplied by source content. Neither option installs software.
For a network-free verification on macOS, run the command inside
`sandbox-exec -p '(version 1)(allow default)(deny network*)'`; browser launch needs
the host's local process permission. Report a denied launch rather than fetching
or switching to another renderer. The manifest's reported version is the CLI's
`--version` output, not an inferred Mermaid core version.

## Explicit presentation mapping

Get exact section IDs from a legacy JSON export's `blocks[].id`, or form them
from the source filename plus normalized heading slug. Duplicate heading slugs
gain -2, -3, etc., checking every emitted ID to avoid collisions with headings
that already contain suffixes. Source links such as `[Bounds](#bounds)` resolve
within their source document to the same filename-prefixed heading ID used by
HTML and DOCX bookmarks. The same destination inventory includes exported document
starts and generated detail IDs, such as `#contracts.md--C-1`. Known exported links
like `contracts.md` or `research.md#bounds` become internal links. Unknown relative
references become readable `label (destination)` text; they never open local files
or trigger resource requests. Truly unresolved fragments fail before publication.
Missing figure anchors fail; placement is never guessed. Each figure
appears after its section's text/tables, before the next heading. Supply caption
and alternative text explicitly; these are not inferred diagram claims. Synthetic
mapping example, saved inside the selected bundle:

```json
{
  "schema_version": "ShapingPresentation.v1",
  "diagrams": {
    "component.mmd": {"section_id": "pitch.md#architecture", "caption": "Component responsibilities", "alt": "Input and output responsibilities shown in the component source"},
    "sequence.mmd": {"section_id": "pitch.md#sequence", "caption": "Interaction sequence", "alt": "Ordered interactions shown in the sequence source"},
    "data-flow.mmd": {"section_id": "pitch.md#contracts", "caption": "Data movement", "alt": "Data movement shown in the data-flow source"}
  }
}
```

The presentation file has a separate hash in JSON. Layout changes do not rewrite
the original Markdown/Mermaid inventory or its aggregate source hash.
Each diagram may also contain optional nonempty plain-text `title` and `legend`
strings, for example `"title": "Component boundaries", "legend": "Dashed: proposed; solid: existing."`.
Supply the legend explicitly; the exporter never infers meaning from colors.
These fields appear in JSON, HTML and DOCX, and renderer manifests bind them with
`presentation_sha256` covering section_id/caption/alt and supplied title/legend.
Changing or removing supplied figure metadata makes those assets stale; rerender
to a fresh directory. Earlier manifests remain compatible when neither optional
field is supplied. Native DOCX keeps title/caption/image/legend together and
reserves page capacity for all supplied figure text; oversized groups fail before
publication. Final typography/pagination still requires pixel inspection.

## Compact tables and lossless supporting detail

Contract summary groups ID, Interface, Purpose (when present), State and Owner.
Security summary groups Responsibility, Owner and How enforced. Every row links
to a stable-ID detail section retaining every original header and value in source
order. HTML uses definition lists; DOCX uses native detail tables with a repeating
`Field / RECORD-ID` header, so continuation pages identify their source record.
Inline code, emphasis and links are rendered in detail cells using the same bounded
inline rules as prose. Raw Markdown and every original field value remain in JSON;
only markup syntax is converted to formatting, never prose or uncertainty rewritten.
No table is rasterized. JSON retains exact Markdown, headers
and cells. Contract IDs must be unique plain identifiers (letters/digits/underscore/
dot/dash). Security uses supplied IDs or a stable hash of unique responsibility
text. Duplicate identities fail instead of creating ambiguous links.

Narrow built-in aliases include Method / interface, Method / Endpoint,
Method / Purpose, Direction; producer → consumer, Inputs / bounds, Output / meaning,
Material errors, Timeout / retry / idempotency, Consistency / persistence / lifecycle,
Trust / access, State / evidence, Owner / action and Non-responsibility. Security
also recognizes How enforced / control, Enforcement location, Trust / data boundary,
Evidence / state, Explicit negative responsibility and actual owner, Gap / next action.
Combined fields retain complete values. The helper never shortens cells, derives
acceptance status or relabels uncertainty as readiness.

For an unfamiliar schema, add a `tables` object to the presentation JSON.
Each document has one entry per pipe table in source order; null selects built-in
aliases for that table. This synthetic map handles custom header names:

```json
{
  "contracts.md": [{
    "id_field": "Key",
    "primary": {
      "ID": ["Key"],
      "Interface": ["Seam"],
      "State": ["Finding"],
      "Owner": ["Custodian"]
    },
    "detail": ["Retained note"]
  }]
}
```

Use that object as the value of `tables`, alongside schema_version and diagrams.
Every source header must occur exactly once across the 1–5 primary groups and
detail list. The first primary group must include id_field for linked detail.
Multiple fields in a group retain labeled original values. Missing, duplicate
or unknown fields fail with a mapping error. Supporting detail always includes
the full original row, including fields also shown in the summary.

For a compact acceptance/example table that is not an interface inventory, use
`{"layout":"native"}` for that specific table entry. All original headers/cells
remain native and unchanged; no interface fields or synthetic IDs are invented.
This explicit layout selection does not satisfy semantic contract completeness
or visual review by itself. A wide native table still needs readable presentation.

## Assets and self-contained HTML

Rendering records the selected executable's reported --version, optional Node
path/browser-config hash, validated source styling, strict Mermaid config
(htmlLabels false), white background, width 1400 and scale 2. It produces
SVG plus PNG for each unchanged Mermaid source, then writes render-manifest.json
binding source SHA256, SVG/PNG SHA256 and dimensions, section ID, caption, alt text
and renderer configuration. Hashes establish mechanical binding, not trusted
authorship or semantic fidelity. Use an already trusted Mermaid CLI; the helper
never downloads one.

SVG validation runs again when assets are consumed. Only UTF-8 is accepted;
declaration/entity checks happen before XML parsing, including rejection of NULs
and unsupported encodings. Style elements cannot contain children. Scripts,
event handlers, foreignObject, animation, external resources (including CSS
image-set), unsafe CSS/URLs, DTD/entities and unsupported SVG elements fail.
Static filter/feDropShadow and CSS child selectors are supported.

Mermaid 11.17.2 emits unused animation CSS even for static drawings. Only renderer
output may undergo this bounded normalization: remove the exact built-in
edge-animation-frame/dash keyframes and slow/fast animation rules when neither
animation class occurs on any element. Unknown/changed rules and remaining active
animation fail full validation. Source-requested animation is not stripped.
Each manifest entry records `svg_original_sha256`, exact removed rules in
`svg_normalization` and the final `svg_sha256`. Normalized XML serialization may
change namespace prefixes/escaping; it does not change drawing text/geometry.
Imported assets are validated, never silently normalized. No source bytes or
source hashes are rewritten by this output-only transform.

Existing strict-JSON `%%{init: {...}}%%` directives may specify static theme,
flat themeVariables and themeCSS. These remain verbatim in the renderer input
under every profile. CSS/resources are validated, and source security/config
overrides, unsupported directives and source-requested animation are refused.
Unsupported content needs a separately reviewed source/layout decision, never
invented diagram internals or a blanket weakening of resource checks.

HTML with `--images ... --self-contained` embeds verified local SVG bytes as data
images with keyboard-accessible full-size views, captions and alternatives. Each
figure has one SVG image: a labeled checkbox switches it between fit-to-width and
its full intrinsic size in a scrollable container. There is no duplicate image in
an expanded details panel. Print always returns the same image to fit-to-width. It
has no runtime script/CDN dependency and supplies a restrictive content policy.
The same PNGs feed DOCX inline shapes with alt text. Source/hash/size or
caption/anchor mismatches, missing assets, symlinks and path traversal fail.
Plain HTML without images retains pinned Mermaid 11.17.2 from jsDelivr and needs
network access. Run an actual offline browser load before claiming offline
acceptance; code/asset checks alone do not prove it.

Supported Markdown is intentionally bounded: headings, joined soft-wrapped
paragraphs, ordinary blockquotes, flat bullet/numbered lists, simple bold/italic/code
spans, safe HTTP(S)/mailto and known exported-document/fragment links, fenced code
and explicit pipe tables. Fenced operators/backticks stay literal. Source HTML
is escaped, unsafe links stay literal, and malformed tables or nested lists fail.
This is not a general Markdown engine. Source prose is not rewritten; full JSON
remains the exact-source audit record.

## Verification and limits

Inspect all DOCX pages and diagram/table regions; check HTML at 375/1280/1920px.
Ordinary native rows are marked non-splitting. Detail headings, repeated headers
and the first two field rows are kept together. A conservative character/line
budget rejects rows or leading groups estimated to exceed a page; the error asks
for a deliberate source-row split rather than clipping, shrinking type or silently
discarding text. This bound is not a font/layout measurement and can reject a
dense row conservatively. Actual viewer pagination remains a separate visual gate.
Long primary cells stay complete and may require a deliberate map/source/layout
revision after visual review. Scrollable tables retain normal word wrapping;
supporting fields remain printable/reachable. Structural equality is not visual
quality, semantic acceptance or saved Google Docs proof. Reference appearance
does not establish readiness or approval. Use the document skill's marker and
render workflow when creating actual deliverables, then verify native saved cells,
links and figures after any separately authorized import.

POSIX directory descriptors/no-follow/exclusive creation protect publication.
Unsupported hosts fail rather than weakening this contract. DOCX is built in
memory and published once with the same verified image buffers. Source reads also
pin every directory and use no-follow descriptor-relative opens with regular-file
checks. Replacing a checked path with a symlink cannot redirect the read. Metadata
checks reject detected in-place changes during a read. This is not an atomic
multi-file snapshot: callers must keep the input bundle quiescent; rendering
rechecks source and presentation hashes before issuing its successful manifest.
Renderer calls
use private snapshots, a 60-second default per invocation
(`--timeout-seconds`, maximum 300), bounded 16 KiB diagnostics and an owned process
group terminated on timeout/failure. Partial SVG/PNG output may remain for
diagnosis after failure without a success manifest; retry in a fresh directory.
Exit 0 means local conversion succeeded; exit 2 means invalid input, missing
dependency or operational failure. Visual review stays pending; target review is
not performed. No sharing, external placement or gate advancement is implied.
