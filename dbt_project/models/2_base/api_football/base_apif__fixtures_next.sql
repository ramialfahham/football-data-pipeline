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
    f.shootout_home,
    f.shootout_away,
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
    case
        when c.awarded and c.awarded_to_team_id is not null then cast(c.awarded_to_team_id as int64)
        when not coalesce(c.awarded, false) and f.status_short = 'PEN'
            then case
                when f.shootout_home > f.shootout_away then f.home_team_id
                when f.shootout_away > f.shootout_home then f.away_team_id
            end
        when c.awarded or f.status_short in ('FT', 'AET', 'AWD', 'WO')
            then case
                when coalesce(c.goals_home, f.goals_home) > coalesce(c.goals_away, f.goals_away) then f.home_team_id
                when coalesce(c.goals_away, f.goals_away) > coalesce(c.goals_home, f.goals_home) then f.away_team_id
            end
    end as winner_team_id
from latest as f
left join result_corrections as c
    on f.fixture_id = c.fixture_id
