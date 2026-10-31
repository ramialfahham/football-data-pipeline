{#
  A domestic league's official table at every kick-off of its season: once each league match
  kicks off, every team's matches played, table points and place in its section, as the league's
  own regulation orders them. The team state at each kick-off comes from
  int_team_season__table_state, the legs from int_team_season__table_legs.

  The order follows the league's rule rows in league_tiebreak_rules for that season and phase.
  Head-to-head criteria form a mini-table of the teams still level on every criterion before
  them, and h2h2 criteria repeat it for the teams still level after it. A criterion with a
  condition counts only where it holds. Teams still level when the rules reach a criterion the
  results cannot settle (fair play, lots) have no place. A league-season and phase with no rule
  rows is ordered by points alone, so teams level on points have no place.

  Grain: (league_code, season_api_year, group_name, table_at, team_sk).
#}

with team_state as (
    select * from {{ ref('int_team_season__table_state') }}
),

single_table_seasons as (
    select distinct
        league_code,
        season_api_year
    from team_state
),

rule_rows as (
    select
        league_code,
        from_season,
        phase,
        criterion_order,
        criterion,
        condition
    from {{ ref('league_tiebreak_rules') }}
),

-- each league-season and phase follows the latest rule version starting by that season
season_rules as (
    select
        t.league_code,
        t.season_api_year,
        r.phase,
        r.criterion_order,
        r.criterion,
        r.condition
    from single_table_seasons as t
    inner join rule_rows as r
        on
            t.league_code = r.league_code
            and t.season_api_year >= r.from_season
    qualify r.from_season = max(r.from_season) over (partition by t.league_code, t.season_api_year, r.phase)
),

-- a league-season and phase with no rule rows is ordered by points alone
phases as (
    select phase from unnest(['in_season', 'end_of_season']) as phase
),

points_only as (
    select
        1 as criterion_order,
        'points' as criterion
    union all
    select
        2 as criterion_order,
        'undecidable' as criterion
),

ruled_phases as (
    select distinct
        league_code,
        season_api_year,
        phase
    from season_rules
),

applied_rules as (
    select * from season_rules
    union all
    select
        t.league_code,
        t.season_api_year,
        p.phase,
        d.criterion_order,
        d.criterion,
        cast(null as string) as condition
    from single_table_seasons as t
    cross join phases as p
    cross join points_only as d
    left join ruled_phases as rp
        on
            t.league_code = rp.league_code
            and t.season_api_year = rp.season_api_year
            and p.phase = rp.phase
    where rp.phase is null
),

legs as (
    select * from {{ ref('int_team_season__table_legs') }}
),

league_legs as (
    select * from legs
    where not is_temporary
),

-- every leg the table counts: a played table match from its kick-off, a temporary result between
-- its dates
counted_legs as (
    select
        league_code,
        season_api_year,
        leg_key,
        team_sk,
        opponent_team_sk,
        home_away,
        goals,
        goals_against,
        result,
        points,
        counts_from,
        counts_until
    from legs
    where round_stage_kind = 'table'
),

-- one value per team, moment and rule row; head-to-head values are filled in below
criteria as (
    select
        ts.league_code,
        ts.season_api_year,
        ts.group_name,
        ts.table_at,
        ts.team_sk,
        sr.criterion_order,
        sr.criterion,
        sr.condition,
        case sr.criterion
            when 'points' then ts.table_points
            when 'points_lost' then ts.table_points - 3 * ts.played
            when 'goal_difference' then ts.goal_difference
            when 'goals' then ts.goals_for
            when 'wins' then ts.wins
            when 'away_wins' then ts.away_wins
            when 'away_goals' then ts.away_goals
            when 'previous_position' then -coalesce(ts.previous_position, 999)
            else 0
        end as base_value
    from team_state as ts
    inner join applied_rules as sr
        on
            ts.league_code = sr.league_code
            and ts.season_api_year = sr.season_api_year
            and ts.phase = sr.phase
),

-- the criteria before the first head-to-head one decide who is level for the mini-table
pre_keys as (
    select
        league_code,
        season_api_year,
        group_name,
        table_at,
        team_sk,
        coalesce(string_agg(
            if(is_before_h2h, format('%07d', 5000000 + base_value), null), '' order by criterion_order
        ), '') as pre_key_1
    from (
        select
            *,
            criterion_order < coalesce(min(if(starts_with(criterion, 'h2h'), criterion_order, null)) over (
                partition by league_code, season_api_year, group_name, table_at, team_sk
            ), 999) as is_before_h2h
        from criteria
    )
    group by league_code, season_api_year, group_name, table_at, team_sk
),

h2h_1_games as (
    select
        a.league_code,
        a.season_api_year,
        a.group_name,
        a.table_at,
        a.team_sk,
        a.pre_key_1,
        count(l.leg_key) as h2h_games,
        count(distinct l.opponent_team_sk) as h2h_opponents_met,
        coalesce(sum(l.points), 0) as h2h_points,
        coalesce(sum(l.goals - l.goals_against), 0) as h2h_goal_difference,
        coalesce(sum(l.goals), 0) as h2h_goals,
        coalesce(sum(if(l.home_away = 'away', l.goals, 0)), 0) as h2h_away_goals
    from pre_keys as a
    left join pre_keys as b
        on
            a.league_code = b.league_code
            and a.season_api_year = b.season_api_year
            and a.group_name = b.group_name
            and a.table_at = b.table_at
            and a.pre_key_1 = b.pre_key_1
            and a.team_sk != b.team_sk
    left join counted_legs as l
        on
            a.team_sk = l.team_sk
            and b.team_sk = l.opponent_team_sk
            and a.league_code = l.league_code
            and a.season_api_year = l.season_api_year
            and a.table_at >= l.counts_from
            and (l.counts_until is null or a.table_at < l.counts_until)
    group by a.league_code, a.season_api_year, a.group_name, a.table_at, a.team_sk, a.pre_key_1
),

-- a play-off between level teams is a league match outside the table rounds, won on aggregate
playoff_wins as (
    select
        a.league_code,
        a.season_api_year,
        a.group_name,
        a.table_at,
        a.team_sk,
        sum(l.goals - l.goals_against) as playoff_wins
    from pre_keys as a
    inner join pre_keys as b
        on
            a.league_code = b.league_code
            and a.season_api_year = b.season_api_year
            and a.group_name = b.group_name
            and a.table_at = b.table_at
            and a.pre_key_1 = b.pre_key_1
            and a.team_sk != b.team_sk
    inner join league_legs as l
        on
            a.team_sk = l.team_sk
            and b.team_sk = l.opponent_team_sk
            and a.league_code = l.league_code
            and a.season_api_year = l.season_api_year
            and coalesce(l.round_stage_kind, '') != 'table'
            and a.table_at >= l.kickoff_datetime
    group by a.league_code, a.season_api_year, a.group_name, a.table_at, a.team_sk
),

h2h_1_sized as (
    select
        *,
        count(*) over (
            partition by league_code, season_api_year, group_name, table_at, pre_key_1
        ) as tied_teams
    from h2h_1_games
),

h2h_1 as (
    select
        g.*,
        logical_and(g.h2h_games = 2 * (g.tied_teams - 1)) over (
            partition by g.league_code, g.season_api_year, g.group_name, g.table_at, g.pre_key_1
        ) as is_complete,
        -- a mini-table counts only while every pair has met as often: unequal meetings make it unfair
        logical_and(
            g.h2h_opponents_met = g.tied_teams - 1 and g.h2h_games in (g.tied_teams - 1, 2 * (g.tied_teams - 1))
        ) over (
            partition by g.league_code, g.season_api_year, g.group_name, g.table_at, g.pre_key_1
        ) as is_met_equally,
        coalesce(p.playoff_wins, 0) as playoff_wins
    from h2h_1_sized as g
    left join playoff_wins as p
        on
            g.league_code = p.league_code
            and g.season_api_year = p.season_api_year
            and g.group_name = p.group_name
            and g.table_at = p.table_at
            and g.team_sk = p.team_sk
),

-- every criterion from the first head-to-head one to the first h2h2 one, as the rule applies
-- it, decides who is still level for the second pass
first_pass_keys as (
    select
        c.league_code,
        c.season_api_year,
        c.group_name,
        c.table_at,
        c.team_sk,
        string_agg(format('%07d', 5000000 + case
            when not starts_with(c.criterion, 'h2h_') and c.criterion != 'playoff_winner' then c.base_value
            when c.condition = 'all_h2h_played' and not h1.is_complete then 0
            when c.condition = 'all_h2h_met' and not h1.is_met_equally then 0
            when c.condition = 'two_teams_only' and h1.tied_teams != 2 then 0
            when c.condition = 'three_plus_only' and h1.tied_teams < 3 then 0
            when c.criterion = 'playoff_winner' then h1.playoff_wins
            when c.criterion = 'h2h_points' then h1.h2h_points
            when c.criterion = 'h2h_goal_difference' then h1.h2h_goal_difference
            when c.criterion = 'h2h_goals' then h1.h2h_goals
            else h1.h2h_away_goals
        end), '' order by c.criterion_order) as first_pass_key
    from (
        select
            *,
            min(if(starts_with(criterion, 'h2h_'), criterion_order, null)) over (
                partition by league_code, season_api_year, group_name, table_at, team_sk
            ) as first_h2h_order,
            min(if(starts_with(criterion, 'h2h2_'), criterion_order, null)) over (
                partition by league_code, season_api_year, group_name, table_at, team_sk
            ) as first_h2h2_order
        from criteria
    ) as c
    inner join h2h_1 as h1
        on
            c.league_code = h1.league_code
            and c.season_api_year = h1.season_api_year
            and c.group_name = h1.group_name
            and c.table_at = h1.table_at
            and c.team_sk = h1.team_sk
    where c.criterion_order >= c.first_h2h_order and c.criterion_order < coalesce(c.first_h2h2_order, 999)
    group by c.league_code, c.season_api_year, c.group_name, c.table_at, c.team_sk
),

pre_keys_2 as (
    select
        h.league_code,
        h.season_api_year,
        h.group_name,
        h.table_at,
        h.team_sk,
        concat(h.pre_key_1, coalesce(f.first_pass_key, '')) as pre_key_2
    from h2h_1 as h
    left join first_pass_keys as f
        on
            h.league_code = f.league_code
            and h.season_api_year = f.season_api_year
            and h.group_name = f.group_name
            and h.table_at = f.table_at
            and h.team_sk = f.team_sk
),

h2h_2_games as (
    select
        a.league_code,
        a.season_api_year,
        a.group_name,
        a.table_at,
        a.team_sk,
        a.pre_key_2,
        count(l.leg_key) as h2h_games,
        count(distinct l.opponent_team_sk) as h2h_opponents_met,
        coalesce(sum(l.points), 0) as h2h_points,
        coalesce(sum(l.goals - l.goals_against), 0) as h2h_goal_difference,
        coalesce(sum(l.goals), 0) as h2h_goals
    from pre_keys_2 as a
    left join pre_keys_2 as b
        on
            a.league_code = b.league_code
            and a.season_api_year = b.season_api_year
            and a.group_name = b.group_name
            and a.table_at = b.table_at
            and a.pre_key_2 = b.pre_key_2
            and a.team_sk != b.team_sk
    left join counted_legs as l
        on
            a.team_sk = l.team_sk
            and b.team_sk = l.opponent_team_sk
            and a.league_code = l.league_code
            and a.season_api_year = l.season_api_year
            and a.table_at >= l.counts_from
            and (l.counts_until is null or a.table_at < l.counts_until)
    group by a.league_code, a.season_api_year, a.group_name, a.table_at, a.team_sk, a.pre_key_2
),

h2h_2_sized as (
    select
        *,
        count(*) over (
            partition by league_code, season_api_year, group_name, table_at, pre_key_2
        ) as tied_teams
    from h2h_2_games
),

h2h_2 as (
    select
        *,
        logical_and(h2h_games = 2 * (tied_teams - 1)) over (
            partition by league_code, season_api_year, group_name, table_at, pre_key_2
        ) as is_complete,
        logical_and(
            h2h_opponents_met = tied_teams - 1 and h2h_games in (tied_teams - 1, 2 * (tied_teams - 1))
        ) over (
            partition by league_code, season_api_year, group_name, table_at, pre_key_2
        ) as is_met_equally
    from h2h_2_sized
),

valued as (
    select
        c.league_code,
        c.season_api_year,
        c.group_name,
        c.table_at,
        c.team_sk,
        c.criterion_order,
        c.criterion,
        case
            when
                c.condition = 'all_h2h_played'
                and not if(starts_with(c.criterion, 'h2h2_'), h2.is_complete, h1.is_complete)
                then 0
            when
                c.condition = 'all_h2h_met'
                and not if(starts_with(c.criterion, 'h2h2_'), h2.is_met_equally, h1.is_met_equally)
                then 0
            when c.condition = 'two_teams_only' and h1.tied_teams != 2 then 0
            when c.condition = 'three_plus_only' and h1.tied_teams < 3 then 0
            when c.criterion = 'h2h_points' then h1.h2h_points
            when c.criterion = 'h2h_goal_difference' then h1.h2h_goal_difference
            when c.criterion = 'h2h_goals' then h1.h2h_goals
            when c.criterion = 'h2h_away_goals' then h1.h2h_away_goals
            when c.criterion = 'h2h2_points' then h2.h2h_points
            when c.criterion = 'h2h2_goal_difference' then h2.h2h_goal_difference
            when c.criterion = 'h2h2_goals' then h2.h2h_goals
            when c.criterion = 'playoff_winner' then h1.playoff_wins
            else c.base_value
        end as criterion_value
    from criteria as c
    inner join h2h_1 as h1
        on
            c.league_code = h1.league_code
            and c.season_api_year = h1.season_api_year
            and c.group_name = h1.group_name
            and c.table_at = h1.table_at
            and c.team_sk = h1.team_sk
    inner join h2h_2 as h2
        on
            c.league_code = h2.league_code
            and c.season_api_year = h2.season_api_year
            and c.group_name = h2.group_name
            and c.table_at = h2.table_at
            and c.team_sk = h2.team_sk
),

keyed as (
    select
        league_code,
        season_api_year,
        group_name,
        table_at,
        team_sk,
        string_agg(format('%07d', 5000000 + criterion_value), '' order by criterion_order) as sort_key,
        logical_or(criterion = 'undecidable') as ends_undecided
    from valued
    group by league_code, season_api_year, group_name, table_at, team_sk
),

placed as (
    select
        *,
        rank() over (
            partition by league_code, season_api_year, group_name, table_at
            order by sort_key desc
        ) as rank_by_rules,
        count(*) over (
            partition by league_code, season_api_year, group_name, table_at, sort_key
        ) as teams_on_key
    from keyed
)

select
    ts.league_code,
    ts.season_api_year,
    ts.group_name,
    ts.table_at,
    ts.team_sk,
    ts.phase,
    ts.played,
    ts.points_from_results,
    ts.table_points,
    ts.goal_difference,
    ts.goals_for,
    p.rank_by_rules as place_by_rules,
    ts.points_from_results - ts.table_points as points_taken,
    p.teams_on_key > 1 as is_level_after_rules,
    if(p.teams_on_key > 1 and p.ends_undecided, null, p.rank_by_rules) as table_position
from team_state as ts
inner join placed as p
    on
        ts.league_code = p.league_code
        and ts.season_api_year = p.season_api_year
        and ts.group_name = p.group_name
        and ts.table_at = p.table_at
        and ts.team_sk = p.team_sk
