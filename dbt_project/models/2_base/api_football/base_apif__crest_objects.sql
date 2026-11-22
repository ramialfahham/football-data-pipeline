-- The crests and league logos held in the crest bucket: one row per stored object, from the
-- newest state the crest phase wrote. An object the provider no longer serves (status missing)
-- has no files, so it is left out and its dimension row publishes no address.
with import_stg_apif__crest_objects as (
    select * from {{ ref('stg_apif__crest_objects') }}
)

select
    crest_kind,
    provider_id,
    source_sha256,
    fetched_at,
    checked_at,
    raw_ingested_at
from import_stg_apif__crest_objects
where
    crest_status = 'ok'
    and provider_id is not null
    and crest_kind in ('teams', 'leagues')
