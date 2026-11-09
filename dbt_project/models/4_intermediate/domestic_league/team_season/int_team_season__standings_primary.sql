{#
  One row per (team_sk, season_sk): the team's table this season, the one its shown rank and form
  come from. It is the section its latest played round names, otherwise the section in which it
  has played most; a ranking is never a team's table, and the provider's section order decides
  what is still tied. A round names a section when the section's name is in the round's name
  ("Group D - 6"), or the round's stage, its name before the " - " number, is in the section's
  name ("Clausura - 16" names "Clausura - Group A"). mart_team_competitions reads the section from
  here, so the Team page and the team-season marts show one table.
#}

with standings as (
    select
        s.*,
        k.table_kind
    from {{ ref('int_standings__official_rank') }} as s
    inner join {{ ref('int_standings__section_kinds') }} as k
        on
            s.league_code = k.league_code
            and s.season_api_year = k.season_api_year
            and s.group_name = k.group_name
),

latest_rounds as (
    select
        team_sk,
        season_sk,
        round_name
    from {{ ref('int_legs__team_match') }}
    qualify row_number() over (
        partition by team_sk, season_sk
        order by kickoff_datetime desc, fixture_sk desc
    ) = 1
)

select
    s.team_sk,
    s.season_sk,
    s.group_name,
    s.standing_rank,
    s.form,
    s.group_description
from standings as s
left join latest_rounds as r
    on s.team_sk = r.team_sk and s.season_sk = r.season_sk
where s.table_kind != 'ranking'
qualify row_number() over (
    partition by s.team_sk, s.season_sk
    order by
        coalesce(
            strpos(lower(r.round_name), lower(s.group_name)) > 0
            or strpos(lower(s.group_name), lower(regexp_replace(r.round_name, r'\s+-\s+[^-]*$', ''))) > 0,
            false
        ) desc,
        s.played desc,
        s.standing_section_order asc,
        s.group_name asc
) = 1
