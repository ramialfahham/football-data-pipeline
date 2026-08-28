{{ config(materialized='table') }}

{#
  TEAM deserved-vs-actual read (points-space). One row per (team_sk, season_sk): the points the
  team's process deserved, versus the points it actually has.

  Method (CPO-locked 2026-07-22, escalations.log): deserved signal = shots_on_goal_difference_per_match
  (SoT for - against per match). Within each league-season, fit ordinary least squares of
  points-per-match on that signal, then deserved_points = the fitted points-per-match * the team's
  own games played. deserved_points_gap = points_won_sum_season - deserved_points, so NEGATIVE = under-
  performing (results lag the process) and POSITIVE = over-performing. deserved_rank = rank teams by
  deserved_points within their league-season (descending; 1 = best). TEAM only; no xG.

  ⚠️ THE GAP SIGN IS INVERTED relative to the sot_rank_gap this replaces, where POSITIVE meant
  under-performing. That column is deleted rather than kept, precisely so one page cannot carry two
  gaps with contradictory signs. A reader carrying the old mental model will read this backwards;
  the contract test in int_team_season.yml pins it.

  Evidence for the method, measured over 91 domestic league-seasons / 1,790 team-seasons: SoT
  difference vs points is Pearson +0.84 (0.85 balanced seasons, 0.83 unbalanced), and the slope is
  ~0.25 points per match per unit of SoT difference, near 9.8 points over a 38-game season. Rank
  space was abandoned because a fitted line there can predict positions that do not exist.

  DOMESTIC LEAGUES ONLY (CPO 2026-07-22). deserved_rank ranks all teams in a competition 1..N, but a
  group-stage tournament's actual standing is a position WITHIN a group (1..4) — not comparable, so
  every tournament team carried a large false gap (mean absolute rank gap 3.43 domestic against
  8.29-21.46 for the tournament types, over 224 rows). The previous gate assumed knockouts carry no
  standing and would drop out on their own; group-stage tournaments DO carry standings, just not
  comparable ones, so it checked that a position EXISTS rather than that it is the same KIND of
  number. The registry join now restricts this explicitly. A tournament-appropriate version is
  wanted eventually and is deliberately NOT designed here.

  Composes int_team_season__metrics (the gated shots_on_goal_difference_per_match plus the season points and
  games-played totals — never recomputed here) and int_team_season__standings_primary. Availability
  handling lives upstream / here, never in the catalogue formula (formula-vs-availability ruling).

  Full-table coverage gate: deserved_points is computed only for league-seasons where EVERY team has
  a computable shots_on_goal_difference_per_match (full SoT coverage) AND an actual league rank AND at least 3
  finished games (the same >= 3 threshold int_team_competition_benchmark_metrics_long uses; below it
  the fit is small-sample noise and can predict impossible point totals). Otherwise NULL for every
  team in that league-season. deserved_points is additionally NULL when the signal has no spread
  across the league-season, since the slope is then undefined rather than flat.

  ⚠️ RESTRICTING TO DOMESTIC LEAGUES IS NOT SUFFICIENT. MLS ranks within Eastern/Western
  conferences, and the Apertura/Clausura formats (LMX, APD) split a year into two separate
  tournaments whose points reset. There `actual_rank` restarts at 1 per section, which is the same
  defect that excluded the tournaments, surviving inside the domestic set -- measured, not assumed:
  9 of the 55 otherwise-fittable league-seasons (232 rows) across MLS, LMX, APD and J1. Detected by
  the PROPERTY (are the actual ranks a 1..N permutation?) rather than by a league list, so a newly
  onboarded conference league needs no file edit. ALL THREE outputs are withheld there, not just the
  rank: for Apertura/Clausura the season points total itself sums two separate competitions (APD
  2025: 30 teams, a 15-position table, 32-37 games each), so a deserved-points figure is equally
  meaningless. MLS could probably support the points read, but telling it apart from Liga MX needs a
  real "is this one continuous competition" signal that does not exist yet, so this errs toward
  withholding. See OWED in the handover.

  NOTE, because it surprises people: because the fit is least squares within the league-season, the
  gap is a REDISTRIBUTION — one team's over-performance is another's under-performance. It sums to
  exactly 0 across a balanced (completed) league-season. Mid-season it sums to only approximately 0
  (measured: mean 3.9, max 9.6 points across a whole league) because each team's fitted rate is
  scaled by its own games played, which then differ.

  Grain: (team_sk, season_sk).
#}

with metrics as (
    select
        team_season_sk,
        team_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        entity_type,
        shots_on_goal_difference_per_match,
        points_won_sum_season,
        season_games_played,
        safe_divide(points_won_sum_season, season_games_played) as points_per_match
    from {{ ref('int_team_season__metrics') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

-- domestic-league rows only: a group-stage tournament's standing is a within-group position, which
-- is not the same kind of number as a 1..N league table rank.
domestic as (
    select m.*
    from metrics as m
    inner join registry as r
        on m.league_code = r.league_code
    where r.competition_type = 'domestic_league'
),

standings as (
    select
        team_sk,
        season_sk,
        standing_rank
    from {{ ref('int_team_season__standings_primary') }}
),

joined as (
    select
        d.*,
        s.standing_rank as actual_rank
    from domestic as d
    left join standings as s
        on d.team_sk = s.team_sk and d.season_sk = s.season_sk
),

-- full-table coverage gate: a league-season is fittable only when EVERY team has a computable
-- shots_on_goal_difference_per_match, an actual league rank, and at least 3 finished games.
-- `distinct_actual_ranks` vs `teams` additionally detects a league whose table is NOT a single
-- ladder — see actual_table_is_single_ladder below.
coverage as (
    select
        league_code,
        season_sk,
        countif(shots_on_goal_difference_per_match is null) as teams_missing_sot,
        countif(actual_rank is null) as teams_missing_rank,
        min(season_games_played) as min_games_played,
        count(*) as teams,
        count(distinct actual_rank) as distinct_actual_ranks
    from joined
    group by league_code, season_sk
),

gated as (
    select
        j.*,
        (
            c.teams_missing_sot = 0
            and c.teams_missing_rank = 0
            and c.min_games_played >= 3
            and c.distinct_actual_ranks = c.teams
        ) as league_season_fittable,
        -- Some DOMESTIC leagues do not run one table either: MLS ranks within Eastern/Western
        -- conferences, and the Apertura/Clausura formats (LMX, APD) split a year into two separate
        -- tournaments whose points reset. There `actual_rank` restarts at 1 per section, so it is
        -- the same "position exists but is not the same KIND of number" defect that excluded the
        -- tournaments — measured, not assumed: 9 of the 55 otherwise-fittable league-seasons
        -- (232 rows) across MLS, LMX, APD and J1. Detected by the PROPERTY (are the actual ranks a
        -- 1..N permutation?) rather than by a league list, so a newly onboarded conference league is
        -- handled with no file edit.
        --
        -- It gates ALL THREE outputs, not just the rank. A first attempt gated only deserved_rank,
        -- on the argument that points stay comparable even where table position does not. That is
        -- true for MLS (one continuous season; its own Supporters' Shield compares points across
        -- conferences) and FALSE for Apertura/Clausura, where one season_sk spans two separate
        -- competitions and `points_won_sum_season` sums across both. Verified: APD 2025 carries 30
        -- teams, a 15-position table and 32-37 games per team — a whole year of two tournaments.
        -- A deserved-points total there is a number nobody tracks.
        -- Telling MLS apart from Liga MX needs a real "is this one continuous competition" signal,
        -- which does not exist yet and is a design decision, not a builder's assumption. Until it
        -- does, this withholds rather than publishes: the conservative direction, at the cost of a
        -- read MLS could probably support. (football-analytics-expert-reviewer, 2026-07-22.)
        (c.distinct_actual_ranks = c.teams) as actual_table_is_single_ladder
    from joined as j
    inner join coverage as c
        on j.league_code = c.league_code and j.season_sk = c.season_sk
),

-- least-squares inputs, over the league-season the gate already partitions by.
stats as (
    select
        g.*,
        avg(g.points_per_match) over w as mean_points_per_match,
        avg(g.shots_on_goal_difference_per_match) over w as mean_sot_difference,
        stddev(g.points_per_match) over w as sd_points_per_match,
        stddev(g.shots_on_goal_difference_per_match) over w as sd_sot_difference,
        corr(g.shots_on_goal_difference_per_match, g.points_per_match) over w as corr_sot_points
    from gated as g
    window w as (partition by g.league_code, g.season_sk)
),

-- OLS slope: r * (sd_y / sd_x). NULL when the signal has no spread (safe_divide), which nulls the
-- whole read for that league-season rather than inventing a flat line.
fitted as (
    select
        s.*,
        s.corr_sot_points * safe_divide(s.sd_points_per_match, s.sd_sot_difference) as slope
    from stats as s
),

deserved as (
    select
        f.*,
        case
            when f.league_season_fittable
                then (
                    (f.mean_points_per_match - f.slope * f.mean_sot_difference)
                    + f.slope * f.shots_on_goal_difference_per_match
                ) * f.season_games_played
        end as deserved_points
    from fitted as f
),

-- single-ladder is now part of league_season_fittable, so deserved_points is already null wherever
-- a rank would be meaningless. deserved_rank therefore appears and disappears exactly with
-- deserved_points, and the schema asserts that biconditionally.
ranked as (
    select
        d.*,
        case
            when d.deserved_points is not null
                then rank() over (
                    partition by d.league_code, d.season_sk
                    order by d.deserved_points desc
                )
        end as deserved_rank
    from deserved as d
)

select
    team_season_sk,
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    entity_type,
    shots_on_goal_difference_per_match,
    points_won_sum_season,
    season_games_played,
    actual_rank,
    deserved_points,
    -- emitted, not just used internally: it is the ONLY thing that explains why a league-season can
    -- carry deserved_points and no deserved_rank, and without it in the output no test can assert
    -- that a genuine single-ladder table MUST get a rank (see the positive-existence guard in
    -- int_team_season.yml). A consumer can also use it to say why the rank is absent.
    actual_table_is_single_ladder,
    deserved_rank,
    -- negative = under-performing (fewer points than the process deserved); null when not fittable
    points_won_sum_season - deserved_points as deserved_points_gap
from ranked
