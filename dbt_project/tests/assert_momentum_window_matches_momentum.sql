-- The momentum-window list (mart_momentum_window__team) and the momentum aggregate
-- (mart_momentum__team) must describe the same matches: for every upcoming
-- fixture side, the number of rows in the list must equal games_in_window,
-- and neither surface may have a side the other lacks. Both consume
-- int_momentum_window__team, so a mismatch means a build-order or join bug.

with list_counts as (
    select
        upcoming_fixture_sk,
        team_sk,
        count(*) as games_in_list
    from {{ ref('mart_momentum_window__team') }}
    group by
        upcoming_fixture_sk,
        team_sk
),

momentum as (
    select
        upcoming_fixture_sk,
        team_sk,
        games_in_window
    from {{ ref('mart_momentum__team') }}
)

select
    m.games_in_window,
    l.games_in_list,
    coalesce(m.upcoming_fixture_sk, l.upcoming_fixture_sk) as upcoming_fixture_sk,
    coalesce(m.team_sk, l.team_sk) as team_sk
from momentum as m
full outer join list_counts as l
    on
        m.upcoming_fixture_sk = l.upcoming_fixture_sk
        and m.team_sk = l.team_sk
where coalesce(m.games_in_window, -1) != coalesce(l.games_in_list, -1)
