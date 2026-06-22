# Review — fix/staging-readall-classes-539 — 2026-06-22

> #539 — codify the read-all staging class in layering.md §1_staging accurately + add the
> missing header/yml read-all rationale to the four fixture-detail staging models. DOC/COMMENT
> ONLY (no SQL/grain change). First real exercise of the #540 impact-map gate (the contract
> carries an evidenced `impact_map`). Required reviewers: scope-auditor (always) +
> analytics-engineer-reviewer (dbt_project/**).

diff_sha256: 93f98c7940641f35ede1be04ac77e5999e9ca77e6205c3a7f9f1f3842ecbf95c

## scope-auditor
VERDICT: PASS
risks_checked:
- Impact-map "blast radius: NONE" honesty: verified all four staging `.sql` files contain header
  comments only with zero SELECT-logic changes; `stg_apif__generic.yml` modifies only
  `description:` text (metadata); `layering.md` is prose. Compiled dbt output is byte-identical
  (comments stripped, descriptions are documentation); lineage unaltered. The evidenced impact_map
  (real `dbt ls` lineage + writers + layer rules) is honest.
- Merge-on-write class codification does not mint a new rule or extend staging purity: both
  incremental-accumulation and the codified merge-on-write class share the identical SELECT rule
  (read all rows, no `partition by league_code` qualify); the diff documents what the loaders
  already do (stg_apif__players already reads all rows). Framed as CPO-recognized (#539). All files
  in scope; no §10 smuggled; no shipped number or SQL changed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Re-insert-without-delete path in batch_fixtures.py: traced `_needs_fetch` → `retry_ids`
  construction → `_fetch_and_persist_batch` delete guard (lines 234-239). The only scenario where a
  fixture exists in the table but is not in retry_ids is when it has non-empty statistics, in which
  case `_needs_fetch` returns False and it never enters `to_fetch`. The exception-swallowing branch
  in `_read_fetched_coverage` is the one real transient-duplicate path — correctly documented by the
  "base dedups defensively" language. No structural accumulation path exists; the corrected premise
  (one bounded row per (league_code, fixture_id)) is accurate.
- check_layer_contract.py comment-stripping compatibility: verified `_strip_sql_comments` applies
  the `--[^\n]*` regex before all purity checks, so the six-line `--` header blocks are invisible to
  the partition-by / group-by / distinct / join checks. Compiled SQL byte-identical; the "blast
  radius: NONE" claim holds. layering.md merge key `(league_code, fixture_id)` matches the loader's
  `_delete_fixtures` SQL; the four headers + yml descriptions accurately state the read-all rationale.

## escalations
(none)
