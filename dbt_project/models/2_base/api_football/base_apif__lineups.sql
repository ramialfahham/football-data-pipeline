-- One row per player the team sheets name for a match: the starting eleven and the bench, from
-- each team's latest fetch or, for a researched match, from fixture_lineup_corrections, with the
-- minute a substitution brought each player on or took them off, and the match's line-up state.
-- Grain: (league_code, fixture_id, team_id, player_id).
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
        mode
    from {{ ref('fixture_team_id_overrides') }}
),

corrected as (
    select
        src.* except (team_id),
        coalesce(
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            src.team_id
        ) as team_id
    from src
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

latest as (
    select *
    from corrected
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
        true as is_starter,
        player_el
    from latest,
        unnest(json_query_array(latest.start_xi_json)) as player_el
    union all
    select
        latest.league_code,
        latest.fixture_id,
        latest.team_id,
        latest.formation,
        latest.raw_ingested_at,
        false as is_starter,
        player_el
    from latest,
        unnest(json_query_array(latest.substitutes_json)) as player_el
),

parsed as (
    select
        league_code,
        fixture_id,
        team_id,
        formation,
        raw_ingested_at,
        is_starter,
        nullif(safe_cast(json_value(player_el, '$.player.id') as int64), 0) as player_id,
        json_value(player_el, '$.player.name') as player_name,
        safe_cast(json_value(player_el, '$.player.number') as int64) as shirt_number,
        json_value(player_el, '$.player.pos') as position_code,
        json_value(player_el, '$.player.grid') as grid_position
    from named
),

provider_sheets as (
    select
        league_code,
        fixture_id,
        team_id,
        countif(is_starter) as n_starters_listed,
        countif(is_starter and player_id is null) as n_starters_without_id,
        count(distinct if(is_starter, player_id, null)) as n_distinct_starters
    from parsed
    group by league_code, fixture_id, team_id
),

provider_players as (
    select *
    from parsed
    where player_id is not null
    qualify row_number() over (
        partition by league_code, fixture_id, team_id, player_id
        order by is_starter desc
    ) = 1
),

starters as (
    select distinct
        league_code,
        fixture_id,
        player_id
    from provider_players
    where is_starter
),

substitutions as (
    select
        league_code,
        fixture_id,
        event_index,
        minute_elapsed,
        minute_extra,
        player_id,
        assist_player_id
    from {{ ref('base_apif__fixture_events') }}
    where event_type = 'subst'
),

-- The event's player goes off and its assist comes on, unless the line-ups say the reverse.
paired as (
    select
        substitutions.league_code,
        substitutions.fixture_id,
        substitutions.event_index,
        substitutions.minute_elapsed,
        substitutions.minute_extra,
        if(
            assist_starter.player_id is not null and player_starter.player_id is null,
            substitutions.assist_player_id,
            substitutions.player_id
        ) as off_player_id,
        if(
            assist_starter.player_id is not null and player_starter.player_id is null,
            substitutions.player_id,
            substitutions.assist_player_id
        ) as on_player_id
    from substitutions
    left join starters as player_starter
        on
            substitutions.league_code = player_starter.league_code
            and substitutions.fixture_id = player_starter.fixture_id
            and substitutions.player_id = player_starter.player_id
    left join starters as assist_starter
        on
            substitutions.league_code = assist_starter.league_code
            and substitutions.fixture_id = assist_starter.fixture_id
            and substitutions.assist_player_id = assist_starter.player_id
),

came_on as (
    select
        league_code,
        fixture_id,
        on_player_id as player_id,
        minute_elapsed as minute_on,
        minute_extra as minute_on_extra,
        off_player_id as replaced_player_id
    from paired
    where on_player_id is not null
    qualify row_number() over (
        partition by league_code, fixture_id, on_player_id
        order by minute_elapsed, coalesce(minute_extra, 0), event_index
    ) = 1
),

went_off as (
    select
        league_code,
        fixture_id,
        off_player_id as player_id,
        minute_elapsed as minute_off,
        minute_extra as minute_off_extra
    from paired
    where off_player_id is not null
    qualify row_number() over (
        partition by league_code, fixture_id, off_player_id
        order by minute_elapsed, coalesce(minute_extra, 0), event_index
    ) = 1
),

researched as (
    select
        fixture_participants.league_code,
        corrections.fixture_id,
        corrections.team_id,
        corrections.player_id,
        corrections.player_name,
        corrections.is_starter,
        corrections.shirt_number,
        corrections.position_code,
        corrections.grid_position,
        corrections.team_formation,
        corrections.minute_on,
        corrections.minute_on_extra,
        corrections.replaced_player_id,
        corrections.minute_off,
        corrections.minute_off_extra
    from {{ ref('fixture_lineup_corrections') }} as corrections
    inner join fixture_participants
        on corrections.fixture_id = fixture_participants.fixture_id
),

researched_fixtures as (
    select distinct
        league_code,
        fixture_id
    from researched
),

lined as (
    select
        provider_players.league_code,
        provider_players.fixture_id,
        provider_players.team_id,
        provider_players.player_id,
        provider_players.player_name,
        provider_players.is_starter,
        provider_players.shirt_number,
        provider_players.position_code,
        provider_players.grid_position,
        provider_players.formation as team_formation,
        came_on.minute_on,
        came_on.minute_on_extra,
        came_on.replaced_player_id,
        went_off.minute_off,
        went_off.minute_off_extra,
        provider_players.raw_ingested_at,
        false as is_researched
    from provider_players
    left join came_on
        on
            provider_players.league_code = came_on.league_code
            and provider_players.fixture_id = came_on.fixture_id
            and provider_players.player_id = came_on.player_id
    left join went_off
        on
            provider_players.league_code = went_off.league_code
            and provider_players.fixture_id = went_off.fixture_id
            and provider_players.player_id = went_off.player_id
    left join researched_fixtures
        on
            provider_players.league_code = researched_fixtures.league_code
            and provider_players.fixture_id = researched_fixtures.fixture_id
    where researched_fixtures.fixture_id is null
    union all
    select
        league_code,
        fixture_id,
        team_id,
        player_id,
        player_name,
        is_starter,
        shirt_number,
        position_code,
        grid_position,
        team_formation,
        minute_on,
        minute_on_extra,
        replaced_player_id,
        minute_off,
        minute_off_extra,
        cast(null as timestamp) as raw_ingested_at,
        true as is_researched
    from researched
),

sheet_listing as (
    select
        provider_sheets.league_code,
        provider_sheets.fixture_id,
        provider_sheets.team_id,
        provider_sheets.n_starters_listed,
        provider_sheets.n_starters_without_id,
        provider_sheets.n_distinct_starters
    from provider_sheets
    left join researched_fixtures
        on
            provider_sheets.league_code = researched_fixtures.league_code
            and provider_sheets.fixture_id = researched_fixtures.fixture_id
    where researched_fixtures.fixture_id is null
    union all
    select
        league_code,
        fixture_id,
        team_id,
        countif(is_starter) as n_starters_listed,
        0 as n_starters_without_id,
        count(distinct if(is_starter, player_id, null)) as n_distinct_starters
    from researched
    group by league_code, fixture_id, team_id
),

squads as (
    select distinct
        player_id,
        team_id,
        season_year
    from {{ ref('base_apif__player_team_season') }}
),

transfers as (
    select
        player_id,
        team_in_id,
        transfer_date
    from {{ ref('base_apif__transfers') }}
    where team_in_id is not null
),

club_on_match_day as (
    select
        lined.league_code,
        lined.fixture_id,
        lined.player_id,
        array_agg(transfers.team_in_id order by transfers.transfer_date desc limit 1)[offset(0)]
            as team_id
    from lined
    inner join fixture_participants
        on
            lined.league_code = fixture_participants.league_code
            and lined.fixture_id = fixture_participants.fixture_id
    inner join transfers
        on
            lined.player_id = transfers.player_id
            and fixture_participants.fixture_date >= transfers.transfer_date
    group by lined.league_code, lined.fixture_id, lined.player_id
),

placed as (
    select
        lined.league_code,
        lined.fixture_id,
        lined.team_id,
        lined.player_id,
        lined.is_researched,
        own_squad.player_id is not null as listed_at_own_team,
        other_squad.player_id is not null as listed_at_other_team,
        coalesce(club_on_match_day.team_id = lined.team_id, false) as joined_own_team,
        coalesce(
            club_on_match_day.team_id = if(
                lined.team_id = fixture_participants.home_team_id,
                fixture_participants.away_team_id,
                fixture_participants.home_team_id
            ),
            false
        ) as joined_other_team
    from lined
    inner join fixture_participants
        on
            lined.league_code = fixture_participants.league_code
            and lined.fixture_id = fixture_participants.fixture_id
    left join squads as own_squad
        on
            lined.player_id = own_squad.player_id
            and lined.team_id = own_squad.team_id
            and fixture_participants.season = own_squad.season_year
    left join squads as other_squad
        on
            lined.player_id = other_squad.player_id
            and other_squad.team_id = if(
                lined.team_id = fixture_participants.home_team_id,
                fixture_participants.away_team_id,
                fixture_participants.home_team_id
            )
            and fixture_participants.season = other_squad.season_year
    left join club_on_match_day
        on
            lined.league_code = club_on_match_day.league_code
            and lined.fixture_id = club_on_match_day.fixture_id
            and lined.player_id = club_on_match_day.player_id
),

sheet_placement as (
    select
        league_code,
        fixture_id,
        team_id,
        countif(listed_at_own_team) as n_listed_own,
        countif(listed_at_other_team) as n_listed_other,
        countif(listed_at_other_team and not listed_at_own_team) as n_listed_only_other,
        countif(joined_own_team) as n_joined_own,
        countif(joined_other_team) as n_joined_other
    from placed
    group by league_code, fixture_id, team_id
),

sheet_checks as (
    select
        sheet_listing.league_code,
        sheet_listing.fixture_id,
        sheet_listing.team_id,
        sheet_listing.team_id in (
            fixture_participants.home_team_id, fixture_participants.away_team_id
        ) as is_participant,
        sheet_listing.n_starters_listed = 11
        and sheet_listing.n_starters_without_id = 0
        and sheet_listing.n_distinct_starters = 11 as has_eleven_starters,
        case
            when coalesce(sheet_placement.n_listed_own + sheet_placement.n_listed_other, 0) > 0
                then
                    sheet_placement.n_listed_own > sheet_placement.n_listed_other
                    and sheet_placement.n_listed_only_other = 0
            else coalesce(
                sheet_placement.n_joined_own > 0 and sheet_placement.n_joined_other = 0, false
            )
        end as is_placed_at_team
    from sheet_listing
    inner join fixture_participants
        on
            sheet_listing.league_code = fixture_participants.league_code
            and sheet_listing.fixture_id = fixture_participants.fixture_id
    left join sheet_placement
        on
            sheet_listing.league_code = sheet_placement.league_code
            and sheet_listing.fixture_id = sheet_placement.fixture_id
            and sheet_listing.team_id = sheet_placement.team_id
),

stat_lines as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id
    from {{ ref('base_apif__fixture_players') }}
),

