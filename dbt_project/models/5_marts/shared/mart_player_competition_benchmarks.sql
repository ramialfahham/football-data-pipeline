{#
  Player competition benchmark (the vs-benchmark block; content_architecture §6 — the engine, table stakes).
  LONG: one row per (player, season, position_group, metric_key). Each row places the player against his
  positional peers in that competition-season: the player's in-position per-90 (or rate) value, the peer
  median (+ mean) and p25/p75 spread, his rank (k of peer_count) AND percentile, and value - median. minutes
  + appearances are carried so the sample is always visible. The player analog of
  mart_team_competition_benchmarks, extended to peers = position group + a percentile (large player N).

  DIRECTION-AGNOSTIC by design: rank is by value DESC and percentile by value within (league_code,
  season_api_year, position_group, metric_key); the good/bad reading is supplied at display from the
  catalogue's `direction`. rank_best_first follows that direction: 1 is the best value, the lowest on
  a lower_better metric, the rank the Player page shows. Composes int_player_competition_benchmark_metrics_long (the metric set, position
  eligibility and who enters, shared with the engine) + the int_player_competition_benchmarks engine.
  Multi-position players appear once per qualifying position, each on their in-role value.

  position_player_count is how many players entered the position, the {n} of the explainer; peer_count
  is a metric's own, smaller where a floor or a blank leaves a player out. page_tab and
  competition_order place a row in the Player page's filter: a competition of the tab's window, in the
  player's page position; null for every other row.

  Grain: (player_sk, season_sk, position_group, metric_key).
#}

with metrics as (
    select * from {{ ref('int_player_competition_benchmark_metrics_long') }}
),

directions as (
    select
        metric_id,
        direction
    from {{ ref('metric_catalogue') }}
    where entity = 'player'
),

position_counts as (
    select
        league_code,
        season_api_year,
        position_group,
        count(distinct player_sk) as position_player_count
    from metrics
    group by league_code, season_api_year, position_group
),

page_filters as (
    select
        w.player_sk,
        w.season_sk,
        p.position_group,
        if(w.window_type = 'this_season', 'club', 'national_team') as page_tab,
        row_number() over (
            partition by w.player_sk, w.window_type
            order by
                {{ competition_type_order('w.competition_type') }} asc,
                w.last_match_at desc,
                w.league_code asc
        ) as window_order
    from {{ ref('int_player_page__window_seasons') }} as w
    inner join {{ ref('int_player__page_profile') }} as p
        on w.player_sk = p.player_sk
    where w.window_type in ('this_season', 'current_competitions')
),

season_labels as (
    select
        season_sk,
        season_label
    from {{ ref('dim_competition_season') }}
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
        rank() over (
            partition by
                u.league_code, u.season_api_year, u.position_group, u.metric_key
            order by if(d.direction = 'lower_better', u.metric_value, -u.metric_value) asc
        ) as rank_best_first,
        percent_rank() over (
            partition by
                u.league_code, u.season_api_year, u.position_group, u.metric_key
            order by u.metric_value asc
        ) as percentile
    from metrics as u
    inner join directions as d
        on u.metric_key = d.metric_id
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
    pc.position_player_count,
    sl.season_label,
    pf.page_tab,
    if(
        pf.page_tab is null,
        null,
        dense_rank() over (partition by r.player_sk, pf.page_tab order by pf.window_order asc)
    ) as competition_order,
    r.rank,
    r.rank_best_first,
    r.percentile,
    r.metric_value - b.peer_median as vs_median_delta
from ranked as r
inner join benchmarks as b
    on
        r.league_code = b.league_code
        and r.season_api_year = b.season_api_year
        and r.position_group = b.position_group
        and r.metric_key = b.metric_key
inner join position_counts as pc
    on
        r.league_code = pc.league_code
        and r.season_api_year = pc.season_api_year
        and r.position_group = pc.position_group
left join players as p
    on r.player_sk = p.player_sk
left join season_labels as sl
    on r.season_sk = sl.season_sk
left join page_filters as pf
    on
        r.player_sk = pf.player_sk
        and r.season_sk = pf.season_sk
        and r.position_group = pf.position_group
