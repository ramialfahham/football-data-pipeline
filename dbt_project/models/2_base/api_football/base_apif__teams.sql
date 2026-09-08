with stg_teams as (
    select
        league_code,
        team_id as team_api_id,
        team_name,
        team_code,
        team_country,
        founded_year as team_founded_year,
        team_logo_url,
        venue_id as venue_api_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        season,
        raw_ingested_at
    from {{ ref('stg_apif__teams') }}
    where team_id is not null
),

stg_fixtures as (
    select
        league_code,
        fixture_id,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        raw_ingested_at
    from {{ ref('stg_apif__fixtures_next') }}
),

-- Standings can introduce teams that never appear in the teams endpoint or in
-- the fixtures_next window (e.g. a club ranked in a conference table whose next
-- match falls outside the ingested round). dim_team must cover every team that
-- appears in any downstream fact, including fct_standings, so standings is a
-- first-class team source here.
stg_standings as (
    select
        league_code,
        team_id as team_api_id,
        team_name,
        raw_ingested_at
    from {{ ref('stg_apif__standings') }}
    where team_id is not null
),

-- Fixture-level sources (statistics, players, events) carry team ids for teams
-- that appear in no other source: the teams endpoint, the fixtures_next window,
-- and standings all miss lower-division clubs that play only a domestic-cup tie
-- (e.g. DFB-Pokal). dim_team must cover every team referenced by a fanout fact,
-- so these are first-class team sources too.
stg_fixture_level as (
    select
        league_code,
        fixture_id,
        team_id as team_api_id,
        team_name,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_statistics') }}
    where team_id is not null

    union all

    select
        league_code,
        fixture_id,
        team_id as team_api_id,
        team_name,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_players') }}
    where team_id is not null

    union all

    select
        league_code,
        fixture_id,
        team_id as team_api_id,
        team_name,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_events') }}
    where team_id is not null
),

-- Fixture participants and the CPO-owned team-id corrections, exactly as the three fixture-level
-- base models apply them (seeds/fixture_team_id_overrides.csv). Only fixtures whose two
-- participants are BOTH known are kept, so the participant checks never hit the
-- NOT IN (value, NULL) -> UNKNOWN trap.
fixture_participants as (
    select
        fixture_id,
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

-- ⛔ THE KEYS MUST GO THROUGH THE OVERRIDE HERE TOO, and this model is the reason it is not enough
-- to correct the three fixture-level base models. It reads the fixture feeds from STAGING, so a
-- correction applied in base does not reach it: a retired id would still be minted as a team key,
-- and if no source can name it -- which is the whole shape of the defect -- dim_team gets a row
-- with a null team_name, its not_null test stops the build, and a bare `dbt build` then skips
-- every model below it. One stub team block from the provider halts the nightly.
-- Only the KEYS are corrected. The name CTEs below deliberately keep reading staging: a wrong id
-- can carry a perfectly correct name of its own (Mação 4767 is a real team; only its rows in two
-- WCQAS fixtures are mis-attributed), and base_apif__fixture_players / _statistics drop team_name
-- at the base layer, so re-pointing the name sources would silently remove a name path.
-- ⚠ That asymmetry has one consequence worth stating, and it only arises under `alias` mode: a key
-- folded into its canonical id takes its name from the CANONICAL id's own sources, never from the
-- duplicate's. If the canonical id is named nowhere, the result is a row with no name rather than
-- one borrowed from the duplicate — which is correct (a duplicate's label is not evidence about
-- the canonical entity) and is caught loudly by not_null on dim_team.team_name rather than shipped.
fixture_level_keys as (
    select
        stg_fixture_level.league_code,
        coalesce(
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            stg_fixture_level.team_api_id
        ) as team_api_id
    from stg_fixture_level
    left join overrides as alias_override
        on
            stg_fixture_level.team_api_id = alias_override.wrong_team_api_id
            and alias_override.mode = 'alias'
    left join fixture_participants
        on stg_fixture_level.fixture_id = fixture_participants.fixture_id
    left join overrides as reattribute_override
        on
            stg_fixture_level.team_api_id = reattribute_override.wrong_team_api_id
            and reattribute_override.mode = 'reattribute_if_cohabiting'
            and reattribute_override.correct_team_api_id in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
            and reattribute_override.wrong_team_api_id not in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
),

team_keys as (
    select
        league_code,
        team_api_id
    from stg_teams

    union all

    select
        league_code,
        home_team_id as team_api_id
    from stg_fixtures
    where home_team_id is not null

    union all

    select
        league_code,
        away_team_id as team_api_id
    from stg_fixtures
    where away_team_id is not null

    union all

    select
        league_code,
        team_api_id
    from stg_standings

    union all

    select
        league_code,
        team_api_id
    from fixture_level_keys
),

distinct_team_keys as (
    select distinct
        league_code,
        team_api_id
    from team_keys
),

teams_latest as (
    select
        *,
        row_number() over (
            partition by league_code, team_api_id
            order by season desc, raw_ingested_at desc
        ) as rn
    from stg_teams
),

fixture_team_names as (
    select
        league_code,
        team_api_id,
        team_name,
        raw_ingested_at,
        row_number() over (
            partition by league_code, team_api_id
            order by raw_ingested_at desc, fixture_id desc
        ) as rn
    from (
        select
            league_code,
            fixture_id,
            home_team_id as team_api_id,
            home_team_name as team_name,
            raw_ingested_at
        from stg_fixtures
        where home_team_id is not null and home_team_name is not null

        union all

        select
            league_code,
            fixture_id,
            away_team_id as team_api_id,
            away_team_name as team_name,
            raw_ingested_at
        from stg_fixtures
        where away_team_id is not null and away_team_name is not null
    )
),

standings_team_names as (
    select
        league_code,
        team_api_id,
        team_name,
        raw_ingested_at,
        row_number() over (
            partition by league_code, team_api_id
            order by raw_ingested_at desc
        ) as rn
    from stg_standings
    where team_name is not null
),

fixture_level_team_names as (
    select
        league_code,
        team_api_id,
        team_name,
        raw_ingested_at,
        row_number() over (
            partition by league_code, team_api_id
            order by raw_ingested_at desc
        ) as rn
    from stg_fixture_level
    where team_name is not null
)

select
    k.league_code,
    k.team_api_id,
    t.team_code,
    t.team_country,
    t.team_founded_year,
    t.team_logo_url,
    t.venue_api_id,
    t.venue_name,
    t.venue_address,
    t.venue_city,
    t.venue_capacity,
    coalesce(
        t.team_name, fn.team_name, sn.team_name, fl.team_name
    ) as team_name,
    coalesce(
        t.raw_ingested_at, fn.raw_ingested_at, sn.raw_ingested_at, fl.raw_ingested_at
    ) as raw_ingested_at
from distinct_team_keys as k
left join teams_latest as t
    on
        k.league_code = t.league_code
        and k.team_api_id = t.team_api_id
        and t.rn = 1
left join fixture_team_names as fn
    on
        k.league_code = fn.league_code
        and k.team_api_id = fn.team_api_id
        and fn.rn = 1
left join standings_team_names as sn
    on
        k.league_code = sn.league_code
        and k.team_api_id = sn.team_api_id
        and sn.rn = 1
left join fixture_level_team_names as fl
    on
        k.league_code = fl.league_code
        and k.team_api_id = fl.team_api_id
        and fl.rn = 1
