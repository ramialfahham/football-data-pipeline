{#
  A competition-season's benchmarks name the rounds they are benchmarked over: table exactly where
  int_team_competition_phase__metrics supplies the season, empty everywhere else. Returns a
  benchmark row whose round_stage_kind says otherwise, so a column left empty or set on the wrong
  seasons fails.
#}
{{ config(store_failures = true, severity = 'error') }}

with phase as (
    select distinct season_sk
    from {{ ref('int_team_competition_phase__metrics') }}
)

select
    b.team_sk,
    b.season_sk,
    b.league_code,
    b.season_api_year,
    b.metric_key,
    b.round_stage_kind,
    p.season_sk is not null as is_phase_season
from {{ ref('mart_team_competition_benchmarks') }} as b
left join phase as p
    on b.season_sk = p.season_sk
where
    (p.season_sk is not null and (b.round_stage_kind is null or b.round_stage_kind != 'table'))
    or (p.season_sk is null and b.round_stage_kind is not null)
