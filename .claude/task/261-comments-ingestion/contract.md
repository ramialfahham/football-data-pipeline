# Task contract — ingestion: comments state only why

objective: >
  Issue #261, the ingestion folder. Bring every comment and docstring in ingestion/**/*.py up to
  dbt_project/docs/engineering_standards.md section 1.2: a one-line why where the reason is not
  obvious, nothing else. No code changes. Dead code and the ingestion documents stay for #196.

refs: >
  #261, #196 (its comment lines). Standard: engineering_standards.md section 1.2. Gate:
  .claude/hooks/comment_history_gate.py.

scope_paths:
  - ingestion/**/*.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_ci_data_job_invariants.py
  - docs/data_contract.md
  - .dockerignore
  - deploy/nightly/entrypoint.sh
  - .gitlab-ci.yml
  - .claude/task/261-comments-ingestion/

decisions_taken: >
  The standard already rules every case, so the sweep is agent-executable under working_agreement
  section 10. A string the code compares, prints, logs, writes or parses is code, not a comment,
  and stays, so a flagged line inside a string stays too. Tool directives (noqa, type, pragma)
  stay. Only the pins in tests/test_no_decision_history_in_code.py change besides comments. A
  citation of an ingestion file by line number elsewhere in the repo moves when comments are
  removed, so it drops the line number and keeps the file name: in .dockerignore,
  deploy/nightly/entrypoint.sh, docs/data_contract.md and three comments in .gitlab-ci.yml, and in
  one assert message in tests/test_ci_data_job_invariants.py. No new mechanism, no new dependency,
  no recurring cost.

decisions_reserved:
  - A length limit on comments in the gate would be a new rule; it is not added here.

protected_override: >
  Approved in chat, 2026-11-09: the CPO typed the go in this task's session for a comment-only
  edit to .gitlab-ci.yml that drops the line numbers from its three settings.py and main.py
  citations.

impact_map: >
  writers: none changes. The 14 raw tables the loaders write (`grep -rho "raw_table(..." ingestion/
  | sort -u | wc -l` → 14) are written by unchanged code; only comments and docstrings move.
  downstream: none. No module reads its own docstring (`grep -rn "__doc__" ingestion` → no output),
  so no docstring reaches a log, a table or a CLI. The two tests that read ingestion source,
  tests/test_batch_fixtures.py:464 and tests/test_ingestion_read_hoisting.py:308, parse it with
  ast, which comments and docstring text do not change.
  layer_rules: check_layer_contract applies unchanged; no model, raw table or column is touched.
  deploy_order: none; the nightly runs identical code before and after merge.
  blast_radius: none; the AST of every changed file with docstrings removed equals gitlab/main.
  .gitlab-ci.yml (protected): GitLab parses it on every push and MR to build the pipeline; readers
  in the repo are tests/test_ci_data_job_invariants.py, test_nightly_entrypoint_parity.py,
  test_governance_hooks.py, test_lint_config.py, test_persist_docs_policy.py,
  test_wait_for_nightly.py, test_governance_doc_parity.py, test_check_chart_screenshots.py,
  test_check_component_registry.py, test_design_inventory.py, scripts/check_copy_gate.py,
  check_description_hygiene.py, check_task_artifacts.py and .claude/hooks/task_contract_gate.py
  (`grep -rln "gitlab-ci.yml" tests scripts .claude/hooks`). The edit touches three `#` lines
  (698, 703, 754), so yaml.safe_load of the file is equal before and after and no job, rule,
  variable or script changes; a reader that scans raw lines sees only the dropped `:31` and `:55`.
  On failure the pipeline would not parse and every job would stop, which the YAML equality rules
  out.

done_when:
  - The AST of every changed ingestion file, with docstrings removed, equals the AST on the base branch.
  - The only non-comment changes are PINNED_LINES and PINNED_FILES in tests/test_no_decision_history_in_code.py and the line number dropped from one assert message in tests/test_ci_data_job_invariants.py.
  - No file cites an ingestion file by line number.
  - yaml.safe_load of .gitlab-ci.yml equals gitlab/main.
  - python -m pytest tests passes.
  - The offline gates pass.

amendments: (none)
