{#
  A club's country is the country of the domestic league it plays in. Each row is a club whose
  country differs from one of its domestic leagues; some are real (Welsh clubs in the Premier
  League, Canadian clubs in MLS), the rest are provider errors to research. Named case: Chelsea
  (49), England, plays in the Premier League and is never listed.
#}
{{ config(store_failures = true, severity = 'warn') }}

with domestic_leagues as (
    select distinct
        m.team_sk,
        l.league_code,
        l.league_country
    from {{ ref('dim_team_competition_season_mapping') }} as m
    inner join {{ ref('dim_league') }} as l
        on m.league_code = l.league_code
    where l.competition_type = 'domestic_league'
),

compared as (
    select
        t.team_api_id,
        t.team_name,
        t.team_country,
        d.league_code,
        d.league_country,
        t.team_country is distinct from d.league_country as is_mismatch
    from domestic_leagues as d
    inner join {{ ref('dim_team') }} as t
        on d.team_sk = t.team_sk
    where not t.is_national_team
),

named_case as (
    select
        49 as team_api_id,
        'PL' as league_code
)

select
    team_api_id,
    team_name,
    team_country,
    league_code,
    league_country,
    'club country differs from its domestic league' as failure
from compared
where is_mismatch

union all

select
    n.team_api_id,
    c.team_name,
    c.team_country,
    n.league_code,
    c.league_country,
    'named case: Chelsea is not an English club in the Premier League' as failure
from named_case as n
left join compared as c
    on n.team_api_id = c.team_api_id and n.league_code = c.league_code
where c.is_mismatch is distinct from false
