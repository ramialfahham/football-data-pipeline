{#
  Hand-written lines run through lines_without_key, the rule the base model calls. Returns each
  match the rule lists and should not, and each it should list and misses: a match whose value is
  lost to the team-id filter that is not listed stays out of the research list, and a match listed
  for nothing sends the research to a match with nothing wrong. Every match is two teams, 5 and 6,
  and the fixture ids are ones no seed row names.
  Statistics, one stat of one NULL-team line per match unless said:
    990000001 team 6 has no Fouls from a line with a team id: listed
    990000002 both teams have Fouls: not listed, in whichever fetch the NULL-team line is
    990000003 the NULL-team line carries no value: not listed
    990000004 the NULL-team line carries a stat base does not read: not listed
    990000005 team 7 is team 5 under an alias, so one team has Fouls: listed
    990000006 a Ball Possession share of one team only: listed
    990000007 a third team has Fouls, team 6 has not: listed
    990000008 a match without known teams: not judged
    990000014 team 8 is team 6 in this fixture by a reattribute_in_fixture row: not listed
    990000015 the same row does not apply to another fixture, so team 6 has no Fouls: listed
    990000016 team 9 is team 6 by a reattribute_if_cohabiting row: not listed
    990000017 teams 6 and 9 both play the match, so the row does not apply: not listed
    no fixture id: names no match
  Line-ups:
    990000010 team 6 has no sheet: listed
    990000011 both teams have a sheet: not listed
    990000012 a third team has a sheet, team 6 has not: listed
    990000013 no NULL-team line-up: not listed
    no fixture id: names no match
#}
{{ config(store_failures = true, severity = 'error') }}

with participants as (
    select *
    from unnest([
        struct(990000001 as fixture_id, 5 as home_team_id, 6 as away_team_id),
        struct(990000002, 5, 6),
        struct(990000003, 5, 6),
        struct(990000004, 5, 6),
        struct(990000005, 5, 6),
        struct(990000006, 5, 6),
        struct(990000007, 5, 6),
        struct(990000014, 5, 6),
        struct(990000015, 5, 6),
        struct(990000016, 5, 6),
        struct(990000017, 6, 9),
        struct(990000010, 5, 6),
        struct(990000011, 5, 6),
        struct(990000012, 5, 6),
        struct(990000013, 5, 6)
    ])
),

overrides as (
    select *
    from unnest([
        struct(7 as wrong_team_api_id, 5 as correct_team_api_id, 'alias' as mode, cast(null as int64) as fixture_id),
        struct(8, 6, 'reattribute_in_fixture', 990000014),
        struct(9, 6, 'reattribute_if_cohabiting', cast(null as int64))
    ])
),

statistics_rows as (
    select *
    from unnest([
        struct(990000001 as fixture_id, cast(null as int64) as team_id, 'Fouls' as stat_type, '10' as stat_value_raw),
        struct(990000001, 5, 'Fouls', '12'),
        struct(990000001, 6, 'Corner Kicks', '3'),
        struct(990000002, cast(null as int64), 'Fouls', '10'),
        struct(990000002, 5, 'Fouls', '12'),
        struct(990000002, 6, 'Fouls', '9'),
        struct(990000003, cast(null as int64), 'Fouls', cast(null as string)),
        struct(990000003, cast(null as int64), 'Corner Kicks', 'n/a'),
        struct(990000003, 5, 'Fouls', '12'),
        struct(990000003, 5, 'Corner Kicks', '4'),
        struct(990000004, cast(null as int64), 'Expected Goals', '1.2'),
        struct(990000004, 5, 'Expected Goals', '0.8'),
        struct(990000005, cast(null as int64), 'Fouls', '10'),
        struct(990000005, 5, 'Fouls', '12'),
        struct(990000005, 7, 'Fouls', '11'),
        struct(990000006, cast(null as int64), 'Ball Possession', '45%'),
        struct(990000006, 5, 'Ball Possession', '55%'),
        struct(990000007, cast(null as int64), 'Fouls', '10'),
        struct(990000007, 5, 'Fouls', '12'),
        struct(990000007, 99, 'Fouls', '11'),
        struct(990000008, cast(null as int64), 'Fouls', '10'),
        struct(990000014, cast(null as int64), 'Fouls', '10'),
        struct(990000014, 5, 'Fouls', '12'),
        struct(990000014, 8, 'Fouls', '11'),
        struct(990000015, cast(null as int64), 'Fouls', '10'),
        struct(990000015, 5, 'Fouls', '12'),
        struct(990000015, 8, 'Fouls', '11'),
        struct(990000016, cast(null as int64), 'Fouls', '10'),
        struct(990000016, 5, 'Fouls', '12'),
        struct(990000016, 9, 'Fouls', '11'),
        struct(990000017, cast(null as int64), 'Fouls', '10'),
        struct(990000017, 6, 'Fouls', '12'),
        struct(990000017, 9, 'Fouls', '11'),
        struct(cast(null as int64), cast(null as int64), 'Fouls', '10')
    ])
),

lineup_rows as (
    select *
    from unnest([
        struct(990000010 as fixture_id, cast(null as int64) as team_id),
        struct(990000010, 5),
        struct(990000011, cast(null as int64)),
        struct(990000011, 5),
        struct(990000011, 6),
        struct(990000012, cast(null as int64)),
        struct(990000012, 5),
        struct(990000013, 5),
        struct(cast(null as int64), cast(null as int64))
    ])
),

served_sheets as (
    select *
    from unnest([
        struct(990000010 as fixture_id, 5 as team_id),
        struct(990000011, 5),
        struct(990000011, 6),
        struct(990000012, 5),
        struct(990000012, 99),
        struct(990000013, 5)
    ])
),

actual as (
    select distinct
        fixture_id,
        line_table,
        missing_key
    from (
        {{ lines_without_key('statistics_rows', 'lineup_rows', 'served_sheets', 'participants', 'overrides') }}
    )
),

expected as (
    select *
    from unnest([
        struct(990000001 as fixture_id, 'stg_apif__fixture_statistics' as line_table, 'team_id' as missing_key),
        struct(990000005, 'stg_apif__fixture_statistics', 'team_id'),
        struct(990000006, 'stg_apif__fixture_statistics', 'team_id'),
        struct(990000007, 'stg_apif__fixture_statistics', 'team_id'),
        struct(990000015, 'stg_apif__fixture_statistics', 'team_id'),
        struct(990000010, 'stg_apif__lineups', 'team_id'),
        struct(990000012, 'stg_apif__lineups', 'team_id')
    ])
)

select
    'not_listed' as problem,
    e.fixture_id,
    e.line_table,
    e.missing_key
from expected as e
left join actual as a
    on e.fixture_id = a.fixture_id and e.line_table = a.line_table and e.missing_key = a.missing_key
where a.fixture_id is null
union all
select
    'listed_for_nothing' as problem,
    a.fixture_id,
    a.line_table,
    a.missing_key
from actual as a
left join expected as e
    on a.fixture_id = e.fixture_id and a.line_table = e.line_table and a.missing_key = e.missing_key
where e.fixture_id is null
