{#
  A player's birth date makes him between 15 and 45 years old in every match he played. Each row
  is a player whose birth date puts him outside that range in his first or last match; most are
  provider placeholders such as 1970-01-01, to research. Named case: Lionel Messi (154), born
  1987-06-24, is never listed.
#}
{{ config(store_failures = true, severity = 'warn') }}

with appearances as (
    select
        player_sk,
        fixture_sk
    from {{ ref('fct_fixture_lineup') }}
    union distinct
    select
        player_sk,
        fixture_sk
    from {{ ref('fct_fixture_player_stats') }}
),

played as (
    select
        a.player_sk,
        min(date(f.fixture_date)) as first_match,
        max(date(f.fixture_date)) as last_match
    from appearances as a
    inner join {{ ref('fct_fixture') }} as f
        on a.fixture_sk = f.fixture_sk
    group by a.player_sk
),

compared as (
    select
        p.player_api_id,
        p.player_name,
        p.player_birth_date,
        x.first_match,
        x.last_match,
        date_diff(x.first_match, p.player_birth_date, year) < 15
        or date_diff(x.last_match, p.player_birth_date, year) > 45 as is_implausible
    from played as x
    inner join {{ ref('dim_player') }} as p
        on x.player_sk = p.player_sk
    where p.player_birth_date is not null
),

named_case as (
    select 154 as player_api_id
)

select
    player_api_id,
    player_name,
    player_birth_date,
    first_match,
    last_match,
    'birth date makes the player younger than 15 or older than 45 in a match' as failure
from compared
where is_implausible

union all

select
    n.player_api_id,
    c.player_name,
    c.player_birth_date,
    c.first_match,
    c.last_match,
    'named case: Messi has no plausible birth date' as failure
from named_case as n
left join compared as c
    on n.player_api_id = c.player_api_id
where c.is_implausible is distinct from false
