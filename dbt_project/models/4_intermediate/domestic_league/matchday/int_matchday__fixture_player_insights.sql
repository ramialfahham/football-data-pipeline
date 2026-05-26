{{ config(materialized='table') }}

{#
  Per (upcoming fixture_sk, team_sk, player_sk) atom aggregates for the player insights surface.
  Grain: (fixture_sk, team_sk, player_sk).

  Form-window dispatch (per docs/player_metrics_catalogue.md + issue #154 2026-05-21 update):

  DOMESTIC (non-WC upcoming fixture):
    - No finished match in current season for this team/league → full previous season.
    - At least one finished match in current season → last 5 in current season.

  WC UPCOMING FIXTURE:
    - Group Stage round 1 (upcoming_round_order == 1 AND round_name contains 'group'):
      → WC pre-tournament: player's full current/most-recent domestic season
        (int_player_season__metrics). Uses dim_player.last_known_team_api_id → dim_team
        to resolve domestic league. If domestic league not ingested → form_source_unavailable.
    - Group Stage round 2+ and knockout rounds:
      → WC tournament: all finished WC tournament legs before this fixture (no cap).

  Squad enumeration:
    - Domestic: all players who appeared for team_sk in league_code in current or previous season.
    - WC pre-tournament: players who appeared for national team_sk in any WCQ match
      (same supporting leagues as team form; wc_supporting_league_codes seed).
    - WC tournament: players who appeared for team_sk in finished WC tournament legs.

  Rates are null when denominator zero. Optional API stats gaps stay null (not coerced to 0).
  Atoms follow docs/player_metrics_catalogue.md exactly.
#}

with import_fct_fixture_player_stats as (
    select * from {{ ref('fct_fixture_player_stats') }}
),

import_fct_fixture as (
    select * from {{ ref('fct_fixture') }}
),

import_int_matchday__upcoming_round_fixtures as (
    select * from {{ ref('int_matchday__upcoming_round_fixtures') }}
),

import_int_matchday__finished_fixture_team_leg as (
    select * from {{ ref('int_matchday__finished_fixture_team_leg') }}
),

import_int_player_season__metrics as (
    select * from {{ ref('int_player_season__metrics') }}
),

import_dim_player as (
    select * from {{ ref('dim_player') }}
),

import_dim_team as (
    select * from {{ ref('dim_team') }}
),

import_wc_supporting_leagues as (
    select * from {{ ref('wc_supporting_league_codes') }}
    where parent_league_code = 'WC'
),

-- ─── Upcoming fixture context ──────────────────────────────────────────────

upcoming_fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        upcoming_round_order,
        home_team_sk,
        away_team_sk
    from import_int_matchday__upcoming_round_fixtures
),

upcoming_both_sides as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        upcoming_round_order,
        home_team_sk as team_sk
    from upcoming_fixtures
    union all
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        upcoming_round_order,
        away_team_sk as team_sk
    from upcoming_fixtures
),

-- ─── WC phase detection ───────────────────────────────────────────────────
-- WC pre-tournament = Group Stage round 1 (round_order=1 AND name contains 'group').
-- Everything else is tournament form.

wc_upcoming as (
    select
        fixture_sk,
        season_api_year,
        kickoff_datetime,
        round_name,
        upcoming_round_order,
        team_sk,
        -- True = pre-tournament (GS-MD1); False = tournament from GS-MD2+
        (
            coalesce(upcoming_round_order, -1) = 1
            and regexp_contains(lower(coalesce(round_name, '')), r'group')
        ) as is_wc_pre_tournament
    from upcoming_both_sides
    where league_code = 'WC'
),

-- ─── Player domestic league resolution (for WC pre-tournament) ───────────
-- dim_player.last_known_team_api_id → dim_team.league_code (must be non-WCQ domestic league).
-- WCQ and WC league codes are excluded; those are national-team competitions, not domestic clubs.

player_domestic_league as (
    select
        dp.player_sk,
        dp.last_known_team_api_id,
        dt.league_code as domestic_league_code,
        dt.team_sk as club_team_sk
    from import_dim_player as dp
    left join import_dim_team as dt
        on dp.last_known_team_api_id = dt.team_api_id
    where
        dt.league_code is not null
        and dt.league_code not in ('WC', 'WCQEU', 'WCQAF', 'WCQCA', 'WCQSA', 'WCQAS', 'WCQIP', 'WCQOC')
),

