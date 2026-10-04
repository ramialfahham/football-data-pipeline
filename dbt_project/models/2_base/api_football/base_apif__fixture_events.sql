with src as (
    select
        league_code,
        fixture_id,
        event_index,
        minute_elapsed,
        minute_extra,
        team_id,
        team_name,
        player_id,
        player_name,
        assist_player_name,
        event_type,
        event_detail,
        event_comments,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_events') }}
    where
        fixture_id is not null
),

deduped as (
    select *
    from src
    qualify row_number() over (
        partition by league_code, fixture_id, event_index
        order by raw_ingested_at desc
    ) = 1
),

recovered as (
    select
        league_code,
        fixture_id,
        event_index,
        minute_elapsed,
        minute_extra,
        team_name,
        player_id,
        player_name,
        assist_player_name,
        event_type,
        event_detail,
        event_comments,
        raw_ingested_at,
        -- Recover a null team_id from the same team's other events in the fixture. Some old
        -- API-Football events (mostly Cards) carry team.name but a null team.id, while the same
        -- team has a valid id on its goals/subs; within (fixture, team_name) we backfill the id so
        -- the event stays attributed and fct_fixture_event.team_sk is never null for a named event.
        -- A fixture has two distinct teams with distinct names, so name -> id is unambiguous.
        case
            when team_id is not null then team_id
            when team_name is not null
                then max(team_id) over (
                    partition by league_code, fixture_id, team_name
                )
            else team_id
        end as team_id
    from deduped
),

-- Fixture participants (home/away team ids), used to evaluate the reattribute_if_cohabiting
-- override condition below. base_apif__fixtures_next grain is one row per fixture_id. Only
-- fixtures whose two participants are BOTH known are kept, so the IN / NOT IN participant checks
-- in the reattribute join never hit the NOT IN (value, NULL) -> UNKNOWN trap (a fixture with a
-- missing participant id is a separate defect; the override conservatively does not fire there).
fixture_participants as (
    select
        fixture_id,
        season,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where
        home_team_id is not null
        and away_team_id is not null
),

-- Hand-curated corrections for known provider team-id defects, from
-- seeds/fixture_team_id_overrides.csv. `alias` = unconditional duplicate-id replacement (one
-- club under two provider ids); `reattribute_if_cohabiting` = replace only when the correct id is
-- a fixture participant and the wrong id is not (a mis-attribution between two DISTINCT clubs, so
-- a club's own legitimate events are never touched).
overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode
    from {{ ref('fixture_team_id_overrides') }}
),

attributed as (
    select
        recovered.league_code,
        recovered.fixture_id,
        recovered.event_index,
        recovered.minute_elapsed,
        recovered.minute_extra,
        recovered.team_name,
        recovered.player_id,
        recovered.player_name,
        recovered.assist_player_name,
        recovered.event_type,
        recovered.event_detail,
        recovered.event_comments,
        recovered.raw_ingested_at,
        recovered.event_type = 'Goal' and recovered.event_detail = 'Own Goal' as is_own_goal,
        coalesce(
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            recovered.team_id
        ) as team_id
    from recovered
    left join overrides as alias_override
        on
            recovered.team_id = alias_override.wrong_team_api_id
            and alias_override.mode = 'alias'
    left join fixture_participants
        on recovered.fixture_id = fixture_participants.fixture_id
    left join overrides as reattribute_override
        on
            recovered.team_id = reattribute_override.wrong_team_api_id
            and reattribute_override.mode = 'reattribute_if_cohabiting'
            and reattribute_override.correct_team_api_id in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
            and reattribute_override.wrong_team_api_id not in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
),

-- The player's team, the cleaning_rules doc block's rule, decided here once: base_apif__fixture_players
-- reads this model, so this is the one place both feeds can be seen. Each player's row team is
-- corrected exactly as base_apif__fixture_players corrects it.
player_rows as (
    select distinct
        player_row.fixture_id,
        player_row.player_id,
        coalesce(
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            player_row.team_id
        ) as team_id
    from {{ ref('stg_apif__fixture_players') }} as player_row
    left join overrides as alias_override
        on
            player_row.team_id = alias_override.wrong_team_api_id
            and alias_override.mode = 'alias'
    left join fixture_participants
        on player_row.fixture_id = fixture_participants.fixture_id
    left join overrides as reattribute_override
        on
            player_row.team_id = reattribute_override.wrong_team_api_id
            and reattribute_override.mode = 'reattribute_if_cohabiting'
            and reattribute_override.correct_team_api_id in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
            and reattribute_override.wrong_team_api_id not in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
    where
        player_row.fixture_id is not null
        and player_row.team_id is not null
        and player_row.player_id is not null
        and player_row.player_id != 0
),

