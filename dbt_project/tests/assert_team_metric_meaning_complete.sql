{#
  Meaning/context completeness guard (metric layer). The metric_catalogue is the authoritative
  source of each metric's meaning, so a TEAM metric must carry BOTH a performance `direction`
  and an `interpretation` — the seed of the website's good/bad reading and auto-narrative. The
  test FAILS (returns rows) for any team metric missing either.

  Scope = team only. PLAYER metrics are exempt: their direction/interpretation are deferred to
  v1.x (the player benchmark is not yet classified — see metric_catalogue schema.yml and
  feedback memory). A `team and player` row is checked as a team row. (CPO 2026-06-29.)

  Blank cells load from the seed as NULL or empty string depending on quoting, so guard both.
#}

select
    metric_id,
    entity,
    direction,
    interpretation
from {{ ref('metric_catalogue') }}
where
    entity in ('team', 'team and player')
    and (
        direction is null or trim(direction) = ''
        or interpretation is null or trim(interpretation) = ''
    )