-- ─── Squad enumeration ────────────────────────────────────────────────────
-- Domestic: players who appeared for team_sk in league_code in current or prev season.

domestic_squad as (
    select distinct
        uf.fixture_sk as upcoming_fixture_sk,
        uf.team_sk,
        fps.player_sk,
        uf.league_code,
        uf.season_api_year,
        uf.kickoff_datetime as upcoming_kickoff_datetime
    from upcoming_both_sides as uf
    inner join import_fct_fixture as f
        on
            f.league_code = uf.league_code
            and f.season_api_year in (uf.season_api_year, uf.season_api_year - 1)
            and f.status_short in ('FT', 'AET', 'PEN')
    inner join import_fct_fixture_player_stats as fps
        on
            fps.fixture_sk = f.fixture_sk
            and fps.team_sk = uf.team_sk
    where uf.league_code != 'WC'
),

-- WC pre-tournament: players who appeared for national team in any supporting WCQ match.
wc_pre_tournament_squad as (
    select distinct
        wu.fixture_sk as upcoming_fixture_sk,
        wu.team_sk,
        fps.player_sk,
        pdl.domestic_league_code,
        wu.kickoff_datetime as upcoming_kickoff_datetime,
        wu.season_api_year
    from wc_upcoming as wu
    inner join import_wc_supporting_leagues as sl on true
    inner join import_fct_fixture as f
        on
            f.league_code = sl.supporting_league_code
            and f.status_short in ('FT', 'AET', 'PEN')
    inner join import_fct_fixture_player_stats as fps
        on
            fps.fixture_sk = f.fixture_sk
            and fps.team_sk = wu.team_sk
    left join player_domestic_league as pdl
        on fps.player_sk = pdl.player_sk
    where wu.is_wc_pre_tournament
),

-- WC tournament (GS-MD2+): players who appeared in finished WC tournament legs for that team.
wc_tournament_squad as (
    select distinct
        wu.fixture_sk as upcoming_fixture_sk,
        wu.team_sk,
        fps.player_sk,
        wu.kickoff_datetime as upcoming_kickoff_datetime,
        wu.season_api_year
    from wc_upcoming as wu
    inner join import_fct_fixture as f
        on
            f.league_code = 'WC'
            and f.season_api_year = wu.season_api_year
            and f.status_short in ('FT', 'AET', 'PEN')
            and f.kickoff_datetime < wu.kickoff_datetime
    inner join import_fct_fixture_player_stats as fps
        on
            fps.fixture_sk = f.fixture_sk
            and fps.team_sk = wu.team_sk
    where not wu.is_wc_pre_tournament
),

-- ─── Domestic form window ─────────────────────────────────────────────────
-- Mirror of int_matchday__team_form_metrics at player grain.
-- Detect if current season has started → last 5 / full prev season.

domestic_current_counts as (
    select
        ds.upcoming_fixture_sk,
        ds.team_sk,
        ds.player_sk,
        count(*) as n_current_legs_before
    from domestic_squad as ds
    inner join import_fct_fixture as f
        on
            f.league_code = ds.league_code
            and f.season_api_year = ds.season_api_year
            and f.status_short in ('FT', 'AET', 'PEN')
            and f.kickoff_datetime < ds.upcoming_kickoff_datetime
    inner join import_fct_fixture_player_stats as fps
        on
            fps.fixture_sk = f.fixture_sk
            and fps.team_sk = ds.team_sk
            and fps.player_sk = ds.player_sk
    group by ds.upcoming_fixture_sk, ds.team_sk, ds.player_sk
),

domestic_season_context as (
    select
        ds.upcoming_fixture_sk,
        ds.team_sk,
        ds.player_sk,
        ds.league_code,
        ds.season_api_year,
        ds.upcoming_kickoff_datetime,
        coalesce(cnt.n_current_legs_before, 0) > 0 as use_current_season,
        case
            when coalesce(cnt.n_current_legs_before, 0) > 0 then ds.season_api_year
            else ds.season_api_year - 1
        end as form_season_api_year
    from domestic_squad as ds
    left join domestic_current_counts as cnt
        on
            ds.upcoming_fixture_sk = cnt.upcoming_fixture_sk
            and ds.team_sk = cnt.team_sk
            and ds.player_sk = cnt.player_sk
),

