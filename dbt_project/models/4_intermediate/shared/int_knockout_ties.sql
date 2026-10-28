{#
  Every knockout tie seen from each of its two teams: the fixtures of one round of ties (a
  knockout round, a final or a third-place match by int_round_names' round_stage_kind) between
  the same two teams, one leg or two. Once every leg
  is played, the tie goes to the team with more goals over its legs; a level tie goes to the
  winner of its last leg when that leg was decided by a shoot-out or awarded. A level tie without
  one stays undecided (won NULL): an FA Cup draw is decided by its replay, which is a round of its
  own. A tie with a leg still to play is undecided too.
  Grain: (league_code, season_api_year, round_name, team_sk, opponent_team_sk).
#}

with rounds as (
    select
        league_code,
        season_api_year,
        round_name
    from {{ ref('int_round_names') }}
    where round_stage_kind in ('knockout', 'final', 'placement')
),

fixtures as (
    select
        f.fixture_sk,
        f.league_code,
        f.season_api_year,
        f.round_name,
        f.home_team_sk,
        f.away_team_sk,
        f.goals_home,
        f.goals_away,
        f.status_short,
        f.winner_team_sk,
        f.kickoff_datetime,
        f.status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO') as is_played
    from {{ ref('fct_fixture') }} as f
    inner join rounds as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
    where f.home_team_sk is not null and f.away_team_sk is not null
),

sides as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_name,
        home_team_sk as team_sk,
        away_team_sk as opponent_team_sk,
        if(is_played, goals_home, null) as goals_for,
        if(is_played, goals_away, null) as goals_against,
        status_short,
        winner_team_sk,
        kickoff_datetime,
        is_played
    from fixtures
    union all
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_name,
        away_team_sk as team_sk,
        home_team_sk as opponent_team_sk,
        if(is_played, goals_away, null) as goals_for,
        if(is_played, goals_home, null) as goals_against,
        status_short,
        winner_team_sk,
        kickoff_datetime,
        is_played
    from fixtures
),

ties as (
    select
        league_code,
        season_api_year,
        round_name,
        team_sk,
        opponent_team_sk,
        count(*) as legs,
        countif(is_played) as legs_played,
        sum(goals_for) as goals_for,
        sum(goals_against) as goals_against,
        array_agg(
            if(is_played, struct(fixture_sk, status_short, winner_team_sk, kickoff_datetime), null)
            ignore nulls order by kickoff_datetime desc, fixture_sk desc limit 1
        )[safe_offset(0)] as last_played_leg,
        max(kickoff_datetime) as last_kickoff_datetime
    from sides
    group by league_code, season_api_year, round_name, team_sk, opponent_team_sk
)

select
    league_code,
    season_api_year,
    round_name,
    team_sk,
    opponent_team_sk,
    legs,
    legs_played,
    goals_for,
    goals_against,
    last_played_leg.fixture_sk as last_played_fixture_sk,
    last_kickoff_datetime,
    case
        when legs_played < legs then null
        when goals_for != goals_against then 'goals'
        when
            last_played_leg.status_short in ('PEN', 'AWD', 'WO')
            and last_played_leg.winner_team_sk is not null
            then if(last_played_leg.status_short = 'PEN', 'shootout', 'award')
    end as decided_by,
    case
        when legs_played < legs then null
        when goals_for != goals_against then goals_for > goals_against
        when
            last_played_leg.status_short in ('PEN', 'AWD', 'WO')
            and last_played_leg.winner_team_sk is not null
            then last_played_leg.winner_team_sk = team_sk
    end as won
from ties
