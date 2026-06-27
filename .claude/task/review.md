# Review — docs/macro-usage-standard — engineering_standards.md §1.3 Macros

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff (`.claude/task/review_input.patch`).
> Required set: always → scope-auditor; `dbt_project/**` → analytics-engineer-reviewer.
> Documentation only — adds a "when / when-not to use a macro" standard. The benchmark macro removals +
> dormant-scaffolding deletions are reserved to separate PRs (contract decisions_reserved).
> Two prior FAILs fixed: (1) the COMPOSE rule mischaracterised the benchmark macro as a "formula" and the
> generate_schema_name claim was imprecise; (2) a "latest partition" example cited dead code
> (apif_latest_source_partition has zero callers) — replaced with the genuinely-used JSON-expansion macro.

diff_sha256: 984190fb2f0474b284c3789e622b239bf3be89e5aa6c76052d4299cf6d1bc9c5

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + decision class: only `dbt_project/docs/engineering_standards.md` (in scope) + the always-allowed
  contract.md are touched; no model/macro change. The text codifies the CPO's already-stated principle
  (macros decrease maintainability; prefer plain SQL + COMPOSE) — no new §10 decision; consistent with
  layering.md (generate_schema_name override; JSON parsing allowed in staging) and §5.
- Boundary — "cross-cutting transform that can't be a model": the "can't be a standalone model" assertion is
  a context-dependent judgment a weak claim could exploit; mitigated by the §5 cross-ref + the COMPOSE
  principle a reviewer can cite to push back. The standard documents the tension honestly rather than
  closing it falsely; the contested existing macros (team/player benchmark) are reserved to the CPO anyway.
- Dormant-macro grandfathering left implicit: "don't add a macro ahead of need" is forward-looking ("add"),
  but a strict reader could try to apply it to the CPO-reserved dormant scaffolding (playoff round names
  etc.). No scope violation (the contract reserves their disposition); a future "applies to new macros"
  clarifier would reduce friction. Low risk.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `generate_schema_name` example — live + accurate: the override exists at
  `dbt_project/macros/generate_schema_name.sql` and is active; dbt's default would produce
  `<target_schema>_<custom>` (e.g. `dbt_analytics_staging`) instead of the bare `staging`, exactly as the
  standard states; layering.md documents the dependency. Correct, necessary example.
- JSON-expansion example — verified in live use: `apif_payload_response_json_strings` has exactly three
  callers (`stg_apif__fixtures_next`, `stg_apif__leagues`, `stg_apif__teams`), each inside
  `unnest({{ ... }})` in the `from` clause; it takes a table alias and resolves inside the caller's from,
  so it genuinely cannot be a standalone model. "Several staging models" + "inside the from/unnest" are
  accurate.
- §5 cross-reference consistency: §1.3's COMPOSE guidance (compute once, downstream reads) aligns with §5
  ("centralize once in `intermediate` if reused") and layering.md's `4_intermediate` definition. No
  contradiction.
- No false legitimation of dead code: `apif_latest_source_partition` has zero callers (staging uses inline
  `qualify`); the standard does NOT cite it — the second example maps to the live JSON macro, so no dead
  macro is canonised.

## escalations
(none)
