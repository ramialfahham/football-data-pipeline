# Review — feat/gap-18-tournament-form-window — 2026-06-16 (commit 1: mart layer)

> Commit 1 of a two-commit branch. The live form LABEL (`form_from_qualifiers` on
> mart_matchday_insights) is commit 2, under its own contract on a clean tree.
> Required reviewers (routing for the 15 staged paths): scope-auditor (always),
> analytics-engineer (dbt), cto (scripts), data-engineer (registry seed),
> bi-analyst (wireframes/gaps register). All PASS on this diff.

diff_sha256: 5cff336089bc4b6e6d72d83c498978f1749f966fbdbe6b05c695af93e8b34f11

## scope-auditor
VERDICT: PASS
risks_checked:
- UNION-branch WHERE scope: `where recency_rank <= 5` in int_momentum_window__team.sql binds only
  to the last branch (last5_window) in BigQuery; tournament_window/qualifier_window stay uncapped
  (cumulative). Load-bearing + fragile; the added comment warns against hoist/parenthesise, and
  assert_tournament_form_window independently validates the uncapped count. Correct.
- Parent-link dangling-reference validation: check_registry_var_sync.py `_registry_dangling_parents()`
  rejects any non-empty parent_competition that is not a known league_code before the sync compare —
  the only gate against a YAML typo silently emptying the qualifier window. Present and correct.
- Scope containment: every diff hunk is within scope_paths; `dbt_project/dbt_project.yml` is a
  legitimate (no-op this run) output of the contracted sync_dbt_vars.py; player window stays last_5
  (#484), qualifying stays last_5 (#483); window_type values + untouched season_to_date match
  decisions_taken; no new mechanism (registry seed via existing single-source sync).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Count-oracle independence (assert_tournament_form_window section B): expected_legs is recomputed
  from int_legs__team_match on (team_sk, league_code, season_api_year, kickoff) — mirrors tournament_legs
  — so a re-introduced 5-cap or wrong season filter makes games_in_window != expected_legs and the
  test fails. A genuine independent oracle; the list-vs-aggregate invariant alone could not catch a
  uniform under-count. entity_type omission is safe (WC/continental are always national).
- combined-CTE WHERE comment: the added comment correctly states BigQuery semantics (WHERE binds to
  the final UNION branch only) and names the DQ test as the guard. No new defect from the comment.
- (Prior round) season-cap relocation to last5_legs preserves the club season boundary; tournament
  and qualifier branches intentionally uncapped/season-scoped per the matrix; player path untouched.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Guard still fails when the seed drifts on the NEW column: check_registry_var_sync.py emits 3-tuples
  both sides; a parent added to the YAML but not synced (`sync_dbt_vars.py` not re-run) → triples differ
  → return 1. Fail-closed on the new column, not just the old pair.
- Dangling-parent rejection is independent of the seed and fires before the sync compare; a typo'd
  parent in the YAML fails CI even with a byte-perfect seed. Sync (`_registry_seed_rows`) and check
  (`_seed_triples`/`_registry_seed_triples`) use identical extraction; codegen is idempotent.
- No new mechanism / boring tech: third CSV column via the existing single-source sync, not a new
  Core dim; no requirements/workflow/secret/run-frequency change; model consumes the column via `select *`.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Seed fidelity vs registry: all 12 non-empty parent links (7× WCQ*→WC, CDF→L1, CDR→PD, CIT→SA,
  DFBP→BL1, FAC→PL) in competition_registry.csv match docs/competition_registry.yml exactly; all 45
  competitions with league_code+competition_type present; empty trailing comma for no-parent rows.
- Sync/check lockstep: the check now requires the parent_competition column (KeyError if absent) and
  validates triples + dangling parents; a future sync omitting the column fails CI. Single-source +
  zero-file rules intact (registry YAML is the source; seed is generated).

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- No overclaim: the GAP-18 gaps-register row says "mart layer landed" (not "implemented"), names the
  live WC form LABEL as "immediate follow-up", and the 01_fixture_page.md §5.3d GAP-18 caveat remains
  true (labels not yet derivable from the payload until commit 2). Numbers are now cumulative-correct;
  honest framing (games_in_window is the true count, the cap was the dishonesty).
- No silent drop of v2 work: form_window[] ≤5 cap and the separate `phase` column are explicitly
  attributed to #391; #483/#484 filed in decisions_reserved. No locked display contract value (metric
  table, i18n keys, labels) is altered in this diff.

## escalations
(none)
