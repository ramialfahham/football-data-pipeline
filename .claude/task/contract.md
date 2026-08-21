# Task contract — cleanup script for orphaned warehouse relations (#84)

objective: >
  Add `scripts/cleanup_orphan_relations.py`: a read-only-by-default reconciliation script that
  reports every relation in the production BigQuery datasets that no dbt manifest node owns, and
  drops them only behind an explicit `--confirm`. It replaces the 310 loose `bq rm` lines the
  investigation produced with something reviewable, repeatable and safe. The script derives the
  orphan set from the manifest every run; it hardcodes no list of table names, so it does not go
  stale the way a captured list would.

refs: >
  GitLab #84 ("Warehouse holds 310 orphaned relations that no dbt model owns"), filed 2026-08-21
  with the full measurement. Authority: `.claude/task/escalations.log`, the 2026-08-21
  `chore/84-orphan-relation-cleanup` entry — it records the CPO's three chat turns verbatim, what
  each one authorises, and the two things they explicitly do NOT authorise. Read that, not this
  line: a contract asserting an approval nobody can check is self-certifying (#28), which is what
  scope-auditor FAILed round 1 for. Convention followed: `scripts/drop_legacy_raw_tables.py`
  and its three siblings, which already establish dry-run-by-default plus `--confirm` for
  destructive warehouse work. Authority for what is expected: dbt's manifest for the built layers,
  and `sources.yml`'s 11 declared `identifier:` values for `raw`.

scope_paths:
  - scripts/cleanup_orphan_relations.py
  - tests/test_cleanup_orphan_relations.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

impact_map: >
  Short-form, and evidenced. `scripts/cleanup_orphan_relations.py` is NOT on the structural
  surface: that surface is `ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py` and
  `site*/` (`task_contract_gate._STRUCTURAL_PREFIXES` + `_EXPORT_RE`), and this file matches none
  of them. It is not a protected path either.

  writers: nothing writes to it; it is a new leaf script with no importers.
  downstream: none. No dbt model, no CI job, no runbook and no other script references it. It is
    not added to `.gitlab-ci.yml` (a protected path, untouched here) so nothing invokes it
    automatically. `tests/` picks the new test file up by pytest discovery, which needs no CI edit.
  layer_rules: none apply. It authors no SQL and adds no model, so `check_layer_contract.py` has
    no surface here.
  deploy_order: none. Merging changes no built relation and nothing runs at 04:00 because of it.
  blast_radius: ZERO on merge, by construction — the script performs no write unless a human
    passes `--confirm`, and the merge does not run it. The blast radius when a human DOES run it
    with `--confirm` is the point of the task and is bounded by the guards in `done_when`.

decisions_taken: >
  CPO, in chat 2026-08-21: "open the MR with the cleanup script", following the proposal of a
  reviewable script with list mode by default and dropping behind an explicit flag. The three
  phases (broken views / views that still return data / tables) are from that same approved
  proposal.

  THRESHOLD DECLARATIONS.
  - NEW MECHANISM: no. This adds a script a human runs by hand. It is not wired into CI, not
    scheduled, and enforces nothing, so it is not a guard. Wiring it in as a recurring check
    WOULD be a new mechanism and is reserved below, not taken.
  - RECURRING COST: none. Zero on merge. When run, it uses the BigQuery metadata API only
    (`list_tables`, `get_table`), which is not billed, and `DROP` DDL, which is also not billed.
    It issues no query, so it scans no bytes. There is no scheduled invocation.
  - NEW DEPENDENCY: no. `google-cloud-bigquery` and `PyYAML` are already required and already
    imported by `scripts/drop_legacy_raw_tables.py`.
  - GUARD INVARIANT: none changed. No hook, no CI rule, no existing check is touched.

decisions_reserved:
  - ⛔ RUNNING IT WITH `--confirm` IS THE CPO'S, NOT MINE. Dropping production relations is
    destructive and permanent. This MR delivers the tool and the evidence; it does not drop
    anything, and nothing in it runs the script. `bq rm` is independently blocked by
    `.claude/settings.json`'s deny list.
  - Whether to wire this into CI as a recurring reconciliation check is a NEW MECHANISM and
    therefore CPO/CTO-class. It is what actually prevents recurrence (the repo guard governs the
    repo; nothing reconciles the warehouse, which is why a 2026-05-27 merge left 310 relations
    standing for three months), but it is proposed in #84, not built here.
  - Whether `dbt_scratch` (16 stale relations) and the other non-prod datasets get cleaned is a
    separate decision. The script refuses to touch any dataset outside its explicit allowlist, so
    a later yes is a one-line change reviewed on its own.
  - `raw_archive` (14 tables dated 20260808) is a deliberate archive. Not in scope, not in the
    allowlist.

done_when:
  - Dry-run is the default. The script performs no destructive call without `--confirm`, and a
    test proves it by asserting `delete_table` is never reached without the flag.
  - A relation that any manifest node owns can never be selected, and a test proves it.
  - The manifest sanity floor aborts the run rather than treating an empty or unreadable manifest
    as "everything is orphaned". A test drives that path and asserts it exits non-zero WITHOUT
    calling `delete_table`. This is the failure that would drop the whole warehouse, so it is
    tested by breaking it, not by reading it (#904).
  - `__dbt_tmp` relations are never selected; they carry a dbt-set 12-hour expiration.
  - Datasets outside the explicit allowlist are never touched, and a test proves it.
  - The three phases select disjoint sets whose union is the full orphan set, proven by a test.
  - `python -m pytest tests/ -v` is green, and the new tests are seen to FAIL first when the
    guard they cover is broken (#904: a passing test proves nothing until it has been red).
  - The five offline gates pass, read from their OUTPUT, not their exit code.
  - Handover updated in the SAME commit as the code it describes.

amendments:
  - 2026-08-21: + `.claude/task/escalations.log` — authority: scope-auditor FAIL, round 1. The
    contract asserted a CPO "go" given in chat with no entry in the log to back it, which is the
    self-certifying pattern GitLab #28 exists to close, and which MR5 and MR6 both avoided by
    recording the approval BEFORE the branch was written. This task is not a protected-path edit,
    but its content is a tool that issues DROP DDL against production, so the authority to build it
    at all has to be checkable by someone who was not in the conversation. Content: an entry
    recording the CPO's actual chat turns and what each one authorised. Written on a clean tree
    (the code was stashed by explicit path and popped straight back).
