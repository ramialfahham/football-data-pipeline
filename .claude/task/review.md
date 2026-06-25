# Review — refactor/500-metric-dedup-team — 2026-06-25 (#500 PR1: team metric consolidation)

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged branch diff
> (`.claude/task/review_input.patch`). Required set for the staged paths (dbt_project/** +
> scripts/export_*.py + dbt_project/tests/**): scope-auditor (always) + analytics-engineer-reviewer
> (dbt) + cto-reviewer (export + tests). No football-analytics/data-engineer/bi-analyst (no
> metric_catalogue, ingestion, or wireframe path touched).

diff_sha256: 9606dd885a4be10b7a47c610093fa0f81f689ffadbcaa829153b687bf6d4113c

## verification
Byte-identical proof (MVP-safe): a row-level JSON value diff of the NEW int_team_season__metrics
projection (computed read-only from prod base tables) vs the CURRENT prod table, over ALL 12,537
team-seasons x 48 output columns = **0 mismatches** (0 only_in_old, 0 only_in_new). The check
surfaced + fixed 2 subtleties before passing: (1) the 9 displayed team-feed `_sum_season` columns
must be NULL-gated on partial coverage (matching the original's season_gated CTE); (2) shot_accuracy
must gate on team coverage too, not just SoT (4 old team-seasons carry shots_on_goal with null
shots_total). mart_team_momentum is the verbatim original (rename + ref only); the W2 mart
(mart_team_season_record) composes the verified projection and emits the SAME output column set as
the original (confirmed: neither emits raw goals_for/goals_against).

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every edited file is in scope_paths (or is the artifact contract.md); the two amendments
  (macro dropped per CPO; the no-drift guard test + 4 prose-only fold-in files added) are clean-tree
  and CPO-authorised.
- Compose-pattern correctness: int_team_season__metrics is the final row per (team, league, season) of
  int_team_season_record (qualify) — correct grain; mart_team_season_record renames `_season`->display
  transparently and does NOT recompute; the team-feed NULL gates propagate through the compose.
- Contract honesty: the `_season` suffix is NOT dropped (live JSON keys preserved); the narrative
  (inline SQL, composition, no macro) matches the code, with no stale macro references contradicting it.
- Rename completeness: grep confirms zero surviving refs to the 4 old names in any .sql/.yml/.py; the
  orphaned old BQ tables are harmless and flagged for a one-time post-merge drop.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Byte-identical of the 9 team-feed `_sum_season` outputs + shot_accuracy: the projection NULL-gates the
  displayed team-feed sums on partial coverage and double-gates shot_accuracy (SoT + team), reproducing
  the original's season_gated behaviour (the 2 documented fixes; 0/12537 confirmed).
- save_ratio denominator: new divides by goalkeeper_saves + goals_against_in_save_games vs the old
  goalkeeper_saves_sum + goals_against (total). Byte-identical — both NULL on partial save coverage (the
  old numerator was gated), and when fully covered `sum(if(saves is not null, goals_against, null)) ==
  sum(goals_against)`. Reasoning sound, no counter-example.
- Compose correctness: every `_season` column mapped to its display name; games_played/W-D-L/clean_sheets/
  entity_type/games_with_team_stats reproduced; the current-else-previous-season selection
  (`season_api_year in (year, year-1)` + priority qualify) is equivalent to the original's two UNION branches.
- season_matchdays_used equivalence: new computes count(distinct round_name) from int_legs__team_match over
  the same (team, league, season) partition as the original's in-aggregation count — equivalent.
- Guard governance: entity_type (dimension) + games_with_team_stats (coverage count) are non-metrics,
  correctly added to the no-drift exempt set; the models list (player + team) is unchanged.
- Layer + completeness: no intermediate ref('mart_*'); mart_team_momentum is the verbatim original; rename
  complete across refs + yml `- name:` entries (renamed models keep their tests); export_site_data.py is a
  pure table-name swap (no derived facts).

## cto-reviewer
VERDICT: PASS
risks_checked:
- export_site_data.py logic purity: the two changed reads are pure table-name swaps (mart_momentum__team
  -> mart_team_momentum, mart_season_record__team -> mart_team_season_record) inside `select *` + key-filter
  queries stored as lookup dicts; no computation/ranking/formula introduced; no credential change. The
  consumption-layer contract is intact.
- DQ test integrity: assert_no_uncatalogued_season_metric gains two correct non-metric exemptions
  (games_with_team_stats, entity_type); assert_tournament_form_window + assert_momentum_window_matches_momentum
  are pure ref()-name swaps with all assertion logic preserved — no DQ test weakened. No CI/hook/dep change.
- CARRIED: the cto-reviewed files (scripts/export_site_data.py + the 3 tests) are byte-identical between this
  locked hash and the first-pass review hash (7cc94ee3...); the only changes since were to the dbt projection,
  code comments, and the contract — none in the cto remit. Verdict carries.

## escalations
(none)
