{%- set sample_source = source('football_data', 'raw_d1_2526') -%}
{%- set relations = dbt_utils.get_relations_by_prefix(
    database=sample_source.database,
    schema=sample_source.schema,
    prefix='RAW_D1_'
) -%}

with unioned as (
    {{ dbt_utils.union_relations(
        relations=relations,
        source_column_name='raw_table'
    ) }}
)

select
    {{
        dbt_utils.generate_surrogate_key([
            "cast(regexp_extract(raw_table, r'RAW_D1_(\\d{4})') as string)",
            "cast(Date as string)",
            "cast(HomeTeam as string)",
            "cast(AwayTeam as string)"
        ])
    }} as match_id,
    'D1' as league,
    regexp_extract(raw_table, r'RAW_D1_(\\d{4})') as season,
    Date as match_date,
    HomeTeam as home_team,
    AwayTeam as away_team,
    cast(FTHG as int64) as full_time_home_goals,
    cast(FTAG as int64) as full_time_away_goals,
    cast(FTR as string) as full_time_result,
    raw_table
from unioned
