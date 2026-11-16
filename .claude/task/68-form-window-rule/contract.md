# Task contract — form-window rule: the qualifying cell and two stale comments

objective: >
  Issue 68: bring the form-window code and the rule in docs/metrics_context_model.md section 4 into
  line. The domestic-league "before it starts" window is already served (mart_team_season_record
  prev_season, flagged is_form_window); two model comments still say a missing fallback fills that
  gap and are removed. The qualifying "While it's running" cell predates the national-context
  ruling of section 8 and is set to the last 5 across the national team's matches, which the code
  already does.

refs: >
  Issue 68. Go-live gate issue 290. Requested by the coordinating session.

scope_paths:
  - docs/metrics_context_model.md
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/tests/assert_team_form_window_follows_the_rule.sql
  - tests/test_no_decision_history_in_code.py
  - .claude/task/68-form-window-rule/contract.md
  - .claude/task/68-form-window-rule/review.md
  - .claude/task/68-form-window-rule/review_input.patch

impact_map: >
  writers: the two models only; the change is inside their header comments, no SQL changes.
  downstream: `dbt ls --select int_team_momentum_window+ int_team_momentum__metrics+
  --resource-type model` gives int_player_momentum__metrics, int_team_momentum__metrics,
  int_team_momentum_window, mart_matchday_insights, mart_player_momentum,
  mart_team_momentum_window, mart_team_window_metrics.
  layer_rules: unchanged; no ref, column or materialisation changes.
  deploy_order: none; the compiled SQL outside the comment block is byte-identical.
  blast_radius: none. Comment-only in models; no number changes. The data build is expected to show
  zero changed team-window rows against prod.

approved_design:
  - none: no page output changes

depends_on:
  - none: no open MR touches these files; the code this needs is on main

shared_files:
  - none: no design baseline or chart pin changes

decisions_taken: >
  The qualifying cell follows the CPO's national-context ruling recorded in commit 4a1a348d
  (17 Jun 2026, section 8 spec): outside a big tournament a national team's figures are the last 5
  national-team matches, pooled. The cell takes the wording of its own "Before it starts" cell.
  No other document text changes. No new mechanism, no spend beyond read-only queries.

decisions_reserved:
  - none: the only rule change is the one cell the 4a1a348d ruling already settles.

done_when:
  - The section 4 qualifying row reads "Last 5 across the national team's matches" in both its
    "Before it starts" and "While it's running" cells.
  - grep for "326" in the two models finds nothing.
  - python scripts/ci_local.py --mr is green.
  - The MR pipeline is green and data:build:mr passes.
  - A read-only comparison of the MR's ci_mr team-window tables against prod (under 20 GB) lists
    every changed row; zero expected.

amendments:
  - + dbt_project/tests/assert_team_form_window_follows_the_rule.sql. Authority: the analytics
    engineer's round-1 finding that the form-window test skips a qualifying side whose campaign is
    under way, the case the corrected cell settles. Content: drop the two qualifying exclusions and
    the header sentence that names the old cell, so the test checks qualifying sides against the
    last 5 national matches. done_when: the test passes in data:build:mr. No new mechanism, no spend.
  - + tests/test_no_decision_history_in_code.py. Authority: the pin rule (a pin only goes down, and
    the test asks for the lower number). Content: PINNED_LINES 273 to 270, because the removed
    comments carried three issue references. PINNED_FILES stays 93.