stat_clashes as (
    select distinct
        lined.league_code,
        lined.fixture_id
    from lined
    inner join stat_lines
        on
            lined.league_code = stat_lines.league_code
            and lined.fixture_id = stat_lines.fixture_id
            and lined.player_id = stat_lines.player_id
            and lined.team_id != stat_lines.team_id
),

player_sheets as (
    select
        league_code,
        fixture_id,
        player_id
    from lined
    group by league_code, fixture_id, player_id
    having count(distinct team_id) > 1
),

on_both_sheets as (
    select distinct
        league_code,
        fixture_id
    from player_sheets
),

broken_sheet_substitutions as (
    select distinct
        came_on.league_code,
        came_on.fixture_id
    from lined as came_on
    left join lined as replaced
        on
            came_on.league_code = replaced.league_code
            and came_on.fixture_id = replaced.fixture_id
            and came_on.replaced_player_id = replaced.player_id
    where
        (came_on.is_starter and came_on.minute_on is not null)
        or (
            came_on.replaced_player_id is not null
            and (
                replaced.player_id is null
                or replaced.team_id != came_on.team_id
                or replaced.minute_off is distinct from came_on.minute_on
                or coalesce(replaced.minute_off_extra, 0) != coalesce(came_on.minute_on_extra, 0)
            )
        )
),

