{{
    config(
        severity = 'warn',
        tags=["dq", "core", "season_reconciliation"]
    )
}}

-- Our own count of a team's played matches must never be LOWER than the number the competition's
-- own standings say it played. When it is, we are missing a match that a governing body records as
-- played — and that is true whatever caused it: a fixture stuck at SUSP or INT, one mislabelled
-- CANC, one awarded and filed under a status nothing reads, or one the provider never published.
--
-- ⭐ THE POINT IS THAT IT ENUMERATES NOTHING. A status list can only catch the causes somebody
-- thought to list, and the status field is the least reliable thing the provider sends. The
-- standings' played count is produced independently of it, so this catches the SYMPTOM instead of
-- guessing at causes. It is the detector an Eredivisie incident actually needed: FC
-- Utrecht was a game short of its league, and no test asked that question.
--
-- ⛔ ONE DIRECTION ONLY, AND THE ASYMMETRY IS MEASURED, NOT ASSUMED. Over 4,082 team-seasons:
-- 2,515 agree, 1,564 have OUR count HIGHER by 1 to 30 games, and 3 have ours LOWER. The "higher"
-- population is not a defect — standings are a snapshot taken when they were last ingested, and we
-- keep counting fixtures afterwards, so being ahead of them is the normal state mid-season. A
-- two-sided test would be red on 38% of all rows and would be deleted within a week. Only
-- `ours < standings` means something is missing.
--
-- ⚠ SEVERITY IS WARN, DELIBERATELY AND FOR NOW, because this test is
-- RED ON REAL DATA TODAY — 3 rows, at least two of them confirmed genuine. Their fix is GitLab
-- #110's open rule on awarded results filed under the wrong status. Error severity would stop the
-- whole warehouse over defects we have deliberately not decided how to correct yet.
--
-- ⛔ IT REPLACES assert_mart_team_season_insights_games_match_played, WHICH COULD NOT FAIL.
-- That test compared mart_team_season_insights.season_games_played against .played — but
-- mart_team_season.sql:34 defines `played` as `m.season_games_played as played`, an alias of our own
-- count. Both operands resolved to the same row through team_season_sk, so it returned zero on any
-- data by construction. It was deleted rather than kept: a test that cannot fail is not a guard, it
-- is false assurance appearing in every green run.
--
-- Joins fct_standings directly because the genuine count never reaches the marts —
-- int_team_season__standings_primary reads fct_standings and projects only standing_rank, form and
-- group_description.
--
-- ⚠ MAX(played), NOT THE LATEST-INGESTED ROW, AND THAT IS NOT A STYLE CHOICE.
-- fct_standings is grained on (league_code, season, team_id, group_name), so one team-season can
-- carry several standings rows — a group table and a play-off or relegation table, say. Measured:
-- 299 team-seasons have more than one row and **204 of those disagree on `played`, by up to 13
-- games**. Collapsing with `qualify row_number() ... order by raw_ingested_at` — the pattern
-- int_team_season__standings_primary uses for DISPLAY fields — picks arbitrarily among them, and
-- those rows frequently share a raw_ingested_at, so the tiebreak is not even stable. For a numeric
-- reconciliation that is unsound in both directions: it can invent a shortfall or hide one.
-- MAX is deterministic and errs toward silence: if any authoritative table says the team played N,
-- we should hold at least N. It returns the same 3 rows as the arbitrary pick today, so this changes
-- no current result — it makes the test correct by construction rather than by luck.
with standings_played as (
    select
        team_sk,
        season_sk,
        max(played) as played
    from {{ ref('fct_standings') }}
    group by team_sk, season_sk
)

select
    m.team_sk,
    m.season_sk,
    m.league_code,
    m.season_api_year,
    m.season_games_played,
    s.played as standings_played,
    s.played - m.season_games_played as games_missing
from {{ ref('int_team_season__metrics') }} as m
inner join standings_played as s
    on
        m.team_sk = s.team_sk
        and m.season_sk = s.season_sk
where
    s.played is not null
    and m.season_games_played < s.played