domestic_ranked_legs as (
    select
        dsc.upcoming_fixture_sk,
        dsc.team_sk,
        dsc.player_sk,
        dsc.league_code,
        dsc.form_season_api_year,
        dsc.use_current_season,
        fps.fixture_sk,
        fps.minutes_played,
        fps.goals_total,
        fps.goals_assists,
        fps.shots_on,
        fps.dribbles_success,
        fps.dribbles_attempts,
        fps.passes_total,
        fps.passes_accuracy_percent,
        fps.passes_key,
        fps.duels_total,
        fps.duels_won,
        fps.tackles_total,
        fps.tackles_interceptions,
        fps.tackles_blocks,
        fps.goals_saves,
        fps.goals_conceded,
        fps.cards_yellow,
        fps.cards_red,
        row_number() over (
            partition by dsc.upcoming_fixture_sk, dsc.team_sk, dsc.player_sk
            order by f.kickoff_datetime desc, f.fixture_sk desc
        ) as game_rn
    from domestic_season_context as dsc
    inner join import_fct_fixture as f
        on
            f.league_code = dsc.league_code
            and f.season_api_year = dsc.form_season_api_year
            and f.status_short in ('FT', 'AET', 'PEN')
            and f.kickoff_datetime < dsc.upcoming_kickoff_datetime
    inner join import_fct_fixture_player_stats as fps
        on
            fps.fixture_sk = f.fixture_sk
            and fps.team_sk = dsc.team_sk
            and fps.player_sk = dsc.player_sk
),

domestic_form_window as (
    select * from domestic_ranked_legs
    where not use_current_season or game_rn <= 5
),

-- ─── WC tournament form window ────────────────────────────────────────────
-- All finished WC tournament legs for this player + national team before upcoming kickoff.

wc_tournament_form_window as (
    select
        wts.upcoming_fixture_sk,
        wts.team_sk,
        wts.player_sk,
        fps.fixture_sk,
        fps.minutes_played,
        fps.goals_total,
        fps.goals_assists,
        fps.shots_on,
        fps.dribbles_success,
        fps.dribbles_attempts,
        fps.passes_total,
        fps.passes_accuracy_percent,
        fps.passes_key,
        fps.duels_total,
        fps.duels_won,
        fps.tackles_total,
        fps.tackles_interceptions,
        fps.tackles_blocks,
        fps.goals_saves,
        fps.goals_conceded,
        fps.cards_yellow,
        fps.cards_red
    from wc_tournament_squad as wts
    inner join import_fct_fixture as f
        on
            f.league_code = 'WC'
            and f.season_api_year = wts.season_api_year
            and f.status_short in ('FT', 'AET', 'PEN')
            and f.kickoff_datetime < wts.upcoming_kickoff_datetime
    inner join import_fct_fixture_player_stats as fps
        on
            fps.fixture_sk = f.fixture_sk
            and fps.team_sk = wts.team_sk
            and fps.player_sk = wts.player_sk
),

-- ─── Atom aggregation ─────────────────────────────────────────────────────

domestic_aggregated as (
    select
        upcoming_fixture_sk,
        team_sk,
        player_sk,
        any_value(league_code) as form_source_league_code,
        any_value(form_season_api_year) as form_season_api_year,
        any_value(use_current_season) as use_current_season,
        count(distinct fixture_sk) as matches_in_window,
        sum(coalesce(minutes_played, 0)) as minutes_played_window,
        sum(goals_total) as goals,
        sum(goals_assists) as assists,
        sum(shots_on) as shots_on,
        sum(dribbles_success) as dribbles_success,
        sum(dribbles_attempts) as dribbles_attempts,
        sum(passes_key) as passes_key,
        sum(passes_total) as passes_total,
        sum(
            safe_cast(
                floor(coalesce(passes_total, 0) * coalesce(passes_accuracy_percent, 0) / 100.0)
                as int64
            )
        ) as passes_accurate,
        sum(duels_total) as duels_total,
        sum(duels_won) as duels_won,
        sum(tackles_total) as tackles_total,
        sum(tackles_interceptions) as interceptions,
        sum(tackles_blocks) as blocks,
        sum(goals_saves) as goals_saves,
        sum(goals_conceded) as goals_conceded,
        sum(cards_yellow) as cards_yellow,
        sum(cards_red) as cards_red
    from domestic_form_window
    group by upcoming_fixture_sk, team_sk, player_sk
),

