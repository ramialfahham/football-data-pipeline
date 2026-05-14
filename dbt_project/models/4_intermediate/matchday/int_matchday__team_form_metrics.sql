{{ config(materialized='table') }}

{#
  Per (upcoming fixture_sk, team_sk) form aggregates. Grain: (fixture_sk, team_sk).

  Step 3 (league_only, e.g. BL1): if the team has no finished match in the current league season
  before this fixture, use the full previous season; otherwise last up to five finished games
  in the current season (kickoff order, not matchday rank).

  Step 3 (WC): before the team’s first finished WC tournament match in this season, use all
  finished legs in supporting qualifier leagues (seed wc_supporting_league_codes); afterwards
  last up to five WC legs only.

  Sums do not coalesce missing stats to 0; rates are null when undefined. Product expectation:
  optional gaps stay rare (ingestion completeness); see docs/pipeline_architecture_plan.md.
#}

with import_int_matchday__finished_fixture_team_leg as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

import_int_matchday__upcoming_round_fixtures as (
    select * from {{ ref('int_matchday__upcoming_round_fixtures') }}
),

supporting_leagues as (
    select
        parent_league_code,
        supporting_league_code
    from {{ ref('wc_supporting_league_codes') }}
),

team_fixture_context as (
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.league_code,
        um.season_api_year,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.upcoming_round_order,
        um.home_team_sk as team_sk
    from import_int_matchday__upcoming_round_fixtures as um
    union all
    select
        um.fixture_sk as upcoming_fixture_sk,
        um.league_code,
        um.season_api_year,
        um.kickoff_datetime as upcoming_kickoff_datetime,
        um.upcoming_round_order,
        um.away_team_sk as team_sk
    from import_int_matchday__upcoming_round_fixtures as um
),

-- ── Non-WC competitions (league_only style: one league_code per form window) ──────
non_wc_context as (
    select * from team_fixture_context
    where league_code != 'WC'
),

non_wc_current_counts as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
        count(*) as n_current_legs_before
    from non_wc_context as tfc
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            tfc.team_sk = fwo.team_sk
            and tfc.league_code = fwo.league_code
            and tfc.season_api_year = fwo.season_api_year
            and (
                tfc.upcoming_kickoff_datetime > fwo.kickoff_datetime
                or (
                    tfc.upcoming_kickoff_datetime = fwo.kickoff_datetime
                    and tfc.upcoming_fixture_sk > fwo.fixture_sk
                )
            )
    group by tfc.upcoming_fixture_sk, tfc.team_sk
),

non_wc_season as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
        tfc.league_code,
        tfc.season_api_year,
        tfc.upcoming_kickoff_datetime,
        tfc.upcoming_round_order,
        coalesce(cnt.n_current_legs_before, 0) > 0 as use_five_game_cap,
        case
            when coalesce(cnt.n_current_legs_before, 0) > 0 then tfc.season_api_year
            else tfc.season_api_year - 1
        end as form_season_api_year
    from non_wc_context as tfc
    left join non_wc_current_counts as cnt
        on
            tfc.upcoming_fixture_sk = cnt.upcoming_fixture_sk
            and tfc.team_sk = cnt.team_sk
),

non_wc_ranked as (
    select
        tsc.upcoming_fixture_sk,
        tsc.team_sk,
        tsc.league_code,
        fwo.fixture_sk,
        fwo.kickoff_datetime,
        fwo.round_name,
        fwo.round_order,
        fwo.goals_for,
        fwo.goals_against,
        fwo.result,
        fwo.shots_on_goal,
        fwo.shots_total,
        fwo.shots_inside_box,
        fwo.corner_kicks,
        fwo.passes_total,
        fwo.passes_accurate,
        fwo.goalkeeper_saves,
        fwo.opponent_total_shots,
        fwo.opponent_corner_kicks,
        tsc.form_season_api_year,
        tsc.use_five_game_cap as form_window_five_capped,
        row_number() over (
            partition by tsc.upcoming_fixture_sk, tsc.team_sk
            order by fwo.kickoff_datetime desc, fwo.fixture_sk desc
        ) as game_rn
    from non_wc_season as tsc
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            tsc.team_sk = fwo.team_sk
            and tsc.league_code = fwo.league_code
            and tsc.form_season_api_year = fwo.season_api_year
            and (
                tsc.upcoming_kickoff_datetime > fwo.kickoff_datetime
                or (
                    tsc.upcoming_kickoff_datetime = fwo.kickoff_datetime
                    and tsc.upcoming_fixture_sk > fwo.fixture_sk
                )
            )
),

