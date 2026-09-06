# Loopy preservation input

This is the complete installed seven-file Loopy package captured for UAC intake.
`provenance.json` pins every file's SHA-256 and records the existing installer's
source and folder hash. `package/` is an immutable preservation fixture, not a
second active skill installation or generated surface.

The installer record names `Forward-Future/loop-library`; that repository now
redirects to `Forward-Future/loopy`. The upstream repository identifies the skill
installer as `npx skills add ... --skill loopy`. The accompanying MIT license was
fetched separately and its Git blob identity is recorded. Current upstream skill
changes were not imported: the requested source is this installed package.

Native package requirements: five relative `references/*.md` links and the
`agents/openai.yaml` interface metadata including `$loopy`. No scripts, binaries,
MCP dependency declarations, secrets, or symlinks are present in the snapshot.
Web/catalog and host repository/thread tools are runtime capabilities described
by the source, not permissions granted by packaging.

Run normal UAC plan/judge before canonical apply. A generic uplift summary,
appended source dump, or changed required output does not satisfy preservation.
Do not promote this fixture solely because a deterministic gate reports accepted.
After an approved intake, author the body in `ssot/loopy.md` and portable companion
files in `sources/skill-package-resources/loopy/`, then generate native surfaces.
Keep this snapshot unchanged as fidelity evidence.
