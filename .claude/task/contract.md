# Task contract — shrink docs/: delete the obsolete documents, merge two, remove every link

objective: >
  MR 1 of the documentation cleanup the CPO approved on 2026-10-05: delete 13 obsolete documents, merge
  the still-true provider facts of the ingestion blueprint into the data contract and the secret rules
  of the development workflow into the README, delete both sources, and remove every link to the 15
  removed files. The area cleanups (#199, #196, #197, #198) then work on the documents left.

refs: >
  The CPO's choice of 2026-10-05, verbatim: "MR 1 (before the area MRs): delete: board_request_sync,
  chat_driven_workflow, ci_failure_watchdog, cursor_dispatch_workflow, pr_autopilot,
  project_status_sync, feedback_collection, match_preview_pages_refinement,
  player_stats_ui_data_modeling_concept, playoff_window_policy, product_direction_threads,
  competitions/wc26.md, audits/2026-06_alignment_audit.md; merge: api_football_ingestion_blueprint ->
  data_contract (true provider facts only); development_workflow -> README (local setup); remove every
  link to them; update CLAUDE.md's document table". Findings behind it: #196-#199.

scope_paths:
  - docs/board_request_sync.md
  - docs/chat_driven_workflow.md
  - docs/ci_failure_watchdog.md
  - docs/cursor_dispatch_workflow.md
  - docs/pr_autopilot.md
  - docs/project_status_sync.md
  - docs/feedback_collection.md
  - docs/match_preview_pages_refinement.md
  - docs/player_stats_ui_data_modeling_concept.md
  - docs/playoff_window_policy.md
  - docs/product_direction_threads.md
  - docs/competitions/wc26.md
  - docs/audits/2026-06_alignment_audit.md
  - docs/api_football_ingestion_blueprint.md
  - docs/development_workflow.md
  - docs/data_contract.md
  - docs/operations_guide.md
  - docs/metrics_context_model.md
  - docs/ui_design_brief.md
  - README.md
  - CLAUDE.md
  - .cursor/rules/project-context.mdc
  - dbt_project/docs/engineering_standards.md
  - dbt_project/tests/assert_fct_fixture_no_stale_ns.sql
  - ingestion/api_football/loads/batch_fixtures.py
  - ingestion/api_football/settings.py
  - scripts/check_registry_var_sync.py
  - design-mocks/gen_competitions.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_materialisation_policy.py
  - tests/test_governance_doc_parity.py
  - tests/test_ingest_profile_pacing.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  Documents and comments only. In ingestion/**: a docstring in loads/batch_fixtures.py (its pointer to the
  deleted blueprint and its rate-limit sentence) and a docstring in settings.py (the same pointer); no
  code token changes (checked with `git diff --word-diff`). No dbt model changes; one comment line in
  dbt_project/tests/assert_fct_fixture_no_stale_ns.sql. No table, model or mart is written or read
  differently; blast radius none. Links: `git grep` over the tree for every removed file name finds only
  the files in scope_paths, plus .claude/task/audit_reviewer_outputs.md (paperwork, left as it is) and
  .github/workflows/pages-match-preview.yml (protected and disabled; listed in #200).

decisions_taken: >
  The CPO's choice quoted in refs. Readings, under the delegation of 2026-10-02:
  - "True provider facts only": the two-step fixture fetch, empty statistics as `[]` with up to 48 hours'
    delay, `league.round` formats and no group field on `/fixtures`, the measured plan limits (450 a
    minute, 75,000 a day, read from the response headers), synchronous calls and the pause setting.
    Each is checked against the code (`batch_fixtures.py`, `http_client.py`, `quota.py`, `settings.py`).
    The blueprint's key-path list (owned by the staging SQL), its finished refactor plan (§7-9) and its
    false "20–50 calls a run" are not carried. The data contract's endpoint row for per-fixture data and
    its coverage-flag paragraph are corrected to the code in the same edit, because the merged text
    would otherwise sit next to their false versions.
  - "Local setup" for the README: the README already holds setup and pre-commit; what moves is the
    secret-safety rule, with the CI scan named as GitLab's `validate:secrets` (gitleaks). The workflow's
    `dbt build` steps are not carried (CLAUDE.md forbids them).
  - "Remove every link": a link inside a section that exists only for a removed document's subject goes
    with its section — the operations guide's GitHub Pages match-preview and play-off-window
    subsections, and engineering_standards.md §11 (GitHub Pages export contract). Every other link is
    replaced by the document that now owns the fact, or removed.
  - tests/test_no_decision_history_in_docs.py loses the rows of deleted documents (its own rule: "remove a
    row at zero"); the two other tests drop their exemptions for removed paths.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - Everything else the audits found in the documents that stay is #196-#200, not this MR.

done_when:
  - `git grep` finds no reference to a removed file outside .claude/task/ and the protected, disabled
    .github/workflows/pages-match-preview.yml.
  - pytest (whole suite), ruff with .ruff-ci.toml and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.

amendments:
  - 2026-10-05: + tests/test_ingest_profile_pacing.py — authority: "remove every link to them"; content:
    its "Blueprint §4" comment and BLUEPRINT names.
