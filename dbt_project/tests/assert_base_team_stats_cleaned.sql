{#
  The cleaning rules hold on every row of base_apif__fixture_statistics, the team's line in a match.
  Returns one row per violation, named by the rule it breaks:

  - missing_team_row: a team of a finished match has no row.
  - blank_where_counted: a count is blank although the other team's line, as the provider delivered
    it (read from stg_apif__fixture_statistics, the fetch base kept), carries a value for it.
    Possession is a share, not a count, and is not checked.
  - card_blank_where_events_prove_none: a card count is blank in a match whose events were
    delivered (a substitution or a card) while the team has no event against that zero: a card of
    that colour or of none, or a video review of a card (an upgrade or a cancelled red counts as red).
  - saves_blank_where_opponent_had_no_shot_on_target.
  - goal_split_blank_where_proven, goal_split_where_unproven, goal_split_not_the_events: penalty and
    own goals are the team's goal events where the match's events were delivered and those events
    add up to its score, 0 where it scored none, and blank otherwise.
  - part_above_whole, open_play_goals_above_shots_on_target, saves_above_ceiling,
    split_does_not_add_up: a contradiction the cleaning must have removed.
  - correction_not_on_row: a stat_corrections entry whose value is not the value the row carries,
    or whose rule is not one of the approved rules.
  A blank the contradiction rule made (recorded in stat_corrections) is not a blank-rule violation.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set provider_names = {
    'shots_on_target': 'Shots on Goal', 'shots_off_target': 'Shots off Goal', 'shots': 'Total Shots',
    'shots_blocked': 'Blocked Shots', 'shots_inside_box': 'Shots insidebox',
    'shots_outside_box': 'Shots outsidebox', 'fouls': 'Fouls', 'corners': 'Corner Kicks',
    'offsides': 'Offsides', 'free_kicks': 'Free Kicks', 'possession_pct': 'Ball Possession', 'cards_yellow': 'Yellow Cards',
    'cards_red': 'Red Cards', 'saves': 'Goalkeeper Saves', 'passes': 'Total passes',
    'passes_accurate': 'Passes accurate'
} %}
{% set rules = [
    'raised_to_open_play_goals', 'raised_to_shots_on_target', 'limited_to_opponent_shots_on_target',
    'opponent_shots_on_target_unverified', 'limited_to_whole', 'own_goals_left_out', 'split_does_not_add_up'
] %}

with lines as (
    select * from {{ ref('base_apif__fixture_statistics') }}
),

-- The provider's own values, per fetch, under the team id base corrects to; base keeps the newest
-- fetch per team-match, and so does this.
fixture_participants as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where home_team_id is not null and away_team_id is not null
),

overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode
    from {{ ref('fixture_team_id_overrides') }}
),

stat_rows as (
    select
        s.league_code,
        s.fixture_id,
        coalesce(a.correct_team_api_id, r.correct_team_api_id, s.team_id) as team_id,
        s.raw_ingested_at,
        s.stat_type,
        s.stat_value_raw
    from {{ ref('stg_apif__fixture_statistics') }} as s
    left join overrides as a
        on s.team_id = a.wrong_team_api_id and a.mode = 'alias'
    left join fixture_participants as p
        on s.fixture_id = p.fixture_id
    left join overrides as r
        on
            s.team_id = r.wrong_team_api_id
            and r.mode = 'reattribute_if_cohabiting'
            and r.correct_team_api_id in (p.home_team_id, p.away_team_id)
            and r.wrong_team_api_id not in (p.home_team_id, p.away_team_id)
    where s.fixture_id is not null and s.team_id is not null
),

delivered as (
    select
        league_code,
        fixture_id,
        team_id,
        {% for stat, name in provider_names.items() %}
        max(if(stat_type = '{{ name }}', safe_cast(regexp_replace(stat_value_raw, r'%', '') as int64), null)) is not null
            as {{ stat }}_delivered{% if not loop.last %},{% endif %}
        {% endfor %}
    from stat_rows
    group by league_code, fixture_id, team_id, raw_ingested_at
    qualify row_number() over (partition by league_code, fixture_id, team_id order by raw_ingested_at desc) = 1
),

