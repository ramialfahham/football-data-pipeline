{#
  One row per (team_sk, season_sk) for table display and marts.
  int_standings__official_rank grain can include multiple rows (e.g. group_description);
  keep the row with latest raw_ingested_at, then the provider's first-listed section (the
  current or final phase; a tournament's group before its cross-group ranking).
#}

with import_int_standings__official_rank as (
    select * from {{ ref('int_standings__official_rank') }}
)

select
    team_sk,
    season_sk,
    standing_rank,
    form,
    group_description
from import_int_standings__official_rank
qualify row_number() over (
    partition by team_sk, season_sk
    order by raw_ingested_at desc nulls last, standing_section_order asc
) = 1
