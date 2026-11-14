{#
  The share of player-match rows the cleaning corrected or left blank because of a contradiction
  or a disagreement between sources (a non-empty stat_corrections), per competition-season, stays
  within one limit for every competition-season, set just above the highest share measured on the
  built cleaning. It catches a provider feed that breaks badly before its numbers reach a page; a
  slow drift is what the comparison with prod before each merge shows.
  It measures the matches whose player stats are final: a match whose latest fetch came under 3
  days after kickoff waits for its second fetch (docs/data_contract.md, "Second fetch"), the
  ingestion's coverage.second_fetch_due rule.
  Returns each competition-season above the limit, and the named case: Aruba-Antigua and Barbuda
  (fixture 1639932, 23 Sep 2026, fetched again on 6 Oct) is measured.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set limit = 0.08 %}

with fetches as (
    select
        fixture_id,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_players') }}
    union all
    select
        fixture_id,
        raw_ingested_at
    from {{ ref('stg_apif__lineups') }}
    union all
    select
        fixture_id,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_events') }}
    union all
    select
        fixture_id,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_statistics') }}
),

latest_fetches as (
    select
        fixture_id,
        max(raw_ingested_at) as latest_fetch
    from fetches
    group by fixture_id
),

awaiting_second_fetch as (
    select f.fixture_id
    from {{ ref('base_apif__fixtures_next') }} as f
    inner join latest_fetches as l
        on f.fixture_id = l.fixture_id
    where l.latest_fetch < timestamp_add(f.kickoff_datetime, interval 72 hour)
),

player_rows as (
    select
        p.league_code,
        f.season,
        p.fixture_id,
        array_length(p.stat_corrections) > 0 as is_corrected
    from {{ ref('base_apif__fixture_players') }} as p
    left join {{ ref('base_apif__fixtures_next') }} as f
        on p.fixture_id = f.fixture_id
    left join awaiting_second_fetch as w
        on p.fixture_id = w.fixture_id
    where w.fixture_id is null
),

over_limit as (
    select
        'over_limit' as failure,
        league_code,
        season,
        countif(is_corrected) as corrected_rows,
        count(*) as player_rows,
        safe_divide(countif(is_corrected), count(*)) as corrected_share
    from player_rows
    group by league_code, season
    having safe_divide(countif(is_corrected), count(*)) > {{ limit }}
),

named_case as (
    select
        'named_case_not_measured' as failure,
        'CNL' as league_code,
        2025 as season,
        cast(null as int64) as corrected_rows,
        cast(null as int64) as player_rows,
        cast(null as float64) as corrected_share
    from (select 1)
    where not exists (
        select 1
        from player_rows as r
        where r.fixture_id = 1639932
    )
)

select * from over_limit
union all
select * from named_case
