{#
  Meaning/context completeness guard (metric layer). The metric_catalogue is the authoritative
  source of each metric's meaning, so a TEAM metric must carry BOTH a performance `direction`
  and an `interpretation` — the seed of the website's good/bad reading and auto-narrative. The
  test FAILS (returns rows) for any team metric missing either.

  Scope = team only, DELIBERATELY. Player metrics now DO carry a `direction` — the catalogue-wide
  direction sweep populated every row — so the old "player benchmark is not yet classified"
  rationale is retired. The test stays team-scoped because the player `interpretation` sweep is
  still outstanding: many player rows now have a direction but a blank interpretation, so
  broadening this test today would fail on interpretation, not on direction. Broaden it once that
  sweep lands. A `team and player` row is checked as a team row. (CPO 2026-06-29; scope
  re-justified 2026-07-21.)

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
