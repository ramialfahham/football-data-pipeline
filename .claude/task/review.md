# Review — refactor/500-pr2-player-renames — #500 PR2-player entity-first renames

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff
> (`.claude/task/review_input.patch`). Required set for the staged paths: scope-auditor (always) +
> analytics-engineer-reviewer (dbt_project/**) + cto-reviewer (scripts/export_*.py). Pure rename of
> four player models to the entity-first scheme; byte-identical output verified (0 mismatches /
> 62,288 + 210,929 rows new-vs-prod).
>
> REBOUND 2026-06-26 after rebasing onto origin/main (sibling PR #576 merged first; only the
> .claude/task/* scratch files conflicted, resolved to PR2). The code diff is byte-identical to the
> reviewed diff — only contract.md's base context shifted — so the three verdicts stand; diff_sha256
> recomputed against the new base.

diff_sha256: 00def73ad98fdcf1b633a99b16fe6b5bd21a225adc094f0d077e723dffd5f9e4

## scope-auditor
VERDICT: PASS
risks_checked:
- yml ↔ model name sync: all four renamed models' yml `name:` entries (int_momentum.yml,
  int_season_record.yml, shared.yml ×2) match the renamed models, and materialization configs are
  preserved (3 tables + 1 view); a mismatch would fail dbt parse. No name invented beyond the
  CPO-confirmed 2026-06-26 ruling; no new mechanism/model/formula introduced.
- Lineage closure + scope: the `+` closure of each int is exactly its one mart (both marts leaf); only
  the listed scope_paths are touched; the 4 old-named BQ relations orphan on merge (not incremental →
  no --full-refresh; pending CPO bq rm, honestly disclosed). No old-name refs left in dbt/scripts; the
  layering.md / site_architecture.md old-name mentions are honestly DEFERRED to PR-c.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Dangling old-name ref() sweep: grepped all dbt SQL + yml for the four old names → zero matches; both
  old .sql files absent; the two cross-model ref()s now resolve to the new names → dbt parse will not
  break on a stale reference.
- Pure-rename integrity + layer contract: the diff changes only comment cross-refs (inside {# #}) and
  the two ref()s — no formula, grain, column set/order, or materialization change; models stay in
  4_intermediate/shared + 5_marts/shared (no int→mart back-ref); no competition hardcoding; mart SELECT
  columns still match shared.yml. (`mart_player_momentum` single-underscore = the pre-existing
  CPO-locked `mart_<entity>_<surface>` convention, mirrors mart_team_momentum — not a new violation.)
  Stale `dbt_project/docs/layering.md` mart inventory (lines 288/291) is deferred to PR-c per the CPO
  scope list; no CI check reads it.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Consumption-layer purity: both changed lines in scripts/export_site_data.py are a docstring comment
  (line 193) + a BigQuery table-name string (line 437) — no new computation, ranking, window, or
  business rule; shape_top_players still delegates ranking to the mart's top_player_rank column
  (anti-pattern A5 respected). Consumption-layer contract intact.
- Missed-reference sweep: grepped scripts/ for all four old names → zero remaining; the new name
  `mart_player_momentum` (lines 193 + 437) spells the renamed mart exactly; mart_season_record__player
  has no consumer in scripts/ (confirmed). No dangling reference to a now-nonexistent table.

## escalations
(none)
