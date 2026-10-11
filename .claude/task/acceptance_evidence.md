# Verification — matches after extra time carry their score after extra time

Read-only queries against prod's tables, with the new model's and the new test's compiled SQL
pointed at `dbt_analytics` (base) and `core`. Each was dry-run first; bytes are listed.

- **Scores that change (0.05 GB):** the new model against today's `core.fct_fixture` changes 41
  scores and no other. 8 are this season, and 14 change the result. All 41 are AET/PEN.
- **Today (0.05 GB):** the new test's compiled SQL on today's `fct_fixture` returns the same 41
  matches.
- **With the fix (0.10 GB):** the new test with `fct_fixture`'s score replaced by the new model's
  returns 0 rows.
- **The first count of 46** included 5 matches from the 2019 Libertadores and AFC Champions League.
  Their extra goal events are shoot-out kicks filed at minute -1 without the shoot-out label. The
  rule counts minute -1 in the first 90 minutes, so it leaves them unchanged.
- **This season's 8 against match reports:** each corrected score matches the report.
  - Pafos 4–0 Hajduk Split (stored 2–0) and Rapid Wien 2–2 Hearts (1–1).
  - ML Vitebsk 2–1 Borac (1–0) and Koper 1–3 NSÍ Runavík (0–2).
  - Ilves 2–1 Stjarnan (1–0) and Lech Poznań 1–4 AGF (0–3).
  - Celje 2–2 Egnatia (1–1) and Yelimay 2–2 Alashkert (1–1).
  - The Lech–AGF report also confirms that the provider's no-player goal event at 21' was a
    penalty VAR overturned.
- **The two stats-cleaning tests** (`assert_base_team_stats_cleaned`,
  `assert_base_player_stats_cleaned`) now read the corrected score, as the models they check do.
  Prod's stats tables were cleaned against the old score, so a query against prod cannot check
  them. `data:build:mr` rebuilds the models in CI's datasets and runs both tests.
- **Nightly cost:** the new model reads 0.05 GB (dry-run against prod), about 1.5 GB a month.
- **Checks:**
  - `dbt parse` passes with 104 models and no cycle.
  - `check_layer_contract`, `check_description_hygiene` and `check_relationships_coverage` pass,
    and so does every other offline gate.
  - pytest: 1,496 passed.
  - sqlfluff (repo root, jinja, bigquery, full rules) reports 0 findings on the new model, the two
    base models and the test. `fct_fixture` shows the same 3 findings as main, on the
    `dbt_utils` line that the jinja templater cannot resolve. The two stats-cleaning tests show
    32 and 66 findings, the same counts as main.
