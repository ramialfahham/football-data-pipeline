# Review — chore/drop-player-rating — 2026-06-18

> Machine-checked review artifact (governance G3, step 4 Lock). Blinded reviewers
> required by .claude/review_routing.json for the changed paths: scope-auditor (always),
> analytics-engineer-reviewer (dbt_project/**), bi-analyst-reviewer (docs/wireframes/**).
> All PASS; no FAIL; no ESCALATE.

diff_sha256: 1a2683c90640cff4b3c9243820152a3e8756047efb145d53ba7cd66b99693639

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope containment: every touched path is within the contract's scope_paths; the contract.md rewrite is the expected task-boundary replacement; no refactoring or unrelated field change rode along (line-by-line diff vs the scope list).
- Column-removal integrity: only `rating`/`rating_avg` were removed across staging -> base -> core -> intermediate -> marts; all other output columns remain (mart_player_season still emits player_sk, season_sk, goals, assists, pass_accuracy_pct, cards, etc.) — no collateral schema change.
- §10 authorization: removing a shipped field is a §10 product change; the contract records it as a CPO decision (2026-06-18), not unilateral; the doc/comment/mockup edits are mechanical follow-through, not new design calls.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Dangling reference end-to-end: grepped all .sql/.yml/.py/docs for whole-word `rating`/`rating_avg` — zero surviving matches map to the removed column; `mart_player_profile` (a consumer of int_player_season__metrics, not in the diff) was read directly and does not select `rating_avg`.
- Incremental fact safety: `fct_fixture_player_stats` keeps `on_schema_change='sync_all_columns'` and its `unique_key` (fixture_player_stat_sk) is untouched, so dbt drops the column from the target on the next run with no row loss/dup; the select lists are clean (no trailing comma at any removal site).
- Catalogue/consumption: `rating`/`rating_avg` confirmed absent from all seeds (no catalogue row to amend — A1 clear); no scripts/export bridge was introduced to compensate for the removal (A5 clear).

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Locked display contract: `docs/wireframes/metrics_display.md` has zero `rating` references and the 9 locked player bundles never included it; removing rating from the wireframe does not disturb, reorder, or alter the locked table.
- Dangling wireframe reference: post-patch the only surviving "rating" token in 03_player_profile.md is "no composite ratings (locked)" (a design constraint, not a JSON key); the §5 binding tables, the match-log row, and the removed "Null rating" state carry no rating field.
- i18n/export sweep: no `rating` key in site/i18n/{en,de,fi}.json; no `rating` in scripts/ or site_v2/src/ — the contract's "no site/i18n/export references" precondition verified in the post-patch state.

## escalations
(none)
