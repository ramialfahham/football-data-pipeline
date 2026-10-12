{#
  The line-up research list: every played match the research priority of the cleaning rules
  covers whose lineup_state is not_available, one row each, with its priority group:
  1 our_league: a match of a domestic league in the competition registry;
  2 national_team: a national-team match;
  3 our_club: another competition's match with a club from such a league in that season.
  A walkover not played has no line-ups and is left out. Warn only: the stored rows are the list
  researchers work from, by group and then current season first.
#}
{{ config(store_failures = true, severity = 'warn') }}

with registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

fixtures as (
    select
        f.fixture_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        f.home_team_sk,
        f.home_team_name,
        f.away_team_sk,
        f.away_team_name,
        f.lineup_state,
        r.competition_type
    from {{ ref('mart_competition_fixtures') }} as f
    left join registry as r
        on f.league_code = r.league_code
    where
        f.is_played
        and coalesce(f.award_kind, '') != 'not_played'
),

our_clubs as (
    select distinct
        team_sk,
        season_api_year
    from fixtures,
        unnest([home_team_sk, away_team_sk]) as team_sk
    where competition_type = 'domestic_league'
),

grouped as (
    select
        fixtures.*,
        case
            when fixtures.competition_type = 'domestic_league' then 'our_league'
            when exists (
                select 1
                from our_clubs
                where
                    our_clubs.season_api_year = fixtures.season_api_year
                    and our_clubs.team_sk in (fixtures.home_team_sk, fixtures.away_team_sk)
            ) then 'our_club'
            when fixtures.competition_type in (
                'qualifying', 'continental_championship', 'world_championship'
            ) then 'national_team'
        end as priority_group
    from fixtures
    where fixtures.lineup_state = 'not_available'
)

select
    priority_group,
    league_code,
    season_api_year,
    fixture_sk,
    kickoff_datetime,
    home_team_name,
    away_team_name
from grouped
where priority_group is not null
