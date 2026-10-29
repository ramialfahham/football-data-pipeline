{#
  The rebuilt table (int_team_season__table_by_time) against every table the provider published:
  each stored standings snapshot, with the league's corrections from standings_corrections. A
  published section is compared at the rebuilt table of the latest kick-off before the snapshot,
  where every team's played count matches; otherwise the provider had not yet counted a match and
  the section is left out. A section is also left out where a deduction step of that league-season
  took effect after that kick-off's day and by the snapshot's day, since the two tables then hold
  different deductions. One row per team whose rebuilt place or table points differ from the
  published ones, and one per rebuilt league-season with no comparable published table.
#}
{{ config(store_failures = true, severity = 'error') }}

with snapshots as (
    select
        league_code,
        ingested_at
    from {{ source('api_football', 'raw_apif_standings') }}
),

published as (
    select
        src.league_code,
        src.ingested_at,
        safe_cast(json_value(league_block, '$.league.season') as int64) as season_api_year,
        json_value(team_row, '$.group') as group_name,
        safe_cast(json_value(team_row, '$.team.id') as int64) as team_id,
        safe_cast(json_value(team_row, '$.rank') as int64) as standing_rank,
        safe_cast(json_value(team_row, '$.points') as int64) as points,
        safe_cast(json_value(team_row, '$.all.played') as int64) as played
    from {{ source('api_football', 'raw_apif_standings') }} as src,
        unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as league_block,
        unnest(json_query_array(json_query(league_block, '$.league.standings'), '$')) as stage_group,
        unnest(json_query_array(stage_group, '$')) as team_row
),

corrected as (
    select
        p.league_code,
        p.ingested_at,
        p.season_api_year,
        p.group_name,
        p.played,
        coalesce(if(p.played = c.played, c.official_team_id, null), p.team_id) as team_sk,
        coalesce(if(p.played = c.played, c.standing_rank, null), p.standing_rank) as standing_rank,
        coalesce(if(p.played = c.played, c.points, null), p.points) as points
    from published as p
    left join {{ ref('standings_corrections') }} as c
        on
            p.league_code = c.league_code
            and p.season_api_year = c.season
            and p.team_id = c.team_id
            and p.group_name = c.group_name
),

rebuilt as (
    select * from {{ ref('int_team_season__table_by_time') }}
),

league_seasons as (
    select distinct
        league_code,
        season_api_year
    from rebuilt
),

moments as (
    select distinct
        league_code,
        season_api_year,
        table_at
    from rebuilt
),

-- each snapshot meets the rebuilt table of the latest kick-off before it
matched as (
    select
        s.league_code,
        s.ingested_at,
        m.season_api_year,
        max(m.table_at) as table_at
    from snapshots as s
    inner join moments as m
        on s.league_code = m.league_code and s.ingested_at > m.table_at
    group by s.league_code, s.ingested_at, m.season_api_year
),

-- a deduction step between the kick-off and the snapshot puts different points in the two tables
deduction_between as (
    select distinct
        m.league_code,
        m.ingested_at,
        m.season_api_year
    from matched as m
    inner join {{ ref('standings_points_adjustments') }} as d
        on
            m.league_code = d.league_code
            and m.season_api_year = d.season
            and d.effective_date > date(m.table_at)
            and d.effective_date <= date(m.ingested_at)
    where d.rule = 'deduction'
),

comparable_moments as (
    select m.*
    from matched as m
    left join deduction_between as db
        on
            m.league_code = db.league_code
            and m.ingested_at = db.ingested_at
            and m.season_api_year = db.season_api_year
    where db.league_code is null
),

compared as (
    select
        c.league_code,
        c.season_api_year,
        c.group_name,
        c.ingested_at,
        c.team_sk,
        c.played as published_played,
        c.standing_rank as published_rank,
        c.points as published_points,
        r.played as rebuilt_played,
        r.table_position as rebuilt_rank,
        r.table_points as rebuilt_points,
        logical_and(r.played is not null and c.played = r.played) over (
            partition by c.league_code, c.season_api_year, c.group_name, c.ingested_at
        ) as is_comparable
    from corrected as c
    inner join league_seasons as ls
        on c.league_code = ls.league_code and c.season_api_year = ls.season_api_year
    inner join comparable_moments as m
        on
            c.league_code = m.league_code
            and c.ingested_at = m.ingested_at
            and c.season_api_year = m.season_api_year
    left join rebuilt as r
        on
            c.league_code = r.league_code
            and c.season_api_year = r.season_api_year
            and c.group_name = r.group_name
            and m.table_at = r.table_at
            and c.team_sk = r.team_sk
),

coverage as (
    select
        ls.league_code,
        ls.season_api_year,
        countif(cp.is_comparable) as comparable_rows
    from league_seasons as ls
    left join compared as cp
        on ls.league_code = cp.league_code and ls.season_api_year = cp.season_api_year
    group by ls.league_code, ls.season_api_year
)

select
    league_code,
    season_api_year,
    group_name,
    ingested_at,
    team_sk,
    'differs from the published table' as failure,
    published_rank,
    rebuilt_rank,
    published_points,
    rebuilt_points
from compared
where
    is_comparable
    and (rebuilt_points != published_points or (rebuilt_rank is not null and rebuilt_rank != published_rank))
union all
select
    league_code,
    season_api_year,
    cast(null as string) as group_name,
    cast(null as timestamp) as ingested_at,
    cast(null as int64) as team_sk,
    'no comparable published table' as failure,
    cast(null as int64) as published_rank,
    cast(null as int64) as rebuilt_rank,
    cast(null as int64) as published_points,
    cast(null as int64) as rebuilt_points
from coverage
where comparable_rows = 0