broken_events as (
    select distinct
        paired.league_code,
        paired.fixture_id
    from paired
    left join researched_fixtures
        on
            paired.league_code = researched_fixtures.league_code
            and paired.fixture_id = researched_fixtures.fixture_id
    left join lined as on_player
        on
            paired.league_code = on_player.league_code
            and paired.fixture_id = on_player.fixture_id
            and paired.on_player_id = on_player.player_id
    left join lined as off_player
        on
            paired.league_code = off_player.league_code
            and paired.fixture_id = off_player.fixture_id
            and paired.off_player_id = off_player.player_id
    where
        researched_fixtures.fixture_id is null
        and (
            on_player.player_id is null
            or off_player.player_id is null
            or on_player.team_id != off_player.team_id
        )
),

broken_substitutions as (
    select
        league_code,
        fixture_id
    from broken_sheet_substitutions
    union distinct
    select
        league_code,
        fixture_id
    from broken_events
),

match_checks as (
    select
        sheet_checks.league_code,
        sheet_checks.fixture_id,
        array_concat(
            if(
                countif(sheet_checks.is_participant) = 2 and logical_and(sheet_checks.is_participant),
                [],
                ['two_sheets']
            ),
            if(logical_and(sheet_checks.has_eleven_starters), [], ['eleven_starters']),
            if(logical_and(sheet_checks.is_placed_at_team), [], ['squad_lists']),
            if(max(stat_clashes.fixture_id) is null, [], ['player_stats_team']),
            if(max(on_both_sheets.fixture_id) is null, [], ['player_on_both_sheets']),
            if(max(broken_substitutions.fixture_id) is null, [], ['substitutions'])
        ) as failed_checks
    from sheet_checks
    left join stat_clashes
        on
            sheet_checks.league_code = stat_clashes.league_code
            and sheet_checks.fixture_id = stat_clashes.fixture_id
    left join on_both_sheets
        on
            sheet_checks.league_code = on_both_sheets.league_code
            and sheet_checks.fixture_id = on_both_sheets.fixture_id
    left join broken_substitutions
        on
            sheet_checks.league_code = broken_substitutions.league_code
            and sheet_checks.fixture_id = broken_substitutions.fixture_id
    group by sheet_checks.league_code, sheet_checks.fixture_id
)

select
    lined.league_code,
    lined.fixture_id,
    lined.team_id,
    lined.player_id,
    lined.player_name,
    lined.is_starter,
    lined.shirt_number,
    lined.position_code,
    lined.grid_position,
    lined.team_formation,
    lined.minute_on,
    lined.minute_on_extra,
    lined.replaced_player_id,
    lined.minute_off,
    lined.minute_off_extra,
    match_checks.failed_checks,
    lined.raw_ingested_at,
    case
        when lined.is_researched then 'researched'
        when array_length(match_checks.failed_checks) = 0 then 'confirmed'
        else 'not_available'
    end as lineup_state
from lined
inner join match_checks
    on
        lined.league_code = match_checks.league_code
        and lined.fixture_id = match_checks.fixture_id
