with import_base_apif__fixtures_next as (
    select * from {{ ref('base_apif__fixtures_next') }}
),

import_dim_venue as (
    select * from {{ ref('dim_venue') }}
),

import_dim_league as (
    select * from {{ ref('dim_league') }}
),

import_dim_country as (
    select * from {{ ref('dim_country') }}
),

import_dim_timezone as (
    select * from {{ ref('dim_timezone') }}
),

-- The venue's zone, else the competition country's, else UTC: every fixture has a zone.
fixture_zone as (
    select
        fixtures.fixture_id,
        fixtures.kickoff_datetime,
        coalesce(import_dim_venue.time_zone, import_dim_country.time_zone, 'UTC') as kickoff_time_zone
    from import_base_apif__fixtures_next as fixtures
    left join import_dim_venue
        on fixtures.venue_id = import_dim_venue.venue_api_id
    left join import_dim_league
        on fixtures.league_code = import_dim_league.league_code
    left join import_dim_country
        on import_dim_league.league_country = import_dim_country.country_name
),

fixture_year as (
    select
        fixture_id,
        kickoff_datetime,
        kickoff_time_zone,
        timestamp(date_trunc(date(kickoff_datetime), year)) as year_start,
        timestamp(date_add(date_trunc(date(kickoff_datetime), year), interval 6 month)) as year_middle
    from fixture_zone
),

fixture_offsets as (
    select
        fixture_id,
        kickoff_datetime,
        kickoff_time_zone,
        {{ utc_offset_minutes('kickoff_datetime', 'kickoff_time_zone') }} as offset_now,
        {{ utc_offset_minutes('year_start', 'kickoff_time_zone') }} as offset_january,
        {{ utc_offset_minutes('year_middle', 'kickoff_time_zone') }} as offset_july
    from fixture_year
),

fixture_clock as (
    select
        fixture_offsets.fixture_id,
        fixture_offsets.kickoff_time_zone,
        datetime(fixture_offsets.kickoff_datetime, fixture_offsets.kickoff_time_zone) as kickoff_local,
        {{ kickoff_zone_label(
            'fixture_offsets.offset_now',
            'fixture_offsets.offset_january',
            'fixture_offsets.offset_july',
            'fixture_offsets.kickoff_datetime',
            'fixture_offsets.kickoff_time_zone',
            'import_dim_timezone.label_standard',
            'import_dim_timezone.label_daylight'
        ) }} as kickoff_zone_label
    from fixture_offsets
    left join import_dim_timezone
        on fixture_offsets.kickoff_time_zone = import_dim_timezone.time_zone
),

import_base_apif__fixture_rounds as (
    select * from {{ ref('base_apif__fixture_rounds') }}
),

fixtures as (
    select
        import_base_apif__fixtures_next.*,
        fixture_clock.kickoff_time_zone,
        fixture_clock.kickoff_local,
        fixture_clock.kickoff_zone_label,
        import_base_apif__fixture_rounds.round_stage_kind
    from import_base_apif__fixtures_next
    left join fixture_clock
        on import_base_apif__fixtures_next.fixture_id = fixture_clock.fixture_id
    left join import_base_apif__fixture_rounds
        on
            import_base_apif__fixtures_next.league_code = import_base_apif__fixture_rounds.league_code
            and import_base_apif__fixtures_next.season = import_base_apif__fixture_rounds.season_api_year
            and import_base_apif__fixtures_next.round_name = import_base_apif__fixture_rounds.round_name
)

select
    cast(fixture_id as int64) as fixture_sk,
    fixture_id as fixture_api_id,
    cast(league_api_id as int64) as league_sk,
    {{ dbt_utils.generate_surrogate_key(['league_api_id', 'season']) }} as season_sk,
    cast(home_team_id as int64) as home_team_sk,
    cast(away_team_id as int64) as away_team_sk,
    cast(format_date('%Y%m%d', fixture_date) as int64) as kickoff_date_sk,
    league_code,
    season as season_api_year,
    home_team_id as home_team_api_id,
    away_team_id as away_team_api_id,
    fixture_date,
    kickoff_datetime,
    kickoff_time_zone,
    kickoff_local,
    kickoff_zone_label,
    kickoff_timezone,
    status_short,
    status_long,
    status_elapsed,
    is_finished,
    is_played,
    is_awarded_result,
    is_shootout,
    round_name,
    round_order,
    round_stage_kind,
    coalesce(round_stage_kind = 'table' and is_shootout, false) as is_table_shootout,
    goals_home,
    goals_away,
    shootout_home,
    shootout_away,
    cast(winner_team_id as int64) as winner_team_sk,
    result_needs_research,
    cast(awarded_to_team_id as int64) as awarded_to_team_sk,
    award_kind,
    on_pitch_home,
    on_pitch_away,
    venue_id as venue_api_id,
    venue_name as venue_name_snapshot,
    venue_city as venue_city_snapshot,
    raw_ingested_at
from fixtures
