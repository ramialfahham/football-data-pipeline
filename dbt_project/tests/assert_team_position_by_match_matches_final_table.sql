{#
  The position at a number of matches (int_team_season__position_by_match) against the official
  table, wherever every team of a section has played the same number of matches: a finished
  season's final table, or a table between two full matchdays. One row per team whose rank at
  that number of matches is not its official rank, or that has no rank there. A points deduction
  or a league's own tie-break is a known reason, so this warns and stores the rows.
#}
{{ config(store_failures = true, severity = 'warn') }}

with ranked as (
    select distinct
        league_code,
        season_api_year,
        group_name
    from {{ ref('int_team_season__position_by_match') }}
),

official as (
    select
        s.league_code,
        s.season_api_year,
        s.group_name,
        s.team_sk,
        s.standing_rank,
        s.played,
        s.points
    from {{ ref('fct_standings') }} as s
    inner join ranked as r
        on
            s.league_code = r.league_code
            and s.season_api_year = r.season_api_year
            and s.group_name = r.group_name
    qualify
        min(s.played) over (partition by s.league_code, s.season_api_year, s.group_name)
        = max(s.played) over (partition by s.league_code, s.season_api_year, s.group_name)
)

select
    o.league_code,
    o.season_api_year,
    o.group_name,
    o.team_sk,
    o.played,
    o.standing_rank,
    p.position_at_match,
    o.points as official_points,
    p.points_won
from official as o
left join {{ ref('int_team_season__position_by_match') }} as p
    on
        o.team_sk = p.team_sk
        and o.league_code = p.league_code
        and o.season_api_year = p.season_api_year
        and o.played = p.match_number
where p.position_at_match is distinct from o.standing_rank
