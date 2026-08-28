{{ config(materialized='table') }}

{#
  Team profile (#324). One row per (team, competition-season): the full profile
  surface a team page renders. Composes existing season rollups and adds the two
  signature differentiators plus a lighter streaks layer.

  Table stakes (composed, not recomputed):
    - identity            dim_team
    - record / rank / form  mart_team_season (same-layer ref, the documented
                            layering exception — mart_team_season_insights does
                            the same)
    - season metric rates  int_team_season__metrics

  Differentiators:
    - Vs own history — matchday-aligned year-over-year (this season vs last,
      through the same matchday), domestic leagues only, from
      int_team_profile__yoy. NULL for non-domestic competitions and where the
      prior season is not ingested (history_seasons = 1).
    - Streaks (lighter layer) — trailing unbeaten / win / winless / clean-sheet /
      scoring runs from int_team_profile__streaks.

  Grain: (team_sk, season_sk).
#}

with metrics as (
    select * from {{ ref('int_team_season__metrics') }}
),

team_season as (
    select * from {{ ref('mart_team_season') }}
),

teams as (
    select * from {{ ref('dim_team') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

yoy as (
    select * from {{ ref('int_team_profile__yoy') }}
),

streaks as (
    select * from {{ ref('int_team_profile__streaks') }}
),

deserved as (
    select * from {{ ref('int_team_season__deserved_vs_actual') }}
)

select
    m.team_sk,
    m.season_sk,
    m.league_sk,
    m.league_code,
    m.season_api_year,
    reg.competition_type,
    -- identity
    t.team_name,
    -- the permanent URL segment; carried so the export can SELECT it rather than compute a
    -- slug of its own, which would be identity derivation in the consumption layer (#846)
    t.team_slug,
    t.team_code,
    t.team_country,
    t.team_logo_url,
    -- founded year + venue (GAP-01); from the same dim_team join
    t.team_founded_year,
    t.venue_name,
    t.venue_city,
    t.venue_capacity,
    -- record / rank / form
    ts.played,
    ts.wins,
    ts.draws,
    ts.losses,
    ts.goals_for,
    ts.goals_against,
    ts.goal_diff,
    ts.points,
    ts.clean_sheets,
    ts.latest_rank,
    ts.latest_form,
    -- season metric rates
    m.season_games_played,
    m.stat_coverage_season_games,
    m.goals_per_match,
    m.goals_against_per_match,
    m.shots_per_match,
    m.shots_on_goal_pct,
    m.shots_inside_box_pct,
    m.finishing_efficiency,
    m.passes_accuracy_pct,
    m.passes_per_match,
    m.corners_per_match,
    m.corners_against_per_match,
    m.saves_pct,
    -- GAP-13: locked-contract season variants (player-derived ones inherit
    -- player-stat coverage gaps; caption from player_stat_coverage_season_games)
    m.player_stat_coverage_season_games,
    m.shots_on_goal_per_match,
    -- the on-target pair behind deserved-vs-actual. Gated upstream in
    -- int_team_season__metrics_cumulative and never re-gated here:
    -- shots_on_goal_against_per_match is NULL unless OPPONENT shots-on-target data
    -- covers every season game; sot_difference_per_match needs BOTH sides covered.
    m.shots_on_goal_against_per_match,
    m.sot_difference_per_match,
    m.passes_key_per_match,
    m.duels_per_match,
    m.duels_won_pct,
    m.defensive_actions_per_match,
    -- shooting dominance + results efficiency (catalogued season metrics)
    m.shots_share_pct,
    m.points_capture_pct,
    -- year-over-year (domestic only; NULL otherwise / when prior season absent)
    y.yoy_games_played_cutoff,
    y.points_this_season,
    y.points_prev_season,
    y.points_delta_yoy,
    y.goals_for_this_season,
    y.goals_for_prev_season,
    y.goals_for_delta_yoy,
    y.goals_against_this_season,
    y.goals_against_prev_season,
    y.goals_against_delta_yoy,
    -- rate-metric YoY: matchday-aligned this/prev/delta for the LOCKED 16-row display set — the
    -- data for the team Stats tab's per-metric vs-last-season column. All simple passthrough from
    -- int_team_profile__yoy (the deltas were computed there).
    y.goals_per_match_this_season,
    y.goals_per_match_prev_season,
    y.goals_per_match_delta_yoy,
    y.goals_against_per_match_this_season,
    y.goals_against_per_match_prev_season,
    y.goals_against_per_match_delta_yoy,
    y.clean_sheets_pct_this_season,
    y.clean_sheets_pct_prev_season,
    y.clean_sheets_pct_delta_yoy,
    y.shots_per_match_this_season,
    y.shots_per_match_prev_season,
    y.shots_per_match_delta_yoy,
    y.shots_inside_box_pct_this_season,
    y.shots_inside_box_pct_prev_season,
    y.shots_inside_box_pct_delta_yoy,
    y.shots_on_goal_per_match_this_season,
    y.shots_on_goal_per_match_prev_season,
    y.shots_on_goal_per_match_delta_yoy,
    y.finishing_efficiency_this_season,
    y.finishing_efficiency_prev_season,
    y.finishing_efficiency_delta_yoy,
    y.duels_per_match_this_season,
    y.duels_per_match_prev_season,
    y.duels_per_match_delta_yoy,
    y.duels_won_pct_this_season,
    y.duels_won_pct_prev_season,
    y.duels_won_pct_delta_yoy,
    y.defensive_actions_per_match_this_season,
    y.defensive_actions_per_match_prev_season,
    y.defensive_actions_per_match_delta_yoy,
    y.passes_per_match_this_season,
    y.passes_per_match_prev_season,
    y.passes_per_match_delta_yoy,
    y.passes_accuracy_pct_this_season,
    y.passes_accuracy_pct_prev_season,
    y.passes_accuracy_pct_delta_yoy,
    y.passes_key_per_match_this_season,
    y.passes_key_per_match_prev_season,
    y.passes_key_per_match_delta_yoy,
    y.corners_per_match_this_season,
    y.corners_per_match_prev_season,
    y.corners_per_match_delta_yoy,
    y.corners_against_per_match_this_season,
    y.corners_against_per_match_prev_season,
    y.corners_against_per_match_delta_yoy,
    y.saves_pct_this_season,
    y.saves_pct_prev_season,
    y.saves_pct_delta_yoy,
    -- streaks (trailing run as of the latest match)
    s.unbeaten_run,
    s.win_run,
    s.winless_run,
    s.clean_sheet_run,
    s.scoring_run,
    -- deserved-vs-actual (points-space; DOMESTIC LEAGUES only, so NULL for every tournament row --
    -- a within-group standing is not a comparable league position). The "actual" points are
    -- `points` above; the "actual" rank is latest_rank (same source: standings_primary).
    -- sot_points_gap is NEGATIVE when under-performing, the inverse of the retired sot_rank_gap.
    -- All three null together. They are withheld for any table that is not a single ladder (MLS
    -- conferences, Apertura/Clausura), because there the actual rank is a within-section position
    -- and, for the split formats, the season points total sums two separate tournaments.
    d.deserved_points,
    d.deserved_rank,
    d.sot_points_gap,
    -- The season this team's page opens on (#846). Exactly one row per team is true: the most
    -- recent DOMESTIC LEAGUE season, falling back to the most recent season of any type for a team
    -- with no league season. Ruled a warehouse fact (CPO 2026-08-02), so the export and the page
    -- SELECT this flag instead of each re-deciding it; three copies of the rule had already
    -- drifted apart. Last in the list because ST06 puts calculations after simple targets.
    row_number() over (
        partition by m.team_sk
        order by
            case when reg.competition_type = 'domestic_league' then 0 else 1 end asc,
            m.season_api_year desc
    ) = 1 as is_featured_season
from metrics as m
left join team_season as ts
    on m.team_season_sk = ts.team_season_sk
left join teams as t
    on m.team_sk = t.team_sk
left join registry as reg
    on m.league_code = reg.league_code
left join yoy as y
    on
        m.team_sk = y.team_sk
        and m.league_code = y.league_code
        and m.season_api_year = y.season_api_year
left join streaks as s
    on
        m.team_sk = s.team_sk
        and m.season_sk = s.season_sk
left join deserved as d
    on
        m.team_sk = d.team_sk
        and m.season_sk = d.season_sk
