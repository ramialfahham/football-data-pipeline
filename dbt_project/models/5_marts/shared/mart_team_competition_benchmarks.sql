{#
  Team competition benchmark (the vs-benchmark block; content_architecture §6 — the engine, table stakes).
  LONG: one row per (team, season, metric_key) over the team benchmark metrics. Each row places the
  team against its league that season: the team's metric_value, the league median (+ mean) and
  p25/p75 spread, the team's rank (k of team_count), metric_value - median, and the team's value at
  the same point last season.

  rank orders by the metric's direction from the catalogue: a lower_better metric ranks the lowest
  value 1, every other metric the highest; tied values share a rank. Median-led; rank not percentile
  (honest at N~18). Composes int_team_competition_benchmark_metrics_long (the shared per-team long
  form) + the int_team_competition_benchmarks engine — both read the same long form, so the metric
  set cannot drift. Who is ranked: the ranking_rules doc block in models/docs/metric_rules.md.

  Season-to-date (W2). Player benchmark + percentile-vs-peers are the v1.x follow-up.
  Grain: (team_sk, season_sk, metric_key).
#}

with metrics as (
    select * from {{ ref('int_team_competition_benchmark_metrics_long') }}
),

teams as (
    select
        team_sk,
        team_name,
        team_logo_url
    from {{ ref('dim_team') }}
),

benchmarks as (
    select * from {{ ref('int_team_competition_benchmarks') }}
),

catalogue as (
    select
        metric_id,
        direction
    from {{ ref('metric_catalogue') }}
    where entity = 'team'
),

ranked as (
    select
        m.team_sk,
        m.season_sk,
        m.league_sk,
        m.league_code,
        m.season_api_year,
        m.metric_key,
        m.metric_value,
        m.metric_value_prev_season,
        rank() over (
            partition by m.league_code, m.season_api_year, m.metric_key
            order by if(c.direction = 'lower_better', m.metric_value, -m.metric_value) asc
        ) as rank
    from metrics as m
    inner join catalogue as c
        on m.metric_key = c.metric_id
    where m.metric_value is not null
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
    r.metric_value_prev_season,
    r.metric_value - b.league_median as vs_median_delta
from ranked as r
inner join benchmarks as b
    on
        r.league_code = b.league_code
        and r.season_api_year = b.season_api_year
        and r.metric_key = b.metric_key
left join teams as t
    on r.team_sk = t.team_sk
