{#
  Building-block team-match leg: one row per (team, finished match with a scoreline), carrying that
  team's cleaned stats AND the opponent's (so danger-zone-conceded etc. are derivable), plus the
  competition's type/entity classification and the dimensions windows need.

  A selection over fct_fixture_team_stats, which holds the team's side of every match; what
  "finished" means is decided in base_apif__fixtures_next. Finished includes forfeits (AWD, WO);
  what they count in is rule R3 in models/docs/metric_rules.md. They carry a scoreline and no stat
  line, and `is_awarded_result` marks them.

  Cross-competition and cross-type — the shared foundation every team performance metric
  aggregates over (a metric = a filter + aggregate of these rows). Grain: (fixture_sk, team_sk).
#}

select
    t.fixture_sk,
    f.league_sk,
    f.season_sk,
    t.league_code,
    f.season_api_year,
    f.kickoff_datetime,
    f.round_name,
    f.round_order,
    t.home_away,
    t.team_sk,
    t.opponent_team_sk,
    t.goals_for as goals,
    t.goals_against,
    t.result,
    t.is_awarded_result,
    t.is_table_shootout_win,
    t.shots_on_target,
    t.shots,
    t.shots_inside_box,
    t.corners,
    t.passes,
    t.passes_accurate,
    t.saves,
    t.shots_off_target,
    t.shots_blocked,
    t.fouls,
    t.offsides,
    t.free_kicks,
    t.passes_against,
    t.shots_on_target_against,
    t.shots_against,
    t.shots_inside_box_against,
    t.corners_against,
    t.cards_yellow,
    t.cards_red,
    t.goals_penalty,
    t.goals_own,
    t.goals_own_against,
    reg.competition_type,
    reg.entity_type
from {{ ref('fct_fixture_team_stats') }} as t
inner join {{ ref('fct_fixture') }} as f
    on t.fixture_sk = f.fixture_sk
left join {{ ref('dim_league') }} as reg
    on t.league_code = reg.league_code
where
    t.is_finished
    and t.goals_for is not null
    and t.goals_against is not null
