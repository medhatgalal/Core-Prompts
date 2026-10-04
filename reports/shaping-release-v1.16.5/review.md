# Release review

Scope: finalize v1.16.5 and fix recognition of pristine v1.16.4 shaping packages.
The five-line installer change adds only three existing first-party identities;
no rename, retirement, agent surface, permission or product code is introduced.
The tag object and peeled commit were verified on both canonical remotes before
being added to the reviewed historical pin set.

All prior catalog package inventories, byte/mode identities, release identities
and runtime/launcher identities remain present with identical meaning. Generated
identity IDs can change; their bindings were compared after resolving them.

The focused regression first failed because all three released packages were
preserved. It now passes for a pristine bundle and proves modified bytes, mode
changes and extra files remain protected. The fixture uses immutable Git trees;
CI already fetches those release tags and supplies Git and procps.

The final full local suite passed 1,627 tests plus 138 subtests, with 13 skips.
Native exporter checks also passed 19 tests after the sandbox process-inspection
restriction was classified and resolved. Strict validation, catalog/capsule
readback and source-preserving archive checks passed. Gemini native discovery
timed out and remains a disclosed environment warning, not native discovery proof.

User docs, examples and source instructions are aligned with the previously
reviewed handover behavior. Installation will add only its required missing
companion skills on existing providers and preserve unrelated customized packages.
No live shaping/build or saved Google Doc placement success is claimed.

Code/docs review findings: none open. Hosted and publication evidence is recorded
separately after delivery.
