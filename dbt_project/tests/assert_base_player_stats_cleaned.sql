{#
  The cleaning rules of docs/metric_layer.md hold on every row of base_apif__fixture_players.
  Returns one row per violation, named by the rule it breaks:

  - blank_where_counted: a stat is blank although the provider delivered a value for it to someone
    else in the match (read from stg_apif__fixture_players, the fetch base kept), and no correction
    on the row left it blank. Exempt as the rules say: a keeper's saves and goals conceded are
    counted only by another keeper; a player who did something (a positive stat, or a goal in the
    events) keeps blank minutes; accurate passes stay blank in a match with no pass data.
  - part_above_whole, open_play_goals_above_shots_on_target, penalty_goals_above_goals,
    penalties_scored_not_penalty_goals, card_maximum, goals_conceded_above_team,
    keepers_goals_conceded_above_team, sole_keeper_goals_conceded, saves_above_ceiling,
    assists_above_team_goals, team_assists_above_team_goals: a contradiction the cleaning must
    have removed.
  - goals_do_not_add_up: the team's goals from its players and its own goals miss the score in a
    match where the per-player count or the goal events add up to it.
  - correction_not_on_row: a stat_corrections entry whose value is not the value the row carries,
    or whose rule is not one of the approved rules.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set provider_names = {
    'minutes': 'minutes_played', 'offsides': 'offsides', 'shots': 'shots_total', 'shots_on_target': 'shots_on',
    'goals': 'goals_total', 'goals_against': 'goals_against', 'assists': 'goals_assists', 'saves': 'saves',
    'passes': 'passes_total', 'passes_key': 'passes_key', 'passes_accurate': 'passes_accuracy_percent',
    'tackles': 'tackles_total', 'blocks': 'tackles_blocks', 'interceptions': 'tackles_interceptions',
    'duels': 'duels_total', 'duels_won': 'duels_won', 'dribbles': 'dribbles_attempts',
    'dribbles_success': 'dribbles_success', 'dribbles_against': 'dribbles_past', 'fouls': 'fouls_committed',
    'fouls_against': 'fouls_drawn', 'cards_yellow': 'cards_yellow', 'cards_red': 'cards_red',
    'penalties_won': 'penalty_won', 'penalties_committed': 'penalty_committed',
    'penalties_scored': 'penalty_scored', 'penalties_missed': 'penalty_missed', 'penalties_saved': 'penalty_saved'
} %}
{% set stats = provider_names | list %}
{% set rules = [
    'goals_from_events', 'penalty_goals_limited_to_goals', 'penalties_scored_matched_to_penalty_goals',
    'raised_to_open_play_goals', 'raised_to_shots_on_target', 'matched_to_team_goals_conceded',
    'limited_to_opponent_shots_on_target', 'opponent_shots_on_target_unverified', 'limited_to_whole',
    'limited_to_card_maximum', 'raised_to_part', 'limited_to_team_goals'
] %}

with players as (
    select * from {{ ref('base_apif__fixture_players') }}
),

-- The provider's own values, per fetch: "counted" means the provider delivered a value, never a
-- zero the cleaning filled in from a second source. Joined to base on the fetch it kept. Where the
-- provider lists a player twice in that fetch, base keeps one row by its own rule, so a value counts
-- as delivered only if both rows carry it, and a positive value in either counts as having played.
delivered as (
    select
        league_code,
        fixture_id,
        player_id,
        raw_ingested_at,
        {% for stat, name in provider_names.items() %}
        if(logical_and({{ name }} is not null), max({{ name }}), null) as {{ stat }},
        {% endfor %}
        greatest(
            {% for stat, name in provider_names.items() if stat != 'minutes' %}coalesce(max({{ name }}), 0), {% endfor %}0
        ) > 0 as has_positive_stat
    from {{ ref('stg_apif__fixture_players') }}
    group by league_code, fixture_id, player_id, raw_ingested_at
),

fixtures as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id,
        goals_home,
        goals_away
    from {{ ref('base_apif__fixtures_next') }}
),

events as (
    select
        fixture_id,
        team_id,
        player_id,
        event_type,
        event_detail
    from {{ ref('base_apif__fixture_events') }}
    where event_comments is distinct from 'Penalty Shootout'
),

fixtures_with_events as (
    select distinct fixture_id
    from {{ ref('base_apif__fixture_events') }}
    where event_type in ('subst', 'Card')
),

team_events as (
    select
        fixture_id,
        team_id,
        countif(event_type = 'Goal' and event_detail in ('Normal Goal', 'Penalty')) as goal_events,
        countif(event_type = 'Goal' and event_detail in ('Normal Goal', 'Penalty') and player_id is null)
            as goal_events_without_scorer,
        countif(event_type = 'Goal' and event_detail = 'Own Goal') as own_goals,
        countif(event_type = 'Goal' and event_detail = 'Penalty') as penalty_goal_events,
        countif(event_type = 'Goal' and event_detail = 'Missed Penalty') as missed_penalty_events
    from events
    group by fixture_id, team_id
),

