# Meeting briefing compatibility

Use this contract for `briefing`, or conversational asks such as "opex briefing", "prepare opex", "operational excellence prep", and "incident briefing". These are intent routes inside the single canonical capability, not native CLI aliases or another skill package. Keep the Daily OpEx Digest's complete board, section order, current policy, and authority boundaries.

## Inputs and selection

Use explicit ticket keys directly. For "prep for next meeting", inspect the user-identified tracking document or verified active query, show the proposed ticket population and meeting date, and confirm inferred selection before proceeding. Preserve every explicitly selected ticket, including closed tickets whose preventive obligations remain. Never cut the board to five incidents. For a briefing, provide full incident depth for every confirmed selected ticket; missing evidence gets an explicit gap rather than an omitted section. Outside briefing mode, daily/deep-dive selection behavior is unchanged.

Use the user's resolved output directory. Default briefing output to `BRIEFING.html` and `BRIEFING.md` with `--basename BRIEFING --format both`; if either exists, choose a fresh dated basename and report it. Do not restore a hardcoded Google Drive home path or automatic upload.

## Evidence collection

- Read each incident and every child/linked remediation story, bug, task and DPA. Do not equate remediation with DPAs or discard completed fixes. Record key, summary, current status, owner, target date or explicit `no date`, verified incident relationship, source locator/date, and why the fix blocks recurrence. Keep ticket completion, deployment and demonstrated effectiveness distinct. Flag sourced contradictions; an open incident with a Done fix is a question to investigate, not proof of an error.
- Follow linked engineering records and all comments/postmortems for causal detail. Each Why is one sourced factual sentence; use up to five without padding. If RCA is absent, say so. Ask the verified current owner to start the postmortem only when current evidence establishes that work is missing; lack of access is not proof of missing work.
- Search the prior six calendar months ending at the reporting date, or the user's explicit alternative window. Open every cited prior incident and record why its component/failure mechanism is relevant, evidence/date, and prior remediation attempts. Two or more verified prior incidents support the recurring-pattern table; one supports prior-incident context, not a confirmed recurring pattern. State an incomplete search as a coverage gap.
- Collect distinct customer identities separately from sites/deployments. Show verified customer counts prominently and per incident; unknown customer coverage stays unknown. Do not relabel affected site counts as customers.
- For a confirmed Appian site, verify historical field mappings before use: customer impact `customfield_10663`, affected customers `customfield_10666`, immediate fix `customfield_10253`, postmortem link `customfield_10673`. Verify the meaning of `Executive-Incident-Communication` before treating it as executive visibility. Historical RCA categories are Infrastructure, Code Defect, Configuration, Capacity, External Dependency, and Process Gap; use only a sourced category, otherwise unknown. None of these mappings replaces current site or SLA policy discovery.

## Normalized incident depth

Existing snapshots remain valid. The optional `deep_dive.briefing: true` marks complete briefing sections, including explicit gaps. In that object use the existing `facts`, `customer_risk`, `five_whys`, `preventive_action`, `talking_points`, and `questions` fields, plus:

- `fix_tickets`: every verified linked remediation record, including DPAs and completed fixes. Each row has `key`, `summary`, `status`, `owner`, `target_date`, `relationship`, `evidence`, `why_it_helps`, `deployment`, and `effectiveness`. Missing optional values stay unknown/no date. Relationship and source evidence are required for included records.
- `recurring_incidents`: prior rows with `key`, `summary`, `relevance`, `evidence`, and `prior_remediation`; `recurrence_window` records the searched dates. Include only verified relevant prior tickets. Empty arrays mean no supplied verified rows, not proof of an exhausted zero-result search.
- `customer_impact`, `interim_mitigation`, and `residual_risk`: sourced prose or explicit unknown.
- `evidence_gaps`: missing reads, unresolved contradictions, incomplete fix/recurrence/customer coverage, or insufficient coaching evidence.

At incident level, optional `affected_customers` lists deduplicated verified customer identities. Omit it when unknown; an empty list is valid only after a verified zero-customer finding. Keep `affected_entities` unchanged for sites/deployments. Existing postmortem state/evidence is reused.

Write 3–4 first-person, present-tense talking points and three likely questions with sourced answers when evidence supports them. If it does not, state the missing evidence rather than fabricate bullets or answers to meet a count. Verified facts use direct language; uncertainty is explicit. Avoid filler. Include the current owner/action in missing-RCA coaching when justified.

## Outputs and optional exports

Render the HTML/Markdown board first. Preserve the accepted top navigation and full daily tables; expand briefing incident sections to include customer impact, postmortem evidence, complete fix tickets, prior recurrence evidence, risks, coaching and source gaps. Verify ticket links against the configured site and escaped source content. The historical sidebar/color template is retained as provenance, not a replacement for the accepted digest.

For additional requested formats, use bundled `export_report.py` on the rendered HTML:

- `txt`: local plain-text equivalent, retaining headings, table cells and drilldowns.
- `pdf`: optional Pandoc conversion, requiring a functioning local PDF engine. If unavailable or conversion fails, report PDF as incomplete and retain HTML/Markdown; do not label a renamed file as PDF.
- `gdoc`: use the authorized existing Google Doc ID and explicit `--authorize-google-write`; the helper appends the plain-text equivalent through `gws docs +write`. If the user needs a new Doc, create it through the available authorized Docs interface first, then pass its returned ID. Do not infer a destination or create/share/announce a document automatically. On auth/tool failure, report the Google export as incomplete and retain local files. Do not retry external writes automatically.

No export runs merely because the snapshot or old metadata mentions a format. Export only the user's requested format and destination. Every final report distinguishes rendered local artifacts, optional converter execution, live source verification and hosted document write/readback evidence.
