{#
  Every team's place-free state in a domestic league's official table at every kick-off of its
  season: matches played, points won, table points after the deductions in
  standings_points_adjustments that took effect by that day, goals, wins, away wins and goals, the
  previous season's final place, and the phase (in the season, or the final table once a finished
  season's teams have all played their table matches). The legs come from
  int_team_season__table_legs.

  Only a season where every team sits in one league, conference or group table, and whose table
  results give every team the official table's goals scored and conceded through its matches
  played.

  Grain: (league_code, season_api_year, group_name, table_at, team_sk).
#}

with registry as (
    select league_code
    from {{ ref('competition_registry') }}
    where competition_type = 'domestic_league'
),

sections as (
    select
        s.league_code,
        s.season_api_year,
        s.team_sk,
        s.team_api_id,
        s.group_name,
        s.played,
        s.goals_scored,
        s.goals_conceded,
        s.standing_rank,
        k.table_kind
    from {{ ref('fct_standings') }} as s
    inner join {{ ref('int_standings__section_kinds') }} as k
        on s.group_name = k.group_name
    inner join registry as r
        on s.league_code = r.league_code
    where k.table_kind != 'ranking'
),

single_table_seasons as (
    select
        league_code,
        season_api_year
    from sections
    group by league_code, season_api_year
    having
        countif(table_kind = 'split_round') = 0
        and count(*) = count(distinct team_sk)
),

legs as (
    select * from {{ ref('int_team_season__table_legs') }}
),

league_legs as (
    select * from legs
    where not is_temporary
),

table_legs as (
    select
        *,
        row_number() over (
            partition by team_sk, league_code, season_api_year
            order by kickoff_datetime, fixture_sk
        ) as table_match_number,
        sum(goals) over (
            partition by team_sk, league_code, season_api_year
            order by kickoff_datetime, fixture_sk
        ) as goals_to_date,
        sum(goals_against) over (
            partition by team_sk, league_code, season_api_year
            order by kickoff_datetime, fixture_sk
        ) as goals_against_to_date
    from league_legs
    where round_stage_kind = 'table'
),

-- seasons whose table results give every team the official table's goals through its played
reproduced_seasons as (
    select
        s.league_code,
        s.season_api_year
    from sections as s
    left join table_legs as l
        on
            s.team_sk = l.team_sk
            and s.league_code = l.league_code
            and s.season_api_year = l.season_api_year
            and s.played = l.table_match_number
    group by s.league_code, s.season_api_year
    having
        logical_and(
            s.played = 0
            or coalesce(l.goals_to_date = s.goals_scored and l.goals_against_to_date = s.goals_conceded, false)
        )
),

ranked_sections as (
    select s.*
    from sections as s
    inner join single_table_seasons as t
        on s.league_code = t.league_code and s.season_api_year = t.season_api_year
    inner join reproduced_seasons as rs
        on s.league_code = rs.league_code and s.season_api_year = rs.season_api_year
),

-- a team's final place in a single-table season, for a rule that ranks by the season before
previous_positions as (
    select
        s.team_sk,
        s.league_code,
        s.season_api_year,
        s.standing_rank
    from sections as s
    inner join single_table_seasons as t
        on s.league_code = t.league_code and s.season_api_year = t.season_api_year
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

latest_seasons as (
    select
        league_code,
        max(season_api_year) as latest_season_api_year
    from sections
    group by league_code
),

table_times as (
    select distinct
        l.league_code,
        l.season_api_year,
        l.kickoff_datetime as table_at
    from league_legs as l
    inner join ranked_sections as s
        on l.team_sk = s.team_sk and l.league_code = s.league_code and l.season_api_year = s.season_api_year
),

deduction_steps as (
    select
        league_code,
        season,
        team_id,
        group_name,
        effective_date,
        points_taken
    from {{ ref('standings_points_adjustments') }}
    where rule = 'deduction'
),

totals as (
    select
        tt.league_code,
        tt.season_api_year,
        s.group_name,
        tt.table_at,
        s.team_sk,
        s.team_api_id,
        s.played as final_played,
        count(l.leg_key) as played,
        coalesce(sum(l.points), 0) as points_from_results,
        coalesce(sum(l.goals - l.goals_against), 0) as goal_difference,
        coalesce(sum(l.goals), 0) as goals_for,
        countif(l.result = 'W') as wins,
        countif(l.result = 'W' and l.home_away = 'away') as away_wins,
        coalesce(sum(if(l.home_away = 'away', l.goals, 0)), 0) as away_goals
    from table_times as tt
    inner join ranked_sections as s
        on tt.league_code = s.league_code and tt.season_api_year = s.season_api_year
    left join counted_legs as l
        on
            s.team_sk = l.team_sk
            and s.league_code = l.league_code
            and s.season_api_year = l.season_api_year
            and tt.table_at >= l.counts_from
            and (l.counts_until is null or tt.table_at < l.counts_until)
    group by tt.league_code, tt.season_api_year, s.group_name, tt.table_at, s.team_sk, s.team_api_id, s.played
),

points_taken_by_then as (
    select
        t.league_code,
        t.season_api_year,
        t.group_name,
        t.table_at,
        t.team_sk,
        sum(d.points_taken) as points_taken
    from totals as t
    inner join deduction_steps as d
        on
            t.league_code = d.league_code
            and t.season_api_year = d.season
            and t.team_api_id = d.team_id
            and trim(t.group_name) = trim(d.group_name)
            and date(t.table_at) >= d.effective_date
    group by t.league_code, t.season_api_year, t.group_name, t.table_at, t.team_sk
),

team_state as (
    select
        t.league_code,
        t.season_api_year,
        t.group_name,
        t.table_at,
        t.team_sk,
        t.played,
        t.points_from_results,
        t.goal_difference,
        t.goals_for,
        t.wins,
        t.away_wins,
        t.away_goals,
        prev.standing_rank as previous_position,
        t.points_from_results - coalesce(pt.points_taken, 0) as table_points,
        if(
            t.season_api_year < ls.latest_season_api_year
            and logical_and(t.played = t.final_played) over (
                partition by t.league_code, t.season_api_year, t.group_name, t.table_at
            ),
            'end_of_season',
            'in_season'
        ) as phase
    from totals as t
    inner join latest_seasons as ls
        on t.league_code = ls.league_code
    left join points_taken_by_then as pt
        on
            t.league_code = pt.league_code
            and t.season_api_year = pt.season_api_year
            and t.group_name = pt.group_name
            and t.table_at = pt.table_at
            and t.team_sk = pt.team_sk
    left join previous_positions as prev
        on
            t.team_sk = prev.team_sk
            and t.league_code = prev.league_code
            and t.season_api_year - 1 = prev.season_api_year
)

select * from team_state
