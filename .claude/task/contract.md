# Task contract — #159: flag each competition's last matchday of this season

objective: >
  Add is_last_round to marts.mart_competition_fixtures: the played matches of each competition's
  newest round with a played match, within the season of its next matchday, so the Matches page's
  past days can reach back to it without deciding it in the site. One leaf mart, its YAML and one
  singular test; no export or site change.

refs: >
  #159 (the build issue; its What exactly is the requirement, first line reworded to the CPO's
  definition); #131 "The days behind the Matches hub: how far back" (the ruling); the plan approved
  in plan mode, with the CPO's answer "Option 1": only played matches are flagged, a round in progress
  carries both flags, a postponed unplayed match is never flagged.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_competition_fixtures_last_round_is_the_round_just_played.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: dbt only; the mart reads fct_fixture, dim_team, int_legs__team_match (the played
    definition, by semi-join) and mart_next_matchday (the next round and so the current season).
    No new input.
  downstream: `.venv/Scripts/dbt.exe ls --project-dir dbt_project --select mart_competition_fixtures+`
    → football_data_pipeline.5_marts.shared.mart_competition_fixtures and only its own tests
    (accepted_values x3, not_null x15, unique fixture_sk, relationships x3,
    competition_fixtures_order_unique_per_season, _played_has_a_score, _slug_unique_per_competition,
    _top_match_is_in_the_next_round, assert_mart_competition_fixtures_next_round_is_one_round,
    _one_row_per_fixture, _team_slugs_resolve). Leaf mart, no downstream model. The export reads it
    by an explicit column list (scripts/export_site_data.py:1339), so the new column reaches no
    payload.
  layer_rules: marts select and present; league_code on every row; no partition_by or cluster_by;
    materialisation from the layer config (check_layer_contract.py).
  deploy_order: additive column; nothing reads it until the Matches page is built; the 04:00 nightly
    builds it after merge.
  blast_radius: no existing column or row changes. Measured read-only today: 29 competitions, 479
    matches carry the new flag.

decisions_taken: >
  The definition is the CPO's (Option 1 in plan mode): the newest round (by round_sequence) of the
  season of the competition's next matchday that has a played match; only its played matches are
  flagged; a round in progress carries both flags; a postponed unplayed match is never flagged; a
  competition with no next matchday has no flag. Builder's: the column name is_last_round, beside
  is_next_round; the test's file name.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none (a column and a singular test on an existing mart, the
  pattern the next-round flag set). RECURRING COST: none measurable; one more column on a table the
  nightly already builds.

decisions_reserved:
  - Anything on the site or in the export (the Matches page, #160).
  - Earlier seasons: not flagged, by the #131 ruling.

done_when:
  - dbt parse succeeds; sqlfluff (repo root, full rule set) passes on the model and the test;
    check_layer_contract.py and check_description_hygiene.py pass.
  - The compiled model, inlined read-only against prod, flags 29 competitions and 479 matches, every
    one played, in the next matchday's season, one round per competition.
  - The compiled test, run against the inlined model, returns 0 rows, and at least one row under each
    mutation: flagging unplayed matches too, dropping the season condition, choosing the round of the
    latest played kick-off, taking the round before the next round.
  - python -m pytest tests/ -q passes.

amendments: (none)
