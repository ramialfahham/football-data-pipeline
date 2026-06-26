# Review — docs/metric-ssot-consolidation — #500 PR-c (metric-definition SSoT consolidation)

> G3 Lock artifact. Three reviewers spawned cold (blinded) on the staged diff
> (`.claude/task/review_input.patch`). Required set for the staged paths: scope-auditor (always) +
> analytics-engineer-reviewer (`dbt_project/**`) + bi-analyst-reviewer (`docs/wireframes/**`). The
> seed (`metric_catalogue.csv`) is deliberately untouched, so football-analytics-expert is NOT
> required. Docs + provenance-comment consolidation; the commit carries contract.md (not artifact-exempt).

diff_sha256: ea792d7421dfed9974dc0657adad6eccc7a47c6f646f610c2d25407b8559cbef

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed file is within the contract's scope_paths (the 11 docs/model files + contract.md,
  including the `docs/player_metrics_catalogue.md` deletion); no out-of-scope edit / no drift.
- §10 decision-rights: no metric definition/formula, product/UX, permanent-naming, or NEW-mechanism
  decision taken without authority. The seed-crowning + retiring `player_metrics_catalogue.md` are the
  explicitly CPO-approved core; the mart-name updates are documentation corrections for the already-merged
  #574/#577 renames, not new naming decisions.
- CPO-LOCKED `metrics_display.md`: every edit is pointer-only (dead-doc repoint + deferral sharpened to
  name the seed + one stale model name); all display rulings preserved verbatim (the 8.5 reword in
  metrics_context_model.md is authorized by the "clear #577/#574 old-name debt" clause and leaves the
  ruling intact).
- Impact-map honesty (Appendix A6): the two `dbt_project/models/**` touches are comment/description-only,
  compiled SQL byte-identical, downstream evidenced via `dbt ls`, no rebuild — verified against the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Provenance repoint accuracy: `dbt_project/seeds/metric_catalogue.csv` carries every player atom the
  retired doc defined as canonical — scorer_points (goals + assists), save_pct (saves / saves+goals_against),
  duels_won_pct, pass_accuracy_pct (passes_accurate / passes_total), dribbles_success_pct — each with
  explicit numerator/denominator. The repoint of the SQL comment + yml description to the seed is therefore
  accurate; no definition loss.
- New mart names in `layering.md` map to real model files (`mart_player_momentum.sql`,
  `mart_player_season_record.sql` confirmed by glob); the old names have zero live source files; the
  export script already queries the new names → docs are in sync with the deployed state.
- The two model-file changes are comment/description ONLY — no SQL logic, no `ref()`/DAG change, no
  materialization change, no metric column added/renamed; the consumption layer (export) is a straight
  `select *` with no computation.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The locked team table (16 rows: groups/tiers/order) and the locked player rows table (9 rows: display
  strings, atomics, groups) are byte-unchanged; the diff only touches prose adjacent to those tables.
- All 12 rulings-log entries intact; the one changed entry dropped only the dead-doc attribution
  ("from `player_metrics_catalogue.md`" → "(legacy player catalogue)"); date + ruling substance verbatim.
- The mart-name fix (`mart_season_record__team` → `mart_team_season_record`) appears in exactly the three
  permitted locations (metrics_display.md GAP-10, 99_gaps_register.md GAP-10, 01_fixture_page.md §3b + footer)
  and matches the `layering.md` canonical inventory corrected in the same PR; the old name was the stale one.
- No i18n key, user-visible label, display format, or new metric/KPI introduced; the deleted doc's
  `playerMetrics.*` i18n keys were already declared superseded (CPO 2026-06-11, GAP-12).

## escalations
(none)
