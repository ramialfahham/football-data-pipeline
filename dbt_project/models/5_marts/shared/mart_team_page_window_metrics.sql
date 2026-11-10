{#
  What a Team page shows over the season, in long form: the This season cards, and each
  comparison metric this season against the whole of last season. Matches and wins, counts of
  results and no catalogue metrics (rule R7), are columns on every row; the four other cards are
  rows. Both windows are every club
  competition of the season (int_team_window__metrics); every comparison metric is a rate, per
  match or a share, so the two windows compare at any number of matches. A blank value is rule R4
  in models/docs/metric_rules.md. A team with no club window, a national team, has no row.

  Grain: (team_sk, metric_key).
#}

with windows as (
    select * from {{ ref('int_team_window__metrics') }}
),

this_season as (
    select * from windows
    where window_type = 'this_season'
),

last_season as (
    select * from windows
    where window_type = 'last_season'
),

cards as (
    select
        t.team_sk,
        m.metric_key,
        m.metric_value,
        true as is_card,
        false as is_comparison,
        cast(null as float64) as metric_value_prev_season
    from this_season as t,
        unnest([
            struct('goals' as metric_key, cast(t.goals as float64) as metric_value),
            ('goals_against', cast(t.goals_against as float64)),
            ('cards_yellow', cast(t.cards_yellow as float64)),
            ('cards_red', cast(t.cards_red as float64))
        ]) as m
),

rates as (
    select
        team_sk,
        window_type,
        metric_key,
        metric_value
    from windows
    unpivot include nulls (
        metric_value for metric_key in (
            goals_per_match,
            goals_against_per_match,
            clean_sheets_pct,
            shots_per_match,
            shots_on_goal_pct,
            shots_inside_box_pct,
            shots_inside_box_per_match,
            shots_on_goal_per_match,
            shots_on_goal_against_per_match,
            shots_on_goal_difference_per_match,
            finishing_efficiency_pct,
            duels_per_match,
            duels_won_per_match,
            duels_won_pct,
            defensive_actions_per_match,
            tackles_per_match,
            interceptions_per_match,
            blocks_per_match,
            passes_per_match,
            passes_accurate_per_match,
            passes_accuracy_pct,
            passes_share_pct,
            passes_key_per_match,
            dribbles_attempts_per_match,
            dribbles_success_per_match,
            dribbles_success_pct,
            corners_per_match,
            corners_against_per_match,
            free_kicks_per_match,
            fouls_per_match,
            offsides_per_match,
            saves_per_match,
            saves_pct
        )
    )
),

comparison as (
    select
        t.team_sk,
        t.metric_key,
        t.metric_value,
        false as is_card,
        true as is_comparison,
        l.metric_value as metric_value_prev_season
    from rates as t
    left join rates as l
        on
            t.team_sk = l.team_sk
            and t.metric_key = l.metric_key
            and l.window_type = 'last_season'
    where t.window_type = 'this_season'
),

all_rows as (
    select * from cards
    union all
    select * from comparison
)

select
    r.team_sk,
    r.metric_key,
    r.is_card,
    r.is_comparison,
    t.matches,
    t.wins,
    l.matches as matches_prev_season,
    t.league_codes,
    r.metric_value,
    r.metric_value_prev_season
from all_rows as r
inner join this_season as t
    on r.team_sk = t.team_sk
left join last_season as l
    on r.team_sk = l.team_sk
