# Task contract — the Bundesliga's completeness gate is soft like every other competition

objective: >
  #195. The Bundesliga is the only competition whose missing match details stop the nightly before
  dbt runs: its registry entry has no `ingest_completeness_gate`, and `ingestion/api_football/registry.py`
  makes an active entry without one `hard`. The other 47 entries set `soft`. BL1 gets the same `soft`.

refs: >
  #195, from the CPO's words on 2026-10-05: "There is no reason to treat Bundesliga differently from
  other competitions".

acceptance_criteria:
  # The issue's checklist line, verbatim.
  - "A gap in the Bundesliga's match details is reported and the nightly carries on, as for every other competition."

scope_paths:
  - docs/competition_registry.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

decisions_taken: >
  #195 as written from the CPO's words of 2026-10-05 (quoted in refs). One line in the registry:
  `ingest_completeness_gate: soft` on BL1, the value and key the other 47 entries carry. The gate is
  read only by the ingestion (`registry.py` → `completeness.py`); it is not synced into
  `dbt_project.yml` or the registry seed, so `scripts/sync_dbt_vars.py` has nothing to write.
  Effect: a BL1 gap is reported in the completeness report and summary and no longer stops the run;
  with no hard-gated competition left, a run still fails on the stagnation signals (statistics,
  dropped calls, per-team gaps) as before.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - The code's default for an entry without the key (hard when active) is unchanged; #195's Not in scope.

done_when:
  - check_registry_var_sync and the offline gates pass; pytest passes.
  - `registry.py` loads BL1 with gate `soft` and no entry with `hard`.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.

amendments: (none)
