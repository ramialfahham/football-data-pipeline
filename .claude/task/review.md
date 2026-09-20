# Review — feat/109-every-column-described — 2026-09-20

diff_sha256: 441f7036fc083781cd25cbfe0666c9a6dc1bbc6e3c7b9a10d53c1213475e1809

rounds: 2

Round 2 (delta): the new `entity_type` block said "NULL when the league_code is absent from the
registry …" while eight sites referencing it keep `not_null` (verdict then: FAIL by the warehouse
reviewer). Resolved by correcting the sentence, not the tests: the block now states the Required
class — never NULL for a tracked competition, a NULL is a registry defect the not_null tests guard —
and `mart_player_profile.entity_type`'s qualifier introduces its silent blank-type case as a form of
that defect. Two hunks; no test moved. The platform reviewer's round-1 pass stands untouched (no
delta in its territory).

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2: both hunks read; the block no longer asserts a NULL path; the qualifier names the same
  registry-gap case as a defect; the `tests:` list beneath it is byte-identical; no other file,
  `tests:` line, scope path or mechanism touched; `decisions_taken` ("a not_null a NULL sentence
  contradicts comes off; no other test moves") still holds — the resolution corrected the sentence
  rather than exceeding the decision.
- Round 1: every touched file is in `scope_paths` (the five untouched scope paths had no blank
  columns); no `not_null` or other test added or removed anywhere in the yml diff; no `.sql`, no
  seed; §3.5's edit is one bullet; exactly 54 new `{% docs %}` blocks; the `NOT POLICED` line's
  issue-number drop is explained and its test updated, not loosened; the three adjusted tests are
  tightenings; no secrets; `_column_coverage` is a rule inside existing machinery, no new mechanism
  or cost.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 2: the reworded block classifies `entity_type` as Required and names the registry defect the
  not_null tests guard; traced every site WITHOUT a not_null — the season and record models, the
  benchmark long form, `int_legs__team_from_players` (`any_value`), `mart_team_season_record`,
  `mart_standings` and `mart_player_career` (re-derived through the identical registry →
  competition_types left join), `mart_competition_season_summary` — none produces a legitimate
  NULL; the `mart_player_profile` qualifier is one mechanism under the same umbrella; the closing
  sentence names test enforcement by category, not a consumer, so §2's ban is not touched.
- Round 1, the finding: the eight not_null sites against a "NULL when" sentence.
- Round 1, passed: the thirteen `*_sum_season` blocks' NULL rules against
  `int_team_season__metrics_cumulative.sql:58-90` (whole-season blank on one missing non-awarded
  match vs never-NULL pass-through for the raw counts); `season_games_played__whole_season`,
  `stat_coverage_season_games`, `games_with_team_stats__season` against the two metrics models;
  the five streaks line by line against `int_team_profile__streaks.sql:71-82`;
  `window_type__season_record` against both int (literal `season_to_date`) and both mart
  (`season_to_date` / `prev_season`) models; the three `__leg` player-count blocks against
  `stg_apif__fixture_players.sql:53-56` and the catalogue (penalties in, own goals out, NULL on an
  omitted object); the `league_code` split (`stg_apif__players` / `base_apif__player_team_season`
  on the competition block is defensible: a squad row applies to every tracked competition the
  team enters); the dimension copies pair no not_null with a NULL claim; no `.sql` touched.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 (no delta since): the five new tests each go green if `_column_coverage` is reverted, so
  none is vacuous; `main()` order unparseable → object coverage → blocks → shared → column coverage
  → description floor → content rules, the parse failure returning before the column floor; the
  three adjusted tests still prove their docstrings and are tightenings; `_ambiguous_names` parity
  tests unaffected by the renamed fixture; only the two files in this territory touched, the CI and
  stop-gate wiring unchanged; the dropped blank-count in `NOT POLICED` is safe because a blank on an
  ambiguous name now returns earlier as a finding; nameless / non-dict / `columns: null` entries
  skipped as the pre-existing rules do and rejected by `dbt parse` first; ruff-clean under
  `.ruff-ci.toml` by inspection.

## escalations
(none)
