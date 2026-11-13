{#
  mart_leaderboards — LONG per-board player rankings: the Statistics leaderboards, the competition
  page's Rankings tab, Home's Top players and the played match page's Match leaders.
  One row per (player, board): the player's place on that board within its competition-season,
  every ranked player, no cut. Composed from int_player_season__metrics (the single source),
  int_player_profile__contribution (share of team goals), dim_player and dim_team.

  metric_key = the catalogue metric_id. rank_order is the board's direction: the catalogue's,
  except the discipline boards, which rank most first by ruling. display_value is the value as the
  page shows it (the display_value macro). rank = RANK over display_value within (league_code,
  season_api_year): players whose shown values are equal share a place and the next place is
  skipped. league_leader_order is the tie-broken order on the exact value, fewer minutes first.

  Who enters a board is the ranking_rules doc block in models/docs/metric_rules.md: a per-90 or
  percentage board from the minutes floor, a percentage board also from its attempts floor, the
  pass-accuracy and finishing boards for outfield players, goals against per 90 for goalkeepers.
  A most-first board leaves out a zero. sort_value holds the exact value as FLOAT64.

  Each row carries the union of the boards' display atoms so the export selects per board (marts
  contain what we show). Grain: (player_sk, season_sk, metric_key).

  The match window (window_type 'match'): for every played match with player stats, eight count
  boards across both teams, from int_player_match__metrics, ranked the same way within the match;
  match_leader_order is the tie-broken position, fewer minutes winning, and the board keeps its first
  three. On match rows the value is sort_value alone, so the season-only columns are NULL. Season rows
  carry window_type 'season_to_date'. Grain of a match row: (fixture_sk, player_sk, metric_key).
#}

