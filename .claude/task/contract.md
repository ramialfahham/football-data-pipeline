# Task contract — a league table's points below its results are explained by a declared adjustment

objective: >
  #147 as rewritten and approved on 2026-10-05. The league-table check accepts a table whose points
  are below 3 x its wins + draws without a reason. Every such row is declared in a new seed with the
  points the league took, the rule (deduction, halving) and its official source, and the check fails
  when a table row's points are not 3 x wins + draws less the declared points taken.

refs: >
  #147, its rewritten text approved by the CPO on 2026-10-05 ("keep #147, then #186").

acceptance_criteria:
  # The issue's checklist lines, verbatim.
  - "Every league-table row whose points are below 3 x its wins + draws, where it counts the same games as our results, is explained by a declared adjustment in a seed: the team-season, the points taken, the rule (deduction, halving) and its official source."
  - "`assert_team_season_equals_league_table` fails, at severity error, on a lower table with no declared adjustment, or a declared one that no longer matches."
  - "The 52 rows lower today are declared, each with its source (Belgian Pro League halving, the Turkish deductions, ...)."

scope_paths:
  - dbt_project/seeds/standings_points_adjustments.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_team_season_equals_league_table.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

decisions_taken: >
  #147 as rewritten and approved on 2026-10-05.

  Readings, under the CPO's delegation of 2026-10-02 ("Readings of approved rules are yours"):
  - One seed row per table row (league_code, season, team_id, group_name), as standings_corrections
    is keyed; points_taken is the positive number of points the league took; rule is deduction or
    halving; source_kind and source are described as in the two correction seeds.
  - The check is one changed condition in the existing test: the table's points equal 3 x wins +
    draws less the declared points taken (0 where none is declared), on every compared table row. A
    renamed or vanished table row needs no check of its own: its lower replacement is undeclared and
    fails.
  - The Belgian halving rows: points taken = half the regular-season points rounded down (the
    league halves them rounded up), checked on prod for all 38 rows against the provider's own
    regular-season table rows; each row cites the Pro League's rule.

  Threshold declarations. NEW MECHANISM: none; a seed of declared official decisions with sources
  is the pattern of standings_corrections. RECURRING COST: one seed of 52 rows and a join in an
  existing test; measured by dry run.

decisions_reserved:
  - No table value, result or metric changes; the site does not show an adjustment (#147's Not in
    scope).

done_when:
  - Over prod (bytes to the CPO first) the test returns no row with the seed; without it, the 52 rows;
    it fails on a deliberate break (a declared value changed, a row removed) and stays green on an
    identical rewrite.
  - dbt parse, description hygiene and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.

amendments: (none)
