{#
  A competition-season whose share of corrected or blanked player rows passes its limit
  (stats_need_research in int_competition_season__player_stat_corrections) is withheld from every
  player and team board: mart_leaderboards, mart_player_competition_benchmarks,
  mart_team_competition_benchmarks, and each squad of mart_player_squad_benchmarks whose window
  holds it. The share is measured on the matches whose player stats are final
  (base_apif__fixture_fetches, docs/data_contract.md "Second fetch").
  Returns each board row of a withheld competition-season, and the named case: Aruba-Antigua and
  Barbuda (fixture 1639932, 23 Sep 2026, fetched again on 6 Oct) is measured.
#}
{{ config(store_failures = true, severity = 'error') }}

with withheld as (
    select season_sk
    from {{ ref('int_competition_season__player_stat_corrections') }}
    where stats_need_research
),

withheld_squads as (
    select distinct squad_sk
    from {{ ref('int_player_squad_window__metrics') }}
    where stats_need_research
)

select
    'withheld_on_leaderboard' as failure,
    cast(b.season_sk as string) as subject
from {{ ref('mart_leaderboards') }} as b
inner join withheld as w
    on b.season_sk = w.season_sk

union all

select
    'withheld_on_player_benchmark' as failure,
    cast(b.season_sk as string) as subject
from {{ ref('mart_player_competition_benchmarks') }} as b
inner join withheld as w
    on b.season_sk = w.season_sk

union all

select
    'withheld_on_team_benchmark' as failure,
    cast(b.season_sk as string) as subject
from {{ ref('mart_team_competition_benchmarks') }} as b
inner join withheld as w
    on b.season_sk = w.season_sk

union all

select
    'withheld_on_squad_benchmark' as failure,
    b.squad_sk as subject
from {{ ref('mart_player_squad_benchmarks') }} as b
inner join withheld_squads as w
    on b.squad_sk = w.squad_sk

union all

select
    'named_case_not_measured' as failure,
    '1639932' as subject
from (select 1)
where not exists (
    select 1
    from {{ ref('base_apif__fixture_players') }} as p
    inner join {{ ref('base_apif__fixture_fetches') }} as f
        on p.fixture_id = f.fixture_id
    where p.fixture_id = 1639932 and not f.is_awaiting_second_fetch
)