non_wc_window as (
    select
        upcoming_fixture_sk,
        team_sk,
        league_code,
        fixture_sk,
        kickoff_datetime,
        round_name,
        round_order,
        goals_for,
        goals_against,
        result,
        shots_on_goal,
        shots_total,
        shots_inside_box,
        corner_kicks,
        passes_total,
        passes_accurate,
        goalkeeper_saves,
        opponent_total_shots,
        opponent_corner_kicks,
        form_season_api_year,
        form_window_five_capped
    from non_wc_ranked
    where not form_window_five_capped or game_rn <= 5
),

-- ── WC: qualifiers until first finished WC leg, then up to five WC legs ─────────
wc_context as (
    select * from team_fixture_context
    where league_code = 'WC'
),

wc_tournament_counts as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
        count(*) as n_wc_tournament_before
    from wc_context as tfc
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            tfc.team_sk = fwo.team_sk
            and fwo.league_code = 'WC'
            and tfc.season_api_year = fwo.season_api_year
            and (
                tfc.upcoming_kickoff_datetime > fwo.kickoff_datetime
                or (
                    tfc.upcoming_kickoff_datetime = fwo.kickoff_datetime
                    and tfc.upcoming_fixture_sk > fwo.fixture_sk
                )
            )
    group by tfc.upcoming_fixture_sk, tfc.team_sk
),

wc_ranked as (
    select
        tfc.upcoming_fixture_sk,
        tfc.team_sk,
        tfc.league_code,
        fwo.fixture_sk,
        fwo.kickoff_datetime,
        fwo.round_name,
        fwo.round_order,
        fwo.goals_for,
        fwo.goals_against,
        fwo.result,
        fwo.shots_on_goal,
        fwo.shots_total,
        fwo.shots_inside_box,
        fwo.corner_kicks,
        fwo.passes_total,
        fwo.passes_accurate,
        fwo.goalkeeper_saves,
        fwo.opponent_total_shots,
        fwo.opponent_corner_kicks,
        tfc.season_api_year as form_season_api_year,
        coalesce(wtc.n_wc_tournament_before, 0) > 0 as form_window_five_capped,
        row_number() over (
            partition by tfc.upcoming_fixture_sk, tfc.team_sk
            order by fwo.kickoff_datetime desc, fwo.fixture_sk desc
        ) as game_rn
    from wc_context as tfc
    left join wc_tournament_counts as wtc
        on
            tfc.upcoming_fixture_sk = wtc.upcoming_fixture_sk
            and tfc.team_sk = wtc.team_sk
    inner join import_int_matchday__finished_fixture_team_leg as fwo
        on
            tfc.team_sk = fwo.team_sk
            and (
                tfc.upcoming_kickoff_datetime > fwo.kickoff_datetime
                or (
                    tfc.upcoming_kickoff_datetime = fwo.kickoff_datetime
                    and tfc.upcoming_fixture_sk > fwo.fixture_sk
                )
            )
    left join supporting_leagues as sl_wc_support
        on
            sl_wc_support.parent_league_code = 'WC'
            and fwo.league_code = sl_wc_support.supporting_league_code
    where
        (
            coalesce(wtc.n_wc_tournament_before, 0) = 0
            and sl_wc_support.supporting_league_code is not null
        )
        or (
            coalesce(wtc.n_wc_tournament_before, 0) > 0
            and fwo.league_code = 'WC'
            and tfc.season_api_year = fwo.season_api_year
        )
),

