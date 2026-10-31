# Verification — teams level on points stand in their league's tie-break order

Read on prod on 2026-10-31, read-only, each query dry-run first. The SQL is the branch's compiled
`int_team_season__table_by_time`, `int_standings__official_rank` and
`assert_standings_rank_follows_league_rule`, pointed at the prod tables, with the rebuilt table
recomputed from `int_team_season__table_state` and `int_team_season__table_legs` because prod
does not yet carry `place_by_rules`. No `dbt build` was run.

criteria_demonstrated:
  - Rule order on the Table page: `mart_standings` reads `int_standings__official_rank`, which orders a section by `place_by_rules` wherever every team's matches played and points equal the provider's row. Today every section with a rule table is compared in all 15 leagues: BL1 10, BL2 5, BPL 1, BSA 5, ED 5, EKS 5, J1 4, L1 11, LP 5, MLS 10, PD 10, PL 11, SA 11, SPL 5, TSL 5. The rules were checked against the leagues' own sources for Liga Portugal (ligaportugal.pt tables by round) and the Saudi Pro League (SPL Handbook 2026-27, Article 9.2), recorded on #237.
  - Teams the rule cannot separate: they share `place_by_rules`, and the order falls back to the provider's `standing_rank`, then `team_sk`.
  - Same place on every page: `mart_next_matchday` and `int_team_season__standings_primary` read the same model, so `mart_team_competitions`, `mart_fixture_standing_context`, `mart_team_season.latest_rank` and the match page read the Table page's place; `assert_one_match_that_matters_per_competition` reads it too.
  - The test: the compiled `assert_standings_rank_follows_league_rule` returns 0 rows on prod. It fails a compared section where a placed team is served off its rule place, or where the served places do not run 1 to n.
  - Places that change, per league, measured on prod before the change: none today in any of the 15 leagues; the provider's current order of teams level on points matches the rule. The stored provider tables of the season show where it did not: Liga Portugal 132 places on 35 tables (latest 2026-10-25), Saudi Pro League 50 places on 11 tables (latest 2026-10-22).
  - R7 and docs/metric_layer.md: both now say that teams level on points stand in the league's tie-break order.

dbt parse passes; SQLFluff passes on every changed SQL file; the offline gates of validate-local pass.
