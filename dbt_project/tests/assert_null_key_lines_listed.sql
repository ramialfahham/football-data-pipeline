-- A match where base loses a value to its team-id filter is on the research list as
-- null_key_line_withheld, and no other match is. The matches are derived from staging here, never
-- from base_apif__fixture_lines_without_key:
--   - a statistics line with a fixture id and no team id carries a value for a stat that a team of
--     the match has from no line with a team id, in any fetch (the way base merges the stats);
--   - a line-up with a fixture id and no team id, in a match where a team's latest fetch has no
--     players.
--   - not_listed: such a match is not on the list.
--   - listed_without_line: the list holds the match and none of the above is true of it.
-- A match with a team id the overrides seed rewrites, or a line-up tie the provider stored twice
-- with different content, is left out on both sides: another row kind lists the tie, and
-- assert_lines_without_key_answer_key proves the override mapping.

{{ config(store_failures = true, severity = 'error') }}

with participants as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where home_team_id is not null and away_team_id is not null
),

statistic_lines as (
    select
        fixture_id,
        team_id,
        stat_type,
        safe_cast(
            if(stat_type = 'Ball Possession', regexp_replace(stat_value_raw, r'%', ''), stat_value_raw) as int64
        ) is not null as has_value
    from {{ ref('stg_apif__fixture_statistics') }}
    where
        fixture_id is not null
        and stat_type in (
            'Shots on Goal', 'Shots off Goal', 'Total Shots', 'Blocked Shots', 'Shots insidebox',
            'Shots outsidebox', 'Fouls', 'Corner Kicks', 'Offsides', 'Free Kicks', 'Ball Possession',
            'Yellow Cards', 'Red Cards', 'Goalkeeper Saves', 'Total passes', 'Passes accurate'
        )
),

statistics_expected as (
    select statistic_lines.fixture_id
    from statistic_lines
    inner join participants
        on statistic_lines.fixture_id = participants.fixture_id
    group by statistic_lines.fixture_id, statistic_lines.stat_type
    having
        logical_or(statistic_lines.team_id is null and statistic_lines.has_value)
        and count(distinct if(
            statistic_lines.has_value
            and statistic_lines.team_id in (participants.home_team_id, participants.away_team_id),
            statistic_lines.team_id,
            null
        )) < 2
),

latest_sheets as (
    select
        fixture_id,
        team_id,
        coalesce(array_length(json_query_array(start_xi_json)), 0)
        + coalesce(array_length(json_query_array(substitutes_json)), 0) > 0 as has_players
    from {{ ref('stg_apif__lineups') }}
    where fixture_id is not null and team_id is not null
    qualify row_number() over (
        partition by league_code, fixture_id, team_id
        order by raw_ingested_at desc
    ) = 1
),

lineups_expected as (
    select unnamed.fixture_id
    from (
        select distinct fixture_id
        from {{ ref('stg_apif__lineups') }}
        where fixture_id is not null and team_id is null
    ) as unnamed
    inner join participants
        on unnamed.fixture_id = participants.fixture_id
    left join latest_sheets
        on
            unnamed.fixture_id = latest_sheets.fixture_id
            and latest_sheets.has_players
            and latest_sheets.team_id in (participants.home_team_id, participants.away_team_id)
    group by unnamed.fixture_id
    having count(distinct latest_sheets.team_id) < 2
),

rewritten_teams as (
    select distinct cast(wrong_team_api_id as int64) as team_id
    from {{ ref('fixture_team_id_overrides') }}
),

left_out as (
    select distinct lines.fixture_id
    from {{ ref('stg_apif__fixture_statistics') }} as lines
    inner join rewritten_teams
        on lines.team_id = rewritten_teams.team_id
    where lines.fixture_id is not null
    union distinct
    select distinct lines.fixture_id
    from {{ ref('stg_apif__lineups') }} as lines
    inner join rewritten_teams
        on lines.team_id = rewritten_teams.team_id
    where lines.fixture_id is not null
    union distinct
    select distinct ties.fixture_id
    from {{ ref('base_apif__lineup_fetch_ties') }} as ties
    where ties.rows_differ and ties.fixture_id is not null
),

expected as (
    select fixture_id from statistics_expected
    union distinct
    select fixture_id from lineups_expected
),

expected_in_fixtures as (
    select expected.fixture_id
    from expected
    inner join {{ ref('fct_fixture') }} as fixtures
        on expected.fixture_id = fixtures.fixture_sk
    left join left_out
        on expected.fixture_id = left_out.fixture_id
    where left_out.fixture_id is null
),

listed as (
    select research.fixture_sk as fixture_id
    from {{ ref('mart_competition_research_list') }} as research
    left join left_out
        on research.fixture_sk = left_out.fixture_id
    where
        research.check_name = 'null_key_line_withheld'
        and left_out.fixture_id is null
)

select
    'not_listed' as problem,
    expected_in_fixtures.fixture_id
from expected_in_fixtures
left join listed
    on expected_in_fixtures.fixture_id = listed.fixture_id
where listed.fixture_id is null
union all
select
    'listed_without_line' as problem,
    listed.fixture_id
from listed
left join expected_in_fixtures
    on listed.fixture_id = expected_in_fixtures.fixture_id
where expected_in_fixtures.fixture_id is null
