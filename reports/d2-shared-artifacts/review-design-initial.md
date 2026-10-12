# D2.S2 independent design review

Reviewed design SHA256: `9ef9096c0144b6d5d0ddc34ea2d259b87f741d9619c87ae7cfa19bb20f495141`. Dependency HEAD: `2f4c16526b75b9df14da8fdedbbb76040878b6cf`. Reviewer: `/root/d2_s2_review_astra`; no design or product authorship.

Decision: needs revision; one open medium finding. Scope, sole ownership, finite closure, detached receipt, compatibility and rollback are otherwise coherent. This is a design review, not implementation or behavioral approval.

## D2S2-DESIGN-001 — Preserve actual source-file provenance

`skill_jobs.py:218`, `uac_modes.py:146`, and `topology.py:118` derive resource source paths from the consumer slug. With imported files that produces a nonexistent authored path. The canonical resource policy requires original files and raw line references. Specify an owner-aware source-location accessor, use it in all three producers, preserve consumer-local destination separately, and test owner-file existence plus matching source bytes/lines. Status: open.

The JSON companion records review conditions for the implementation and UAC rounds. No product files were edited.
