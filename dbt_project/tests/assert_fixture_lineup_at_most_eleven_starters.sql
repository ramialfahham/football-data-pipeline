-- A team starts a match with at most eleven players. Returns a row (= fails) per confirmed or
-- researched team line-up that names more than eleven starters; a provider sheet that does is
-- not_available and never shown.
{{ config(store_failures = true) }}

select
    fixture_sk,
    team_sk,
    countif(is_starter) as n_starters
from {{ ref('fct_fixture_lineup') }}
where lineup_state in ('confirmed', 'researched')
group by fixture_sk, team_sk
having countif(is_starter) > 11
