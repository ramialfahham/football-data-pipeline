# Acceptance evidence — memory cut to behaviour rules, with size budgets a hook enforces

criteria_demonstrated:
  - THE MEMORY FOLDER IS CUT TO BEHAVIOUR RULES AND POINTERS. `memory_budget_gate.py --report` on
    a backup of the folder as it was (`scratchpad/memory_before/`, 109 files) versus the live
    folder now — two-sided: **files 108 → 50; index 17,152 → 7,669 chars; largest note 20,407 →
    4,232 chars; total 477,078 → 116,101 chars.** By class: STALE 22 deleted (13 `session_handoff_*`
    superseded by `.claude/active_work.md`; `governance_artifact_commit_ordering`,
    `project_architecture`, `project_competition_benchmarks_design`, `project_gitlab_migration`,
    `project_leaderboards_roster_design`, `project_metric_layer_two_seeds` — `metric_definitions.csv`
    no longer exists, `project_player_page_design` — the "three tabs" file, `project_season_model_naming_parked`
    — a dead GitHub issue, `project_vision` — "Matchday IQ" and GitHub Pages); FOLD 12 deleted, each
    fact grep-verified in the repo (`project_dbt_mcp_server` → `agent_guardrails.md`;
    `project_dbt_shared_ci_prod_datasets` → `CLAUDE.md`; `project_metrics_context_model` →
    `docs/metrics_context_model.md`; `project_mvp_retired` → `CLAUDE.md` + `north_star.md`;
    `project_no_api_predictions` → `north_star.md`; `project_player_model_redesign` and
    `project_team_model_redesign` → `layering.md`; `project_player_stat_nulls_zero` →
    `metric_layer.md`; `project_provider_name_is_identity` → `site_architecture.md`;
    `project_slug_assigned_not_derived` → `base.yml` + #95; `project_team_metric_rank_correlation_sweep`
    → the model header + `active_work.md`; `project_v2_frontend_design` → `ui_design_brief.md`);
    `project_semantic_layer_ai_ready` dropped (an intention with no requirement). Behaviour lines
    inside deleted files moved first: the three mock-delivery rules and "one tab at a time" →
    `feedback_design_discipline.md`; "suspect stale prod state, prove a data-semantics claim from
    ground truth" → `feedback_verify_by_running.md`. MERGE MAP (29 → 9): escalation
    (`decide_dont_escalate` + `stop_micro_escalating` + `premature_escalation` + `one_decision_at_a_time`
    → `feedback_escalation_discipline`); git (`branch_discipline` + `branch_workflow` +
    `git_push_tracking` + `git_tool_discipline` → `feedback_git_discipline`); governance
    (`governance_review_mechanics` + `governance_edit_gate_scope` + `review_exclude_false_positive` +
    `sibling_pr_rebase_rebind` → `feedback_governance_review_mechanics`); never-merge (`never_merge` +
    `never_ship_unreviewed` + `remove_the_permission_not_parse_the_command` → `feedback_never_merge`);
    design (`design_off_the_cuff` + `design_spec_altitude` + `v2_design_schema_first` →
    `feedback_design_discipline`); metrics (`metric_catalogue_governance` + `metric_direction_judgement`
    + `metric_formula_vs_availability` + `metric_calc_layer_placement` → `feedback_metric_governance`);
    continuity (`handover_discipline` + `continuity_writeback` → `feedback_continuity`); tracker
    (`tracker_not_documents` + `doc_clutter_discipline` + `issues_for_upcoming_work` →
    `feedback_tracker_not_documents`); verify (`verify_by_running` + `verify_the_test_fails` →
    `feedback_verify_by_running`); plus consumption (`consumption_layer_contract` +
    `export_is_consumption_too` → `feedback_consumption_layer_contract`, found while rewriting) and
    `percentile_display_phrasing` deleted (the rule is `metrics_display.md`, LOCKED).
    `project_repo_portfolio` → `feedback_repo_tone` (a preference, not a product fact). Every one of
    the 50 survivors was rewritten to the rule, why, and how to apply; `MEMORY.md` rebuilt with one
    line per file — 50 links, 50 files, 0 missing, 0 dangling; every `[[link]]` in every note
    resolves (checked by script: 0 broken).
  - THE THREE MEMORY-ONLY FACTS HAVE A HOME OR ARE GONE. `ci-runner-01` → `docs/operations_guide.md`
    "The CI runner (GitLab)" (one small Hetzner VM as the only runner, per-project registration
    and why no group, why it exists, no GCP credentials on the host, the IPv6 clone failure and its
    non-persistent fix, the console keyboard, SSH by key only); one stale claim in the memory ("the
    SSH key is rejected") corrected to the handover's current fact (the key is passphrase-protected).
    NOT moved, on the cto-reviewer's round-1 finding: the host's public address, size, city and
    firewall rule — a live host's fingerprint has no place in a public repo; the section says the
    address is in the Hetzner account; a grep for the address over the tracked tree → 0. `project_guardrails_plugin` →
    `reference_guardrails_plugin.md`, cut to the pointer and the one live gotcha.
    `project_semantic_layer_ai_ready` dropped.
  - THE HOOK IS WIRED AND ITS BUDGETS EQUAL THE MEASURED LANDING. `MAX_FILES = 50`,
    `INDEX_MAX_CHARS = 7669`, `FILE_MAX_CHARS = 4232`; `--report` on the live folder → `files 50/50,
    index 7669/7669, largest 4232/4232 (feedback_no_hacky_solutions.md)`, exit 0; on the backup →
    `files 108/50, index 17152/7669, largest 20407/4232 … OVER BUDGET`, exit 1. Six mutations on the
    REAL folder through the hook as the harness calls it (stdin event → stdout decision): a 51st note
    → DENIED ("the folder already holds 50 notes and the cap is 50 …"); an existing note rewritten to
    4,233 chars → DENIED ("… 4,233 characters; its budget is 4,232 …"); the same at 4,232 → allowed;
    `MEMORY.md` +1 char → DENIED ("… the index `MEMORY.md` 7,670 characters; its budget is 7,669");
    the largest note −1 char → allowed; the largest note +1 char → DENIED. And live in this session:
    a real `Write` of a 51st note was refused by the gate with the same text.
  - THE TEST COVERS EACH DENY AND EACH PASS. `tests/test_memory_budget_gate.py`: 29 tests, each
    deny with a passing twin one character inside the budget — the path test on both slash styles
    and five ignored paths; Write at/over the note budget; Edit measured on the resulting file;
    `replace_all` counted per occurrence; MultiEdit applied in order; shrinking an over-budget note
    passes; an Edit whose `old_string` is absent is left to the tool; a CRLF note written as bytes
    measures like LF text (at the budget after normalisation, over it raw — the no-op Edit passes,
    one char more is denied); the index's own budget; the index never counts as a note; a new note
    at the cap denied until one is removed; editing an existing note at the cap passes; one below
    the cap admits exactly one; six malformed inputs fail open; `--report` output pinned, its exit
    code over budget, and its message on a missing folder; the hook wired for Edit/Write/MultiEdit
    in `settings.json`; the three budgets pinned at ≤ the measured values by three separate
    assertions. Mutations run and watched go red: `MAX_FILES` 49 + `FILE_MAX_CHARS` 999999 → the pin
    test fails (a tuple comparison passed it); `_read_text` with `newline=""` → the CRLF test fails.
    `pytest tests/` → **1,084 passed, 1 skipped, 14 subtests passed** (12:09) on the 27-test
    version; the two added tests pass in the file's own run (29 passed). `ruff check --config .ruff-ci.toml` on the hook and the test →
    "All checks passed!".
  - THE DOCS AND THE HANDOVER ARE CURRENT. `docs/agent_guardrails.md` has the row; `CLAUDE.md`
    "Memory files" names the three budgets, the hook and `--report`, and its two key-files lines
    point at files that exist (`feedback_engineering.md`, `user_profile.md`);
    `tests/test_no_dead_issue_refs.py` still passes (6 passed) with the `#115` mention;
    `.claude/active_work.md` states #115 done with this branch and #118 next (15,890 chars, under
    the 16,000 budget).

## What is NOT demonstrated
- A shell write (`>`, `tee`, `sed -i`) into the memory folder bypasses the hook, as it bypasses
  `comment_history_gate.py`; the repo's rule already forbids shell writes for files. Closing it is
  reserved.
- The harness rewrites a note's frontmatter (`node_type`, `originSessionId`, `modified`) after a
  write, adding ~100 characters outside any tool call; the budgets were measured after that
  rewrite settled, so the largest note sits exactly at its budget and a later harness rewrite of
  it is not gated. A subsequent tool write to it must shrink it or be denied — the ratchet, working.
- The rest of `docs/operations_guide.md` "CI/CD guardrails" is GitHub-era prose (workflows, Pages)
  that no longer describes CI; the new runner section sits beneath it unchanged. Rewriting that
  section is a separate doc item, not this step's.
- The memory folder is outside the patch. Reviewers cannot diff it; this file and the backup in the
  scratchpad are the record. The 13 deleted handovers and the 21 deleted `project_*` files can be
  read in `scratchpad/memory_before/` for the rest of this session only.
