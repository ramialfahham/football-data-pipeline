{#
  mart_team_competitions' cup_status follows one tie of the reached round: the tie against the
  opponent of the team's latest fixture in that round, or the round's latest tie when that fixture
  names no opponent. While that tie is unplayed, the team is through when it won the latest tie of
  the round before, or when the round before is a table. This recomputes both ties from
  mart_competition_fixtures and int_knockout_ties. Each failing row is a cup_status the ties do not
  give.
#}
{{ config(store_failures = true, severity = 'error') }}

with sides as (
    select
        league_code,
        season_api_year,
        home_team_sk as team_sk,
        away_team_sk as opponent_team_sk,
        round_name,
        round_sequence,
        kickoff_datetime,
        fixture_sk
    from {{ ref('mart_competition_fixtures') }}
    where home_team_sk is not null
    union all
    select
        league_code,
        season_api_year,
        away_team_sk as team_sk,
        home_team_sk as opponent_team_sk,
        round_name,
        round_sequence,
        kickoff_datetime,
        fixture_sk
    from {{ ref('mart_competition_fixtures') }}
    where away_team_sk is not null
),

ties as (
    select * from {{ ref('int_knockout_ties') }}
),

-- A team's tie in a round that no other tie of its in that round follows.
latest_ties as (
    select a.*
    from ties as a
    left join ties as b
        on
            a.league_code = b.league_code
            and a.season_api_year = b.season_api_year
            and a.round_name = b.round_name
            and a.team_sk = b.team_sk
            and (
                a.last_kickoff_datetime < b.last_kickoff_datetime
                or (a.last_kickoff_datetime = b.last_kickoff_datetime and a.opponent_team_sk > b.opponent_team_sk)
            )
    where b.team_sk is null
),

reached_fixtures as (
    select
        c.team_sk,
        c.league_code,
        c.season_api_year,
        c.cup_status,
        c.reached_round_name,
        s.round_sequence,
        s.opponent_team_sk
    from {{ ref('mart_team_competitions') }} as c
    inner join sides as s
        on
            c.team_sk = s.team_sk
            and c.league_code = s.league_code
            and c.season_api_year = s.season_api_year
            and c.reached_round_name = s.round_name
    where c.reached_round_stage_kind in ('knockout', 'final')
    qualify row_number() over (
        partition by c.team_sk, c.league_code, c.season_api_year
        order by s.round_sequence desc, s.kickoff_datetime desc, s.fixture_sk desc
    ) = 1
),

reached_ties as (
    select
        r.*,
        coalesce(own.won, latest.won) as won,
        coalesce(own.legs_played, latest.legs_played) as legs_played
    from reached_fixtures as r
    left join ties as own
        on
            r.league_code = own.league_code
            and r.season_api_year = own.season_api_year
            and r.reached_round_name = own.round_name
            and r.team_sk = own.team_sk
            and r.opponent_team_sk = own.opponent_team_sk
    left join latest_ties as latest
        on
            r.league_code = latest.league_code
            and r.season_api_year = latest.season_api_year
            and r.reached_round_name = latest.round_name
            and r.team_sk = latest.team_sk
            and own.team_sk is null
),

team_rounds as (
    select distinct
        s.team_sk,
        s.league_code,
        s.season_api_year,
        s.round_name,
        s.round_sequence,
        k.round_stage_kind
    from sides as s
    left join {{ ref('int_round_names') }} as k
        on
            s.league_code = k.league_code
            and s.season_api_year = k.season_api_year
            and s.round_name = k.round_name
    where coalesce(k.round_stage_kind, '') != 'placement'
),

waiting as (
    select
        r.team_sk,
        r.league_code,
        r.season_api_year,
        r.cup_status,
        p.round_stage_kind = 'table' or coalesce(previous_tie.won, false) as is_through
    from reached_ties as r
    inner join team_rounds as p
        on
            r.team_sk = p.team_sk
            and r.league_code = p.league_code
            and r.season_api_year = p.season_api_year
            and r.round_sequence > p.round_sequence
    left join latest_ties as previous_tie
        on
            p.league_code = previous_tie.league_code
            and p.season_api_year = previous_tie.season_api_year
            and p.round_name = previous_tie.round_name
            and p.team_sk = previous_tie.team_sk
    where r.won is null and r.legs_played = 0
    qualify row_number() over (
        partition by r.team_sk, r.league_code, r.season_api_year
        order by p.round_sequence desc
    ) = 1
)

select
    team_sk,
    league_code,
    season_api_year,
    cup_status,
    won as tie_won,
    legs_played as tie_legs_played
from reached_ties
where
    (won = false and cup_status is distinct from 'knocked_out')
    or (won and coalesce(cup_status not in ('winners', 'through'), true))
    or (won is null and legs_played > 0 and cup_status is not null)
    or (won is null and cup_status in ('knocked_out', 'winners'))

union all

select
    team_sk,
    league_code,
    season_api_year,
    cup_status,
    null as tie_won,
    0 as tie_legs_played
from waiting
where coalesce(cup_status = 'through', false) != coalesce(is_through, false)
