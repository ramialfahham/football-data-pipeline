# Review — refactor/500-export-from-catalogue — point the live match-preview data at the catalogue

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff
> (`.claude/task/review_input.patch`). Required set for the staged paths:
> scripts/export_*.py → analytics-engineer + cto; dbt_project/** → analytics-engineer; tests/** → cto;
> site/match-preview/metric_bindings.csv matches no path pattern; always → scope-auditor; contract.md
> is artifact_only_never → commit not exempt. #500 PR-d step 2: invisible source swap (byte-identical).

diff_sha256: 724d78155b0ae3be91e2d4d880fc09782eb5576834c569d5b60d60b070587631

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + reserved-decision compliance: all 7 changed files are within scope_paths; nothing from the
  reserved later steps is folded in (i18n/labelling scheme, corners rename, team-season _season, the
  workflow trigger tidy — none in the diff); metric_catalogue.csv (the SSoT) is NOT in the diff (untouched).
- Decision rights (§10/§11): no new metric invented, no definition changed, no user-visible naming/wording;
  the diff merely executes the CPO-approved architecture (catalogue clean + wiring in a separate file). No
  unauthorized decision inside the diff.
- Byte-identity consistency: the generated JSON is absent from the diff, which (confirmed) means it did not
  change; the dual lock — the regen test + the fact any real change would surface as a JSON diff — prevents
  silent output drift.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Warehouse dependency isolation: `grep metric_definitions` across all of dbt_project/ returns zero matches
  after deletion; the `dbt seed` steps in ci-data-build.yml / dbt-scheduled.yml / pages-match-preview.yml
  just stop loading one table (no failure path). schema.yml is structurally valid after the block removal
  (clean transition between metric_catalogue and wc_team_market_value_snapshot).
- Byte-identity of the generated JSON: all 13 catalogue_metric_id values resolve in metric_catalogue.csv,
  and format + lower_is_better are identical to what the deleted seed carried (verified cell-by-cell against
  the patch's deleted rows). build_defs inserts entry keys in the same order as the old script
  (format → context → conditional lower_is_better → columns); render preserves
  `json.dumps(..., ensure_ascii=False, indent=2) + "\n"`. The regen test is a genuine byte-identity guard.
escalations: none

## cto-reviewer
VERDICT: PASS
risks_checked:
- Caller compatibility: both callers invoke with zero args (pages-match-preview.yml:129,
  export_matchday_insights.ps1:14); the rewrite drops --csv and adds --bindings/--catalogue/--out with
  defaults resolved from the repo root (cwd-independent), both default inputs exist — no caller breaks.
- Seed deletion breaks no CI/build: no dbt model refs the seed; `dbt seed` in all three workflows just omits
  one table; the stale `metric_definitions.csv` trigger line is dead-but-harmless; the new bindings file is
  covered by the existing `site/**` trigger.
- Script + test quality: deterministic field order (Py3.7+ insertion order; matches the committed JSON);
  idempotent write with mkdir(parents,exist_ok); fail-closed SystemExit on an unknown catalogue id; the
  regen test runs the real script via subprocess (sys.executable, cwd, tempdir) and asserts equality — a
  real guard. Stdlib-only; no new deps/secrets/mechanisms.
escalations: none

## escalations
(none)