wc_tournament_aggregated as (
    select
        upcoming_fixture_sk,
        team_sk,
        player_sk,
        count(distinct fixture_sk) as matches_in_window,
        sum(coalesce(minutes_played, 0)) as minutes_played_window,
        sum(goals_total) as goals,
        sum(goals_assists) as assists,
        sum(shots_on) as shots_on,
        sum(dribbles_success) as dribbles_success,
        sum(dribbles_attempts) as dribbles_attempts,
        sum(passes_key) as passes_key,
        sum(passes_total) as passes_total,
        sum(
            safe_cast(
                floor(coalesce(passes_total, 0) * coalesce(passes_accuracy_percent, 0) / 100.0)
                as int64
            )
        ) as passes_accurate,
        sum(duels_total) as duels_total,
        sum(duels_won) as duels_won,
        sum(tackles_total) as tackles_total,
        sum(tackles_interceptions) as interceptions,
        sum(tackles_blocks) as blocks,
        sum(goals_saves) as goals_saves,
        sum(goals_conceded) as goals_conceded,
        sum(cards_yellow) as cards_yellow,
        sum(cards_red) as cards_red
    from wc_tournament_form_window
    group by upcoming_fixture_sk, team_sk, player_sk
),

-- ─── WC pre-tournament: pull from int_player_season__metrics ─────────────
-- Full current/most-recent domestic season per player (issue #154 2026-05-21 update).

wc_pre_tournament_with_season as (
    select
        wps.upcoming_fixture_sk,
        wps.team_sk,
        wps.player_sk,
        wps.domestic_league_code,
        -- Most recent season in that domestic league for this player
        psm.season_api_year as form_season_api_year,
        psm.matches_played as matches_in_window,
        psm.minutes_played_total as minutes_played_window,
        psm.goals,
        psm.assists,
        psm.shots_on,
        psm.dribbles_success,
        psm.dribbles_attempts,
        psm.passes_key,
        psm.passes_total,
        psm.passes_accurate,
        psm.duels_total,
        psm.duels_won,
        psm.tackles_total,
        psm.interceptions,
        psm.blocks,
        psm.goals_saves,
        psm.goals_conceded,
        psm.cards_yellow,
        psm.cards_red,
        row_number() over (
            partition by wps.upcoming_fixture_sk, wps.team_sk, wps.player_sk
            order by psm.season_api_year desc
        ) as season_rn
    from wc_pre_tournament_squad as wps
    inner join import_int_player_season__metrics as psm
        on
            psm.player_sk = wps.player_sk
            and psm.league_code = wps.domestic_league_code
),

wc_pre_tournament_aggregated as (
    select * except (season_rn)
    from wc_pre_tournament_with_season
    where season_rn = 1
),

-- ─── All players × upcoming fixtures with form window kind ───────────────

domestic_with_kind as (
    select
        dsc.upcoming_fixture_sk as fixture_sk,
        dsc.team_sk,
        dsc.player_sk,
        dsc.league_code as fixture_league_code,
        dsc.league_code as form_source_league_code,
        case
            when da.matches_in_window is null or da.matches_in_window = 0
                then 'domestic_prev_season_fallback'
            when dsc.use_current_season
                then 'domestic_last_5'
            else 'domestic_prev_season_fallback'
        end as form_window_kind,
        da.matches_in_window,
        da.minutes_played_window,
        da.goals,
        da.assists,
        da.shots_on,
        da.dribbles_success,
        da.dribbles_attempts,
        da.passes_key,
        da.passes_total,
        da.passes_accurate,
        da.duels_total,
        da.duels_won,
        da.tackles_total,
        da.interceptions,
        da.blocks,
        da.goals_saves,
        da.goals_conceded,
        da.cards_yellow,
        da.cards_red,
        case
            when da.matches_in_window is null or da.matches_in_window = 0
                then 'no_appearances_in_window'
        end as form_source_unavailable_reason
    from domestic_season_context as dsc
    left join domestic_aggregated as da
        on
            dsc.upcoming_fixture_sk = da.upcoming_fixture_sk
            and dsc.team_sk = da.team_sk
            and dsc.player_sk = da.player_sk
),

wc_tournament_with_kind as (
    select
        wts.upcoming_fixture_sk as fixture_sk,
        wts.team_sk,
        wts.player_sk,
        'WC' as fixture_league_code,
        'WC' as form_source_league_code,
        'wc_tournament_cumulative' as form_window_kind,
        wta.matches_in_window,
        wta.minutes_played_window,
        wta.goals,
        wta.assists,
        wta.shots_on,
        wta.dribbles_success,
        wta.dribbles_attempts,
        wta.passes_key,
        wta.passes_total,
        wta.passes_accurate,
        wta.duels_total,
        wta.duels_won,
        wta.tackles_total,
        wta.interceptions,
        wta.blocks,
        wta.goals_saves,
        wta.goals_conceded,
        wta.cards_yellow,
        wta.cards_red,
        case
            when wta.matches_in_window is null or wta.matches_in_window = 0
                then 'no_appearances_in_window'
        end as form_source_unavailable_reason
    from wc_tournament_squad as wts
    left join wc_tournament_aggregated as wta
        on
            wts.upcoming_fixture_sk = wta.upcoming_fixture_sk
            and wts.team_sk = wta.team_sk
            and wts.player_sk = wta.player_sk
),

wc_pre_with_kind as (
    select
        wps.upcoming_fixture_sk as fixture_sk,
        wps.team_sk,
        wps.player_sk,
        'WC' as fixture_league_code,
        coalesce(wps.domestic_league_code, 'unknown') as form_source_league_code,
        'wc_pre_via_domestic_full_season' as form_window_kind,
        wpa.matches_in_window,
        wpa.minutes_played_window,
        wpa.goals,
        wpa.assists,
        wpa.shots_on,
        wpa.dribbles_success,
        wpa.dribbles_attempts,
        wpa.passes_key,
        wpa.passes_total,
        wpa.passes_accurate,
        wpa.duels_total,
        wpa.duels_won,
        wpa.tackles_total,
        wpa.interceptions,
        wpa.blocks,
        wpa.goals_saves,
        wpa.goals_conceded,
        wpa.cards_yellow,
        wpa.cards_red,
        case
            when wps.domestic_league_code is null
                then 'league_not_covered'
            when wpa.matches_in_window is null or wpa.matches_in_window = 0
                then 'no_appearances_in_window'
        end as form_source_unavailable_reason
    from wc_pre_tournament_squad as wps
    left join wc_pre_tournament_aggregated as wpa
        on
            wps.upcoming_fixture_sk = wpa.upcoming_fixture_sk
            and wps.team_sk = wpa.team_sk
            and wps.player_sk = wpa.player_sk
),

all_insights as (
    select * from domestic_with_kind
    union all
    select * from wc_tournament_with_kind
    union all
    select * from wc_pre_with_kind
)

select
    fixture_sk,
    team_sk,
    player_sk,
    fixture_league_code as league_code,
    form_source_league_code,
    form_window_kind,
    form_source_unavailable_reason,
    coalesce(matches_in_window, 0) as matches_in_window,
    coalesce(minutes_played_window, 0) as minutes_played_window,
    -- Atoms: null when form_source_unavailable_reason is set
    case when form_source_unavailable_reason is null then goals end as goals,
    case when form_source_unavailable_reason is null then assists end as assists,
    case when form_source_unavailable_reason is null then shots_on end as shots_on,
    case when form_source_unavailable_reason is null then dribbles_success end as dribbles_success,
    case when form_source_unavailable_reason is null then dribbles_attempts end as dribbles_attempts,
    case when form_source_unavailable_reason is null then passes_key end as passes_key,
    case when form_source_unavailable_reason is null then passes_total end as passes_total,
    case when form_source_unavailable_reason is null then passes_accurate end as passes_accurate,
    case when form_source_unavailable_reason is null then duels_total end as duels_total,
    case when form_source_unavailable_reason is null then duels_won end as duels_won,
    case when form_source_unavailable_reason is null then tackles_total end as tackles_total,
    case when form_source_unavailable_reason is null then interceptions end as interceptions,
    case when form_source_unavailable_reason is null then blocks end as blocks,
    case when form_source_unavailable_reason is null then goals_saves end as goals_saves,
    case when form_source_unavailable_reason is null then goals_conceded end as goals_conceded,
    case when form_source_unavailable_reason is null then cards_yellow end as cards_yellow,
    case when form_source_unavailable_reason is null then cards_red end as cards_red,
    -- Derived rates (null when denominator zero or form unavailable)
    case
        when form_source_unavailable_reason is null
            then safe_divide(dribbles_success, dribbles_attempts)
    end as dribbles_success_pct,
    case
        when form_source_unavailable_reason is null
            then safe_divide(passes_accurate, passes_total)
    end as pass_accuracy_pct,
    case
        when form_source_unavailable_reason is null
            then safe_divide(duels_won, duels_total)
    end as duels_won_pct,
    case
        when form_source_unavailable_reason is null
            then safe_divide(goals_saves, nullif(goals_saves + goals_conceded, 0))
    end as save_pct
from all_insights
