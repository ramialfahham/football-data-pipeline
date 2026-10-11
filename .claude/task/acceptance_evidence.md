# Verification — one goal definition

What counts as a goal is now defined once, in `base_apif__fixture_events`. Every model and test that
counts goals reads it. The checks below ran the branch's compiled SQL on prod data in session-only
temp tables (read-only, dry-run first), against today's prod tables.

- **Before the plan (0.29 GB in three queries):** leaving out every goal event without a scorer id
  would break 275 matches that add up today, so the nameless rule applies only where the match then
  adds up. Negative-minute kicks: leaving them out fixes 5 matches and breaks none.
- **Row by row against prod (about 1.5 GB):**

  | Model | Rows | Rows that differ | Matches that differ |
  |---|---|---|---|
  | `base_apif__fixture_events` (existing columns) | 871,852 | 0 | none |
  | `base_apif__fixture_players` | 1,911,038 | 128 | 5 shoot-outs with kicks at a negative minute |
  | `base_apif__fixture_statistics` | 120,266 | 18 | 17, each with a nameless event left out or a negative-minute kick |

  - The new flags are never null; a nameless goal event is left out in exactly the 19 matches
    measured before the plan.
- **What changes, column by column (about 1.8 GB):**
  - Players, 2019 AFC Champions League shoot-outs (241324, 241336, 253614, 253618, 253724): 7
    players had a shoot-out kick counted as an in-match penalty goal; their `goals_penalty` and
    `penalties_scored` drop by 1, their goals do not change. Blank `penalties_won` and
    `penalties_committed` become 0 on 124 and 110 rows, because the events now show no penalty in
    the match.
  - Statistics: the team goal split (`goals_penalty`, `goals_own`) is filled for those matches,
    whose goal events now add up to the score.
  - The four changed tests (`assert_base_player_stats_cleaned`, `assert_base_team_stats_cleaned`,
    `assert_team_goal_split_adds_up_to_score`, `assert_extra_time_goals_counted_in_score`)
    return 0 rows on the branch's rebuilt data.
- **Nightly read:** the events model now also reads `base_apif__fixtures_next`'s score columns,
  2.5 MB a night (about 75 MB a month). Nothing else reads more.
- **The first `data:build:mr` failed on two tests; both fixes approved in chat, 2026-10-11:**
  - `assert_team_match_cleaning_answer_key`: Aston Villa 0-1 Arsenal's expected penalties change
    from blank to 0. The nameless goal event did not count (the match report has only Saka 59'),
    and without it the events add up.
  - The `assist_player_sk` relationships test: 3,026 assist events in 1,449 matches named 2,318
    players missing from `dim_player`. All 2,318 carry a name (13 MB check on the MR's CI
    tables). `base_apif__players` now adds the assister as it adds the event's own player.
- **Checks:**
  - `dbt parse` passes.
  - sqlfluff shows no new finding on any changed model or test (counts equal to main's).
  - Every offline gate passes.
  - pytest: 1496 passed, 2 skipped.
