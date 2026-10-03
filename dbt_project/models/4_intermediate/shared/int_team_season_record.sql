{#
  W2 season-record window — team. The rows of a team's season in one competition: one row per
  finished match, with that match's inputs (the team-match leg and the team totals from players)
  and its place in the season. The window is hand-written here; int_team_season__metrics_cumulative
  applies the catalogue formulas to it at every matchday (the totals THROUGH each match), and
  int_team_season__metrics is the final matchday. The complement to the form window
  (int_team_momentum_window): this answers "what have they done in this competition this season?".

  Grain: (team_sk, league_code, season_api_year, fixture_sk).

  Ordered by kickoff. Carries round_order (the matchday number parsed from round_name)
  and match_number (the team's Nth match that season) so the year-over-year surface can align two
  seasons by matchday.

  Season-bounded: partitioned by (league_code, season_api_year). This covers clubs and
  single-season tournaments (WC/continental — the latest row is "all matches so far in
  the tournament"). A national qualifying campaign is one season here: the provider stamps
  a whole campaign with a single season_api_year even though its matches span 2–3 calendar
  years (e.g. WCQEU = season 2024, matches 2025-03→2026-03), so this partition already
  cumulates the full campaign — matching the momentum qualifiers window (§4 / #655).
#}

with team_legs as (
    select * from {{ ref('int_legs__team_match') }}
),

player_legs as (
    select * from {{ ref('int_legs__team_from_players') }}
)

select
    tl.team_sk,
    tl.league_sk,
    tl.season_sk,
    tl.league_code,
    tl.season_api_year,
    tl.fixture_sk,
    tl.entity_type,
    tl.kickoff_datetime,
    tl.round_order,
    tl.result,
    tl.is_awarded_result,
    tl.goals,
    tl.goals_against,
    tl.goals_penalty,
    tl.goals_own,
    tl.goals_own_against,
    tl.shots,
    tl.shots_on_target,
    tl.shots_inside_box,
    tl.passes,
    tl.passes_accurate,
    tl.corners,
    tl.corners_against,
    tl.shots_against,
    tl.shots_on_target_against,
    tl.saves,
    tl.cards_yellow,
    tl.cards_red,
    pl.passes_key,
    pl.tackles,
    pl.interceptions,
    pl.blocks,
    pl.duels,
    pl.duels_won,
    'season_to_date' as window_type,
    row_number() over (
        partition by tl.team_sk, tl.league_code, tl.season_api_year
        order by tl.kickoff_datetime asc, tl.fixture_sk asc
    ) as match_number,
    pl.fixture_sk is not null as has_player_stats
from team_legs as tl
left join player_legs as pl
    on
        tl.fixture_sk = pl.fixture_sk
        and tl.team_sk = pl.team_sk
