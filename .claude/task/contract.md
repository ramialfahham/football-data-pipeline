# Task contract — assign `direction` to every metric in the metric layer (catalogue-wide sweep)

> Written on a CLEAN tree (branch `feat/metric-direction-sweep` off main @ 9e7f8da).
> CPO-directed this conversation 2026-07-21: "I gave you the framing for why we want direction for all
> metrics. Apply this framing for every metric that has no direction yet" + "double check with the
> football analyst every metric". The CPO also restated the governing principle: "the metric layer
> defines what's in the mock not vice versa" — the catalogue is the SoT; the v2 mocks follow it.
> See docs/working_agreement.md §1 (E→P→C→I→V), §2, §10, §11, Appendix A;
> feedback: [[feedback-metric-direction-judgement]] [[feedback-metric-catalogue-governance]].

objective: >
  Make `direction` non-empty for EVERY row of metric_catalogue.csv, applying the CPO's all-else-equal
  framing. 36 rows change: 26 rows whose `direction` cell was BLANK get a value (18 higher_better,
  8 lower_better), and 10 rows currently mis-classified `neutral` become higher_better (the volume/style
  metrics — 3 team T/I/B per-match atoms + the 7 player per-90 volume metrics). Exactly 2 rows keep
  `neutral` because they genuinely have no better/worse pole: `sot_rank_gap` (a narrative) and
  `contribution_share` (a position-dependent share). The 10 rows flipping off `neutral` also get their
  `interpretation` rewritten to LEAD with the direction reading and keep the honest style/volume caveat
  SECOND — the same treatment PR #676 applied to the 5 team style metrics.

