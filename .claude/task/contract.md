# Task contract — #69 step 5 (country FKs) + #62 step 3 (mart_competition_index)

objective: >
  Wire the four free-text country columns (`dim_league.league_country`, `dim_team.team_country`,
  `dim_player.player_birth_country`, `dim_coach.coach_birth_country`) to `dim_country` via
  relationships tests (#69 step 5), which is what deletes `competition_types.single_country` and
  makes "which relationship is populated" a real, enforced answer instead of a hand-typed flag.
  Then unpark and fix `mart_competition_index` (#62 step 3), the single mart the competitions page
  (#54) will read, whose `region_label` column was blocked on exactly this flag.
refs: GitLab #69 (country/region dims, step 5 of its own order of work), #62 (step 3 of 5), #54
  (page design, the region-resolution note)

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__leagues.sql
  - dbt_project/models/2_base/api_football/base_apif__teams_global.sql
  - dbt_project/models/2_base/api_football/base_apif__coaches.sql
  - dbt_project/models/2_base/api_football/base_apif__player_profiles.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/3_core/dim_country.sql
  - dbt_project/models/3_core/dim_region.sql
  - dbt_project/models/5_marts/shared/mart_competition_index.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/competition_types.csv
  - dbt_project/seeds/confederations.csv
  - dbt_project/seeds/schema.yml
  - .claude/active_work.md

impact_map: >
  writers: `league.country` is written by `ingestion/api_football/loads/catalog.py:38` into
    `RAW_APIF_LEAGUES`; `team_country`/`player_birth_country`/`coach_birth_country` by the
    teams/players-profiles/coaches loaders into `RAW_APIF_TEAMS`, `RAW_APIF_PLAYER_PROFILES`,
    `RAW_APIF_COACHES` respectively. None of those loaders change here — only the base-layer
    reconciliation (seed join) applied to the values already landing.

  downstream (dbt 1.7.19, .venv/Scripts/dbt.exe, run 2026-08-17, `dbt ls --select <model>+`,
    pasted verbatim):

    base_apif__leagues+ (17 models) includes mart_competition_index (this task's new leaf, already
    dependent because it's staged), mart_fixture_standing_context, mart_matchday_insights,
    mart_roster, mart_standings, mart_team_profile, mart_team_season, mart_team_season_insights,
    dim_league, dim_competition_season, dim_player_team_season_mapping, fct_standings,
    int_team_season__deserved_vs_actual, int_team_season__standings_primary,
    base_apif__league_entity, base_apif__competition_seasons.

    base_apif__teams_global+ (19 models) includes dim_team, dim_player_team_season_mapping, and
    every mart that reads dim_team: mart_fixture_standing_context, mart_matchday_insights,
    mart_player_career, mart_player_fixture_stats, mart_player_match_log, mart_player_profile,
    mart_roster, mart_standings, mart_team_competition_benchmarks, mart_team_fixture_stats,
    mart_team_fixtures, mart_team_market_value, mart_team_momentum_window, mart_team_profile,
    mart_team_season, mart_team_season_insights.

    base_apif__coaches+ (2 models): base_apif__coaches, dim_coach. Nothing reads
    dim_coach.coach_birth_country downstream yet — grep confirms zero hits outside dim_coach
    itself and this contract's own core.yml edit.

    base_apif__player_profiles+ (10 models) includes dim_player and the marts that read it:
    mart_leaderboards, mart_player_career, mart_player_competition_benchmarks,
    mart_player_fixture_stats, mart_player_match_log, mart_player_profile, mart_roster,
    mart_team_momentum_window.

    mart_competition_index+ (1 model): itself only — confirmed LEAF, step 4 (export repoint)
    has not landed.

  blast_radius: every downstream consumer of team_country/player_birth_country/coach_birth_country
    was checked (`grep -n` across `dbt_project/models/5_marts/`) and every hit is a plain
    SELECT/pass-through display column — mart_player_career, mart_player_profile,
    mart_team_market_value, mart_team_profile, mart_team_season, mart_team_season_insights. None
    joins or filters on the column's string value, so correcting the spelling changes what
    renders, never which rows join. league_country gains new NULLs (the 24 international rows,
    previously the literal string `'World'`) — grep confirms nothing downstream reads
    league_country today (mart_competition_index, staged in this same commit, is the first real
    reader), so this is additive rather than a behaviour change to a shipped feature.
    `single_country` is deleted from `competition_types.csv`; grep confirms its only reader
    anywhere in the repo was the parked (uncommitted) mart being fixed in this same task.

  layer_rules: `scripts/check_layer_contract.py`. The override join is applied in BASE
    (`feedback_entity_corrections_in_base`: base prepares, the core dim publishes) — same pattern
    `base_apif__leagues.sql` and `base_apif__teams_global.sql`'s `team_name_overrides` join already
    use, applied to a second/third/fourth column rather than a new mechanism. `mart_competition_index`
    reads only core dims and seeds (`dim_league`, `fct_fixture`, `competition_registry`,
    `competition_types`, `confederations`), never staging or raw — the marts layer rule holds.

  deploy_order: base and staging are TABLES, so corrected values land on the next
    `data:build:main` after merge; until then the four dims keep today's provider spellings, which
    nothing downstream reads by predicate (see blast_radius). The new relationships tests run in
    the same build and are what actually proves the override coverage — `data:build:mr` on this
    MR's pipeline is the first real check. `mart_competition_index` is additive (new table); its
    reader (#62 step 4, `export_site_data.py`) is explicitly NOT in this task and ships after this
    merges and prod rebuilds.

decisions_taken: >
  CPO ruling 2026-08-16 (#69, quoted on the issue): "These things should have been already decided
  in cleanly defined dimensional tables with clear columns. You don't mix up countries and
  continents or regions in one column and add a flag 'single country'. That's really bad
  modeling." This is the ruling `single_country` is deleted under.

  CPO ruling 2026-08-16 (#69, canonical names note): the 225-entry canonical country list, the
  "official form" (UN English short name) rule, and the Ireland/Yugoslavia exceptions are already
  approved and already built into `countries.csv` + `country_name_overrides.csv` on main (merged
  in `!61`). Nothing about the NAMES is decided in this task — this task only WIRES the existing,
  CPO-approved seed to the three remaining surfaces and adds the foreign keys #69's own "order of
  work" lists as step 5.

  MEASURED (#69 note, 2026-08-16, priced with `bq query --dry_run`, 474,334 bytes): `league.country`
  carries the literal sentinel `'World'` for exactly 24 rows, all international/continental
  competitions, and `'World'` appears on no other surface. Under the two-dimension model those rows
  carry no country and take their region from `confederation` instead — so `league_country` becomes
  NULL for them rather than a corrected string. This is re-verified fresh in this task's `done_when`
  before pushing, since the note is a day old and league onboarding has changed counts before.

  WHERE THE REGION BRANCH LIVES (#54 note, 2026-08-16, and #69's rescope note): "which relationship
  is populated IS the answer" — `mart_competition_index.region_label` branches on
  `leagues.league_country is not null`, not on a competition_type-level flag. This mart already
  reads `dim_league` (parked, unpark unchanged), so no new join is added — only the case
  expression's condition changes.

  NEW MECHANISM: none. `country_name_overrides` applied in base is the same three-part pattern
  (seed + left join + coalesce) `team_name_overrides` already uses in the same two files
  (`base_apif__leagues.sql`, `base_apif__teams_global.sql`); this task only widens its application
  to the two files that don't have it yet (`base_apif__coaches.sql`, `base_apif__player_profiles.sql`)
  and adds the World-sentinel case on the one surface that needs it. RECURRING COST: none — no new
  seed, no new schedule; `confederations.csv` and `country_name_overrides.csv` already exist.

decisions_reserved:
  - none: this task executes #69's own already-approved "order of work" step 5 and #62's already
    -designed step 3 as parked on 2026-08-16. No new CPO-class question surfaces in wiring an
    approved FK or fixing a case expression to match an approved rule.

done_when:
  - `dbt parse` succeeds against the full changed model set.
  - SQLFluff clean, full rule set, from the repo root, on every changed `.sql` file.
  - `dbt ls --select mart_competition_index+ --resource-type model` still returns only itself
    (still a leaf — step 4 has not landed).
  - A fresh priced `bq query --dry_run` + real read confirms `'World'` is still exactly the
    international/continental league rows and nothing else on the league surface.
  - A priced read-only query simulating the override join for team/player/coach against RAW or
    staging confirms zero values fail to resolve against `countries.csv`'s canonical set (proves
    the new relationships tests will pass in CI before pushing, rather than discovering it after).
  - `grep -rn "single_country" dbt_project/ .claude/` returns no live column reference — only
    historical-rationale prose, if any, explaining why it was removed.
  - `.claude/active_work.md` updated in this same commit, `len()` under 16,000 characters, rebased
    on the 2026-08-17 #74 handover-pointer update (main @ 67924ef) so a parallel session's edit
    isn't clobbered.
  - CI's `data:build:mr` (the actual dbt build + the new relationships tests, on real BigQuery) is
    the authoritative pass/fail for the FK coverage claim above — this task never runs `dbt build`
    locally.

amendments: (none)
