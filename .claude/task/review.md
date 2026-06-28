# Review — feat/formalize-metric-catalogue-formulas — formalize metric_catalogue formulas

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff (`.claude/task/review_input.patch`).
> Required set (routing): always → scope-auditor; `dbt_project/**` → analytics-engineer-reviewer;
> `dbt_project/seeds/metric_catalogue.csv` → +football-analytics-expert-reviewer.
> Change: add `base_relation` + replace prose numerator/denominator with precise window-free
> `numerator_expr`/`denominator_expr` over int_legs__* columns; 67/71 rows formalized, 4 blank-deferred.
> Doc-only columns (no consumer) → no model SQL, no shipped-number change.
> CPO RULING (in contract decisions_taken): the formula is the fixed math definition; data
> availability is the model's compute-or-not concern, never encoded in the expression.

diff_sha256: 3458f03b3d98c40120c9bd16fdddac1f0b987a9da52748f118ab9c6d65f62cc4

## scope-auditor
VERDICT: PASS
risks_checked:
- Formula transcription accuracy across 71 rows: spot-checks (clean_sheets, goals_per_match, save_ratio,
  passes_accurate) matched the canonical models, but local dbt parse is unavailable this session
  (deferred to CI), so a single transcription error could slip past this cycle. Mitigated by the
  football-analytics-expert review (PASS, formula-by-formula) + CI dbt compile on the seed.
- Entity-dual rows (finishing_efficiency, duels_won_pct) blank-deferred rather than filling the
  extractable team side: a trade-off, but recorded in the contract `amendments` as a CPO follow-up
  (split per entity) — not a silent decision; tracked. The save_ratio revert + the 4 deferrals are all
  recorded in amendments; diff stays within scope_paths (the 2 seeds + .claude/task/**).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `count(*)` over `int_legs__team_from_players` (duels/defensive_actions/tackles/interceptions/blocks/
  key_passes per_match) counts only player-covered matches (the leg has a row only where player stats
  exist), a different domain than `count(*)` over `int_legs__team_match`. Per the CPO ruling `count(*)`
  is the definition and the model handles availability; flagged that the PR2 conformance check must key
  on `base_relation` (and on (metric_id, entity)).
- `passes_accurate`/`pass_accuracy_pct` (player) carry a BigQuery-dialect expression
  `sum(cast(round(passes_total * passes_accuracy_percent / 100.0) as int64))` — faithfully transcribed
  from `int_player_season__metrics.sql` but a structural fragility for any future dialect migration or a
  naive PR2 parser. Not blocking; resolvability confirmed (all non-blank expressions resolve against
  their base; blank-base rows carry no expression).

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- save_ratio: the catalogue uses raw `goals_against` from `int_legs__team_match` while the model uses the
  derived coverage-scoped `goals_against_in_save_games`; both resolve, are numerically identical at full
  coverage (model comment: 0/12537 divergence), and the difference is model availability-handling per the
  CPO ruling. Definition is football-correct (saves ÷ shots-on-target-faced = saves + goals conceded).
- Column aliasing across the team/player defensive boundary: `int_legs__team_from_players` renames the
  player atoms (`tackles_total`→`tackles`, etc.); the catalogue correctly uses `tackles/interceptions/
  blocks` for the team base and `tackles_total/tackles_interceptions/tackles_blocks` for the player base.
  Each expression resolves against its declared base. Compositions verified (defensive_actions, scorer_
  points, points_capture, finishing_efficiency, per-90) against the canonical models.

## escalations
(none) — the formula-vs-availability question is settled by the CPO ruling recorded in
`.claude/task/contract.md` (decisions_taken); no outstanding ESCALATE.
