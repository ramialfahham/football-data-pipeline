# Task contract — matchday-aligned team YoY for ALL metrics (Option A)

> Written on a CLEAN tree (branch `feat/team-yoy-all-metrics` off main @ d674905).
> CPO-directed this conversation 2026-07-11: the team page's "vs last season" must cover
> EVERY season metric, matchday-aligned — "extend the model" (not a frontend shortcut).
> CPO chose Option A (the COMPOSE architecture) for formula placement.
> See docs/working_agreement.md §1 (E→P→C→I→V), §2, §10, §11, Appendix A;
> feedback: [[feedback-metric-calc-layer-placement]] [[feedback-macros-maintainability]]
> [[project-dbt-shared-ci-prod-datasets]] [[reference-incremental-rename-full-refresh]].

objective: >
  Extend the team year-over-year surface from 3 metrics (points, goals for, goals against)
  to ALL season metrics, matchday-aligned (this season through N games vs the SAME team's
  prior season through its first N games), so the v2 team "Stats" tab can show a per-metric
  this/last column. Option A: lift the season-metric rate formulas into ONE cumulative model
  (rates at every matchday), make the existing whole-season int_team_season__metrics its
  final-row PROJECTION (byte-identical → zero downstream number change), and have
  int_team_profile__yoy COMPOSE the cumulative model at the cutoff N for both seasons.

