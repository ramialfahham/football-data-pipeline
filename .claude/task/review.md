# Review — fix/finishing-open-play-conversion — 2026-06-25

> G3 review of the finishing_efficiency → open-play conversion change (CPO Option A).
> Three rounds were run cold/blinded on the cumulative branch diff; this file records the
> FINAL-round verdicts that bind to the committed diff. Round 1 caught a runtime
> column-resolution bug in int_season_record__team (legs CTE missing tl.goals_penalty/
> tl.goals_own); round 2 caught the missing [0,1] finishing test on int_player_season_
> position__metrics. Both fixed; this final round is all-PASS. football-analytics-expert
> PASSed on the catalogue rows and is carried from its review — metric_catalogue.csv is
> byte-identical since (the only post-review changes were the build fix + the position-model
> test, neither touching the catalogue).

diff_sha256: 690814761a2ff1e17195dee92d4c0ea7ca58e91c63eb4c2bc87de83154cce4cb

## scope-auditor
VERDICT: PASS
risks_checked:
- goals_own event attribution: the opponent-team own-goal events are credited to the scoring
  team via the opponent_team_sk join in int_legs__team_match — checked the join cannot invert
  the penalty/own-goal subtraction; held.
- [0,1] finishing bounds enforcement on every exposing surface (CASE guards in 3 intermediates
  + the marts, plus dbt range tests), so no row can exceed the [0,1] open-play-conversion
  constraint; held. Also verified the 2026-06-25 amendment is pure test/scope widening with
  recorded authority (reviewer FAIL + standing fix-then-re-review rule), no §10 decision
  smuggled in, and the impact_map is honest that LIVE finishing numbers change.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Run-time column resolution (dbt compile does not validate it): re-checked every model that
  aggregates goals_penalty/goals_own. int_season_record__team's legs CTE now projects
  tl.goals_penalty/tl.goals_own and the outer `sum(...) over w` resolves; int_momentum__team,
  int_team_season__metrics and both player models project the columns through their source
  chains. No remaining unresolved-column reference.
- Own-goal join semantics in int_legs__team_match (goals_own = ev_opp.own_goals_scored on
  l.opponent_team_sk = ev_opp.team_sk — the opponent's own goals that credit THIS team; no
  fan-out, events grouped by fixture_sk/team_sk before the join), AND the no-drift guard (new
  _season-suffixed team columns + the player goals_penalty/goals_open_play normalize to
  catalogued (entity, metric_id) pairs → guard passes), AND [0,1] finishing test coverage
  enumerated on every surface exposing finishing_efficiency (the intermediates
  int_momentum__team/int_season_record__team carry raw sums only — ratios live in the marts —
  so no gap). findings: none.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Numerator/denominator penalty-consistency: the provider's shots_on_goal excludes penalty
  kicks (confirmed by the diagnostic — 85% of the residual "own goals > SoG" rows were
  penalties); removing penalties from the numerator (goals_open_play) makes both sides
  penalty-free and eliminates the structural cause of >100% readings — football-correct
  open-play / non-penalty conversion.
- goals_own team-only correctness: own goals are credited to the benefiting team's scoreline by
  football convention, and a player's goals_total already excludes own goals — so the player
  rows correctly carry goals_penalty + goals_open_play but no goals_own. Descriptions accurate;
  "shown uncapped" / >100% wording removed; a penalty-heavy striker now reads lower finishing
  by design (intended; goals_penalty is catalogued alongside for context).
findings:
- Non-blocking, out of scope: docs/wireframes/metrics_display.md still carries stale copy
  ("finishing can exceed 100%"). It is a bi-analyst-owned display doc, deferred per D2; flagged
  for a follow-up, not edited in this PR.

## escalations
(none)
