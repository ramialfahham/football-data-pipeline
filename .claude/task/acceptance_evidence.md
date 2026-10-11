# Verification — a played match's goals on the match mart

Every played match now has its goals on `mart_competition_fixtures` and one goal-data state.
Matches whose provider data is wrong are corrected from sourced research. All checks ran the
branch's compiled SQL on prod data in session-only temp tables, read-only, dry-run first.

- **Research (web, two sources per match or an official record; Wikipedia never):**
  - 60 matches whose goal events did not add up: 37 corrected goal by goal (6 of them 0-0, one
    "no goal" row each), 20 whose stored score was wrong, 3 left out because no source names their
    scorers (they show as not recorded).
  - The 20 wrong scores were the two-leg aggregate or counted shoot-out kicks. Once corrected, the
    provider's own goal events add up, so they need only a score row.
  - 23 matches the provider files as awarded: each gets how it came about. Two (Djoliba-Red Star
    Bangui, Al Hilal-Salaam) were not played and won by the home side by two reports each, but no
    source states a score; the provider's is kept and the note says so.
  - 5 awarded matches that were played or abandoned get their goals as scored on the pitch.
- **Seeds:** `fixture_goal_corrections` 108 rows in 42 matches; `fixture_result_corrections` 43
  new rows (20 scores, 23 awards). A script checked every row before writing: sides add up,
  https sources, two sites for match reports, no Wikipedia.
- **What changes:** 20 scores (no winner changes), 8 walkovers filed 0-0 gain their winner, 11
  statuses WO to AWD, 23 award kinds, and the goals of the 42 corrected matches.
- **The mart on prod data, every played match:**

  | State | This season | Earlier |
  |---|---|---|
  | goals | 4,019 | 52,590 |
  | goals_without_minutes | 1 | 16 |
  | not_recorded | 248 | 3,185 |
  | awarded | 3 | 71 |

  - `assert_mart_competition_fixtures_goals_add_up` and `assert_result_corrections_applied`
    return 0 rows.
- **Nightly read:** the mart reads about 0.15 GB more a night (goal events, players' goals,
  player names), about 4.6 GB a month.
- **Checks:**
  - `dbt parse` passes.
  - sqlfluff: 0 findings on every changed model and test.
  - Every offline gate passes, `check_relationships_coverage` included.
  - pytest: 1496 passed, 2 skipped.