refs: >
  #324 (team profile + YoY) · #500 (one-aggregation philosophy) · wireframe 02 §6 ·
  the team-page redesign (this conversation). Source model already anticipates this:
  int_team_season_record header — carries match_number "so the deferred year-over-year
  surface can align two seasons by matchday without a rewrite."

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/**   # new cumulative model + int_team_season__metrics (→ projection) + int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql # +all-metric aligned YoY
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml      # YoY tests/docs
  - dbt_project/models/5_marts/shared/mart_team_profile.sql            # + YoY columns (passthrough)
  - dbt_project/models/5_marts/shared/shared.yml                       # mart tests/docs
  - .claude/task/**
  - .claude/active_work.md

impact_map: >
  writers: none — all models read int_team_season_record (the cumulative raw-sums source,
    UNCHANGED). No raw/staging/ingestion touched.
  downstream (grep ref-graph; full `dbt ls --select int_team_season__metrics+` runs in
    ci-data-build — dbt CLI is broken locally): int_team_season__metrics is read by SIX
    models → int_team_season__deserved_vs_actual, int_team_competition_benchmark_metrics_long
    (→ int/mart_team_competition_benchmarks → v2 benchmark export), mart_team_season,
    mart_team_season_insights (→ LIVE MVP team-season JSON via export_pages_data.py),
    mart_team_profile (→ v2 team export), mart_team_season_record (→ v2 W2 window + fixture).
  layer_rules: intermediate materialization=table (like int_team_season__metrics + siblings);
    check_layer_contract (no per-competition staging; generic model reading league_code).
    int_team_season__metrics is ALL-competitions (verified: no domestic filter) — the new
    cumulative base must keep that scope; the YoY consumer filters to domestic_league + aligns.
  deploy_order: the refactor is BYTE-IDENTICAL (int_team_season__metrics = final row of the
    same formulas over the same input) → zero prod number change on the 04:00 nightly. dbt
    shares CI/prod datasets, so ci-data-build runs the full singular DQ suite vs shared prod —
    that suite on all 6 consumers is the byte-identity gate (any drift fails a test). The new
    YoY columns are ADDITIVE.
  blast_radius: int_team_season__metrics OUTPUT unchanged (the LIVE MVP team-season numbers +
    every v2 team/benchmark number stay identical — proven by the existing DQ suite staying
    green). NEW = matchday-aligned this/prev/delta for the ~13 rate metrics on
    int_team_profile__yoy → mart_team_profile → v2 team export only (additive; the live MVP
    does not read YoY). NO catalogue rows (windowed YoY variants are exempt from the drift
    guard — same as today's 3-metric YoY).

decisions_taken: >
  1. Option A (CPO-approved this session): a cumulative team-season RATES model (the current
     int_team_season__metrics SELECT applied to EVERY cumulative row of int_team_season_record,
     not just the final), with int_team_season__metrics becoming its final-row projection.
     Formulas live in ONE place; no macro (inline SQL, per [[feedback-macros-maintainability]]).
  2. Matchday alignment is by GAMES PLAYED (match_number), reusing the existing YoY mechanism
     (cur = latest cumulative row this season → cutoff N; prev = prior season's largest
     match_number ≤ N). The rate coverage gates carry over unchanged: a metric is NULL on a
     side when that season's first N games are not fully stat-covered — honest, never fabricated.
  3. Byte-identity of int_team_season__metrics is REQUIRED (it feeds the live MVP). Verified by
     ci-data-build's existing DQ suite on the 6 consumers staying green.
  4. No catalogue changes; YoY stays domestic-league only (cups/tournaments have no aligned
     comparison — the existing scope).
  5. BOTH new ratio DQ tests — on int_team_season__metrics_cumulative AND on the composed
     int_team_profile__yoy (which reads the cumulative model at cutoff N) — are split by INVARIANT
     FAMILY, not a verbatim copy of the whole-season [0,1] test (that over-strict copy failed
     ci-data-build on exactly one row, LIBER 2024 team 2546 match 1, danger_zone_ratio 1.25).
     Structurally-bounded ratios (points_capture / clean_sheets / shot_share / save_ratio /
     finishing_efficiency — the last guarded to NULL when goals>SoT) keep strict [0,1] at every
     matchday. Provider-subset ratios (shot_accuracy / danger_zone_ratio / pass_accuracy /
     duels_won_pct = one provider stat over another) are bounded ≥0 only: at low N a single game
     where the provider reports numerator > denominator (verified at source: fixture 1149592 has
     shots_inside_box 5 > shots_total 4) is not yet diluted, so >1 is a genuine data reality, not a
     model bug — clamping would hide it. The YoY cutoff N is low by construction early in every
     season, so it inherits the same split (the caught round-3 gap). The whole-season test keeps
     its strict [0,1] (dilution holds at season scale). Both bounds still catch real defects
     (a structural ratio >1, or any ratio <0). Whether the display layer should ever surface a
     provider-subset ratio >1 mid-season is a downstream product/legibility call, deferred to the
     Stats-tab build (this data layer stays honest — never clamps).

decisions_reserved:
  - "NAME of the new cumulative model (proposal: int_team_season__metrics_cumulative) — a naming
     call; surfaced in the plan-back for CPO ok."
  - "Exactly which metrics get aligned YoY: the ~13 displayed rate metrics (goals/goals-against/
     shots/danger-zone/SoT/finishing/passes/pass-acc/corners/corners-against/save/key-passes/
     duels/duels-won/defensive-actions per metrics_display), plus the existing 3 totals kept as-is.
     The T·I·B atoms feed defensive_actions only (not their own YoY), mirroring the display. Confirm set."
  - "Cumulative model materialization (table like the sibling, vs view) — an analytics call; table
     unless the per-matchday row count argues otherwise."
  - "Whether a new invariant DQ test is warranted (e.g. cur/prev computed through the same N; the
     byte-identity is already covered by the existing downstream suite) — analytics-engineer call."

done_when:
  - The new cumulative model builds; int_team_season__metrics = its final-row projection and is
    BYTE-IDENTICAL (ci-data-build DQ suite on all 6 consumers green — no number drift).
  - int_team_profile__yoy carries matchday-aligned this/prev/delta for every in-scope metric;
    NULL on either side where coverage is incomplete through N; domestic-league only.
  - mart_team_profile carries the new YoY columns; the v2 team export auto-carries them
    (mart passthrough — confirm no export edit, or a minimal one).
  - ci-data-build GREEN (parse + build + full DQ). Required reviewers PASS (scope-auditor +
    analytics-engineer per review_routing.json for dbt_project/**); review.md diff_sha256 binds;
    CPO merges (I never merge).
  - Handover bullet added to .claude/active_work.md (artifact-only follow-up commit).

amendments: (none)
