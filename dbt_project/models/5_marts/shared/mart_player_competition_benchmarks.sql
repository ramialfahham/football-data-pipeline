{{ config(materialized='view') }}

{#
  Player competition benchmark (the vs-benchmark block; content_architecture §6 — the engine, table stakes).
  LONG: one row per (player, season, position_group, metric_key). Each row places the player against his
  positional peers in that competition-season: the player's in-position per-90 (or rate) value, the peer
  median (+ mean) and p25/p75 spread, his rank (k of peer_count) AND percentile, and value - median. minutes
  + appearances are carried so the sample is always visible. The player analog of
  mart_team_competition_benchmarks, extended to peers = position group + a percentile (large player N).

  DIRECTION-AGNOSTIC by design (D7): rank is by value DESC and percentile by value within (league_code,
  season_api_year, position_group, metric_key); the good/bad reading is supplied at display from the
  catalogue's `direction`. Composes int_player_season_position__metrics + the int_player_competition_benchmarks
  engine (the shared player_benchmark_metrics() macro keeps the metric set + position eligibility
  identical). Floor: minutes >= 270 in the position (finishing also >= 10 shots on target). Multi-position
  players appear once per qualifying position, each on their in-role value.

  Grain: (player_sk, season_sk, position_group, metric_key).
#}

with season as (
    select * from {{ ref('int_player_season_position__metrics') }}
    where minutes >= 270
),

players as (
    select
        player_sk,
        player_name,
        player_nationality,
        player_photo_url
    from {{ ref('dim_player') }}
),

benchmarks as (
    select * from {{ ref('int_player_competition_benchmarks') }}
),

unpivoted as (
    {% for m in player_benchmark_metrics() %}
    select
        player_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        position_group,
        minutes,
        appearances,
        '{{ m.key }}' as metric_key,
        case
            when
                position_group in ('{{ m.pos | join("', '") }}')
                {%- if m.floor is defined %} and {{ m.floor }}{% endif %}
                then {{ m.col }}
        end as metric_value,
        -- GAP-21: the volume behind each ratio %, gated by the SAME eligibility+floor as
        -- metric_value; null when the metric defines no num/den (the 13 per-90 metrics).
        -- Feeds the {num} of {den} · {pct}% triple on the Stats screen.
        case
            when
                position_group in ('{{ m.pos | join("', '") }}')
                {%- if m.floor is defined %} and {{ m.floor }}{% endif %}
                then {% if m.num is defined %}{{ m.num }}{% else %}cast(null as int64){% endif %}
        end as metric_numerator,
        case
            when
                position_group in ('{{ m.pos | join("', '") }}')
                {%- if m.floor is defined %} and {{ m.floor }}{% endif %}
                then {% if m.den is defined %}{{ m.den }}{% else %}cast(null as int64){% endif %}
        end as metric_denominator
    from season
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
),

ranked as (
    select
        u.player_sk,
        u.season_sk,
        u.league_sk,
        u.league_code,
        u.season_api_year,
        u.position_group,
        u.minutes,
        u.appearances,
        u.metric_key,
        u.metric_value,
        u.metric_numerator,
        u.metric_denominator,
        rank() over (
            partition by
                u.league_code, u.season_api_year, u.position_group, u.metric_key
            order by u.metric_value desc
        ) as rank,
        percent_rank() over (
            partition by
                u.league_code, u.season_api_year, u.position_group, u.metric_key
            order by u.metric_value asc
        ) as percentile
    from unpivoted as u
    where u.metric_value is not null
)

select
    {{ dbt_utils.generate_surrogate_key([
        'r.player_sk', 'r.season_sk', 'r.position_group', 'r.metric_key'
    ]) }} as player_benchmark_sk,
    r.player_sk,
    r.season_sk,
    r.league_sk,
    r.league_code,
    r.season_api_year,
    r.position_group,
    r.metric_key,
    p.player_name,
    p.player_nationality,
    p.player_photo_url,
    r.minutes,
    r.appearances,
    r.metric_value,
    r.metric_numerator,
    r.metric_denominator,
    b.peer_mean,
    b.peer_median,
    b.peer_p25,
    b.peer_p75,
    b.player_count as peer_count,
    r.rank,
    r.percentile,
    r.metric_value - b.peer_median as vs_median_delta
from ranked as r
inner join benchmarks as b
    on
        r.league_code = b.league_code
        and r.season_api_year = b.season_api_year
        and r.position_group = b.position_group
        and r.metric_key = b.metric_key
left join players as p
    on r.player_sk = p.player_sk
