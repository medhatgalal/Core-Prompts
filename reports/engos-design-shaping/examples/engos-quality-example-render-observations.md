# engos-quality-example-render-observations

Actual controller observations, 2026-09-17. This receipt supplements, rather than rewrites, author journals. It does not pass semantic G3 or placement G4.

All nine final component/sequence/data-flow sources rendered successfully using cached Mermaid 11.17.2 and its CLI, white background, width 1400, scale 2. All nine PNGs were visually inspected. The first Round 2 render exposed note overflow in two sequences and an ignored palette in the configuration sequence. A bounded visual repair added explicit note line breaks, used escaped double-quoted CSS selectors and changed the admin glyph from a stick figure to a labeled participant. Relationships and contract semantics were preserved. All three sequences were rerendered and inspected again; labels, alternate paths, headers/footers and role colors were legible without cropped text. Long horizontal diagrams require pan/zoom at narrow target widths.

Round-one parse failures remain unmodified. The author journals' three sequence hashes describe the pre-visual-repair state. The following hashes supersede those three source/render bindings only; other content remains as authored.

Native HTML preview actually rendered nine SVGs with zero Mermaid error elements and 87 tables across the full two-round library. Controller inspected representative native sequence, component and data-flow screenshots and added full-size PNG links and horizontal panning. This is draft reference-library placement, not a Bet-ready gate pass or a claim of complete saved-target parity. No Google Doc was created for these examples.

## Final source and PNG inventory

```text
f15f6fb6c6c1cc936de4f4ebeb2887e790c91118baacb18b1c2a0ce051073543  reports/engos-design-shaping/examples/engos-example-model-capacity/round-2/component.mmd
49bd53a7e5d2c55d4fad323a6555611d84b20988177453eed52870a338a5f571  reports/engos-design-shaping/examples/engos-example-model-capacity/round-2/data-flow.mmd
fe73f39d292d8622f92c4e986559a39e62ff569a4f698ccb7df3288b3a509573  reports/engos-design-shaping/examples/engos-example-model-capacity/round-2/sequence.mmd
5c9181e61db5328841e580460c528da92dfa9f56b43447ffea33a3bc664ee496  reports/engos-design-shaping/examples/engos-example-insight-visibility/round-2/component.mmd
ffc8f805d8407a3a1d3d761d387d19ac3c0e7cb70d0006473f8895c23cc93f90  reports/engos-design-shaping/examples/engos-example-insight-visibility/round-2/data-flow.mmd
d4347a2f992a483e7367c382d4f2df0a56179ed15d6a3a0aad279e0d8db16626  reports/engos-design-shaping/examples/engos-example-insight-visibility/round-2/sequence.mmd
f4f84211f97c00bcd769a1a00740608e32e7d69d57c2b4937fe111baa3c84197  reports/engos-design-shaping/examples/engos-example-config-deployment/round-2/component.mmd
9e79050034e104024f3481b27e4198247a65c12051e3e1dce8edaaa572cb27a1  reports/engos-design-shaping/examples/engos-example-config-deployment/round-2/data-flow.mmd
c0a628664a620d2f91b24278aa7bda02046d4ab1ce2f01218fa7f800bc2d711a  reports/engos-design-shaping/examples/engos-example-config-deployment/round-2/sequence.mmd
bda23910cf5c2d0415ea6ab62dceec8863c98f7d40cd4b385aa3a01390959157  reports/engos-design-shaping/examples/engos-example-model-capacity/round-2/rendered/component.png
bbcb6629b9a0863695e0b3c1a24a5b10db490ad80cc7139aff6f88c23ea16e9a  reports/engos-design-shaping/examples/engos-example-model-capacity/round-2/rendered/data-flow.png
0b078774d2449c886d5df3b2104b0ae0e01b67c957d469b8e24dd746add70d2d  reports/engos-design-shaping/examples/engos-example-model-capacity/round-2/rendered/sequence.png
321cab8e9f45bec00ca6e8e2854c2bcfae663e32d5ef5bbe3292dae1b69080b9  reports/engos-design-shaping/examples/engos-example-insight-visibility/round-2/rendered/component.png
6c8b00c4beae013bd913336fef50a40ce851e73db6ea30c0b947669fe95b81ce  reports/engos-design-shaping/examples/engos-example-insight-visibility/round-2/rendered/data-flow.png
cb307df8069225f6da69cb94c82680545a0e54878eae76be8ee49be10391ed96  reports/engos-design-shaping/examples/engos-example-insight-visibility/round-2/rendered/sequence.png
30bd4ff5e0b8c6e65d9b208568e5daa237f555c556d5faf20b4774850cdc550e  reports/engos-design-shaping/examples/engos-example-config-deployment/round-2/rendered/component.png
ce03a1db04145963582496f9eccf62f2108f9ec31b189a15535f6b5d4cb985b4  reports/engos-design-shaping/examples/engos-example-config-deployment/round-2/rendered/data-flow.png
481defedcea5540ddc2031b36cde1e120392b1be0bcc4dcbde9f8a06b63ed184  reports/engos-design-shaping/examples/engos-example-config-deployment/round-2/rendered/sequence.png
```
