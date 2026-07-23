{{ config(materialized='table') }}

{#
  Player Career log (content_architecture §4; #480 §8.3). One row per (player, CLUB, competition-season):
  the player's appearances / goals / assists at that club that competition-season + player identity
  (dim_player) + club identity (dim_team) + the competition's entity_type (club / national, via the
  registry -> competition_types seeds). This is the Transfermarkt-shaped career table — a mid-season
  transfer shows as two rows (two clubs, one season). Club and national rows are handled uniformly:
  a "national" row is a season in a competition whose entity_type is national.

  National-entity rows are the player's NATIONAL APPEARANCES IN COVERED COMPETITIONS — honestly NOT true
  career caps: we ingest only a subset of national competitions. national_appearances_total denormalises
  the per-player national-appearance sum so the export reads it directly (a fact computed in dbt, never in
  the consumption layer).

  Grain: (player_sk, team_sk, season_sk). Composes int_player_club_season__metrics (the single per-club
  atoms base) — no re-aggregation here, just identity + typing joins. Rows come from finished-match
  player-stat rows via the base, so a row means "this player was in this club's matchday squad at
  least once that competition-season". `appearances` counts only the legs he actually PLAYED
  (minutes > 0), so it can legitimately be 0: a squad member who never got on the pitch keeps his row
  (CPO 2026-07-23 — "Players are part of the squad even with zero appearances") and simply scores 0.
  Until 2026-07-23 `appearances` counted every matchday selection, which inflated 51.4% of rows.
  Per-club / per-competition / national subtotals are derivable from this grain (display-side), so
  they are not precomputed.
#}

with club_season as (
    select * from {{ ref('int_player_club_season__metrics') }}
),

players as (
    select
        player_sk,
        player_name,
        player_nationality,
        player_photo_url
    from {{ ref('dim_player') }}
),

teams as (
    select
        team_sk,
        team_name,
        team_logo_url,
        team_country
    from {{ ref('dim_team') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

types as (
    select
        competition_type,
        entity_type
    from {{ ref('competition_types') }}
),

typed as (
    select
        cs.player_sk,
        cs.team_sk,
        cs.league_sk,
        cs.league_code,
        cs.season_sk,
        cs.season_api_year,
        cs.appearances,
        cs.minutes,
        cs.goals,
        cs.assists,
        cs.last_kickoff_at,
        types.entity_type
    from club_season as cs
    left join registry on cs.league_code = registry.league_code
    left join types on registry.competition_type = types.competition_type
),

with_caps as (
    select
        typed.player_sk,
        typed.team_sk,
        typed.league_sk,
        typed.league_code,
        typed.season_sk,
        typed.season_api_year,
        typed.entity_type,
        typed.appearances,
        typed.minutes,
        typed.goals,
        typed.assists,
        typed.last_kickoff_at,
        -- the CLUB's latest match across all the player's seasons at that club (season-collapsed recency).
        -- The export sorts the career log by this so a club's rows stay contiguous and clubs sort
        -- most-recent-first — the ordering SIGNAL lives here (mart), the export only selects+sorts by it
        -- (never aggregates client-side). Handles a mid-season transfer and a return spell correctly.
        max(typed.last_kickoff_at)
            over (partition by typed.player_sk, typed.team_sk) as club_latest_kickoff_at,
        -- per-player national-appearance total (covered comps only — honestly not true caps),
        -- denormalised so the export reads it directly (never derived in the consumption layer).
        sum(case when typed.entity_type = 'national' then typed.appearances else 0 end)
            over (partition by typed.player_sk) as national_appearances_total
    from typed
)

select
    {{ dbt_utils.generate_surrogate_key(['wc.player_sk', 'wc.team_sk', 'wc.season_sk']) }}
        as player_career_sk,
    wc.player_sk,
    wc.team_sk,
    wc.league_sk,
    wc.league_code,
    wc.season_sk,
    wc.season_api_year,
    p.player_name,
    p.player_nationality,
    p.player_photo_url,
    tm.team_name,
    tm.team_logo_url,
    tm.team_country,
    wc.entity_type,
    wc.appearances,
    -- raw seasonal minutes sum at this club (carried up unchanged from int_player_club_season__metrics,
    -- same class as appearances/goals/assists — a playing-time dimension, not a catalogue metric).
    -- A minutes_per_appearance ratio is deliberately NOT computed here: it is a catalogue-governed
    -- rate (analytics-engineer ruling 2026-07-23), so it lands with its metric_catalogue row in the
    -- PR that consumes it, now that `appearances` is a real appearance count to divide by.
    wc.minutes,
    wc.goals,
    wc.assists,
    wc.national_appearances_total,
    -- ordering SIGNALS for the export's career log (sort keys, not displayed metrics): last_kickoff_at =
    -- this club-season's latest match (within-club season order); club_latest_kickoff_at = the club's latest
    -- match across all the player's seasons there (club-block order + contiguity). season_api_year alone can't
    -- disambiguate two clubs in one season (mid-season transfer) or keep a return spell's rows contiguous.
    wc.last_kickoff_at,
    wc.club_latest_kickoff_at
from with_caps as wc
left join players as p on wc.player_sk = p.player_sk
left join teams as tm on wc.team_sk = tm.team_sk