refs: >
  [[feedback-metric-direction-judgement]] (the framing) · PR #676 contract (this task executes its
  explicitly RESERVED player-per-90 decision) · the v2 player-page design conversation (2026-07-21).
  Design/governance-driven; no issue number.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv        # `direction` for 36 rows + `interpretation` for the 10 un-neutralled
  - dbt_project/seeds/schema.yml                  # AMENDMENT r1 — de-stale the `direction`/`interpretation` column docs (prose only)
  - dbt_project/tests/assert_team_metric_meaning_complete.sql   # AMENDMENT r1 — de-stale the docstring (prose only, NO logic change)
  - .claude/task/**
  - .claude/active_work.md

impact_map: >
  writers: none — a seed VALUE change only (the `direction` cell of 36 existing rows + the
    `interpretation` cell of 10 of them). No new column, no row added or removed, no formula touched
    (numerator_expr/denominator_expr/base_relation all unchanged). No model, raw table or ingestion code.
  downstream (evidence: `grep -r direction` + `grep -r lower_is_better` over dbt_project + scripts +
    site_v2, every hit read):
      - mart_team_competition_benchmarks.sql + mart_player_competition_benchmarks.sql: DIRECTION-AGNOSTIC
        by design (rank by metric_value; good/bad applied at DISPLAY). ZERO number change; benchmark DQ
        tests unaffected.
      - seeds/schema.yml: `direction` accepted_values [higher_better, lower_better, neutral] — every new
        value is in-set. Still passes.
      - tests/assert_team_metric_meaning_complete.sql: FAILs if a TEAM metric has NULL/empty direction OR
        interpretation. The only team rows touched (tackles/interceptions/blocks_per_match) keep a
        non-empty interpretation (rewritten, not cleared). Still passes.
      - tests/assert_metric_catalogue_expr_resolvable.sql: reads the expression columns, which are
        untouched. Unaffected.
      - scripts/export_metric_definitions_json.py (LIVE MVP): reads `lower_is_better`, NOT `direction`.
        `lower_is_better` is NOT touched here, so the live MVP good/bad reading is BYTE-IDENTICAL.
      - scripts/export_site_data.py (v2): direction is applied at render; the marts carry no direction
        column. No payload shape change.
      - site_v2/src/lib/metricRows.ts: mirrors direction for the FIXTURE comparison's 16 TEAM display
        rows only. None of the 36 rows changed here is one of those 16 (they are player metrics, player
        per-90s, and the 3 team T/I/B atoms which render as a sub-breakdown "15 tkl · 8 int · 3 blk",
        not as their own comparison bar). So metricRows.ts needs NO mirror edit and is out of scope.
  layer_rules: seed value change; no dbt model layer touched (check_layer_contract N/A).
  deploy_order: no prod number moves. Nothing changes on the 04:00 nightly. ci-data-build (shared prod
    dataset, full DQ suite) is the byte-safety gate.
  blast_radius: ZERO number change anywhere. 36 metrics gain a good/bad reading they did not have. The
    only currently-rendered surface affected is the v2 player Performance percentile bar (not yet built),
    which is precisely why the CPO asked for this now.

decisions_taken: >
  1. THE FRAMING (CPO, restated 2026-07-21, already recorded in [[feedback-metric-direction-judgement]]):
     `direction` is a JUDGEMENT — "all else equal, is MORE of this better?" — NOT a correlation with
     results or final rank. A style/volume metric STILL gets a direction; it is not `neutral` merely
     because it is also a style attribute or a weak predictor of rank. `neutral` is reserved for a
     metric with genuinely NO better/worse pole.
  2. VALIDATION: two INDEPENDENT derivations over all 78 rows (a general pass and the
     football-analytics-expert-reviewer) agreed on the direction for EVERY row — no disagreement. The
     football reviewer's contestable calls are documented in decisions_reserved, not re-litigated.
  3. This executes the decision PR #676 explicitly RESERVED: "Player per-90 volume analogs
     (passes_per90, tackles_per90, interceptions_per90, blocks_per90, defensive_actions_per90,
     duels_won_per90, saves_per90) stay `neutral` — out of scope; a consistency call for when the player
     page is designed." The player page is now designed, so the call is made: all 7 become higher_better.
  4. CONSCIOUS REVERSAL of PR #676 decision 4 ("T/I/B atoms + sot_rank_gap stay `neutral` — not verdict
     bars"). Under the framing, direction is a property of the METRIC, not of whether it is drawn as a
     verdict bar, so tackles/interceptions/blocks_per_match become higher_better. `sot_rank_gap` still
     stays `neutral`, on the framing's own no-pole test, not on the display argument.
  5. `lower_is_better` is NOT touched. The LIVE MVP export reads it, so changing it would move live
     behaviour; #676 set the same precedent. Four rows where the boolean now disagrees with the new
     direction are logged in decisions_reserved.

decisions_reserved:
  - "`lower_is_better` vs `direction` divergence on 4 player rows (cards_yellow, cards_red, cards_total,
     shots_on_goal_against read lower_is_better=false while direction is now lower_better). Fixing the
     boolean CHANGES THE LIVE MVP good/bad reading, so it is its own CPO decision + PR. Not touched here."
  - "The 26 newly-directional player rows still have a BLANK `interpretation`. A catalogue-wide
     interpretation sweep is a separate task; this PR only rewrites the 10 interpretations that would
     otherwise contradict their own new direction (the un-neutralled ones)."
  - "Football-reviewer contestable calls, CPO-accepted per the framing and NOT to be re-litigated:
     `saves` + `saves_per90` = higher_better (a save is a good act, though volume also tracks shots
     faced) and `shots_on_goal_against` = lower_better (fewer on-target shots faced is better, though
     it is mostly the outfield defence's doing). The honest caveat belongs in `interpretation`."
  - "Whether `contribution_share` ever gets a display home (it is built and wired but rendered on no
     screen) — a v2 design decision, not this PR."

done_when:
  - metric_catalogue.csv: EVERY row has a non-empty `direction`; the only `neutral` values remaining are
    `sot_rank_gap` and `contribution_share` (grep-verified, exactly 2).
  - The 10 un-neutralled rows carry an `interpretation` that leads with the direction reading and keeps
    the style/volume caveat second; no interpretation is cleared.
  - No other column changed anywhere in the seed (diff-verified: only the `direction` and
    `interpretation` cells move).
  - ci-data-build GREEN (seed loads; accepted_values + assert_team_metric_meaning_complete + the full DQ
    suite pass; no number drift — benchmarks are direction-agnostic).
  - Required reviewers PASS: scope-auditor + analytics-engineer-reviewer + football-analytics-expert-
    reviewer (metric_catalogue.csv), per review_routing.json. review.md diff_sha256 binds; CPO merges
    (I never merge).
  - Handover bullet added to .claude/active_work.md.

amendments:
  - >
    r1 (2026-07-21, REVIEWER-DRIVEN — analytics-engineer-reviewer FAIL, MEDIUM, config-as-code rule #5):
    the seed's OWN governing docs assert an invariant this change falsifies. `dbt_project/seeds/schema.yml`
    describes `direction` as "Populated for team metrics; null for the not-yet-classified player metrics
    (player benchmark, v1.x) ... player rows exempt while v1.x", and the docstring of
    `dbt_project/tests/assert_team_metric_meaning_complete.sql` repeats the same claim. Both become FALSE
    once every player row carries a direction, and `dbt docs generate` would publish them as current truth.
    Added both files to scope_paths to correct the PROSE ONLY. Explicitly NOT changed: the test's LOGIC and
    its team-only enforcement scope, which is RETAINED DELIBERATELY and re-justified in the docstring — the
    26 newly-directional player rows still carry a blank `interpretation` (a reserved follow-up sweep), so
    broadening the test to players would fail on interpretation, not on direction. Both files route to
    analytics-engineer-reviewer, already in the required reviewer set, so the review gate is UNCHANGED by
    this amendment. scope-auditor had already PASSed the pre-amendment scope; it is re-run after this.
