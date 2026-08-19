# Task contract — extend team_name_overrides beyond collision-only corrections

objective: >
  The existing `team_name_overrides` seed only corrects a provider team_name when it COLLIDES
  (two real clubs share the identical bare string) — 9 pairs fixed this way (#850/#851). CPO
  ruling this session: that bar is too narrow. A name can be unique in our data and still be
  wrong to show bare — "Arsenal" is not the display name, "Arsenal FC" is. Extends the same,
  already-proven mechanism to non-colliding-but-incomplete provider names, verified externally
  per row exactly like the existing 9.
refs: dbt_project/seeds/team_name_overrides.csv (existing mechanism); base_apif__teams_global.sql
  header comment (why this field matters — drives fixture card, H1, title, meta, URL slug).

scope_paths:
  - dbt_project/seeds/team_name_overrides.csv
  - dbt_project/seeds/schema.yml
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: dbt_project/models/2_base/api_football/base_apif__teams_global.sql (the only place
  this seed is joined — coalesce(overrides.team_name, teams.team_name)).

  downstream, ACTUAL pasted output (`dbt ls --select base_apif__teams_global+ --resource-type
  model`, run from dbt_project/, 2026-08-19 — round-1 review FAILed the prior version of this
  field for asserting a hand-typed list instead of pasting real command output; this replaces it):

    Found 97 models, 936 tests, 9 seeds, 11 sources, 0 exposures, 0 metrics, 851 macros, 0 groups
    football_data_pipeline.2_base.api_football.base_apif__teams_global
    football_data_pipeline.3_core.dim_player_team_season_mapping
    football_data_pipeline.3_core.dim_team
    football_data_pipeline.5_marts.shared.mart_fixture_standing_context
    football_data_pipeline.5_marts.domestic_league.mart_matchday_insights
    football_data_pipeline.5_marts.shared.mart_player_career
    football_data_pipeline.5_marts.shared.mart_player_fixture_stats
    football_data_pipeline.5_marts.shared.mart_player_match_log
    football_data_pipeline.5_marts.shared.mart_player_profile
    football_data_pipeline.5_marts.shared.mart_roster
    football_data_pipeline.5_marts.shared.mart_standings
    football_data_pipeline.5_marts.shared.mart_team_competition_benchmarks
    football_data_pipeline.5_marts.shared.mart_team_fixture_stats
    football_data_pipeline.5_marts.shared.mart_team_fixtures
    football_data_pipeline.5_marts.shared.mart_team_market_value
    football_data_pipeline.5_marts.shared.mart_team_momentum_window
    football_data_pipeline.5_marts.shared.mart_team_profile
    football_data_pipeline.5_marts.shared.mart_team_season
    football_data_pipeline.5_marts.domestic_league.mart_team_season_insights

  18 downstream models total (16 marts + dim_team + dim_player_team_season_mapping), out of 97
  models in the whole project — effectively the entire team-keyed mart surface, confirmed by the
  real select, not remembered. Full node count including tests: 297 (`dbt ls --select
  base_apif__teams_global+` unfiltered). Plus dim_team's own `unique_dim_team_team_slug` test and
  the seed's own `relationships_team_name_overrides_team_api_id__team_api_id__ref_dim_team_` FK
  test, both visible in that unfiltered count.

  layer_rules: correction applied in base (2_base), matching the CPO's 2026-07-27 ruling that base
  is where these preparations happen and core.dim_team publishes the settled result — no change to
  that pattern, only more rows in the same seed. blast_radius: team_name AND team_slug change for
  every corrected team_api_id (`team_slug` is derived FROM team_name in the same model, e.g.
  Arsenal's slug likely moves from `arsenal` to `arsenal-fc`). Acceptable now: site_architecture.md
  §3 states slugs are explicitly NOT yet stable pre-launch, no page is indexed, no link equity
  exists to lose. Would NOT be acceptable post-launch without #852 (slug persistence) landing
  first. No other model outside the team surface reads team_name.

decisions_taken: >
  CPO, this session, verbatim: "The name is Arsenal London and not Arsenal England. We have to fix
  and standardize these names... it's not Arsenal London. It's Arsenal FC. But it's Inter Milan...
  we have to define the name we use as the single source of truth for what we display." Each row
  added here is independently sourced against English Wikipedia's article title for the club
  (the same convention the existing 9 rows already use), pasted as a citation, not asserted.

decisions_reserved:
  - How far beyond the 9 teams checked so far this sweep goes (rest of Pool 1, then possibly wider)
    is being decided iteratively in chat with the CPO, not pre-committed here.

done_when:
  - Every new row cites its English Wikipedia source URL in the `source` column, matching the
    existing 9 rows' format.
  - `dbt test --select team_name_overrides assert_team_name_overrides_still_needed
    unique_dim_team_team_slug` passes (needs a `dbt build`/`run` first to materialize dim_team with
    the new coalesce — flagged for the CPO: this is the one case that needs an actual warehouse
    build to verify, not just parse/compile, given CLAUDE.md's standing "never run dbt build"
    guidance; confirm before running one).
  - Committed on this branch; MR opened by the post-commit hook.

amendments:
  - 2026-08-19: + `dbt_project/seeds/schema.yml` — authority: analytics-engineer-reviewer round-1
    FAIL. The seed's own schema docs (model description + the `note` column's stated contract)
    still described the old collision-only rule; this diff broadens the rule and several new rows
    say so explicitly in their own note text, so the docs now contradicted the majority of the
    data they govern. Updating the description to state both triggers (collision, and — new —
    incompleteness against an external source), not just the original one.
  - 2026-08-19: impact_map's downstream field replaced — scope-auditor round-1 FAIL. It claimed
    "pasted evidence" but was a hand-typed prose list from memory, not actual command output. Now
    real `dbt ls` output, run this session, pasted above.