row_teams as (
    select
        fixture_id,
        player_id,
        any_value(team_id) as team_id
    from player_rows
    group by fixture_id, player_id
    having count(*) = 1
),

event_teams as (
    select
        fixture_id,
        player_id,
        array_agg(distinct team_id) as team_ids
    from attributed
    where
        player_id is not null
        and team_id is not null
        and not is_own_goal
    group by fixture_id, player_id
),

disputes as (
    select
        row_teams.fixture_id,
        row_teams.player_id,
        fixture_participants.season,
        row_teams.team_id as row_team_id,
        if(
            row_teams.team_id = fixture_participants.home_team_id,
            fixture_participants.away_team_id,
            fixture_participants.home_team_id
        ) as other_team_id
    from row_teams
    inner join event_teams
        on
            row_teams.fixture_id = event_teams.fixture_id
            and row_teams.player_id = event_teams.player_id
    inner join fixture_participants
        on row_teams.fixture_id = fixture_participants.fixture_id
    where
        row_teams.team_id in (fixture_participants.home_team_id, fixture_participants.away_team_id)
        and if(
            row_teams.team_id = fixture_participants.home_team_id,
            fixture_participants.away_team_id,
            fixture_participants.home_team_id
        ) in unnest(event_teams.team_ids)
),

squad_listing as (
    select
        disputes.fixture_id,
        disputes.player_id,
        coalesce(logical_or(squad.team_id = disputes.row_team_id), false) as lists_row_team,
        coalesce(logical_or(squad.team_id = disputes.other_team_id), false) as lists_other_team
    from disputes
    left join {{ ref('base_apif__player_team_season') }} as squad
        on
            disputes.player_id = squad.player_id
            and disputes.season = squad.season_year
    group by disputes.fixture_id, disputes.player_id
),

other_matches as (
    select
        disputes.fixture_id,
        disputes.player_id,
        countif(player_rows.team_id = disputes.row_team_id) as at_row_team,
        countif(player_rows.team_id = disputes.other_team_id) as at_other_team
    from disputes
    left join player_rows
        on
            disputes.player_id = player_rows.player_id
            and disputes.fixture_id != player_rows.fixture_id
    group by disputes.fixture_id, disputes.player_id
),

decisions as (
    select
        disputes.fixture_id,
        disputes.player_id,
        case
            when squad_listing.lists_row_team and not squad_listing.lists_other_team
                then disputes.row_team_id
            when squad_listing.lists_other_team and not squad_listing.lists_row_team
                then disputes.other_team_id
            when other_matches.at_row_team > other_matches.at_other_team then disputes.row_team_id
            when other_matches.at_other_team > other_matches.at_row_team then disputes.other_team_id
        end as resolved_player_team_id
    from disputes
    inner join squad_listing
        on
            disputes.fixture_id = squad_listing.fixture_id
            and disputes.player_id = squad_listing.player_id
    inner join other_matches
        on
            disputes.fixture_id = other_matches.fixture_id
            and disputes.player_id = other_matches.player_id
),

team_names as (
    select
        fixture_id,
        team_id,
        max(team_name) as team_name
    from attributed
    group by fixture_id, team_id
)

select
    attributed.league_code,
    attributed.fixture_id,
    attributed.event_index,
    attributed.minute_elapsed,
    attributed.minute_extra,
    attributed.player_id,
    attributed.player_name,
    attributed.assist_player_name,
    attributed.event_type,
    attributed.event_detail,
    attributed.event_comments,
    attributed.raw_ingested_at,
    decisions.resolved_player_team_id,
    coalesce(decisions.resolved_player_team_id, attributed.team_id) as team_id,
    if(
        decisions.resolved_player_team_id != attributed.team_id,
        team_names.team_name,
        attributed.team_name
    ) as team_name
from attributed
left join decisions
    on
        attributed.fixture_id = decisions.fixture_id
        and attributed.player_id = decisions.player_id
        and not attributed.is_own_goal
left join team_names
    on
        attributed.fixture_id = team_names.fixture_id
        and decisions.resolved_player_team_id = team_names.team_id
