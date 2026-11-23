# Task contract — #343 leftovers: stale order wording, old metric ids, the match mock's leaders order

objective: >
  Three leftovers of #343 (the catalogue sets the metric order on every surface). The
  _shape_team_benchmarks docstring in scripts/export_site_data.py no longer says the frontend
  re-orders per the metrics_display block order. The player table in metrics_display.md and the
  bundle table in 03_player_profile.md name the catalogue's ids for shots on target and shots on
  target faced. The Match leaders boards of design-mocks/gen_match_page.py take their order from
  design-mocks/catalogue_order.py and keep their metric set.

refs: >
  #343; the coordinating session's brief for the follow-up after !522.

scope_paths:
  - scripts/export_site_data.py
  - docs/wireframes/metrics_display.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/99_gaps_register.md
  - design-mocks/gen_match_page.py
  - tests/test_design_mocks_read_catalogue_order.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/343-catalogue-order-leftovers/contract.md
  - .claude/task/343-catalogue-order-leftovers/review.md
  - .claude/task/343-catalogue-order-leftovers/review_input.patch

impact_map: >
  Leaf change. The export edit is one docstring: `git diff gitlab/main -- scripts/export_site_data.py`
  changes comment text only, no code line, so no payload, mart or number changes. The mock edit
  reads an existing seed through design-mocks/catalogue_order.py. `grep -rn "gen_match_page"
  scripts dbt_project site_v2/src` returns nothing outside design-mocks and tests, so no consumer
  reads the mock's output. The wireframe edits are documents. dbt lineage: no model, seed or
  macro file changes, so `dbt ls` has nothing to select.

approved_design:
  - none: no page output changes

depends_on:
  - none: !522 is merged into main; no open MR touches these files
shared_files:
  - none: no design baseline, component registry, font coverage or chart screenshot file changes

decisions_taken: >
  The coordinating session scoped these three leftovers as #343 work and said the leaders lists
  keep their metric set and only take their order from the catalogue. The ids follow the catalogue:
  shots_on_goal_player for the shots on target atomic and shots_on_goal_against_player for shots
  on target faced. The team display id `shots_on_target_per_match` in metrics_display.md stays,
  because that document explains it as the display id.

decisions_reserved:
  - none: every rule applied is named in decisions_taken

done_when:
  - python -m pytest tests/test_design_mocks_read_catalogue_order.py tests/test_no_decision_history_in_docs.py tests/test_sentence_length_in_docs.py -q passes
  - python scripts/ci_local.py --mr passes

amendments: (none)
