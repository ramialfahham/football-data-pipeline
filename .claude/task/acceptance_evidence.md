# Verification — the goals of CAF match 1639347

Read from production before the change (dry-run bytes put to the CPO first): `core.fct_fixture`
holds fixture 1639347 as Young Africans (5370) 4–1 CFFA (17447), FT, 21 Oct 2026, 2nd Preliminary
Round; `core.fct_fixture_event` holds three goal events, all Young Africans (Kazimoto 27',
Mwalimu 49' and 53'); `intermediate.int_legs__player_match` holds no player goals. The nightly's
stored failure (`dbt_test__audit.assert_mart_competition_fixtures_goals_add_up`) is this one match,
problem `goals_not_reconciled`.

criteria_demonstrated:
  - The seed gains exactly five rows, all fixture 1639347, goal_order 1–5, and no other line changes (`git diff --stat`: 5 insertions). Each row has its team, scorer, minute, `Normal Goal`, a source kind, the source URLs and the note; `dbt parse` passes and the seed's schema tests compile.
  - assert_mart_competition_fixtures_goals_add_up and assert_result_corrections_applied are run by the MR's data build (`data:build:mr`), which builds the seed and its 56 downstream models; its result is read before the MR is reported ready.
  - mart_match_days is among those 56 models; the same data build runs assert_mart_match_days_is_the_matches_page_reach on it.
