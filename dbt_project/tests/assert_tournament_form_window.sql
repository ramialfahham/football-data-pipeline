-- GAP-18: the tournament form-window selection must be correct in two ways.
--
-- A. Provenance (per window leg, from the published drill-down list):
--    1. Only tournament-type fixtures (world_championship / continental_championship) ever
--       carry the tournament window_types — a non-tournament fixture must stay 'last_5'.
--    2. 'tournament_to_date' legs are played in the tournament itself (played_league_code =
--       the upcoming fixture's league_code).
--    3. 'qualifiers' legs are played in a qualifier competition — one whose registry
--       parent_competition is the upcoming fixture's tournament.
--
-- B. The window is uncapped (per side, from the aggregate): a 'tournament_to_date' side's
--    games_in_window must equal the team's FULL count of prior same-edition tournament legs,
--    recomputed independently from int_legs__team_match. This catches a re-introduced 5-cap
--    or a wrong season filter — failures the list-vs-aggregate invariant
--    (assert_momentum_window_matches_momentum) and the provenance checks above cannot see,
--    because a uniform under-count keeps the list and aggregate consistent with each other.
--
-- Any returned row is a defect.

{{ config(store_failures = true) }}

with legs as (
    select
        upcoming_fixture_sk,
        team_sk,
        league_code as upcoming_league_code,
        window_type,
        played_league_code
    from {{ ref('mart_team_momentum_window') }}
),

registry as (
    select
        league_code,
        competition_type,
        parent_competition
    from {{ ref('competition_registry') }}
),

provenance_failures as (
    select
        l.upcoming_fixture_sk,
        l.team_sk,
        l.window_type,
        'leg_wrong_competition' as failure
    from legs as l
    left join registry as up
        on l.upcoming_league_code = up.league_code
    left join registry as lp
        on l.played_league_code = lp.league_code
    where
        (
            l.window_type in ('tournament_to_date', 'qualifiers')
            and up.competition_type
            not in ('world_championship', 'continental_championship')
        )
        or (
            l.window_type = 'tournament_to_date'
            and l.played_league_code != l.upcoming_league_code
        )
        or (
            l.window_type = 'qualifiers'
            and coalesce(lp.parent_competition, '') != l.upcoming_league_code
        )
),

tournament_sides as (
    select
        m.upcoming_fixture_sk,
        m.team_sk,
        m.league_code,
        m.season_api_year,
        m.games_in_window,
        f.kickoff_datetime
    from {{ ref('mart_team_momentum') }} as m
    inner join {{ ref('fct_fixture') }} as f
        on m.upcoming_fixture_sk = f.fixture_sk
    where m.window_type = 'tournament_to_date'
),

expected_counts as (
    select
        ts.upcoming_fixture_sk,
        ts.team_sk,
        ts.games_in_window,
        count(l.fixture_sk) as expected_legs
    from tournament_sides as ts
    left join {{ ref('int_legs__team_match') }} as l
        on
            ts.team_sk = l.team_sk
            and ts.league_code = l.league_code
            and ts.season_api_year = l.season_api_year
            and ts.kickoff_datetime > l.kickoff_datetime
    group by
        ts.upcoming_fixture_sk,
        ts.team_sk,
        ts.games_in_window
),

count_failures as (
    select
        upcoming_fixture_sk,
        team_sk,
        'tournament_to_date' as window_type,
        'games_in_window_not_full_cumulative' as failure
    from expected_counts
    where games_in_window != expected_legs
)

select * from provenance_failures
union all
select * from count_failures
