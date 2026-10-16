-- A team sheet is numbered 1 to n with every starter before every substitute. Returns a row
-- (= fails) per team sheet whose lineup_order skips, repeats or lists a substitute first.
{{ config(store_failures = true) }}

select
    fixture_sk,
    team_sk,
    count(*) as n_players,
    min(lineup_order) as first_order,
    max(lineup_order) as last_order,
    max(if(is_starter, lineup_order, null)) as last_starter,
    min(if(not is_starter, lineup_order, null)) as first_substitute
from {{ ref('fct_fixture_lineup') }}
group by fixture_sk, team_sk
having
    min(lineup_order) != 1
    or max(lineup_order) != count(*)
    or count(distinct lineup_order) != count(*)
    or max(if(is_starter, lineup_order, null)) > min(if(not is_starter, lineup_order, null))
