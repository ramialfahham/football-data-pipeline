# Task contract — declare staging columns named by grain tests

objective: >
  Declare `group_name` on stg_apif__standings and `season` on stg_apif__teams in the model YAML.
  Both columns exist in the SQL and are named by unique_combination_of_columns tests, but a
  dbt-to-DBML import rejects columns a test names and the YAML does not declare. Documentation only.
refs: "#328"

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - .claude/task/328-declare-staging-columns/**

impact_map: >
  writers: none changed; the two columns are already produced by stg_apif__standings.sql:43 and
  stg_apif__teams.sql:25.
  downstream: `dbt ls --resource-type model --select stg_apif__standings+ stg_apif__teams+` returns
  46 models (base_apif__standings first). No SQL changes, so none of them recompile differently.
  layer_rules: staging stays raw cleanup; no SQL, grain or test is touched.
  deploy_order: YAML descriptions only; persist_docs writes the new column descriptions to the two
  staging tables on the next build. No ordering constraint against the 04:00 nightly.
  blast_radius: none for any number; two column descriptions added, no test added or changed.

depends_on:
  - none: documentation-only change to one YAML file, needs no open MR's code
shared_files:
  - none: no design baseline or fixture is touched

decisions_taken: >
  Approved in chat, 2026-11-19: add the two column declarations with descriptions, no test.
  group_name reuses the description text of the same column in core.yml; season reuses
  doc('season_api_year'). No new mechanism, no recurring cost.

decisions_reserved:
  - none: the change is CPO-approved as described in decisions_taken and adds nothing beyond it

done_when:
  - ".venv/Scripts/dbt.exe parse --project-dir dbt_project exits 0"
  - "python scripts/check_description_hygiene.py exits 0"
  - "ci_local --job test:python passes"
  - "git diff --stat main shows only stg_apif__generic.yml and the task folder"

amendments: (none)
