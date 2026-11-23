{#
  Hand-written answer key for the macro team_seasons_off_standings. Every team-season below has
  10 games, 5 wins, 3 draws, 2 losses, 16 goals, 9 goals against and 18 points, and the standings
  row that counts the same games agrees unless the case says otherwise. Each case names what the
  macro must return; a case missing from the expected list must return nothing.

   1 agrees                                               -> nothing
   2 wins, 3 draws, 4 losses, 5 goals, 6 goals against, 7 points each differ -> counts_differ
   8 table points 15 and 3 points taken by the league     -> nothing (adjusted points agree)
   9 same, ours 19                                        -> counts_differ
  10 table points 15, the adjustment is another team's    -> counts_differ
  11 adjustment group name padded with a space            -> nothing (names are trimmed)
  12 two adjustments of 3 add to 6 on table points 12     -> nothing
  13 the table counts 8 games, ours 10 (an older snapshot) -> nothing (ahead is normal, not compared)
  14 the table counts 11 games, ours 10                   -> games_short
  15 a group row that agrees and a play-off row of 4 games -> nothing
  16 rows of 8 and 12 games                               -> games_short (the largest counts)
  17 two rows of 10 games, one agrees, one has 6 wins     -> counts_differ
  18 our goals blank, the table has 16                    -> counts_differ
  19 no standings row                                     -> nothing
  20 a row of 10 games with 6 wins and a row of 11 games  -> counts_differ and games_short
  21 the standings row is of another season               -> nothing
  22 a table row that differs in a count but counts other games than ours -> nothing
  23 two adjustments of 3 whose group names differ by a space, table points 12 -> nothing
  Returns every case where the macro's rows differ from the expected rows.
#}
{{ config(store_failures = true, severity = 'error') }}

with counts as (
    select * from unnest([
        struct(1 as team_sk, 'S1' as season_sk, 10 as season_games_played, 5 as wins, 3 as draws, 2 as losses, 16 as goals, 9 as goals_against, 18 as points_won),
        (2, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (3, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (4, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (5, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (6, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (7, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (8, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (9, 'S1', 10, 5, 3, 2, 16, 9, 19),
        (10, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (11, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (12, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (13, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (14, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (15, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (16, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (17, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (18, 'S1', 10, 5, 3, 2, cast(null as int64), 9, 18),
        (19, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (20, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (21, 'S2', 10, 5, 3, 2, 16, 9, 18),
        (22, 'S1', 10, 5, 3, 2, 16, 9, 18),
        (23, 'S1', 10, 5, 3, 2, 16, 9, 18)
    ])
),

standings as (
    select * from unnest([
        struct(1 as team_sk, 'S1' as season_sk, 'XX' as league_code, 2025 as season_api_year, 1 as team_api_id, 'Main' as group_name, 10 as played, 5 as wins, 3 as draws, 2 as losses, 16 as goals_scored, 9 as goals_conceded, 18 as points),
        (2, 'S1', 'XX', 2025, 2, 'Main', 10, 6, 3, 2, 16, 9, 18),
        (3, 'S1', 'XX', 2025, 3, 'Main', 10, 5, 4, 2, 16, 9, 18),
        (4, 'S1', 'XX', 2025, 4, 'Main', 10, 5, 3, 3, 16, 9, 18),
        (5, 'S1', 'XX', 2025, 5, 'Main', 10, 5, 3, 2, 17, 9, 18),
        (6, 'S1', 'XX', 2025, 6, 'Main', 10, 5, 3, 2, 16, 10, 18),
        (7, 'S1', 'XX', 2025, 7, 'Main', 10, 5, 3, 2, 16, 9, 19),
        (8, 'S1', 'XX', 2025, 8, 'Main', 10, 5, 3, 2, 16, 9, 15),
        (9, 'S1', 'XX', 2025, 9, 'Main', 10, 5, 3, 2, 16, 9, 15),
        (10, 'S1', 'XX', 2025, 10, 'Main', 10, 5, 3, 2, 16, 9, 15),
        (11, 'S1', 'XX', 2025, 11, 'Main', 10, 5, 3, 2, 16, 9, 15),
        (12, 'S1', 'XX', 2025, 12, 'Main', 10, 5, 3, 2, 16, 9, 12),
        (13, 'S1', 'XX', 2025, 13, 'Main', 8, 4, 2, 2, 12, 8, 14),
        (14, 'S1', 'XX', 2025, 14, 'Main', 11, 1, 1, 1, 1, 1, 1),
        (15, 'S1', 'XX', 2025, 15, 'Main', 10, 5, 3, 2, 16, 9, 18),
        (15, 'S1', 'XX', 2025, 15, 'Play-off', 4, 1, 1, 2, 3, 4, 4),
        (16, 'S1', 'XX', 2025, 16, 'Main', 8, 4, 2, 2, 12, 8, 14),
        (16, 'S1', 'XX', 2025, 16, 'Play-off', 12, 6, 3, 3, 20, 10, 21),
        (17, 'S1', 'XX', 2025, 17, 'Main', 10, 5, 3, 2, 16, 9, 18),
        (17, 'S1', 'XX', 2025, 17, 'Play-off', 10, 6, 3, 2, 16, 9, 18),
        (18, 'S1', 'XX', 2025, 18, 'Main', 10, 5, 3, 2, 16, 9, 18),
        (20, 'S1', 'XX', 2025, 20, 'Main', 10, 6, 3, 2, 16, 9, 18),
        (20, 'S1', 'XX', 2025, 20, 'Play-off', 11, 1, 1, 1, 1, 1, 1),
        (21, 'S1', 'XX', 2025, 21, 'Main', 99, 9, 9, 9, 9, 9, 9),
        (22, 'S1', 'XX', 2025, 22, 'Main', 7, 1, 1, 1, 1, 1, 1),
        (23, 'S1', 'XX', 2025, 23, 'Main', 10, 5, 3, 2, 16, 9, 12)
    ])
),

adjustments as (
    select * from unnest([
        struct('XX' as league_code, 2025 as season, 8 as team_id, 'Main' as group_name, 3 as points_taken),
        ('XX', 2025, 9, 'Main', 3),
        ('XX', 2025, 99, 'Main', 3),
        ('XX', 2025, 11, 'Main ', 3),
        ('XX', 2025, 12, 'Main', 3),
        ('XX', 2025, 12, 'Main', 3),
        ('XX', 2025, 23, 'Main', 3),
        ('XX', 2025, 23, 'Main ', 3)
    ])
),

expected as (
    select * from unnest([
        struct(2 as team_sk, 'S1' as season_sk, 'counts_differ' as reason),
        (3, 'S1', 'counts_differ'),
        (4, 'S1', 'counts_differ'),
        (5, 'S1', 'counts_differ'),
        (6, 'S1', 'counts_differ'),
        (7, 'S1', 'counts_differ'),
        (9, 'S1', 'counts_differ'),
        (10, 'S1', 'counts_differ'),
        (14, 'S1', 'games_short'),
        (16, 'S1', 'games_short'),
        (17, 'S1', 'counts_differ'),
        (18, 'S1', 'counts_differ'),
        (20, 'S1', 'counts_differ'),
        (20, 'S1', 'games_short')
    ])
),

found as (
    {{ team_seasons_off_standings('counts', 'standings', 'adjustments') }}
)

select
    coalesce(f.team_sk, e.team_sk) as team_sk,
    coalesce(f.season_sk, e.season_sk) as season_sk,
    coalesce(f.reason, e.reason) as reason,
    f.team_sk is not null as returned,
    e.team_sk is not null as expected
from found as f
full outer join expected as e
    on f.team_sk = e.team_sk and f.season_sk = e.season_sk and f.reason = e.reason
where f.team_sk is null or e.team_sk is null
