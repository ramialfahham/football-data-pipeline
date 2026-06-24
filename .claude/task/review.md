# Review — refactor/500-metric-layer-naming — 2026-06-24 (PR-a)

> G3 review artifact. PR-a of the non-gated #500 metric-layer consolidation:
> catalogue restructure + metric-layer renames + v2 consumers + CSV-corruption repair.
> Four reviewers required by review_routing.json for the staged paths (scope-auditor
> always; dbt_project/** + scripts/export_*.py + metric_catalogue.csv route the rest).
> No guard path touched, so cto stays on its pinned model.

diff_sha256: d288b2296fb704ae331604b82dda464a289e12db61cf9df9cd62a42f014c77b9

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope drift: every edited file is within `scope_paths`; all out-of-scope live-chain and atom-layer files are untouched; contract.md change carries recorded CPO authority (active_work.md 2026-06-24 lock + 2026-06-25 non-gated correction). No edit exceeds the lock.
- De-dup entity-join correctness + column-rename traceability: catalogue carries exactly one `finishing_efficiency` and one `duels_won_pct` row (entity `team and player`); the no-drift guard's OR clause resolves each model entity to exactly one row; the 8 renamed columns are consistently updated through int → benchmark macro → mart → export with no stale references and no formula change (Appendix A1–A6 all clear).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `mart_momentum__team` (line 54) still emits `shots_on_target_per_match` but reads from `int_momentum__team` (the atom chain), NOT the renamed `int_team_season__metrics`; it is an out-of-scope live-boundary mart whose rename is deferred to PR-d (D1). Not a broken consumer; no BQ break in the PR-a graph.
- No-drift guard: removing the `goals_saves→saves` normalisation is safe because `int_player_season__metrics` now outputs the literal column `saves`; the `team and player` OR clause covers `finishing_efficiency`/`duels_won_pct` for both passes; CSV repair restores `dribbles_success` and `goals_against` as their own 13-column rows; `save_pct` and `finishing_efficiency` formulas use the same atoms (numbers unchanged — only aliases renamed).

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- `finishing_efficiency` de-dup (numerator `goals_for→goals`, entity → `team and player`): goals/shots-on-target is mathematically identical for team and player; the >100% caveat (penalties/own goals) and the null-when-zero case are retained in the surviving description; no football-meaningful distinction lost. CPO-locked (D2).
- `goals_against` (player, repair): `lower_is_better=true` is football-correct for a conceded stat; description honest ("GK-relevant"); atom unchanged. `shots_on_goal_against` derived as saves+conceded is the exhaustive partition of SoT faced (`lower_is_better=false` correct for a volume denominator). Stale `label_i18n_key` flagged as the recorded D5 deferral, not a silent error.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `export_site_data.py` is the v2 export, NOT the live Pages deploy: docstring (lines 1–9) states it is gitignored/isolated, and it is absent from `.github/workflows/pages-match-preview.yml` `paths:` (which lists every live-chain script). So the renamed literal refs cannot break the live MVP (premise D4 holds).
- The two renamed refs (`shots_on_target→shots_on_goal` in `_LEADERBOARD_METRICS`/`_LB_KEEP`) match what `mart_leaderboards` now emits at all three levels (count_boards key, intermediate select, final select); grep finds no other stale metric-id literal; player-profile/match-log paths use `select *` so other renamed columns forward transparently; no workflow file touched.

## escalations
(none)
