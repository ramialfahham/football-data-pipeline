# Task contract — define `direction` for the 5 style team metrics (metric layer + fixture-bar mirror)

> Written on a CLEAN tree (branch `feat/team-metric-directions` off main @ 16b4e1c).
> CPO-directed this conversation 2026-07-20: the v2 team Stats "vs the league" verdict view must show
> NO `neutral` metric — "we shouldn't allow neutral classification. It has to be clearly defined as
> better or worse" — then "define the direction in the metric layer first" + "adjust the fixture bars
> accordingly." CPO chose (AskUserQuestion) "Give each a direction" over dropping the style metrics.
> See docs/working_agreement.md §1 (E→P→C→I→V), §2, §10, §11, Appendix A;
> feedback: [[feedback-metric-catalogue-governance]] [[feedback-v2-design-schema-first]].

objective: >
  Set a real performance `direction` on the 5 team metrics currently classified `neutral` in the
  metric catalogue (passes/duels/defensive-actions/corners → higher_better; corners-against →
  lower_better), aligning `direction` to the long-standing `lower_is_better` boolean (only dropping
  the v2 `neutral` abstention), and update each `interpretation` to state the good direction. Mirror
  the same 5 directions on the fixture comparison's display config (metricRows.ts). The metric layer
  becomes the source of truth for the good/bad reading so the team Stats "vs the league" view and the
  fixture bars render every metric as clearly better or worse (green = beats the league median).

