-- One row per player a team's chosen fetch names on its sheet: the starting eleven and the bench of
-- each team's latest fetch, with an earlier fetch's grid places and formation when the latest has none
-- and both name the same starting eleven, and each player's id after the shirt pairing.
-- base_apif__lineups reads it.
-- Grain: (league_code, fixture_id, team_id, is_starter, sheet_index).
with src as (
    select
        league_code,
        fixture_id,
        team_id,
        formation,
        start_xi_json,
        substitutes_json,
        raw_ingested_at
    from {{ ref('stg_apif__lineups') }}
    where
        fixture_id is not null
        and team_id is not null
),

fixture_participants as (
    select
        league_code,
        fixture_id,
        season,
        fixture_date,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where
        home_team_id is not null
        and away_team_id is not null
),

overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode,
        cast(fixture_id as int64) as fixture_id
    from {{ ref('fixture_team_id_overrides') }}
),

corrected as (
    select
        src.* except (team_id),
        coalesce(
            fixture_override.correct_team_api_id,
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            src.team_id
        ) as team_id
    from src
    left join overrides as fixture_override
        on
            src.team_id = fixture_override.wrong_team_api_id
            and src.fixture_id = fixture_override.fixture_id
            and fixture_override.mode = 'reattribute_in_fixture'
    left join overrides as alias_override
        on
            src.team_id = alias_override.wrong_team_api_id
            and alias_override.mode = 'alias'
    left join fixture_participants
        on src.fixture_id = fixture_participants.fixture_id
    left join overrides as reattribute_override
        on
            src.team_id = reattribute_override.wrong_team_api_id
            and reattribute_override.mode = 'reattribute_if_cohabiting'
            and reattribute_override.correct_team_api_id in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
            and reattribute_override.wrong_team_api_id not in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
),

fetches as (
    select
        *,
        exists(
            select 1 from unnest(json_query_array(start_xi_json)) as el
            where json_value(el, '$.player.grid') is not null
        ) as has_grid,
        (
            select string_agg(id, ',' order by id)
            from unnest(json_query_array(start_xi_json)) as el,
                unnest([coalesce(json_value(el, '$.player.id'), '')]) as id
        ) as starting_eleven
    from corrected
),

fetch_history as (
    select
        *,
        array_agg(
            struct(
                raw_ingested_at as fetched_at,
                has_grid as fetch_has_grid,
                starting_eleven as fetch_starting_eleven,
                formation as fetch_formation,
                start_xi_json as fetch_start_xi_json
            )
        ) over (partition by league_code, fixture_id, team_id) as history
    from fetches
),

-- When a team's latest fetch has no grid places, the latest earlier fetch that has them lends its
-- grid places and formation, but only if both name the same starting eleven.
latest as (
    select
        * except (has_grid, starting_eleven, history),
        if(
            has_grid,
            null,
            (
                select as struct
                    h.fetch_formation as formation,
                    h.fetch_start_xi_json as start_xi_json
                from unnest(history) as h
                where h.fetch_has_grid and h.fetch_starting_eleven = fetch_history.starting_eleven
                order by h.fetched_at desc
                limit 1
            )
        ) as lender
    from fetch_history
    qualify row_number() over (
        partition by league_code, fixture_id, team_id
        order by raw_ingested_at desc
    ) = 1
),

named as (
    select
        latest.league_code,
        latest.fixture_id,
        latest.team_id,
        latest.formation,
        latest.raw_ingested_at,
        latest.lender,
        true as is_starter,
        player_el,
        sheet_index
    from latest,
        unnest(json_query_array(latest.start_xi_json)) as player_el with offset as sheet_index
    union all
    select
        latest.league_code,
        latest.fixture_id,
        latest.team_id,
        latest.formation,
        latest.raw_ingested_at,
        latest.lender,
        false as is_starter,
        player_el,
        sheet_index
    from latest,
        unnest(json_query_array(latest.substitutes_json)) as player_el with offset as sheet_index
),

sheet_ids as (
    select
        *,
        coalesce(safe_cast(json_value(player_el, '$.player.id') as int64), 0) as provider_player_id,
        safe_cast(json_value(player_el, '$.player.number') as int64) as provider_shirt_number
    from named
),