fixtures as (
    select
        fixture_id,
        league_code,
        status_short,
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
        event_type,
        event_detail,
        event_comments is not distinct from 'Penalty Shootout' as is_shootout
    from {{ ref('base_apif__fixture_events') }}
),

matches_with_events as (
    select distinct fixture_id
    from events
    where event_type in ('subst', 'Card')
),

team_events as (
    select
        fixture_id,
        team_id,
        countif(not is_shootout and event_type = 'Goal' and event_detail in ('Normal Goal', 'Penalty', 'Own Goal'))
            as goal_events,
        countif(not is_shootout and event_type = 'Goal' and event_detail = 'Penalty') as penalty_goal_events,
        countif(not is_shootout and event_type = 'Goal' and event_detail = 'Own Goal') as own_goal_events,
        countif(not is_shootout and event_type = 'Goal' and event_detail = 'Missed Penalty') as missed_penalty_events,
        countif(
            (event_type = 'Card' and coalesce(event_detail, '') != 'Red Card')
            or (event_type = 'Var' and event_detail = 'Card reviewed')
        ) as events_against_no_yellow,
        countif(
            (event_type = 'Card' and coalesce(event_detail, '') != 'Yellow Card')
            or (event_type = 'Var' and (starts_with(event_detail, 'Card upgrade') or event_detail in ('Red card cancelled', 'Card reviewed')))
        ) as events_against_no_red
    from events
    group by fixture_id, team_id
),

team_matches as (
    select
        fixture_id,
        league_code,
        home_team_id as team_id
    from fixtures
    where
        status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO') and goals_home is not null and goals_away is not null
        and home_team_id is not null and away_team_id is not null
    union all
    select
        fixture_id,
        league_code,
        away_team_id
    from fixtures
    where
        status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO') and goals_home is not null and goals_away is not null
        and home_team_id is not null and away_team_id is not null
),

