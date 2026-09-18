# Local export and render helper

Run `python3 resources/scripts/artifact_export.py --help` from the resolved skill
package, not a guessed machine path. The helper performs no network publication,
no skill discovery, no review and no gate advancement. Its source-export result
always reports visual and saved-target review as pending/not performed.

Use an explicit bundle directory containing pitch.md, contracts.md,
security-owners.md, component.mmd, sequence.mmd and data-flow.mmd. The
`--documents` option adds required source sidecars to the export; it must retain
the three required prose files. Never export unrelated raw private input merely
because it shares a folder. Obtain target-specific write authority separately.
This helper's complete-pitch input contract is for full shaping. Standalone
artifact-only placement can use the existing host formatter/native passthrough
with its actual bundle inventory; do not invent a pitch document just to run this
helper. Its source and saved-target verification obligations remain unchanged.

```text
python3 resources/scripts/artifact_export.py json --bundle BUNDLE --output NEW_EXPORT/pitch.json
python3 resources/scripts/artifact_export.py html --bundle BUNDLE --output NEW_EXPORT/pitch.html
python3 resources/scripts/artifact_export.py render --bundle BUNDLE --output FRESH_IMAGES --mmdc TRUSTED_MERMAID_CLI
python3 resources/scripts/artifact_export.py docx --bundle BUNDLE --images FRESH_IMAGES --output NEW_EXPORT/pitch.docx
```

Replace uppercase paths with actual scoped paths. The existing Mermaid executable
must already be trusted/available; the helper never installs it. JSON/HTML need
Python standard library. DOCX needs python-docx and Pillow in the host's approved
document runtime. Resolve that runtime before using the DOCX path. A missing
dependency is a named blocker, not permission to install globally.

JSON preserves exact Markdown/Mermaid, source hashes, structured blocks with section
identity and full table row inventories. HTML escapes source HTML and renders all
three diagrams using pinned Mermaid 11.17.2 from jsDelivr; network access to that
renderer is needed. Offline use requires a trusted local renderer/asset path or
the source-bound PNGs, not a claim that raw fences rendered. The supported Markdown
subset is headings, paragraph/list lines, code fences and explicit pipe tables;
HTML inline markup remains literal; DOCX paragraphs format simple bold/code spans
and retain link destinations as visible references. Table cell text is preserved.
Complex or malformed table structures fail loudly.
Inspect presentation, including wide tables and labels, instead of assuming fidelity
from equal counts. Readable rendering can need source layout/format adjustments.

Render outputs include render-manifest.json binding each PNG to its Mermaid source.
It records pixel inspection as pending. DOCX rejects stale/mismatched render images,
uses native tables and embeds all three PNGs. The initial layout is landscape for
wide engineering tables and portrait for tall diagrams: Title 18, H1 13, H2 11.5,
Arial 11 body, bold/color hierarchy.
This is a starting representation, not a visual quality certificate. Render every
DOCX page and inspect it, repair and rerender, sanitize title borders where the host
document workflow requires it, then use only the verified version for import.

Existing differing exports are not overwritten; use a new revision directory.
Output publication pins physical directories through POSIX no-follow directory
descriptors and uses exclusive creation. Unsupported hosts fail explicitly; this
helper does not silently use weaker Windows path-based publication. DOCX is built
in memory and published once; embedded image buffers are the same bytes whose
hashes were verified. Fenced code stays literal, including shell operators.
An identical JSON/HTML repeat is a no-op. Partial render output is retained after
failure for diagnosis; it has no successful manifest. Exit 0 means local conversion
succeeded, exit 2 means invalid input, unavailable dependency or operational error.
Neither outcome claims that a Google Doc exists or a shaping gate has passed.

The renderer runs on source snapshots in a private temporary directory, with a
60-second per-diagram default (`--timeout-seconds`, maximum 300), an owned process
group that is terminated on timeout/failure, and at most 16 KiB of diagnostic
capture. Temporary scratch is cleaned; already-published partial PNGs may remain
in the caller's fresh output directory for diagnosis, without a success manifest.
Keep operator-selected artifact retention bounded and clean only task-owned outputs
after preserving evidence. Local conversion does not certify rendered readability.
