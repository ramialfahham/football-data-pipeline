-- Every board of mart_team_leaderboards ranks in the direction it serves.
--
-- rank_order is a served fact the page reads ("fewest first" beside an asc board), so the rows
-- must actually be ordered that way: on an asc board the rank-1 row holds the board's smallest
-- value and on a desc board its largest, within every (league_code, season_api_year). A model
-- edit that negates the wrong side, or a catalogue direction that flips without the model
-- noticing, puts the worst team at the top of a board that says it shows the best; no schema
-- test sees that.
--
-- The second half pins the zero rule the same way: a desc board never ranks a 0 (a zero is not
-- a ranking on a most-first board), while an asc board may hold one, since 0 conceded is the
-- top row.
--
-- Returns a row (= fails) per league-board-season whose leader is not its extreme, and per
-- desc row at zero.
{{ config(store_failures = true) }}

with boards as (
    select
        league_code,
        season_api_year,
        metric_key,
        rank_order,
        min(sort_value) as least,
        max(sort_value) as most,
        min(case when rank = 1 then sort_value end) as leader_value
    from {{ ref('mart_team_leaderboards') }}
    group by league_code, season_api_year, metric_key, rank_order
),

wrong_way as (
    select
        league_code,
        season_api_year,
        metric_key,
        rank_order,
        leader_value,
        'leader is not the extreme' as defect
    from boards
    where
        (rank_order = 'asc' and leader_value != least)
        or (rank_order = 'desc' and leader_value != most)
),

zero_ranked as (
    select
        league_code,
        season_api_year,
        metric_key,
        rank_order,
        sort_value as leader_value,
        'zero ranked on a most-first board' as defect
    from {{ ref('mart_team_leaderboards') }}
    where rank_order = 'desc' and sort_value <= 0
)

select * from wrong_way
union all
select * from zero_ranked
