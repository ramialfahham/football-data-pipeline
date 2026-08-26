# Review — chore/refresh-export-sample-after-90 — 2026-08-26

diff_sha256: c987a67a9e2d6d2cc5005986873d828c8c70cefa5850785b9c8245a9c419ffad

rounds: 1

<!--
Required reviewer set computed from .claude/review_routing.json against the staged paths:
  scope-auditor        always
  bi-analyst-reviewer  site_v2/src/**
`site_v2/src/data/**` is in review_summarise_paths, so the 746 KB payload is summarised in the
patch rather than pasted. No guard path is staged, so no opus promotion; both run on the pinned
sonnet. Verdicts are appended below as each blinded reviewer returns; none is written by the
builder.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: diff touches only `site_v2/src/data/teams/33.json` plus the standard task-artifact set.
  All within `scope_paths`; no script, model, `.gitignore` or frontend source edited — matches the
  contract's explicit "NO script, NO model, NO frontend source" note.
- Credentials/secrets: grepped `teams/33.json` for key/token/secret/password/Authorization/Bearer
  patterns — only legitimate data fields (`key_passes_per_match` etc.) matched.
- Undeclared threshold crossing: `decisions_taken` declares both CTO thresholds explicitly as
  "none"; verified the impact_map's per-mart `bq --dry_run` sizes sum correctly and read as a
  one-time cost, not recurring.
- §10 "permanent once published" (slug/name): `dim_team.team_slug` for team 33 changed from
  `manchester-united` to `manchester-united-fc` in the refreshed payload (confirmed by reading the
  file directly). Disclosed prominently in `decisions_reserved`, not decided or silently shipped as
  policy, and the "no page links to a team page today" claim is independently confirmed in
  `site_v2/src/data/README.md:30`, so no internal link breaks and `audit-seo.mjs` cannot fire on
  it. Correctly deferred rather than smuggled.
- Data honesty: verified in the raw JSON that PL2026 (1 game played) carries `"benchmarks": []` and
  PL2025 (38 games) carries the 22-row benchmark list including `metric_key: "clean_sheets_share"`
  — matches the contract's corrected acceptance criteria.
- Doc-sync: `README.md`'s stale "18 files" count predates this diff and is unrelated; the README is
  untouched and its documented refresh procedure is exactly what was followed.
- `decisions_reserved` integrity: cross-checked each reserved item against the diff and found none
  silently decided inside this commit.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule / fabrication risk on the changed sample: read `teams/33.json` directly and traced
  every renamed field back to its dbt source rather than trusting the contract's prose.
  `mart_team_profile.sql:86` (the count, untouched) and `:140-142`, plus
  `int_team_profile__yoy.sql:91,111,131` and
  `int_team_competition_benchmark_metrics_long.sql:34`, confirm these are real already-merged
  warehouse columns, not something typed into the sample. `export_site_data.py` is a `select *`
  pass-through with no per-metric hardcoding, so the export is structurally capable of producing
  every field found — no fabrication.
- Frontend binding still resolves against the new sample: `metricRows.ts:83-84` binds the team
  surface to `clean_sheets_share`, exactly the `metric_key` value and key stem in the JSON;
  `strings.ts` resolves `metrics.clean_sheets_share.label` in all three locales — no
  falling-back-to-English and no dangling key.
- Numeric self-consistency, re-derived rather than trusted from `acceptance_evidence.md`: old
  `metric_key` = 0, new = 22, total `metric_key` = 466, `clean_sheets_share_*` = 75 (3×25 seasons),
  `clean_sheet_run` = 25/25, and 22 non-empty benchmark seasons = 25 minus 3 with `benchmarks: []`.
  Every number in the artifact checks out against the file.
- Scope leakage / stale data across the rest of the sample: grepped all of
  `site_v2/src/data/**/*.json` — the 17 fixture payloads legitimately carry `clean_sheets` as an
  unrelated count from `mart_team_momentum`/`mart_team_season_record`, and no file anywhere carries
  a stale yoy key or old `metric_key`. Consistent with "exactly one tracked file".
- `rendered_page_evidence.md`: present and states its method (built `dist/` HTML, comments
  stripped, not source/`outerHTML`/screenshot) and what it does and does not show. Verified against
  `TeamPerformance.astro:35-40,75-131` that `hasBench` gates BOTH panels together, which matches
  the reported all-zero-rows state for the featured season — no naked or fabricated percentage is
  shown; the honest-absent path fires as described.
- Slug/name drift: verified it is served verbatim from `mart_team_profile.team_slug`/`team_name` by
  `export_site_data.py:331-335` (no export-layer identity generation), not fabricated by this diff,
  and correctly disclosed rather than silently shipped.

## escalations
(none)
