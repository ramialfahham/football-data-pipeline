-- Every season the Teams page counts (a top club cup's last five finished seasons, the latest
-- finished World Cup and championships) has exactly one winner in mart_team_competitions.

with regions as (
    select
        top_club_competition,
        continental_championship
    from {{ ref('confederations') }}
),

world_championships as (
    select league_code
    from {{ ref('competition_registry') }}
    where competition_type = 'world_championship'
),

finals as (
    select
        f.league_code,
        f.season_api_year,
        row_number() over (
            partition by f.league_code order by f.season_api_year desc
        ) as recency
    from {{ ref('fct_fixture') }} as f
    inner join {{ ref('int_round_names') }} as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
    where r.round_stage_kind = 'final'
    group by f.league_code, f.season_api_year
    having logical_and(f.status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO'))
),

counted_competitions as (
    select
        top_club_competition as league_code,
        5 as seasons_counted
    from regions
    where top_club_competition is not null
    union all
    select
        continental_championship as league_code,
        1 as seasons_counted
    from regions
    where continental_championship is not null
    union all
    select
        league_code,
        1 as seasons_counted
    from world_championships
),

counted_seasons as (
    select
        s.league_code,
        s.season_api_year
    from finals as s
    inner join counted_competitions as c
        on s.league_code = c.league_code
    where s.recency <= c.seasons_counted
),

winners as (
    select
        league_code,
        season_api_year,
        countif(cup_status = 'winners') as winner_count
    from {{ ref('mart_team_competitions') }}
    group by league_code, season_api_year
)

select
    c.league_code,
    c.season_api_year,
    coalesce(w.winner_count, 0) as winner_count
from counted_seasons as c
left join winners as w
    on
        c.league_code = w.league_code
        and c.season_api_year = w.season_api_year
where coalesce(w.winner_count, 0) != 1
