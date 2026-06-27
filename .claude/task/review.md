# Review — docs/macro-standard-trim — trim §1.3 to a calibrated default

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff (`.claude/task/review_input.patch`).
> Required set: always → scope-auditor; `dbt_project/**` → analytics-engineer-reviewer.
> Documentation only — CPO-directed trim of §1.3 (Macros) from a rule/test framing to a calibrated default;
> keeps the plain-SQL default + COMPOSE + the two verified examples, drops the "test" line, closes with
> "beyond those it is the engineer's judgment."

diff_sha256: 53c826f5442649c4f21b349d29f77e1cbe8cc348139b3f455b4a8beef1c1745a

## scope-auditor
VERDICT: PASS
risks_checked:
- Consistency with the established macro preference: "default to plain SQL + COMPOSE" aligns with the
  documented feedback (dropping team_window_metrics in #500 PR1). Removing the rigid "test" line acknowledges
  judgment, but the two justified cases (override hook, cross-query expression) stay explicit, so the
  reframing does not open a loophole for bad macros; §10 still gates NEW mechanisms.
- Interaction with the shipped macro inventory: the existing macros (generate_schema_name override,
  apif_response_to_json_strings cross-query expression) fit the new framing; the trim does not retroactively
  invalidate them, and layering.md / §5 are unchanged. Scope clean (only engineering_standards.md + contract.md);
  faithful CPO-directed trim, no new §10 decision.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- generate_schema_name example — verified live at dbt_project/macros/generate_schema_name.sql: dbt's stock
  hook prefixes the target schema (e.g. dbt_scratch__staging); this override returns the custom name verbatim
  so layer models land in `staging`/`base`/etc. "default would name datasets wrong" is accurate; not dead code.
- JSON-expansion example — apif_payload_response_json_strings (dbt_project/macros/apif_response_to_json_strings.sql)
  is used in three staging models (stg_apif__fixtures_next/teams/leagues, line 16) inside
  unnest({{ ... }}) — a correlated subquery producing ARRAY<STRING> that must sit inside the from/unnest, so it
  cannot be a standalone model. The "expression that must sit inside other queries" framing is accurate.
- §5 cross-reference (soft): "see §5" lands on Performance Standards, which states "centralize once in
  intermediate if reused" (the same idea) but does not name COMPOSE — documentation imprecision, not a false
  technical claim; the COMPOSE guidance in §1.3 is self-contained and sound (live exemplar:
  int_team_competition_benchmark_metrics_long read by both the engine and the mart). Not a defect.

## escalations
(none)
