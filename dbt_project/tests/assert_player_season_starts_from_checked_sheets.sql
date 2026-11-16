{#
  Hand-worked starts and substitute appearances of a real player-season whose stat lines file him
  as a starter in matches his team sheet has him on the bench. D. Ings (player 18955), Southampton,
  Premier League 2019: the raw sheets of Southampton's 38 league matches list him in the starting
  eleven 32 times and among the substitutes 6 times, and he has minutes in all 38; the stat lines
  make 36 of them starts. Both season grains must return 32 starts and 6 substitute appearances.
#}
{{ config(store_failures = true, severity = 'error') }}

with expected as (
    select
        'PL' as league_code,
        2019 as season_api_year,
        18955 as player_sk,
        32 as starts,
        6 as substitute_appearances,
        38 as appearances
),

actual as (
    select
        'competition_season' as grain,
        league_code,
        season_api_year,
        player_sk,
        starts,
        substitute_appearances,
        appearances
    from {{ ref('int_player_season__metrics') }}
    union all
    select
        'club_season' as grain,
        league_code,
        season_api_year,
        player_sk,
        starts,
        substitute_appearances,
        appearances
    from {{ ref('int_player_club_season__metrics') }}
),

grains as (
    select grain from unnest(['competition_season', 'club_season']) as grain
)

select
    g.grain,
    e.league_code,
    e.season_api_year,
    e.player_sk,
    e.starts as expected_starts,
    a.starts as actual_starts,
    e.substitute_appearances as expected_substitute_appearances,
    a.substitute_appearances as actual_substitute_appearances,
    e.appearances as expected_appearances,
    a.appearances as actual_appearances
from expected as e
cross join grains as g
left join actual as a
    on
        g.grain = a.grain
        and e.league_code = a.league_code
        and e.season_api_year = a.season_api_year
        and e.player_sk = a.player_sk
where
    a.player_sk is null
    or a.starts is distinct from e.starts
    or a.substitute_appearances is distinct from e.substitute_appearances
    or a.appearances is distinct from e.appearances