wc_window as (
    select
        upcoming_fixture_sk,
        team_sk,
        league_code,
        fixture_sk,
        kickoff_datetime,
        round_name,
        round_order,
        goals_for,
        goals_against,
        result,
        shots_on_goal,
        shots_total,
        shots_inside_box,
        corner_kicks,
        passes_total,
        passes_accurate,
        goalkeeper_saves,
        opponent_total_shots,
        opponent_corner_kicks,
        form_season_api_year,
        form_window_five_capped
    from wc_ranked
    where not form_window_five_capped or game_rn <= 5
),

form_window_matches as (
    select * from non_wc_window
    union all
    select * from wc_window
),

aggregated_form as (
    select
        upcoming_fixture_sk as fixture_sk,
        team_sk,
        any_value(form_season_api_year) as form_season_api_year,
        max(form_window_five_capped) as form_window_five_capped,
        count(distinct fixture_sk) as form_games_played,
        count(distinct round_name) as form_matchdays_used,
        count(distinct case when shots_on_goal is not null then fixture_sk end) as stat_coverage_form_games,
        sum(
            case result
                when 'W' then 3
                when 'D' then 1
                else 0
            end
        ) as points_won_sum_form,
        sum(goals_for) as goals_for_sum_form,
        sum(goals_against) as goals_against_sum_form,
        sum(shots_total) as total_shots_sum_form,
        sum(opponent_total_shots) as opponent_total_shots_sum_form,
        sum(shots_inside_box) as shots_inside_box_sum_form,
        sum(shots_on_goal) as shots_on_goal_sum_form,
        sum(corner_kicks) as corner_kicks_sum_form,
        sum(opponent_corner_kicks) as opponent_corner_kicks_sum_form,
        sum(passes_accurate) as passes_accurate_sum_form,
        sum(passes_total) as passes_total_sum_form,
        sum(goalkeeper_saves) as goalkeeper_saves_sum_form
    from form_window_matches
    group by upcoming_fixture_sk, team_sk
)

select
    fixture_sk,
    team_sk,
    form_season_api_year,
    form_window_five_capped,
    form_games_played,
    form_matchdays_used,
    stat_coverage_form_games,
    points_won_sum_form,
    goals_for_sum_form,
    goals_against_sum_form,
    total_shots_sum_form,
    opponent_total_shots_sum_form,
    shots_inside_box_sum_form,
    shots_on_goal_sum_form,
    corner_kicks_sum_form,
    opponent_corner_kicks_sum_form,
    passes_accurate_sum_form,
    passes_total_sum_form,
    goalkeeper_saves_sum_form,
    safe_divide(points_won_sum_form, 3 * form_games_played) as points_capture_recent,
    safe_divide(goals_for_sum_form, form_games_played) as goals_per_match_recent,
    safe_divide(goals_against_sum_form, form_games_played) as goals_against_per_match_recent,
    safe_divide(total_shots_sum_form, form_games_played) as shots_per_match_recent,
    safe_divide(
        total_shots_sum_form,
        nullif(total_shots_sum_form + opponent_total_shots_sum_form, 0)
    ) as shot_share_recent,
    safe_divide(shots_inside_box_sum_form, total_shots_sum_form) as danger_zone_ratio_recent,
    safe_divide(shots_on_goal_sum_form, total_shots_sum_form) as shot_accuracy_recent,
    safe_divide(goals_for_sum_form, shots_on_goal_sum_form) as finishing_efficiency_recent,
    safe_divide(passes_accurate_sum_form, passes_total_sum_form) as pass_accuracy_recent,
    safe_divide(passes_total_sum_form, form_games_played) as passes_per_match_recent,
    safe_divide(corner_kicks_sum_form, form_games_played) as corner_kicks_per_match_recent,
    safe_divide(opponent_corner_kicks_sum_form, form_games_played) as corners_conceded_per_match_recent,
    safe_divide(
        goalkeeper_saves_sum_form,
        nullif(goalkeeper_saves_sum_form + goals_against_sum_form, 0)
    ) as save_ratio_recent
from aggregated_form
