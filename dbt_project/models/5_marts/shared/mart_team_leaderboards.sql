{#
  mart_team_leaderboards — LONG per-board team rankings: the Statistics team leaderboards, the
  competition page's Rankings tab and Home's Top teams. The team mirror of mart_leaderboards. One
  row per (team, board): the team's place on that board within its competition-season, every ranked
  team, no cut. Season-to-date, composed from int_team_season__metrics (the canonical whole-season
  team rollup) and dim_team identity.

  Each board ranks in the direction the catalogue gives its metric, served as rank_order: a
  lower_better metric ranks fewest first, everything else most first. The discipline boards are the
  ruled exception, most first whatever the catalogue's direction. display_value is the value as the
  page shows it (the display_value macro). rank = RANK over display_value within (league_code,
  season_api_year): teams whose shown values are equal share a place and the next place is skipped.

  Who enters a board is the ranking_rules doc block in models/docs/metric_rules.md; its zero rule
  is the cut `metric_value > 0`, on most-first boards other than a difference.

  UNPIVOT rather than mart_leaderboards' union-all loop, because every team board shares one rule.
  BigQuery UNPIVOT excludes nulls, so a metric with no value for a team (a coverage gap) yields no
  row rather than a null rank.

  Grain: (team_sk, season_sk, metric_key).
#}

{# The board set. Adding or removing a key here must also move shared.yml's accepted_values. #}
{% set boards = [
    'goals',
    'goals_per_match',
    'goals_against',
    'goals_against_per_match',
    'clean_sheets',
    'clean_sheets_pct',
    'goals_penalty',
    'shots_per_match',
    'shots_on_goal_per_match',
    'shots_inside_box_per_match',
    'shots_inside_box_pct',
    'shots_on_goal_pct',
    'finishing_efficiency_pct',
    'shots_on_goal_against_per_match',
    'shots_on_goal_difference_per_match',
    'passes_per_match',
    'passes_accurate_per_match',
    'passes_accuracy_pct',
    'passes_key_per_match',
    'passes_share_pct',
    'dribbles_attempts_per_match',
    'dribbles_success_per_match',
    'dribbles_success_pct',
    'duels_per_match',
    'duels_won_per_match',
    'duels_won_pct',
    'defensive_actions_per_match',
    'tackles_per_match',
    'interceptions_per_match',
    'blocks_per_match',
    'saves_per_match',
    'saves_pct',
    'corners_per_match',
    'corners_against_per_match',
    'cards_yellow',
    'cards_red',
    'fouls_per_match',
    'offsides_per_match',
] %}

{# Ranked most first by ruling, whatever direction the catalogue gives the metric. #}
{% set most_first_by_ruling = ['cards_yellow', 'cards_red', 'fouls_per_match', 'offsides_per_match'] %}

{# A difference, where zero and a negative value are values: the zero rule does not apply. #}
{% set difference_boards = ['shots_on_goal_difference_per_match'] %}

with season as (
    select
        * except (goals, goals_against, clean_sheets, goals_penalty, cards_yellow, cards_red),
        -- UNPIVOT needs one type across its columns: the rates are FLOAT64, the totals INT64
        cast(goals as float64) as goals,
        cast(goals_against as float64) as goals_against,
        cast(clean_sheets as float64) as clean_sheets,
        cast(goals_penalty as float64) as goals_penalty,
        cast(cards_yellow as float64) as cards_yellow,
        cast(cards_red as float64) as cards_red
    from {{ ref('int_team_season__metrics') }}
    where season_games_played >= 1
),

-- The direction and format of each board's metric, from the catalogue: the one place a metric's
-- meaning is defined, so a board cannot rank a fewest-is-best figure most first by accident.
catalogue as (
    select
        metric_id,
        direction,
        format
    from {{ ref('metric_catalogue') }}
    where entity = 'team'
),

-- One row per (team-season, board). UNPIVOT drops nulls, so a team missing a metric through a
-- coverage gap is absent from that board rather than ranked on a null.
long as (
    select
        team_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        season_games_played,
        metric_key,
        metric_value
    from season
    unpivot (
        metric_value for metric_key in (
            {% for board in boards %}
            {{ board }}{% if not loop.last %},{% endif %}
            {% endfor %}
        )
    )
),

-- Identity only. dim_team is unique on team_sk, so the left join cannot fan the row count out.
teams as (
    select
        team_sk,
        team_name,
        team_slug,
        team_logo_url
    from {{ ref('dim_team') }}
),

competition_seasons as (
    select
        season_sk,
        competition_group
    from {{ ref('dim_competition_season') }}
),

base as (
    select
        l.team_sk,
        l.season_sk,
        l.league_sk,
        l.league_code,
        l.season_api_year,
        l.season_games_played,
        l.metric_key,
        l.metric_value,
        {{ display_value('l.metric_value', 'c.format') }} as display_value,
        t.team_name,
        t.team_slug,
        t.team_logo_url,
        cs.competition_group,
        case
            when l.metric_key in (
                {% for key in most_first_by_ruling %}
                '{{ key }}'{% if not loop.last %},{% endif %}
                {% endfor %}
            ) then 'desc'
            when c.direction = 'lower_better' then 'asc'
            else 'desc'
        end as rank_order
    from long as l
    left join teams as t on l.team_sk = t.team_sk
    left join competition_seasons as cs on l.season_sk = cs.season_sk
    -- inner: a board whose metric the catalogue does not define has no direction and no rows,
    -- which assert_mart_team_leaderboards_all_boards_present then reports as a missing board
    inner join catalogue as c on l.metric_key = c.metric_id
),

-- The value in ranking order: negated on a descending board so one ASC sort ranks both kinds.
signed as (
    select
        *,
        if(rank_order = 'asc', metric_value, -metric_value) as sort_key,
        if(rank_order = 'asc', display_value, -display_value) as display_key
    from base
),

ranked as (
    select
        signed.*,
        rank() over (
            partition by league_code, season_api_year, metric_key
            order by display_key asc
        ) as board_rank,
        -- The TIE-BROKEN order within a league, for a consumer that shows one team per league. Teams
        -- have no minutes, and for a per-match rate fewer games is less evidence rather than better
        -- performance, so after the exact value only team_sk breaks a tie: it makes the order stable
        -- and says nothing about the teams.
        row_number() over (
            partition by league_code, season_api_year, metric_key
            order by sort_key asc, team_sk asc
        ) as league_leader_order
    from signed
    -- a zero is not a ranking on a most-first board; on a fewest-first board it is the top row, and
    -- on a difference it is a value like any other
    where
        rank_order = 'asc'
        or metric_value > 0
        or metric_key in ({% for key in difference_boards %}'{{ key }}'{% if not loop.last %}, {% endif %}{% endfor %})
)

select
    {{ dbt_utils.generate_surrogate_key(['team_sk', 'season_sk', 'metric_key']) }}
        as team_leaderboard_sk,
    metric_key,
    rank_order,
    board_rank as rank,
    league_leader_order,
    metric_value as sort_value,
    display_value,
    league_code,
    season_api_year,
    competition_group,
    season_sk,
    league_sk,
    team_sk,
    team_name,
    team_slug,
    team_logo_url,
    season_games_played,
    -- WHICH SEASON a consumer should show, served as a fact: the latest season per LEAGUE, so every
    -- row of a league agrees.
    rank() over (
        partition by league_code
        order by season_api_year desc
    ) = 1 as is_current_season,
    -- The order the league leaders appear in on a board, across every league, by the same rule.
    -- Partitioned by metric_key alone: the order is total, so any pool of leagues keeps its
    -- relative sequence and the values come out sparse within a pool. NULL on any row that is not a
    -- league leader. Computed here rather than in a CTE joined back: sorting the leaders to the front
    -- of the window gives identical positions with no join.
    case
        when league_leader_order = 1 then row_number() over (
            partition by metric_key
            order by
                case when league_leader_order = 1 then 0 else 1 end,
                sort_key asc,
                team_sk asc,
                season_api_year desc,
                league_code asc
        )
    end as board_leader_order
from ranked