refs: >
  The team Stats-tab design (this conversation) · metrics_display.md (fixture comparison contract) ·
  [[feedback-v2-design-schema-first]] Stats-tab section. Design-driven; no issue number.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv        # direction + interpretation for the 5 team metrics
  - site_v2/src/lib/metricRows.ts                 # mirror the 5 direction values (fixture bars)
  - .claude/task/**
  - .claude/active_work.md

impact_map: >
  writers: none — a seed VALUE change (the `direction`/`interpretation` cells of 5 existing rows; no
    new column, no row added/removed) + a frontend display constant. No model/raw/ingestion touched.
  downstream (evidence: `grep -r direction` over dbt_project + scripts, every hit READ; dbt CLI is
    broken locally so no `dbt ls`): every consumer of the catalogue `direction` is direction-AGNOSTIC
    or non-breaking —
      - mart_team_competition_benchmarks.sql + mart_player_competition_benchmarks.sql: "DIRECTION-
        AGNOSTIC by design" (rank by metric_value DESC; good/bad applied at DISPLAY from the catalogue
        direction). No output/number change; benchmark DQ tests unaffected.
      - tests/assert_team_metric_meaning_complete.sql: FAILs only if direction OR interpretation is
        NULL/empty — the 5 stay non-empty (neutral -> higher/lower_better). Still passes.
      - seeds/schema.yml: `direction` accepted_values [higher_better, lower_better, neutral] — new
        values in-set. Still passes.
      - mart_head_to_head.sql: does NOT use metric direction (H2H record facts only).
      - shared.yml: `direction` appears only in column DESCRIPTIONS (still accurate). No test.
      - scripts/export_metric_definitions_json.py (LIVE MVP): reads `lower_is_better`, NOT `direction`
        — UNCHANGED, so the live MVP good/bad reading is untouched.
      - scripts/export_site_data.py (v2): direction "applied at render"; the mart carries no direction
        column — no payload change.
      - site_v2/src/lib/metricRows.ts: the fixture comparison's hand-mirror of the catalogue direction
        — the 5 rows now show a green better-side (display only; sample fixture data unchanged).
  layer_rules: seed change (no dbt model layer touched; check_layer_contract N/A). metricRows.ts is
    DISPLAY CONFIG whose own header says `direction` mirrors metric_catalogue.csv — keeping them in
    lockstep is the rule.
  deploy_order: NO prod number moves (direction is a display semantic; benchmarks agnostic; live MVP
    reads lower_is_better). Nothing breaks the deployed model on the 04:00 nightly. ci-data-build
    (shared prod dataset, full DQ suite) is the byte-safety gate.
  blast_radius: ZERO number change anywhere. The good/bad reading of the 5 metrics flips from "no
    verdict" to a verdict — a green better-side on the fixture comparison for those rows, and the
    catalogue becomes the SoT for the not-yet-built team Stats "vs the league" view.

decisions_taken: >
  1. CPO ruled (this session): the team Stats "vs the league" verdict view must not classify any
     displayed metric `neutral` — every metric reads clearly better or worse. CPO chose (AskUserQuestion)
     "Give each a direction" over dropping the style metrics, then directed "define the direction in the
     metric layer first" + "adjust the fixture bars accordingly."
  2. Direction values ALIGN to the existing `lower_is_better` boolean (passes/duels/defensive-actions/
     corners: lower_is_better=false -> higher_better; corners-against: lower_is_better=true -> lower_better).
     Not a new football judgment invented here — the boolean (which the live MVP already reads) has
     classified these all along; we only drop the v2 `neutral` abstention and make `direction` consistent.
  3. FOOTBALL-HONESTY OVERRIDE (CPO-accepted; flagged for football-analytics-expert-reviewer):
     higher_better on duels_per_match + defensive_actions_per_match is a VOLUME signal — a possession-
     dominant side that duels/defends less reads "below par" despite being strong (the reason the
     catalogue authors chose `neutral`). The CPO chose display clarity (a clear verdict) over the
     abstention. The interpretation text keeps the volume caveat honest. §10 metrics decision the CPO
     ruled in-conversation (recorded in escalations.log) — the reviewer's expected objection is
     documented, not re-litigated.
  4. `lower_is_better` is NOT touched (retained until the full migration; the live MVP depends on it).
     T/I/B atoms (tackles/interceptions/blocks) + sot_rank_gap stay `neutral` (not verdict bars).
  5. INTERPRETATION SWEEP (CPO-directed 2026-07-20, same PR): after the direction-is-judgement framing
     was settled ([[feedback-metric-direction-judgement]] — `direction` is "all else equal, is more
     better?", NOT a rank/results correlation), the CPO asked to review the `interpretation` text of ALL
     metrics and adjust where applicable. Revised the volume/style interpretations to LEAD with the
     direction reading and keep the honest style/volume caveat SECOND (shots_per_match + the 5 style
     metrics). The rest were reviewed and already lead with the judgement (kept as-is). Neutral metrics
     (T/I/B atoms, sot_rank_gap, contribution_share, the deferred player per-90 volume metrics) keep
     their neutral/no-verdict interpretation, consistent with their neutral direction. No further
     direction flips.

decisions_reserved:
  - "Player per-90 volume analogs (passes_per90, tackles_per90, interceptions_per90, blocks_per90,
     defensive_actions_per90, duels_won_per90, saves_per90) stay `neutral` — out of scope; a consistency
     call for when the player page is designed. Do NOT touch here."
  - "The exact interpretation WORDING for duels/defensive-actions (volume-caveat phrasing) — the
     football reviewer may refine; the CPO has the final call. Not a blocker to the direction."

done_when:
  - metric_catalogue.csv: the 5 team rows carry the new `direction` + a consistent `interpretation`;
    `neutral` no longer appears on those 5 rows (grep-verified).
  - metricRows.ts: the same 5 rows carry the mirrored `direction`; compiles (ci-site-v2).
  - ci-data-build GREEN (seed loads; assert_team_metric_meaning_complete + accepted_values + the full
    DQ suite pass; no number drift — benchmarks are direction-agnostic).
  - ci-site-v2 GREEN; the fixture sample renders a green better-side on the 5 rows (Browser spot-check).
  - Required reviewers PASS: scope-auditor + analytics-engineer-reviewer + football-analytics-expert-
    reviewer (metric_catalogue.csv) + cto-reviewer (site_v2/**), per review_routing.json. review.md
    diff_sha256 binds; CPO merges (I never merge).
  - Handover bullet added to .claude/active_work.md.

amendments: (none)
