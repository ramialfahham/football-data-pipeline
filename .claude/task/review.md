# Review — chore/rename-momentum-season-record — 2026-06-13

> CPO §10 naming ruling (Option 2, escalations.log 2026-06-13): the form-window model
> family adopts ONE root per concept — `momentum` (live form / last-5) and `season_record`
> (within-competition cumulative). PURE rename: 8 models + 1 test renamed, all refs/comments/
> consumers updated; NO SQL logic/grain/metric change. Boundaries kept: `window_type` VALUES
> (last_5/season_to_date/prev_season) and the published JSON key `form_window` are NOT renamed.
> Local validation: layer contract PASS, registry sync PASS, `dbt parse` PASS (all refs
> resolve), sqlfluff PASS on changed SQL. Required reviewers (routing): scope-auditor +
> analytics-engineer-reviewer + cto-reviewer + data-engineer-reviewer + bi-analyst-reviewer.
> One cold iteration: all five PASS against the hash below.

diff_sha256: 8e55b6cc209e621ee14366128ade80afa5415147191e0de53c2778da1796a2c9

## scope-auditor
VERDICT: PASS
risks_checked:
- §10/authorization + pure-rename trap: the naming choice is the CPO's (Option 2 recorded in
  escalations.log 2026-06-13), not the builder's. Spot-checked renamed SQL bodies — only model
  name, comments, and ref() targets differ; no filter/window/aggregate/grain/column smuggled
  under the rename.
- Boundary integrity + scope: the deliberately-KEPT items are kept — `window_type` values
  (last_5/season_to_date/prev_season) and the `form_window` JSON output key in
  export_site_data.py; no stale OLD model-name token in code or in-scope docs; no protected
  path touched; all changed files within scope_paths; excluded items (form_window_kind,
  int_matchday__player_form_window) absent from the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Logic drift: all 6 renamed model SQL bodies confirmed byte-identical to their predecessors
  (no CTE/filter/window/partition/aggregate/join/column change) — only comment + ref() strings.
- Ref-graph closure: grep across all .sql/.yml finds zero old-name occurrences; every consumer
  (int_momentum__team, mart_momentum_window__team, mart_season_record__{team,player},
  int_team_profile__yoy, the test, export, shared.yml name: entries) resolves to a new name
  with a matching file.
- window_type value integrity: 'season_to_date'/'last_5'/'prev_season' literals + the
  int_season_record.yml accepted_values are unchanged.
- DAG direction: no intermediate refs a mart; all models stayed in their layer.

## cto-reviewer
VERDICT: PASS
risks_checked:
- export_site_data.py: all three renamed-mart reads updated (mart_season_record__team x1,
  mart_momentum_window__team x2); zero old-name tokens in any .py; the `form_window` variable +
  JSON key preserved; mart_momentum__team/__player (not renamed) unchanged.
- Test rename integrity: assert_momentum_window_matches_momentum.sql present with correct new
  ref()s; assertion logic byte-identical; shared.yml cross-reference updated; no test-name
  collision. No stale old token in scripts/ or tests/.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Registry integrity: the ONLY competition_registry.yml change is one YAML comment-line model
  token; no provider_league_id/ingest_active/history_seasons/parent_competition/any data field
  altered; zero-file + ingest-cost rules unaffected.
- Accuracy + completeness: int_momentum_window__team exists and implements the recency-based
  selection the comment describes; repo-wide grep finds zero residual old-name refs in
  ingestion/ or scheduler workflows.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Display-contract integrity: `form_window[]` JSON key, `window_type` column + caption values
  (season_to_date/prev_season/last_5), the LOCKED team/player display tables, and the rulings
  log are all unchanged; only model-name identifiers changed.
- Stale-reference completeness: zero old-name tokens across the three wireframes; the four
  targeted refs updated (mart_season_record__team, int_momentum_window__team); GAP-18 remainder
  (incl. the orphaned wc_supporting_league_codes mention) left as-is per scope.

## escalations
(none — single cold iteration; all five routed reviewers PASS against the locked hash. Pure
rename: dbt parse confirms ref resolution; window_type values + the form_window JSON key
deliberately preserved per the recorded ruling. Old BQ tables become orphaned after the next
build — dropping them is a separate CPO-approved destructive cleanup, NOT in this PR.)
