# Task contract — declare every staging column in stg_apif__generic.yml

objective: >
  Declare every column the 16 stg_apif__* models return in stg_apif__generic.yml with a
  description, and add an offline pytest check that fails when a staging model returns a column the
  YAML does not declare. Documentation and a test only; no SQL, data test, grain or contract change.
refs: "#329"

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - tests/test_staging_columns_declared.py
  - dbt_project/models/docs/shared_columns.md
  - .claude/task/329-declare-staging-columns/**

impact_map: >
  writers: none changed; every column already exists in the stg_apif__*.sql final select.
  downstream: no SQL changes, so no model compiles differently. persist_docs writes the new
  column descriptions to the staging tables on the next build.
  layer_rules: staging stays raw cleanup; no SQL, grain or test is touched.
  deploy_order: YAML descriptions only, no ordering constraint against the 04:00 nightly.
  blast_radius: none for any number; 169 column descriptions added, each under the 1,024-character
  BigQuery limit that check_description_hygiene.py enforces, no data test added or changed.

depends_on:
  - none: documentation and a test over one YAML file, needs no open MR's code
shared_files:
  - none: no design baseline or fixture is touched

decisions_taken: >
  Plan approved in chat, 2026-11-19: declare the 169 missing columns (239 in the staging dataset,
  70 declared), reusing doc() blocks where they fit; add a pytest check that parses each model's
  final select with sqlfluff (already pinned) and fails on an undeclared column. Runs in the
  existing test:python job, so no CI change. No new dependency, no recurring cost.
  Where the existing doc() block for a column name describes the cleaned value, the staging column
  references a new `<name>__provider` block in shared_columns.md instead, the pattern
  team_name__provider already sets. check_description_hygiene.py requires every column named like
  a block to reference a block, so plain text alone is refused.

decisions_reserved:
  - none: the change is CPO-approved as described in decisions_taken and adds nothing beyond it

done_when:
  - ".venv/Scripts/dbt.exe parse --project-dir dbt_project exits 0"
  - "python scripts/check_description_hygiene.py exits 0"
  - "pytest tests/test_staging_columns_declared.py passes, its per-model column lists equal the 239 columns of the staging dataset, and it fails on an undeclared column"
  - "the full pytest suite passes"
  - "git diff main shows zero deleted lines in stg_apif__generic.yml"

amendments: (none)
