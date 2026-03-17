# Requirements

## Functional
- Add `bin/uac judge <source...>`.
- Add `--quality-loop`, `--quality-profile`, and `--max-quality-passes` to `plan` and `apply`.
- Persist quality profiles under `.meta/quality-profiles/`.
- Persist review artifacts under `reports/quality-reviews/<slug>/`.
- Extend descriptors with `quality_profile`, `quality_status`, `benchmark_sources`, `judge_reports`, `consumption_hints`, `quality_pass_count`, and `quality_stop_reason`.
- Extend the advisory handoff contract with `quality_status`, `benchmark_profile`, `preferred_use_cases`, `artifact_conventions`, `invocation_style`, and `requires_human_confirmation`.
- Architecture remains provider-only and keeps orchestration out of scope.

## Quality Rules
- Global default targets: 9/9/9 with no blockers.
- Architecture profile targets: 10/9/9 with no blockers.
- Thin or unresolved `manual_review` candidates must not auto-land.
- Metadata cannot compensate for a weak prompt body.
- Quality review artifacts must be inspectable without mutating generated vendor homes.

## Acceptance
- Rich architecture exemplar reaches `ship` under the architecture profile.
- Structured generic source can refine into `ship` under the default profile.
- Thin source is refused and stays `manual_review`.
- Build and strict validation pass after integration.
