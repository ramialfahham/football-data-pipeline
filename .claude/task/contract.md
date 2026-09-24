# Task contract — #160 part 1: the warehouse decides the Matches page's days

objective: >
  Add marts.mart_match_days: one row per fixture the Matches page shows, with its day, its order
  within its competition that day, the opening day and each day's neighbouring days with a match,
  so the export and the site select and order nothing. Part 1 of #160; the export and the page are
  part 2, in a second MR after this is built in prod.

refs: >
  #160 (the build issue); #130 "The approved design" (opens on the build day or the next day with a
  match; each day its own page); #131 rulings (forward to the end of each competition's next
  matchday, back to its last matchday of this season; days with none skipped); #159 (is_last_round);
  the plan approved in plan mode (two MRs, the warehouse decides reach, opening day and neighbours).

scope_paths:
  - dbt_project/models/5_marts/shared/mart_match_days.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_match_days_is_the_matches_page_reach.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: dbt only; the new mart reads mart_competition_fixtures (is_last_round, fixture_date,
    kickoff_datetime) and mart_next_matchday (the next matchday's upcoming fixtures, the rows Home
    shows); mart-to-mart refs are established (mart_competition_fixtures reads mart_next_matchday).
  downstream: a new model, so `dbt ls --select mart_match_days+` lists only it and its own tests;
    nothing reads it until part 2's export does. Upstream unchanged.
  layer_rules: marts select and present; league_code on every row; no partition_by or cluster_by;
    materialisation from the layer config (check_layer_contract.py).
  deploy_order: additive; a new table the 04:00 nightly builds after merge; part 2 exports from it
    only after that build.
  blast_radius: no existing model, column or row changes. Measured read-only today: 58 days, 32
    competitions, 837 rows.

decisions_taken: >
  The reach is the CPO's (#131): a past day shows its competition's last matchday (is_last_round,
  played by definition), a future day its next matchday (mart_next_matchday's rows, the same rows
  Home's Next matches block shows); days with none are skipped. The opening day is #130's: the build
  day, else the next day with a match. A day is the UTC fixture_date until #146. The competition
  order within a day stays the site's shared order (#130 names it so). Builder's: the name
  mart_match_days, its column names, the test's file name, and splitting #160 into two MRs.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none (a new mart and a singular test, the established
  pattern). RECURRING COST: one more small mart table in the nightly build; its input tables are
  already built, so the added scan is a few MB.

decisions_reserved:
  - Everything on the site and in the export: part 2 of #160.
  - The venue's local day: #146.

done_when:
  - dbt parse succeeds; sqlfluff (repo root, full rule set) passes on the model and the test;
    check_layer_contract.py and check_description_hygiene.py pass.
  - The compiled model, inlined read-only against prod: 58 days, 32 competitions, 837 rows, exactly
    one opening day.
  - The compiled test against the inlined model returns 0 rows, and at least one row under each
    mutation: past unplayed matches included, next-matchday rows dated in the past included, the
    opening day taken from the first day overall, a neighbour that skips a day with a match.
  - python -m pytest tests/ -q passes.

amendments: (none)
