{#
  A team's table is the section of the phase it is playing. Pinned on the cases where the
  provider lists an earlier or overall table first, and on a group tournament whose cross-group
  ranking is listed first: APD 2026 Clausura, BPL 2024 Charleroi in its Qualifying Round, KL1 2026
  FC Seoul in the Championship Group, VL 2026 Ilves in its relegation group, EURO 2024 Netherlands
  in Group D. mart_team_competitions and mart_team_season read the same pick, so both are checked.
  Each failing row is a case whose table or rank is not the expected one.
#}
{{ config(store_failures = true, severity = 'error') }}

with expected as (
    select
        'APD' as league_code,
        2026 as season_api_year,
        'Estudiantes L.P.' as team_name,
        'Clausura - Group A' as group_name
    union all
    select
        'BPL' as league_code,
        2024 as season_api_year,
        'Charleroi' as team_name,
        'Qualifying Round' as group_name
    union all
    select
        'KL1' as league_code,
        2026 as season_api_year,
        'FC Seoul' as team_name,
        'K-League: Championship Group' as group_name
    union all
    select
        'VL' as league_code,
        2026 as season_api_year,
        'Ilves' as team_name,
        'Relegration Group' as group_name
    union all
    select
        'EURO' as league_code,
        2024 as season_api_year,
        'Netherlands' as team_name,
        'Group D' as group_name
),

cases as (
    select
        e.*,
        t.team_sk
    from expected as e
    inner join {{ ref('dim_team') }} as t
        on e.team_name = t.team_name
    inner join {{ ref('mart_standings') }} as s
        on
            e.league_code = s.league_code
            and e.season_api_year = s.season_api_year
            and e.group_name = s.group_name
            and t.team_sk = s.team_sk
)

select
    e.league_code,
    e.season_api_year,
    e.team_name,
    e.group_name as expected_group_name,
    c.standing_group_name,
    c.standing_rank,
    ts.latest_rank,
    s.standing_rank as expected_rank
from expected as e
left join cases as k
    on
        e.league_code = k.league_code
        and e.season_api_year = k.season_api_year
        and e.team_name = k.team_name
left join {{ ref('mart_standings') }} as s
    on
        k.league_code = s.league_code
        and k.season_api_year = s.season_api_year
        and k.group_name = s.group_name
        and k.team_sk = s.team_sk
left join {{ ref('mart_team_competitions') }} as c
    on
        k.team_sk = c.team_sk
        and k.league_code = c.league_code
        and k.season_api_year = c.season_api_year
left join {{ ref('mart_team_season') }} as ts
    on
        k.team_sk = ts.team_sk
        and k.league_code = ts.league_code
        and k.season_api_year = ts.season_api_year
where
    k.team_sk is null
    or c.standing_group_name is distinct from e.group_name
    or c.standing_rank is distinct from s.standing_rank
    or ts.latest_rank is distinct from s.standing_rank
