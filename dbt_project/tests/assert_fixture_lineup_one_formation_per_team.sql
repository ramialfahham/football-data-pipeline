-- A team takes the field in one formation per match. Returns a row (= fails) per team line-up
-- whose players carry more than one formation.
{{ config(store_failures = true) }}

select
    fixture_sk,
    team_sk,
    count(distinct team_formation) as n_formations
from {{ ref('fct_fixture_lineup') }}
group by fixture_sk, team_sk
having count(distinct team_formation) > 1
