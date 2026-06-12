# Review — docs/audit-doc-sync — 2026-06-13

> Issue #419: G4 audit batched stale-doc cleanup (F27–F37). Pure doc/comment/
> docstring fixes, no behavior change. F35 + F37 found already-correct, not touched.
> Required reviewers for the staged paths: scope-auditor (always) + analytics-engineer
> (layering.md + int models) + data-engineer (ingestion comments + registry).

diff_sha256: 4c7297590de682fc2d19f2de2ec5ab62cdd266fc94712261e2d6d62c6f251955

## scope-auditor
VERDICT: PASS
risks_checked:
- Grain accuracy in the expanded 19-mart inventory: sampled grains (mart_team_season,
  mart_season_to_date__team, mart_fixture_standing_context) against the model
  docstrings — all matched; the new claims are load-bearing descriptors of the actual
  schemas, not aspirational. No §10 decision is disguised as documentation.
- Materialization (view vs table) correctness + scope: spot-checked table/view claims
  against `config(materialized=...)`; all 8 changed files are within scope_paths; the
  diff changes only comments/docstrings/markdown/yaml-notes — no code logic, column,
  config value, or registry data field; the orphaned int_player_season__metrics model
  is NOT deleted (only its stale docstring corrected), honoring decisions_reserved.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Mart inventory exhaustiveness + materialization: enumerated all 19 `5_marts/**/*.sql`
  via glob and verified EACH model's `config(materialized=...)` against the inventory
  table — all 19 match (table/view correct); grains cross-checked against each model's
  inline `Grain:` docstring — all align. No phantom rows; no real mart omitted.
- Fact inventory + league_code exception: `fct_team_market_value_snapshot` row is
  accurate — grain `(team_sk, as_of_date, source_code)`, seed-sourced, no `league_code`
  column in the SELECT; softening "All facts propagate league_code" → "Most…" is
  warranted. The retired-consumer fix is correct: no `int_matchday__fixture_player_insights`
  .sql exists anywhere in models/; only the two stale docstrings were corrected, no logic.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Write-mode comment (F32): the corrected comment in catalog.py now reads WRITE_APPEND,
  matching the actual `append=True` passed to `load_json_to_bq`; the empty-payload guard
  is unchanged and its justification is now accurate. No code line changed.
- Quota-budget docstring (F33): `_fixture_fanout_http_estimate()` hard-returns 4 and its
  inline docstring already states predictions are not ingested; the corrected docstring
  ("4 calls — lineups, events, stats, players") now matches the runtime value (the old
  "5 incl. predictions" overstated budget by 20%). No predictions endpoint is called
  (no-API-predictions rule upheld). Behavior unchanged.
- Registry header (F34): all five #262 'Continental club showpieces' entries (LIBER,
  CAFCL, AFCCL, CCCU, CWC) carry `status: in_progress` / `ingest_active: true`, so the
  PLANNED→IN PROGRESS header is correct; only the comment line changed — no
  provider_league_id, history_seasons, or ingest_active field touched.

## escalations
(none — all three reviewers PASS.)
