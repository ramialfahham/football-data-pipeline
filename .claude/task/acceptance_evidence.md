# Verification — one naming rule for core and mart models

Two documents change; no model, test or script.

- **The rule against the models:** every core model is `fct_` or `dim_`. Every mart starts with
  one of `player`, `team`, `competition`, `fixture` or `matchday`, except seven:
  - `mart_leaderboards`, `mart_standings`, `mart_roster`, `mart_head_to_head`,
    `mart_match_days`, `mart_next_matchday`;
  - `mart_player_match_log`, which #176 merges into `mart_player_fixture_stats`.
- **Readers:** a search for the old rule text finds it only in the two edited files; no script,
  hook, test or CI gate reads either line.
- **Checks:** every offline gate passes; pytest 1496 passed, 2 skipped; the 8 test files that
  read documents, rerun on the final text, 532 passed.