player_goal_events as (
    select
        fixture_id,
        team_id,
        player_id,
        count(*) as goals
    from events
    where event_type = 'Goal' and event_detail in ('Normal Goal', 'Penalty') and player_id is not null
    group by fixture_id, team_id, player_id
),

team_lines as (
    select
        fixture_id,
        team_id,
        shots_total,
        shots_on_goal
    from {{ ref('base_apif__fixture_statistics') }}
),

rows_in_context as (
    select
        p.*,
        if(p.team_id = f.home_team_id, f.away_team_id, f.home_team_id) as opponent_team_id,
        if(p.team_id = f.home_team_id, f.goals_home, f.goals_away) as team_goals_for,
        if(p.team_id = f.home_team_id, f.goals_away, f.goals_home) as team_goals_conceded,
        coalesce(te.own_goals, 0) as team_own_goals,
        coalesce(oe.own_goals, 0) as opponent_own_goals,
        coalesce(oe.penalty_goal_events, 0) as opponent_penalty_goal_events,
        coalesce(oe.missed_penalty_events, 0) as opponent_missed_penalty_events,
        ol.shots_total as opponent_shots,
        ol.shots_on_goal as opponent_shots_on_target,
        {% for stat in stats %}
        countif(d.{{ stat }} is not null) over fixture as {{ stat }}_values_in_match,
        {% endfor %}
        countif(p.position_code = 'G' and d.saves is not null) over fixture as keeper_saves_values,
        countif(p.position_code = 'G' and d.goals_against is not null) over fixture as keeper_goals_against_values,
        coalesce(
            sum(if(d.passes is not null and d.passes_accurate is not null, d.passes, null)) over fixture > 0,
            false
        ) as match_has_pass_data,
        coalesce(d.has_positive_stat, false) or coalesce(pge.goals, 0) > 0 as did_something,
        countif(p.position_code = 'G' and p.minutes > 0) over team_match as team_keepers_with_minutes,
        sum(if(p.position_code = 'G' and p.minutes > 0, p.goals_against, null)) over team_match
            as team_keepers_goals_against,
        sum(p.assists) over team_match as team_assists
    from players as p
    left join delivered as d
        on
            p.league_code = d.league_code and p.fixture_id = d.fixture_id and p.player_id = d.player_id
            and p.raw_ingested_at = d.raw_ingested_at
    left join player_goal_events as pge
        on p.fixture_id = pge.fixture_id and p.team_id = pge.team_id and p.player_id = pge.player_id
    left join fixtures as f on p.fixture_id = f.fixture_id
    left join team_events as te on p.fixture_id = te.fixture_id and p.team_id = te.team_id
    left join team_events as oe
        on
            p.fixture_id = oe.fixture_id
            and oe.team_id = if(p.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
    left join team_lines as ol
        on
            p.fixture_id = ol.fixture_id
            and ol.team_id = if(p.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
    window
        fixture as (partition by p.league_code, p.fixture_id),
        team_match as (partition by p.league_code, p.fixture_id, p.team_id)
),

corrected_stats as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id,
        correction.stat
    from players, unnest(stat_corrections) as correction
),

violations as (
    {% for stat in stats %}
    select
        r.league_code,
        r.fixture_id,
        r.team_id,
        r.player_id,
        'blank_where_counted' as rule_broken,
        '{{ stat }}' as detail
    from rows_in_context as r
    left join corrected_stats as c
        on
            r.league_code = c.league_code and r.fixture_id = c.fixture_id and r.team_id = c.team_id
            and r.player_id = c.player_id and c.stat = '{{ stat }}'
    where
        r.{{ stat }} is null
        and r.{{ stat }}_values_in_match > 0
        and c.stat is null
        {% if stat in ['saves', 'goals_against'] %}
        and not (r.position_code = 'G' and r.keeper_{{ stat }}_values = 0)
        {% endif %}
        {% if stat == 'minutes' %}
        and not r.did_something
        {% endif %}
        {% if stat == 'passes_accurate' %}
        and r.match_has_pass_data
        {% endif %}

    union all
    {% endfor %}

    select league_code, fixture_id, team_id, player_id, 'part_above_whole', 'passes_accurate'
    from rows_in_context where passes_accurate > passes
    union all
    select league_code, fixture_id, team_id, player_id, 'part_above_whole', 'passes_key'
    from rows_in_context where passes_key > passes
    union all
    select league_code, fixture_id, team_id, player_id, 'part_above_whole', 'dribbles_success'
    from rows_in_context where dribbles_success > dribbles
    union all
    select league_code, fixture_id, team_id, player_id, 'part_above_whole', 'duels_won'
    from rows_in_context where duels_won > duels
    union all
    select league_code, fixture_id, team_id, player_id, 'part_above_whole', 'shots_on_target'
    from rows_in_context where shots_on_target > shots
    union all
    select league_code, fixture_id, team_id, player_id, 'open_play_goals_above_shots_on_target', ''
    from rows_in_context where goals - goals_penalty > shots_on_target
    union all
    select league_code, fixture_id, team_id, player_id, 'penalty_goals_above_goals', ''
    from rows_in_context where goals_penalty > goals or goals_penalty < 0
    union all
    select league_code, fixture_id, team_id, player_id, 'penalties_scored_not_penalty_goals', ''
    from rows_in_context where penalties_scored is distinct from goals_penalty
    union all
    select league_code, fixture_id, team_id, player_id, 'card_maximum', ''
    from rows_in_context where cards_yellow > 2 or cards_red > 1
    union all
    select league_code, fixture_id, team_id, player_id, 'goals_conceded_above_team', ''
    from rows_in_context where goals_against > team_goals_conceded
    union all
    select league_code, fixture_id, team_id, player_id, 'sole_keeper_goals_conceded', ''
    from rows_in_context
    where
        position_code = 'G' and team_keepers_with_minutes = 1 and minutes >= 90
        and goals_against != team_goals_conceded
    union all
    select league_code, fixture_id, team_id, player_id, 'keepers_goals_conceded_above_team', ''
    from rows_in_context
    where
        position_code = 'G' and minutes > 0 and team_keepers_with_minutes > 1
        and team_keepers_goals_against > team_goals_conceded
    union all
    select league_code, fixture_id, team_id, player_id, 'assists_above_team_goals', ''
    from rows_in_context
    where assists > greatest(team_goals_for - coalesce(goals, 0), 0)
    union all
    select distinct league_code, fixture_id, team_id, cast(null as int64), 'team_assists_above_team_goals', ''
    from rows_in_context
    where team_assists > team_goals_for
    union all
    select league_code, fixture_id, team_id, player_id, 'saves_above_ceiling', ''
    from rows_in_context
    where
        saves > opponent_shots_on_target + opponent_missed_penalty_events
        and opponent_shots_on_target >= team_goals_conceded - opponent_penalty_goal_events - opponent_own_goals
        and (opponent_shots is null or opponent_shots_on_target <= opponent_shots)
    union all
    select league_code, fixture_id, team_id, player_id, 'correction_not_on_row', correction.stat
    from players, unnest(stat_corrections) as correction
    where
        correction.rule not in ('{{ rules | join("', '") }}')
        or correction.cleaned_value is distinct from case correction.stat
            {% for stat in stats %}
            when '{{ stat }}' then {{ stat }}
            {% endfor %}
            when 'goals_penalty' then goals_penalty
        end
),

-- The team's goals must add up to the score wherever one of the two sources does.
team_goal_sources as (
    select
        r.league_code,
        r.fixture_id,
        r.team_id,
        any_value(r.team_goals_for) as score,
        any_value(r.team_own_goals) as own_goals,
        sum(r.goals) as cleaned_goals,
        logical_and(r.goals is not null) as all_goals_known,
        sum(
            if(
                c.stat is not null,
                coalesce(c.provider_value, 0),
                r.goals
            )
        ) as count_goals,
        logical_and(c.stat is not null or r.goals is not null) as count_known,
        sum(coalesce(pge.goals, 0)) as placed_event_goals,
        any_value(coalesce(te.goal_events, 0)) as goal_events,
        any_value(coalesce(te.goal_events_without_scorer, 0)) as goal_events_without_scorer,
        logical_or(fe.fixture_id is not null) as has_events
    from rows_in_context as r
    left join (
        select players.league_code, players.fixture_id, players.team_id, players.player_id, correction.provider_value,
            correction.stat
        from players, unnest(stat_corrections) as correction
        where correction.rule = 'goals_from_events'
    ) as c
        on r.league_code = c.league_code and r.fixture_id = c.fixture_id and r.team_id = c.team_id
        and r.player_id = c.player_id
    left join player_goal_events as pge
        on r.fixture_id = pge.fixture_id and r.team_id = pge.team_id and r.player_id = pge.player_id
    left join team_events as te
        on r.fixture_id = te.fixture_id and r.team_id = te.team_id
    left join fixtures_with_events as fe
        on r.fixture_id = fe.fixture_id
    group by r.league_code, r.fixture_id, r.team_id
)

select * from violations
union all
select
    league_code,
    fixture_id,
    team_id,
    cast(null as int64) as player_id,
    'goals_do_not_add_up' as rule_broken,
    concat('score ', cast(score as string), ', players ', coalesce(cast(cleaned_goals as string), 'blank'))
        as detail
from team_goal_sources
where
    score is not null
    and not (all_goals_known and cleaned_goals + own_goals = score)
    and (
        (count_known and count_goals + own_goals = score)
        or (
            has_events
            and goal_events_without_scorer = 0
            and goal_events + own_goals = score
            and placed_event_goals = goal_events
        )
    )
