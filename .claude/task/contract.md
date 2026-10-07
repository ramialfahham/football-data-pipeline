# Task contract — #173, part 1: the match page's lists of matches read mart_competition_fixtures

objective: >
  The match page's readers of matches read mart_competition_fixtures and only filter it: the
  header (the match) and each team's next match, served for the future match page's Next matches. The mart gains venue_name, is_home_team_next_match and
  is_away_team_next_match.

refs: >
  #173 (one source for every list of matches), its How step 2 order, approved in chat, 2026-10-07;
  the three column names and the acceptance criteria, approved in chat, 2026-10-07; #166 Next
  matches (the block that draws the next match).

acceptance_criteria:
  - Every fixture file shows the same header and the same Recent matches before and after; the export's output is compared file by file.
  - Every fixture file carries each team's next match, other than this one, read from mart_competition_fixtures. A team whose next match is this one has none.
  - A dbt test fails when a team has more than one next match.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_competition_fixtures_one_next_match_per_team.sql
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: mart_competition_fixtures is written only by its own model (dbt). The export reads it.
  downstream: `dbt ls --select mart_competition_fixtures+ --resource-type model` →
    football_data_pipeline.5_marts.shared.mart_competition_fixtures,
    football_data_pipeline.5_marts.shared.mart_match_days. mart_match_days selects named columns,
    so three added columns change nothing there. Export readers: fetch_fixture_payloads (changed
    here), fetch_match_day_payloads, fetch_landing_payload, fetch_competition_payloads (read named
    columns or group rows; an added column changes no payload they write).
  layer_rules: marts layer; league_code stays the discriminator, no competition is named in logic;
    check_layer_contract.py and the materialisation rule unchanged.
  deploy_order: the export reads the new columns, so it is run against prod only after the
    nightly after merge builds them; the committed site sample is not regenerated in this MR.
    data:build:mr builds the mart and mart_match_days into the MR's own datasets.
  blast_radius: mart_competition_fixtures gains three columns, existing columns unchanged. The
    fixture payload gains next_match per side; header and form_window values unchanged (the header
  read from the mart, form_window not touched), proven by
    a file-by-file comparison of the export before and after on the same data.

decisions_taken: >
  The column names and the three acceptance criteria are approved in chat, 2026-10-07. "Not yet
  started" is status NS or TBD with a kick-off after the build, the export's own test for an
  unplayed fixture page. Recent matches stay on mart_team_momentum_window in this MR: each row is
  one team's side of a match, which only dbt may derive; they move with the team page's played
  matches (#173 How step 2, approved in chat, 2026-10-07). The next match is the mart's row as it
  stands, both teams, no side derived. The team's country stays on dim_team, a team attribute, not a match. The committed site
  sample is not regenerated; the before/after comparison runs on scratch output, with the new
  mart's compiled SQL inlined against prod, read-only.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none (a mart column, a singular test, an export field).
  RECURRING COST: the mart's nightly read before and after, measured by dry run and put to the CPO
  before merge.

decisions_reserved:
  - The other readers of #173 (Home, the Matches page, the Matchdays tab, the team page): their
    own MRs.
  - How Next matches looks on the future match page: #166.

done_when:
  - dbt parse clean; SQLFluff clean on the mart and the new test.
  - The new singular test runs against prod with the compiled SQL inlined, red under a mutation
    that gives a team two next matches, then green.
  - pytest tests/test_export_site_data.py passes.
  - The fixture export run before and after on the same data: every file equal once next_match is
    set aside; every side's next_match checked against the mart filter.
  - The mart's nightly bytes before and after, measured by dry run, put to the CPO.
  - data:build:mr green.

amendments: (none)
