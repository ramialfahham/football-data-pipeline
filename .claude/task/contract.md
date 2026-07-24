# Task contract — PR-A: minutes_per_appearance on the career mart (Squad tab warehouse prep)

> Written on a CLEAN tree (branch `feat/player-mins-per-appearance` off main at 60900f7, after #813
> merged and deployed). This is the warehouse half of the Squad-tab build; the build PR (PR-B: export
> + frontend + sample) follows once this deploys through ci-data-build.

objective: >
  Add `minutes_per_appearance` = `safe_divide(minutes, appearances)` to `mart_player_career`, and
  register it in `metric_catalogue.csv`. This was deferred out of #813 because its denominator
  (`appearances`) was counting matchday selections; #813 fixed and deployed that, so the ratio can now
  be computed on a correct denominator (matches actually PLAYED). The Squad tab renders "mins/app" from
  this column with zero derivation in the export or the frontend (a ratio is a fact — the consumption
  layer may not compute it).

refs: >
  Plan `C:\Users\Rami\.claude\plans\fuzzy-roaming-zebra.md`. #813 (merged) fixed `appearances` to
  `countif(minutes_played > 0)` warehouse-wide and shipped `minutes`. Verified in prod after that
  deploy: 26,657 zero-appearance rows now exist, so this ratio is null for them (safe_divide by 0) —
  which makes the null-safe DQ test below non-vacuous, unlike when the mart was appearance-gated.
  `minutes_played` is a real column of `int_legs__player_match` (the catalogue base_relation).
  CPO authority for the catalogue row: AskUserQuestion 2026-07-23 — "Catalogue it now" + "Ship minutes
  only, fix apps next" (see decisions_taken (1)).

scope_paths:
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/metric_catalogue.csv
  - .claude/active_work.md

impact_map: >
  writers: `mart_player_career.sql` is the only writer; it computes the ratio inline via safe_divide
    from its own `minutes` and `appearances` (both already present). No upstream model changes.
  downstream: `mart_player_career` is a LEAF mart (grep: zero `ref('mart_player_career')` in models).
    The only consumer is `scripts/export_site_data.py` via `select *` + `_shape_career_row`, which picks
    columns by name — the new column is ignored until PR-B wires it. No consumer breaks on merge.
  metric_catalogue_seed: one added row (`minutes_per_appearance`, player) — governance registration,
    NOT a code path (the season-metric engine reads the catalogue as documentation, verified in #813).
    base_relation `int_legs__player_match`, numerator `sum(minutes_played)`, denominator
    `countif(minutes_played > 0)` — the same played-legs definition as the corrected `appearances`, so
    the catalogue formula and the mart column agree. Denominator uses `countif(minutes_played > 0)` not
    `count(*)` (bench legs excluded) and NO coalesce (null > 0 is already not-counted), keeping the
    *_expr free of null-gates per the standing rule. Satisfies all five catalogue guards (resolvable:
    both tokens resolve; unique (metric_id, entity); direction + interpretation present; direction
    `neutral` agrees with lower_is_better false). DEFERRAL NOTE: on a PR the catalogue singular guards
    run against MAIN's seed via --favor-state, so this row is validated on main's next build
    post-merge — the normal flow for a catalogue value change; all five checked by hand.
  layer_rules: marts + a catalogue seed row. `check_layer_contract.py` passes. `minutes_per_appearance`
    is a derived RATE, so it is catalogue-governed (analytics-engineer ruling on #813); `minutes` and
    `appearances` remain uncatalogued dimensions.
  deploy_order: additive `table` rebuild. On merge, ci-data-build recomputes the column; PR-B waits on
    this deploy before re-exporting the committed sample.
  blast_radius: bounded / additive. One new column on a leaf mart + one catalogue row. No existing
    number moves; nothing renamed or dropped. The 26,657 never-played rows carry a null ratio (correct
    — no mins/app without an appearance).

decisions_taken: >
  (1) CATALOGUE `minutes_per_appearance` — CPO authority (both AskUserQuestion, 2026-07-23):
      "Catalogue it now" (the metric IS catalogue-governed, after the analytics-engineer ruled the same
      on #813), then "Ship minutes only, fix apps next" (defer it until the appearances denominator is
      fixed). #813 fixed and deployed that denominator, so this PR now executes exactly that authorised
      sequence: catalogue the ratio, on the corrected appearances. Not a new decision — the recorded
      one, carried out.
  (2) Catalogue attributes: entity=player, base_relation=int_legs__player_match,
      numerator=sum(minutes_played), denominator=countif(minutes_played > 0), format=decimal_0 (a
      divided value like every other ratio row — `integer` is only for undivided sums, and safe_divide
      returns FLOAT64; renders identically to integer per site_v2 format.ts), direction=neutral,
      lower_is_better=false. `neutral` because mins/app is a role/playing-time read with no better/worse
      pole (a full-90 regular is not "better" than an impact sub) — same call as contribution_share.
      The direction is the one domain judgement; PROPOSED for the football-analytics-expert to ratify
      (RATIFIED in review: they confirmed neutral).

decisions_reserved:
  - The `direction` of minutes_per_appearance (proposed neutral): a football-domain judgement the
    football-analytics-expert reviewer ratifies. If they rule higher_better, that is a one-value change.
  - PR-B (export + frontend + sample re-export + i18n/types/tests) waits on this deploying.

done_when:
  - `mart_player_career.sql` selects `safe_divide(minutes, appearances) as minutes_per_appearance`.
  - `shared.yml` documents the column + a null-safe DQ test (null iff appearances = 0, non-negative
    otherwise).
  - `metric_catalogue.csv` carries the row with the attributes in decisions_taken (2).
  - `python scripts/check_layer_contract.py` passes; YAML parses.
  - `ci-data-build` GREEN: dbt build + DQ pass (dbt + SQLFluff do not run locally — CI is the gate;
    catalogue guards validate post-merge).
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments: (none)