{# The season boards. Adding or removing a key here must also move shared.yml's accepted_values. #}
{% set count_boards = [
    'goals_player',
    'assists_player',
    'scorer_points_player',
    'goals_penalty_player',
    'shots_on_goal_player',
    'passes_player',
    'passes_key_player',
    'ball_actions_player',
    'dribbles_attempts_player',
    'duels_player',
    'defensive_actions_player',
    'saves_player',
    'cards_yellow_player',
    'cards_red_player',
    'penalty_committed_player',
] %}

{% set per90_boards = [
    'goals_per90',
    'assists_per90',
    'scorer_points_per90',
    'shots_per90',
    'shots_on_goal_per90',
    'passes_per90',
    'passes_accurate_per90',
    'passes_key_per90',
    'ball_actions_per90',
    'dribbles_attempts_per90',
    'dribbles_success_per90',
    'duels_per90',
    'duels_won_per90',
    'defensive_actions_per90',
    'tackles_per90',
    'interceptions_per90',
    'blocks_per90',
    'saves_per90',
    'fouls_per90',
    'offsides_per90',
    'dribbles_past_per90',
] %}

{% set outfield = "player_position is not null and player_position != 'Goalkeeper'" %}
{% set keeper = "player_position = 'Goalkeeper'" %}
{% set min_minutes = 'minutes >= ' ~ var('player_min_minutes') %}

{% set scoped_per90_boards = [
    {'key': 'goals_against_per90', 'qualify': keeper},
] %}

{% set rate_boards = [
    {'key': 'passes_accuracy_player_pct', 'qualify': outfield},
    {'key': 'finishing_efficiency_player_pct',
     'qualify': outfield ~ ' and shots_on_goal_player >= ' ~ var('player_min_shots_on_target')},
    {'key': 'shots_on_goal_player_pct', 'qualify': 'shots_player >= ' ~ var('player_min_shots')},
    {'key': 'dribbles_success_player_pct',
     'qualify': 'dribbles_attempts_player >= ' ~ var('player_min_dribbles')},
    {'key': 'duels_won_player_pct', 'qualify': 'duels_player >= ' ~ var('player_min_duels')},
    {'key': 'saves_player_pct',
     'qualify': 'shots_on_goal_against_player >= ' ~ var('player_min_shots_on_target_faced')},
    {'key': 'contribution_player_pct', 'qualify': 'true'},
] %}

{# Ranked most first by ruling, whatever direction the catalogue gives the metric. #}
{% set most_first_by_ruling = [
    'cards_yellow_player',
    'cards_red_player',
    'penalty_committed_player',
    'fouls_per90',
    'offsides_per90',
] %}

{% set boards = [] %}
{% for key in count_boards %}
{% do boards.append({'key': key, 'where': 'true'}) %}
{% endfor %}
{% for key in per90_boards %}
{% do boards.append({'key': key, 'where': min_minutes}) %}
{% endfor %}
{% for board in scoped_per90_boards + rate_boards %}
{% do boards.append({'key': board.key, 'where': min_minutes ~ ' and ' ~ board.qualify}) %}
{% endfor %}

{# The Match leaders boards of the played match page, in the catalogue's order. #}
{% set match_boards = [
    'shots_player',
    'passes_player',
    'passes_key_player',
    'ball_actions_player',
    'dribbles_attempts_player',
    'duels_won_player',
    'defensive_actions_player',
    'fouls_player',
] %}
{% set match_board_rows = 3 %}

with season as (
    select * from {{ ref('int_player_season__metrics') }}
),

match_metrics as (
    select * from {{ ref('int_player_match__metrics') }}
),

contribution as (
    select
        player_sk,
        team_sk,
        season_sk,
        contribution_player_pct
    from {{ ref('int_player_profile__contribution') }}
),

players as (
    select
        player_sk,
        player_name,
        player_nationality,
        player_position,
        player_photo_url
    from {{ ref('dim_player') }}
),

-- The club the row belongs to. team_sk arrives from int_player_season__metrics already resolved to
-- the player's last known club that competition-season, so this is identity lookup only. dim_team
-- is unique on team_sk, so the left join cannot fan the row count out.
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

-- The direction and format of each board's metric, from the catalogue: the one place a metric's
-- meaning is defined.
catalogue as (
    select
        metric_id,
        direction,
        format
    from {{ ref('metric_catalogue') }}
    where entity = 'player'
),

base as (
    select
        s.*,
        c.contribution_player_pct,
        p.player_name,
        p.player_nationality,
        p.player_position,
        p.player_photo_url,
        t.team_name,
        t.team_slug,
        t.team_logo_url,
        cs.competition_group
    from season as s
    left join contribution as c
        on s.player_sk = c.player_sk and s.team_sk = c.team_sk and s.season_sk = c.season_sk
    left join players as p on s.player_sk = p.player_sk
    left join teams as t on s.team_sk = t.team_sk
    left join competition_seasons as cs on s.season_sk = cs.season_sk
),

-- One row per (player-season, board) where the player enters the board.
season_long as (
    {% for board in boards %}
    select
        player_sk,
        season_sk,
        '{{ board.key }}' as metric_key,
        cast({{ board.key }} as float64) as metric_value
    from base
    where {{ board.where }} and {{ board.key }} is not null
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
),

season_directed as (
    select
        l.player_sk,
        l.season_sk,
        l.metric_key,
        l.metric_value,
        {{ display_value('l.metric_value', 'c.format') }} as display_value,
        case
            when l.metric_key in (
                {% for key in most_first_by_ruling %}
                '{{ key }}'{% if not loop.last %},{% endif %}
                {% endfor %}
            ) then 'desc'
            when c.direction = 'lower_better' then 'asc'
            else 'desc'
        end as rank_order
    from season_long as l
    -- inner: a board whose metric the catalogue does not define has no direction and no rows,
    -- which assert_mart_leaderboards_boards_follow_their_floors then reports as a missing board
    inner join catalogue as c on l.metric_key = c.metric_id
),

season_scored as (
    select
        b.*,
        d.metric_key,
        d.metric_value,
        d.display_value,
        d.rank_order,
        -- the value in ranking order: negated on a most-first board so one ascending sort ranks both
        if(d.rank_order = 'asc', d.metric_value, -d.metric_value) as sort_key,
        if(d.rank_order = 'asc', d.display_value, -d.display_value) as display_key
    from season_directed as d
    inner join base as b
        on d.player_sk = b.player_sk and d.season_sk = b.season_sk
    -- a zero is not a ranking on a most-first board
    where d.rank_order = 'asc' or d.metric_value > 0
),

ranked as (
    select
        season_scored.*,
        rank() over (
            partition by league_code, season_api_year, metric_key
            order by display_key asc
        ) as board_rank,
        -- The TIE-BROKEN order within a league, for a consumer that shows one player per league.
        -- FEWER MINUTES WINS: the same tally in less time is the better performance. player_sk last
        -- only makes the order stable; it says nothing about the players. `nulls last` keeps an
        -- unknown minutes total from winning the tie, because BigQuery sorts NULLs first ascending.
        row_number() over (
            partition by league_code, season_api_year, metric_key
            order by sort_key asc, minutes asc nulls last, player_sk asc
        ) as league_leader_order
    from season_scored
),

match_base as (
    select
        m.fixture_sk,
        m.player_sk,
        m.season_sk,
        m.league_sk,
        m.league_code,
        m.season_api_year,
        m.minutes,
        m.team_sk,
        m.shots_player,
        m.passes_player,
        m.passes_key_player,
        m.ball_actions_player,
        m.dribbles_attempts_player,
        m.duels_won_player,
        m.defensive_actions_player,
        m.fouls_player,
        p.player_name,
        p.player_nationality,
        p.player_position,
        p.player_photo_url,
        t.team_name,
        t.team_slug,
        t.team_logo_url,
        cs.competition_group
    from match_metrics as m
    left join players as p on m.player_sk = p.player_sk
    left join teams as t on m.team_sk = t.team_sk
    left join competition_seasons as cs on m.season_sk = cs.season_sk
),

-- One match's boards: the same rank as a season board, and the same tie-break at the cut, fewer
-- minutes first, with player_sk as the stable last resort. Every match board is a count.
match_ranked as (
    {% for key in match_boards %}
    select
        fixture_sk,
        player_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        competition_group,
        minutes,
        team_sk,
        player_name,
        player_nationality,
        player_position,
        player_photo_url,
        team_name,
        team_slug,
        team_logo_url,
        '{{ key }}' as metric_key,
        cast({{ key }} as float64) as sort_value,
        rank() over (
            partition by fixture_sk
            order by {{ key }} desc
        ) as board_rank,
        row_number() over (
            partition by fixture_sk
            order by {{ key }} desc, minutes asc nulls last, player_sk asc
        ) as match_leader_order
    from match_base
    where {{ key }} > 0
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
),

match_rows as (
    select
        fixture_sk,
        player_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        competition_group,
        minutes,
        team_sk,
        player_name,
        player_nationality,
        player_position,
        player_photo_url,
        team_name,
        team_slug,
        team_logo_url,
        metric_key,
        sort_value,
        board_rank,
        match_leader_order,
        {{ dbt_utils.generate_surrogate_key(["'match'", 'fixture_sk', 'player_sk', 'metric_key']) }}
            as player_leaderboard_sk,
        'match' as window_type,
        'desc' as rank_order,
        sort_value as display_value,
        cast(null as int64) as league_leader_order,
        cast(null as int64) as appearances,
        cast(null as int64) as goals_player,
        cast(null as int64) as assists_player,
        cast(null as int64) as shots_on_goal_player,
        cast(null as int64) as dribbles_attempts_player,
        cast(null as int64) as dribbles_success_player,
        cast(null as int64) as passes_player,
        cast(null as int64) as passes_key_player,
        cast(null as int64) as duels_player,
        cast(null as int64) as duels_won_player,
        cast(null as int64) as tackles_player,
        cast(null as int64) as interceptions_player,
        cast(null as int64) as blocks_player,
        cast(null as int64) as cards_yellow_player,
        cast(null as int64) as cards_red_player,
        cast(null as int64) as saves_player,
        cast(null as int64) as scorer_points_player,
        cast(null as int64) as defensive_actions_player,
        cast(null as int64) as cards_player,
        cast(null as float64) as passes_accuracy_player_pct,
        cast(null as float64) as duels_won_player_pct,
        cast(null as float64) as dribbles_success_player_pct,
        cast(null as float64) as saves_player_pct,
        cast(null as float64) as finishing_efficiency_player_pct,
        cast(null as bool) as is_current_season,
        cast(null as int64) as board_leader_order
    from match_ranked
    where match_leader_order <= {{ match_board_rows }}
)

-- THE ORDER OF THE LEAGUE LEADERS ON A BOARD, so a consumer showing one leader per league orders by
-- a single served column and compares nothing itself. Partitioned by metric_key alone: the order is
-- total, so any pool of leagues filtered from it keeps the right relative order, and values come out
-- sparse within a pool. No season in the partition, because is_current_season is per league.
-- Computed in the final select rather than a CTE joined back: sorting the leaders to the front of
-- the window gives them positions 1..N with no join, and the CASE discards the rest.
select
    {{ dbt_utils.generate_surrogate_key(['player_sk', 'season_sk', 'metric_key']) }}
        as player_leaderboard_sk,
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
    player_sk,
    player_name,
    player_nationality,
    player_position,
    player_photo_url,
    team_sk,
    team_name,
    team_slug,
    team_logo_url,
    appearances,
    minutes,
    goals_player,
    assists_player,
    shots_on_goal_player,
    dribbles_attempts_player,
    dribbles_success_player,
    passes_player,
    passes_key_player,
    duels_player,
    duels_won_player,
    tackles_player,
    interceptions_player,
    blocks_player,
    cards_yellow_player,
    cards_red_player,
    saves_player,
    scorer_points_player,
    defensive_actions_player,
    cards_player,
    passes_accuracy_player_pct,
    duels_won_player_pct,
    dribbles_success_player_pct,
    saves_player_pct,
    finishing_efficiency_player_pct,
    -- WHICH SEASON a consumer should show, served as a fact: the latest season per LEAGUE, so every
    -- row of a league agrees.
    rank() over (
        partition by league_code
        order by season_api_year desc
    ) = 1 as is_current_season,
    -- NULL on every row that is not a league leader: the position is only defined among leaders.
    case
        when league_leader_order = 1 then row_number() over (
            partition by metric_key
            order by
                case when league_leader_order = 1 then 0 else 1 end,
                sort_key asc,
                minutes asc nulls last,
                player_sk asc,
                season_api_year desc,
                league_code asc
        )
    end as board_leader_order,
    'season_to_date' as window_type,
    cast(null as int64) as fixture_sk,
    cast(null as int64) as match_leader_order
from ranked

union all

select
    player_leaderboard_sk,
    metric_key,
    rank_order,
    board_rank as rank,
    league_leader_order,
    sort_value,
    display_value,
    league_code,
    season_api_year,
    competition_group,
    season_sk,
    league_sk,
    player_sk,
    player_name,
    player_nationality,
    player_position,
    player_photo_url,
    team_sk,
    team_name,
    team_slug,
    team_logo_url,
    appearances,
    minutes,
    goals_player,
    assists_player,
    shots_on_goal_player,
    dribbles_attempts_player,
    dribbles_success_player,
    passes_player,
    passes_key_player,
    duels_player,
    duels_won_player,
    tackles_player,
    interceptions_player,
    blocks_player,
    cards_yellow_player,
    cards_red_player,
    saves_player,
    scorer_points_player,
    defensive_actions_player,
    cards_player,
    passes_accuracy_player_pct,
    duels_won_player_pct,
    dribbles_success_player_pct,
    saves_player_pct,
    finishing_efficiency_player_pct,
    is_current_season,
    board_leader_order,
    window_type,
    fixture_sk,
    match_leader_order
from match_rows
