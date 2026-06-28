# Task contract — formalize the metric_catalogue formulas (structured, resolvable)

objective: >
  Make every metric's formula precise and resolvable in metric_catalogue.csv: add a `base_relation`
  column (the int_legs__* per-(entity,fixture) building block the metric aggregates over) and replace
  the loose prose `numerator`/`denominator` with precise `numerator_expr`/`denominator_expr` over that
  base's REAL columns. Fill all 71 rows by transcribing each metric's EXISTING computed formula from
  the canonical model (int_team_season__metrics / int_player_season__metrics) — documenting what is
  already calculated, NOT changing any metric's meaning. Doc-only columns → no shipped-number change.

refs: >
  CPO-directed this session: the catalogue lacked the "how it's calculated"; a metric is one universal
  formula (window/entity are just inputs), so it belongs stated once, precisely, as the correctness
  contract every model must conform to. CPO chose the structured encoding (base_relation +
  numerator_expr + denominator_expr). Supersedes the labeling-gate approach to #530 (reshaped: a cheap
  resolvability check follows in PR2). Plan: ~/.claude/plans/goofy-crafting-ritchie.md. Governance:
  metric-catalogue-governance (the seed is the SSoT; formula meaning is football-analytics + CPO).
  numerator/denominator verified DOC-ONLY (no script/site/model consumer).

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - .claude/task/**

impact_map: >
  writers: metric_catalogue.csv (seed) — add base_relation; rename numerator/denominator →
  numerator_expr/denominator_expr; fill 71 rows. seeds/schema.yml — column docs + base_relation
  accepted_values.
  downstream: numerator/denominator are DOCUMENTATION-ONLY — grep across scripts/, site/, and dbt
  models shows no consumer reads them (only dbt_utils package internals, compiled target/ artifacts,
  and the schema doc). Renaming/filling them changes no compiled SQL, no mart output, no export
  payload, no site value. Models that ref('metric_catalogue') (the drift tests) read metric_id/entity,
  not these columns.
  layer_rules: seed = configuration / SSoT (the correct home for metric definitions). No model logic
  touched; no layer boundary crossed.
  deploy_order: seed is full_refresh; `dbt seed` reloads a wider table. No migration, nothing to
  backfill. The expressions document what the models already implement; no model rebuild needed.
  blast_radius: adds one column + precise expressions to the metric SSoT. NO shipped number moves
  (doc-only columns). Reversible. The one real risk is a TRANSCRIPTION error (a formula that does not
  match what the model computes) — mitigated by transcribing from the canonical model + a manual
  resolvability spot-check + football-analytics review.

decisions_taken: >
  Structured encoding (CPO). base_relation is always an int_legs__* leg (int_legs__team_match /
  int_legs__team_from_players / int_legs__player_match) or blank for non-leg lookups (league_rank is
  sourced from fct_standings, noted in description). Expressions are window-free aggregates over real
  leg columns (sum(...)/count(*)). Rename numerator/denominator → *_expr (safe — doc-only). Transcribe
  the EXISTING formula; do NOT change any metric's definition. A model-vs-catalogue discrepancy is
  FLAGGED to the CPO, not silently reconciled. CPO RULING (2026-06-28): a metric's formula is its
  fixed mathematical definition; data availability decides only whether a model can APPLY it (compute
  vs null) and is NEVER encoded in the expression — so per-match denominators are count(*) (number of
  matches in the window), NOT coverage counts, and no expression carries coalesce/countif/null-gates.
  (This resolves the reviewers' "count(*) infidelity" findings: those describe the model's
  availability handling, not the formula.)

decisions_reserved: >
  - The resolvability check (PR2) and model-conformance enforcement (later) — separate.
  - Any actual formula/definition CHANGE — out of scope; this PR only documents the current formula.
  - Divergent-column renames, the placement-standard doc, the momentum/record note — separate.

done_when:
  - metric_catalogue.csv has base_relation + numerator_expr + denominator_expr; 67 rows formalized;
    4 rows intentionally blank-deferred (the 2 entity-dual 'team and player' rows finishing_efficiency
    + duels_won_pct, and player goals_penalty + goals_open_play) per the CPO follow-up decision; every
    non-blank referenced column exists in its base_relation (spot-checked — all resolve).
  - seeds/schema.yml documents the three columns (base_relation accepted_values = the 3 legs; blank
    cells load NULL and are skipped by accepted_values).
  - mcp__dbt__parse clean (dbt MCP unavailable this session — deferred to CI). No model file touched;
    no shipped number changes.
  - football-analytics-expert + analytics-engineer + scope-auditor PASS; staged sha == review hash.

amendments:
  - 2026-06-28 (CPO "do as recommended"): defer 4 rows to follow-ups, committed with blank
    base_relation/numerator_expr/denominator_expr — the 2 entity-dual 'team and player' rows (split
    per entity) and player goals_penalty/goals_open_play (pending int_legs__player_match exposing the
    event-derived penalty-goal atom). Honors decisions_reserved; not a definition change.
  - 2026-06-28 (review + CPO ruling): schema per-90 denominator doc corrected (the * 90 sits in
    numerator_expr). The round-2 save_ratio "coverage-scoped" change and the null-safe SUM note were
    REVERTED per the CPO formula-vs-availability ruling above — save_ratio is the clean definitional
    sum(goalkeeper_saves) / sum(goalkeeper_saves + goals_against); availability is the model's concern,
    never the formula's. Per-match denominators stay count(*).
