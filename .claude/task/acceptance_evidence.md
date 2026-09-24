# Acceptance evidence — #160 part 1, mart_match_days

No `site_v2/src/` change, so no acceptance gate applies; this records what was run. The compiled
model and the compiled test were run read-only against prod (dev datasets swapped for prod's, the
model inlined into the test), never `dbt build`.

criteria_demonstrated:
  - THE REACH IS THE RULED ONE. The inlined mart: 837 rows over 58 days and 32 competitions, the
    same count as a direct query of is_last_round plus mart_next_matchday's rows; the new test,
    recomputing both sides from fct_fixture and int_legs__team_match, returns 0 rows. RED with past
    matches outside the last matchday let in (203 rows) and with the next matchday taken by flag so
    unplayed rows dated in the past come in (29 rows).
  - ONE OPENING DAY, AND NEIGHBOURS THAT SKIP EMPTY DAYS. Exactly 1 opening day, 2026-09-24 (the
    build day, which has matches); 24 rows sit on the first day (no previous day) and 2 on the last
    (no next day). RED with the opening day taken as the first day overall (27 rows) and with the
    next day skipping a day with a match (835 rows). dbt parse OK; sqlfluff clean on the model and
    the test; check_layer_contract and check_description_hygiene pass; pytest 1325 passed.
