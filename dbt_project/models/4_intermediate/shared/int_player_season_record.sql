{#
  W2 season-record builder — player. Cumulative totals over a player's finished matches within one
  competition+season, one row per match the player appeared in (totals THROUGH that match). The
  complement to int_player_momentum__metrics (W1 = last 5).

  Grain: (team_sk, player_sk, league_code, season_api_year, fixture_sk).

  A player-match leg exists wherever the API provides player stats, and the provider lists the whole
  matchday squad — so an UNUSED SUBSTITUTE arrives as a 0-minute leg. Those rows are not output, because
  this model's row IS an appearance and match_number/games_played count matches actually played. A leg
  whose minutes are unknown is not output either, but it stays in the running window, so whatever the
  player did there counts.

  Every metric is its catalogue formula over the window's leg rows, written by
  scripts/generate_metric_sql.py by the rules in models/docs/metric_rules.md.

  Carries round_order + match_number for the deferred year-over-year surface.
  Season-bounded (partition by league_code, season_api_year). A national qualifying
  campaign is one season here — the provider stamps a whole campaign with a single
  season_api_year even though its matches span 2–3 calendar years — so this partition
  already cumulates the full campaign (§4 / #655).
#}

with player_legs as (
    select * from {{ ref('int_legs__player_match') }}
    where minutes > 0 or minutes is null
),

-- A team match with no player data at all: nobody knows who played or what they did, so every running
-- total of that team's players is blank from that match on. Awarded results are no match played.
first_match_without_player_data as (
    select
        tm.team_sk,
        tm.league_code,
        tm.season_api_year,
        min(tm.kickoff_datetime) as kickoff_datetime
    from {{ ref('int_legs__team_match') }} as tm
    left join {{ ref('int_legs__team_from_players') }} as tp
        on tm.fixture_sk = tp.fixture_sk and tm.team_sk = tp.team_sk
    where not tm.is_awarded_result and tp.fixture_sk is null
    group by tm.team_sk, tm.league_code, tm.season_api_year
),

window_rows as (
    select
        pl.*,
        uncovered.kickoff_datetime is null or pl.kickoff_datetime < uncovered.kickoff_datetime
            as window_is_complete
    from player_legs as pl
    left join first_match_without_player_data as uncovered
        on
            pl.team_sk = uncovered.team_sk
            and pl.league_code = uncovered.league_code
            and pl.season_api_year = uncovered.season_api_year
),

running as (
    select
        team_sk,
        player_sk,
        league_code,
        season_api_year,
        fixture_sk,
        entity_type,
        kickoff_datetime,
        round_order,
        minutes,
        any_value(position_code) over w as position_code,
        countif(minutes > 0) over w as match_number,
        if(logical_and(window_is_complete and minutes is not null) over w, sum(minutes) over w, null)
            as minutes_to_date,
        -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
        if(logical_and(window_is_complete and goals is not null) over w, sum(goals) over w, null) as goals_player,
        if(logical_and(window_is_complete and assists is not null) over w, sum(assists) over w, null) as assists_player,
        if(
            logical_and(window_is_complete and goals_against is not null) over w,
            sum(goals_against) over w,
            null
        ) as goals_against_player,
        if(logical_and(window_is_complete and saves is not null) over w, sum(saves) over w, null) as saves_player,
        if(logical_and(window_is_complete and shots is not null) over w, sum(shots) over w, null) as shots_player,
        if(
            logical_and(window_is_complete and shots_on_target is not null) over w,
            sum(shots_on_target) over w,
            null
        ) as shots_on_goal_player,
        if(logical_and(window_is_complete and passes is not null) over w, sum(passes) over w, null) as passes_player,
        if(
            logical_and(window_is_complete and passes_key is not null) over w,
            sum(passes_key) over w,
            null
        ) as passes_key_player,
        if(
            logical_and(window_is_complete and passes_accurate is not null) over w,
            sum(passes_accurate) over w,
            null
        ) as passes_accurate_player,
        if(logical_and(window_is_complete and tackles is not null) over w, sum(tackles) over w, null) as tackles_player,
        if(logical_and(window_is_complete and blocks is not null) over w, sum(blocks) over w, null) as blocks_player,
        if(
            logical_and(window_is_complete and interceptions is not null) over w,
            sum(interceptions) over w,
            null
        ) as interceptions_player,
        if(logical_and(window_is_complete and duels is not null) over w, sum(duels) over w, null) as duels_player,
        if(
            logical_and(window_is_complete and duels_won is not null) over w,
            sum(duels_won) over w,
            null
        ) as duels_won_player,
        if(
            logical_and(window_is_complete and dribbles is not null) over w,
            sum(dribbles) over w,
            null
        ) as dribbles_attempts_player,
        if(
            logical_and(window_is_complete and dribbles_success is not null) over w,
            sum(dribbles_success) over w,
            null
        ) as dribbles_success_player,
        if(
            logical_and(window_is_complete and dribbles_against is not null) over w,
            sum(dribbles_against) over w,
            null
        ) as dribbles_past_player,
        if(
            logical_and(window_is_complete and offsides is not null) over w,
            sum(offsides) over w,
            null
        ) as offsides_player,
        if(
            logical_and(window_is_complete and cards_yellow is not null) over w,
            sum(cards_yellow) over w,
            null
        ) as cards_yellow_player,
        if(
            logical_and(window_is_complete and cards_red is not null) over w,
            sum(cards_red) over w,
            null
        ) as cards_red_player,
        if(
            logical_and(window_is_complete and penalties_won is not null) over w,
            sum(penalties_won) over w,
            null
        ) as penalty_won_player,
        if(
            logical_and(window_is_complete and penalties_committed is not null) over w,
            sum(penalties_committed) over w,
            null
        ) as penalty_committed_player,
        if(
            logical_and(window_is_complete and (tackles + interceptions + blocks) is not null) over w,
            sum(tackles + interceptions + blocks) over w,
            null
        ) as defensive_actions_player,
        if(
            logical_and(window_is_complete and (goals + assists) is not null) over w,
            sum(goals + assists) over w,
            null
        ) as scorer_points_player,
        safe_divide(
            if(
                logical_and(window_is_complete and saves is not null) over w,
                sum(saves) over w,
                null
            ),
            if(
                logical_and(window_is_complete and (saves + goals_against) is not null) over w,
                sum(saves + goals_against) over w,
                null
            )
        ) as saves_player_pct,
        safe_divide(
            if(
                logical_and(window_is_complete and dribbles_success is not null) over w,
                sum(dribbles_success) over w,
                null
            ),
            if(
                logical_and(window_is_complete and dribbles is not null) over w,
                sum(dribbles) over w,
                null
            )
        ) as dribbles_success_player_pct,
        safe_divide(
            if(
                logical_and(window_is_complete and passes_accurate is not null) over w,
                sum(passes_accurate) over w,
                null
            ),
            if(
                logical_and(window_is_complete and passes is not null) over w,
                sum(passes) over w,
                null
            )
        ) as passes_accuracy_player_pct,
        safe_divide(
            if(logical_and(window_is_complete and duels_won is not null) over w, sum(duels_won) over w, null),
            if(logical_and(window_is_complete and duels is not null) over w, sum(duels) over w, null)
        ) as duels_won_player_pct
        -- end of generated metric sql
    from window_rows
    window w as (
        partition by team_sk, player_sk, league_code, season_api_year
        order by kickoff_datetime asc, fixture_sk asc
        rows between unbounded preceding and current row
    )
)

select
    * except (minutes, match_number, minutes_to_date),
    minutes_to_date as minutes,
    'season_to_date' as window_type,
    match_number,
    match_number as games_played
from running
where minutes > 0