sheet_players as (
    select
        sheet.league_code,
        sheet.fixture_id,
        sheet.team_id,
        coalesce(sheet.formation, sheet.lender.formation) as formation,
        sheet.raw_ingested_at,
        sheet.is_starter,
        sheet.sheet_index,
        sheet.provider_player_id,
        nullif(
            {{ fixture_player_id(
                'sheet.provider_player_id', 'sheet.fixture_id', 'sheet.team_id', 'sheet.provider_shirt_number'
            ) }},
            0
        ) as player_id,
        {{ decode_html_entities("json_value(sheet.player_el, '$.player.name')") }} as player_name,
        sheet.provider_shirt_number as shirt_number,
        json_value(sheet.player_el, '$.player.pos') as provider_position,
        -- A starter the lender names twice under one provider id gets no lent place.
        coalesce(
            json_value(sheet.player_el, '$.player.grid'),
            if(
                sheet.is_starter,
                (
                    select if(count(*) = 1, max(json_value(el, '$.player.grid')), null)
                    from unnest(json_query_array(sheet.lender.start_xi_json)) as el
                    where coalesce(safe_cast(json_value(el, '$.player.id') as int64), 0) = sheet.provider_player_id
                ),
                null
            )
        ) as grid_position
    from sheet_ids as sheet
),

stat_shirts as (
    select distinct
        league_code,
        fixture_id,
        team_id,
        player_id,
        shirt_number
    from {{ ref('base_apif__fixture_players') }}
    where player_id is not null and shirt_number is not null
),

sheet_shirts as (
    select distinct
        league_code,
        fixture_id,
        team_id,
        player_id,
        shirt_number
    from sheet_players
    where player_id is not null and shirt_number is not null and player_id = provider_player_id
),

match_stat_players as (
    select distinct
        league_code,
        fixture_id,
        player_id
    from {{ ref('base_apif__fixture_players') }}
    where player_id is not null
),

match_sheet_players as (
    select distinct
        league_code,
        fixture_id,
        player_id
    from sheet_players
    where player_id is not null
),

-- The ids a hand correction of a card or goal names in its match keep their own id there.
hand_corrected as (
    select
        fixture_id,
        player_id
    from {{ ref('fixture_card_corrections') }}
    union distinct
    select
        fixture_id,
        player_id
    from {{ ref('fixture_goal_corrections') }}
    union distinct
    select
        fixture_id,
        assist_player_id as player_id
    from {{ ref('fixture_goal_corrections') }}
),

-- One player under two provider ids in a match: a sheet player whose id has no stats line in it is
-- the player of the same team whose stats line carries his shirt number and who is on no sheet row.
-- A pair holds for that match only. An id a hand override changed or a hand correction names is
-- never paired.
shirt_pairs as (
    select
        sheet.league_code,
        sheet.fixture_id,
        sheet.team_id,
        sheet.player_id as sheet_player_id,
        stat.player_id as stats_player_id
    from sheet_shirts as sheet
    inner join stat_shirts as stat
        on
            sheet.league_code = stat.league_code
            and sheet.fixture_id = stat.fixture_id
            and sheet.team_id = stat.team_id
            and sheet.shirt_number = stat.shirt_number
    left join match_stat_players as own_line
        on
            sheet.league_code = own_line.league_code
            and sheet.fixture_id = own_line.fixture_id
            and sheet.player_id = own_line.player_id
    left join match_sheet_players as named
        on
            stat.league_code = named.league_code
            and stat.fixture_id = named.fixture_id
            and stat.player_id = named.player_id
    left join hand_corrected
        on
            cast(sheet.fixture_id as int64) = cast(hand_corrected.fixture_id as int64)
            and sheet.player_id = cast(hand_corrected.player_id as int64)
    where
        own_line.player_id is null
        and named.player_id is null
        and hand_corrected.player_id is null
        and sheet.player_id != stat.player_id
    qualify
        count(*) over (partition by sheet.league_code, sheet.fixture_id, sheet.team_id, sheet.shirt_number) = 1
        and count(*) over (partition by sheet.league_code, sheet.fixture_id, sheet.player_id) = 1
        and count(*) over (partition by sheet.league_code, sheet.fixture_id, stat.player_id) = 1
)

select
    sheet_players.* except (provider_player_id, player_id),
    sheet_players.player_id as sheet_player_id,
    coalesce(shirt_pairs.stats_player_id, sheet_players.player_id) as player_id
from sheet_players
left join shirt_pairs
    on
        sheet_players.league_code = shirt_pairs.league_code
        and sheet_players.fixture_id = shirt_pairs.fixture_id
        and sheet_players.team_id = shirt_pairs.team_id
        and sheet_players.player_id = shirt_pairs.sheet_player_id
