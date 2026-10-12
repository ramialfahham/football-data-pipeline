-- mart_player_fixture_stats serves every stat line of a finished match exactly once, flagged
-- has_stat_line, and flags no row that has none. A join to the line-ups that drops, doubles or
-- moves a stat line fails here.
--
-- Returns a row (= fails) per stat line missing from the mart, per flagged row with no stat line,
-- and per stat line served more than once.
{{ config(store_failures = true) }}

with expected as (
    select
        s.fixture_sk,
        s.team_sk,
        s.player_sk
    from {{ ref('fct_fixture_player_stats') }} as s
    inner join {{ ref('fct_fixture') }} as f
        on s.fixture_sk = f.fixture_sk
    where f.status_short in ('FT', 'AET', 'PEN')
),

served as (
    select
        fixture_sk,
        team_sk,
        player_sk,
        count(*) as n_served
    from {{ ref('mart_player_fixture_stats') }}
    where has_stat_line
    group by fixture_sk, team_sk, player_sk
)

select
    coalesce(e.fixture_sk, s.fixture_sk) as fixture_sk,
    coalesce(e.team_sk, s.team_sk) as team_sk,
    coalesce(e.player_sk, s.player_sk) as player_sk,
    e.fixture_sk is not null as in_stat_lines,
    coalesce(s.n_served, 0) as n_served
from expected as e
full outer join served as s
    on
        e.fixture_sk = s.fixture_sk
        and e.team_sk = s.team_sk
        and e.player_sk = s.player_sk
where
    e.fixture_sk is null
    or s.fixture_sk is null
    or s.n_served > 1
