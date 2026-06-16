{{ config(materialized='table') }}

{#
  W1 momentum-window selection — team.

  One row per (upcoming fixture side, window leg), kept UN-aggregated so the momentum aggregate
  (int_momentum__team) and its drill-down list (mart_momentum_window__team) consume the same
  selection and cannot drift (extracted in #323).

  Default window (window_type='last_5'): the team's last 5 finished matches before the upcoming
  fixture, cross-competition within the same entity_type. Season boundary (unchanged, #320):
  - Club: season_api_year = the upcoming fixture's season (real calendar boundary).
  - National: no season cap — recency alone is the boundary.

  Tournament exception (GAP-18; matrix §4 in docs/metrics_context_model.md). For an upcoming
  fixture whose competition_type is a tournament (world_championship / continental_championship)
  the window is CUMULATIVE, not last-5, and is never capped at 5:
  - window_type='tournament_to_date': every finished leg in THIS tournament (same league_code)
    and this edition (season_api_year) before kickoff — used once the team has a tournament leg
    (group-stage MD2 onward, including knockout).
  - window_type='qualifiers': when the team has NO tournament leg yet (its opener / pre-MD1),
    every finished leg in the tournament's qualifier competitions (registry parent_competition =
    this league_code) before kickoff, no season cap (a qualifying campaign spans seasons).
  A tournament side with neither tournament nor qualifier legs yields no rows (the mart renders
  the empty-form state). `qualifying`-type previews keep last_5 here (#483); the player path
  keeps last_5 (#484).

  Returns no rows for a team with no finished matches yet (before phase for a club
  domestic_league); #326's season-to-date fallback covers that gap.

  Grain: (upcoming_fixture_sk, team_sk, leg_fixture_sk).
#}

with upcoming as (
    select
        fixture_sk,
        home_team_sk,
        away_team_sk,
        league_code,
        season_api_year,
        kickoff_datetime
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

registry as (
    select * from {{ ref('competition_registry') }}
),

types as (
    select * from {{ ref('competition_types') }}
),

upcoming_with_type as (
    select
        u.fixture_sk,
        u.home_team_sk,
        u.away_team_sk,
        u.league_code,
        u.season_api_year,
        u.kickoff_datetime,
        reg.competition_type,
        typ.entity_type
    from upcoming as u
    left join registry as reg
        on u.league_code = reg.league_code
    left join types as typ
        on reg.competition_type = typ.competition_type
),

-- Expand each fixture into two sides (home + away)
upcoming_sides as (
    select
        fixture_sk as upcoming_fixture_sk,
        home_team_sk as team_sk,
        league_code as upcoming_league_code,
        season_api_year,
        kickoff_datetime,
        competition_type,
        entity_type
    from upcoming_with_type

    union all

    select
        fixture_sk as upcoming_fixture_sk,
        away_team_sk as team_sk,
        league_code as upcoming_league_code,
        season_api_year,
        kickoff_datetime,
        competition_type,
        entity_type
    from upcoming_with_type
),

-- Every candidate leg for a side: the team's finished matches (same entity_type) before
-- kickoff, with the leg's own parent_competition resolved for the qualifier window.
candidate_legs as (
    select
        s.upcoming_fixture_sk,
        s.team_sk,
        s.season_api_year,
        s.entity_type,
        s.upcoming_league_code,
        l.fixture_sk as leg_fixture_sk,
        l.league_code as leg_league_code,
        legreg.parent_competition as leg_parent_competition,
        l.season_api_year as leg_season_api_year,
        l.kickoff_datetime as leg_kickoff_datetime,
        l.round_name as leg_round_name,
        l.home_away,
        l.opponent_team_sk,
        l.result,
        l.goals_for,
        l.goals_against,
        l.shots_total,
        l.shots_on_goal,
        l.shots_inside_box,
        l.passes_total,
        l.passes_accurate,
        l.corner_kicks,
        l.opponent_corner_kicks,
        l.goalkeeper_saves,
        l.opponent_shots_on_goal,
        -- Tournament types (matrix §4) use a cumulative within-tournament window. The
        -- competition_type is the declared axis here (like entity_type), so we branch on it
        -- once — never on a hardcoded league_code. coalesce keeps it total: an unresolved
        -- type is treated as non-tournament (last_5), never dropped from both branches.
        coalesce(
            s.competition_type in ('world_championship', 'continental_championship'), false
        ) as is_tournament
    from upcoming_sides as s
    inner join {{ ref('int_legs__team_match') }} as l
        on
            s.team_sk = l.team_sk
            and s.entity_type = l.entity_type
            and s.kickoff_datetime > l.kickoff_datetime
    left join registry as legreg
        on l.league_code = legreg.league_code
),

-- Tournament side, while running: legs played in THIS tournament edition so far.
tournament_legs as (
    select *
    from candidate_legs
    where
        is_tournament
        and leg_league_code = upcoming_league_code
        and leg_season_api_year = season_api_year
),

sides_with_tournament_legs as (
    select distinct
        upcoming_fixture_sk,
        team_sk
    from tournament_legs
),

-- Tournament side at its opener (no tournament leg yet): the team's qualifier legs.
qualifier_legs as (
    select cl.*
    from candidate_legs as cl
    where
        cl.is_tournament
        and cl.leg_parent_competition = cl.upcoming_league_code
        and not exists (
            select 1
            from sides_with_tournament_legs as t
            where
                t.upcoming_fixture_sk = cl.upcoming_fixture_sk
                and t.team_sk = cl.team_sk
        )
),

-- Every non-tournament side: the last-5 cross-competition window.
last5_legs as (
    select *
    from candidate_legs
    where
        not is_tournament
        and (
            entity_type = 'national'
            or season_api_year = leg_season_api_year
        )
),

tournament_window as (
    select
        *,
        'tournament_to_date' as window_type,
        row_number() over (
            partition by upcoming_fixture_sk, team_sk
            order by leg_kickoff_datetime desc
        ) as recency_rank
    from tournament_legs
),

qualifier_window as (
    select
        *,
        'qualifiers' as window_type,
        row_number() over (
            partition by upcoming_fixture_sk, team_sk
            order by leg_kickoff_datetime desc
        ) as recency_rank
    from qualifier_legs
),

last5_window as (
    select
        *,
        'last_5' as window_type,
        row_number() over (
            partition by upcoming_fixture_sk, team_sk
            order by leg_kickoff_datetime desc
        ) as recency_rank
    from last5_legs
),

combined as (
    -- The WHERE binds only to the last UNION branch (last5_window) in BigQuery: last_5 is
    -- capped at 5, while tournament_window and qualifier_window are deliberately uncapped
    -- (cumulative, GAP-18). Do NOT parenthesise or hoist this WHERE — that would silently
    -- re-cap the tournament windows. assert_tournament_form_window guards the uncapped count.
    select * from tournament_window
    union all
    select * from qualifier_window
    union all
    select * from last5_window
    where recency_rank <= 5
)

select
    upcoming_fixture_sk,
    team_sk,
    season_api_year,
    entity_type,
    window_type,
    leg_fixture_sk,
    leg_league_code,
    leg_kickoff_datetime,
    leg_round_name,
    home_away,
    opponent_team_sk,
    result,
    goals_for,
    goals_against,
    shots_total,
    shots_on_goal,
    shots_inside_box,
    passes_total,
    passes_accurate,
    corner_kicks,
    opponent_corner_kicks,
    goalkeeper_saves,
    opponent_shots_on_goal,
    recency_rank
from combined
