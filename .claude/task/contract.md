# Task contract — retire the transfers chain entirely

> CPO ruling 2026-06-13: transfers are not consumed anywhere (fct_transfer is a leaf with
> zero consumers; no mart/export/UI reads transfers; the only use was a dim_player identity
> fallback feeding the unconsumed fct_transfer). They are derivable from
> dim_player_team_season_mapping if ever needed. CPO approved: REMOVE ENTIRELY, including
> dropping the RAW_APIF_TRANSFERS BigQuery table (explicit destructive-drop authorization +
> cost approval to stop the daily /transfers ingest). Follows the RAW_APIF_ROUNDS retirement
> precedent (docs/data_contract.md). See docs/working_agreement.md §2/§10.

objective: >
  Retire transfers end-to-end: stop ingesting /transfers, delete the staging/base/core
  transfers models, drop the dim_player transfer-identity fallback, remove the raw source,
  and update the docs. The RAW_APIF_TRANSFERS BigQuery table is dropped as a POST-MERGE
  step (after the no-writer code is on main, so the 04:00 UTC run cannot recreate it).
  This closes #420/#441 by deletion and removes the name-less-transfer DQ problem at root.
  Verified: fct_transfer has no consumers (only comments mention it); no metric_catalogue
  entry; no export/site reference.

scope_paths:
  # deletions
  - ingestion/api_football/loads/transfers.py
  - dbt_project/models/1_staging/api_football/stg_apif__transfers.sql
  - dbt_project/models/2_base/api_football/base_apif__transfers.sql
  - dbt_project/models/3_core/fct_transfer.sql
  # ingestion edits
  - ingestion/api_football/loads/competition_runner.py
  - ingestion/api_football/main.py
  - ingestion/api_football/quota.py
  - ingestion/api_football/settings.py
  # dbt model edits
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/2_base/api_football/base_apif__player_team_season.sql
  - dbt_project/models/3_core/dim_player_team_season_mapping.sql
  # dbt config / yml edits
  - dbt_project/models/1_staging/api_football/sources.yml
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/core.yml
  - dbt_project/macros/apif_latest_source_partition.sql
  # docs
  - dbt_project/docs/layering.md
  - docs/data_contract.md
  - docs/operations_guide.md
  - README.md
  - dbt_project/models/1_staging/api_football/README.md
  - .env.example
  # task artifacts
  - .claude/task/contract.md
  - .claude/active_work.md

decisions_taken: >
  CPO-approved full retirement + BQ table drop (2026-06-13; cost + destructive-drop
  authorized). Removing the transfers_src CTE from base_apif__players is a deliberate
  behaviour change: dim_player loses transfer-only player identities — safe because
  fct_transfer (the only consumer of those identities) is deleted, and played players are
  covered by the fixture identity sources. RAW_APIF_TRANSFERS left in BQ ONLY until the PR
  merges, then dropped (bq rm) — sequencing prevents recreation by the scheduled run.

decisions_reserved:
  - Intentionally NOT updated (out of scope, not contract-docs): docs/pipeline_architecture_plan.md
    (draft roadmap / historical), docs/audits/2026-06_alignment_audit.md and
    .claude/task/audit_reviewer_outputs.md (point-in-time records), and generic-prose
    mentions of the word "transfers" (shared.yml mart description, layering.md fact-example
    "a transfer", gaps_register.md "players transfer"). If a reviewer judges any of these a
    required doc-sync, STOP and escalate rather than expand silently.
  - README.md line 29 also undercounts dims (omits dim_player_team_season_mapping from #444);
    fixing the dims count is a #444 doc-sync follow-up, not this task — I will correct only
    the facts list (remove fct_transfer) unless a reviewer requires the whole line be made
    consistent.

done_when:
  - the 4 files above are git-rm'd; no remaining ref()/import to stg_apif__transfers,
    base_apif__transfers, fct_transfer, loads.transfers, or raw_apif_transfers anywhere in
    ingestion/ or dbt_project/models/ (grep clean).
  - base_apif__players no longer has a transfers_src CTE / union member; dim_player_team_season_mapping
    + base_apif__player_team_season comments no longer reference fct_transfer/the transfer fact.
  - sources.yml, stg_apif__generic.yml, base.yml, core.yml no longer carry the transfers
    entries; the macro comment + README tables drop transfers.
  - data_contract.md: transfers removed from unified-tables/endpoints/plan-vs-product/append-only
    prose + a "Retired" note added (mirroring ROUNDS); operations_guide.md drops the transfers
    env-var sections; layering.md drops the fct_transfer inventory row + full-refresh mention.
  - validate-local Tier 1+2 green (dbt parse, sqlfluff lint, layer contract, pytest); full DQ
    build → ci-data-build.
  - reviewers: scope-auditor (always) + data-engineer-reviewer (ingestion/** + docs/data_contract.md)
    + analytics-engineer-reviewer (dbt_project/**) — PASS.
  - POST-MERGE: drop RAW_APIF_TRANSFERS from BigQuery (verify table identity first).

amendments:
  - 2026-06-13 A1: + .env.example to scope. authority: iteration-1 data-engineer-reviewer
    finding — `# API_FOOTBALL_FETCH_TRANSFERS=1` left as a dangling commented example var
    after the env var was removed from all live code. content: remove that line. (Also
    fixed two in-scope iter-1 findings: the competition_runner module docstring still
    listed "→ transfers", and the data_contract Retired note said the table was "dropped"
    past-tense — reworded to "dropped post-merge".)
  - 2026-06-13 NOTE (not an amendment): the iter-1 data-engineer-reviewer also raised a
    "sample-based test rule (2026-06-12)" requiring fixture coverage before deleting a
    parser. REBUTTED as spurious: no such rule exists in engineering_standards.md,
    working_agreement.md, or development_workflow.md (grep); there is no tests/fixtures
    directory and the repo has no sample-payload parser tests; and deleting code does not
    require test coverage OF the deleted code. Not actioned.
