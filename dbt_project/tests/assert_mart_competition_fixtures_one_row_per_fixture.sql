-- mart_competition_fixtures is fct_fixture, whole: every fixture of every competition-season is
-- in it exactly once and nothing else is. A filter on status, a season cap or a join that drops a
-- fixture with an unknown team fails here even when the mart's unique test stays green.
--
-- Returns a row (= fails) per fixture missing from the mart, present in the mart but not in
-- fct_fixture, or served more than once.
{{ config(store_failures = true) }}

with expected as (
    select fixture_sk
    from {{ ref('fct_fixture') }}
),

served as (
    select
        fixture_sk,
        count(*) as n_served
    from {{ ref('mart_competition_fixtures') }}
    group by fixture_sk
)

select
    coalesce(e.fixture_sk, s.fixture_sk) as fixture_sk,
    e.fixture_sk is not null as in_fct_fixture,
    coalesce(s.n_served, 0) as n_served
from expected as e
full outer join served as s
    on e.fixture_sk = s.fixture_sk
where
    e.fixture_sk is null
    or s.fixture_sk is null
    or s.n_served != 1
