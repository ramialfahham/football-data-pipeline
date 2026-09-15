-- mart_competition_season_summary reconciles with the finished matches it summarises: the two
-- referenced fixtures are finished matches of that competition-season with the scores the row
-- repeats; the biggest margin is the largest margin among them and the most goals the largest
-- total; the season's match and goal counts equal the fixture fact's; no run is longer than the
-- most matches any team played; and every run holder played in that competition-season.
--
-- Recomputed from fct_fixture, not from the mart's CTEs, so a rewrite of the mart that changes
-- the finished-match definition, the tie rule or the run computation fails here even when the
-- schema tests stay green.
--
-- Returns a row (= fails) per competition-season where any property does not hold.
with finished as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        home_team_sk,
        away_team_sk,
        goals_home,
        goals_away
    from {{ ref('fct_fixture') }}
    where
        status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO')
        and goals_home is not null
        and goals_away is not null
),

expected as (
    select
        league_code,
        season_api_year,
        count(*) as matches_played,
        sum(goals_home + goals_away) as goals,
        max(abs(goals_home - goals_away)) as max_margin,
        max(goals_home + goals_away) as max_total
    from finished
    group by league_code, season_api_year
),

team_matches as (
    select
        league_code,
        season_api_year,
        team_sk,
        count(*) as played
    from (
        select
            league_code,
            season_api_year,
            home_team_sk as team_sk
        from finished
        union all
        select
            league_code,
            season_api_year,
            away_team_sk as team_sk
        from finished
    )
    group by league_code, season_api_year, team_sk
),

most_played as (
    select
        league_code,
        season_api_year,
        max(played) as max_team_played
    from team_matches
    group by league_code, season_api_year
),

served as (
    select * from {{ ref('mart_competition_season_summary') }}
),

holders as (
    select
        s.league_code,
        s.season_api_year,
        holder as team_sk
    from served as s
    cross join unnest(s.longest_unbeaten_team_sks) as holder
    union all
    select
        s.league_code,
        s.season_api_year,
        holder as team_sk
    from served as s
    cross join unnest(s.longest_winless_team_sks) as holder
),

unknown_holders as (
    select
        h.league_code,
        h.season_api_year,
        count(*) as n_unknown
    from holders as h
    left join team_matches as tm
        on
            h.league_code = tm.league_code
            and h.season_api_year = tm.season_api_year
            and h.team_sk = tm.team_sk
    where tm.team_sk is null
    group by h.league_code, h.season_api_year
)

select
    s.league_code,
    s.season_api_year
from served as s
left join expected as e
    on
        s.league_code = e.league_code
        and s.season_api_year = e.season_api_year
left join most_played as mp
    on
        s.league_code = mp.league_code
        and s.season_api_year = mp.season_api_year
left join unknown_holders as uh
    on
        s.league_code = uh.league_code
        and s.season_api_year = uh.season_api_year
left join finished as b
    on s.biggest_margin_fixture_sk = b.fixture_sk
left join finished as g
    on s.most_goals_fixture_sk = g.fixture_sk
where
    e.league_code is null
    or s.matches_played != e.matches_played
    or s.total_goals != e.goals
    or b.fixture_sk is null
    or b.league_code != s.league_code
    or b.season_api_year != s.season_api_year
    or b.goals_home != s.biggest_margin_goals_home
    or b.goals_away != s.biggest_margin_goals_away
    or abs(b.goals_home - b.goals_away) != e.max_margin
    or g.fixture_sk is null
    or g.league_code != s.league_code
    or g.season_api_year != s.season_api_year
    or g.goals_home + g.goals_away != e.max_total
    or s.longest_unbeaten_run > mp.max_team_played
    or s.longest_winless_run > mp.max_team_played
    or coalesce(uh.n_unknown, 0) > 0
