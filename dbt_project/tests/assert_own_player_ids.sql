{#
  A row of player_id_overrides that gives a player an id in one match or one season holds: it is
  sourced by https URLs separated by a space, dim_player has a row for the id it gives, the match or
  season carries that id at that team, and the provider id it moves away from is gone there. A player
  the provider holds under the placeholder 0 gets the warehouse's own id, a negative id that names
  one researched player. One failing row per broken row. Named cases: Víctor Rodríguez (-1),
  Navalcarnero shirt 5 in fixture 1644363, has a stat line and his yellow card; Alhassane Bangoura
  (586701) has the Guinea assist in fixture 1126027 and the yellow card in 1126107 that the provider
  filed under Lass Bangoura (51294).
#}
{{ config(store_failures = true, severity = 'error') }}

with assigned as (
    select
        mode,
        wrong_player_api_id,
        correct_player_api_id as player_id,
        fixture_id,
        team_id,
        league_code,
        season_year,
        source
    from {{ ref('player_id_overrides') }}
    where mode in ('assign_in_fixture', 'assign_in_season')
),

match_players as (
    select
        fixture_id,
        team_id,
        player_id
    from {{ ref('base_apif__lineups') }}
    union distinct
    select
        fixture_id,
        team_id,
        player_id
    from {{ ref('base_apif__fixture_players') }}
    union distinct
    select
        fixture_id,
        team_id,
        player_id
    from {{ ref('base_apif__fixture_events') }}
    union distinct
    select
        fixture_id,
        team_id,
        assist_player_id
    from {{ ref('base_apif__fixture_events') }}
),

season_players as (
    select distinct
        league_code,
        season_year,
        team_id,
        player_id
    from {{ ref('base_apif__player_team_season') }}
),

checked as (
    select
        a.player_id,
        a.fixture_id,
        a.wrong_player_api_id = 0 and a.player_id >= 0 as is_not_negative,
        not regexp_contains(coalesce(a.source, ''), r'^https://\S+( https://\S+)*$') as is_not_sourced,
        a.mode = 'assign_in_fixture' and kept_in_match.player_id is null as is_off_the_match,
        wrong_in_match.player_id is not null as is_left_in_the_match,
        a.mode = 'assign_in_season' and kept_in_season.player_id is null as is_off_the_season,
        wrong_in_season.player_id is not null as is_left_in_the_season,
        d.player_api_id is null as is_not_a_player
    from assigned as a
    left join match_players as kept_in_match
        on
            a.mode = 'assign_in_fixture'
            and a.fixture_id = kept_in_match.fixture_id
            and a.team_id = kept_in_match.team_id
            and a.player_id = kept_in_match.player_id
    left join match_players as wrong_in_match
        on
            a.mode = 'assign_in_fixture'
            and a.wrong_player_api_id != 0
            and a.fixture_id = wrong_in_match.fixture_id
            and a.team_id = wrong_in_match.team_id
            and a.wrong_player_api_id = wrong_in_match.player_id
    left join season_players as kept_in_season
        on
            a.mode = 'assign_in_season'
            and a.league_code = kept_in_season.league_code
            and a.season_year = kept_in_season.season_year
            and a.team_id = kept_in_season.team_id
            and a.player_id = kept_in_season.player_id
    left join season_players as wrong_in_season
        on
            a.mode = 'assign_in_season'
            and a.league_code = wrong_in_season.league_code
            and a.season_year = wrong_in_season.season_year
            and a.team_id = wrong_in_season.team_id
            and a.wrong_player_api_id = wrong_in_season.player_id
    left join {{ ref('dim_player') }} as d
        on a.player_id = d.player_api_id
),

own_id_case as (
    select countif(minutes > 0 and cards_yellow = 1) as rows_found
    from {{ ref('fct_fixture_player_stats') }}
    where player_sk = -1 and fixture_sk = 1644363
),

moved_events_case as (
    select
        countif(fixture_sk = 1126027 and assist_player_sk = 586701) as assists_found,
        countif(fixture_sk = 1126107 and player_sk = 586701 and event_type = 'Card') as cards_found,
        countif(player_sk = 51294 or assist_player_sk = 51294) as events_left
    from {{ ref('fct_fixture_event') }}
    where fixture_sk in (1126027, 1126107)
)

select
    player_id,
    fixture_id,
    case
        when is_not_negative then 'own id is not negative'
        when is_not_sourced then 'not sourced'
        when is_off_the_match then 'not on the match sheet, stat lines or events'
        when is_left_in_the_match then 'the moved id is still in the match'
        when is_off_the_season then 'not on the season row'
        when is_left_in_the_season then 'the moved id is still on the season row'
        else 'not in dim_player'
    end as failure
from checked
where
    is_not_negative
    or is_not_sourced
    or is_off_the_match
    or is_left_in_the_match
    or is_off_the_season
    or is_left_in_the_season
    or is_not_a_player

union all

select
    -1 as player_id,
    1644363 as fixture_id,
    'named case: Víctor Rodríguez has no stat line with his yellow card' as failure
from own_id_case
where rows_found = 0

union all

select
    586701 as player_id,
    1126027 as fixture_id,
    'named case: the Guinea assist and yellow card are not all under Alhassane Bangoura' as failure
from moved_events_case
where assists_found = 0 or cards_found = 0 or events_left > 0
