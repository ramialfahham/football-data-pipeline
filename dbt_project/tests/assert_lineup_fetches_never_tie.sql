{#
  The provider can store a team's line-up twice at one ingest time, also under two provider ids of
  one team. Sheets that are identical collapse to one, and a team whose sheets differ has none: no
  sheet of it reaches base. The differing teams are found here from base_apif__lineup_fetches, which
  holds the team after fixture_team_id_overrides, with the sheets compared as JSON. The macro and
  base_apif__lineup_fetch_ties are not used. Returns each model that holds a row of such a team.
#}
{{ config(store_failures = true, severity = 'error') }}

with newest_sheets as (
    select
        league_code,
        fixture_id,
        team_id,
        to_json_string(sheet) as sheet_json
    from (
        select
            * except (raw_ingested_at, provider_team_id),
            raw_ingested_at = max(raw_ingested_at) over (partition by league_code, fixture_id, team_id)
                as in_newest_fetch
        from {{ ref('base_apif__lineup_fetches') }}
    ) as sheet
    where in_newest_fetch
),

differing_teams as (
    select
        league_code,
        fixture_id,
        team_id
    from newest_sheets
    group by league_code, fixture_id, team_id
    having count(distinct sheet_json) > 1
)

select
    'base_apif__lineup_sheets' as model_name,
    sheets.fixture_id,
    sheets.team_id
from {{ ref('base_apif__lineup_sheets') }} as sheets
inner join differing_teams
    on
        sheets.league_code = differing_teams.league_code
        and sheets.fixture_id = differing_teams.fixture_id
        and sheets.team_id = differing_teams.team_id
group by sheets.fixture_id, sheets.team_id
union all
select
    'base_apif__lineups' as model_name,
    lineups.fixture_id,
    lineups.team_id
from {{ ref('base_apif__lineups') }} as lineups
inner join differing_teams
    on
        lineups.league_code = differing_teams.league_code
        and lineups.fixture_id = differing_teams.fixture_id
        and lineups.team_id = differing_teams.team_id
where lineups.lineup_state != 'researched'
group by lineups.fixture_id, lineups.team_id
