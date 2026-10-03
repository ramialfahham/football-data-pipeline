{#
  Building-block team-match leg: one row per (team, finished match), carrying that team's
  cleaned stats AND the opponent's (so danger-zone-conceded etc. are derivable), plus the
  competition's type/entity classification and the dimensions windows need.

  "Finished" includes forfeits (AWD, WO); what they count in is rule R3 in
  models/docs/metric_rules.md. They carry a scoreline and no stat line, and `is_awarded_result`
  marks them.

  Cross-competition and cross-type — the shared foundation every team performance metric
  aggregates over (a metric = a filter + aggregate of these rows). Grain: (fixture_sk, team_sk).

  Built alongside the legacy int_matchday__finished_fixture_team_leg during migration
  (see issue #321); that one is retired once marts cut over to this.
#}

with fixtures as (
    select * from {{ ref('fct_fixture') }}
),

team_stats as (
    select * from {{ ref('fct_fixture_team_stats') }}
),

registry as (
    select * from {{ ref('competition_registry') }}
),

types as (
    select * from {{ ref('competition_types') }}
),

-- Each finished match as two team legs: the home side's perspective and the away side's.
legs as (
    select
        f.fixture_sk,
        f.league_sk,
        f.season_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        f.round_name,
        safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
        'home' as home_away,
        f.home_team_sk as team_sk,
        f.away_team_sk as opponent_team_sk,
        f.goals_home as goals,
        f.goals_away as goals_against,
        case
            when f.goals_home > f.goals_away then 'W'
            when f.goals_home < f.goals_away then 'L'
            else 'D'
        end as result,
        -- an AWARDED result: the match was decided off the pitch (technical loss / walkover), so it
        -- counts for points and goals and can NEVER have a stat line. Emitted so the coverage gates
        -- downstream can tell "the stats are missing" from "there were never any to have" — without
        -- it, counting these as played nulls every rate for the whole season.
        f.status_short in ('AWD', 'WO') as is_awarded_result
    from fixtures as f
    where
        f.status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO')
        and f.goals_home is not null
        and f.goals_away is not null
    union all
    select
        f.fixture_sk,
        f.league_sk,
        f.season_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        f.round_name,
        safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
        'away' as home_away,
        f.away_team_sk as team_sk,
        f.home_team_sk as opponent_team_sk,
        f.goals_away as goals,
        f.goals_home as goals_against,
        case
            when f.goals_away > f.goals_home then 'W'
            when f.goals_away < f.goals_home then 'L'
            else 'D'
        end as result,
        -- an AWARDED result: the match was decided off the pitch (technical loss / walkover), so it
        -- counts for points and goals and can NEVER have a stat line. Emitted so the coverage gates
        -- downstream can tell "the stats are missing" from "there were never any to have" — without
        -- it, counting these as played nulls every rate for the whole season.
        f.status_short in ('AWD', 'WO') as is_awarded_result
    from fixtures as f
    where
        f.status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO')
        and f.goals_home is not null
        and f.goals_away is not null
),

with_stats as (
    select
        l.fixture_sk,
        l.league_sk,
        l.season_sk,
        l.league_code,
        l.season_api_year,
        l.kickoff_datetime,
        l.round_name,
        l.round_order,
        l.home_away,
        l.team_sk,
        l.opponent_team_sk,
        l.goals,
        l.goals_against,
        l.result,
        l.is_awarded_result,
        own.shots_on_target,
        own.shots,
        own.shots_inside_box,
        own.corners,
        own.passes,
        own.passes_accurate,
        own.saves,
        opp.shots_on_target as shots_on_target_against,
        opp.shots as shots_against,
        opp.shots_inside_box as shots_inside_box_against,
        opp.corners as corners_against,
        own.cards_yellow,
        own.cards_red,
        -- the goal split, cleaned in base from the events; goals stays the scoreline
        own.goals_penalty,
        own.goals_own,
        -- own goals this team conceded: credited to the opponent, so they sit on its row. Part of
        -- goals_against, but not a shot on target the keeper faced (saves_pct leaves them out).
        opp.goals_own as goals_own_against
    from legs as l
    left join team_stats as own
        on l.fixture_sk = own.fixture_sk and l.team_sk = own.team_sk
    left join team_stats as opp
        on l.fixture_sk = opp.fixture_sk and l.opponent_team_sk = opp.team_sk
)

select
    ws.*,
    reg.competition_type,
    typ.entity_type
from with_stats as ws
left join registry as reg
    on ws.league_code = reg.league_code
left join types as typ
    on reg.competition_type = typ.competition_type
