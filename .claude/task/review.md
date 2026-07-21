# Review — feat/metric-layer-meaning-gates (TASK 0 part 1, VALUES ONLY) — 2026-07-21

> Re-scoped from the original single-commit PR #681, which shipped the seed values AND both guards and
> went red in CI for a stale-read reason (see `contract.md` objective). The commit is now values only.
> Required reviewers per `.claude/review_routing.json`: scope-auditor (always) ·
> analytics-engineer-reviewer + football-analytics-expert-reviewer
> (`dbt_project/seeds/metric_catalogue.csv`).
> scope-auditor re-ran on the SPLIT and PASSes. The other two PASSed the identical seed content before
> the split and their verdicts carry: the seed bytes did not change during the restructure, only which
> commit they ship in. Their round-1 findings and the fixes are preserved below.

diff_sha256: 8bc7a425dd05432e661f17f1a3fc60793be5ab3ab0103565304a7aef9e6d4006

## scope-auditor
VERDICT: PASS
risks_checked:
- Split legitimacy — is this evading a gate? Re-derived the mechanism from `.github/workflows/ci-data-build.yml:216-223`: `dbt test --select test_type:singular --defer --favor-state` defers every node not selected, `dbt test` can only select TEST nodes, so `ref('metric_catalogue')` resolves to the state manifest compiled from main at the prod target and the new guards read main's pre-PR values. Measured, not theorised: prod's seed carries exactly the 28 blank-meaning rows and the 4 disagreements that CI reported. The split dissolves it — part 1 lands values only so nothing depends on data not yet on main; its main-push build runs `dbt seed --target prod`; part 2's CI then reads an already-correct main. Legitimate architecture, not scope evasion.
- The CPO's three-step ruling survives. (a) the 28 values and (c)'s 4 corrections are in part 1; (b) the widened guard and (c)'s lockstep guard are part 2. The order and the content are unchanged; only the commit boundary moved. The handover states the sequencing as load-bearing and warns explicitly against pushing part 2 early.
- Revert completeness — a protected-workflow edit plus `seed_only` tags on three test files had been staged earlier and then abandoned. Confirmed NOTHING survives: no `dbt_project/tests/*.sql`, no `dbt_project/seeds/schema.yml`, no `.github/workflows/` path is in the diff. The five changed files are exactly the contract's `scope_paths`.
- Seed content integrity across the restructure. Verified all 28 `interpretation` cells are filled and all 4 `lower_is_better` booleans are `true` beside `direction=lower_better`; 78 rows x 14 columns, no row added or removed. Byte-identical to what the other two reviewers passed, including the three wording corrections the football reviewer forced in round 1.
- `done_when` fidelity — every clause is satisfiable by THIS commit; nothing in it demands the guards that ship in part 2.
- Handover sufficiency for a cold chat — part 2's existence, its branch name, the mandatory ordering, the reason, and the explicit "do not resurrect the workflow fix" are all recorded, with the CPO's own words. No surviving statement claims the guards have landed.
- No §10 decision is taken here. `direction` as the authority and the `interpretation` house style were both CPO-decided in the session brief; the split is a sequencing call, not a product, metric, naming or permanence decision.

## analytics-engineer-reviewer
VERDICT: PASS
> Verdict carried from the pre-split review of byte-identical seed content. The restructure removed
> files from the commit; it changed no cell of the CSV.
risks_checked:
- Full 78-row truth-table walk of every `(lower_is_better, direction)` pair, not a sample. After the fix all 78 agree (`lower_better` to `true`; `higher_better`/`neutral` to `false`, including both `neutral` rows).
- CSV integrity across all 32 changed cells: 78 rows x 14 columns preserved, header unchanged, no raw comma / em dash / double quote / trailing period introduced, and no non-target column moved — `base_relation`, `numerator_expr`, `denominator_expr`, `direction`, `format`, `metric_group`, `importance_tier`, `group_display_order` byte-identical on every touched row.
- Consumption-layer independence re-derived directly from `scripts/export_metric_definitions_json.py` and `site/match-preview/metric_bindings.csv` rather than from the contract's claim: none of the four corrected rows is bound, so `metric_definitions.json` is unaffected.
- Catalogue governance: the diff edits the SSoT itself — grep-confirmed that no model, mart or export recomputes or overrides `interpretation` or `lower_is_better`.
- FINDING (r1, non-blocking, ACTED ON): the contract's out-of-scope note claimed all four colliding metric ids agree on the three fields the export reads. True only of the two BOUND ids (`finishing_efficiency`, `duels_won_pct`); `goals_penalty`/`goals_open_play` differ on `label_i18n_key` but are never looked up. Corrected in `.claude/active_work.md` and now stated precisely in `contract.md` out_of_scope.
- NOTE for part 2: this reviewer's `seeds/schema.yml` findings applied to prose that has MOVED to part 2 and must be re-checked there, not here. This commit contains no `schema.yml` change, so nothing false is published through `dbt docs generate`.

## football-analytics-expert-reviewer
VERDICT: PASS
> FAIL round 1, PASS round 2. Verdict carried from the pre-split review of byte-identical seed content.
risks_checked:
- All four `lower_is_better` flips (`cards_yellow`, `cards_red`, `cards_total`, `shots_on_goal_against`) verified football-correct as `lower_better`. Every one of the 78 rows' directions re-checked against what its formula actually measures; no fifth row is football-wrong.
- Each of the 28 new interpretations checked against its own `description`, its `numerator_expr`/`denominator_expr`, its `direction`, and its per-90 or team-level sibling.
- FAIL r1, three findings, ALL upheld and fixed in this seed:
  1. **`duels_won` overclaimed.** "wins the ball back and holds it up" is defensively coded and names a target-forward skill, but a duel here pools ground and aerial contests including attacking duels, and the unchanged `duels_won_per90` reads neutrally on the same stat. Replaced with "physical 1v1 contests won in the window; high = comes out on top in physical battles".
  2. **`saves` contradicted itself.** It claimed "a busy and effective keeper" from raw volume while its own parenthetical conceded the opposite, and `saves_per90` is explicit that volume is not shot-stopping quality — the "reflects the defence rather than the keeper" trap. Replaced with "a busy keeper facing plenty of work", and the caveat clause taken verbatim from `saves_per90` so the family states one thing in one wording. The reviewer confirmed this is MORE honest than its own proposal, since it states the quality gap rather than implying it.
  3. **`passes_total` was missing the minutes caveat** every sibling raw-count row carries. Added verbatim.
- r2 re-verified the three replacements and found no new inconsistency against the per-90 family or the team-level rows.

## escalations
(none — the `lower_is_better` resolution and the `interpretation` house style were CPO decisions taken in the session brief; the three football findings were detail-level corrections fixed with judgment per [[feedback-decide-dont-escalate]]; the split was CPO-directed after rejecting the workflow fix)
