{#
  Per-fixture team stat line (#323). The detail view behind a match in the
  form-window list: the full team stat line for one finished fixture, both
  sides as two rows: a projection of fct_fixture_team_stats plus fixture
  metadata and team identity for display. The one derived value,
  passes_accuracy_percent, is the catalogue's pass accuracy over the team's own
  match, written by scripts/generate_metric_sql.py and shown as a whole
  percentage. The app reads this mart, never core.

  Covers ALL finished fixtures that have team stats, not just form-window
  matches: it is selection-free by design and serves the team/player profile
  surfaces (#324/#325) too. A fixture with no rows here has no team stats —
  the honest "not available" state. The stat line is the cleaned one from
  core, handed on under the names the export reads.

  Grain: (fixture_sk, team_sk).
#}

with stats as (
    select
        *,
        false as is_awarded_result
    from {{ ref('fct_fixture_team_stats') }}
    -- Core holds a row for every team of a finished match; only a line the provider
    -- sent with a value in it is shown, so a team without one gets the "stats not
    -- available" state rather than a view of blanks and event-proven zero cards.
    where has_stat_line
),

match_rates as (
    select
        fixture_sk,
        team_sk,
        -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
        safe_divide(
            if(
                logical_and(is_awarded_result or passes_accurate is not null) over w,
                sum(if(is_awarded_result, null, passes_accurate)) over w,
                null
            ),
            if(
                logical_and(is_awarded_result or passes is not null) over w,
                sum(if(is_awarded_result, null, passes)) over w,
                null
            )
        ) as passes_accuracy_pct
        -- end of generated metric sql
    from stats
    window w as (partition by fixture_sk, team_sk)
),

fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        round_name,
        home_team_sk,
        goals_home,
        goals_away
    from {{ ref('fct_fixture') }}
    where status_short in ('FT', 'AET', 'PEN')
),

teams as (
    select
        team_sk,
        team_name,
        team_logo_url
    from {{ ref('dim_team') }}
)

select
    s.fixture_sk,
    s.team_sk,
    f.league_code,
    f.season_api_year,
    f.kickoff_datetime,
    f.round_name,
    t.team_name,
    t.team_logo_url,
    s.shots_on_target as shots_on_goal,
    s.shots_off_target as shots_off_goal,
    s.shots as shots_total,
    s.shots_blocked,
    s.shots_inside_box,
    s.shots_outside_box,
    s.fouls,
    s.corners as corner_kicks,
    s.offsides,
    s.possession_pct as ball_possession_percent,
    s.cards_yellow as yellow_cards,
    s.cards_red as red_cards,
    s.saves as goalkeeper_saves,
    s.passes as passes_total,
    s.passes_accurate,
    cast(round(100 * r.passes_accuracy_pct) as int64) as passes_accuracy_percent,
    s.team_sk = f.home_team_sk as is_home,
    if(s.team_sk = f.home_team_sk, f.goals_home, f.goals_away) as goals_for,
    if(s.team_sk = f.home_team_sk, f.goals_away, f.goals_home) as goals_against
from stats as s
inner join match_rates as r
    on s.fixture_sk = r.fixture_sk and s.team_sk = r.team_sk
inner join fixtures as f
    on s.fixture_sk = f.fixture_sk
left join teams as t
    on s.team_sk = t.team_sk
