# Exercise Verification Receipt

## Source and renderer

- Source pitch: `https://docs.appian-stratus.io/process-mining/new-arch/`
- Bundle hash: `c44623c2c1ad5189ff636bae7fa811480a1cb1ee626802ed24c7e842c238a73b`
- Renderer: Mermaid CLI `11.17.0`
- Render command: `npx --yes @mermaid-js/mermaid-cli -i <source>.mmd -o <rendered>.png -b white`
- Output files: `rendered/component.png`, `rendered/sequence.png`,
  `rendered/data-flow.png`

## Pixel inspection

The three standalone PNGs were opened and inspected as images. The component
render shows the LCP boundary, semantic node colors, labeled HTTPS/REST/gRPC
edges, and the ADS store. The sequence render shows six participants, the
authorized/unauthorized branches, and the logUuid invariant note. The data-flow
render shows synced records, CTAS flat tables, analytical tables, and both
preprocessor/query-path inputs. No clipped nodes or blank render was observed.

The HTML surface was served locally and inspected in the authenticated browser.
The rendered DOM contained three Mermaid SVGs, two tables, and the placement
receipt. Pixel inspection of the lower page confirmed readable data-flow,
contract, security, and receipt sections. The HTML path is therefore observed
as a native Mermaid/Markdown passthrough.

## Gate fixture checks

| Fixture | Expected | Observed |
| --- | --- | --- |
| `fixtures/missing-artifacts.md` | `partial`; fail artifact completeness | Missing component/sequence/data-flow/contracts/security bundle is explicit; the updated gate requires these artifacts for a seam-crossing pitch |
| `fixtures/complete-artifacts.md` | Artifact completeness passes; rubric still applies | Manifest, three diagrams, two tables, evidence, no-gos, and receipts are present |

## Google-Doc adapter check

The same bundle produces a deterministic dry-run receipt in
`google-doc-placement.md`. The adapter selects rendered image plus native Docs
tables, preserves the bundle hash, and stops at `human_step_required` because
the known private-image insertion/readback path is not available and no
external write was authorized. This is an honest adapter result, not a live
Google-Doc placement claim.
