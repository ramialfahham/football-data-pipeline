{#
  The share of team stat lines the cleaning corrected or left blank because of a contradiction (a
  non-empty stat_corrections), per competition-season, stays within one limit for every
  competition-season of at least 20 lines, set just above the highest share measured on the built
  cleaning (the Jupiler Pro League's 2025 season, whose on target, off target and blocked shots
  often miss the total). A share over a single match is not a share, so smaller competition-seasons
  are left out. Only lines with shots or shots on target count: a team-match without them has
  almost nothing to correct. It catches a provider feed that breaks badly before its numbers reach a
  page; a slow drift is what the comparison with prod before each merge shows.
  Returns each competition-season above the limit.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set limit = 0.20 %}
{% set min_lines = 20 %}

with team_lines as (
    select
        s.league_code,
        f.season,
        array_length(s.stat_corrections) > 0 as is_corrected
    from {{ ref('base_apif__fixture_statistics') }} as s
    left join {{ ref('base_apif__fixtures_next') }} as f
        on s.fixture_id = f.fixture_id
    where s.shots is not null or s.shots_on_target is not null or array_length(s.stat_corrections) > 0
)

select
    league_code,
    season,
    countif(is_corrected) as corrected_lines,
    count(*) as team_lines,
    safe_divide(countif(is_corrected), count(*)) as corrected_share
from team_lines
group by league_code, season
having count(*) >= {{ min_lines }} and safe_divide(countif(is_corrected), count(*)) > {{ limit }}
