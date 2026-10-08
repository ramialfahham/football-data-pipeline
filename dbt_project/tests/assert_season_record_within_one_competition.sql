-- A season record stays within one competition (docs/metrics_context_model.md section 1). Fail any
-- season-record row that counts more matches than its team or player played in that row's competition
-- and season; a window that crosses competitions does.
{{ config(store_failures = true, severity = 'error') }}

with team_matches as (
    select
        team_sk,
        league_code,
        season_api_year,
        count(*) as matches
    from {{ ref('int_legs__team_match') }}
    group by team_sk, league_code, season_api_year
),

player_matches as (
    select
        team_sk,
        player_sk,
        league_code,
        season_api_year,
        count(*) as matches
    from {{ ref('int_legs__player_match') }}
    group by team_sk, player_sk, league_code, season_api_year
)

select
    'mart_team_season_record' as mart_name,
    r.upcoming_fixture_sk,
    r.team_sk,
    cast(null as int64) as player_sk,
    r.games_played,
    m.matches
from {{ ref('mart_team_season_record') }} as r
left join team_matches as m
    on r.team_sk = m.team_sk and r.league_code = m.league_code and r.season_api_year = m.season_api_year
where r.games_played > coalesce(m.matches, 0)

union all

select
    'mart_player_season_record' as mart_name,
    r.upcoming_fixture_sk,
    r.team_sk,
    r.player_sk,
    r.games_played,
    m.matches
from {{ ref('mart_player_season_record') }} as r
left join player_matches as m
    on
        r.team_sk = m.team_sk
        and r.player_sk = m.player_sk
        and r.league_code = m.league_code
        and r.season_api_year = m.season_api_year
where r.games_played > coalesce(m.matches, 0)
