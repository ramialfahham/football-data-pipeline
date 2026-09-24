-- is_last_round on mart_competition_fixtures is the round just played: for each competition, the
-- played fixtures of the latest round (by first kick-off) with a played fixture, within the season
-- of its earliest fixture not yet started (its next matchday's season). A flagged fixture that is
-- unplayed, or of another season, or a second flagged round, or any flag on a competition with no
-- upcoming fixture, or a played fixture of that round left unflagged, fails.
--
-- Recomputed from fct_fixture and int_legs__team_match, not from either mart's CTEs, so a rewrite
-- that flags a round's unplayed fixtures too, drops the season condition, picks the round of the
-- latest played kick-off, or takes the round before the next one fails here even when the schema
-- tests stay green.
--
-- Returns a row (= fails) per competition where any property does not hold.
{{ config(store_failures = true) }}

with upcoming as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        fixture_date,
        kickoff_datetime
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

current_season as (
    select
        league_code,
        season_api_year
    from upcoming
    qualify row_number() over (
        partition by league_code
        order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
    ) = 1
),

played as (
    select distinct fixture_sk
    from {{ ref('int_legs__team_match') }}
),

rounds as (
    select
        league_code,
        season_api_year,
        round_name,
        dense_rank() over (
            partition by league_code, season_api_year
            order by min(kickoff_datetime) asc, round_name asc
        ) as round_sequence
    from {{ ref('fct_fixture') }}
    group by league_code, season_api_year, round_name
),

season_played as (
    select
        f.fixture_sk,
        f.league_code,
        r.round_sequence
    from {{ ref('fct_fixture') }} as f
    inner join current_season as c
        on
            f.league_code = c.league_code
            and f.season_api_year = c.season_api_year
    inner join played as p
        on f.fixture_sk = p.fixture_sk
    inner join rounds as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
),

expected as (
    select
        fixture_sk,
        league_code
    from season_played
    qualify round_sequence = max(round_sequence) over (partition by league_code)
),

served as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_name
    from {{ ref('mart_competition_fixtures') }}
    where is_last_round
),

compared as (
    select
        coalesce(e.league_code, s.league_code) as league_code,
        countif(e.fixture_sk is null) as n_unexpected,
        countif(s.fixture_sk is null) as n_missing
    from expected as e
    full outer join served as s
        on e.fixture_sk = s.fixture_sk
    group by coalesce(e.league_code, s.league_code)
),

properties as (
    select
        s.league_code,
        count(distinct concat(s.season_api_year, ' ', s.round_name)) as n_rounds,
        countif(p.fixture_sk is null) as n_unplayed,
        countif(c.season_api_year is null or s.season_api_year != c.season_api_year) as n_other_season
    from served as s
    left join played as p
        on s.fixture_sk = p.fixture_sk
    left join current_season as c
        on s.league_code = c.league_code
    group by s.league_code
)

select
    x.league_code,
    x.n_unexpected,
    x.n_missing,
    coalesce(y.n_rounds, 0) as n_rounds,
    coalesce(y.n_unplayed, 0) as n_unplayed,
    coalesce(y.n_other_season, 0) as n_other_season
from compared as x
left join properties as y
    on x.league_code = y.league_code
where
    x.n_unexpected != 0
    or x.n_missing != 0
    or coalesce(y.n_rounds, 0) > 1
    or coalesce(y.n_unplayed, 0) != 0
    or coalesce(y.n_other_season, 0) != 0
