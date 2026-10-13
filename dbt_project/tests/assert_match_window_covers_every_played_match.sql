-- Every played match is a window of one for each of its sides on mart_team_window_metrics: one
-- match row per side, holding that match alone. A side with a team match row that has no match
-- window, a side served twice, or a match window of any other size fails here.
--
-- Returns a row (= fails) per side missing from either side of the comparison, per side served
-- more than once, and per match window whose games_in_window is not 1.
{{ config(store_failures = true) }}

with played_sides as (
    select
        fixture_sk,
        team_sk
    from {{ ref('int_legs__team_match') }}
),

match_windows as (
    select
        fixture_sk,
        team_sk,
        count(*) as n_served,
        max(games_in_window) as games_in_window
    from {{ ref('mart_team_window_metrics') }}
    where window_type = 'match'
    group by fixture_sk, team_sk
)

select
    coalesce(p.fixture_sk, m.fixture_sk) as fixture_sk,
    coalesce(p.team_sk, m.team_sk) as team_sk,
    p.fixture_sk is not null as is_played_side,
    coalesce(m.n_served, 0) as n_served,
    m.games_in_window
from played_sides as p
full outer join match_windows as m
    on
        p.fixture_sk = m.fixture_sk
        and p.team_sk = m.team_sk
where
    p.fixture_sk is null
    or m.fixture_sk is null
    or m.n_served > 1
    or m.games_in_window != 1
