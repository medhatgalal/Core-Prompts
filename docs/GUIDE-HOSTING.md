# View or host the visual guide

The [visual guide](guide/index.html) is a self-contained static HTML file, with its own routing snapshot, styles and script. It makes no AI/API call, fetch, telemetry or external asset request. Typed task text stays in the tab. Source links open only when selected. It ports the user-facing navigation idea, not the private skill-landscape research report or its dataset.

## Start without hosting

1. In a trusted checkout or extracted release, open `docs/guide/index.html` in a browser. No server, package installation or API key is needed.
2. From GitLab/GitHub file views, download the file and open it locally. A repository blob or raw HTML endpoint is not equivalent to a website serving active JavaScript.
3. Use the [static overview](guide/intent-flow.svg) and [Markdown guide](INTENT-ROUTING.md) directly in repository docs when interactive hosting is unavailable.

The browser guide lists source-catalog owners. It cannot observe another user's installed skills, accept artifacts or authorize a workflow. Use the project integration in the Markdown guide for assistant recommendations.

## GitLab primary

GitLab Pages supports static HTML/CSS/JavaScript. For an internal or private guide, require **Only project members** access and confirm that the instance administrator enabled Pages access control. Project visibility alone is not sufficient: Pages can have a separate audience. Do not fall back to public hosting if access control is unavailable.

The project was observed on October 21, 2026 as internal with `pages_access_level: private`; that is a configuration observation, not a successful Pages deployment or proof that the instance serves Pages. No hosting/access setting is changed by this documentation slice.

A reviewed deployment can publish the `docs/guide/` directory as static output after running `python3 scripts/build-intent-guide.py --check`. Choose the exact Pages URL, audience and instance capability before enabling a Pages job. This change deliberately contains no automatic Pages deployment job.

GitLab can preview HTML artifacts only when Pages is enabled globally; internal/private artifact previews also need instance-level access control. Raw artifact API endpoints return plain text. Artifact retention and preview support make this an optional review route, not a permanent documentation URL.

## GitHub mirror

Keep source and generated guide bytes synchronized with GitLab. GitHub Pages can host this same static file, but ordinary Pages publication is normally public even when its source repository is private. Private Pages requires an eligible organization on Enterprise Cloud; it is not available merely because a personally owned repository is private.

The existing GitHub mirror was observed as public, personally owned, with no Pages site. Those source settings are preserved. Do not treat permission to synchronize source as permission to activate another hosted website or copy the private research report there.

## Rebuild and maintain

Canonical route metadata: `.meta/intent-routing.json`. Canonical agent policy: `.kiro/steering/skill-routing.md`. The builder uses the existing job map only for source-catalog lookup labels; it does not change skill contracts or implement a natural-language classifier.

```bash
python3 scripts/build-intent-guide.py
python3 scripts/build-intent-guide.py --check
```

Generated files are `docs/guide/index.html`, `docs/guide/intent-flow.svg` and `.kiro/steering/intent-routing.json`. The last file travels in the already supported steering/runtime boundary, so an adopted runtime can load routing data without depending on source-only docs. Regenerate the normal Core surfaces/runtime inventory after routing changes. No home-global rule, installed skill, account or scheduler is modified by the guide builder.

Verification covers source consistency and observed browser interactions. It does not establish model-routing effectiveness, globally loaded instructions, actual installation, or successful private hosting.

## Primary sources

- [GitLab Pages access control](https://docs.gitlab.com/user/project/pages/pages_access_control/)
- [GitLab Pages administration](https://docs.gitlab.com/administration/pages/)
- [GitLab artifact preview and raw content](https://docs.gitlab.com/ci/jobs/job_artifacts/)
- [GitHub Pages visibility and private-site requirements](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site)
- [GitLab Markdown diagrams](https://docs.gitlab.com/user/markdown/)
- [GitHub Markdown diagrams](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
