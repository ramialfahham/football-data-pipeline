{#- The matches where base loses a value to its team-id filter, one row per match and line table.
    The relations are the macro's only inputs, so a test can run hand-written lines through it:
    statistics_lines  stg_apif__fixture_statistics: fixture_id, team_id, stat_type, stat_value_raw
    lineups           stg_apif__lineups: fixture_id, team_id
    served_sheets     base_apif__lineup_sheets: fixture_id, team_id
    participants      the matches whose two teams are known: fixture_id, home_team_id, away_team_id
    overrides         fixture_team_id_overrides: wrong_team_api_id, correct_team_api_id, mode, fixture_id
    A statistics line with no team id is lost where a stat it carries has no value for a team of the
    match from a line with a team id, in any fetch: base_apif__fixture_statistics merges the newest
    value of each stat from any fetch, under the team id after the overrides. A line-up with no team
    id is lost where a team of the match has no sheet in served_sheets. A line with no fixture id
    names no match and a match not in participants is not judged. -#}
{% macro lines_without_key(statistics_lines, lineups, served_sheets, participants, overrides) -%}
    with statistic_values as (
        select
            fixture_id,
            team_id as provider_team_id,
            stat_type,
            case
                when stat_type = 'Ball Possession'
                    then safe_cast(regexp_replace(stat_value_raw, r'%', '') as int64)
                when stat_type in (
                    'Shots on Goal', 'Shots off Goal', 'Total Shots', 'Blocked Shots', 'Shots insidebox',
                    'Shots outsidebox', 'Fouls', 'Corner Kicks', 'Offsides', 'Free Kicks', 'Yellow Cards',
                    'Red Cards', 'Goalkeeper Saves', 'Total passes', 'Passes accurate'
                )
                    then safe_cast(stat_value_raw as int64)
            end as stat_value
        from {{ statistics_lines }}
        where fixture_id is not null
    ),

    stats_without_team as (
        select distinct
            fixture_id,
            stat_type
        from statistic_values
        where provider_team_id is null and stat_value is not null
    ),

    stats_with_team as (
        select distinct
            fixture_id,
            provider_team_id,
            stat_type
        from statistic_values
        where provider_team_id is not null and stat_value is not null
    ),

    stats_by_team as (
        select
            line.fixture_id,
            line.stat_type,
            coalesce(
                fixture_override.correct_team_api_id,
                alias_override.correct_team_api_id,
                reattribute_override.correct_team_api_id,
                line.provider_team_id
            ) as team_id
        from stats_with_team as line
        left join {{ overrides }} as fixture_override
            on
                line.provider_team_id = fixture_override.wrong_team_api_id
                and line.fixture_id = fixture_override.fixture_id
                and fixture_override.mode = 'reattribute_in_fixture'
        left join {{ overrides }} as alias_override
            on
                line.provider_team_id = alias_override.wrong_team_api_id
                and alias_override.mode = 'alias'
        left join {{ participants }} as line_match
            on line.fixture_id = line_match.fixture_id
        left join {{ overrides }} as reattribute_override
            on
                line.provider_team_id = reattribute_override.wrong_team_api_id
                and reattribute_override.mode = 'reattribute_if_cohabiting'
                and reattribute_override.correct_team_api_id in (line_match.home_team_id, line_match.away_team_id)
                and reattribute_override.wrong_team_api_id not in (line_match.home_team_id, line_match.away_team_id)
    ),

    statistics_lost as (
        select distinct unnamed.fixture_id
        from stats_without_team as unnamed
        inner join {{ participants }} as match_teams
            on unnamed.fixture_id = match_teams.fixture_id
        left join stats_by_team as named
            on
                unnamed.fixture_id = named.fixture_id
                and unnamed.stat_type = named.stat_type
                and named.team_id in (match_teams.home_team_id, match_teams.away_team_id)
        group by unnamed.fixture_id, unnamed.stat_type
        having count(distinct named.team_id) < 2
    ),

    lineups_without_team as (
        select distinct fixture_id
        from {{ lineups }}
        where fixture_id is not null and team_id is null
    ),

    lineups_lost as (
        select unnamed.fixture_id
        from lineups_without_team as unnamed
        inner join {{ participants }} as match_teams
            on unnamed.fixture_id = match_teams.fixture_id
        left join {{ served_sheets }} as sheet
            on
                unnamed.fixture_id = sheet.fixture_id
                and sheet.team_id in (match_teams.home_team_id, match_teams.away_team_id)
        group by unnamed.fixture_id
        having count(distinct sheet.team_id) < 2
    )

    select
        fixture_id,
        'stg_apif__fixture_statistics' as line_table,
        'team_id' as missing_key
    from statistics_lost
    union all
    select
        fixture_id,
        'stg_apif__lineups' as line_table,
        'team_id' as missing_key
    from lineups_lost
{%- endmacro %}
