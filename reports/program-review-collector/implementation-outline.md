# D6.S2 bounded implementation outline

Entry: accepted contract JSON d63794fd008b872b8318b3d9f9b1447709b91d80604ebccb9861b78f3aa1bc88 and Markdown 43946a1b3e289dee753a9a89c83b50c1a02e0d9eecd2562e8eb466b04c8c4809 verified. All four D6 owner sources match frozen hashes. Intentional shared foundation plumbing drifts reported to controller; source writes wait for its admission/CI clearance.

Implementation: a standalone standard-library Python CLI with strict argparse exit 3, duplicate-key schema/map entry snapshots, bounded fixed Git argv and sanitized environment, exact full endpoint verification and raw object hashes, NUL raw/numstat parsing, raw pathname encoding, explicit short gitlinks and incomplete errors, fd-relative exclusive artifacts and atomic no-replace manifest publication. Adjacent frozen schema is copied verbatim. Existing review route/defaults/Findings.v1 stay intact; additive collect route.

Verification: fixtures RP-01 through RP-13 and RP-16 execute against canonical script; fault seams monkeypatch actual runner or output syscall wrappers while counting injected faults. Real initialized-submodule observation injects Trace2 into actual children and checks capture, commands, endpoint-only artifact contents. RP-14 generated standalone copies and RP-15 hosted/shared CI are integration-controller evidence, not source-only acceptance claims.

Candidate: start full current SSOT body, add conditional collect guidance and CLI limits only; save candidate for controller same-slug UAC. No builds, metadata/generated writes, release, installed state, push or merge in worker scope.
