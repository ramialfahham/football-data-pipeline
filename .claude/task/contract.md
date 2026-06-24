# Task contract — finishing_efficiency → open-play conversion (Option A), team + player

> CPO-directed (2026-06-24): finishing_efficiency must be a true rate ∈ [0,1]. The >100% bug
> is a DEFINITION flaw — the numerator was the scoreline (own goals + penalties), which aren't
> the team finishing its own on-target shots. CPO chose **Option A — non-penalty (open-play)
> conversion**, and ruled that the penalty/own components used in the calculation must themselves
> be FIRST-CLASS CATALOGUED metrics (no un-catalogued hidden derivation — the goals_for_in_shot_games
> lesson). This CHANGES LIVE NUMBERS (finishing_efficiency_recent is on the live match preview)
> → directed PR + before/after deltas + the review cycle. It lands BEFORE PR-a (#567), which is
> blocked by the finishing [0,1] test; PR-a rebases after. The universal "can't-calculate → NULL"
> guard (every window metric + the enforcing mechanism) is the IMMEDIATE FOLLOW-ON PR.

objective: >
  Redefine finishing_efficiency as open-play conversion. Numerator = `goals_open_play`
  (= goals − goals_penalty − goals_own; player = goals − goals_penalty), denominator = shots_on_goal
  (already penalty-free in the provider data). `goals` stays the AUTHORITATIVE total (team scoreline
  goals_for / player goals_total) and the penalty/own components are SUBTRACTED — NOT computed by
  counting Normal-Goal events — so a stray disallowed/VAR event cannot inflate the numerator
  (measured: events reconcile with the scoreline 99.3%, undercount 0.018%, overcount 0.67%).
  Apply the calculability rule to finishing: NULL ("—") when the window is not fully shot-covered,
  and when a rare inconsistent row has goals_open_play > shots_on_goal (the ~0.06% broken-stat
  cases). Delete the partial-window device goals_for_in_shot_games. Make finishing ∈ [0,1]
  enforceable: range test on every finishing surface, remove the "uncapped" exemptions, rewrite
  the catalogue row. Team and player, end-to-end, one definition.

refs: >
  CPO ruling 2026-06-24 (this conversation): finishing is a rate, must be [0,1]; Option A
  (open-play, exclude own goals + penalties) chosen after the diagnostic; penalty/own components
  must be catalogued metrics with the `goals_` naming; event data quality confirmed sufficient.
  Foundational rule "if we can't calculate it, we don't show it" ([[feedback-no-hacky-solutions]]
  7th mode). Catalogue-first governance #324. Unblocks PR-a (#567). #500 context.

# DIAGNOSTIC EVIDENCE (dbt show, 2026-06-24):
#   (1) Goal event_detail vocabulary: Normal Goal 123,249 | Penalty 15,248 | Own Goal 3,941 |
#       Missed Penalty 1,976. (2) Of 87,626 team-fixtures with shots_on_goal, after excluding own
#       goals + missed penalties 328 (0.37%) still have own goals > SoG — 278 (85%) are penalties
#       (the provider's "Shots on Goal" does NOT count penalty kicks) → Option A removes penalties
#       too. (3) Event completeness vs the finishing population: 43,813 fixtures with shots_on_goal;
#       events reconcile with the scoreline 99.3% (43,510), undercount 8 (0.018%), zero "goals but
#       no events", overcount 295 (0.67%, disallowed/VAR) → events reliable; basing goals on the
#       scoreline + subtracting event-derived penalty/own makes it robust to the overcount.

scope_paths:
  - .claude/task/**
  - .claude/active_work.md
  # --- the catalogue (3 NEW rows: goals_penalty team+player, goals_own team, goals_open_play; + finishing row) ---
  - dbt_project/seeds/metric_catalogue.csv
  # --- the component + numerator derivation: penalty/own from events, threaded into the legs ---
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  # --- the team finishing aggregates (finishing = goals_open_play / shots_on_goal; drop goals_for_in_shot_games) ---
  # int_momentum_window__team passes the leg columns (incl. goals_penalty/goals_own) into int_momentum__team
  - dbt_project/models/4_intermediate/shared/int_momentum_window__team.sql
  - dbt_project/models/4_intermediate/shared/int_momentum__team.sql
  - dbt_project/models/4_intermediate/shared/int_season_record__team.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  # --- the player finishing aggregates ---
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  # --- the marts that compute/pass finishing (team) ---
  - dbt_project/models/5_marts/shared/mart_momentum__team.sql
  - dbt_project/models/5_marts/shared/mart_season_record__team.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  # --- the marts that compute/pass finishing (player) ---
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_competition_benchmarks__player.sql
  # --- the LIVE marts that inherit the changed finishing numbers (numbers change) ---
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  # --- the schema/yml docs + tests ([0,1] on finishing; remove uncapped exemptions; doc the new metrics) ---
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  # added 2026-06-25 (reviewer-driven amendment, see amendments): the [0,1] finishing test for
  # int_player_season_position__metrics must live in this model's existing schema yml.
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  # NOTE: exact computed-vs-passthrough per mart confirmed during build by `dbt compile` + a
  # `dbt show` before/after delta. Any finishing-bearing file not listed here is added by a
  # clean-tree amendment, never edited silently.

# EXPLICITLY OUT OF SCOPE (this PR):
#   - The UNIVERSAL calculability rule for all OTHER window metrics + the enforcing guard +
#     goals_against_in_save_games (save_ratio's analogue) — the FOLLOW-ON PR.
#   - The #500 naming renames (shots_on_target->shots_on_goal etc.) — that is PR-a (#567), which
#     rebases on this. This PR uses main's current atom names; it does NOT rename.

impact_map: >
  NEW catalogued component metrics (CPO-approved 2026-06-24; `goals_` naming):
    - goals_penalty (team + player): count of fct_fixture_event rows event_type='Goal' AND
      event_detail='Penalty', attributed to the team / player.
    - goals_own (team only): own goals credited to the team = the OPPONENT's Own Goal events in
      the fixture. (Player goals_total already excludes own goals, so players need only goals_penalty.)
    - goals_open_play (numerator): goals − goals_penalty − goals_own (player: goals − goals_penalty).
  derivation (where the events are read):
    - int_legs__team_match: ADD ref('fct_fixture_event'); per (fixture,team) compute goals_penalty
      (team's Penalty events) and goals_own (opponent's Own Goal events); goals_open_play_for =
      goals_for (scoreline) − goals_penalty − goals_own. (Today legs ref fct_fixture +
      fct_fixture_team_stats only.)
    - PLAYER finishing models read fct_fixture_player_stats DIRECTLY (not the legs), so player
      goals_penalty is derived IN int_player_season__metrics + int_player_season_position__metrics
      (ADD ref('fct_fixture_event'), per (fixture,player) Penalty count); goals_open_play =
      goals_total − goals_penalty. int_legs__player_match is NOT on the player finishing path.
  finishing recomputation (numerator -> goals_open_play in shot-covered games; denominator = shots_on_goal):
    - team: int_momentum__team, int_season_record__team, int_team_season__metrics — finishing =
      sum(goals_open_play over shot-covered games) / shots_on_goal, NULL unless fully shot-covered
      AND numerator <= shots_on_goal. DROP goals_for_in_shot_games.
    - player: int_player_season__metrics, int_player_season_position__metrics — finishing =
      goals_open_play / shots_on_goal (same null rules).
  downstream (finishing-bearing marts): mart_momentum__team, mart_season_record__team,
    mart_team_profile (team); mart_player_profile, mart_leaderboards, mart_competition_benchmarks__player
    (player). LIVE: mart_matchday_insights (home/away finishing_efficiency_recent) +
    mart_team_season_insights (finishing_efficiency_season) inherit the changed numbers.
  LIVE BOUNDARY (numbers CHANGE — the whole point): finishing_efficiency_recent is a live
    metric_definitions.csv row -> the live match preview "Conversion rate". Today it can read >100%;
    after this it is open-play conversion, [0,1], or "—". Before/after deltas REQUIRED.
  layer_rules: legs gain an events join (intermediate layer — allowed; no staging/base change). The
    momentum_team_finishing_efficiency_in_range [0,1] test now PASSES by construction. The catalogue
    no-drift guard: the new goals_penalty/goals_own/goals_open_play columns must be catalogued (they
    are, this PR) or the guard fails — so the catalogue rows and the model columns ship together.
  deploy_order: shared single BigQuery — one dbt build rebuilds legs + aggregates + marts together.
    Lands first; PR-a (#567) rebases (the #500 renames replay on top; sibling-rebase recovery).
  blast_radius: NUMBERS CHANGE for finishing_efficiency on every surface (team + player, all
    windows), by design + the 3 new catalogued columns. No OTHER existing metric changes (the
    numerator change is isolated to finishing; save_ratio etc. untouched). Quantified by before/after
    deltas at review.

decisions_taken: >
  CPO locked Option A (2026-06-24): finishing_efficiency = open-play conversion, numerator
  goals_open_play = goals − goals_penalty − goals_own (player: goals − goals_penalty), denominator
  shots_on_goal. NULL when not fully shot-covered OR goals_open_play > shots_on_goal (rare
  broken-stat rows — honest "can't calculate", NOT a cap). [0,1] enforced by test on every finishing
  surface; the "uncapped" exemptions removed; the catalogue "shown uncapped" text deleted.
  CPO APPROVED the 3 NEW catalogue rows with the `goals_` naming (no un-catalogued quantity in a
  metric's calculation): goals_penalty (team+player), goals_own (team), goals_open_play. CPO
  confirmed event data quality is sufficient (99.3% reconcile) and "Go" to build (2026-06-24).
  Deriving the components from fct_fixture_event is the mechanical implementation.

decisions_reserved:
  - D1 (save_ratio + the universal rule + the guard — DEFERRED to the follow-on PR, not here):
    save_ratio uses the analogous goals_against_in_save_games partial-window device; the "NULL
    unless fully covered" rule applies to ALL window metrics; the enforcing guard the CPO asked for
    is its own PR (a simple generic mechanism — not a conformance engine). This PR is finishing-only
    so the live-number delta is isolated and reviewable.
  - D2 (display of the new component metrics — NOT decided here): goals_penalty / goals_own /
    goals_open_play are catalogued (registry) this PR; WHETHER/where they are shown on a page is a
    separate display (§10) decision, deferred. Cataloguing != displaying.

done_when:
  - The 3 catalogue rows (goals_penalty team+player, goals_own team, goals_open_play) added to
    metric_catalogue.csv with `goals_` naming; the finishing_efficiency row rewritten (numerator =
    goals_open_play; "shown uncapped" deleted); metric_id == the model column for each.
  - goals_penalty / goals_own derived from fct_fixture_event in both legs; goals_open_play computed;
    finishing recomputed as goals_open_play / shots_on_goal on every team + player surface;
    goals_for_in_shot_games removed.
  - finishing is NULL (never >1, never a partial-window value): NULL unless fully shot-covered AND
    goals_open_play <= shots_on_goal.
  - `[0,1]` range test present on finishing on EVERY surface; the uncapped exemptions removed.
  - dbt parse + compile clean; sqlfluff(models) clean; the no-drift guard passes (new columns
    catalogued); the momentum_team_finishing_efficiency_in_range test (and siblings) PASS.
  - BEFORE/AFTER deltas captured (dbt show, old vs new finishing on the affected marts incl. live)
    and recorded for the reviewers — directed shipped-number change.
  - G3 review cycle passes (scope-auditor + analytics-engineer + football-analytics for the
    catalogue rows). PR opened; CPO merges. PR-a (#567) noted for rebase after this merges.

amendments:
  - 2026-06-24 scope correction (trace-driven, pre-commit): a full finishing-lineage trace added
    int_momentum_window__team (team momentum passthrough — was missing from the first-pass scope)
    and corrected the PLAYER derivation. Player finishing models read fct_fixture_player_stats
    directly, so goals_penalty is derived IN the two player season models, NOT via
    int_legs__player_match (that leg edit was reverted as misdirected). Team derivation stays via
    int_legs__team_match. Authority: the lineage grep evidence; scope only widened to honour the
    trace, no new product/metric decision.
  - 2026-06-25 reviewer-driven scope amendment (G3): the analytics-engineer reviewer FAILed because
    int_player_season_position__metrics exposes finishing_efficiency but had no [0,1] range test of
    its own (done_when requires the test on EVERY finishing surface; the benchmark-mart filtered
    test does not cover sub-floor / GK rows). The fix must live in that model's existing schema yml,
    dbt_project/models/4_intermediate/shared/int_player_season_position.yml, which was not in the
    first-pass scope. Added to scope_paths above. Authority: the reviewer FAIL + the standing
    "fix-then-re-review" rule (working_agreement §2); scope only widened to add a test, no new
    product/metric decision. CPO authorised the clean-tree amendment mechanism (temporary stash) in
    this conversation.
