# Task contract — UDF calls read as missing tables in cleanup_orphan_relations.py (#84 follow-up)

objective: >
  Fix a defect in `scripts/cleanup_orphan_relations.py` merged in `!90`. Its reference regex matches
  any `project.dataset.name`, and `bq ls` / `Client.list_tables` never returns ROUTINES, so a call
  to a user-defined function reads as a reference to a missing table. `resolves()` then returns
  False and the view is classified BROKEN — the phase the script advertises as risk-free because
  "they already error, so nothing can be reading them". For `marts.mart_fixture_index` that claim
  was false: it calls `dbt_analytics.url_fixture_slug`, it validates, and it returns 1.5 MB.
  Fix: look up routines as well as relations, and treat a reference that resolves to a routine as
  resolving. Correct the docstring claims, and pin it with tests.

refs: >
  Found by the CPO reading the phase-1 list before approving the drop, and asking why
  `mart_fixture_index` was in it. Authority to fix, in chat 2026-08-21: "yes, fix it". Recorded in
  `.claude/task/escalations.log` under the 2026-08-21 `fix/84-udf-refs-misread-as-missing-tables`
  entry, with what was measured. Parent issue GitLab #84; the script landed in `!90`, merged as
  `df0dc7e`. THE DROP WAS NOT RUN — it was stopped before execution, so no relation was lost to
  this defect.

scope_paths:
  - scripts/cleanup_orphan_relations.py
  - tests/test_cleanup_orphan_relations.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

impact_map: >
  Short-form, evidenced. `scripts/cleanup_orphan_relations.py` is not on the structural surface
  (`ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py`, `site*/`) and is not protected.

  writers: nothing writes to it; still a leaf script with no importers.
  downstream: none. No dbt model, CI job, runbook or other script references it; it is not in
    `.gitlab-ci.yml`. The new test file is picked up by pytest discovery, so no CI edit is needed.
  layer_rules: none apply; it authors no SQL and adds no model.
  deploy_order: none. Merging changes no built relation and nothing runs at 04:00 because of it.
  blast_radius: ZERO on merge (the script performs no write without `--confirm`, and merging does
    not run it). The blast radius of the DEFECT, measured rather than estimated: across every
    orphan view body, 183 extracted referents are not tables. 182 are genuinely absent
    per-competition raw tables. Exactly 1 is a routine — `dbt_analytics.url_fixture_slug` — and it
    misclassified exactly one view, `marts.mart_fixture_index`. So phase `broken` was 250 selected,
    249 genuinely broken, 1 live. After the fix, expect broken 249, live-views 27, tables 34,
    total unchanged at 310.

decisions_taken: >
  CPO in chat 2026-08-21: "yes, fix it", after being shown the root cause, the dry-run proof that
  `mart_fixture_index` still returns data, and the measured blast radius. This is a defect fix to a
  tool he already approved and merged; it changes no product behaviour and no data.

  THRESHOLD DECLARATIONS.
  - NEW MECHANISM: no. Same manual script; not wired into CI, not scheduled, enforces nothing.
  - RECURRING COST: none. Zero on merge. `Client.list_routines` is a metadata call and is not
    billed, exactly like `list_tables`. It adds one metadata call per allowed dataset (6), issues
    no query, and scans no bytes.
  - NEW DEPENDENCY: no. `list_routines` is part of `google-cloud-bigquery`, already pinned at
    3.25.0 in `requirements.txt` and already used by this script.
  - GUARD INVARIANT: none weakened. Every existing guard is kept and re-tested. The change makes
    the tool select FEWER relations, never more: a reference that previously failed to resolve can
    now resolve, which moves a view out of `broken` into `live-views`. It cannot move anything into
    `broken`, and it cannot make a live model droppable.

decisions_reserved:
  - Running the script with `--confirm` remains the CPO's, unchanged from `!90`. Nothing in this
    task drops anything, and the phase-1 drop stays unrun until he says so.
  - Whether `marts.mart_fixture_index` should ultimately be dropped is NOT decided here. The fix
    only moves it into the cautious phase. It is still an orphan (no manifest node owns it, and the
    consumer sweep found no reader), but it is a live one and belongs with the other 26.
  - Wiring this in as a recurring reconciliation check is still a NEW MECHANISM, still proposed in
    #84, still not built.

done_when:
  - A reference that resolves to a routine is treated as resolving, and a test proves it by
    reproducing the `mart_fixture_index` shape (a view over live tables plus a UDF call).
  - Routines are NEVER added to the droppable set. `find_orphans()` iterates the warehouse map, so
    folding routines into it would make every UDF look like an orphan relation and select it for
    deletion — a far worse bug than the one being fixed. A test asserts no routine is ever
    returned as an orphan.
  - The docstring no longer claims BROKEN means "already errors" without qualification, and states
    the routine case explicitly.
  - Every guard from `!90` still holds: mutation-test the whole set, not only the new one, and each
    must be seen RED.
  - Run dry against production and confirm the classification moves 250/26/34 to 249/27/34 with the
    total unchanged at 310, and that `mart_fixture_index` is in `live-views`.
  - `python -m pytest tests/ -v` green; `ruff check . --config .ruff-ci.toml` clean; the offline
    gates pass, read from their OUTPUT.
  - Handover updated in the SAME commit. ⚠ Keep the edit small and character-neutral: `!91` is open
    and also edits `.claude/active_work.md`, which is at 15,984 of a hard 16,000-character cap.

amendments: (none)
