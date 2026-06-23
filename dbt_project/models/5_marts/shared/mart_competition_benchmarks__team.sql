{{ config(materialized='view') }}

{#
  Team competition benchmark (the vs-benchmark block; content_architecture §6 — the engine, table stakes).
  LONG: one row per (team, season, metric_key) over the 20 team season metrics. Each row places the team
  against its league that season: the team's metric_value, the league median (+ mean) and p25/p75 spread,
  the team's rank (k of team_count), and metric_value - median.

  DIRECTION-AGNOSTIC by design: the mart reports position, not a verdict. rank is by metric_value DESC
  within (league_code, season_api_year, metric_key) — stated as "k of team_count" — and the good/bad
  reading is supplied at display from the catalogue's `direction` (joined there), since most football
  metrics are style, not quality. Median-led; rank not percentile (honest at N~18). Composes
  int_team_season__metrics + the int_competition_benchmarks__team engine (the shared
  team_benchmark_metrics() macro keeps the metric set identical). >= 3 games to be ranked.

  Season-to-date (W2). Player benchmark + percentile-vs-peers are the v1.x follow-up.
  Grain: (team_sk, season_sk, metric_key).
#}

with season as (
    select * from {{ ref('int_team_season__metrics') }}
    where season_games_played >= 3
),

teams as (
    select
        team_sk,
        team_name,
        team_logo_url
    from {{ ref('dim_team') }}
),

benchmarks as (
    select * from {{ ref('int_competition_benchmarks__team') }}
),

unpivoted as (
    {% for metric_key, col in team_benchmark_metrics() %}
    select
        team_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        '{{ metric_key }}' as metric_key,
        {{ col }} as metric_value
    from season
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
),

ranked as (
    select
        u.team_sk,
        u.season_sk,
        u.league_sk,
        u.league_code,
        u.season_api_year,
        u.metric_key,
        u.metric_value,
        rank() over (
            partition by u.league_code, u.season_api_year, u.metric_key
            order by u.metric_value desc
        ) as rank
    from unpivoted as u
    where u.metric_value is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['r.team_sk', 'r.season_sk', 'r.metric_key']) }}
        as team_benchmark_sk,
    r.team_sk,
    r.season_sk,
    r.league_sk,
    r.league_code,
    r.season_api_year,
    r.metric_key,
    t.team_name,
    t.team_logo_url,
    r.metric_value,
    b.league_mean,
    b.league_median,
    b.league_p25,
    b.league_p75,
    b.team_count,
    r.rank,
    r.metric_value - b.league_median as vs_median_delta
from ranked as r
inner join benchmarks as b
    on
        r.league_code = b.league_code
        and r.season_api_year = b.season_api_year
        and r.metric_key = b.metric_key
left join teams as t
    on r.team_sk = t.team_sk
