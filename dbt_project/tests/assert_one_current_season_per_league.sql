-- Exactly ONE season per competition may be flagged current.
--
-- `is_current_season` is a served pick: the Home block filters on it instead of choosing a season
-- itself. If two seasons were flagged for one league, that filter would return a league's leaders
-- twice and the block's "one player per league" rule would break silently — the rows would still
-- look plausible, just doubled.
--
-- Counts DISTINCT seasons, not rows: the flag is per league-season and every row of that season
-- carries it, so a row count would be the leaderboard's size and always > 1.
--
-- A league with no flagged season is caught too (count 0 <> 1). That is reachable only if the
-- window function stops matching any row, which would mean the column had silently become false
-- everywhere — the failure mode a `> 1` check alone would pass.

-- ⚠ IT ASSERTS RECENCY AS WELL AS CARDINALITY, and the second half was added because mutation
-- testing proved the first half alone was too weak: flipping the window's ORDER BY to ascending
-- flags the OLDEST season instead of the newest, still exactly one per league, and a
-- cardinality-only check stayed GREEN. The block would then have shown last season's leaders under
-- a heading that says "season totals to date" — wrong, and invisible to every other guard.

-- ⛔ AND IT ASSERTS ROW COMPLETENESS, which is the property the whole `rank()` choice rests on and
-- which the first two halves CANNOT see. Revert the model's `rank()` to `row_number()` and exactly
-- ONE row per league carries the flag: the distinct-season count is still 1, that row's season is
-- still the max, and a cardinality-plus-recency test stays GREEN while the flag is false on every
-- other row of the season. The obvious mutations (ascending order, two seasons flagged) both miss
-- that gap because neither changes the season SET.
-- A flagged season must therefore be flagged ENTIRELY.

{{ config(store_failures = true) }}

with import_mart_leaderboards as (
    select * from {{ ref('mart_leaderboards') }}
    where window_type = 'season_to_date'
),

per_season as (
    select
        league_code,
        season_api_year,
        countif(is_current_season) as flagged_rows,
        count(*) as season_rows
    from import_mart_leaderboards
    group by league_code, season_api_year
),

per_league as (
    select
        league_code,
        max(season_api_year) as latest_season,
        countif(flagged_rows > 0) as flagged_seasons,
        max(case when flagged_rows > 0 then season_api_year end) as flagged_season,
        countif(flagged_rows > 0 and flagged_rows <> season_rows) as partly_flagged_seasons
    from per_season
    group by league_code
),

matches_with_player_stats as (
    select fixture_sk
    from {{ ref('fct_fixture_player_stats') }}
    where coalesce(minutes, 0) > 0
    group by fixture_sk
),

seasons_missing_player_stats as (
    select f.season_sk
    from {{ ref('fct_fixture') }} as f
    left join matches_with_player_stats as s
        on f.fixture_sk = s.fixture_sk
    where f.status_short in ('FT', 'AET', 'PEN') and s.fixture_sk is null
    group by f.season_sk
),

withheld_seasons as (
    select
        c.league_code,
        c.season_api_year
    from {{ ref('int_competition_season__player_stat_corrections') }} as c
    where c.stats_need_research
    union distinct
    select
        d.league_code,
        d.season_api_year
    from seasons_missing_player_stats as m
    inner join {{ ref('dim_competition_season') }} as d
        on m.season_sk = d.season_sk
),

-- A league whose latest season is withheld (stats_need_research, or a finished match without
-- player statistics) keeps no current season: the flag never moves to the season before it.
withheld_latest as (
    select distinct p.league_code
    from per_league as p
    inner join withheld_seasons as w
        on p.league_code = w.league_code
    where w.season_api_year > p.latest_season
)

select
    p.league_code,
    p.latest_season,
    p.flagged_season,
    p.flagged_seasons,
    p.partly_flagged_seasons
from per_league as p
left join withheld_latest as h
    on p.league_code = h.league_code
where
    (h.league_code is not null and p.flagged_seasons > 0)
    or (
        h.league_code is null
        and (
            p.flagged_seasons <> 1
            or p.flagged_season <> p.latest_season
            or p.partly_flagged_seasons > 0
        )
    )
