-- Every round the Teams page counts has a value in int_team_index__round_values: the rounds of
-- each top club cup's last five finished seasons and of the latest finished World Cup and
-- championships, a round without a name included. A round without a value would score nothing
-- and drop a team down the ranking. A configured competition with no counted season fails too.

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

fixtures as (
    select
        league_code,
        season_api_year,
        round_name,
        status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO') as is_finished
    from {{ ref('fct_fixture') }}
),

round_names as (
    select
        league_code,
        season_api_year,
        round_name,
        round_label_i18n_key,
        round_stage_kind
    from {{ ref('int_round_names') }}
),

round_values as (
    select * from {{ ref('int_team_index__round_values') }}
),

finished_seasons as (
    select
        f.league_code,
        f.season_api_year,
        row_number() over (
            partition by f.league_code order by f.season_api_year desc
        ) as recency
    from fixtures as f
    inner join round_names as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
    where r.round_stage_kind = 'final'
    group by f.league_code, f.season_api_year
    having logical_and(f.is_finished)
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
    from finished_seasons as s
    inner join counted_competitions as c
        on s.league_code = c.league_code
    where s.recency <= c.seasons_counted
)

select
    r.league_code,
    r.season_api_year,
    r.round_name,
    r.round_label_i18n_key
from round_names as r
inner join counted_seasons as c
    on
        r.league_code = c.league_code
        and r.season_api_year = c.season_api_year
left join round_values as v
    on r.round_label_i18n_key = v.round_key
where
    (r.round_stage_kind is null or r.round_stage_kind in ('table', 'knockout', 'final'))
    and v.round_key is null

union all

select
    c.league_code,
    null as season_api_year,
    null as round_name,
    'no counted season' as round_label_i18n_key
from counted_competitions as c
left join counted_seasons as s
    on c.league_code = s.league_code
where s.league_code is null
