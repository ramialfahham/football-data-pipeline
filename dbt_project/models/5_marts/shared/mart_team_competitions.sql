{#
  The Team page's Competitions block: one row per team, competition and season the team has a
  fixture in. Each row carries the team's standing in that competition's table, the round of its
  latest played match (a league's "Matchday N"), and the round it has reached: its latest round,
  played or scheduled, leaving out a third-place match, so a semi-final loser has reached the
  semi-final.

  For a round of ties (int_round_names' round_stage_kind knockout or final) cup_status follows the
  tie in that round (int_knockout_ties):
    - knocked_out when the team lost it;
    - winners when it won a final of one tie (a cup's, or a league's play-off final for its
      title), outside a qualifying competition, where winning the final is qualifying; a round
      named final with more ties, as K League's promotion play-offs, is no title;
    - through when it won any other tie, or when it is drawn into the round's unplayed tie after
      winning its tie in the round before, or after a table round;
    - NULL while the tie is being played or undecided, in a first round not yet played, and in a
      table round, where the standing tells the story.
  The standing is the team's table section named in its latest played round (Liga MX's Clausura
  while the Clausura is played), otherwise its section with the most matches played; a ranking
  section is not a table.

  Reads mart_competition_fixtures and mart_standings in its own layer, for the round order the
  competition pages use and the tables they show. Grain: (team_sk, league_code, season_api_year).
#}

with fixtures as (
    select * from {{ ref('mart_competition_fixtures') }}
),

round_kinds as (
    select
        league_code,
        season_api_year,
        round_name,
        round_stage_kind
    from {{ ref('int_round_names') }}
),

ties as (
    select * from {{ ref('int_knockout_ties') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

types as (
    select
        competition_type,
        entity_type
    from {{ ref('competition_types') }}
),

sides as (
    select
        league_code,
        season_api_year,
        home_team_sk as team_sk,
        round_name,
        round_label_i18n_key,
        round_number,
        round_letter,
        round_sequence,
        kickoff_datetime,
        fixture_sk,
        is_played
    from fixtures
    where home_team_sk is not null
    union all
    select
        league_code,
        season_api_year,
        away_team_sk as team_sk,
        round_name,
        round_label_i18n_key,
        round_number,
        round_letter,
        round_sequence,
        kickoff_datetime,
        fixture_sk,
        is_played
    from fixtures
    where away_team_sk is not null
),

team_fixtures as (
    select
        s.*,
        rk.round_stage_kind
    from sides as s
    left join round_kinds as rk
        on
            s.league_code = rk.league_code
            and s.season_api_year = rk.season_api_year
            and s.round_name = rk.round_name
),

latest_played as (
    select *
    from team_fixtures
    where is_played
    qualify row_number() over (
        partition by team_sk, league_code, season_api_year
        order by round_sequence desc, kickoff_datetime desc, fixture_sk desc
    ) = 1
),

-- each team's rounds in order, a third-place match left out, with the round before each
team_rounds as (
    select
        team_sk,
        league_code,
        season_api_year,
        round_name,
        round_stage_kind,
        lag(round_name) over (
            partition by team_sk, league_code, season_api_year order by round_sequence
        ) as previous_round_name,
        lag(round_stage_kind) over (
            partition by team_sk, league_code, season_api_year order by round_sequence
        ) as previous_stage_kind
    from (
        select distinct
            team_sk,
            league_code,
            season_api_year,
            round_name,
            round_sequence,
            round_stage_kind
        from team_fixtures
        where coalesce(round_stage_kind, '') != 'placement'
    )
),

reached as (
    select
        tf.*,
        tr.previous_round_name,
        tr.previous_stage_kind
    from team_fixtures as tf
    inner join team_rounds as tr
        on
            tf.team_sk = tr.team_sk
            and tf.league_code = tr.league_code
            and tf.season_api_year = tr.season_api_year
            and tf.round_name = tr.round_name
    qualify row_number() over (
        partition by tf.team_sk, tf.league_code, tf.season_api_year
        order by tf.round_sequence desc, tf.kickoff_datetime desc, tf.fixture_sk desc
    ) = 1
),

reached_ties as (
    select
        r.team_sk,
        r.league_code,
        r.season_api_year,
        any_value(t.legs_played) as legs_played,
        any_value(t.won) as won
    from reached as r
    inner join ties as t
        on
            r.league_code = t.league_code
            and r.season_api_year = t.season_api_year
            and r.round_name = t.round_name
            and r.team_sk = t.team_sk
    group by r.team_sk, r.league_code, r.season_api_year
),

-- how many ties each round of ties holds: a final is one tie, K League's play-off "Final" two
round_ties as (
    select
        league_code,
        season_api_year,
        round_name,
        count(*) / 2 as ties_in_round
    from ties
    group by league_code, season_api_year, round_name
),

-- the tie of the round before the reached one: a team waiting for an FA Cup replay is not through
previous_ties as (
    select
        r.team_sk,
        r.league_code,
        r.season_api_year,
        any_value(t.won) as previous_won
    from reached as r
    inner join ties as t
        on
            r.league_code = t.league_code
            and r.season_api_year = t.season_api_year
            and r.previous_round_name = t.round_name
            and r.team_sk = t.team_sk
    group by r.team_sk, r.league_code, r.season_api_year
),

standings as (
    select
        s.team_sk,
        s.league_code,
        s.season_api_year,
        s.group_name,
        s.standing_rank,
        s.played,
        s.wins,
        s.draws,
        s.losses,
        s.goals_scored,
        s.goals_conceded,
        s.points
    from {{ ref('mart_standings') }} as s
    left join latest_played as lp
        on
            s.team_sk = lp.team_sk
            and s.league_code = lp.league_code
            and s.season_api_year = lp.season_api_year
    where s.table_kind != 'ranking'
    qualify row_number() over (
        partition by s.team_sk, s.league_code, s.season_api_year
        order by
            coalesce(strpos(lower(lp.round_name), lower(s.group_name)) > 0, false) desc,
            s.played desc,
            s.group_name asc
    ) = 1
)

select
    r.team_sk,
    r.league_code,
    r.season_api_year,
    reg.competition_type,
    typ.entity_type,
    s.group_name as standing_group_name,
    s.standing_rank,
    s.played,
    s.wins,
    s.draws,
    s.losses,
    s.goals_scored as goals_for,
    s.goals_conceded as goals_against,
    s.points,
    lp.round_name as latest_played_round_name,
    lp.round_label_i18n_key as latest_played_round_label_i18n_key,
    lp.round_number as latest_played_round_number,
    lp.round_letter as latest_played_round_letter,
    lp.kickoff_datetime as latest_played_kickoff_datetime,
    r.round_name as reached_round_name,
    r.round_label_i18n_key as reached_round_label_i18n_key,
    r.round_number as reached_round_number,
    r.round_letter as reached_round_letter,
    r.round_stage_kind as reached_round_stage_kind,
    case
        when coalesce(r.round_stage_kind, '') not in ('knockout', 'final') then null
        when rt.won = false then 'knocked_out'
        when
            rt.won
            and r.round_stage_kind = 'final'
            and rd.ties_in_round = 1
            and coalesce(reg.competition_type, '') != 'qualifying'
            then 'winners'
        when rt.won then 'through'
        when
            rt.legs_played = 0
            and (r.previous_stage_kind = 'table' or pt.previous_won)
            then 'through'
    end as cup_status,
    -- the block's order: the domestic league, then the domestic cups, then every other
    -- competition, each group by its latest match
    row_number() over (
        partition by r.team_sk, r.season_api_year
        order by
            case reg.competition_type
                when 'domestic_league' then 1
                when 'domestic_cup' then 2
                when 'domestic_super_cup' then 3
                else 4
            end asc,
            r.kickoff_datetime desc,
            r.league_code asc
    ) as competition_order
from reached as r
left join latest_played as lp
    on
        r.team_sk = lp.team_sk
        and r.league_code = lp.league_code
        and r.season_api_year = lp.season_api_year
left join reached_ties as rt
    on
        r.team_sk = rt.team_sk
        and r.league_code = rt.league_code
        and r.season_api_year = rt.season_api_year
left join round_ties as rd
    on
        r.league_code = rd.league_code
        and r.season_api_year = rd.season_api_year
        and r.round_name = rd.round_name
left join previous_ties as pt
    on
        r.team_sk = pt.team_sk
        and r.league_code = pt.league_code
        and r.season_api_year = pt.season_api_year
left join standings as s
    on
        r.team_sk = s.team_sk
        and r.league_code = s.league_code
        and r.season_api_year = s.season_api_year
left join registry as reg
    on r.league_code = reg.league_code
left join types as typ
    on reg.competition_type = typ.competition_type
