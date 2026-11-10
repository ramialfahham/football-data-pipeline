# Task contract — scripts: comments state only why

objective: >
  Issue #261, the scripts folder. Bring every comment and docstring in scripts/**/*.py up to
  dbt_project/docs/engineering_standards.md section 1.2: a one-line why where the reason is not
  obvious, nothing else. No code changes. Left for later MRs: the protected design-check scripts,
  export_site_data.py and generate_metric_sql.py, and check_task_artifacts.py, which a protected
  hook cites by line number.

refs: >
  #261. Standard: engineering_standards.md section 1.2. Gate:
  .claude/hooks/comment_history_gate.py.

scope_paths:
  - scripts/bootstrap.py
  - scripts/check_chart_components.py
  - scripts/check_chart_screenshots.py
  - scripts/check_competition_type_seed.py
  - scripts/check_component_registry.py
  - scripts/check_copy_gate.py
  - scripts/check_description_hygiene.py
  - scripts/check_layer_contract.py
  - scripts/check_raw_freshness.py
  - scripts/check_registry_var_sync.py
  - scripts/check_relationships_coverage.py
  - scripts/check_ui_i18n_metrics.py
  - scripts/check_yml_vs_projection.py
  - scripts/cleanup_orphan_relations.py
  - scripts/clear_apif_ingest_lock.py
  - scripts/compare_fixture_statistics_live.py
  - scripts/declare_missing_columns.py
  - scripts/diagnostics/*.py
  - scripts/drop_injuries_raw_tables.py
  - scripts/drop_legacy_raw_tables.py
  - scripts/drop_raw_apif_wc_qualifier_fixtures.py
  - scripts/drop_snap_apif_d1_standings.py
  - scripts/export_matchday_json.py
  - scripts/export_metric_definitions_json.py
  - scripts/export_pages_data.py
  - scripts/export_team_season_json.py
  - scripts/extract_preview_json.py
  - scripts/gen_domestic_marts.py
  - scripts/get_new_league_codes.py
  - scripts/inject_feedback_endpoint.py
  - scripts/refetch_from_provider.py
  - scripts/report_bq_cost.py
  - scripts/report_process_health.py
  - scripts/security/check_no_secrets.py
  - scripts/snapshot_tracker.py
  - scripts/sync_dbt_vars.py
  - scripts/sync_metric_docs_blocks.py
  - scripts/wait_for_nightly.py
  - tests/test_no_decision_history_in_code.py
  - .claude/task/261-comments-scripts/

decisions_taken: >
  The standard already rules every case, so the sweep is agent-executable under working_agreement
  section 10. A string the code compares, prints, writes or parses is code, not a comment, and
  stays, so a flagged line inside a string stays too. A module docstring that a script reads
  through __doc__ is its --help text and stays as it is. Tool directives (noqa, type, pragma)
  stay. The .sh, .ps1 and .gs files carry no history and .gitlab-ci.yml cites one of them by line,
  so they are not touched. Only the pins in tests/test_no_decision_history_in_code.py change
  besides comments. No new mechanism, no new dependency, no recurring cost.

impact_map: >
  writers: none changes. Four scope files are consumption scripts (scripts/export_*.py):
  export_matchday_json.py, export_team_season_json.py, export_pages_data.py and
  export_metric_definitions_json.py; only their comments and docstrings move, so every table they
  read and every file they write is unchanged.
  downstream: their readers are the legacy site/ pages, the disabled .github/workflows copies,
  the `.ui_paths` trigger list in .gitlab-ci.yml, scripts/export_matchday_insights.ps1 (runs two
  of them), the E402 ignores in .ruff-ci.toml, tests/test_export_pages_data.py (imports and calls
  functions) and tests/test_metric_bindings.py (runs the script with --out)
  (`git grep -l export_<name>`). None reads a comment; export_metric_definitions_json.py passes
  __doc__ to argparse, and that docstring stays byte-identical.
  layer_rules: check_layer_contract applies unchanged; no model, raw table or column is touched.
  deploy_order: none; nothing deployed runs these scripts differently after merge.
  blast_radius: none; the AST of every changed file with docstrings removed equals gitlab/main.

decisions_reserved:
  - A length limit on comments in the gate would be a new rule; it is not added here.

done_when:
  - The AST of every changed script, with docstrings removed, equals the AST on the base branch.
  - Every module docstring a script reads through __doc__ is unchanged.
  - No file cites a changed script by a line number that moved.
  - The only non-comment change is PINNED_LINES and PINNED_FILES in tests/test_no_decision_history_in_code.py.
  - python -m pytest tests passes.
  - The offline gates pass.

amendments: (none)
