with src as (
    select *
    from {{ ref('stg_apif__fixtures_next') }}
    where fixture_id is not null
),

latest as (
    select *
    from src
    qualify row_number() over (
        partition by fixture_id
        order by raw_ingested_at desc
    ) = 1
),

-- A team id two clubs share, corrected inside the one fixture named, from
-- seeds/fixture_team_id_overrides.csv. The match feeds read their participants from here.
fixture_overrides as (
    select
        cast(fixture_id as int64) as fixture_id,
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id
    from {{ ref('fixture_team_id_overrides') }}
    where mode = 'reattribute_in_fixture'
),

corrected as (
    select
        latest.* except (home_team_id, away_team_id),
        coalesce(home_override.correct_team_api_id, latest.home_team_id) as home_team_id,
        coalesce(away_override.correct_team_api_id, latest.away_team_id) as away_team_id
    from latest
    left join fixture_overrides as home_override
        on
            latest.fixture_id = home_override.fixture_id
            and latest.home_team_id = home_override.wrong_team_api_id
    left join fixture_overrides as away_override
        on
            latest.fixture_id = away_override.fixture_id
            and latest.away_team_id = away_override.wrong_team_api_id
),

-- The league's official result where the provider's differs, from seeds/fixture_result_corrections.csv.
result_corrections as (
    select * from {{ ref('fixture_result_corrections') }}
)

select
    f.league_code,
    f.fixture_id,
    f.league_api_id,
    f.season,
    f.fixture_date,
    f.kickoff_datetime,
    f.kickoff_timezone,
    f.status_elapsed,
    f.round_name,
    f.home_team_id,
    f.away_team_id,
    c.awarded_to_team_id,
    c.award_kind,
    c.on_pitch_home,
    c.on_pitch_away,
    f.goals_home as provider_goals_home,
    f.goals_away as provider_goals_away,
    f.shootout_home as provider_shootout_home,
    f.shootout_away as provider_shootout_away,
    f.status_short as provider_status_short,
    c.source as result_correction_source,
    f.venue_id,
    f.venue_name,
    f.venue_city,
    f.raw_ingested_at,
    if(c.awarded, 'AWD', f.status_short) as status_short,
    if(c.awarded, 'Technical loss', f.status_long) as status_long,
    coalesce(c.goals_home, f.goals_home) as goals_home,
    coalesce(c.goals_away, f.goals_away) as goals_away,
    coalesce(c.shootout_home, f.shootout_home) as shootout_home,
    coalesce(c.shootout_away, f.shootout_away) as shootout_away,
    case
        when c.awarded and c.awarded_to_team_id is not null then cast(c.awarded_to_team_id as int64)
        when not coalesce(c.awarded, false) and f.status_short = 'PEN'
            then case
                when coalesce(c.shootout_home, f.shootout_home) > coalesce(c.shootout_away, f.shootout_away)
                    then f.home_team_id
                when coalesce(c.shootout_away, f.shootout_away) > coalesce(c.shootout_home, f.shootout_home)
                    then f.away_team_id
            end
        when c.awarded or f.status_short in ('FT', 'AET', 'AWD', 'WO')
            then case
                when coalesce(c.goals_home, f.goals_home) > coalesce(c.goals_away, f.goals_away) then f.home_team_id
                when coalesce(c.goals_away, f.goals_away) > coalesce(c.goals_home, f.goals_home) then f.away_team_id
            end
    end as winner_team_id
from corrected as f
left join result_corrections as c
    on f.fixture_id = c.fixture_id
