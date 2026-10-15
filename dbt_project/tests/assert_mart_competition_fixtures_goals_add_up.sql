{#
  Every played match of mart_competition_fixtures has one goal-data state, and the goals it serves
  add up to its score side by side: the score on the pitch for a played or abandoned award. Returns
  one row per broken match:
  - no_state: a played match without a state, or a match not played with a state or goals;
  - award_kind_missing: an awarded result with no kind;
  - goals_on_unplayed_award: goals on an award that was not played;
  - does_not_add_up: served goals that differ from the score on either side, or name a team not
    in the match;
  - minute_missing: a goal without its minute in a match whose state says every minute is known;
  - score_after_wrong: a list in match order whose scores after each goal do not step up one goal
    at a time to the goals it serves;
  - unknown_player: a scorer's or assister's provider id that dim_player does not hold;
  - goals_not_reconciled: a match whose goal events exist but add up neither alone nor with the
    players' goals; it needs its goals in fixture_goal_corrections.
#}
{{ config(store_failures = true, severity = 'error') }}

with fixtures as (
    select * from {{ ref('mart_competition_fixtures') }}
),

goal_events as (
    select
        fixture_sk,
        count(*) as goal_events
    from {{ ref('fct_fixture_event') }}
    where is_goal
    group by fixture_sk
),

players as (
    select player_sk
    from {{ ref('dim_player') }}
),

served as (
    select
        f.fixture_sk,
        coalesce(sum(if(g.side = 'home', g.goals, 0)), 0) as served_home,
        coalesce(sum(if(g.side = 'away', g.goals, 0)), 0) as served_away,
        countif(g.goals is not null and g.side is null) as served_other_side,
        countif(g.goals is not null and g.minute_elapsed is null) as served_without_minute,
        countif(g.player_api_id is not null and p.player_sk is null) as served_unknown_player,
        countif(g.assist_player_api_id is not null and ap.player_sk is null) as served_unknown_assist,
        max(g.score_home_after) as last_score_home,
        max(g.score_away_after) as last_score_away,
        count(distinct g.score_home_after + g.score_away_after) as score_steps,
        count(g.goals) as entries
    from fixtures as f
    left join unnest(f.goals) as g
        on true
    left join players as p
        on g.player_api_id = p.player_sk
    left join players as ap
        on g.assist_player_api_id = ap.player_sk
    group by f.fixture_sk
),

checked as (
    select
        f.fixture_sk,
        f.league_code,
        f.season_api_year,
        f.status_short,
        f.goal_data_state,
        f.award_kind,
        f.goals_home,
        f.goals_away,
        f.on_pitch_home,
        f.on_pitch_away,
        s.served_home,
        s.served_away,
        case
            when f.is_played and f.goal_data_state is null then 'no_state'
            when not f.is_played and (f.goal_data_state is not null or s.entries > 0) then 'no_state'
            when f.goal_data_state = 'awarded' and f.award_kind is null then 'award_kind_missing'
            when f.award_kind = 'not_played' and s.entries > 0 then 'goals_on_unplayed_award'
            when
                (f.goal_data_state in ('goals', 'goals_without_minutes') or f.award_kind in ('played', 'abandoned'))
                and (
                    s.served_other_side > 0
                    or s.served_home
                    is distinct from if(f.award_kind in ('played', 'abandoned'), f.on_pitch_home, f.goals_home)
                    or s.served_away
                    is distinct from if(f.award_kind in ('played', 'abandoned'), f.on_pitch_away, f.goals_away)
                )
                then 'does_not_add_up'
            when f.goal_data_state = 'goals' and s.served_without_minute > 0 then 'minute_missing'
            when
                s.entries > 0 and s.served_without_minute = 0
                and (
                    s.score_steps != s.entries
                    or s.last_score_home is distinct from s.served_home
                    or s.last_score_away is distinct from s.served_away
                )
                then 'score_after_wrong'
            when s.served_unknown_player > 0 or s.served_unknown_assist > 0 then 'unknown_player'
            when f.goal_data_state = 'not_recorded' and coalesce(e.goal_events, 0) > 0 then 'goals_not_reconciled'
        end as problem
    from fixtures as f
    inner join served as s
        on f.fixture_sk = s.fixture_sk
    left join goal_events as e
        on f.fixture_sk = e.fixture_sk
)

select *
from checked
where problem is not null
