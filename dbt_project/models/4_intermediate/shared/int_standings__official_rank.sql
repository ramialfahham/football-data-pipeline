{#
  Every standings row with its official place: fct_standings, with standing_rank in the league's
  own tie-break order where it can be applied and the provider's rank everywhere else.

  The order comes from int_team_season__table_by_time at the section's latest kick-off. It applies
  only to a section where every team's matches played and points equal its standings row; that
  section is ordered by place_by_rules, and teams the rules leave level keep the provider's order.
  Every other section, and every table int_team_season__table_by_time does not cover, keeps the
  provider's rank.

  Grain: (league_code, season_api_year, group_name, team_sk).
#}

with standings as (
    select * from {{ ref('fct_standings') }}
),

rule_table as (
    select
        league_code,
        season_api_year,
        group_name,
        team_sk,
        played,
        table_points,
        place_by_rules
    from {{ ref('int_team_season__table_by_time') }}
    qualify table_at = max(table_at) over (partition by league_code, season_api_year, group_name)
),

compared as (
    select
        s.*,
        r.place_by_rules,
        logical_and(coalesce(r.played = s.played and r.table_points = s.points, false)) over (
            partition by s.league_code, s.season_api_year, s.group_name
        ) as is_section_matched
    from standings as s
    left join rule_table as r
        on
            s.league_code = r.league_code
            and s.season_api_year = r.season_api_year
            and s.group_name = r.group_name
            and s.team_sk = r.team_sk
)

select
    * except (standing_rank, place_by_rules, is_section_matched),
    if(
        is_section_matched,
        row_number() over (
            partition by league_code, season_api_year, group_name
            order by place_by_rules, standing_rank, team_sk
        ),
        standing_rank
    ) as standing_rank
from compared