in_context as (
    select
        l.*,
        if(l.team_id = f.home_team_id, f.away_team_id, f.home_team_id) as opponent_team_id,
        if(l.team_id = f.home_team_id, f.goals_home, f.goals_away) as goals_for,
        f.status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO') and f.goals_home is not null and f.goals_away is not null
            as is_finished,
        me.fixture_id is not null as match_has_events,
        coalesce(te.goal_events, 0) as goal_events,
        coalesce(te.penalty_goal_events, 0) as penalty_goal_events,
        coalesce(te.own_goal_events, 0) as own_goal_events,
        coalesce(te.events_against_no_yellow, 0) as events_against_no_yellow,
        coalesce(te.events_against_no_red, 0) as events_against_no_red,
        o.shots_on_target as opponent_shots_on_target,
        coalesce(oe.missed_penalty_events, 0) as opponent_missed_penalty_events,
        {% for stat in provider_names %}
        od.{{ stat }}_delivered as opponent_{{ stat }}_delivered,
        {% endfor %}
        array(select c.stat from unnest(l.stat_corrections) as c) as corrected_stats
    from lines as l
    left join fixtures as f
        on l.fixture_id = f.fixture_id
    left join lines as o
        on
            l.fixture_id = o.fixture_id
            and o.team_id = if(l.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
    left join matches_with_events as me
        on l.fixture_id = me.fixture_id
    left join team_events as te
        on l.fixture_id = te.fixture_id and l.team_id = te.team_id
    left join team_events as oe
        on l.fixture_id = oe.fixture_id and oe.team_id = if(l.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
    left join delivered as od
        on
            l.league_code = od.league_code
            and l.fixture_id = od.fixture_id
            and od.team_id = if(l.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
),

violations as (
    select
        'missing_team_row' as rule,
        tm.league_code,
        tm.fixture_id,
        tm.team_id,
        cast(null as string) as stat,
        cast(null as string) as detail
    from team_matches as tm
    left join lines as l
        on tm.fixture_id = l.fixture_id and tm.team_id = l.team_id
    where l.fixture_id is null

    {% for stat in provider_names if stat != 'possession_pct' %}
    union all
    select
        'blank_where_counted',
        league_code,
        fixture_id,
        team_id,
        '{{ stat }}',
        null
    from in_context
    where {{ stat }} is null and opponent_{{ stat }}_delivered and '{{ stat }}' not in unnest(corrected_stats)
    {% endfor %}

    union all
    select
        'card_blank_where_events_prove_none',
        league_code,
        fixture_id,
        team_id,
        stat,
        null
    from in_context,
        unnest([
            struct('cards_yellow' as stat, cards_yellow as value, events_against_no_yellow as against),
            struct('cards_red', cards_red, events_against_no_red)
        ])
    where value is null and match_has_events and against = 0

    union all
    select
        'saves_blank_where_opponent_had_no_shot_on_target',
        league_code,
        fixture_id,
        team_id,
        'saves',
        null
    from in_context
    where saves is null and opponent_shots_on_target = 0 and 'saves' not in unnest(corrected_stats)

    union all
    select
        case
            when value is null then 'goal_split_blank_where_proven'
            when not proven then 'goal_split_where_unproven'
            else 'goal_split_not_the_events'
        end,
        league_code,
        fixture_id,
        team_id,
        stat,
        format('model %t, events %d, goals %t', value, from_events, goals_for)
    from (
        select
            *,
            goals_for = 0 or (match_has_events and goal_events = goals_for) as proven
        from in_context
        where is_finished
    ),
        unnest([
            struct('goals_penalty' as stat, goals_penalty as value, if(goals_for = 0, 0, penalty_goal_events) as from_events),
            struct('goals_own', goals_own, if(goals_for = 0, 0, own_goal_events))
        ])
    where
        (value is null and proven)
        or (value is not null and not proven)
        or (value is not null and value != from_events)

    union all
    select
        'part_above_whole',
        league_code,
        fixture_id,
        team_id,
        part,
        format('%d above %d', part_value, whole_value)
    from in_context,
        unnest([
            struct('shots_on_target' as part, shots_on_target as part_value, shots as whole_value),
            struct('shots_inside_box', shots_inside_box, shots),
            struct('passes_accurate', passes_accurate, passes)
        ])
    where part_value > whole_value

    union all
    select
        'open_play_goals_above_shots_on_target',
        league_code,
        fixture_id,
        team_id,
        stat,
        format('%d open-play goals, %d %s', goals_for - goals_penalty - goals_own, value, stat)
    from in_context,
        unnest([
            struct('shots_on_target' as stat, shots_on_target as value),
            struct('shots', shots)
        ])
    where goals_for - goals_penalty - goals_own > value

    union all
    select
        'saves_above_ceiling',
        league_code,
        fixture_id,
        team_id,
        'saves',
        format('%d saves, ceiling %d', saves, opponent_shots_on_target + opponent_missed_penalty_events)
    from in_context
    where saves > opponent_shots_on_target + opponent_missed_penalty_events

    union all
    select
        'split_does_not_add_up',
        league_code,
        fixture_id,
        team_id,
        split,
        format('%d against %d shots', parts, shots)
    from in_context,
        unnest([
            struct('on, off, blocked' as split, shots_on_target + shots_off_target + shots_blocked as parts),
            struct('inside, outside', shots_inside_box + shots_outside_box)
        ])
    where parts != shots

    union all
    select
        'correction_not_on_row',
        l.league_code,
        l.fixture_id,
        l.team_id,
        c.stat,
        format('%t %t', c.cleaned_value, c.rule)
    from lines as l, unnest(l.stat_corrections) as c
    where
        c.rule not in ({% for r in rules %}'{{ r }}'{% if not loop.last %}, {% endif %}{% endfor %})
        or c.cleaned_value is distinct from case c.stat
            {% for stat in provider_names %}
            when '{{ stat }}' then l.{{ stat }}
            {% endfor %}
        end
)

select * from violations
