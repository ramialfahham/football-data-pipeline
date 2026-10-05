with src as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_name,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        goals_for_all,
        goals_against_all,
        raw_ingested_at
    from {{ ref('stg_apif__standings') }}
    where
        team_id is not null
        and season is not null
),

-- Grain includes group_name: split-season leagues put a team in more than one
-- section (e.g. a regular table plus a "Championship Round" table). Deduping on
-- (league, season, team) alone would drop one section arbitrarily.
deduped_standings as (
    select *
    from src
    qualify row_number() over (
        partition by league_code, season, team_id, group_name
        order by raw_ingested_at desc
    ) = 1
),

-- The league's official figures and team where the provider's row differs, from
-- seeds/standings_corrections.csv.
table_corrections as (
    select * from {{ ref('standings_corrections') }}
)

select
    s.league_code,
    s.league_api_id,
    s.league_name,
    s.season,
    s.team_id as provider_team_id,
    s.team_name,
    s.form,
    s.group_name,
    s.group_description,
    s.standing_rank as provider_standing_rank,
    s.points as provider_points,
    s.goals_diff as provider_goals_diff,
    s.played_all as provider_played_all,
    s.wins_all as provider_wins_all,
    s.draws_all as provider_draws_all,
    s.losses_all as provider_losses_all,
    s.goals_for_all as provider_goals_for_all,
    s.goals_against_all as provider_goals_against_all,
    c.source as result_correction_source,
    s.raw_ingested_at,
    coalesce(c.official_team_id, s.team_id) as team_id,
    coalesce(c.standing_rank, s.standing_rank) as standing_rank,
    coalesce(c.points, s.points) as points,
    if(c.team_id is null, s.goals_diff, c.goals_for - c.goals_against) as goals_diff,
    coalesce(c.played, s.played_all) as played_all,
    coalesce(c.wins, s.wins_all) as wins_all,
    coalesce(c.draws, s.draws_all) as draws_all,
    coalesce(c.losses, s.losses_all) as losses_all,
    coalesce(c.goals_for, s.goals_for_all) as goals_for_all,
    coalesce(c.goals_against, s.goals_against_all) as goals_against_all
from deduped_standings as s
left join table_corrections as c
    on
        s.league_code = c.league_code
        and s.season = c.season
        and s.team_id = c.team_id
        and s.group_name = c.group_name
